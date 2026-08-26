#!/usr/bin/env python3
"""Execute V4 system sensitivity screening R1 against the frozen V3/V3.1 public API.

This is a synthetic/replay software-screening harness. Its finite-difference step
sizes are numerical probes, not physical uncertainty ranges.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

from cteas_ufotri.coupling.atmos_v3 import AtmosphericForcingMetadata, AtmosphericHTOForcing
from cteas_ufotri.exposure.dose_v3 import DOSE_COEFFICIENT_UNIT, DoseParameters
from cteas_ufotri.exposure.intake_v3 import CONSUMPTION_RATE_UNIT, ConsumptionParameters
from cteas_ufotri.plant.food_v3 import HarvestParameters
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance, ResistanceChain
from cteas_ufotri.plant.obt_v3 import OBTParameters, OBTState, PlantBiologicalForcing
from cteas_ufotri.plant.root_v3 import RootParameters
from cteas_ufotri.plant.soil_v3 import SoilParameters, SoilProvenance, SoilState
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.v3_pipeline import V3PipelineParameters, V3PipelineRunner, V3SimulationState


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
INTERVAL_SECONDS = 10.0
PROFILE_FLAGS = {
    "OBT_ONLY_ENDPOINT": [True, True, True, True, True, True],
    "MIXED_OBT_TFWT_ENDPOINT": [True, True, True, True, True, True],
    "DAY_NIGHT_SEQUENCE": [True, True, False, False, True, False],
}
ATMOS_PROVENANCE = ForcingProvenance(
    source_id="v4-screening-synthetic-atmos",
    source_version="r1",
    artifact_sha256="a" * 64,
    spatial_reference="synthetic-screening-point",
    temporal_resolution_s=INTERVAL_SECONDS,
)
SOIL_PROVENANCE = SoilProvenance(
    source_id="v4-screening-synthetic-soil",
    source_version="r1",
    artifact_sha256="b" * 64,
    spatial_reference="synthetic-screening-point",
    temporal_resolution_s=INTERVAL_SECONDS,
)


def baseline_config() -> dict[str, Any]:
    return {
        "air_hto_concentration": 60.0,
        "surface_deposition_flux": 1.0,
        "air_temperature_k": 293.15,
        "relative_humidity": 0.5,
        "wind_speed_m_s": 1.0,
        "precipitation_rate_m_s": 0.0,
        "equilibrium_air_concentration": 10.0,
        "total_resistance": 60.0,
        "soil_layer_depth_m": 0.05,
        "soil_water_content": 0.02,
        "k_root_m_s": 2.0e-4,
        "kf_s": 5.0e-3,
        "kr_s": 1.0e-3,
        "daylight_multiplier": 0.8,
        "nighttime_multiplier": 0.2,
        "biological_temperature_k": None,
        "photosynthetic_activity": None,
        "biological_growth_stage": None,
        "harvest_fraction": 0.6,
        "tfwt_harvest_fraction": 0.3,
        "harvest_area_m2": 1.0,
        "annual_consumption_amount": 1.0,
        "food_product_mass_kg": 1.0,
        "dose_coefficient": 0.2,
        "initial_soil_inventory": 40.0,
        "initial_tfwt_inventory": 5.0,
        "tfwt_water_content_kg_m2": 1.0,
        "initial_obt_inventory": 2.0,
        "obt_plant_mass_kg_m2": 1.0,
        "tritium_half_life_s": 1000.0,
    }


def _forcing(timestamp: datetime, cfg: dict[str, Any]) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        timestamp=timestamp,
        location="v4-screening-point",
        air_hto_concentration=cfg["air_hto_concentration"],
        deposition_flux=cfg["surface_deposition_flux"],
        temperature=cfg["air_temperature_k"],
        humidity=cfg["relative_humidity"],
        wind_speed=cfg["wind_speed_m_s"],
        precipitation=cfg["precipitation_rate_m_s"],
        source="v4-screening-synthetic",
        provenance=ATMOS_PROVENANCE,
        metadata=AtmosphericForcingMetadata(
            model_name="v4-screening-synthetic",
            version="r1",
            grid_definition="point-support",
            time_resolution=INTERVAL_SECONDS,
            source_dataset="repository-controlled-synthetic-screening",
            creation_time=START,
            quality_flag="SYNTHETIC_TEST_ONLY",
        ),
    )


def _initial_states(cfg: dict[str, Any]) -> tuple[SoilState, TFWTState, OBTState]:
    soil = SoilState.from_inventory(
        soil_identifier="v4-screening-soil",
        layer_id="surface",
        layer_depth_m=cfg["soil_layer_depth_m"],
        soil_water_content=cfg["soil_water_content"],
        soil_water_inventory_bq_m2=cfg["initial_soil_inventory"],
        timestamp=START,
        provenance=SOIL_PROVENANCE,
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier="v4-screening-plant",
        crop="synthetic-crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=cfg["initial_tfwt_inventory"],
        water_content_kg_m2=cfg["tfwt_water_content_kg_m2"],
        time=START,
        provenance=ATMOS_PROVENANCE,
    )
    obt = OBTState.from_inventory(
        plant_identifier="v4-screening-plant",
        crop="synthetic-crop",
        growth_stage="vegetative",
        obt_inventory_bq_m2=cfg["initial_obt_inventory"],
        plant_mass_kg_m2=cfg["obt_plant_mass_kg_m2"],
        timestamp=START,
        provenance=ATMOS_PROVENANCE,
    )
    return soil, tfwt, obt


def _runner(cfg: dict[str, Any], *, is_daylight: bool, tfwt_fraction: float) -> V3PipelineRunner:
    resistance = ResistanceChain.from_components(
        cfg["total_resistance"] / 3.0,
        cfg["total_resistance"] / 3.0,
        cfg["total_resistance"] / 3.0,
    )
    params = V3PipelineParameters(
        interval_seconds=INTERVAL_SECONDS,
        equilibrium_air_concentration_bq_m3=cfg["equilibrium_air_concentration"],
        resistance=resistance,
        soil_parameters=SoilParameters(tritium_half_life_s=cfg["tritium_half_life_s"]),
        root_parameters=RootParameters(k_root_m_s=cfg["k_root_m_s"]),
        obt_parameters=OBTParameters(
            kf_s=cfg["kf_s"],
            kr_s=cfg["kr_s"],
            daylight_multiplier=cfg["daylight_multiplier"],
            nighttime_multiplier=cfg["nighttime_multiplier"],
        ),
        biological_forcing=PlantBiologicalForcing(
            is_daylight=is_daylight,
            temperature_k=cfg["biological_temperature_k"],
            photosynthetic_activity=cfg["photosynthetic_activity"],
            growth_stage=cfg["biological_growth_stage"],
        ),
        root_zone_identifier="v4-screening-root-zone",
        harvest_parameters=HarvestParameters(
            plant_identifier="v4-screening-plant",
            crop_identifier="synthetic-crop",
            growth_stage="harvest",
            food_product_identifier="synthetic-food",
            harvest_fraction=cfg["harvest_fraction"],
            harvest_area_m2=cfg["harvest_area_m2"],
            tfwt_harvest_fraction=tfwt_fraction,
            provenance=ATMOS_PROVENANCE,
        ),
        consumption_parameters=ConsumptionParameters(
            food_product_identifier="synthetic-food",
            age_group_identifier="adult",
            annual_consumption_amount=cfg["annual_consumption_amount"],
            consumption_unit=CONSUMPTION_RATE_UNIT,
            provenance=ATMOS_PROVENANCE,
            food_product_mass_kg=cfg["food_product_mass_kg"],
        ),
        dose_parameters=DoseParameters(
            age_group_identifier="adult",
            radionuclide_identifier="H-3",
            pathway_identifier="food-ingestion",
            dose_coefficient=cfg["dose_coefficient"],
            dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
            provenance=ATMOS_PROVENANCE,
        ),
        consumer_identifier="v4-screening-consumer",
    )
    return V3PipelineRunner(parameters=params)


def _tfwt_fraction(profile_id: str, cfg: dict[str, Any]) -> float:
    return 0.0 if profile_id == "OBT_ONLY_ENDPOINT" else cfg["tfwt_harvest_fraction"]


def _state_outputs(state: V3SimulationState) -> dict[str, float]:
    return {
        "final_committed_dose_sv": state.dose_state.dose(),
        "final_food_total_inventory_bq": state.food_state.inventory(),
        "final_food_obt_inventory_bq": state.food_state.obt_inventory_bq,
        "final_food_tfwt_inventory_bq": state.food_state.tfwt_inventory_bq,
        "final_soil_inventory_bq_m2": state.soil_state.inventory(),
        "final_tfwt_inventory_bq_m2": state.tfwt_state.inventory(),
        "final_obt_inventory_bq_m2": state.obt_state.inventory(),
    }


def run_profile(
    profile_id: str,
    cfg: dict[str, Any] | None = None,
    *,
    restart_split_step: int | None = None,
) -> dict[str, Any]:
    if profile_id not in PROFILE_FLAGS:
        raise ValueError(f"unknown profile_id {profile_id!r}")
    cfg = deepcopy(baseline_config() if cfg is None else cfg)
    flags = PROFILE_FLAGS[profile_id]
    tfwt_fraction = _tfwt_fraction(profile_id, cfg)
    soil, tfwt, obt = _initial_states(cfg)
    current: V3SimulationState | None = None
    per_step: list[dict[str, float]] = []

    for index, is_daylight in enumerate(flags):
        timestamp = START if current is None else current.timestamp
        runner = _runner(cfg, is_daylight=is_daylight, tfwt_fraction=tfwt_fraction)
        forcing = _forcing(timestamp, cfg)
        if current is None:
            current = runner.run(
                forcing,
                soil_state=soil,
                tfwt_state=tfwt,
                obt_state=obt,
            )
        else:
            current = runner.advance(current, forcing)
        if restart_split_step is not None and index + 1 == restart_split_step:
            current = V3SimulationState.from_json(current.to_json())
        ledger = current.ledger
        assert ledger is not None
        per_step.append(
            {
                "root_transfer_bq_m2": current.root_state.inventory(),
                "leaf_exchange_input_bq_m2": ledger.tfwt_balance.leaf_exchange_input_bq_m2,
                "obt_formation_bq_m2": ledger.obt_balance.obt_formation_bq_m2,
                "soil_balance_residual_bq_m2": ledger.soil_balance.residual_bq_m2,
                "root_balance_residual_bq_m2": ledger.root_balance.residual_bq_m2,
                "tfwt_balance_residual_bq_m2": ledger.tfwt_balance.residual_bq_m2,
                "obt_balance_residual_bq_m2": ledger.obt_balance.residual_bq_m2,
                "food_balance_residual_bq": ledger.food_balance.residual_bq,
            }
        )
    assert current is not None
    return {"outputs": _state_outputs(current), "per_step": per_step}


STRUCTURAL_ZERO_CASES = {
    "atmos.temperature": ("air_temperature_k", 310.0),
    "atmos.relative_humidity": ("relative_humidity", 0.9),
    "atmos.wind_speed": ("wind_speed_m_s", 5.0),
    "atmos.precipitation_rate": ("precipitation_rate_m_s", 1.0e-6),
    "soil.layer_depth": ("soil_layer_depth_m", 0.2),
    "tfwt.water_content": ("tfwt_water_content_kg_m2", 2.0),
    "obt.plant_mass": ("obt_plant_mass_kg_m2", 2.0),
    "obt.photosynthetic_activity": ("photosynthetic_activity", 0.9),
    "obt.temperature_response": ("biological_temperature_k", 310.0),
    "obt.growth_stage_response": ("biological_growth_stage", "flowering"),
}

LOCAL_INPUTS = {
    "atmos.air_hto_concentration": "air_hto_concentration",
    "atmos.surface_deposition_flux": "surface_deposition_flux",
    "leaf.equilibrium_air_concentration": "equilibrium_air_concentration",
    "leaf.total_resistance": "total_resistance",
    "soil.water_content": "soil_water_content",
    "root.k_root": "k_root_m_s",
    "obt.kf": "kf_s",
    "obt.kr": "kr_s",
    "obt.daylight_multiplier": "daylight_multiplier",
    "obt.nighttime_multiplier": "nighttime_multiplier",
    "food.harvest_fraction": "harvest_fraction",
    "food.tfwt_harvest_fraction": "tfwt_harvest_fraction",
    "initial.soil_inventory": "initial_soil_inventory",
    "initial.tfwt_inventory": "initial_tfwt_inventory",
    "initial.obt_inventory": "initial_obt_inventory",
}
LOCAL_METRICS = [
    "final_committed_dose_sv",
    "final_food_total_inventory_bq",
    "final_soil_inventory_bq_m2",
    "final_tfwt_inventory_bq_m2",
    "final_obt_inventory_bq_m2",
]
FINITE_DIFFERENCE_STEPS = [0.01, 0.005]
CONVERGENCE_ABS_TOL = 1.0e-3


def _elasticity(input_name: str, relative_step: float) -> dict[str, float]:
    key = LOCAL_INPUTS[input_name]
    cfg = baseline_config()
    x0 = cfg[key]
    if not isinstance(x0, (int, float)) or x0 <= 0.0:
        raise ValueError(f"{input_name} requires a positive baseline for symmetric screening")
    minus = deepcopy(cfg)
    plus = deepcopy(cfg)
    minus[key] = x0 * (1.0 - relative_step)
    plus[key] = x0 * (1.0 + relative_step)
    y0 = run_profile("DAY_NIGHT_SEQUENCE", cfg)["outputs"]
    ym = run_profile("DAY_NIGHT_SEQUENCE", minus)["outputs"]
    yp = run_profile("DAY_NIGHT_SEQUENCE", plus)["outputs"]
    result: dict[str, float] = {}
    for metric in LOCAL_METRICS:
        if y0[metric] == 0.0:
            raise ValueError(f"{metric} has zero baseline; elasticity is undefined")
        result[metric] = (yp[metric] - ym[metric]) / (2.0 * relative_step * y0[metric])
    return result


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def execute_screening() -> dict[str, Any]:
    cfg = baseline_config()
    profiles = {
        profile_id: run_profile(profile_id, cfg)
        for profile_id in PROFILE_FLAGS
    }

    repeat_profiles = {
        profile_id: run_profile(profile_id, cfg)
        for profile_id in PROFILE_FLAGS
    }
    deterministic_repeat_equal = profiles == repeat_profiles

    structural_zero: dict[str, Any] = {}
    zero_reference = run_profile("DAY_NIGHT_SEQUENCE", cfg)["outputs"]
    for input_name, (key, value) in STRUCTURAL_ZERO_CASES.items():
        altered = deepcopy(cfg)
        altered[key] = value
        outputs = run_profile("DAY_NIGHT_SEQUENCE", altered)["outputs"]
        deltas = {metric: outputs[metric] - zero_reference[metric] for metric in zero_reference}
        structural_zero[input_name] = {
            "max_abs_output_delta": max(abs(value) for value in deltas.values()),
            "pass": all(delta == 0.0 for delta in deltas.values()),
        }

    local_response: dict[str, Any] = {}
    for input_name in LOCAL_INPUTS:
        by_step = {
            f"{step:.6g}": _elasticity(input_name, step)
            for step in FINITE_DIFFERENCE_STEPS
        }
        coarse = by_step[f"{FINITE_DIFFERENCE_STEPS[0]:.6g}"]
        fine = by_step[f"{FINITE_DIFFERENCE_STEPS[1]:.6g}"]
        max_delta = max(abs(coarse[m] - fine[m]) for m in LOCAL_METRICS)
        local_response[input_name] = {
            "elasticity_by_relative_step": by_step,
            "max_abs_step_change": max_delta,
            "converged": max_delta <= CONVERGENCE_ABS_TOL,
            "interpretation": "LOCAL_COMPUTATIONAL_INFLUENCE_NOT_PHYSICAL_UNCERTAINTY",
        }

    uninterrupted = run_profile("DAY_NIGHT_SEQUENCE", cfg)
    restarted = run_profile("DAY_NIGHT_SEQUENCE", cfg, restart_split_step=3)
    restart_equivalence = uninterrupted == restarted

    max_abs_residual = 0.0
    finite_nonnegative = True
    for profile in profiles.values():
        for step in profile["per_step"]:
            for name, value in step.items():
                if "residual" in name:
                    max_abs_residual = max(max_abs_residual, abs(value))
        for name, value in profile["outputs"].items():
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                finite_nonnegative = False
            if name in {
                "final_food_total_inventory_bq",
                "final_food_obt_inventory_bq",
                "final_food_tfwt_inventory_bq",
                "final_soil_inventory_bq_m2",
                "final_tfwt_inventory_bq_m2",
                "final_obt_inventory_bq_m2",
            } and value < 0.0:
                finite_nonnegative = False

    external_scaling: dict[str, Any] = {}
    base_dose = profiles["DAY_NIGHT_SEQUENCE"]["outputs"]["final_committed_dose_sv"]
    for name, key, expected in [
        ("intake.annual_consumption_amount", "annual_consumption_amount", 1.0),
        ("intake.food_product_mass", "food_product_mass_kg", -1.0),
        ("dose.dose_coefficient", "dose_coefficient", 1.0),
        ("food.harvest_area", "harvest_area_m2", 1.0),
    ]:
        h = 0.005
        minus = deepcopy(cfg)
        plus = deepcopy(cfg)
        minus[key] = cfg[key] * (1.0 - h)
        plus[key] = cfg[key] * (1.0 + h)
        ym = run_profile("DAY_NIGHT_SEQUENCE", minus)["outputs"]["final_committed_dose_sv"]
        yp = run_profile("DAY_NIGHT_SEQUENCE", plus)["outputs"]["final_committed_dose_sv"]
        elasticity = (yp - ym) / (2.0 * h * base_dose)
        external_scaling[name] = {
            "dose_elasticity": elasticity,
            "expected_relation_elasticity": expected,
            "classification": "EXTERNAL_SCENARIO_OR_GEOMETRY_ONLY",
        }

    all_local_converged = all(item["converged"] for item in local_response.values())
    all_structural_zero_pass = all(item["pass"] for item in structural_zero.values())
    pass_gate = (
        deterministic_repeat_equal
        and all_local_converged
        and all_structural_zero_pass
        and restart_equivalence
        and max_abs_residual <= 1.0e-9
        and finite_nonnegative
    )

    return {
        "schema_version": "v1",
        "stage": "V4_SYSTEM_SENSITIVITY_SCREENING_EXECUTION_R1",
        "status": "PASS_SOFTWARE_SCREENING" if pass_gate else "FAIL_SOFTWARE_SCREENING",
        "source_kind": "SYNTHETIC_TEST_ONLY",
        "physical_uncertainty_ranking": "NOT_AVAILABLE",
        "empirical_validation": False,
        "finite_difference_steps": FINITE_DIFFERENCE_STEPS,
        "finite_difference_steps_are_physical_uncertainty": False,
        "convergence_abs_tolerance": CONVERGENCE_ABS_TOL,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "git_head": _git_head(),
        },
        "profiles": profiles,
        "structural_zero_verification": structural_zero,
        "local_numeric_response": local_response,
        "external_endpoint_scaling": external_scaling,
        "invariants": {
            "deterministic_repeat_equal": deterministic_repeat_equal,
            "restart_equivalence": restart_equivalence,
            "max_abs_balance_residual": max_abs_residual,
            "finite_nonnegative_continuous_inventories": finite_nonnegative,
            "all_structural_zero_checks_pass": all_structural_zero_pass,
            "all_local_response_steps_converged": all_local_converged,
        },
        "hard_boundaries": {
            "production_src_changed": False,
            "solver_physics_changed": False,
            "numerical_coupling_changed": False,
            "parameter_activation": False,
            "calibration": False,
            "real_cteas_atmos_binding": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = execute_screening()
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print("V4_SCREENING_STATUS=" + result["status"])
    print("V4_SCREENING_RESULT_JSON=" + json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "PASS_SOFTWARE_SCREENING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
