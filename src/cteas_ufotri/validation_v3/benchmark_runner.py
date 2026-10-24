"""P7.7B execution harness for the five synthetic V3 benchmark cases.

The runner is deliberately a caller of existing public V3 APIs.  It owns no
production equations, parameter database, calibration path, or environmental
dataset.  Every numeric execution input is read from the validated case YAML;
the only references generated here are independent analytic synthetic
references declared by the case contract.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
from typing import Any

from ..coupling.atmos_v3 import AtmosphericForcingMetadata, AtmosphericHTOForcing
from ..exposure.dose_v3 import DOSE_COEFFICIENT_UNIT, DoseParameters
from ..exposure.intake_v3 import (
    CONSUMPTION_RATE_UNIT,
    ConsumptionParameters,
    FoodIntakeSolver,
)
from ..plant.food_v3 import HarvestParameters
from ..plant.leaf_exchange_resistance import (
    ForcingProvenance,
    LeafExchangeFlux,
    ResistanceChain,
)
from ..plant.obt_v3 import (
    OBTParameters,
    OBTState,
    OBTSolver,
    PlantBiologicalForcing,
)
from ..plant.root_v3 import RootParameters, RootUptakeForcing, RootUptakeSolver
from ..plant.soil_v3 import (
    SoilForcing,
    SoilParameters,
    SoilProvenance,
    SoilState,
    SoilStorageSolver,
)
from ..plant.tfwt_v3 import TFWTState, TFWTStorageSolver
from ..v3_pipeline import V3PipelineRunner, V3PipelineParameters, V3SimulationState
from .benchmarks import load_baseline_benchmark_cases
from .benchmark_registry import (
    _thaw,
    BenchmarkMetricResult,
    BenchmarkRegistry,
    BenchmarkResult,
    can_accept_synthetic_benchmark,
)
from .validation_case import ValidationCase
from .validation_gate import evaluate_validation_gate
from .validation_metric import (
    compute_metric,
)


SOLVER_VERSION = "v3-p7-7b-existing-solvers-v1"
_EPSILON = 1.0e-12


class BenchmarkRunnerError(ValueError):
    """A synthetic benchmark is malformed or cannot execute fail-closed."""




def _canonical(value: Any) -> str:
    return json.dumps(
        _thaw(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _number(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BenchmarkRunnerError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise BenchmarkRunnerError(f"{field} must be finite")
    return result


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkRunnerError(f"{field} must be non-empty text")
    return value


def _mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BenchmarkRunnerError(f"{field} must be a mapping")
    return value


def _value(mapping: Mapping[str, Any], key: str, *, field: str) -> Any:
    if key not in mapping:
        raise BenchmarkRunnerError(f"{field}.{key} is required")
    return mapping[key]


def _variable(case: ValidationCase, key: str, *, section: str = "forcing_definition") -> Any:
    payload = _mapping(getattr(case, section), field=section)
    variables = _mapping(_value(payload, "variables", field=section), field=f"{section}.variables")
    variable = _value(variables, key, field=f"{section}.variables")
    if isinstance(variable, Mapping):
        return _value(variable, "value", field=f"{section}.variables.{key}")
    return variable


def _parameter(case: ValidationCase, parameter_id: str) -> float:
    for parameter in case.parameter_context:
        if parameter.parameter_id == parameter_id:
            return _number(parameter.value, field=f"parameter_context.{parameter_id}")
    raise BenchmarkRunnerError(
        f"{case.case_id} does not declare parameter_context.{parameter_id}"
    )


def _execution(case: ValidationCase) -> Mapping[str, Any]:
    execution = _mapping(case.execution_definition, field="execution_definition")
    _text(_value(execution, "benchmark_kind", field="execution_definition"), field="benchmark_kind")
    return execution


def _timestamp(execution: Mapping[str, Any]) -> datetime:
    try:
        timestamp = datetime.fromisoformat(
            _text(
                _value(execution, "start_timestamp", field="execution_definition"),
                field="execution_definition.start_timestamp",
            )
        )
    except ValueError as exc:
        raise BenchmarkRunnerError(
            "execution_definition.start_timestamp must be ISO-8601"
        ) from exc
    if timestamp.tzinfo is None or timestamp.utcoffset().total_seconds() != 0.0:
        raise BenchmarkRunnerError(
            "execution_definition.start_timestamp must be timezone-aware UTC"
        )
    return timestamp


def _schedule(execution: Mapping[str, Any], factor: int) -> tuple[float, int]:
    base_dt = _number(
        _value(execution, "timestep_seconds", field="execution_definition"),
        field="execution_definition.timestep_seconds",
    )
    duration = _number(
        _value(execution, "duration_seconds", field="execution_definition"),
        field="execution_definition.duration_seconds",
    )
    if factor <= 0 or not math.isfinite(float(factor)):
        raise BenchmarkRunnerError("refinement factor must be positive")
    dt = base_dt / factor
    steps = round(duration / dt)
    if dt <= 0.0 or duration <= 0.0 or steps <= 0 or not math.isclose(
        steps * dt,
        duration,
        rel_tol=0.0,
        abs_tol=1.0e-10,
    ):
        raise BenchmarkRunnerError(
            "duration_seconds must be an exact multiple of each timestep"
        )
    return dt, steps


def _factors(execution: Mapping[str, Any]) -> tuple[int, ...]:
    raw = _value(execution, "refinement_factors", field="execution_definition")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise BenchmarkRunnerError("refinement_factors must be a sequence")
    factors = tuple(int(item) for item in raw)
    if not factors or factors[0] != 1 or len(set(factors)) != len(factors):
        raise BenchmarkRunnerError(
            "refinement_factors must be unique and start with 1"
        )
    return factors


def _tolerance(execution: Mapping[str, Any], name: str) -> float:
    tolerances = _mapping(
        _value(execution, "acceptance_thresholds", field="execution_definition"),
        field="execution_definition.acceptance_thresholds",
    )
    return _number(
        _value(tolerances, name, field="execution_definition.acceptance_thresholds"),
        field=f"acceptance_thresholds.{name}",
    )


def _runtime_provenance(case: ValidationCase, execution: Mapping[str, Any]) -> ForcingProvenance:
    return ForcingProvenance(
        source_id=case.provenance.source_identifier,
        source_version=str(execution.get("source_version", "p7-7b-synthetic")),
        artifact_sha256=case.provenance.artifact_sha256,
        spatial_reference="synthetic-v3",
        temporal_resolution_s=_number(
            _value(execution, "timestep_seconds", field="execution_definition"),
            field="execution_definition.timestep_seconds",
        ),
    )


def _soil_provenance(case: ValidationCase, execution: Mapping[str, Any]) -> SoilProvenance:
    forcing_provenance = _runtime_provenance(case, execution)
    return SoilProvenance(
        source_id=forcing_provenance.source_id,
        source_version=forcing_provenance.source_version,
        artifact_sha256=forcing_provenance.artifact_sha256,
        spatial_reference=forcing_provenance.spatial_reference,
        temporal_resolution_s=forcing_provenance.temporal_resolution_s,
    )


def _initial_inventory(case: ValidationCase, key: str = "inventory") -> float:
    variables = _mapping(case.initial_state["variables"], field="initial_state.variables")
    variable = _mapping(_value(variables, key, field="initial_state.variables"), field=f"initial_state.variables.{key}")
    return _number(
        _value(variable, "value", field=f"initial_state.variables.{key}"),
        field=f"initial_state.variables.{key}.value",
    )


def _soil_state(
    case: ValidationCase,
    execution: Mapping[str, Any],
    timestamp: datetime,
    inventory: float | None = None,
) -> SoilState:
    return SoilState.from_inventory(
        soil_identifier=_text(_value(execution, "soil_identifier", field="execution_definition"), field="soil_identifier"),
        layer_id=_text(_value(execution, "layer_id", field="execution_definition"), field="layer_id"),
        layer_depth_m=_number(_value(execution, "layer_depth_m", field="execution_definition"), field="layer_depth_m"),
        soil_water_content=_number(_value(execution, "soil_water_content", field="execution_definition"), field="soil_water_content"),
        soil_water_inventory_bq_m2=(
            _initial_inventory(case) if inventory is None else inventory
        ),
        timestamp=timestamp,
        provenance=_soil_provenance(case, execution),
    )


def _tfwt_state(
    case: ValidationCase,
    execution: Mapping[str, Any],
    timestamp: datetime,
    inventory: float | None = None,
) -> TFWTState:
    return TFWTState.from_inventory(
        plant_identifier=_text(_value(execution, "plant_identifier", field="execution_definition"), field="plant_identifier"),
        crop=_text(_value(execution, "crop", field="execution_definition"), field="crop"),
        growth_stage=_text(_value(execution, "growth_stage", field="execution_definition"), field="growth_stage"),
        tfwt_inventory_bq_m2=(
            _initial_inventory(case) if inventory is None else inventory
        ),
        water_content_kg_m2=_number(_value(execution, "water_content_kg_m2", field="execution_definition"), field="water_content_kg_m2"),
        time=timestamp,
        provenance=_runtime_provenance(case, execution),
    )


def _obt_state(
    case: ValidationCase,
    execution: Mapping[str, Any],
    timestamp: datetime,
    inventory: float | None = None,
) -> OBTState:
    return OBTState.from_inventory(
        plant_identifier=_text(_value(execution, "plant_identifier", field="execution_definition"), field="plant_identifier"),
        crop=_text(_value(execution, "crop", field="execution_definition"), field="crop"),
        growth_stage=_text(_value(execution, "growth_stage", field="execution_definition"), field="growth_stage"),
        obt_inventory_bq_m2=(
            _initial_inventory(case) if inventory is None else inventory
        ),
        plant_mass_kg_m2=_number(_value(execution, "plant_mass_kg_m2", field="execution_definition"), field="plant_mass_kg_m2"),
        timestamp=timestamp,
        provenance=_runtime_provenance(case, execution),
    )


def _audit(residuals: Mapping[str, float], tolerance: float) -> dict[str, Any]:
    numeric = {key: _number(value, field=f"residuals.{key}") for key, value in residuals.items()}
    maximum = max((abs(value) for value in numeric.values()), default=0.0)
    return {
        "passed": maximum <= tolerance,
        "max_abs_residual": maximum,
        "tolerance": tolerance,
        "residuals": numeric,
    }


def _trend_metric(
    execution: Mapping[str, Any],
    differences: Sequence[float],
) -> tuple[float, dict[str, Any]]:
    tolerance = _tolerance(execution, "numerical_stability")
    values = tuple(_number(item, field="refinement_difference") for item in differences)
    trend_ok = all(
        current <= previous + tolerance
        for previous, current in zip(values, values[1:])
    )
    return (
        0.0 if trend_ok else 1.0,
        {
            "refinement_differences": list(values),
            "trend": "non-increasing" if trend_ok else "not_non-increasing",
            "tolerance": tolerance,
        },
    )


def _restart_audit(
    differences: Mapping[str, float],
    tolerance: float,
) -> dict[str, Any]:
    numeric = {
        key: _number(value, field=f"restart_difference.{key}")
        for key, value in differences.items()
    }
    maximum = max((abs(value) for value in numeric.values()), default=0.0)
    return {
        "passed": maximum <= tolerance,
        "max_abs_difference": maximum,
        "tolerance": tolerance,
        "differences": numeric,
    }


def _criterion_metric(
    case: ValidationCase,
    criterion: Any,
    *,
    model: Sequence[float],
    reference: Sequence[float] | None,
    conservation: Mapping[str, Any],
) -> BenchmarkMetricResult:
    metric_name = criterion.metric_name
    if metric_name == "conservation_residual":
        value = _number(
            conservation["max_abs_residual"],
            field="conservation_result.max_abs_residual",
        )
    elif metric_name == "relative_error":
        if reference is None:
            raise BenchmarkRunnerError(
                f"{case.case_id} relative_error requires an independent reference"
            )
        value = compute_metric(metric_name, model[0], reference[0])
    else:
        if reference is None:
            raise BenchmarkRunnerError(
                f"{case.case_id} {metric_name} requires an independent reference"
            )
        value = compute_metric(metric_name, model, reference)
    return BenchmarkMetricResult.from_value(
        metric_name=metric_name,
        value=value,
        threshold=criterion.threshold,
        unit=criterion.unit,
        comparison=criterion.comparison,
    )


@dataclass(frozen=True)
class _BenchmarkComputation:
    metrics: tuple[BenchmarkMetricResult, ...]
    conservation_result: Mapping[str, Any]
    restart_result: Mapping[str, Any]
    numerical_stability: BenchmarkMetricResult
    observations: Mapping[str, Any]

    def signature(self) -> Mapping[str, Any]:
        return {
            "metrics": [item.to_mapping() for item in self.metrics],
            "conservation_result": self.conservation_result,
            "restart_result": self.restart_result,
            "numerical_stability": self.numerical_stability.to_mapping(),
            "observations": self.observations,
        }


class SyntheticBenchmarkRunner:
    """Execute the declared P7.7B cases through existing V3 public APIs."""

    def __init__(
        self,
        cases: Sequence[ValidationCase] | None = None,
        *,
        solver_version: str = SOLVER_VERSION,
    ) -> None:
        self.cases = tuple(
            load_baseline_benchmark_cases() if cases is None else cases
        )
        self.solver_version = _text(solver_version, field="solver_version")

    def run_all(self) -> BenchmarkRegistry:
        """Run every declared case in stable case-id order."""

        results = tuple(self.run_case(case) for case in self.cases)
        return BenchmarkRegistry(results=results)

    def run_case(self, case: ValidationCase) -> BenchmarkResult:
        """Run one case twice and record a deterministic result."""

        if not isinstance(case, ValidationCase):
            raise BenchmarkRunnerError("case must be a ValidationCase")
        gate = evaluate_validation_gate(case)
        gate.assert_allowed()
        input_hash = _sha256(case.to_mapping())
        execution_id = "exec-" + _sha256(
            {"input_hash": input_hash, "solver_version": self.solver_version}
        )
        first = self._execute_case(case)
        second = self._execute_case(case)
        deterministic_difference = self._signature_difference(
            first.signature(),
            second.signature(),
        )
        deterministic_metric = BenchmarkMetricResult.from_value(
            metric_name="deterministic",
            value=deterministic_difference,
            threshold=_tolerance(_execution(case), "deterministic"),
            unit="1",
            comparison="ABSOLUTE_LTE",
        )
        metrics = (
            first.metrics
            + (first.numerical_stability, deterministic_metric)
        )
        status = (
            "PASS_SYNTHETIC_BENCHMARK_VALIDATION"
            if all(item.pass_fail for item in metrics)
            and bool(first.conservation_result["passed"])
            and bool(first.restart_result["passed"])
            else "FAIL_SYNTHETIC_BENCHMARK_VALIDATION"
        )
        return BenchmarkResult(
            benchmark_id=case.case_id.replace("-7a-", "-7b-"),
            execution_id=execution_id,
            solver_version=self.solver_version,
            input_hash=input_hash,
            parameter_snapshot=case.parameter_context,
            metrics=metrics,
            conservation_result=first.conservation_result,
            restart_result=first.restart_result,
            status=status,
            provenance=case.provenance,
        )

    def _execute_case(self, case: ValidationCase) -> _BenchmarkComputation:
        kind = _execution(case)["benchmark_kind"]
        dispatch = {
            "radioactive_decay": self._radioactive_decay,
            "leaf_exchange_tfwt": self._leaf_exchange_tfwt,
            "tfwt_obt": self._tfwt_obt,
            "soil_root": self._soil_root,
            "end_to_end_pathway": self._end_to_end_pathway,
        }
        try:
            handler = dispatch[kind]
        except KeyError as exc:
            raise BenchmarkRunnerError(
                f"unsupported synthetic benchmark kind {kind!r}"
            ) from exc
        return handler(case)

    @staticmethod
    def _signature_difference(left: Any, right: Any) -> float:
        if _canonical(left) == _canonical(right):
            return 0.0
        left_text = _canonical(left)
        right_text = _canonical(right)
        if left_text != right_text:
            return 1.0
        return 0.0

    def _radioactive_decay(self, case: ValidationCase) -> _BenchmarkComputation:
        execution = _execution(case)
        start = _timestamp(execution)
        initial = _initial_inventory(case)
        half_life = _parameter(case, "half_life")
        external_input = _number(
            _variable(case, "external_input"),
            field="external_input",
        )
        soil_parameters = SoilParameters(tritium_half_life_s=half_life)
        provenance = _runtime_provenance(case, execution)

        def run(dt: float, steps: int) -> tuple[list[float], list[float]]:
            state = _soil_state(case, execution, start, initial)
            solver = SoilStorageSolver(parameters=soil_parameters)
            trajectory = [state.inventory()]
            residuals: list[float] = []
            for _ in range(steps):
                result = solver.advance(
                    state,
                    SoilForcing(deposition_flux_bq_m2_s=external_input),
                    dt,
                )
                state = result.state
                trajectory.append(state.inventory())
                residuals.append(result.balance.residual_bq_m2)
            return trajectory, residuals

        factors = _factors(execution)
        schedules = [_schedule(execution, factor) for factor in factors]
        trajectories = [run(dt, steps)[0] for dt, steps in schedules]
        reference = [
            initial * math.exp(-math.log(2.0) * (index * schedules[0][0]) / half_life)
            for index in range(len(trajectories[0]))
        ]
        model = trajectories[0]
        criteria = tuple(
            _criterion_metric(
                case,
                criterion,
                model=model,
                reference=reference,
                conservation={"max_abs_residual": 0.0},
            )
            for criterion in case.acceptance_criteria
        )
        final_values = [trajectory[-1] for trajectory in trajectories]
        differences = [abs(left - right) for left, right in zip(final_values, final_values[1:])]
        stability_value, stability_details = _trend_metric(execution, differences)
        stability = BenchmarkMetricResult.from_value(
            metric_name="numerical_stability",
            value=stability_value,
            threshold=0.0,
            details={"dt_seconds": [item[0] for item in schedules], **stability_details},
        )

        _, residuals = run(*schedules[0])
        conservation = _audit(
            {f"step_{index}": value for index, value in enumerate(residuals)},
            _tolerance(execution, "conservation"),
        )
        split_steps = int(_value(execution, "restart_split_steps", field="execution_definition"))
        full_trajectory, _ = run(*schedules[0])
        if split_steps <= 0 or split_steps >= schedules[0][1]:
            restart = _restart_audit({"inventory": 0.0}, _tolerance(execution, "restart"))
        else:
            state = _soil_state(case, execution, start, initial)
            solver = SoilStorageSolver(parameters=soil_parameters)
            forcing = SoilForcing(deposition_flux_bq_m2_s=external_input)
            for _ in range(split_steps):
                state = solver.advance(state, forcing, schedules[0][0]).state
            for _ in range(schedules[0][1] - split_steps):
                state = solver.advance(state, forcing, schedules[0][0]).state
            restart = _restart_audit(
                {"inventory": state.inventory() - full_trajectory[-1]},
                _tolerance(execution, "restart"),
            )
        return _BenchmarkComputation(
            metrics=criteria,
            conservation_result=conservation,
            restart_result=restart,
            numerical_stability=stability,
            observations={"inventory": model, "reference": reference},
        )

    def _leaf_exchange_tfwt(self, case: ValidationCase) -> _BenchmarkComputation:
        execution = _execution(case)
        start = _timestamp(execution)
        initial = _initial_inventory(case)
        flux_value = _number(_variable(case, "leaf_exchange_flux"), field="leaf_exchange_flux")
        leaf_flux = LeafExchangeFlux(air_to_leaf_flux_bq_m2_s=flux_value)

        def run(dt: float, steps: int, flux: LeafExchangeFlux = leaf_flux) -> tuple[list[float], list[float]]:
            state = _tfwt_state(case, execution, start, initial)
            trajectory = [state.inventory()]
            residuals: list[float] = []
            for _ in range(steps):
                result = TFWTStorageSolver().advance(state, flux, dt)
                state = result.state
                trajectory.append(state.inventory())
                residuals.append(result.balance.residual_bq_m2)
            return trajectory, residuals

        factors = _factors(execution)
        schedules = [_schedule(execution, factor) for factor in factors]
        trajectories = [run(dt, steps)[0] for dt, steps in schedules]
        reference = [initial + flux_value * (index * schedules[0][0]) for index in range(len(trajectories[0]))]
        criteria = tuple(
            _criterion_metric(
                case,
                criterion,
                model=trajectories[0],
                reference=reference,
                conservation={"max_abs_residual": 0.0},
            )
            for criterion in case.acceptance_criteria
        )
        final_values = [trajectory[-1] for trajectory in trajectories]
        stability_value, stability_details = _trend_metric(
            execution,
            [abs(left - right) for left, right in zip(final_values, final_values[1:])],
        )
        zero_trajectory, _ = run(schedules[0][0], schedules[0][1], LeafExchangeFlux(0.0))
        zero_invariant = abs(zero_trajectory[-1] - initial) <= _tolerance(execution, "conservation")
        stability = BenchmarkMetricResult.from_value(
            metric_name="numerical_stability",
            value=stability_value if zero_invariant else 1.0,
            threshold=0.0,
            details={"zero_input_invariant": zero_invariant, **stability_details},
        )
        _, residuals = run(*schedules[0])
        conservation = _audit(
            {f"step_{index}": value for index, value in enumerate(residuals)},
            _tolerance(execution, "conservation"),
        )
        full_trajectory, _ = run(*schedules[0])
        split_steps = int(_value(execution, "restart_split_steps", field="execution_definition"))
        state = _tfwt_state(case, execution, start, initial)
        for _ in range(split_steps):
            state = TFWTStorageSolver().advance(state, leaf_flux, schedules[0][0]).state
        for _ in range(schedules[0][1] - split_steps):
            state = TFWTStorageSolver().advance(state, leaf_flux, schedules[0][0]).state
        restart = _restart_audit(
            {"tfwt_inventory": state.inventory() - full_trajectory[-1]},
            _tolerance(execution, "restart"),
        )
        return _BenchmarkComputation(
            metrics=criteria,
            conservation_result=conservation,
            restart_result=restart,
            numerical_stability=stability,
            observations={"tfwt_inventory": trajectories[0], "reference": reference},
        )

    def _tfwt_obt(self, case: ValidationCase) -> _BenchmarkComputation:
        execution = _execution(case)
        start = _timestamp(execution)
        tfwt_inventory = _number(_variable(case, "tfwt_inventory"), field="tfwt_inventory")
        initial_obt = _initial_inventory(case)
        kf = _parameter(case, "kf_s")
        kr = _parameter(case, "kr_s")
        daylight = bool(_variable(case, "daylight"))
        tfwt = _tfwt_state(case, execution, start, tfwt_inventory)
        biological = PlantBiologicalForcing(is_daylight=daylight)
        solver = OBTSolver(parameters=OBTParameters(kf_s=kf, kr_s=kr))

        def run(dt: float, steps: int) -> tuple[list[float], list[float]]:
            state = _obt_state(case, execution, start, initial_obt)
            trajectory = [state.inventory()]
            residuals: list[float] = []
            for _ in range(steps):
                result = solver.advance(tfwt, state, dt, biological)
                state = result.state
                trajectory.append(state.inventory())
                residuals.append(result.balance.residual_bq_m2)
            return trajectory, residuals

        factors = _factors(execution)
        schedules = [_schedule(execution, factor) for factor in factors]
        trajectories = [run(dt, steps)[0] for dt, steps in schedules]
        source_rate = kf * tfwt_inventory if daylight else 0.0
        if kr == 0.0:
            reference = [initial_obt + source_rate * (index * schedules[0][0]) for index in range(len(trajectories[0]))]
        else:
            equilibrium = source_rate / kr
            reference = [
                equilibrium
                + (initial_obt - equilibrium)
                * math.exp(-kr * (index * schedules[0][0]))
                for index in range(len(trajectories[0]))
            ]
        criteria = tuple(
            _criterion_metric(
                case,
                criterion,
                model=trajectories[0],
                reference=reference,
                conservation={"max_abs_residual": 0.0},
            )
            for criterion in case.acceptance_criteria
        )
        final_values = [trajectory[-1] for trajectory in trajectories]
        stability_value, stability_details = _trend_metric(
            execution,
            [abs(left - right) for left, right in zip(final_values, final_values[1:])],
        )
        stability = BenchmarkMetricResult.from_value(
            metric_name="numerical_stability",
            value=stability_value,
            threshold=0.0,
            details=stability_details,
        )
        _, residuals = run(*schedules[0])
        conservation = _audit(
            {f"step_{index}": value for index, value in enumerate(residuals)},
            _tolerance(execution, "conservation"),
        )
        full_trajectory, _ = run(*schedules[0])
        split_steps = int(_value(execution, "restart_split_steps", field="execution_definition"))
        state = _obt_state(case, execution, start, initial_obt)
        for _ in range(split_steps):
            state = solver.advance(tfwt, state, schedules[0][0], biological).state
        for _ in range(schedules[0][1] - split_steps):
            state = solver.advance(tfwt, state, schedules[0][0], biological).state
        restart = _restart_audit(
            {"obt_inventory": state.inventory() - full_trajectory[-1]},
            _tolerance(execution, "restart"),
        )
        return _BenchmarkComputation(
            metrics=criteria,
            conservation_result=conservation,
            restart_result=restart,
            numerical_stability=stability,
            observations={"obt_inventory": trajectories[0], "reference": reference},
        )

    def _soil_root(self, case: ValidationCase) -> _BenchmarkComputation:
        execution = _execution(case)
        start = _timestamp(execution)
        initial = _initial_inventory(case)
        coefficient = _parameter(case, "root_coefficient")
        expected_concentration = _number(
            _variable(case, "root_zone_concentration"),
            field="root_zone_concentration",
        )
        provenance = _runtime_provenance(case, execution)

        def run(dt: float, steps: int) -> tuple[list[float], list[float], SoilState]:
            state = _soil_state(case, execution, start, initial)
            solver = RootUptakeSolver(parameters=RootParameters(k_root_m_s=coefficient))
            trajectory: list[float] = []
            residuals: list[float] = []
            for _ in range(steps):
                result = solver.advance_result(
                    state,
                    RootUptakeForcing(
                        plant_identifier=_text(_value(execution, "plant_identifier", field="execution_definition"), field="plant_identifier"),
                        root_zone_identifier=_text(_value(execution, "root_zone_identifier", field="execution_definition"), field="root_zone_identifier"),
                        interval_seconds=dt,
                        provenance=provenance,
                    ),
                )
                trajectory.append(result.root_flux.flux())
                residuals.append(result.balance.residual_bq_m2)
                state = state.with_inventory(
                    soil_water_inventory_bq_m2=result.balance.remaining_soil_inventory_bq_m2,
                    timestamp=result.root_flux.timestamp,
                )
            return trajectory, residuals, state

        factors = _factors(execution)
        schedules = [_schedule(execution, factor) for factor in factors]
        runs = [run(dt, steps) for dt, steps in schedules]
        reference_flux = coefficient * expected_concentration
        model = runs[0][0]
        reference = [reference_flux for _ in model]
        criteria = tuple(
            _criterion_metric(
                case,
                criterion,
                model=model,
                reference=reference,
                conservation={"max_abs_residual": 0.0},
            )
            for criterion in case.acceptance_criteria
        )
        final_inventories = [item[2].inventory() for item in runs]
        stability_value, stability_details = _trend_metric(
            execution,
            [abs(left - right) for left, right in zip(final_inventories, final_inventories[1:])],
        )
        stability = BenchmarkMetricResult.from_value(
            metric_name="numerical_stability",
            value=stability_value,
            threshold=0.0,
            details={"final_soil_inventories": final_inventories, **stability_details},
        )
        conservation = _audit(
            {f"step_{index}": value for index, value in enumerate(runs[0][1])},
            _tolerance(execution, "conservation"),
        )
        split_steps = int(_value(execution, "restart_split_steps", field="execution_definition"))
        if split_steps <= 0 or split_steps >= schedules[0][1]:
            restart = _restart_audit({"soil_inventory": 0.0}, _tolerance(execution, "restart"))
        else:
            full_state = runs[0][2]
            state = _soil_state(case, execution, start, initial)
            solver = RootUptakeSolver(parameters=RootParameters(k_root_m_s=coefficient))
            forcing = RootUptakeForcing(
                plant_identifier=_text(_value(execution, "plant_identifier", field="execution_definition"), field="plant_identifier"),
                root_zone_identifier=_text(_value(execution, "root_zone_identifier", field="execution_definition"), field="root_zone_identifier"),
                interval_seconds=schedules[0][0],
                provenance=provenance,
            )
            for _ in range(split_steps):
                result = solver.advance_result(state, forcing)
                state = state.with_inventory(
                    soil_water_inventory_bq_m2=result.balance.remaining_soil_inventory_bq_m2,
                    timestamp=result.root_flux.timestamp,
                )
            for _ in range(schedules[0][1] - split_steps):
                result = solver.advance_result(state, forcing)
                state = state.with_inventory(
                    soil_water_inventory_bq_m2=result.balance.remaining_soil_inventory_bq_m2,
                    timestamp=result.root_flux.timestamp,
                )
            restart = _restart_audit(
                {"soil_inventory": state.inventory() - full_state.inventory()},
                _tolerance(execution, "restart"),
            )
        return _BenchmarkComputation(
            metrics=criteria,
            conservation_result=conservation,
            restart_result=restart,
            numerical_stability=stability,
            observations={"root_flux": model, "reference": reference},
        )

    def _end_to_end_pathway(self, case: ValidationCase) -> _BenchmarkComputation:
        execution = _execution(case)
        start = _timestamp(execution)
        base_dt, base_steps = _schedule(execution, 1)
        parameters = self._pipeline_parameters(case, execution, base_dt)
        pipeline = V3PipelineRunner(parameters=parameters)
        initial_soil = _soil_state(case, execution, start, _initial_inventory(case, "soil_inventory"))
        initial_tfwt = _tfwt_state(case, execution, start, _initial_inventory(case, "tfwt_inventory"))
        initial_obt = _obt_state(case, execution, start, _initial_inventory(case, "obt_inventory"))

        def forcing(timestamp: datetime) -> AtmosphericHTOForcing:
            return self._atmospheric_forcing(case, execution, timestamp)

        def run(dt: float, steps: int) -> tuple[list[dict[str, float]], V3SimulationState]:
            runner = V3PipelineRunner(
                parameters=self._pipeline_parameters(case, execution, dt)
            )
            state: V3SimulationState | None = None
            observations: list[dict[str, float]] = [
                {
                    "soil": initial_soil.inventory(),
                    "tfwt": initial_tfwt.inventory(),
                    "obt": initial_obt.inventory(),
                    "food": 0.0,
                    "intake": 0.0,
                    "dose": 0.0,
                }
            ]
            for _ in range(steps):
                if state is None:
                    state = runner.run(
                        forcing(start),
                        soil_state=initial_soil,
                        tfwt_state=initial_tfwt,
                        obt_state=initial_obt,
                    )
                else:
                    state = runner.advance(state, forcing(state.timestamp))
                observations.append(
                    {
                        "soil": state.soil_state.inventory(),
                        "tfwt": state.tfwt_state.inventory(),
                        "obt": state.obt_state.inventory(),
                        "food": state.food_state.inventory(),
                        "intake": state.intake_state.inventory(),
                        "dose": state.dose_state.dose(),
                    }
                )
            if state is None:
                raise BenchmarkRunnerError("end-to-end schedule produced no state")
            return observations, state

        factors = _factors(execution)
        schedules = [_schedule(execution, factor) for factor in factors]
        runs = [run(dt, steps) for dt, steps in schedules]
        observations = runs[0][0]
        model_tfwt = [item["tfwt"] for item in observations]
        reference_tfwt = [
            _number(value, field="reference_tfwt_trajectory")
            for value in _value(execution, "reference_tfwt_trajectory", field="execution_definition")
        ]
        if len(reference_tfwt) != len(model_tfwt):
            raise BenchmarkRunnerError(
                "reference_tfwt_trajectory must align with the base schedule"
            )
        first_state = runs[0][1]
        if first_state.ledger is None:
            raise BenchmarkRunnerError("end-to-end state must include a pipeline ledger")
        residuals = {
            "soil": first_state.ledger.soil_balance.residual_bq_m2,
            "root": first_state.ledger.root_balance.residual_bq_m2,
            "tfwt": first_state.ledger.tfwt_balance.residual_bq_m2,
            "obt": first_state.ledger.obt_balance.residual_bq_m2,
            "food": first_state.ledger.food_balance.residual_bq,
        }
        conservation = _audit(residuals, _tolerance(execution, "conservation"))
        criteria = tuple(
            _criterion_metric(
                case,
                criterion,
                model=model_tfwt,
                reference=reference_tfwt,
                conservation=conservation,
            )
            for criterion in case.acceptance_criteria
        )
        final_tfwt = [item[0][-1]["tfwt"] for item in runs]
        stability_value, stability_details = _trend_metric(
            execution,
            [abs(left - right) for left, right in zip(final_tfwt, final_tfwt[1:])],
        )
        expected_leaf_flux = _number(_variable(case, "leaf_exchange_flux"), field="leaf_exchange_flux")
        actual_leaf_flux = first_state.ledger.tfwt_balance.leaf_exchange_input_bq_m2 / base_dt
        leaf_flux_match = abs(actual_leaf_flux - expected_leaf_flux) <= _tolerance(execution, "conservation")
        stability = BenchmarkMetricResult.from_value(
            metric_name="numerical_stability",
            value=stability_value if leaf_flux_match else 1.0,
            threshold=0.0,
            details={
                "expected_leaf_exchange_flux": expected_leaf_flux,
                "actual_leaf_exchange_flux": actual_leaf_flux,
                "leaf_flux_match": leaf_flux_match,
                **stability_details,
            },
        )

        split_steps = int(_value(execution, "restart_split_steps", field="execution_definition"))
        full_state = runs[0][1]
        if split_steps <= 0 or split_steps >= base_steps:
            restart = _restart_audit({"pipeline_state": 0.0}, _tolerance(execution, "restart"))
        else:
            runner = V3PipelineRunner(parameters=parameters)
            state: V3SimulationState | None = None
            for step_index in range(split_steps):
                if state is None:
                    state = runner.run(
                        forcing(start),
                        soil_state=initial_soil,
                        tfwt_state=initial_tfwt,
                        obt_state=initial_obt,
                    )
                else:
                    state = runner.advance(state, forcing(state.timestamp))
            if state is None:
                raise BenchmarkRunnerError("restart split produced no state")
            restored = V3SimulationState.from_json(state.to_json())
            for _ in range(base_steps - split_steps):
                restored = runner.advance(restored, forcing(restored.timestamp))
            restart = _restart_audit(
                {
                    "soil_inventory": restored.soil_state.inventory() - full_state.soil_state.inventory(),
                    "tfwt_inventory": restored.tfwt_state.inventory() - full_state.tfwt_state.inventory(),
                    "obt_inventory": restored.obt_state.inventory() - full_state.obt_state.inventory(),
                    "food_inventory": restored.food_state.inventory() - full_state.food_state.inventory(),
                    "intake_inventory": restored.intake_state.inventory() - full_state.intake_state.inventory(),
                    "dose": restored.dose_state.dose() - full_state.dose_state.dose(),
                },
                _tolerance(execution, "restart"),
            )
        return _BenchmarkComputation(
            metrics=criteria,
            conservation_result=conservation,
            restart_result=restart,
            numerical_stability=stability,
            observations={
                "soil": [item["soil"] for item in observations],
                "tfwt": model_tfwt,
                "obt": [item["obt"] for item in observations],
                "food": [item["food"] for item in observations],
                "intake": [item["intake"] for item in observations],
                "dose": [item["dose"] for item in observations],
                "reference_tfwt": reference_tfwt,
            },
        )

    def _atmospheric_forcing(
        self,
        case: ValidationCase,
        execution: Mapping[str, Any],
        timestamp: datetime,
    ) -> AtmosphericHTOForcing:
        metadata = AtmosphericForcingMetadata(
            model_name=_text(_value(execution, "metadata_model_name", field="execution_definition"), field="metadata_model_name"),
            version=str(_value(execution, "source_version", field="execution_definition")),
            grid_definition=_text(_value(execution, "metadata_grid_definition", field="execution_definition"), field="metadata_grid_definition"),
            time_resolution=_number(_value(execution, "timestep_seconds", field="execution_definition"), field="timestep_seconds"),
            source_dataset=_text(_value(execution, "metadata_source_dataset", field="execution_definition"), field="metadata_source_dataset"),
            creation_time=_timestamp(execution),
            quality_flag=_text(_value(execution, "metadata_quality_flag", field="execution_definition"), field="metadata_quality_flag"),
        )
        return AtmosphericHTOForcing(
            timestamp=timestamp,
            location=_text(_value(execution, "location", field="execution_definition"), field="location"),
            air_hto_concentration=_number(_variable(case, "atmospheric_hto"), field="atmospheric_hto"),
            deposition_flux=_number(_variable(case, "deposition_flux"), field="deposition_flux"),
            temperature=_number(_value(execution, "air_temperature_k", field="execution_definition"), field="air_temperature_k"),
            humidity=_number(_value(execution, "relative_humidity", field="execution_definition"), field="relative_humidity"),
            wind_speed=_number(_value(execution, "wind_speed_m_s", field="execution_definition"), field="wind_speed_m_s"),
            precipitation=_number(_value(execution, "precipitation_m_s", field="execution_definition"), field="precipitation_m_s"),
            source=_text(_value(execution, "metadata_source_dataset", field="execution_definition"), field="metadata_source_dataset"),
            provenance=_runtime_provenance(case, execution),
            metadata=metadata,
        )

    def _pipeline_parameters(
        self,
        case: ValidationCase,
        execution: Mapping[str, Any],
        interval_seconds: float,
    ) -> V3PipelineParameters:
        provenance = _runtime_provenance(case, execution)
        resistance_components = _value(execution, "resistance_components_s_m", field="execution_definition")
        if not isinstance(resistance_components, Sequence) or len(resistance_components) != 3:
            raise BenchmarkRunnerError("resistance_components_s_m must contain three values")
        harvest_fraction = _parameter(case, "harvest_fraction")
        consumption_rate = _parameter(case, "consumption_rate")
        dose_coefficient = _parameter(case, "dose_coefficient")
        return V3PipelineParameters(
            interval_seconds=interval_seconds,
            equilibrium_air_concentration_bq_m3=_number(_value(execution, "equilibrium_air_concentration_bq_m3", field="execution_definition"), field="equilibrium_air_concentration_bq_m3"),
            resistance=ResistanceChain.from_components(
                *(_number(item, field="resistance_components_s_m") for item in resistance_components)
            ),
            soil_parameters=SoilParameters(
                tritium_half_life_s=_number(_value(execution, "soil_half_life_seconds", field="execution_definition"), field="soil_half_life_seconds")
            ),
            root_parameters=RootParameters(k_root_m_s=_parameter(case, "root_coefficient")),
            obt_parameters=OBTParameters(
                kf_s=_parameter(case, "kf_s"),
                kr_s=_parameter(case, "kr_s"),
            ),
            biological_forcing=PlantBiologicalForcing(is_daylight=True),
            root_zone_identifier=_text(_value(execution, "root_zone_identifier", field="execution_definition"), field="root_zone_identifier"),
            harvest_parameters=HarvestParameters(
                plant_identifier=_text(_value(execution, "plant_identifier", field="execution_definition"), field="plant_identifier"),
                crop_identifier=_text(_value(execution, "crop", field="execution_definition"), field="crop"),
                growth_stage=_text(_value(execution, "harvest_growth_stage", field="execution_definition"), field="harvest_growth_stage"),
                food_product_identifier=_text(_value(execution, "food_product_identifier", field="execution_definition"), field="food_product_identifier"),
                harvest_fraction=harvest_fraction,
                harvest_area_m2=_number(_value(execution, "harvest_area_m2", field="execution_definition"), field="harvest_area_m2"),
                tfwt_harvest_fraction=_number(_value(execution, "tfwt_harvest_fraction", field="execution_definition"), field="tfwt_harvest_fraction"),
                provenance=provenance,
            ),
            consumption_parameters=ConsumptionParameters(
                food_product_identifier=_text(_value(execution, "food_product_identifier", field="execution_definition"), field="food_product_identifier"),
                age_group_identifier=_text(_value(execution, "age_group_identifier", field="execution_definition"), field="age_group_identifier"),
                annual_consumption_amount=consumption_rate,
                consumption_unit=CONSUMPTION_RATE_UNIT,
                provenance=provenance,
                food_product_mass_kg=_number(_value(execution, "food_product_mass_kg", field="execution_definition"), field="food_product_mass_kg"),
            ),
            dose_parameters=DoseParameters(
                age_group_identifier=_text(_value(execution, "age_group_identifier", field="execution_definition"), field="age_group_identifier"),
                radionuclide_identifier=_text(_value(execution, "radionuclide_identifier", field="execution_definition"), field="radionuclide_identifier"),
                pathway_identifier=_text(_value(execution, "pathway_identifier", field="execution_definition"), field="pathway_identifier"),
                dose_coefficient=dose_coefficient,
                dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
                provenance=provenance,
            ),
            consumer_identifier=_text(_value(execution, "consumer_identifier", field="execution_definition"), field="consumer_identifier"),
        )


def run_baseline_synthetic_benchmarks() -> BenchmarkRegistry:
    """Convenience entry point used by tests and the report-generation script."""

    registry = SyntheticBenchmarkRunner().run_all()
    if not all(can_accept_synthetic_benchmark(item) for item in registry.results):
        raise BenchmarkRunnerError("P7.7B synthetic benchmark registry failed acceptance")
    return registry


__all__ = [
    "SOLVER_VERSION",
    "BenchmarkRunnerError",
    "SyntheticBenchmarkRunner",
    "run_baseline_synthetic_benchmarks",
]
