#!/usr/bin/env python3
"""Run preregistered validation-only SB1 mechanism discrimination."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import yaml


ROOT = Path(__file__).resolve().parents[4]
MECHANISM_ROOT = (
    ROOT / "validation" / "benchmarks" / "emras_soybean_sb1_mechanisms"
)
SB1_ROOT = ROOT / "validation" / "benchmarks" / "emras_soybean_sb1"
REPORTS = MECHANISM_ROOT / "reports"
PROTOCOL_PATH = (
    MECHANISM_ROOT
    / "preregistration"
    / "sb1_mechanism_discrimination_protocol.yaml"
)
LOCAL_OUTPUTS = (
    ROOT
    / "validation"
    / "external_local"
    / "emras_soybean_sb1"
    / "outputs"
    / "mechanism_discrimination"
)

sys.path.insert(0, str(SB1_ROOT / "scripts"))
sys.path.insert(0, str(MECHANISM_ROOT))
sys.path.insert(0, str(MECHANISM_ROOT / "scripts"))
import run_sb1_benchmark as sb1  # noqa: E402
from evaluate_mechanism_metrics import (  # noqa: E402
    evaluate_primary_success,
    late_improvement,
    log_metrics,
)
from models import (  # noqa: E402
    current_single_pool,
    dynamic_water_storage,
    obt_recycle,
    parallel_fast_slow,
    reversible_fast_slow,
)
from verify_mechanism_mass_balance import summarize_mass_balance  # noqa: E402


CANDIDATES = (
    "H0_CURRENT_SINGLE_POOL",
    "H1_DYNAMIC_WATER_STORAGE",
    "H2_PARALLEL_FAST_SLOW_RESIDUAL",
    "H3_REVERSIBLE_FAST_SLOW_EXCHANGE",
    "H4_OBT_MEDIATED_RECYCLE",
)
FROZEN_LEAF_PARAMETERS = {
    "leaf_stomatal_resistance_day_s_m": 800.0,
    "leaf_characteristic_length_m": 0.10,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("calibrate", "late"),
        required=True,
        help="Late is refused until calibration parameters are tracked.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping: {path}")
    return value


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
    ).hexdigest()


def git_output(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def protocol_commit() -> str:
    return git_output(
        "log", "-1", "--format=%H", "--", str(PROTOCOL_PATH.relative_to(ROOT))
    )


def model_config(
    mechanism_id: str, parameters: dict[str, float]
) -> dict[str, Any]:
    config = sb1.model_config(FROZEN_LEAF_PARAMETERS)
    if mechanism_id == "H4_OBT_MEDIATED_RECYCLE":
        config = obt_recycle.apply_multipliers(
            config,
            parameters["formation_multiplier"],
            parameters["turnover_multiplier"],
        )
    return config


def observed_body_tfwt_bq_l(
    mechanism_id: str,
    fast_inventory_bq_m2: float,
    slow_inventory_bq_m2: float,
    time_local: pd.Timestamp,
    parameters: dict[str, float],
) -> float:
    if mechanism_id == "H1_DYNAMIC_WATER_STORAGE":
        duration = (sb1.HARVEST - sb1.EXPOSURE_END).total_seconds()
        return dynamic_water_storage.concentration_bq_l(
            fast_inventory_bq_m2,
            max((time_local - sb1.EXPOSURE_END).total_seconds(), 0.0),
            duration,
            parameters.get(
                "storage_shape", "LINEAR_EXPOSURE_TO_HARVEST"
            ),
        )
    if mechanism_id in {
        "H2_PARALLEL_FAST_SLOW_RESIDUAL",
        "H3_REVERSIBLE_FAST_SLOW_EXCHANGE",
    }:
        inventory = fast_inventory_bq_m2 + slow_inventory_bq_m2
    else:
        inventory = current_single_pool.observed_inventory_bq_m2(
            fast_inventory_bq_m2
        )
    return inventory / sb1.EXPOSURE_BODY_WATER_M / 1000.0


def simulate(
    forcing: pd.DataFrame,
    mechanism_id: str,
    parameters: dict[str, float],
    maximum_hours_after_exposure: float,
) -> pd.DataFrame:
    if mechanism_id not in CANDIDATES:
        raise ValueError(f"Unknown mechanism: {mechanism_id}")
    config = model_config(mechanism_id, parameters)
    physics = config["physics"]
    state = sb1.State(config["soil"]["initial_water_m"])
    slow_inventory = 0.0
    end_time = sb1.EXPOSURE_END + pd.Timedelta(
        hours=maximum_hours_after_exposure
    )
    rows: list[dict[str, Any]] = [
        {
            "time_utc": forcing.iloc[0]["time_utc"],
            "hours_after_exposure": -1.0,
            "plant_body_tfwt_bq_l_water": 0.0,
            "pods_tfwt_bq_l_water": 0.0,
            "plant_body_obt_bq_l_combustion_water": 0.0,
            "pods_obt_bq_l_combustion_water": 0.0,
            "plant_fast_tfwt_inventory_bq_m2": 0.0,
            "plant_slow_tfwt_inventory_bq_m2": 0.0,
            "plant_total_tfwt_inventory_bq_m2": 0.0,
            "plant_obt_inventory_bq_m2": 0.0,
            "pods_tfwt_inventory_bq_m2": 0.0,
            "pods_obt_inventory_bq_m2": 0.0,
            "formal_mass_closure_abs_bq_m2": 0.0,
            "internal_transfer_residual_abs_bq_m2": 0.0,
            "slow_decay_bq_m2": 0.0,
        }
    ]
    for index in range(1, len(forcing)):
        current = forcing.iloc[index]
        previous = forcing.iloc[index - 1]
        time_local = current["time_local"]
        if time_local > end_time:
            break
        temperature_k = (
            0.5
            * (
                previous["air_temperature_c"]
                + current["air_temperature_c"]
            )
            + 273.15
        )
        dewpoint_k = (
            0.5
            * (
                previous["dewpoint_temperature_c"]
                + current["dewpoint_temperature_c"]
            )
            + 273.15
        )
        wind = 0.5 * (
            previous["wind_speed_m_s"] + current["wind_speed_m_s"]
        )
        shortwave = 0.5 * (
            previous["shortwave_down_w_m2"]
            + current["shortwave_down_w_m2"]
        )
        net_radiation = (
            physics["fallback_shortwave_absorptivity"] * shortwave
            - physics["fallback_net_longwave_loss_w_m2"]
        )
        pet, radiation_pet, aerodynamic_pet = (
            sb1.penman_ufotri_components_m_s(
                temperature_k,
                dewpoint_k,
                wind,
                net_radiation,
                physics["latent_heat_j_kg"],
                physics["water_density_kg_m3"],
                physics["psychrometric_constant_pa_k"],
                physics["penman_aerodynamic_coefficient_w_m2_pa"],
            )
        )
        lai = sb1.soybean_lai(time_local)
        water_fluxes = sb1.partition_evapotranspiration(
            pet,
            lai,
            state.soil_water_m,
            config["soil"]["maximum_water_m"],
            config["soil"]["wilting_water_m"],
            config["evapotranspiration"]["lai_shading_mode"],
            radiation_pet,
            aerodynamic_pet,
        )
        precipitation_m_s = (
            float(current["precipitation_mm_interval"])
            / 1000.0
            / sb1.DT_SECONDS
        )
        cloud = 0.5 * (
            previous["total_cloud_cover_fraction"]
            + current["total_cloud_cover_fraction"]
        )
        stability = sb1.classify_pasquill_gifford(
            wind, net_radiation, cloud
        )
        air_hto = 0.5 * (
            previous["air_hto_bq_m3"] + current["air_hto_bq_m3"]
        )
        pod_active = time_local >= sb1.POD_START
        allocation_rate = (
            config["crops"]["parameters"]["generic_crop"][
                "edible_allocation_rate_s"
            ]
            if pod_active
            else 0.0
        )
        state, diagnostics = sb1.advance(
            state,
            sb1.DT_SECONDS,
            air_hto,
            precipitation_m_s,
            water_fluxes.soil_evaporation_m_s,
            water_fluxes.plant_transpiration_m_s,
            config,
            rain_hto_concentration_bq_m3=0.0,
            root_uptake_m_s=0.0,
            elapsed_since_release_s=max(
                (time_local - sb1.EXPOSURE_START).total_seconds(), 0.0
            ),
            is_day=shortwave > 0.0,
            air_temperature_k=temperature_k,
            dewpoint_temperature_k=dewpoint_k,
            wind_speed_m_s=wind,
            stability_class=stability,
            leaf_area_index=lai,
            edible_allocation_rate_s=allocation_rate,
            root_activity_fraction=0.0,
        )
        internal_residual = 0.0
        slow_decay = 0.0
        if mechanism_id == "H2_PARALLEL_FAST_SLOW_RESIDUAL":
            transfer = parallel_fast_slow.transfer(
                state.plant_tfwt_bq_m2,
                slow_inventory,
                diagnostics.leaf_uptake_bq_m2_s,
                parameters["slow_capture_fraction"],
                parameters["slow_release_rate_s"],
                physics["tritium_decay_constant_s"],
                sb1.DT_SECONDS,
            )
            state = replace(
                state,
                plant_tfwt_bq_m2=transfer.fast_inventory_bq_m2,
            )
            slow_inventory = transfer.slow_inventory_bq_m2
            internal_residual = transfer.internal_transfer_residual_bq_m2
            slow_decay = transfer.slow_decay_bq_m2
        elif mechanism_id == "H3_REVERSIBLE_FAST_SLOW_EXCHANGE":
            transfer = reversible_fast_slow.transfer(
                state.plant_tfwt_bq_m2,
                slow_inventory,
                parameters["fast_to_slow_rate_s"],
                parameters["slow_to_fast_rate_s"],
                physics["tritium_decay_constant_s"],
                sb1.DT_SECONDS,
            )
            state = replace(
                state,
                plant_tfwt_bq_m2=transfer.fast_inventory_bq_m2,
            )
            slow_inventory = transfer.slow_inventory_bq_m2
            internal_residual = transfer.internal_transfer_residual_bq_m2
            slow_decay = transfer.slow_decay_bq_m2

        pod_fraction = sb1.growth_fraction(
            time_local, sb1.POD_START, sb1.HARVEST
        )
        pod_fresh_kg_m2 = (
            sb1.HARVEST_POD_FRESH_G_M2 / 1000.0 * pod_fraction
        )
        pod_water_fraction = (
            (
                sb1.HARVEST_POD_FRESH_G_M2
                - sb1.HARVEST_POD_DRY_G_M2
            )
            / sb1.HARVEST_POD_FRESH_G_M2
        )
        edible = sb1.edible_concentrations(
            state.edible_tfwt_bq_m2,
            state.edible_obt_bq_m2,
            pod_fresh_kg_m2,
            pod_water_fraction,
            physics["water_density_kg_m3"],
        )
        body_dry = sb1.EXPOSURE_BODY_DRY_G_M2 + sb1.growth_fraction(
            time_local, sb1.EXPOSURE_END, sb1.HARVEST
        ) * (sb1.HARVEST_BODY_DRY_G_M2 - sb1.EXPOSURE_BODY_DRY_G_M2)
        body_combustion_l = (
            body_dry * sb1.COMBUSTION_WATER_ML_PER_G_DRY / 1000.0
        )
        pod_combustion_l = (
            sb1.HARVEST_POD_DRY_G_M2
            * pod_fraction
            * sb1.COMBUSTION_WATER_ML_PER_G_DRY
            / 1000.0
        )
        rows.append(
            {
                "time_utc": current["time_utc"],
                "hours_after_exposure": (
                    time_local - sb1.EXPOSURE_END
                ).total_seconds()
                / 3600.0,
                "plant_body_tfwt_bq_l_water": observed_body_tfwt_bq_l(
                    mechanism_id,
                    state.plant_tfwt_bq_m2,
                    slow_inventory,
                    time_local,
                    parameters,
                ),
                "pods_tfwt_bq_l_water": (
                    edible.tfwt_bq_m3_water / 1000.0
                    if pod_fraction > 0
                    else 0.0
                ),
                "plant_body_obt_bq_l_combustion_water": (
                    state.plant_obt_bq_m2 / body_combustion_l
                    if body_combustion_l > 0
                    else 0.0
                ),
                "pods_obt_bq_l_combustion_water": (
                    state.edible_obt_bq_m2 / pod_combustion_l
                    if pod_combustion_l > 0
                    else 0.0
                ),
                "plant_fast_tfwt_inventory_bq_m2": (
                    state.plant_tfwt_bq_m2
                ),
                "plant_slow_tfwt_inventory_bq_m2": slow_inventory,
                "plant_total_tfwt_inventory_bq_m2": (
                    state.plant_tfwt_bq_m2 + slow_inventory
                ),
                "plant_obt_inventory_bq_m2": state.plant_obt_bq_m2,
                "pods_tfwt_inventory_bq_m2": state.edible_tfwt_bq_m2,
                "pods_obt_inventory_bq_m2": state.edible_obt_bq_m2,
                "formal_mass_closure_abs_bq_m2": abs(
                    diagnostics.surface_box_mass_closure.residual_bq_m2
                ),
                "internal_transfer_residual_abs_bq_m2": abs(
                    internal_residual
                ),
                "slow_decay_bq_m2": slow_decay,
            }
        )
    frame = pd.DataFrame(rows)
    numeric = frame.select_dtypes(include=[np.number])
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError(f"{mechanism_id} produced NaN or Inf")
    inventories = numeric.filter(regex="_inventory_bq_m2$")
    concentrations = numeric.filter(regex="_bq_l_")
    if (inventories.to_numpy() < -1.0e-12).any():
        raise ValueError(f"{mechanism_id} produced negative inventory")
    if (concentrations.to_numpy() < -1.0e-12).any():
        raise ValueError(f"{mechanism_id} produced negative concentration")
    return frame


def sample_predictions(
    model: pd.DataFrame, observed: pd.DataFrame
) -> pd.DataFrame:
    return sb1.sample_predictions(model, observed)


def calibration_observations() -> pd.DataFrame:
    observed = sb1.observations()
    return observed[
        (observed["compartment"] == "plant_body")
        & observed["hours_after_exposure"].isin([0.2, 1, 24, 120, 336])
    ].copy()


def candidate_grid(
    mechanism_id: str, protocol: dict[str, Any]
) -> list[dict[str, float]]:
    candidate = protocol["candidates"][mechanism_id]
    if mechanism_id in {
        "H0_CURRENT_SINGLE_POOL",
        "H1_DYNAMIC_WATER_STORAGE",
    }:
        return [{}]
    if mechanism_id == "H2_PARALLEL_FAST_SLOW_RESIDUAL":
        first = candidate["parameters"]["slow_capture_fraction"]["values"]
        second = candidate["parameters"]["slow_release_rate_s"]["values"]
        names = ("slow_capture_fraction", "slow_release_rate_s")
    elif mechanism_id == "H3_REVERSIBLE_FAST_SLOW_EXCHANGE":
        first = candidate["common_rate_values_s"]
        second = candidate["common_rate_values_s"]
        names = ("fast_to_slow_rate_s", "slow_to_fast_rate_s")
    else:
        first = candidate["parameters"]["formation_multiplier"]["values"]
        second = candidate["parameters"]["turnover_multiplier"]["values"]
        names = ("formation_multiplier", "turnover_multiplier")
    return [
        {names[0]: float(a), names[1]: float(b)}
        for a, b in itertools.product(first, second)
    ]


def parameter_names(mechanism_id: str) -> tuple[str, ...]:
    return {
        "H0_CURRENT_SINGLE_POOL": (),
        "H1_DYNAMIC_WATER_STORAGE": (),
        "H2_PARALLEL_FAST_SLOW_RESIDUAL": (
            "slow_capture_fraction",
            "slow_release_rate_s",
        ),
        "H3_REVERSIBLE_FAST_SLOW_EXCHANGE": (
            "fast_to_slow_rate_s",
            "slow_to_fast_rate_s",
        ),
        "H4_OBT_MEDIATED_RECYCLE": (
            "formation_multiplier",
            "turnover_multiplier",
        ),
    }[mechanism_id]


def parameter_values(
    mechanism_id: str, protocol: dict[str, Any]
) -> dict[str, list[float]]:
    grid = candidate_grid(mechanism_id, protocol)
    return {
        name: sorted({float(row[name]) for row in grid})
        for name in parameter_names(mechanism_id)
    }


def identify_parameters(
    mechanism_id: str,
    protocol: dict[str, Any],
    evaluations: list[dict[str, Any]],
    best_parameters: dict[str, float],
) -> dict[str, Any]:
    names = parameter_names(mechanism_id)
    if not names:
        return {
            "mechanism_id": mechanism_id,
            "parameter_count": 0,
            "jacobian_rank": 0,
            "maximum_absolute_parameter_correlation": None,
            "boundary_hit": False,
            "bounded_profile_both_sides": True,
            "identifiability_status": "NOT_APPLICABLE_NO_NEW_PARAMETERS",
        }
    values = parameter_values(mechanism_id, protocol)
    boundary_hit = any(
        math.isclose(best_parameters[name], values[name][0])
        or math.isclose(best_parameters[name], values[name][-1])
        for name in names
    )
    lookup = {
        tuple(float(item["parameters"][name]) for name in names): item
        for item in evaluations
    }
    derivative_columns = []
    profile_both_sides = True
    for name_index, name in enumerate(names):
        grid_values = values[name]
        center_index = grid_values.index(best_parameters[name])
        if center_index == 0 or center_index == len(grid_values) - 1:
            profile_both_sides = False
        else:
            profile = []
            for value in grid_values:
                profile.append(
                    min(
                        item["metrics"]["log10_rmse"]
                        for item in evaluations
                        if math.isclose(item["parameters"][name], value)
                    )
                )
            profile_both_sides &= (
                profile[center_index - 1] > profile[center_index]
                and profile[center_index + 1] > profile[center_index]
            )
        lower_index = max(center_index - 1, 0)
        upper_index = min(center_index + 1, len(grid_values) - 1)
        lower_parameters = dict(best_parameters)
        upper_parameters = dict(best_parameters)
        lower_parameters[name] = grid_values[lower_index]
        upper_parameters[name] = grid_values[upper_index]
        low = lookup[tuple(lower_parameters[item] for item in names)]
        high = lookup[tuple(upper_parameters[item] for item in names)]
        transform = (
            np.log10
            if (
                "rate_s" in name
                or mechanism_id == "H4_OBT_MEDIATED_RECYCLE"
            )
            else np.asarray
        )
        lower_coordinate = float(transform(lower_parameters[name]))
        upper_coordinate = float(transform(upper_parameters[name]))
        derivative = (
            np.log10(high["prediction_vector"])
            - np.log10(low["prediction_vector"])
        ) / (upper_coordinate - lower_coordinate)
        derivative_columns.append(derivative)
    jacobian = np.column_stack(derivative_columns)
    rank = int(np.linalg.matrix_rank(jacobian, tol=1.0e-8))
    correlation = float(abs(np.corrcoef(jacobian, rowvar=False)[0, 1]))
    correlation_limit = float(
        protocol["identifiability"]["correlation_warning_absolute"]
    )
    passed = (
        not boundary_hit
        and rank == len(names)
        and (correlation < correlation_limit or profile_both_sides)
    )
    return {
        "mechanism_id": mechanism_id,
        "parameter_count": len(names),
        "jacobian_rank": rank,
        "maximum_absolute_parameter_correlation": correlation,
        "boundary_hit": boundary_hit,
        "bounded_profile_both_sides": bool(profile_both_sides),
        "identifiability_status": (
            "PASS_BOUNDED_LOCAL_SCREEN"
            if passed
            else "LIMITED_BOUNDARY_RANK_OR_CORRELATION"
        ),
    }


def calibration_stage(protocol: dict[str, Any]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    LOCAL_OUTPUTS.mkdir(parents=True, exist_ok=True)
    forcing = sb1.load_forcing("RUN_01")
    observed = calibration_observations()
    search_rows: list[dict[str, Any]] = []
    best_prediction_rows: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    mass_rows: list[dict[str, Any]] = []
    identifiability_rows: list[dict[str, Any]] = []
    selected: dict[str, dict[str, Any]] = {}
    for mechanism_id in CANDIDATES:
        evaluations: list[dict[str, Any]] = []
        for evaluation_id, parameters in enumerate(
            candidate_grid(mechanism_id, protocol), start=1
        ):
            model = simulate(forcing, mechanism_id, parameters, 336.0)
            sampled = sample_predictions(model, observed)
            metrics = log_metrics(sampled)
            mass = summarize_mass_balance(model, protocol)
            evaluations.append(
                {
                    "evaluation_id": evaluation_id,
                    "parameters": parameters,
                    "metrics": metrics,
                    "prediction_vector": sampled[
                        "predicted_bq_l_water"
                    ].to_numpy(float),
                    "sampled": sampled,
                    "mass": mass,
                }
            )
            names = parameter_names(mechanism_id)
            search_rows.append(
                {
                    "mechanism_id": mechanism_id,
                    "evaluation_id": evaluation_id,
                    "parameter_1_name": names[0] if names else "",
                    "parameter_1_value": parameters.get(names[0]) if names else np.nan,
                    "parameter_2_name": names[1] if names else "",
                    "parameter_2_value": parameters.get(names[1]) if names else np.nan,
                    **metrics,
                    "mass_balance_pass": mass["mass_balance_pass"],
                }
            )
        best = min(
            evaluations,
            key=lambda item: (
                item["metrics"]["log10_rmse"],
                *[
                    item["parameters"][name]
                    for name in parameter_names(mechanism_id)
                ],
            ),
        )
        best_parameters = {
            name: float(best["parameters"][name])
            for name in parameter_names(mechanism_id)
        }
        identification = identify_parameters(
            mechanism_id, protocol, evaluations, best_parameters
        )
        identifiability_rows.append(identification)
        selected[mechanism_id] = {
            "parameters": best_parameters,
            "calibration_metrics": best["metrics"],
            "boundary_hit": identification["boundary_hit"],
            "identifiability_status": identification[
                "identifiability_status"
            ],
        }
        best_sampled = best["sampled"].copy()
        best_sampled.insert(0, "mechanism_id", mechanism_id)
        best_prediction_rows.append(best_sampled)
        metric_rows.append({"mechanism_id": mechanism_id, **best["metrics"]})
        mass_rows.append({"mechanism_id": mechanism_id, **best["mass"]})

        if mechanism_id == "H1_DYNAMIC_WATER_STORAGE":
            sensitivity = simulate(
                forcing,
                mechanism_id,
                {"storage_shape": "SQRT_TIME_EXPOSURE_TO_HARVEST"},
                336.0,
            )
            sensitivity_sampled = sample_predictions(sensitivity, observed)
            sensitivity_sampled.to_csv(
                REPORTS / "h1_storage_shape_sensitivity.csv", index=False
            )

    pd.DataFrame(search_rows).to_csv(
        REPORTS / "mechanism_parameter_search.csv", index=False
    )
    pd.concat(best_prediction_rows, ignore_index=True).to_csv(
        REPORTS / "mechanism_calibration_predictions.csv", index=False
    )
    pd.DataFrame(metric_rows).to_csv(
        REPORTS / "mechanism_calibration_metrics.csv", index=False
    )
    pd.DataFrame(identifiability_rows).to_csv(
        REPORTS / "mechanism_identifiability.csv", index=False
    )
    pd.DataFrame(mass_rows).to_csv(
        REPORTS / "mechanism_mass_balance_calibration.csv", index=False
    )
    contract = {
        "protocol_id": protocol["protocol_id"],
        "protocol_commit": protocol_commit(),
        "merged_sb1_baseline_head": protocol["merged_sb1_baseline_head"],
        "frozen_existing_leaf_parameters": FROZEN_LEAF_PARAMETERS,
        "candidates": selected,
    }
    result_hash = canonical_hash(contract)
    frozen = {
        **contract,
        "mechanism_parameter_result_hash": result_hash,
        "late_check_executed": False,
    }
    (REPORTS / "frozen_mechanism_parameters.yaml").write_text(
        yaml.safe_dump(frozen, sort_keys=False), encoding="utf-8"
    )
    result = {
        "status": "CALIBRATION_COMPLETE_PARAMETERS_FROZEN_PENDING_COMMIT",
        "selection_data_hours": [0.2, 1, 24, 120, 336],
        "late_data_used_for_selection": False,
        "candidate_evaluation_counts": {
            mechanism: len(candidate_grid(mechanism, protocol))
            for mechanism in CANDIDATES
        },
        "selected": selected,
        "mechanism_parameter_result_hash": result_hash,
    }
    (REPORTS / "mechanism_calibration_result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print("MECHANISM_CALIBRATION_STATUS = COMPLETE_PENDING_PARAMETER_COMMIT")
    print(f"MECHANISM_PARAMETER_RESULT_HASH = {result_hash}")
    for mechanism_id in CANDIDATES:
        print(
            f"{mechanism_id}_CALIBRATION_LOG10_RMSE = "
            f"{selected[mechanism_id]['calibration_metrics']['log10_rmse']:.9g}"
        )


def load_frozen_parameters() -> dict[str, Any]:
    path = REPORTS / "frozen_mechanism_parameters.yaml"
    frozen = load_yaml(path)
    contract = {
        key: frozen[key]
        for key in (
            "protocol_id",
            "protocol_commit",
            "merged_sb1_baseline_head",
            "frozen_existing_leaf_parameters",
            "candidates",
        )
    }
    if canonical_hash(contract) != frozen["mechanism_parameter_result_hash"]:
        raise ValueError("Frozen mechanism parameter hash mismatch")
    relative = str(path.relative_to(ROOT))
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", relative],
        cwd=ROOT,
        check=False,
    ).returncode != 0:
        raise ValueError("Frozen mechanism parameter file differs from HEAD")
    frozen_commit = git_output("log", "-1", "--format=%H", "--", relative)
    if not frozen_commit:
        raise ValueError("Frozen parameter commit is unavailable")
    frozen["frozen_parameter_commit"] = frozen_commit
    return frozen


def descriptive_timescales() -> dict[str, Any]:
    observed = sb1.observations()
    body = observed[observed["compartment"] == "plant_body"].copy()
    time_h = body["hours_after_exposure"].to_numpy(float)
    values = body["tfwt_bq_l_water"].to_numpy(float)
    log_values = np.log(values)
    slope, intercept = np.polyfit(time_h, log_values, 1)
    single = {
        "amplitude_bq_l": float(math.exp(intercept)),
        "rate_h": float(max(-slope, 0.0)),
        "e_folding_time_h": (
            float(1.0 / -slope) if slope < 0 else math.inf
        ),
        "log_sse": float(
            np.sum((log_values - (intercept + slope * time_h)) ** 2)
        ),
    }

    def double_model(
        time: np.ndarray,
        fast_amplitude: float,
        fast_rate: float,
        slow_amplitude: float,
        slow_rate: float,
    ) -> np.ndarray:
        return (
            fast_amplitude * np.exp(-fast_rate * time)
            + slow_amplitude * np.exp(-slow_rate * time)
        )

    double_status = "PASS"
    try:
        fitted, _ = curve_fit(
            double_model,
            time_h,
            values,
            p0=[values[0] * 0.95, 1.0, values[-1] * 10.0, 0.001],
            bounds=([0, 1.0e-8, 0, 1.0e-10], [1.0e9, 100, 1.0e8, 10]),
            maxfev=100000,
        )
        fast_amplitude, fast_rate, slow_amplitude, slow_rate = fitted
        if fast_rate < slow_rate:
            fast_amplitude, slow_amplitude = slow_amplitude, fast_amplitude
            fast_rate, slow_rate = slow_rate, fast_rate
        double_prediction = double_model(
            time_h,
            fast_amplitude,
            fast_rate,
            slow_amplitude,
            slow_rate,
        )
        double = {
            "fast_amplitude_bq_l": float(fast_amplitude),
            "fast_rate_h": float(fast_rate),
            "fast_e_folding_time_h": float(1.0 / fast_rate),
            "slow_amplitude_bq_l": float(slow_amplitude),
            "slow_rate_h": float(slow_rate),
            "slow_e_folding_time_h": float(1.0 / slow_rate),
            "log_sse": float(
                np.sum((np.log(values) - np.log(double_prediction)) ** 2)
            ),
        }
    except (RuntimeError, ValueError, FloatingPointError) as exc:
        double_status = f"FIT_FAILED_{type(exc).__name__}"
        double = {}

    best_piecewise: dict[str, Any] | None = None
    log10_values = np.log10(values)
    for split in range(2, len(time_h) - 1):
        first_slope, first_intercept = np.polyfit(
            time_h[: split + 1], log10_values[: split + 1], 1
        )
        second_slope, second_intercept = np.polyfit(
            time_h[split:], log10_values[split:], 1
        )
        prediction = np.concatenate(
            [
                first_intercept + first_slope * time_h[:split],
                second_intercept + second_slope * time_h[split:],
            ]
        )
        sse = float(np.sum((log10_values - prediction) ** 2))
        candidate = {
            "break_time_h": float(time_h[split]),
            "early_log10_slope_per_h": float(first_slope),
            "late_log10_slope_per_h": float(second_slope),
            "log10_sse": sse,
        }
        if best_piecewise is None or sse < best_piecewise["log10_sse"]:
            best_piecewise = candidate
    return {
        "descriptive_only": True,
        "used_for_candidate_calibration": False,
        "used_for_model_selection": False,
        "single_exponential": single,
        "double_exponential_status": double_status,
        "double_exponential": double,
        "piecewise_log_linear": best_piecewise,
    }


def late_stage(protocol: dict[str, Any]) -> None:
    frozen = load_frozen_parameters()
    calibration_metrics = pd.read_csv(
        REPORTS / "mechanism_calibration_metrics.csv"
    ).set_index("mechanism_id")
    identifiability = pd.read_csv(
        REPORTS / "mechanism_identifiability.csv"
    ).set_index("mechanism_id")
    observed = sb1.observations()
    sample_rows: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    mass_rows: list[dict[str, Any]] = []
    structural_rows: list[dict[str, Any]] = []
    sampled_lookup: dict[tuple[str, str], pd.DataFrame] = {}
    metric_lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    mass_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for mechanism_id in CANDIDATES:
        parameters = {
            name: float(value)
            for name, value in frozen["candidates"][mechanism_id][
                "parameters"
            ].items()
        }
        for run_id in sb1.RUN_FILES:
            model = simulate(
                sb1.load_forcing(run_id),
                mechanism_id,
                parameters,
                2280.0,
            )
            sampled = sample_predictions(model, observed)
            sampled.insert(0, "run_id", run_id)
            sampled.insert(0, "mechanism_id", mechanism_id)
            sampled["mechanism_parameter_result_hash"] = frozen[
                "mechanism_parameter_result_hash"
            ]
            sample_rows.append(sampled)
            sampled_lookup[(mechanism_id, run_id)] = sampled
            parts = sb1.partitions(sampled)
            for partition_name, partition in parts.items():
                values = log_metrics(partition)
                metric_lookup[
                    (mechanism_id, run_id, partition_name)
                ] = values
                metric_rows.append(
                    {
                        "mechanism_id": mechanism_id,
                        "run_id": run_id,
                        "partition": partition_name,
                        **values,
                    }
                )
            mass = summarize_mass_balance(model, protocol)
            mass_lookup[(mechanism_id, run_id)] = mass
            mass_rows.append(
                {
                    "mechanism_id": mechanism_id,
                    "run_id": run_id,
                    **mass,
                }
            )
            final = model.iloc[-1]
            structural_rows.append(
                {
                    "mechanism_id": mechanism_id,
                    "run_id": run_id,
                    "plant_body_obt_bq_l_combustion_water": final[
                        "plant_body_obt_bq_l_combustion_water"
                    ],
                    "pods_obt_bq_l_combustion_water": final[
                        "pods_obt_bq_l_combustion_water"
                    ],
                    "pods_status": "NOT_USED_FOR_SELECTION",
                    "obt_status": "CONSISTENCY_CHECK_ONLY",
                }
            )
    all_samples = pd.concat(sample_rows, ignore_index=True)
    all_samples[
        all_samples["hours_after_exposure"].isin([936, 1608, 2280])
    ].to_csv(REPORTS / "mechanism_late_predictions.csv", index=False)
    pd.DataFrame(metric_rows).to_csv(
        REPORTS / "mechanism_late_metrics.csv", index=False
    )
    pd.DataFrame(mass_rows).to_csv(
        REPORTS / "mechanism_mass_balance.csv", index=False
    )
    structural = pd.DataFrame(structural_rows)
    structural.to_csv(
        REPORTS / "mechanism_structural_diagnostics.csv", index=False
    )

    robustness_rows = []
    for mechanism_id in CANDIDATES[1:]:
        for run_id in sb1.RUN_FILES:
            reference = metric_lookup[
                ("H0_CURRENT_SINGLE_POOL", run_id, "pseudo_holdout_a")
            ]
            candidate = metric_lookup[
                (mechanism_id, run_id, "pseudo_holdout_a")
            ]
            improvement = late_improvement(reference, candidate)
            passed = bool(
                improvement["late_rmse_improvement_dex"]
                >= float(
                    protocol["success_criteria"][
                        "late_log10_rmse_improvement_minimum_dex"
                    ]
                )
                and improvement[
                    "late_median_ratio_closeness_improvement_dex"
                ]
                >= float(
                    protocol["success_criteria"][
                        "late_median_ratio_closeness_improvement_minimum_dex"
                    ]
                )
            )
            robustness_rows.append(
                {
                    "mechanism_id": mechanism_id,
                    "run_id": run_id,
                    **improvement,
                    "frozen_late_thresholds_pass": passed,
                }
            )
    robustness = pd.DataFrame(robustness_rows)
    robustness.to_csv(
        REPORTS / "mechanism_forcing_robustness.csv", index=False
    )

    reference_calibration = calibration_metrics.loc[
        "H0_CURRENT_SINGLE_POOL"
    ].to_dict()
    reference_late = metric_lookup[
        ("H0_CURRENT_SINGLE_POOL", "RUN_01", "pseudo_holdout_a")
    ]
    h0_obt = structural[
        (structural["mechanism_id"] == "H0_CURRENT_SINGLE_POOL")
        & (structural["run_id"] == "RUN_01")
    ]["plant_body_obt_bq_l_combustion_water"].iloc[0]
    observed_obt = 16000.0
    h0_obt_error = abs(math.log10(h0_obt / observed_obt))
    selection: dict[str, Any] = {
        "H0_CURRENT_SINGLE_POOL": {
            "status": "REFERENCE_BASELINE",
            "supported": False,
        }
    }
    supported = []
    for mechanism_id in CANDIDATES[1:]:
        candidate_calibration = calibration_metrics.loc[
            mechanism_id
        ].to_dict()
        candidate_late = metric_lookup[
            (mechanism_id, "RUN_01", "pseudo_holdout_a")
        ]
        sampled = sampled_lookup[(mechanism_id, "RUN_01")]
        early = sampled[
            (sampled["compartment"] == "plant_body")
            & sampled["hours_after_exposure"].isin([0.2, 1.0])
        ]
        mass = mass_lookup[(mechanism_id, "RUN_01")]
        finite_nonnegative = bool(
            mass["nan_count"] == 0
            and mass["inf_count"] == 0
            and mass["negative_inventory_count"] == 0
            and mass["negative_concentration_count"] == 0
        )
        boundary_hit = bool(
            identifiability.loc[mechanism_id, "boundary_hit"]
        )
        ident_status = str(
            identifiability.loc[mechanism_id, "identifiability_status"]
        )
        ident_pass = (
            ident_status == "PASS_BOUNDED_LOCAL_SCREEN"
            or ident_status == "NOT_APPLICABLE_NO_NEW_PARAMETERS"
        )
        forcing_pass_count = int(
            robustness[
                (robustness["mechanism_id"] == mechanism_id)
                & robustness["frozen_late_thresholds_pass"]
            ].shape[0]
        )
        candidate_obt = structural[
            (structural["mechanism_id"] == mechanism_id)
            & (structural["run_id"] == "RUN_01")
        ]["plant_body_obt_bq_l_combustion_water"].iloc[0]
        obt_consistency = (
            abs(math.log10(candidate_obt / observed_obt))
            <= h0_obt_error + 1.0e-12
        )
        result = evaluate_primary_success(
            protocol=protocol,
            reference_calibration=reference_calibration,
            reference_late=reference_late,
            candidate_calibration=candidate_calibration,
            candidate_late=candidate_late,
            early_predictions=early,
            finite_nonnegative=finite_nonnegative,
            mass_balance_pass=bool(mass["mass_balance_pass"]),
            boundary_hit=boundary_hit,
            identifiability_pass=ident_pass,
            forcing_pass_count=forcing_pass_count,
            obt_consistency_pass=obt_consistency,
        )
        result.update(
            {
                "status": (
                    "SUPPORTED_FOR_BOUNDED_V3_DESIGN"
                    if result["supported"]
                    else "NOT_SUPPORTED_BY_FROZEN_CRITERIA"
                ),
                "new_fitted_parameter_count": protocol["candidates"][
                    mechanism_id
                ]["new_fitted_parameter_count"],
                "parameters": frozen["candidates"][mechanism_id][
                    "parameters"
                ],
                "identifiability_status": ident_status,
                "boundary_hit": boundary_hit,
                "primary_late_metrics": candidate_late,
                "primary_calibration_metrics": candidate_calibration,
                "primary_plant_body_obt_bq_l": float(candidate_obt),
            }
        )
        selection[mechanism_id] = result
        if result["supported"]:
            supported.append(mechanism_id)
    supported.sort(
        key=lambda mechanism_id: (
            protocol["candidates"][mechanism_id][
                "new_fitted_parameter_count"
            ],
            -selection[mechanism_id]["late_rmse_improvement_dex"],
            mechanism_id,
        )
    )
    best = supported[0] if supported else None
    if best is None:
        discrimination_status = "NO_MINIMAL_MECHANISM_SUPPORTED"
        design_recommendation = "NOT_READY"
    elif best == "H1_DYNAMIC_WATER_STORAGE":
        discrimination_status = "DYNAMIC_WATER_STORAGE_SUPPORTED"
        design_recommendation = "BOUNDED_VALIDATION_DESIGN_ONLY"
    elif best in {
        "H2_PARALLEL_FAST_SLOW_RESIDUAL",
        "H3_REVERSIBLE_FAST_SLOW_EXCHANGE",
    }:
        discrimination_status = (
            "FAST_SLOW_WATER_STORAGE_SUPPORTED_FOR_BOUNDED_DESIGN"
        )
        design_recommendation = best
    else:
        discrimination_status = "OBT_RECYCLE_SUPPORTED_FOR_BOUNDED_DESIGN"
        design_recommendation = "H4_OBT_MEDIATED_RECYCLE"
    descriptive = descriptive_timescales()
    (REPORTS / "descriptive_timescale_results.json").write_text(
        json.dumps(descriptive, indent=2) + "\n", encoding="utf-8"
    )
    final = {
        "protocol_id": protocol["protocol_id"],
        "frozen_parameter_commit": frozen["frozen_parameter_commit"],
        "mechanism_parameter_result_hash": frozen[
            "mechanism_parameter_result_hash"
        ],
        "late_check_hours": [936, 1608, 2280],
        "late_data_used_for_fit": False,
        "candidate_results": selection,
        "best_supported_mechanism": best,
        "mechanism_discrimination_status": discrimination_status,
        "formal_v3_design_recommendation": design_recommendation,
        "v3_physics_implementation_status": "NOT_STARTED",
        "empirical_validation_claim": False,
        "production_gate_eligible": False,
        "v3_physics_start_gate": (
            "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        ),
    }
    (REPORTS / "mechanism_selection.json").write_text(
        json.dumps(final, indent=2) + "\n", encoding="utf-8"
    )
    write_reports(protocol, frozen, descriptive, final)
    print(
        "MECHANISM_DISCRIMINATION_STATUS = "
        f"{discrimination_status}"
    )
    print(f"BEST_SUPPORTED_MECHANISM = {best or 'NONE'}")
    print("V3_PHYSICS_IMPLEMENTATION_STATUS = NOT_STARTED")
    print(
        "V3_PHYSICS_START_GATE = "
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )


def write_reports(
    protocol: dict[str, Any],
    frozen: dict[str, Any],
    descriptive: dict[str, Any],
    final: dict[str, Any],
) -> None:
    calibration = pd.read_csv(REPORTS / "mechanism_calibration_metrics.csv")
    late = pd.read_csv(REPORTS / "mechanism_late_metrics.csv")
    primary_late = late[
        (late["run_id"] == "RUN_01")
        & (late["partition"] == "pseudo_holdout_a")
    ]
    ident = pd.read_csv(REPORTS / "mechanism_identifiability.csv")
    mass = pd.read_csv(REPORTS / "mechanism_mass_balance.csv")
    robustness = pd.read_csv(REPORTS / "mechanism_forcing_robustness.csv")

    double = descriptive["double_exponential"]
    descriptive_lines = [
        "# Descriptive SB1 timescale analysis",
        "",
        "`DESCRIPTIVE_ONLY = TRUE`",
        "",
        "`USED_FOR_CANDIDATE_CALIBRATION = FALSE`",
        "",
        "`USED_FOR_MODEL_SELECTION = FALSE`",
        "",
        f"Single-exponential e-folding time: "
        f"{descriptive['single_exponential']['e_folding_time_h']:.6g} h.",
        "",
        (
            "Double-exponential fit: fast "
            f"{double.get('fast_e_folding_time_h', float('nan')):.6g} h; "
            "slow "
            f"{double.get('slow_e_folding_time_h', float('nan')):.6g} h."
        ),
        "",
        (
            "Best piecewise log-linear break: "
            f"{descriptive['piecewise_log_linear']['break_time_h']:.6g} h."
        ),
        "",
        "This analysis describes the eight observations and did not set any",
        "candidate range, parameter or selection result.",
    ]
    (REPORTS / "descriptive_timescale_report.md").write_text(
        "\n".join(descriptive_lines) + "\n", encoding="utf-8"
    )

    calibration_lines = [
        "# Mechanism calibration report",
        "",
        "`CALIBRATION_HOURS = 0.2,1,24,120,336`",
        "",
        "`LATE_DATA_USED_FOR_FIT = FALSE`",
        "",
        "| mechanism | log10 RMSE | log10 bias | median P/O |",
        "|---|---:|---:|---:|",
    ]
    for row in calibration.itertuples(index=False):
        calibration_lines.append(
            f"| {row.mechanism_id} | {row.log10_rmse:.6g} | "
            f"{row.log10_mean_bias:.6g} | "
            f"{row.median_predicted_to_observed_ratio:.6g} |"
        )
    calibration_lines.extend(
        [
            "",
            f"Frozen parameter commit: `{frozen['frozen_parameter_commit']}`.",
        ]
    )
    (REPORTS / "mechanism_calibration_report.md").write_text(
        "\n".join(calibration_lines) + "\n", encoding="utf-8"
    )

    late_lines = [
        "# Frozen late-check report",
        "",
        "`LATE_CHECK_HOURS = 936,1608,2280`",
        "",
        "`PARAMETER_RECALL = FALSE`",
        "",
        "| mechanism | log10 RMSE | log10 bias | median P/O |",
        "|---|---:|---:|---:|",
    ]
    for row in primary_late.itertuples(index=False):
        late_lines.append(
            f"| {row.mechanism_id} | {row.log10_rmse:.6g} | "
            f"{row.log10_mean_bias:.6g} | "
            f"{row.median_predicted_to_observed_ratio:.6g} |"
        )
    late_lines.extend(
        [
            "",
            "`PODS_STATUS = NOT_USED_FOR_SELECTION`",
            "",
            "`OBT_STATUS = CONSISTENCY_CHECK_ONLY`",
            "",
            "Frozen-threshold passes across seven forcing scenarios:",
            "",
        ]
    )
    for mechanism_id in CANDIDATES[1:]:
        count = robustness[
            (robustness["mechanism_id"] == mechanism_id)
            & robustness["frozen_late_thresholds_pass"]
        ].shape[0]
        late_lines.append(f"- {mechanism_id}: {count}/7")
    (REPORTS / "mechanism_late_check_report.md").write_text(
        "\n".join(late_lines) + "\n", encoding="utf-8"
    )

    ident_lines = [
        "# Mechanism identifiability report",
        "",
        "| mechanism | rank | max abs correlation | boundary | status |",
        "|---|---:|---:|---|---|",
    ]
    for row in ident.itertuples(index=False):
        correlation = (
            "N/A"
            if pd.isna(row.maximum_absolute_parameter_correlation)
            else f"{row.maximum_absolute_parameter_correlation:.6g}"
        )
        ident_lines.append(
            f"| {row.mechanism_id} | {row.jacobian_rank} | {correlation} | "
            f"{row.boundary_hit} | {row.identifiability_status} |"
        )
    (REPORTS / "mechanism_identifiability_report.md").write_text(
        "\n".join(ident_lines) + "\n", encoding="utf-8"
    )

    mass_lines = [
        "# Mechanism mass-balance report",
        "",
        "`FAST_SLOW_INTERNAL_TRANSFER_NET = ZERO_WITHIN_TOLERANCE`",
        "",
        "| mechanism | runs passed | max formal residual | "
        "max internal residual |",
        "|---|---:|---:|---:|",
    ]
    for mechanism_id in CANDIDATES:
        subset = mass[mass["mechanism_id"] == mechanism_id]
        mass_lines.append(
            f"| {mechanism_id} | "
            f"{int(subset['mass_balance_pass'].sum())}/7 | "
            f"{subset['maximum_formal_mass_closure_abs_bq_m2'].max():.6g} | "
            f"{subset['maximum_internal_transfer_residual_abs_bq_m2'].max():.6g} |"
        )
    (REPORTS / "mechanism_mass_balance_report.md").write_text(
        "\n".join(mass_lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    protocol = load_yaml(PROTOCOL_PATH)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if args.stage == "calibrate":
        calibration_stage(protocol)
    else:
        late_stage(protocol)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"SB1 mechanism discrimination failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
