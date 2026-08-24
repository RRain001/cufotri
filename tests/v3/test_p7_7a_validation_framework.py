"""P7.7A schema, metric, result, benchmark, and gate tests."""

from dataclasses import replace
import json
from pathlib import Path

import jsonschema
import pytest

from cteas_ufotri.validation_v3 import (
    ConservationLedger,
    ParameterStatus,
    ScenarioType,
    ValidationCase,
    ValidationCaseError,
    ValidationResult,
    can_enter_validation,
    compute_metric,
    conservation_residual,
    decay_error,
    load_baseline_benchmark_cases,
    mae,
    relative_error,
    rmse,
    state_difference,
    trajectory_comparison,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/v3/validation/p7_7a_baseline_benchmarks.yaml"
SCHEMA = ROOT / "schemas/v3/validation_case.schema.json"


def test_baseline_manifest_defines_five_cases_and_gate_allows_them() -> None:
    cases = load_baseline_benchmark_cases(CONFIG)

    assert len(cases) == 5
    assert {case.scenario_type for case in cases} == {
        ScenarioType.SYNTHETIC_BENCHMARK
    }
    assert all(can_enter_validation(case) for case in cases)
    assert all(
        parameter.status is ParameterStatus.TEST_ONLY
        for case in cases
        for parameter in case.parameter_context
    )


def test_case_round_trip_preserves_named_inputs_and_provenance() -> None:
    case = load_baseline_benchmark_cases(CONFIG)[0]
    restored = ValidationCase.from_mapping(case.to_mapping())

    assert restored == case
    assert restored.case_id.startswith("v3-p7-7a-")
    assert restored.forcing_definition["forcing_id"]
    assert restored.initial_state["state_id"]
    assert restored.provenance.artifact_sha256


def test_case_rejects_anonymous_forcing_and_hidden_parameter_mapping() -> None:
    raw = load_baseline_benchmark_cases(CONFIG)[0].to_mapping()
    raw["forcing_definition"].pop("forcing_id")
    with pytest.raises(ValidationCaseError, match="forcing_id"):
        ValidationCase.from_mapping(raw)

    raw = load_baseline_benchmark_cases(CONFIG)[0].to_mapping()
    raw["parameter_context"] = [
        {
            "parameter_id": "hidden",
            "value": {"value": 1.0},
            "unit": "1",
            "status": "TEST_ONLY",
            "provenance": raw["provenance"],
        }
    ]
    with pytest.raises(ValidationCaseError, match="hidden mapping"):
        ValidationCase.from_mapping(raw)


def test_json_schema_accepts_every_declared_case() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    cases = load_baseline_benchmark_cases(CONFIG)

    for case in cases:
        jsonschema.validate(instance=case.to_mapping(), schema=schema)


def test_numerical_metrics_are_explicit_and_aligned() -> None:
    model = [1.0, 2.0, 4.0]
    reference = [1.0, 3.0, 4.0]

    assert rmse(model, reference) == pytest.approx((1.0 / 3.0) ** 0.5)
    assert mae(model, reference) == pytest.approx(1.0 / 3.0)
    assert relative_error(9.0, 10.0) == pytest.approx(0.1)
    assert trajectory_comparison(model, reference) == rmse(model, reference)
    assert decay_error(model, reference) == pytest.approx(0.0)
    assert state_difference(model, reference) == pytest.approx(1.0)
    assert compute_metric("MAE", model, reference) == pytest.approx(1.0 / 3.0)

    with pytest.raises(ValueError, match="align"):
        rmse([1.0], [1.0, 2.0])


def test_conservation_metric_preserves_recorded_ledger() -> None:
    ledger = ConservationLedger(
        input_inventory=10.0,
        output_inventory=3.0,
        storage_change=7.0,
        residual=0.0,
    )

    assert conservation_residual(10.0, 3.0, 7.0) == pytest.approx(0.0)
    assert ledger.calculated_residual == pytest.approx(0.0)
    assert ledger.residual == pytest.approx(0.0)
    assert ledger.residual_difference == pytest.approx(0.0)
    assert compute_metric("conservation_residual", ledger) == pytest.approx(0.0)


def test_validation_result_requires_provenance_and_consistent_pass_fail() -> None:
    case = load_baseline_benchmark_cases(CONFIG)[0]
    result = ValidationResult.from_metric(
        case_id=case.case_id,
        metric_name="RMSE",
        value=0.1,
        threshold=0.2,
        uncertainty=0.01,
        execution_hash="a" * 64,
        solver_version="synthetic-harness-v1",
        parameter_snapshot=case.parameter_context,
        unit="Bq m^-2",
    )

    assert result.pass_fail is True
    assert ValidationResult.from_mapping(result.to_mapping()) == result

    with pytest.raises(ValueError, match="does not match"):
        ValidationResult(
            case_id=case.case_id,
            metric_name="RMSE",
            value=0.1,
            threshold=0.2,
            pass_fail=False,
            uncertainty=None,
            execution_hash="a" * 64,
            solver_version="synthetic-harness-v1",
            parameter_snapshot=case.parameter_context,
        )


def test_gate_blocks_active_parameter_and_physical_validation_paths() -> None:
    case = load_baseline_benchmark_cases(CONFIG)[0]
    parameter = replace(
        case.parameter_context[0],
        status=ParameterStatus.ACTIVE,
    )
    active_case = replace(case, parameter_context=(parameter,))

    assert can_enter_validation(active_case) is False
    assert can_enter_validation(case, active_parameters=1) is False
    assert can_enter_validation(case, calibration_started=True) is False
    assert can_enter_validation(case, ufotri_active_database=True) is False
    assert can_enter_validation(case, v3_physics_ready=True) is False

    physical_case = replace(
        case,
        scenario_type=ScenarioType.EMPIRICAL_OBSERVATION,
    )
    assert can_enter_validation(physical_case) is False
