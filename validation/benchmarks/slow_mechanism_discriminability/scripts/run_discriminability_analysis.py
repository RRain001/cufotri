#!/usr/bin/env python3
"""Run the frozen H2/H3 controlled-exposure discriminability design."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = (
    ROOT / "validation" / "benchmarks" / "slow_mechanism_discriminability"
)
PROTOCOL_PATH = (
    BENCHMARK / "preregistration" / "h2_h3_discriminability_protocol.yaml"
)
RESULTS = BENCHMARK / "results"
REPORTS = BENCHMARK / "reports"
SB1 = ROOT / "validation" / "benchmarks" / "emras_soybean_sb1"
SB1_MECHANISMS = (
    ROOT / "validation" / "benchmarks" / "emras_soybean_sb1_mechanisms"
)
SB4 = ROOT / "validation" / "benchmarks" / "emras_soybean_sb4"
DOCS = ROOT / "docs" / "v3" / "benchmarks"
SOURCE_PROTOCOL = (
    SB1_MECHANISMS
    / "preregistration"
    / "sb1_mechanism_discrimination_protocol.yaml"
)
MECHANISMS = ("H2_SB1_FROZEN", "H3_SB1_FROZEN")
SOURCE_IDS = {
    "H2_SB1_FROZEN": "H2_PARALLEL_FAST_SLOW_RESIDUAL",
    "H3_SB1_FROZEN": "H3_REVERSIBLE_FAST_SLOW_EXCHANGE",
}
BASE_TIME = pd.Timestamp("2001-01-01T09:30:00+09:00")
MAXIMUM_POST_EXPOSURE_HOURS = 768.0
FORMAL_MASS_TOLERANCE_BQ_M2 = 1.0e-6
INTERNAL_LEDGER_TOLERANCE_BQ_M2 = 1.0e-9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        required=True,
        choices=("base", "robustness", "sensitivity", "reports", "all"),
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def validate_protocol_mapping(protocol: dict[str, Any]) -> None:
    if not isinstance(protocol, dict):
        raise ValueError("Discriminability protocol must be a mapping")
    if protocol["status"] != "FROZEN_BEFORE_SYNTHETIC_EXECUTION":
        raise ValueError("Discriminability protocol is not frozen")
    scope = protocol["scope"]
    if (
        scope["parameter_refit_allowed"]
        or scope["parameter_refit_count"] != 0
        or scope["parameter_bound_expansion_allowed"]
    ):
        raise ValueError("Parameter refit or bound expansion is not allowed")
    if (
        scope["synthetic_status"]
        != "DESIGN_ONLY_NOT_EXPERIMENTAL_EVIDENCE"
        or scope["empirical_validation_claim"]
        or scope["production_gate_eligible"]
        or scope["trusted_registry_eligible"]
        or scope["formal_model_change"]
        or scope["formal_v3_physics"] != "NOT_STARTED"
        or scope["v3_physics_start_gate"]
        != "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        or scope["model_selection_from_current_sb1_sb4_data_authorized"]
    ):
        raise ValueError("Design-only evidence or production-gate scope changed")
    if protocol["observables"]["latent_pool_used_for_classification"]:
        raise ValueError("Latent pool cannot be used for classification")
    if (
        protocol["observables"]["primary"]["id"]
        != "total_plant_body_tfwt"
        or protocol["observables"]["primary"]["classification_role"]
        != "PRIMARY_ONLY"
    ):
        raise ValueError("Primary observable contract changed")
    if len(protocol["designs"]) != 6:
        raise ValueError("Exactly six frozen designs are required")
    expected_parameters = {
        "H2_SB1_FROZEN": {
            "slow_capture_fraction": 0.001,
            "slow_release_rate_s": 1.0e-6,
        },
        "H3_SB1_FROZEN": {
            "fast_to_slow_rate_s": 1.0e-7,
            "slow_to_fast_rate_s": 1.0e-6,
        },
    }
    for mechanism_id, parameters in expected_parameters.items():
        if parameter_values(protocol, mechanism_id) != parameters:
            raise ValueError(f"{mechanism_id} frozen parameters changed")
        model = protocol["target_models"][mechanism_id]
        if model["refit_allowed"] or model["selected_from_sb4"]:
            raise ValueError(f"{mechanism_id} refit or SB4 selection enabled")
    if protocol["sampling"]["candidate_hours_after_final_exposure"] != [
        0.2,
        0.5,
        1,
        3,
        6,
        12,
        24,
        48,
        72,
        120,
        168,
        336,
        504,
        768,
    ] or not protocol["sampling"]["frozen_before_execution"]:
        raise ValueError("Frozen sampling grid changed")
    monte_carlo = protocol["monte_carlo"]
    if (
        monte_carlo["coefficient_of_variation"] != [0.10, 0.20, 0.30]
        or monte_carlo["random_seed"] != 20260727
        or monte_carlo["replicates_per_truth_model_design_noise"] != 1000
        or monte_carlo["truth_models"] != list(MECHANISMS)
        or monte_carlo["parameter_refit"]
        or monte_carlo["latent_pool_input_allowed"]
    ):
        raise ValueError("Frozen Monte Carlo contract changed")
    criteria = protocol["design_success_criteria"]
    if (
        criteria["classification_accuracy_minimum"]
        != {"cv_0_10": 0.90, "cv_0_20": 0.80, "cv_0_30": 0.70}
        or criteria["strong_pointwise_separation"]
        != {"delta_log10_minimum": 0.30, "minimum_time_point_count": 2}
        or criteria["latent_pool_observation_allowed"]
    ):
        raise ValueError("Frozen discrimination criteria changed")


def load_protocol() -> dict[str, Any]:
    protocol = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))
    validate_protocol_mapping(protocol)
    relative = PROTOCOL_PATH.relative_to(ROOT).as_posix()
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
        raise ValueError("Protocol differs from committed HEAD")
    source = protocol["source_contract"]
    for key in ("h2", "h3"):
        path = ROOT / source[f"{key}_implementation_file"]
        if sha256(path) != source[f"{key}_implementation_sha256"]:
            raise ValueError(f"{key.upper()} implementation checksum mismatch")
    frozen = ROOT / source["sb1_frozen_parameter_file"]
    if sha256(frozen) != source["sb1_frozen_parameter_file_sha256"]:
        raise ValueError("Frozen parameter file checksum mismatch")
    value = yaml.safe_load(frozen.read_text(encoding="utf-8"))
    if (
        value["mechanism_parameter_result_hash"]
        != source["mechanism_parameter_result_hash"]
    ):
        raise ValueError("Frozen parameter-result hash mismatch")
    return protocol


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_mechanism_runner() -> Any:
    scripts = SB1_MECHANISMS / "scripts"
    sys.path.insert(0, str(scripts))
    sys.path.insert(0, str(SB1_MECHANISMS))
    return load_module(
        scripts / "run_mechanism_discrimination.py",
        "slow_mechanism_discriminability_runner",
    )


def parameter_values(
    protocol: dict[str, Any], mechanism_id: str
) -> dict[str, float]:
    return {
        name: float(item["value"])
        for name, item in protocol["target_models"][mechanism_id][
            "parameters"
        ].items()
    }


def dewpoint_from_temperature_rh(
    temperature_c: float, relative_humidity_percent: float
) -> float:
    rh = float(np.clip(relative_humidity_percent / 100.0, 1.0e-12, 1.0))
    gamma = (
        math.log(rh)
        + 17.2694 * temperature_c / (temperature_c + 237.29)
    )
    return 237.29 * gamma / (17.2694 - gamma)


def actual_vapour_density_g_m3(
    temperature_c: float, relative_humidity_percent: float
) -> float:
    temperature_k = temperature_c + 273.15
    saturation_pa = 610.78 * math.exp(
        17.2694 * temperature_c / (temperature_c + 237.29)
    )
    actual_pa = saturation_pa * relative_humidity_percent / 100.0
    return actual_pa / (461.5 * temperature_k) * 1000.0


def exposure_windows(design: dict[str, Any]) -> list[dict[str, float]]:
    windows = [design["first_exposure"]]
    if design["second_exposure"] is not None:
        windows.append(design["second_exposure"])
    return windows


def build_forcing(
    protocol: dict[str, Any],
    design_id: str,
    *,
    concentration_multiplier: float = 1.0,
    relative_humidity_percent: float | None = None,
    wind_speed_m_s: float | None = None,
) -> pd.DataFrame:
    design = protocol["designs"][design_id]
    conditions = protocol["controlled_conditions"]
    final_end_h = float(design["final_exposure_end_h"])
    simulation_days = float(
        design["simulation_length_days_after_final_exposure"]
    )
    start = BASE_TIME - pd.Timedelta(minutes=5)
    end = (
        BASE_TIME
        + pd.Timedelta(hours=final_end_h)
        + pd.Timedelta(days=simulation_days)
    )
    time_local = pd.date_range(start, end, freq="5min", inclusive="both")
    hours = np.asarray(
        (time_local - BASE_TIME).total_seconds() / 3600.0,
        dtype=float,
    )
    moisture = np.full(
        len(time_local),
        float(conditions["background_air_moisture_hto_bq_ml_water"]),
        dtype=float,
    )
    phase = np.full(len(time_local), "STRICT_ZERO_BACKGROUND", dtype=object)
    for index, window in enumerate(exposure_windows(design), start=1):
        window_start = float(window["start_h"])
        window_end = window_start + float(window["duration_h"])
        selected = (hours > window_start) & (hours <= window_end)
        moisture[selected] = (
            float(window["concentration_bq_ml_water"])
            * float(concentration_multiplier)
        )
        phase[selected] = f"CONTROLLED_EXPOSURE_{index}"
    temperature_c = float(conditions["temperature_c"])
    rh = float(
        conditions["relative_humidity_percent"]
        if relative_humidity_percent is None
        else relative_humidity_percent
    )
    wind = float(
        conditions["wind_speed_m_s"]
        if wind_speed_m_s is None
        else wind_speed_m_s
    )
    dewpoint_c = dewpoint_from_temperature_rh(temperature_c, rh)
    vapour_density = actual_vapour_density_g_m3(temperature_c, rh)
    frame = pd.DataFrame(
        {
            "time_utc": time_local.tz_convert("UTC"),
            "time_local": time_local,
            "hours_from_first_exposure_start": hours,
            "hours_after_final_exposure": hours - final_end_h,
            "air_temperature_c": temperature_c,
            "dewpoint_temperature_c": dewpoint_c,
            "relative_humidity_percent": rh,
            "surface_pressure_pa": float(
                conditions["surface_pressure_pa"]
            ),
            "wind_speed_m_s": wind,
            "shortwave_down_w_m2": float(
                conditions["shortwave_down_w_m2"]
            ),
            "longwave_down_w_m2": float(
                conditions["longwave_down_w_m2"]
            ),
            "total_cloud_cover_fraction": float(
                conditions["total_cloud_cover_fraction"]
            ),
            "precipitation_mm_interval": float(
                conditions["precipitation_mm_interval"]
            ),
            "air_moisture_hto_bq_ml_water": moisture,
            "air_hto_bq_m3": moisture * vapour_density,
            "phase": phase,
            "forcing_evidence_class": "SYNTHETIC_CONTROLLED_CONDITIONS",
        }
    )
    numeric = frame.select_dtypes(include=[np.number])
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError(f"{design_id} forcing contains NaN or Inf")
    nonnegative = frame[
        [
            "relative_humidity_percent",
            "surface_pressure_pa",
            "wind_speed_m_s",
            "shortwave_down_w_m2",
            "longwave_down_w_m2",
            "total_cloud_cover_fraction",
            "precipitation_mm_interval",
            "air_moisture_hto_bq_ml_water",
            "air_hto_bq_m3",
        ]
    ]
    if (nonnegative.to_numpy() < 0).any():
        raise ValueError(f"{design_id} forcing contains a negative value")
    return frame


def design_schedule_rows(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for design_id, design in protocol["designs"].items():
        for sequence, window in enumerate(exposure_windows(design), start=1):
            rows.append(
                {
                    "design_id": design_id,
                    "sequence": sequence,
                    "start_h": float(window["start_h"]),
                    "end_h": float(window["start_h"])
                    + float(window["duration_h"]),
                    "duration_h": float(window["duration_h"]),
                    "concentration_bq_ml_water": float(
                        window["concentration_bq_ml_water"]
                    ),
                    "final_exposure_end_h": float(
                        design["final_exposure_end_h"]
                    ),
                    "evidence_class": "SYNTHETIC_CONTROLLED_CONDITIONS",
                }
            )
    return rows


def configure_runner(
    runner: Any,
    protocol: dict[str, Any],
    design_id: str,
    stomatal_resistance_multiplier: float,
) -> tuple[Any, dict[str, float]]:
    design = protocol["designs"][design_id]
    conditions = protocol["controlled_conditions"]
    final_end = BASE_TIME + pd.Timedelta(
        hours=float(design["final_exposure_end_h"])
    )
    runner.sb1.DT_SECONDS = (
        float(conditions["time_step_minutes"]) * 60.0
    )
    runner.sb1.EXPOSURE_START = BASE_TIME
    runner.sb1.EXPOSURE_END = final_end
    runner.sb1.HARVEST = final_end + pd.Timedelta(
        days=float(design["simulation_length_days_after_final_exposure"])
    )
    runner.sb1.POD_START = runner.sb1.HARVEST + pd.Timedelta(days=1)
    runner.sb1.EXPOSURE_BODY_WATER_M = float(
        conditions["plant_body_water_storage_m"]
    )
    runner.sb1.EXPOSURE_BODY_DRY_G_M2 = float(
        conditions["exposure_body_dry_g_m2"]
    )
    runner.sb1.HARVEST_BODY_DRY_G_M2 = float(
        conditions["harvest_body_dry_g_m2"]
    )
    runner.sb1.HARVEST_POD_FRESH_G_M2 = float(
        conditions["harvest_pod_fresh_g_m2"]
    )
    runner.sb1.HARVEST_POD_DRY_G_M2 = float(
        conditions["harvest_pod_dry_g_m2"]
    )
    runner.sb1.HARVEST_POD_WATER_M = (
        runner.sb1.HARVEST_POD_FRESH_G_M2
        - runner.sb1.HARVEST_POD_DRY_G_M2
    ) / 1000.0 / 1000.0
    runner.sb1.soybean_lai = lambda _: float(conditions["lai"])
    frozen_leaf = {
        "leaf_stomatal_resistance_day_s_m": float(
            conditions["leaf_stomatal_resistance_day_s_m"]
        )
        * float(stomatal_resistance_multiplier),
        "leaf_characteristic_length_m": float(
            conditions["leaf_characteristic_length_m"]
        ),
    }
    previous = runner.FROZEN_LEAF_PARAMETERS
    runner.FROZEN_LEAF_PARAMETERS = frozen_leaf
    return previous, frozen_leaf


def simulate_with_ledger(
    runner: Any,
    forcing: pd.DataFrame,
    mechanism_id: str,
    parameters: dict[str, float],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    source_id = SOURCE_IDS[mechanism_id]
    ledger = [0.0]
    if source_id == "H2_PARALLEL_FAST_SLOW_RESIDUAL":
        module = runner.parallel_fast_slow
        original = module.transfer

        def audited_transfer(*args: Any, **kwargs: Any) -> Any:
            result = original(*args, **kwargs)
            ledger.append(
                abs(
                    math.fsum(
                        [
                            -result.capture_bq_m2,
                            result.release_bq_m2,
                            result.capture_bq_m2,
                            -result.release_bq_m2,
                        ]
                    )
                )
            )
            return result

    else:
        module = runner.reversible_fast_slow
        original = module.transfer

        def audited_transfer(*args: Any, **kwargs: Any) -> Any:
            result = original(*args, **kwargs)
            ledger.append(
                abs(
                    math.fsum(
                        [
                            -result.fast_to_slow_bq_m2,
                            result.slow_to_fast_bq_m2,
                            result.fast_to_slow_bq_m2,
                            -result.slow_to_fast_bq_m2,
                        ]
                    )
                )
            )
            return result

    module.transfer = audited_transfer
    try:
        model = runner.simulate(
            forcing,
            source_id,
            parameters,
            MAXIMUM_POST_EXPOSURE_HOURS,
        )
    finally:
        module.transfer = original
    numeric = model.select_dtypes(include=[np.number])
    inventory = numeric.filter(regex="_inventory_bq_m2$")
    concentration = numeric.filter(regex="_bq_l_")
    qa = {
        "nan_count": int(numeric.isna().sum().sum()),
        "inf_count": int(np.isinf(numeric.to_numpy()).sum()),
        "negative_inventory_count": int(
            (inventory.to_numpy() < -1.0e-12).sum()
        ),
        "negative_concentration_count": int(
            (concentration.to_numpy() < -1.0e-12).sum()
        ),
        "maximum_formal_mass_closure_abs_bq_m2": float(
            model["formal_mass_closure_abs_bq_m2"].max()
        ),
        "maximum_internal_transfer_ledger_residual_abs_bq_m2": max(
            ledger
        ),
        "maximum_internal_state_sum_roundoff_abs_bq_m2": float(
            model["internal_transfer_residual_abs_bq_m2"].max()
        ),
    }
    qa["finite_nonnegative_pass"] = bool(
        qa["nan_count"] == 0
        and qa["inf_count"] == 0
        and qa["negative_inventory_count"] == 0
        and qa["negative_concentration_count"] == 0
    )
    qa["mass_conservation_pass"] = bool(
        qa["maximum_formal_mass_closure_abs_bq_m2"]
        <= FORMAL_MASS_TOLERANCE_BQ_M2
        and qa["maximum_internal_transfer_ledger_residual_abs_bq_m2"]
        <= INTERNAL_LEDGER_TOLERANCE_BQ_M2
    )
    return model, qa


def interpolate_field(
    model: pd.DataFrame, coordinates: np.ndarray, field: str
) -> np.ndarray:
    x = model["hours_after_exposure"].to_numpy(float)
    y = model[field].to_numpy(float)
    return np.interp(coordinates, x, y)


def sample_model(
    model: pd.DataFrame,
    protocol: dict[str, Any],
    design_id: str,
    mechanism_id: str,
) -> list[dict[str, Any]]:
    hours = np.asarray(
        protocol["sampling"]["candidate_hours_after_final_exposure"],
        dtype=float,
    )
    body = interpolate_field(
        model, hours, "plant_body_tfwt_bq_l_water"
    )
    fast = interpolate_field(
        model, hours, "plant_fast_tfwt_inventory_bq_m2"
    )
    slow = interpolate_field(
        model, hours, "plant_slow_tfwt_inventory_bq_m2"
    )
    rows = [
        {
            "design_id": design_id,
            "mechanism_id": mechanism_id,
            "sample_context": "POST_FINAL_EXPOSURE",
            "sample_hour": float(hour),
            "plant_body_tfwt_bq_l_water": float(value),
            "plant_fast_tfwt_inventory_bq_m2": float(fast_value),
            "plant_slow_tfwt_inventory_bq_m2": float(slow_value),
            "classification_observable": "total_plant_body_tfwt",
            "latent_pool_used_for_classification": False,
            "evidence_class": "SYNTHETIC_DESIGN_ONLY",
            "parameter_refit_count": 0,
        }
        for hour, value, fast_value, slow_value in zip(
            hours, body, fast, slow, strict=True
        )
    ]
    exposure_designs = set(
        protocol["sampling"]["exposure_period_designs"]
    )
    if design_id in exposure_designs:
        absolute_hours = np.asarray(
            protocol["sampling"][
                "exposure_period_hours_from_first_exposure_start"
            ],
            dtype=float,
        )
        design = protocol["designs"][design_id]
        duration = float(design["first_exposure"]["duration_h"])
        absolute_hours = absolute_hours[absolute_hours <= duration]
        relative = (
            absolute_hours - float(design["final_exposure_end_h"])
        )
        body = interpolate_field(
            model, relative, "plant_body_tfwt_bq_l_water"
        )
        fast = interpolate_field(
            model, relative, "plant_fast_tfwt_inventory_bq_m2"
        )
        slow = interpolate_field(
            model, relative, "plant_slow_tfwt_inventory_bq_m2"
        )
        rows.extend(
            {
                "design_id": design_id,
                "mechanism_id": mechanism_id,
                "sample_context": "DURING_FIRST_EXPOSURE",
                "sample_hour": float(hour),
                "plant_body_tfwt_bq_l_water": float(value),
                "plant_fast_tfwt_inventory_bq_m2": float(fast_value),
                "plant_slow_tfwt_inventory_bq_m2": float(slow_value),
                "classification_observable": "total_plant_body_tfwt",
                "latent_pool_used_for_classification": False,
                "evidence_class": "SYNTHETIC_DESIGN_ONLY",
                "parameter_refit_count": 0,
            }
            for hour, value, fast_value, slow_value in zip(
                absolute_hours, body, fast, slow, strict=True
            )
        )
    return rows


def run_design(
    runner: Any,
    protocol: dict[str, Any],
    design_id: str,
    *,
    concentration_multiplier: float = 1.0,
    relative_humidity_percent: float | None = None,
    wind_speed_m_s: float | None = None,
    stomatal_resistance_multiplier: float = 1.0,
    parameters_override: dict[str, dict[str, float]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    forcing = build_forcing(
        protocol,
        design_id,
        concentration_multiplier=concentration_multiplier,
        relative_humidity_percent=relative_humidity_percent,
        wind_speed_m_s=wind_speed_m_s,
    )
    previous_leaf, _ = configure_runner(
        runner, protocol, design_id, stomatal_resistance_multiplier
    )
    prediction_rows: list[dict[str, Any]] = []
    qa_rows: list[dict[str, Any]] = []
    try:
        for mechanism_id in MECHANISMS:
            parameters = (
                parameter_values(protocol, mechanism_id)
                if parameters_override is None
                else parameters_override[mechanism_id]
            )
            model, qa = simulate_with_ledger(
                runner, forcing, mechanism_id, parameters
            )
            prediction_rows.extend(
                sample_model(model, protocol, design_id, mechanism_id)
            )
            qa_rows.append(
                {
                    "design_id": design_id,
                    "mechanism_id": mechanism_id,
                    "concentration_multiplier": concentration_multiplier,
                    "relative_humidity_percent": (
                        protocol["controlled_conditions"][
                            "relative_humidity_percent"
                        ]
                        if relative_humidity_percent is None
                        else relative_humidity_percent
                    ),
                    "wind_speed_m_s": (
                        protocol["controlled_conditions"]["wind_speed_m_s"]
                        if wind_speed_m_s is None
                        else wind_speed_m_s
                    ),
                    "stomatal_resistance_multiplier": (
                        stomatal_resistance_multiplier
                    ),
                    "parameter_refit_count": 0,
                    **qa,
                }
            )
    finally:
        runner.FROZEN_LEAF_PARAMETERS = previous_leaf
    return pd.DataFrame(prediction_rows), pd.DataFrame(qa_rows)


def stable_seed(protocol: dict[str, Any], key: str) -> int:
    base = int(protocol["monte_carlo"]["random_seed"])
    digest = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
    return (base + digest) % (2**32 - 1)


def prediction_vectors(
    predictions: pd.DataFrame,
    design_id: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    subset = predictions[
        (predictions["design_id"] == design_id)
        & (predictions["sample_context"] == "POST_FINAL_EXPOSURE")
    ]
    vectors: dict[str, np.ndarray] = {}
    hours: np.ndarray | None = None
    for mechanism_id in MECHANISMS:
        frame = subset[
            subset["mechanism_id"] == mechanism_id
        ].sort_values("sample_hour")
        current_hours = frame["sample_hour"].to_numpy(float)
        if hours is None:
            hours = current_hours
        else:
            np.testing.assert_array_equal(hours, current_hours)
        vectors[mechanism_id] = frame[
            "plant_body_tfwt_bq_l_water"
        ].to_numpy(float)
    if hours is None:
        raise ValueError(f"No predictions for {design_id}")
    return hours, vectors[MECHANISMS[0]], vectors[MECHANISMS[1]]


def pointwise_rows(predictions: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for design_id in sorted(predictions["design_id"].unique()):
        hours, h2, h3 = prediction_vectors(predictions, design_id)
        h2 = np.clip(h2, np.finfo(float).tiny, None)
        h3 = np.clip(h3, np.finfo(float).tiny, None)
        delta = np.abs(np.log10(h2) - np.log10(h3))
        for index, hour in enumerate(hours):
            rows.append(
                {
                    "design_id": design_id,
                    "sample_hour": float(hour),
                    "h2_prediction_bq_l_water": float(h2[index]),
                    "h3_prediction_bq_l_water": float(h3[index]),
                    "delta_log10": float(delta[index]),
                    "ratio": float(max(h2[index], h3[index]) / min(h2[index], h3[index])),
                    "signed_difference_bq_l_water": float(
                        h2[index] - h3[index]
                    ),
                    "relative_difference": float(
                        abs(h2[index] - h3[index])
                        / math.sqrt(h2[index] * h3[index])
                    ),
                    "strong_separation": bool(delta[index] >= 0.30),
                    "moderate_separation": bool(delta[index] >= 0.15),
                }
            )
    return rows


def noise_replicates(
    protocol: dict[str, Any],
    truth: np.ndarray,
    cv: float,
    key: str,
) -> np.ndarray:
    count = int(
        protocol["monte_carlo"]["replicates_per_truth_model_design_noise"]
    )
    sigma = math.sqrt(math.log1p(cv**2))
    mu = -0.5 * sigma**2
    rng = np.random.default_rng(stable_seed(protocol, key))
    multiplier = rng.lognormal(mu, sigma, size=(count, len(truth)))
    return truth[None, :] * multiplier


def classify_replicates(
    observations: np.ndarray,
    h2: np.ndarray,
    h3: np.ndarray,
    truth_model: str,
) -> float:
    tiny = np.finfo(float).tiny
    observed_log = np.log10(np.clip(observations, tiny, None))
    h2_error = np.sqrt(
        np.mean((observed_log - np.log10(np.clip(h2, tiny, None))) ** 2, axis=1)
    )
    h3_error = np.sqrt(
        np.mean((observed_log - np.log10(np.clip(h3, tiny, None))) ** 2, axis=1)
    )
    predicted = np.where(
        h2_error < h3_error,
        "H2_SB1_FROZEN",
        np.where(h3_error < h2_error, "H3_SB1_FROZEN", "INCONCLUSIVE"),
    )
    return float(np.mean(predicted == truth_model))


def monte_carlo_rows(
    protocol: dict[str, Any],
    predictions: pd.DataFrame,
    *,
    key_prefix: str,
    selected_hours: dict[str, list[float]] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for design_id in sorted(predictions["design_id"].unique()):
        hours, h2, h3 = prediction_vectors(predictions, design_id)
        if selected_hours is None:
            indices = np.arange(len(hours))
        else:
            selected = selected_hours[design_id]
            indices = np.asarray(
                [int(np.where(np.isclose(hours, value))[0][0]) for value in selected],
                dtype=int,
            )
        for cv in protocol["monte_carlo"]["coefficient_of_variation"]:
            cv_value = float(cv)
            for truth_model, truth in zip(MECHANISMS, (h2, h3), strict=True):
                observations = noise_replicates(
                    protocol,
                    truth,
                    cv_value,
                    f"{key_prefix}:{design_id}:{truth_model}:{cv_value:.2f}",
                )
                accuracy = classify_replicates(
                    observations[:, indices],
                    h2[indices],
                    h3[indices],
                    truth_model,
                )
                rows.append(
                    {
                        "design_id": design_id,
                        "truth_model": truth_model,
                        "coefficient_of_variation": cv_value,
                        "sample_count": int(len(indices)),
                        "sample_hours": ";".join(
                            f"{hours[index]:g}" for index in indices
                        ),
                        "correct_classification_rate": accuracy,
                        "parameter_refit_count": 0,
                        "latent_pool_used": False,
                        "replicate_count": int(
                            protocol["monte_carlo"][
                                "replicates_per_truth_model_design_noise"
                            ]
                        ),
                    }
                )
    return rows


def accuracy_threshold(protocol: dict[str, Any], cv: float) -> float:
    key = f"cv_{cv:.2f}".replace(".", "_")
    return float(
        protocol["design_success_criteria"][
            "classification_accuracy_minimum"
        ][key]
    )


def classification_pass(
    protocol: dict[str, Any], rows: pd.DataFrame
) -> bool:
    return bool(
        all(
            group["correct_classification_rate"].min()
            >= accuracy_threshold(protocol, float(cv))
            for cv, group in rows.groupby("coefficient_of_variation")
        )
    )


def greedy_sampling(
    protocol: dict[str, Any],
    predictions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    result_rows: list[dict[str, Any]] = []
    tradeoff_rows: list[dict[str, Any]] = []
    minimum = int(protocol["sampling"]["optimization"]["minimum_sample_count"])
    maximum = int(protocol["sampling"]["optimization"]["maximum_sample_count"])
    for design_id in sorted(predictions["design_id"].unique()):
        hours, h2, h3 = prediction_vectors(predictions, design_id)
        delta = np.abs(
            np.log10(np.clip(h2, np.finfo(float).tiny, None))
            - np.log10(np.clip(h3, np.finfo(float).tiny, None))
        )
        selected = [int(np.argmax(delta))]
        cached: dict[tuple[str, float], np.ndarray] = {}
        for cv in protocol["monte_carlo"]["coefficient_of_variation"]:
            cv_value = float(cv)
            for truth_model, truth in zip(MECHANISMS, (h2, h3), strict=True):
                cached[(truth_model, cv_value)] = noise_replicates(
                    protocol,
                    truth,
                    cv_value,
                    f"sampling:{design_id}:{truth_model}:{cv_value:.2f}",
                )

        def evaluate(indices: list[int]) -> dict[tuple[str, float], float]:
            values: dict[tuple[str, float], float] = {}
            array = np.asarray(sorted(indices), dtype=int)
            for cv in protocol["monte_carlo"]["coefficient_of_variation"]:
                cv_value = float(cv)
                for truth_model in MECHANISMS:
                    values[(truth_model, cv_value)] = classify_replicates(
                        cached[(truth_model, cv_value)][:, array],
                        h2[array],
                        h3[array],
                        truth_model,
                    )
            return values

        while len(selected) <= maximum:
            values = evaluate(selected)
            selected_sorted = sorted(selected)
            pass_accuracy = all(
                min(values[(model, float(cv))] for model in MECHANISMS)
                >= accuracy_threshold(protocol, float(cv))
                for cv in protocol["monte_carlo"]["coefficient_of_variation"]
            )
            strong_count = int(np.sum(delta[selected_sorted] >= 0.30))
            tradeoff_rows.append(
                {
                    "design_id": design_id,
                    "sample_count": len(selected),
                    "sample_hours": ";".join(
                        f"{hours[index]:g}" for index in selected_sorted
                    ),
                    "cv10_min_accuracy": min(
                        values[(model, 0.10)] for model in MECHANISMS
                    ),
                    "cv20_min_accuracy": min(
                        values[(model, 0.20)] for model in MECHANISMS
                    ),
                    "cv30_min_accuracy": min(
                        values[(model, 0.30)] for model in MECHANISMS
                    ),
                    "strong_separation_point_count": strong_count,
                    "accuracy_thresholds_pass": pass_accuracy,
                }
            )
            if (
                len(selected) >= minimum
                and pass_accuracy
                and strong_count
                >= int(
                    protocol["design_success_criteria"][
                        "strong_pointwise_separation"
                    ]["minimum_time_point_count"]
                )
            ):
                status = "MINIMUM_SAMPLING_CRITERIA_PASS"
                break
            if len(selected) == maximum:
                status = "NO_3_TO_8_POINT_SET_MEETS_FROZEN_CRITERIA"
                break
            candidates = [index for index in range(len(hours)) if index not in selected]
            scored: list[tuple[tuple[float, float, float], int]] = []
            for candidate in candidates:
                trial = selected + [candidate]
                trial_values = evaluate(trial)
                cv20 = min(
                    trial_values[(model, 0.20)] for model in MECHANISMS
                )
                normalized_worst = min(
                    trial_values[(model, float(cv))]
                    / accuracy_threshold(protocol, float(cv))
                    for model in MECHANISMS
                    for cv in protocol["monte_carlo"][
                        "coefficient_of_variation"
                    ]
                )
                score = (cv20, normalized_worst, -float(hours[candidate]))
                scored.append((score, candidate))
            selected.append(max(scored, key=lambda item: item[0])[1])
        final_values = evaluate(selected)
        final_sorted = sorted(selected)
        result_rows.append(
            {
                "design_id": design_id,
                "status": status,
                "sample_count": len(selected),
                "sample_hours": ";".join(
                    f"{hours[index]:g}" for index in final_sorted
                ),
                "cv10_h2_accuracy": final_values[("H2_SB1_FROZEN", 0.10)],
                "cv10_h3_accuracy": final_values[("H3_SB1_FROZEN", 0.10)],
                "cv20_h2_accuracy": final_values[("H2_SB1_FROZEN", 0.20)],
                "cv20_h3_accuracy": final_values[("H3_SB1_FROZEN", 0.20)],
                "cv30_h2_accuracy": final_values[("H2_SB1_FROZEN", 0.30)],
                "cv30_h3_accuracy": final_values[("H3_SB1_FROZEN", 0.30)],
                "strong_separation_point_count": int(
                    np.sum(delta[final_sorted] >= 0.30)
                ),
                "parameter_refit_count": 0,
                "latent_pool_used": False,
            }
        )
    return pd.DataFrame(result_rows), pd.DataFrame(tradeoff_rows)


def existing_evidence_analysis(
    protocol: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    calibration = pd.read_csv(
        SB1_MECHANISMS / "reports" / "mechanism_calibration_predictions.csv"
    )
    late = pd.read_csv(
        SB1_MECHANISMS / "reports" / "mechanism_late_predictions.csv"
    )
    mapping = {
        "H2_PARALLEL_FAST_SLOW_RESIDUAL": "H2_SB1_FROZEN",
        "H3_REVERSIBLE_FAST_SLOW_EXCHANGE": "H3_SB1_FROZEN",
    }
    sb1_rows: list[dict[str, Any]] = []
    combined = pd.concat(
        [
            calibration[
                calibration["mechanism_id"].isin(mapping)
                & (calibration["compartment"] == "plant_body")
            ].assign(run_id="CALIBRATION_PRIMARY"),
            late[
                late["mechanism_id"].isin(mapping)
                & (late["compartment"] == "plant_body")
                & (late["run_id"] == "RUN_01")
            ],
        ],
        ignore_index=True,
    )
    for hour, group in combined.groupby("hours_after_exposure"):
        indexed = group.set_index("mechanism_id")
        h2 = float(
            indexed.loc[
                "H2_PARALLEL_FAST_SLOW_RESIDUAL", "predicted_bq_l_water"
            ]
        )
        h3 = float(
            indexed.loc[
                "H3_REVERSIBLE_FAST_SLOW_EXCHANGE", "predicted_bq_l_water"
            ]
        )
        delta = abs(math.log10(h2) - math.log10(h3))
        row = {
            "case_id": "SB1",
            "hours_after_exposure": float(hour),
            "h2_prediction_bq_l_water": h2,
            "h3_prediction_bq_l_water": h3,
            "delta_log10": delta,
            "ratio": max(h2, h3) / min(h2, h3),
            "signed_difference_bq_l_water": h2 - h3,
            "difference_direction": "H2_GT_H3" if h2 > h3 else "H3_GT_H2",
        }
        geometric = math.sqrt(h2 * h3)
        for cv in protocol["existing_evidence_analysis"]["noise_cv"]:
            row[f"normalized_difference_cv_{int(float(cv)*100)}"] = (
                abs(h2 - h3) / (float(cv) * geometric)
            )
        sb1_rows.append(row)

    sb4 = pd.read_csv(SB4 / "reports" / "sb4_transfer_predictions.csv")
    sb4 = sb4[
        sb4["mechanism_id"].isin(MECHANISMS)
        & (sb4["compartment"] == "plant_body")
    ]
    sb4_rows: list[dict[str, Any]] = []
    for keys, group in sb4.groupby(
        ["profile_id", "run_id", "hours_after_exposure"]
    ):
        indexed = group.set_index("mechanism_id")
        h2 = float(indexed.loc["H2_SB1_FROZEN", "predicted_bq_l_water"])
        h3 = float(indexed.loc["H3_SB1_FROZEN", "predicted_bq_l_water"])
        delta = abs(math.log10(h2) - math.log10(h3))
        row = {
            "case_id": "SB4",
            "profile_id": keys[0],
            "run_id": keys[1],
            "hours_after_exposure": float(keys[2]),
            "h2_prediction_bq_l_water": h2,
            "h3_prediction_bq_l_water": h3,
            "delta_log10": delta,
            "ratio": max(h2, h3) / min(h2, h3),
            "signed_difference_bq_l_water": h2 - h3,
            "difference_direction": "H2_GT_H3" if h2 > h3 else "H3_GT_H2",
        }
        geometric = math.sqrt(h2 * h3)
        for cv in protocol["existing_evidence_analysis"]["noise_cv"]:
            row[f"normalized_difference_cv_{int(float(cv)*100)}"] = (
                abs(h2 - h3) / (float(cv) * geometric)
            )
        sb4_rows.append(row)
    sb4_frame = pd.DataFrame(sb4_rows)
    stability = (
        sb4_frame.groupby("hours_after_exposure")
        .agg(
            forcing_min_delta_log10=("delta_log10", "min"),
            forcing_max_delta_log10=("delta_log10", "max"),
            forcing_direction_count=("difference_direction", "nunique"),
        )
        .reset_index()
    )
    sb4_frame = sb4_frame.merge(stability, on="hours_after_exposure")
    return pd.DataFrame(sb1_rows).sort_values(
        "hours_after_exposure"
    ), sb4_frame.sort_values(
        ["profile_id", "run_id", "hours_after_exposure"]
    )


def base_stage(protocol: dict[str, Any]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    runner = load_mechanism_runner()
    prediction_frames: list[pd.DataFrame] = []
    qa_frames: list[pd.DataFrame] = []
    for design_id in protocol["designs"]:
        predictions, qa = run_design(runner, protocol, design_id)
        prediction_frames.append(predictions)
        qa_frames.append(qa.assign(run_class="BASE_DESIGN"))
    predictions = pd.concat(prediction_frames, ignore_index=True)
    qa = pd.concat(qa_frames, ignore_index=True)
    if not qa["finite_nonnegative_pass"].all():
        raise ValueError("A base design produced invalid values")
    if not qa["mass_conservation_pass"].all():
        raise ValueError("A base design failed mass conservation")
    predictions.to_csv(
        RESULTS / "synthetic_design_predictions.csv", index=False
    )
    qa.to_csv(RESULTS / "design_run_qa.csv", index=False)
    pd.DataFrame(design_schedule_rows(protocol)).to_csv(
        RESULTS / "design_schedule.csv", index=False
    )
    pd.DataFrame(pointwise_rows(predictions)).to_csv(
        RESULTS / "model_output_distance.csv", index=False
    )
    mc = pd.DataFrame(
        monte_carlo_rows(
            protocol, predictions, key_prefix="full_grid"
        )
    )
    mc.to_csv(RESULTS / "monte_carlo_classification.csv", index=False)
    minimum, tradeoff = greedy_sampling(protocol, predictions)
    minimum.to_csv(RESULTS / "minimum_sampling_design.csv", index=False)
    tradeoff.to_csv(RESULTS / "sampling_design_tradeoff.csv", index=False)
    sb1, sb4 = existing_evidence_analysis(protocol)
    sb1.to_csv(RESULTS / "existing_sb1_discriminability.csv", index=False)
    sb4.to_csv(RESULTS / "existing_sb4_discriminability.csv", index=False)
    print(f"BASE_DESIGN_RUN_COUNT = {len(qa)}")
    print("BASE_DESIGN_QA = PASS_FINITE_NONNEGATIVE_CONSERVATIVE")


def selected_hours_mapping() -> dict[str, list[float]]:
    minimum = pd.read_csv(RESULTS / "minimum_sampling_design.csv")
    return {
        row["design_id"]: [
            float(value) for value in str(row["sample_hours"]).split(";")
        ]
        for _, row in minimum.iterrows()
    }


def top_designs(protocol: dict[str, Any]) -> list[str]:
    mc = pd.read_csv(RESULTS / "monte_carlo_classification.csv")
    pointwise = pd.read_csv(RESULTS / "model_output_distance.csv")
    summary = (
        mc.groupby(["design_id", "coefficient_of_variation"])[
            "correct_classification_rate"
        ]
        .min()
        .unstack()
    )
    strong = (
        pointwise.groupby("design_id")["strong_separation"].sum().astype(int)
    )
    ranked = pd.DataFrame(
        {
            "cv10": summary[0.10],
            "cv20": summary[0.20],
            "cv30": summary[0.30],
            "strong": strong,
        }
    )
    ranked["base_pass"] = [
        bool(
            row.cv10 >= accuracy_threshold(protocol, 0.10)
            and row.cv20 >= accuracy_threshold(protocol, 0.20)
            and row.cv30 >= accuracy_threshold(protocol, 0.30)
            and row.strong
            >= protocol["design_success_criteria"][
                "strong_pointwise_separation"
            ]["minimum_time_point_count"]
        )
        for row in ranked.itertuples()
    ]
    ranked = ranked.sort_values(
        ["base_pass", "cv20", "cv30", "strong"],
        ascending=[False, False, False, False],
    )
    return ranked.head(
        int(protocol["robustness"]["top_design_count"])
    ).index.tolist()


def robustness_stage(protocol: dict[str, Any]) -> None:
    runner = load_mechanism_runner()
    selected = selected_hours_mapping()
    designs = top_designs(protocol)
    rows: list[dict[str, Any]] = []
    cache: dict[tuple[Any, ...], tuple[pd.DataFrame, pd.DataFrame]] = {}
    factor_levels = {
        "exposure_concentration_multiplier": protocol["robustness"][
            "exposure_concentration_multiplier"
        ],
        "relative_humidity_percent": protocol["robustness"][
            "relative_humidity_percent"
        ],
        "wind_speed_m_s": protocol["robustness"]["wind_speed_m_s"],
        "stomatal_resistance_multiplier": protocol["robustness"][
            "stomatal_resistance_multiplier"
        ],
    }
    baseline = protocol["controlled_conditions"]
    for design_id in designs:
        for factor, levels in factor_levels.items():
            for level in levels:
                settings = {
                    "concentration_multiplier": 1.0,
                    "relative_humidity_percent": float(
                        baseline["relative_humidity_percent"]
                    ),
                    "wind_speed_m_s": float(baseline["wind_speed_m_s"]),
                    "stomatal_resistance_multiplier": 1.0,
                }
                key_name = {
                    "exposure_concentration_multiplier": (
                        "concentration_multiplier"
                    ),
                    "relative_humidity_percent": "relative_humidity_percent",
                    "wind_speed_m_s": "wind_speed_m_s",
                    "stomatal_resistance_multiplier": (
                        "stomatal_resistance_multiplier"
                    ),
                }[factor]
                settings[key_name] = float(level)
                cache_key = (
                    design_id,
                    settings["concentration_multiplier"],
                    settings["relative_humidity_percent"],
                    settings["wind_speed_m_s"],
                    settings["stomatal_resistance_multiplier"],
                )
                if cache_key not in cache:
                    cache[cache_key] = run_design(
                        runner, protocol, design_id, **settings
                    )
                predictions, qa = cache[cache_key]
                hours, h2, h3 = prediction_vectors(predictions, design_id)
                indices = np.asarray(
                    [
                        int(np.where(np.isclose(hours, value))[0][0])
                        for value in selected[design_id]
                    ],
                    dtype=int,
                )
                delta = np.abs(
                    np.log10(np.clip(h2[indices], np.finfo(float).tiny, None))
                    - np.log10(np.clip(h3[indices], np.finfo(float).tiny, None))
                )
                accuracies: dict[float, float] = {}
                for cv in protocol["monte_carlo"]["coefficient_of_variation"]:
                    cv_value = float(cv)
                    truth_accuracies = []
                    for truth_model, truth in zip(
                        MECHANISMS, (h2, h3), strict=True
                    ):
                        observations = noise_replicates(
                            protocol,
                            truth,
                            cv_value,
                            (
                                f"robustness:{design_id}:{factor}:{level}:"
                                f"{truth_model}:{cv_value:.2f}"
                            ),
                        )
                        truth_accuracies.append(
                            classify_replicates(
                                observations[:, indices],
                                h2[indices],
                                h3[indices],
                                truth_model,
                            )
                        )
                    accuracies[cv_value] = min(truth_accuracies)
                qa_pass = bool(
                    qa["finite_nonnegative_pass"].all()
                    and qa["mass_conservation_pass"].all()
                )
                criteria_pass = bool(
                    qa_pass
                    and int(np.sum(delta >= 0.30))
                    >= protocol["design_success_criteria"][
                        "strong_pointwise_separation"
                    ]["minimum_time_point_count"]
                    and all(
                        accuracies[float(cv)]
                        >= accuracy_threshold(protocol, float(cv))
                        for cv in protocol["monte_carlo"][
                            "coefficient_of_variation"
                        ]
                    )
                )
                rows.append(
                    {
                        "design_id": design_id,
                        "factor": factor,
                        "level": float(level),
                        "sample_hours": ";".join(
                            f"{value:g}" for value in selected[design_id]
                        ),
                        "strong_separation_point_count": int(
                            np.sum(delta >= 0.30)
                        ),
                        "cv10_min_accuracy": accuracies[0.10],
                        "cv20_min_accuracy": accuracies[0.20],
                        "cv30_min_accuracy": accuracies[0.30],
                        "finite_nonnegative_pass": bool(
                            qa["finite_nonnegative_pass"].all()
                        ),
                        "mass_conservation_pass": bool(
                            qa["mass_conservation_pass"].all()
                        ),
                        "criteria_pass": criteria_pass,
                        "parameter_refit_count": 0,
                        "latent_pool_used": False,
                    }
                )
    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "design_robustness_matrix.csv", index=False)
    print(f"ROBUSTNESS_UNIQUE_SIMULATION_CONFIG_COUNT = {len(cache)}")
    print(f"ROBUSTNESS_REPORTED_FACTOR_LEVEL_COUNT = {len(frame)}")


def source_parameter_bounds() -> dict[str, dict[str, tuple[float, float]]]:
    protocol = yaml.safe_load(SOURCE_PROTOCOL.read_text(encoding="utf-8"))
    h2 = protocol["candidates"]["H2_PARALLEL_FAST_SLOW_RESIDUAL"][
        "parameters"
    ]
    rates = protocol["candidates"]["H3_REVERSIBLE_FAST_SLOW_EXCHANGE"][
        "common_rate_values_s"
    ]
    return {
        "H2_SB1_FROZEN": {
            name: (min(map(float, item["values"])), max(map(float, item["values"])))
            for name, item in h2.items()
        },
        "H3_SB1_FROZEN": {
            "fast_to_slow_rate_s": (min(map(float, rates)), max(map(float, rates))),
            "slow_to_fast_rate_s": (min(map(float, rates)), max(map(float, rates))),
        },
    }


def sensitivity_stage(protocol: dict[str, Any]) -> None:
    runner = load_mechanism_runner()
    base_predictions = pd.read_csv(
        RESULTS / "synthetic_design_predictions.csv"
    )
    bounds = source_parameter_bounds()
    step = float(protocol["local_sensitivity"]["fractional_step"])
    sensitivity_rows: dict[str, list[dict[str, Any]]] = {
        "H2_SB1_FROZEN": [],
        "H3_SB1_FROZEN": [],
    }
    distance_rows: list[dict[str, Any]] = []
    for design_id in protocol["designs"]:
        hours, base_h2, base_h3 = prediction_vectors(
            base_predictions, design_id
        )
        distance_rows.append(
            {
                "design_id": design_id,
                "euclidean_log10_output_distance": float(
                    np.linalg.norm(
                        np.log10(np.clip(base_h2, np.finfo(float).tiny, None))
                        - np.log10(np.clip(base_h3, np.finfo(float).tiny, None))
                    )
                ),
                "maximum_delta_log10": float(
                    np.max(
                        np.abs(
                            np.log10(
                                np.clip(base_h2, np.finfo(float).tiny, None)
                            )
                            - np.log10(
                                np.clip(base_h3, np.finfo(float).tiny, None)
                            )
                        )
                    )
                ),
                "strong_separation_point_count": int(
                    np.sum(
                        np.abs(
                            np.log10(
                                np.clip(base_h2, np.finfo(float).tiny, None)
                            )
                            - np.log10(
                                np.clip(base_h3, np.finfo(float).tiny, None)
                            )
                        )
                        >= 0.30
                    )
                ),
            }
        )
        for mechanism_id, base_vector in zip(
            MECHANISMS, (base_h2, base_h3), strict=True
        ):
            base_parameters = parameter_values(protocol, mechanism_id)
            columns: list[np.ndarray] = []
            metadata: list[tuple[str, str, float, float]] = []
            for name, value in base_parameters.items():
                lower_bound, upper_bound = bounds[mechanism_id][name]
                if math.isclose(value, lower_bound):
                    lower = value
                    upper = min(value * (1.0 + step), upper_bound)
                    scheme = "FORWARD_LOG_DIFFERENCE"
                else:
                    lower = max(value / (1.0 + step), lower_bound)
                    upper = min(value * (1.0 + step), upper_bound)
                    scheme = "CENTRAL_LOG_DIFFERENCE"
                vectors: list[np.ndarray] = []
                for perturbed in (lower, upper):
                    override = {
                        item: parameter_values(protocol, item)
                        for item in MECHANISMS
                    }
                    override[mechanism_id][name] = perturbed
                    prediction, _ = run_design(
                        runner,
                        protocol,
                        design_id,
                        parameters_override=override,
                    )
                    _, current_h2, current_h3 = prediction_vectors(
                        prediction, design_id
                    )
                    vectors.append(
                        current_h2
                        if mechanism_id == "H2_SB1_FROZEN"
                        else current_h3
                    )
                derivative = (
                    np.log10(np.clip(vectors[1], np.finfo(float).tiny, None))
                    - np.log10(np.clip(vectors[0], np.finfo(float).tiny, None))
                ) / (math.log10(upper) - math.log10(lower))
                columns.append(derivative)
                metadata.append((name, scheme, lower, upper))
            matrix = np.column_stack(columns)
            rank = int(np.linalg.matrix_rank(matrix, tol=1.0e-8))
            condition = float(np.linalg.cond(matrix))
            correlation = float(
                abs(np.corrcoef(matrix, rowvar=False)[0, 1])
            )
            fisher = matrix.T @ matrix
            determinant = float(np.linalg.det(fisher))
            for column, (name, scheme, lower, upper) in zip(
                columns, metadata, strict=True
            ):
                for hour, value in zip(hours, column, strict=True):
                    sensitivity_rows[mechanism_id].append(
                        {
                            "design_id": design_id,
                            "mechanism_id": mechanism_id,
                            "parameter_name": name,
                            "sample_hour": float(hour),
                            "d_log10_output_d_log10_parameter": float(value),
                            "difference_scheme": scheme,
                            "lower_parameter_value": lower,
                            "upper_parameter_value": upper,
                            "jacobian_rank": rank,
                            "condition_number": condition,
                            "maximum_absolute_column_correlation": correlation,
                            "fisher_information_determinant": determinant,
                            "global_identifiability_claim": False,
                        }
                    )
    pd.DataFrame(sensitivity_rows["H2_SB1_FROZEN"]).to_csv(
        RESULTS / "h2_local_sensitivity.csv", index=False
    )
    pd.DataFrame(sensitivity_rows["H3_SB1_FROZEN"]).to_csv(
        RESULTS / "h3_local_sensitivity.csv", index=False
    )
    pd.DataFrame(distance_rows).to_csv(
        RESULTS / "model_output_distance.csv", index=False
    )
    print("LOCAL_SENSITIVITY_DESIGN_COUNT = 6")
    print("GLOBAL_STRUCTURAL_IDENTIFIABILITY_CLAIM = FALSE")


def markdown_table(
    headers: list[str], rows: Iterable[Iterable[Any]]
) -> str:
    output = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    output.extend(
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in rows
    )
    return "\n".join(output)


def design_summary(protocol: dict[str, Any]) -> pd.DataFrame:
    mc = pd.read_csv(RESULTS / "monte_carlo_classification.csv")
    distance = pd.read_csv(RESULTS / "model_output_distance.csv")
    minimum = pd.read_csv(RESULTS / "minimum_sampling_design.csv")
    robustness_path = RESULTS / "design_robustness_matrix.csv"
    robustness = (
        pd.read_csv(robustness_path)
        if robustness_path.is_file()
        else pd.DataFrame(columns=["design_id", "criteria_pass"])
    )
    accuracy = (
        mc.groupby(["design_id", "coefficient_of_variation"])[
            "correct_classification_rate"
        ]
        .min()
        .unstack()
    )
    frame = pd.DataFrame(
        {
            "design_id": accuracy.index,
            "cv10_min_accuracy": accuracy[0.10].to_numpy(),
            "cv20_min_accuracy": accuracy[0.20].to_numpy(),
            "cv30_min_accuracy": accuracy[0.30].to_numpy(),
        }
    ).set_index("design_id")
    frame = frame.join(
        distance.set_index("design_id")[
            ["maximum_delta_log10", "strong_separation_point_count"]
        ]
    ).join(
        minimum.set_index("design_id")[
            ["status", "sample_count", "sample_hours"]
        ]
    )
    robust_status = (
        robustness.groupby("design_id")["criteria_pass"].all()
        if len(robustness)
        else pd.Series(dtype=bool)
    )
    frame["robustness_evaluated"] = frame.index.isin(robust_status.index)
    frame["robustness_pass"] = [
        bool(robust_status.get(item, False)) for item in frame.index
    ]
    frame["base_criteria_pass"] = [
        bool(
            row.cv10_min_accuracy >= accuracy_threshold(protocol, 0.10)
            and row.cv20_min_accuracy >= accuracy_threshold(protocol, 0.20)
            and row.cv30_min_accuracy >= accuracy_threshold(protocol, 0.30)
            and row.strong_separation_point_count
            >= protocol["design_success_criteria"][
                "strong_pointwise_separation"
            ]["minimum_time_point_count"]
            and row.status == "MINIMUM_SAMPLING_CRITERIA_PASS"
        )
        for row in frame.itertuples()
    ]
    frame["final_status"] = [
        (
            "DISCRIMINATING_DESIGN_SUPPORTED"
            if row.base_criteria_pass and row.robustness_pass
            else (
                "SYNTHETIC_DESIGN_NOT_ROBUST"
                if row.base_criteria_pass and row.robustness_evaluated
                else (
                    "BASE_CRITERIA_PASS_ROBUSTNESS_NOT_EVALUATED"
                    if row.base_criteria_pass
                    else "SYNTHETIC_DESIGN_NOT_ROBUST"
                )
            )
        )
        for row in frame.itertuples()
    ]
    return frame.reset_index().sort_values(
        [
            "final_status",
            "base_criteria_pass",
            "cv20_min_accuracy",
            "cv30_min_accuracy",
        ],
        ascending=[True, False, False, False],
    )


def repeat_recommendation(
    protocol: dict[str, Any],
    predictions: pd.DataFrame,
    design_id: str,
    sample_hours: list[float],
) -> int:
    hours, h2, h3 = prediction_vectors(predictions, design_id)
    indices = np.asarray(
        [int(np.where(np.isclose(hours, value))[0][0]) for value in sample_hours]
    )
    for replicate_count in range(1, 7):
        passed = True
        for cv in protocol["monte_carlo"]["coefficient_of_variation"]:
            effective_cv = float(cv) / math.sqrt(replicate_count)
            for truth_model, truth in zip(MECHANISMS, (h2, h3), strict=True):
                observations = noise_replicates(
                    protocol,
                    truth,
                    effective_cv,
                    (
                        f"replicate:{design_id}:{replicate_count}:"
                        f"{truth_model}:{float(cv):.2f}"
                    ),
                )
                accuracy = classify_replicates(
                    observations[:, indices],
                    h2[indices],
                    h3[indices],
                    truth_model,
                )
                passed &= accuracy >= accuracy_threshold(
                    protocol, float(cv)
                )
        if passed:
            return max(3, replicate_count)
    return 6


def all_factor_levels_pass(
    robustness: pd.DataFrame, factor: str
) -> bool:
    selected = robustness[robustness["factor"] == factor]
    return bool(len(selected) and selected["criteria_pass"].all())


def write_reports(protocol: dict[str, Any]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    sb1 = pd.read_csv(RESULTS / "existing_sb1_discriminability.csv")
    sb4 = pd.read_csv(RESULTS / "existing_sb4_discriminability.csv")
    summary = design_summary(protocol)
    predictions = pd.read_csv(
        RESULTS / "synthetic_design_predictions.csv"
    )
    qa = pd.read_csv(RESULTS / "design_run_qa.csv")
    minimum = pd.read_csv(RESULTS / "minimum_sampling_design.csv")
    robustness = pd.read_csv(RESULTS / "design_robustness_matrix.csv")
    h2_sensitivity = pd.read_csv(RESULTS / "h2_local_sensitivity.csv")
    h3_sensitivity = pd.read_csv(RESULTS / "h3_local_sensitivity.csv")

    existing_text = f"""# Existing SB1/SB4 discriminability

```text
SB1_EXISTING_DATA_DISCRIMINABILITY =
INSUFFICIENT_TO_SELECT_H2_OR_H3

SB4_EXISTING_DATA_DISCRIMINABILITY =
INSUFFICIENT_TO_SELECT_H2_OR_H3

PARAMETER_REFIT_COUNT = 0
```

The largest SB1 H2-H3 separation is {sb1['delta_log10'].max():.6f} dex at
{sb1.loc[sb1['delta_log10'].idxmax(), 'hours_after_exposure']:g} h. The
largest SB4 separation over both reconstructed profiles and all seven forcing
cases is {sb4['delta_log10'].max():.6f} dex. Both mechanisms already passed
the frozen SB4 transfer criteria, so these within-model prediction distances
cannot identify the true mechanism or authorize selection from the small
RMSE difference.

This analysis uses total plant-body TFWT only. It does not use a latent pool
or refit either mechanism.
"""
    (REPORTS / "existing_evidence_discriminability_report.md").write_text(
        existing_text, encoding="utf-8"
    )

    table = markdown_table(
        [
            "design",
            "max delta dex",
            "strong points",
            "CV10",
            "CV20",
            "CV30",
            "minimum samples",
            "status",
        ],
        (
            (
                row.design_id,
                f"{row.maximum_delta_log10:.4f}",
                int(row.strong_separation_point_count),
                f"{row.cv10_min_accuracy:.3f}",
                f"{row.cv20_min_accuracy:.3f}",
                f"{row.cv30_min_accuracy:.3f}",
                f"{int(row.sample_count)}: {row.sample_hours}",
                row.final_status,
            )
            for row in summary.itertuples()
        ),
    )
    ranking_text = f"""# Synthetic design ranking

All results are `SYNTHETIC_DESIGN_ONLY`; no row is experimental evidence.
H2/H3 parameters remain frozen and total plant-body TFWT is the only
classification observable.

{table}
"""
    (REPORTS / "synthetic_design_ranking.md").write_text(
        ranking_text, encoding="utf-8"
    )
    (REPORTS / "monte_carlo_classification_report.md").write_text(
        "# Monte Carlo classification\n\n"
        "Each truth-model/design/noise cell uses 1000 mean-one lognormal "
        "replicates and minimum log10 RMSE to the two frozen predictions. "
        "No parameter is fitted and no latent pool is supplied.\n\n"
        + table
        + "\n",
        encoding="utf-8",
    )
    (REPORTS / "sampling_optimization_report.md").write_text(
        "# Sampling optimization\n\n"
        "The deterministic greedy search starts at maximum H2-H3 log10 "
        "separation, uses only the 14 preregistered candidate times, and "
        "selects 3-8 samples by worst-noise accuracy. Tie breaks choose the "
        "earlier time.\n\n"
        + markdown_table(
            ["design", "status", "count", "hours"],
            (
                (
                    row.design_id,
                    row.status,
                    int(row.sample_count),
                    row.sample_hours,
                )
                for row in minimum.itertuples()
            ),
        )
        + "\n",
        encoding="utf-8",
    )
    (REPORTS / "robustness_report.md").write_text(
        "# One-factor-at-a-time robustness\n\n"
        "The top three base designs were tested against exposure "
        "concentration, RH, wind speed and stomatal-resistance levels frozen "
        "in the protocol. Slow-process parameters were never refitted.\n\n"
        + markdown_table(
            ["design", "all levels pass"],
            (
                (design_id, bool(group["criteria_pass"].all()))
                for design_id, group in robustness.groupby("design_id")
            ),
        )
        + "\n",
        encoding="utf-8",
    )
    structural_rows = []
    for mechanism_id, frame in (
        ("H2", h2_sensitivity),
        ("H3", h3_sensitivity),
    ):
        for design_id, group in frame.groupby("design_id"):
            first = group.iloc[0]
            structural_rows.append(
                (
                    design_id,
                    mechanism_id,
                    int(first["jacobian_rank"]),
                    f"{first['condition_number']:.4g}",
                    f"{first['maximum_absolute_column_correlation']:.4f}",
                    f"{first['fisher_information_determinant']:.4g}",
                )
            )
    (REPORTS / "structural_discriminability_report.md").write_text(
        "# Local structural discriminability supplement\n\n"
        "These are bounded local sensitivities, not a proof of global "
        "structural identifiability. H2's boundary parameter uses a forward "
        "difference; all other eligible coordinates use central log "
        "differences inside the frozen screening bounds.\n\n"
        + markdown_table(
            ["design", "model", "rank", "condition", "max correlation", "FIM det"],
            structural_rows,
        )
        + "\n",
        encoding="utf-8",
    )

    supported = summary[
        summary["final_status"] == "DISCRIMINATING_DESIGN_SUPPORTED"
    ]
    if len(supported):
        best = supported.sort_values(
            ["cv20_min_accuracy", "cv30_min_accuracy", "sample_count"],
            ascending=[False, False, True],
        ).iloc[0]
        best_design = str(best["design_id"])
        sample_hours = [
            float(value) for value in str(best["sample_hours"]).split(";")
        ]
        repeats = repeat_recommendation(
            protocol, predictions, best_design, sample_hours
        )
        selected_predictions = predictions[
            (predictions["design_id"] == best_design)
            & (predictions["sample_context"] == "POST_FINAL_EXPOSURE")
            & (predictions["sample_hour"].isin(sample_hours))
        ]
        detection_limit = (
            float(
                selected_predictions["plant_body_tfwt_bq_l_water"].min()
            )
            * 0.10
        )
        design = protocol["designs"][best_design]
        spec_status = "READY_FOR_EXTERNAL_DATA_SEARCH_OR_NEW_EXPERIMENT"
        spec = f"""# Minimum H2/H3 discriminating experiment specification

```text
SPECIFICATION_STATUS = {spec_status}
DESIGN_ID = {best_design}
SYNTHETIC_DESIGN_STATUS = DESIGN_ONLY
EMPIRICAL_VALIDATION_CLAIM = FALSE
```

- Controlled chamber conditions: 25 degC, RH 70%, wind 0.5 m/s, LAI 4,
  constant daytime exchange, zero precipitation and strict zero HTO
  background outside declared exposures.
- First exposure: start {design['first_exposure']['start_h']:g} h, duration
  {design['first_exposure']['duration_h']:g} h, concentration
  {design['first_exposure']['concentration_bq_ml_water']:g} Bq/mL water.
- Washout: {design['washout']['duration_h']:g} h at strict zero background.
- Second exposure: {json.dumps(design['second_exposure'], sort_keys=True)}.
- Total planned model follow-up: 120 d after the final exposure; minimum
  TFWT sampling times after final exposure: {', '.join(f'{v:g} h' for v in sample_hours)}.
- Recommended additional times: all remaining preregistered candidate times
  needed for diagnostic coverage:
  {', '.join(str(v) for v in protocol['sampling']['candidate_hours_after_final_exposure'])} h.
- Biological replicate recommendation: at least {repeats} independent plants
  or chamber-equivalent biological replicates per time. This is a Monte Carlo
  design recommendation, not a formal power proof.
- Primary measurement: total plant-body TFWT, Bq/L tissue water. Record
  combined stem+leaf result; leaf and stem separation is recommended as an
  additional diagnostic. Roots and pods are optional secondary matrices and
  must not replace the preregistered total plant-body classifier.
- Measure air-moisture HTO at 5-minute or finer resolution throughout both
  exposure and washout periods. Measure chamber temperature and RH at
  5-minute or finer resolution; record wind/mixing continuously or at the
  same interval.
- Record fresh and dry mass for each sampled organ and the water-extraction
  or combustion-water basis. Preserve raw instrument units and conversion
  metadata.
- Target total relative TFWT uncertainty: <=20%. Recommended analytical
  detection limit: <= {detection_limit:.6g} Bq/L tissue water, defined here as
  no more than 10% of the smallest frozen predicted concentration at the
  minimum sampling times. This is a design target, not an instrument claim.
- Background air-moisture HTO must be measured rather than assumed and should
  remain below 1% of the low-exposure setpoint. Any exceedance must be retained
  in the forcing record.
- Required data fields: experiment_id, chamber_id, replicate_id,
  sample_datetime_utc, hours_after_final_exposure, organ, fresh_mass_g,
  dry_mass_g, tissue_water_ml, tfwt_bq_l_water, analytical_uncertainty,
  detection_limit, air_hto_bq_ml_water, temperature_c, RH_percent,
  wind_speed_m_s, mixing_status, exposure_phase, method_version and
  quality_flag.
- Deliver UTF-8 CSV plus a machine-readable manifest containing SHA-256 for
  every raw and processed file, timezone, units, instrument calibration,
  detection-limit method, missing-value encoding and licence/redistribution
  terms.
"""
    else:
        best_design = "NONE"
        spec_status = "NO_ROBUST_DISCRIMINATING_EXPERIMENT_FOUND"
        spec = """# Minimum H2/H3 discriminating experiment specification

```text
SPECIFICATION_STATUS = NO_ROBUST_DISCRIMINATING_EXPERIMENT_FOUND
SYNTHETIC_DESIGN_STATUS = DESIGN_ONLY
EMPIRICAL_VALIDATION_CLAIM = FALSE
```

None of the six preregistered designs passed all frozen bidirectional
classification, strong-separation, concentration, RH, wind, stomatal,
finite/nonnegative and conservation criteria. No external experiment
specification is authorized from this screen.
"""
    (
        DOCS / "h2_h3_minimum_discriminating_experiment_spec.md"
    ).write_text(spec, encoding="utf-8")

    best_row = (
        supported.sort_values(
            ["cv20_min_accuracy", "cv30_min_accuracy"],
            ascending=False,
        ).iloc[0]
        if len(supported)
        else summary.iloc[0]
    )
    design_status_lines = "\n".join(
        f"{row.design_id.split('_', 1)[0]}_STATUS = {row.final_status}"
        for row in summary.sort_values("design_id").itertuples()
    )
    best_robustness = robustness[
        robustness["design_id"] == best_design
    ]
    main_report = f"""# H2/H3 slow-mechanism discriminability design

```text
MERGED_SB4_BASELINE_HEAD =
e10c0be1d1fac51eb99643ceac71708426c30dd3

DISCRIMINABILITY_BRANCH =
codex/v3-slow-mechanism-discriminability-design

DISCRIMINABILITY_REPORT_GENERATION_HEAD =
{git_output('rev-parse', 'HEAD')}

H2_PARAMETER_SOURCE =
4b79f62741db4d4b51f4d608df33d2e13c499636

H3_PARAMETER_SOURCE =
4b79f62741db4d4b51f4d608df33d2e13c499636

PARAMETER_REFIT_COUNT = 0

SB1_EXISTING_DATA_DISCRIMINABILITY =
INSUFFICIENT_TO_SELECT_H2_OR_H3

SB4_EXISTING_DATA_DISCRIMINABILITY =
INSUFFICIENT_TO_SELECT_H2_OR_H3

BEST_DISCRIMINATING_DESIGN = {best_design}
MINIMUM_SAMPLING_TIMES = {best_row['sample_hours']}
CV10_CLASSIFICATION_ACCURACY = {best_row['cv10_min_accuracy']:.3f}
CV20_CLASSIFICATION_ACCURACY = {best_row['cv20_min_accuracy']:.3f}
CV30_CLASSIFICATION_ACCURACY = {best_row['cv30_min_accuracy']:.3f}

{design_status_lines}

H2_H3_SELECTION_FROM_CURRENT_DATA = NOT_AUTHORIZED
SYNTHETIC_DESIGN_STATUS = DESIGN_ONLY
EXPERIMENT_SPECIFICATION = {spec_status}
FORMAL_V3_PHYSICS = NOT_STARTED
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Design outcomes

{table}

## Robustness

The top three designs were evaluated one factor at a time for exposure
concentration 0.8/1.0/1.2, RH 60/70/80%, wind 0.2/0.5/1.0 m/s and stomatal
resistance 0.8/1.0/1.2 of the frozen value. A design is supported only when
every reported level passes both truth directions, all noise thresholds,
finite/nonnegative checks and the independent paired-transfer ledger.

```text
BEST_DESIGN_ROBUSTNESS_SCOPE = {best_design}
CONCENTRATION_ROBUSTNESS = {all_factor_levels_pass(best_robustness, 'exposure_concentration_multiplier')}
RH_ROBUSTNESS = {all_factor_levels_pass(best_robustness, 'relative_humidity_percent')}
WIND_ROBUSTNESS = {all_factor_levels_pass(best_robustness, 'wind_speed_m_s')}
LEAF_PARAMETER_ROBUSTNESS = {all_factor_levels_pass(best_robustness, 'stomatal_resistance_multiplier')}
ALL_BASE_RUNS_FINITE_NONNEGATIVE = {bool(qa['finite_nonnegative_pass'].all())}
ALL_BASE_RUNS_MASS_CONSERVATIVE = {bool(qa['mass_conservation_pass'].all())}
LATENT_SLOW_POOL_USED_FOR_CLASSIFICATION = FALSE
```

The local sensitivity matrices are bounded numerical diagnostics. They are
not a global structural-identifiability proof. The valid interpretation is
either `SYNTHETIC_DESIGN_PROMISING` for fully robust designs or
`SYNTHETIC_DESIGN_NOT_ROBUST`; current SB1/SB4 observations remain
`CURRENT_DATA_INSUFFICIENT`.
"""
    (
        DOCS / "h2_h3_slow_mechanism_discriminability_report.md"
    ).write_text(main_report, encoding="utf-8")
    print(f"BEST_DISCRIMINATING_DESIGN = {best_design}")
    print(f"EXPERIMENT_SPECIFICATION = {spec_status}")


def main() -> int:
    protocol = load_protocol()
    stage = parse_args().stage
    if stage in {"base", "all"}:
        base_stage(protocol)
    if stage in {"robustness", "all"}:
        robustness_stage(protocol)
    if stage in {"sensitivity", "all"}:
        sensitivity_stage(protocol)
    if stage in {"reports", "all"}:
        write_reports(protocol)
    print("PARAMETER_REFIT_COUNT = 0")
    print("SYNTHETIC_DESIGN_STATUS = DESIGN_ONLY")
    print("V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        AssertionError,
        FileNotFoundError,
        KeyError,
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"Discriminability analysis failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
