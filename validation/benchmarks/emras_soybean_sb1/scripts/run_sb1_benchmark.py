#!/usr/bin/env python3
"""Run frozen V2 physics through an SB1-only validation adapter."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb1"
LOCAL = ROOT / "validation" / "external_local" / "emras_soybean_sb1"
GENERATED = LOCAL / "generated_forcing"
OUTPUTS = LOCAL / "outputs"
REPORTS = BENCHMARK / "reports"
TABLES = BENCHMARK / "published_tables"
PROTOCOL = BENCHMARK / "preregistration" / "sb1_benchmark_protocol.yaml"
DEFAULTS = ROOT / "configs" / "default_parameters.yaml"

sys.path.insert(0, str(ROOT / "src"))
from cteas_ufotri.atmosphere.dispersion_parameters import (  # noqa: E402
    classify_pasquill_gifford,
)
from cteas_ufotri.coupling.integrator import advance  # noqa: E402
from cteas_ufotri.coupling.state import State  # noqa: E402
from cteas_ufotri.meteorology.fallback_fluxes import (  # noqa: E402
    partition_evapotranspiration,
    penman_ufotri_components_m_s,
)
from cteas_ufotri.plant.edible import edible_concentrations  # noqa: E402


DT_SECONDS = 300.0
EXPOSURE_START = pd.Timestamp("2001-07-02T09:30:00+09:00")
EXPOSURE_END = pd.Timestamp("2001-07-02T10:30:00+09:00")
POD_START = pd.Timestamp("2001-07-10T00:00:00+09:00")
HARVEST = pd.Timestamp("2001-10-05T10:30:00+09:00")
EXPOSURE_BODY_WATER_M = 0.0007882
EXPOSURE_BODY_DRY_G_M2 = 173.2
HARVEST_BODY_DRY_G_M2 = 922.4
HARVEST_POD_FRESH_G_M2 = 1623.0
HARVEST_POD_DRY_G_M2 = 806.5
HARVEST_POD_WATER_M = (
    (HARVEST_POD_FRESH_G_M2 - HARVEST_POD_DRY_G_M2) / 1000.0 / 1000.0
)
COMBUSTION_WATER_ML_PER_G_DRY = 0.6
RUN_FILES = {
    "RUN_01": "sb1_forcing_primary.csv",
    "RUN_02": "sb1_forcing_run_02.csv",
    "RUN_03": "sb1_forcing_run_03.csv",
    "RUN_04": "sb1_forcing_run_04.csv",
    "RUN_05": "sb1_forcing_run_05.csv",
    "RUN_06": "sb1_forcing_run_06.csv",
    "RUN_07": "sb1_forcing_run_07.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("baseline", "calibrate", "holdout", "all"),
        default="all",
    )
    return parser.parse_args()


def load_mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def model_config(parameters: dict[str, float]) -> dict[str, Any]:
    config = load_mapping(DEFAULTS)
    config["plant"]["leaf_exchange_mode"] = "bidirectional_resistance"
    config["plant"]["water_storage_m"] = EXPOSURE_BODY_WATER_M
    config["plant"]["root_uptake_fraction_from_modelled_layer"] = 0.0
    config["plant"]["leaf_stomatal_resistance_day_s_m"] = float(
        parameters["leaf_stomatal_resistance_day_s_m"]
    )
    config["plant"]["leaf_characteristic_length_m"] = float(
        parameters["leaf_characteristic_length_m"]
    )
    return config


def soybean_lai(time_local: pd.Timestamp) -> float:
    """Published generic, explicitly unmeasured midpoint soybean LAI curve."""
    start = pd.Timestamp("2001-05-25T00:00:00+09:00")
    peak = pd.Timestamp("2001-08-10T00:00:00+09:00")
    decline = pd.Timestamp("2001-08-30T00:00:00+09:00")
    end = pd.Timestamp("2001-10-05T00:00:00+09:00")
    if time_local <= start:
        return 0.0
    if time_local < peak:
        return 6.5 * (time_local - start).total_seconds() / (
            peak - start
        ).total_seconds()
    if time_local <= decline:
        return 6.5
    fraction = min(
        max(
            (time_local - decline).total_seconds()
            / (end - decline).total_seconds(),
            0.0,
        ),
        1.0,
    )
    return 6.5 + fraction * (3.0 - 6.5)


def growth_fraction(
    time_local: pd.Timestamp, start: pd.Timestamp, end: pd.Timestamp
) -> float:
    return min(
        max(
            (time_local - start).total_seconds() / (end - start).total_seconds(),
            0.0,
        ),
        1.0,
    )


def load_forcing(run_id: str) -> pd.DataFrame:
    path = GENERATED / RUN_FILES[run_id]
    if not path.is_file():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
    frame["time_local"] = frame["time_utc"].dt.tz_convert("Asia/Seoul")
    frame = frame[
        frame["time_local"].between(EXPOSURE_START, HARVEST)
    ].copy()
    frame = frame.sort_values("time_utc").reset_index(drop=True)
    if frame["time_utc"].duplicated().any():
        raise ValueError(f"{run_id} has duplicate timestamps")
    differences = frame["time_utc"].diff().dropna().dt.total_seconds()
    if not (differences == DT_SECONDS).all():
        raise ValueError(f"{run_id} is not continuous at five minutes")
    return frame


def run_model(
    forcing: pd.DataFrame,
    parameters: dict[str, float],
    maximum_hours_after_exposure: float = 2280.0,
) -> pd.DataFrame:
    config = model_config(parameters)
    physics = config["physics"]
    state = State(config["soil"]["initial_water_m"])
    rows = [
        {
            "time_utc": forcing.iloc[0]["time_utc"],
            "hours_after_exposure": -1.0,
            "plant_body_tfwt_bq_l_water": 0.0,
            "pods_tfwt_bq_l_water": np.nan,
            "plant_body_obt_bq_l_combustion_water": 0.0,
            "pods_obt_bq_l_combustion_water": np.nan,
            "plant_tfwt_inventory_bq_m2": 0.0,
            "plant_obt_inventory_bq_m2": 0.0,
            "pods_tfwt_inventory_bq_m2": 0.0,
            "pods_obt_inventory_bq_m2": 0.0,
            "surface_box_residual_bq_m2": 0.0,
        }
    ]
    end_time = EXPOSURE_END + pd.Timedelta(hours=maximum_hours_after_exposure)
    for index in range(1, len(forcing)):
        current = forcing.iloc[index]
        previous = forcing.iloc[index - 1]
        time_local = current["time_local"]
        if time_local > end_time:
            break
        temperature_k = (
            0.5
            * (previous["air_temperature_c"] + current["air_temperature_c"])
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
            previous["shortwave_down_w_m2"] + current["shortwave_down_w_m2"]
        )
        net_radiation = (
            physics["fallback_shortwave_absorptivity"] * shortwave
            - physics["fallback_net_longwave_loss_w_m2"]
        )
        pet, radiation_pet, aerodynamic_pet = penman_ufotri_components_m_s(
            temperature_k,
            dewpoint_k,
            wind,
            net_radiation,
            physics["latent_heat_j_kg"],
            physics["water_density_kg_m3"],
            physics["psychrometric_constant_pa_k"],
            physics["penman_aerodynamic_coefficient_w_m2_pa"],
        )
        lai = soybean_lai(time_local)
        water_fluxes = partition_evapotranspiration(
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
            float(current["precipitation_mm_interval"]) / 1000.0 / DT_SECONDS
        )
        cloud = 0.5 * (
            previous["total_cloud_cover_fraction"]
            + current["total_cloud_cover_fraction"]
        )
        stability = classify_pasquill_gifford(wind, net_radiation, cloud)
        air_hto = 0.5 * (
            previous["air_hto_bq_m3"] + current["air_hto_bq_m3"]
        )
        pod_active = time_local >= POD_START
        allocation_rate = (
            config["crops"]["parameters"]["generic_crop"][
                "edible_allocation_rate_s"
            ]
            if pod_active
            else 0.0
        )
        state, diagnostics = advance(
            state,
            DT_SECONDS,
            air_hto,
            precipitation_m_s,
            water_fluxes.soil_evaporation_m_s,
            water_fluxes.plant_transpiration_m_s,
            config,
            rain_hto_concentration_bq_m3=0.0,
            root_uptake_m_s=0.0,
            elapsed_since_release_s=max(
                (time_local - EXPOSURE_START).total_seconds(), 0.0
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
        if min(state.total_hto_bq_m2, *asdict(state).values()) < -1.0e-12:
            raise ValueError("Model produced a negative inventory")
        pod_fraction = growth_fraction(time_local, POD_START, HARVEST)
        pod_water_m = HARVEST_POD_WATER_M * pod_fraction
        pod_fresh_kg_m2 = HARVEST_POD_FRESH_G_M2 / 1000.0 * pod_fraction
        water_content = (
            (HARVEST_POD_FRESH_G_M2 - HARVEST_POD_DRY_G_M2)
            / HARVEST_POD_FRESH_G_M2
        )
        edible = edible_concentrations(
            state.edible_tfwt_bq_m2,
            state.edible_obt_bq_m2,
            pod_fresh_kg_m2,
            water_content,
            physics["water_density_kg_m3"],
        )
        body_dry = EXPOSURE_BODY_DRY_G_M2 + growth_fraction(
            time_local, EXPOSURE_END, HARVEST
        ) * (HARVEST_BODY_DRY_G_M2 - EXPOSURE_BODY_DRY_G_M2)
        body_combustion_l = (
            body_dry * COMBUSTION_WATER_ML_PER_G_DRY / 1000.0
        )
        pod_combustion_l = (
            HARVEST_POD_DRY_G_M2
            * pod_fraction
            * COMBUSTION_WATER_ML_PER_G_DRY
            / 1000.0
        )
        rows.append(
            {
                "time_utc": current["time_utc"],
                "hours_after_exposure": (
                    time_local - EXPOSURE_END
                ).total_seconds()
                / 3600.0,
                "plant_body_tfwt_bq_l_water": (
                    state.plant_tfwt_bq_m2 / EXPOSURE_BODY_WATER_M / 1000.0
                ),
                "pods_tfwt_bq_l_water": (
                    edible.tfwt_bq_m3_water / 1000.0
                    if pod_water_m > 0
                    else np.nan
                ),
                "plant_body_obt_bq_l_combustion_water": (
                    state.plant_obt_bq_m2 / body_combustion_l
                    if body_combustion_l > 0
                    else np.nan
                ),
                "pods_obt_bq_l_combustion_water": (
                    state.edible_obt_bq_m2 / pod_combustion_l
                    if pod_combustion_l > 0
                    else np.nan
                ),
                "plant_tfwt_inventory_bq_m2": state.plant_tfwt_bq_m2,
                "plant_obt_inventory_bq_m2": state.plant_obt_bq_m2,
                "pods_tfwt_inventory_bq_m2": state.edible_tfwt_bq_m2,
                "pods_obt_inventory_bq_m2": state.edible_obt_bq_m2,
                "surface_box_residual_bq_m2": (
                    diagnostics.surface_box_mass_closure.residual_bq_m2
                ),
            }
        )
    result = pd.DataFrame(rows)
    numeric = result.select_dtypes(include=[np.number]).dropna()
    if np.isinf(numeric.to_numpy()).any():
        raise ValueError("Model output contains Inf")
    return result


def observations() -> pd.DataFrame:
    frame = pd.read_csv(TABLES / "sb1_tfwt_observations.csv")
    frame["sample_datetime_utc"] = pd.to_datetime(
        frame["sample_datetime_utc"], utc=True
    )
    return frame


def sample_predictions(model: pd.DataFrame, observed: pd.DataFrame) -> pd.DataFrame:
    model = model.set_index("time_utc")
    rows = []
    for _, row in observed.iterrows():
        column = (
            "plant_body_tfwt_bq_l_water"
            if row["compartment"] == "plant_body"
            else "pods_tfwt_bq_l_water"
        )
        timestamp = row["sample_datetime_utc"]
        if timestamp not in model.index:
            index = model.index.get_indexer([timestamp], method="nearest")
            if index[0] < 0:
                raise ValueError(f"No model time near {timestamp}")
            selected_time = model.index[index[0]]
            if abs((selected_time - timestamp).total_seconds()) > DT_SECONDS / 2:
                raise ValueError(f"Model/observation time mismatch at {timestamp}")
        else:
            selected_time = timestamp
        rows.append(
            {
                "compartment": row["compartment"],
                "sample_datetime_utc": timestamp,
                "hours_after_exposure": row["hours_after_exposure"],
                "observed_bq_l_water": row["tfwt_bq_l_water"],
                "predicted_bq_l_water": model.loc[selected_time, column],
            }
        )
    return pd.DataFrame(rows)


def metrics(frame: pd.DataFrame) -> dict[str, float]:
    observed = frame["observed_bq_l_water"].to_numpy(float)
    predicted = frame["predicted_bq_l_water"].to_numpy(float)
    if np.any(observed <= 0) or np.any(predicted <= 0):
        raise ValueError("Log metrics require positive observed and predicted values")
    residual = np.log10(predicted) - np.log10(observed)
    ratio = predicted / observed
    return {
        "log10_rmse": float(np.sqrt(np.mean(residual**2))),
        "log10_mean_bias": float(np.mean(residual)),
        "median_predicted_to_observed_ratio": float(np.median(ratio)),
        "factor_2_coverage": float(np.mean((ratio >= 0.5) & (ratio <= 2.0))),
        "factor_10_coverage": float(np.mean((ratio >= 0.1) & (ratio <= 10.0))),
        "n": int(len(frame)),
    }


def partitions(sampled: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "calibration": sampled[
            (sampled["compartment"] == "plant_body")
            & sampled["hours_after_exposure"].isin([0.2, 1, 24, 120, 336])
        ],
        "pseudo_holdout_a": sampled[
            (sampled["compartment"] == "plant_body")
            & sampled["hours_after_exposure"].isin([936, 1608, 2280])
        ],
        "pseudo_holdout_b": sampled[
            (sampled["compartment"] == "pods")
            & sampled["hours_after_exposure"].isin([936, 1608, 2280])
        ],
    }


def baseline_stage(protocol: dict[str, Any]) -> None:
    initial = {
        item["name"]: float(item["initial"])
        for item in protocol["calibration_parameters"]
    }
    all_rows = []
    summary = {}
    observed = observations()
    for run_id in RUN_FILES:
        model = run_model(load_forcing(run_id), initial)
        sampled = sample_predictions(model, observed)
        sampled["run_id"] = run_id
        all_rows.append(sampled)
        summary[run_id] = {
            name: metrics(part)
            for name, part in partitions(sampled).items()
        }
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    pd.concat(all_rows, ignore_index=True).to_csv(
        OUTPUTS / "baseline_predictions.csv", index=False
    )
    (OUTPUTS / "baseline_metrics.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(f"BASELINE_RUN_COUNT = {len(RUN_FILES)}")


def calibration_stage(protocol: dict[str, Any]) -> None:
    forcing = load_forcing("RUN_01")
    observed = observations()
    calibration_observed = observed[
        (observed["compartment"] == "plant_body")
        & observed["hours_after_exposure"].isin([0.2, 1, 24, 120, 336])
    ].copy()
    definitions = {
        item["name"]: item for item in protocol["calibration_parameters"]
    }
    initial = {name: float(item["initial"]) for name, item in definitions.items()}
    sensitivity_rows = []
    for name, item in definitions.items():
        low = dict(initial)
        high = dict(initial)
        low[name] = float(item["lower"])
        high[name] = float(item["upper"])
        low_sample = sample_predictions(
            run_model(forcing, low, 336), calibration_observed
        )
        high_sample = sample_predictions(
            run_model(forcing, high, 336), calibration_observed
        )
        for low_row, high_row in zip(
            low_sample.itertuples(index=False),
            high_sample.itertuples(index=False),
            strict=True,
        ):
            sensitivity_rows.append(
                {
                    "parameter_name": name,
                    "hours_after_exposure": low_row.hours_after_exposure,
                    "low": item["lower"],
                    "high": item["upper"],
                    "prediction_low_bq_l": low_row.predicted_bq_l_water,
                    "prediction_high_bq_l": high_row.predicted_bq_l_water,
                    "normalized_log10_sensitivity": (
                        math.log10(high_row.predicted_bq_l_water)
                        - math.log10(low_row.predicted_bq_l_water)
                    )
                    / 2.0,
                }
            )
    REPORTS.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sensitivity_rows).to_csv(
        REPORTS / "parameter_sensitivity.csv", index=False
    )

    names = list(definitions)
    grid_values = {
        name: np.linspace(
            float(definitions[name]["lower"]),
            float(definitions[name]["upper"]),
            7,
        )
        for name in names
    }
    best: tuple[float, dict[str, float], pd.DataFrame] | None = None
    grid_rows = []
    for first in grid_values[names[0]]:
        for second in grid_values[names[1]]:
            parameters = {names[0]: float(first), names[1]: float(second)}
            sampled = sample_predictions(
                run_model(forcing, parameters, 336), calibration_observed
            )
            score = metrics(sampled)["log10_rmse"]
            grid_rows.append({**parameters, "log10_rmse": score})
            if best is None or score < best[0]:
                best = (score, parameters, sampled)
    if best is None:
        raise RuntimeError("Calibration grid produced no result")
    pd.DataFrame(grid_rows).to_csv(OUTPUTS / "calibration_grid.csv", index=False)
    score, best_parameters, best_sampled = best
    best_sampled.to_csv(REPORTS / "calibration_predictions.csv", index=False)

    jacobian_columns = []
    for name, item in definitions.items():
        center = best_parameters[name]
        step = max(abs(center) * 0.01, (item["upper"] - item["lower"]) * 0.001)
        lower = dict(best_parameters)
        upper = dict(best_parameters)
        lower[name] = max(float(item["lower"]), center - step)
        upper[name] = min(float(item["upper"]), center + step)
        low_sample = sample_predictions(
            run_model(forcing, lower, 336), calibration_observed
        )
        high_sample = sample_predictions(
            run_model(forcing, upper, 336), calibration_observed
        )
        denominator = upper[name] - lower[name]
        derivative = (
            np.log10(high_sample["predicted_bq_l_water"].to_numpy())
            - np.log10(low_sample["predicted_bq_l_water"].to_numpy())
        ) / denominator
        jacobian_columns.append(derivative)
    jacobian = np.column_stack(jacobian_columns)
    rank = int(np.linalg.matrix_rank(jacobian, tol=1.0e-8))
    correlation = np.corrcoef(jacobian, rowvar=False)
    correlation_rows = []
    for row_index, first_name in enumerate(names):
        for column_index, second_name in enumerate(names):
            correlation_rows.append(
                {
                    "parameter_1": first_name,
                    "parameter_2": second_name,
                    "jacobian_column_correlation": correlation[
                        row_index, column_index
                    ],
                }
            )
    pd.DataFrame(correlation_rows).to_csv(
        REPORTS / "parameter_correlation.csv", index=False
    )
    contract = {
        "case_id": "EMRAS_SOYBEAN_SB1_PDF_ERA5_V1",
        "calibration_partition_hours": [0.2, 1, 24, 120, 336],
        "parameters": {
            name: {
                "value": best_parameters[name],
                "unit": definitions[name]["unit"],
                "lower": definitions[name]["lower"],
                "upper": definitions[name]["upper"],
                "bounds_source": definitions[name]["bounds_source"],
            }
            for name in names
        },
    }
    result_hash = canonical_hash(contract)
    parameter_set = {**contract, "parameter_result_hash": result_hash}
    (REPORTS / "calibrated_parameter_set.yaml").write_text(
        yaml.safe_dump(parameter_set, sort_keys=False),
        encoding="utf-8",
    )
    boundary_hit = any(
        np.isclose(best_parameters[name], definitions[name]["lower"])
        or np.isclose(best_parameters[name], definitions[name]["upper"])
        for name in names
    )
    identifiable = (
        rank == len(names)
        and abs(correlation[0, 1])
        < protocol["identifiability"]["correlation_warning_absolute"]
        and not boundary_hit
    )
    screening_status = (
        "PASS_LOCAL_SCREEN"
        if identifiable
        else "LIMITED_BOUNDARY_OR_CORRELATION"
    )
    result = {
        "status": "CALIBRATED_MODEL_DEVELOPMENT_ONLY",
        "method": "7x7 bounded grid",
        "grid_evaluations": len(grid_rows),
        "best_log10_rmse": score,
        "calibration_metrics": metrics(best_sampled),
        "best_parameters": best_parameters,
        "parameter_result_hash": result_hash,
        "jacobian_rank": rank,
        "jacobian_parameter_count": len(names),
        "maximum_absolute_off_diagonal_correlation": float(abs(correlation[0, 1])),
        "boundary_hit": boundary_hit,
        "identifiability_screening": screening_status,
    }
    (REPORTS / "calibration_result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    (REPORTS / "identifiability_screening.md").write_text(
        "\n".join(
            [
                "# SB1 parameter identifiability screening",
                "",
                f"`JACOBIAN_RANK = {rank}_OF_{len(names)}`",
                "",
                f"`MAX_ABS_PARAMETER_CORRELATION = {abs(correlation[0, 1]):.6g}`",
                "",
                f"`IDENTIFIABILITY_SCREENING = {screening_status}`",
                "",
                "This is a local two-parameter screen against five published",
                "calibration points. It is not proof of global or empirical",
                "identifiability.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("CALIBRATION_STATUS = CALIBRATED_MODEL_DEVELOPMENT_ONLY")
    print(f"PARAMETER_RESULT_HASH = {result_hash}")
    print(f"CALIBRATION_LOG10_RMSE = {score:.8g}")


def load_frozen_parameters() -> tuple[dict[str, float], str]:
    path = REPORTS / "calibrated_parameter_set.yaml"
    frozen = load_mapping(path)
    contract = {
        "case_id": frozen["case_id"],
        "calibration_partition_hours": frozen["calibration_partition_hours"],
        "parameters": frozen["parameters"],
    }
    actual_hash = canonical_hash(contract)
    if actual_hash != frozen["parameter_result_hash"]:
        raise ValueError("Frozen parameter-result hash mismatch")
    return (
        {
            name: float(values["value"])
            for name, values in frozen["parameters"].items()
        },
        actual_hash,
    )


def holdout_stage() -> None:
    parameters, parameter_hash = load_frozen_parameters()
    observed = observations()
    all_samples = []
    metrics_by_run = {}
    structural_rows = []
    for run_id in RUN_FILES:
        model = run_model(load_forcing(run_id), parameters)
        sampled = sample_predictions(model, observed)
        sampled["run_id"] = run_id
        sampled["parameter_result_hash"] = parameter_hash
        all_samples.append(sampled)
        parts = partitions(sampled)
        metrics_by_run[run_id] = {
            name: metrics(frame) for name, frame in parts.items()
        }
        final = model.iloc[-1]
        structural_rows.extend(
            [
                {
                    "run_id": run_id,
                    "compartment": "plant_body_average",
                    "predicted_bq_l_combustion_water": final[
                        "plant_body_obt_bq_l_combustion_water"
                    ],
                    "mapping_status": "CURRENT_MODEL_AVERAGE_ONLY",
                    "parameter_result_hash": parameter_hash,
                },
                {
                    "run_id": run_id,
                    "compartment": "pods_average",
                    "predicted_bq_l_combustion_water": final[
                        "pods_obt_bq_l_combustion_water"
                    ],
                    "mapping_status": "PROVISIONAL_GENERIC_EDIBLE_COMPARTMENT",
                    "parameter_result_hash": parameter_hash,
                },
            ]
        )
    predictions = pd.concat(all_samples, ignore_index=True)
    calibration = predictions[
        (predictions["run_id"] == "RUN_01")
        & (predictions["compartment"] == "plant_body")
        & predictions["hours_after_exposure"].isin([0.2, 1, 24, 120, 336])
    ]
    holdout = predictions[
        predictions["hours_after_exposure"].isin([936, 1608, 2280])
    ]
    calibration.to_csv(REPORTS / "calibration_predictions_frozen.csv", index=False)
    holdout.to_csv(REPORTS / "pseudo_holdout_predictions.csv", index=False)
    pd.DataFrame(structural_rows).to_csv(
        REPORTS / "structural_obt_predictions.csv", index=False
    )
    (REPORTS / "metrics.json").write_text(
        json.dumps(
            {
                "parameter_result_hash": parameter_hash,
                "metrics_by_run": metrics_by_run,
                "empirical_validation": False,
                "independent_external_holdout": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    plot_results(predictions)
    print(f"PSEUDO_HOLDOUT_RUN_COUNT = {len(RUN_FILES)}")
    print("PSEUDO_HOLDOUT_CLASS = PUBLISHED_REPORT_PSEUDO_HOLDOUT")


def plot_results(predictions: pd.DataFrame) -> None:
    figure_dir = OUTPUTS / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    primary = predictions[predictions["run_id"] == "RUN_01"]
    for compartment, filename in (
        ("plant_body", "sb1_plant_body_tfwt_vs_time.png"),
        ("pods", "sb1_pods_tfwt_vs_time.png"),
    ):
        data = primary[primary["compartment"] == compartment]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.loglog(
            data["hours_after_exposure"],
            data["observed_bq_l_water"],
            "o-",
            label="observed",
        )
        ax.loglog(
            data["hours_after_exposure"],
            data["predicted_bq_l_water"],
            "s--",
            label="model",
        )
        ax.set_xlabel("Hours after exposure")
        ax.set_ylabel("TFWT (Bq/L plant water)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(figure_dir / filename, dpi=180)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    for run_id, data in predictions.groupby("run_id"):
        body = data[data["compartment"] == "plant_body"]
        ax.semilogx(
            body["hours_after_exposure"],
            body["predicted_bq_l_water"] / body["observed_bq_l_water"],
            marker="o",
            label=run_id,
        )
    ax.axhline(1.0, color="black", linewidth=1)
    ax.set_xlabel("Hours after exposure")
    ax.set_ylabel("Predicted / observed")
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(figure_dir / "sb1_predicted_observed_ratio.png", dpi=180)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    protocol = load_mapping(PROTOCOL)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    if args.stage in {"baseline", "all"}:
        baseline_stage(protocol)
    if args.stage in {"calibrate", "all"}:
        calibration_stage(protocol)
    if args.stage in {"holdout", "all"}:
        holdout_stage()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"SB1 benchmark failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
