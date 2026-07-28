"""Shared validation-only helpers for the synthetic D3 prospective dry run."""

from __future__ import annotations

import hashlib
import importlib.util
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "d3_prospective_experiment"
CLASSIFICATION_PROTOCOL_PATH = (
    BENCHMARK
    / "preregistration"
    / "d3_blinded_classification_protocol_v2.yaml"
)
H2H3_PROTOCOL_PATH = (
    ROOT
    / "validation"
    / "benchmarks"
    / "slow_mechanism_discriminability"
    / "preregistration"
    / "h2_h3_discriminability_protocol.yaml"
)
FORCING_SUMMARY_PATH = (
    BENCHMARK / "results" / "forcing_quality_summary.yaml"
)
LOCAL_ROOT = (
    ROOT / "validation" / "external_local" / "d3_prospective_experiment"
)
TRACKED_DATA_ROOT = BENCHMARK / "blinded"
MEASURED_FORCING_PATH = (
    LOCAL_ROOT / "forcing" / "d3_forcing_measured_background.csv"
)
MECHANISMS = ("H2_SB1_FROZEN", "H3_SB1_FROZEN")
PRIMARY_TIMES = (0.2, 48.0, 120.0)
COMPLETE_TIMES = (0.2, 1.0, 6.0, 24.0, 48.0, 72.0, 120.0)
SYNTHETIC_STATUS = "SYNTHETIC_NOT_EXTERNAL_EVIDENCE"
EVIDENCE_CLASS = "SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_discriminability_module() -> Any:
    return load_module(
        ROOT
        / "validation"
        / "benchmarks"
        / "slow_mechanism_discriminability"
        / "scripts"
        / "run_discriminability_analysis.py",
        "d3_prospective_frozen_discriminability",
    )


def load_classification_protocol() -> dict[str, Any]:
    protocol = yaml.safe_load(
        CLASSIFICATION_PROTOCOL_PATH.read_text(encoding="utf-8")
    )
    if (
        protocol["protocol_id"] != "D3_BLINDED_CLASSIFICATION_PROTOCOL_V2"
        or protocol["status"]
        != "FROZEN_BACKGROUND_BOUND_CORRECTION_BEFORE_RERUN"
    ):
        raise ValueError("Blinded classification protocol is not frozen")
    boundary = protocol["evidence_boundary"]
    if (
        boundary["real_external_evidence"]
        or boundary["empirical_validation_claim"]
        or boundary["trusted_registry_eligible"]
        or boundary["production_eligible"]
        or boundary["formal_v3_physics"] != "NOT_STARTED"
        or boundary["v3_physics_start_gate"]
        != "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    ):
        raise ValueError("Blinded protocol evidence boundary changed")
    model = protocol["model_contract"]
    if (
        model["parameter_refit"]
        or model["parameter_refit_count"] != 0
        or model["parameter_bound_expansion"]
    ):
        raise ValueError("Parameter refit or expansion is prohibited")
    if model["H2_SB1_FROZEN"]["parameters"] != {
        "slow_capture_fraction": 0.001,
        "slow_release_rate_s": 1.0e-6,
    } or model["H3_SB1_FROZEN"]["parameters"] != {
        "fast_to_slow_rate_s": 1.0e-7,
        "slow_to_fast_rate_s": 1.0e-6,
    }:
        raise ValueError("Frozen H2/H3 parameters changed")
    observable = protocol["observable_contract"]
    if (
        observable["classifier_observable"] != "total plant-body TFWT"
        or observable["latent_state_allowed"]
        or observable["pods_allowed"]
        or observable["roots_allowed"]
    ):
        raise ValueError("Classifier observable contract changed")
    if tuple(
        float(value)
        for value in protocol["sampling_contract"]["classification_times_h"]
    ) != PRIMARY_TIMES:
        raise ValueError("Primary classification times changed")
    if protocol["sampling_contract"][
        "diagnostic_times_allowed_for_classification"
    ]:
        raise ValueError("Diagnostic times cannot enter classification")
    classifier = protocol["classifier"]
    if classifier["primary_metric"] != "log10 RMSE":
        raise ValueError("Primary metric changed")
    if classifier["absolute_rmse_difference_inconclusive_dex"] != {
        "value": 0.15,
        "status": "PROJECT_ASSUMPTION_NOT_LITERATURE_FACT",
    } or classifier["both_model_rmse_inadequate_dex"] != {
        "value": 0.50,
        "status": "PROJECT_ASSUMPTION_NOT_LITERATURE_FACT",
    }:
        raise ValueError("Fail-closed RMSE thresholds changed")
    if set(classifier["allowed_results"]) != {
        "H2_SUPPORTED_OVER_H3",
        "H3_SUPPORTED_OVER_H2",
        "BOTH_INADEQUATE",
        "DATA_INCONCLUSIVE",
    }:
        raise ValueError("Allowed classification outcomes changed")
    challenge = protocol["challenge_contract"]
    if (
        challenge["class"] != "SYNTHETIC_OUT_OF_MODEL_CHALLENGE"
        or challenge["expected_result"] != "DATA_INCONCLUSIVE"
        or challenge["third_physical_model_claim"]
    ):
        raise ValueError("Out-of-model challenge boundary changed")
    return protocol


def validate_source_contract(
    protocol: dict[str, Any], disc: Any
) -> dict[str, Any]:
    source = protocol["source_contract"]
    assumptions = ROOT / source["assumptions_file"]
    frozen = ROOT / source["frozen_parameter_file"]
    forcing_generator = ROOT / source["forcing_generator_file"]
    if sha256(assumptions) != source["assumptions_file_sha256"]:
        raise ValueError("Prospective assumptions checksum mismatch")
    if sha256(frozen) != source["frozen_parameter_file_sha256"]:
        raise ValueError("Frozen parameter checksum mismatch")
    if sha256(forcing_generator) != source["forcing_generator_sha256"]:
        raise ValueError("Forcing generator checksum mismatch")
    frozen_mapping = yaml.safe_load(frozen.read_text(encoding="utf-8"))
    if (
        frozen_mapping["mechanism_parameter_result_hash"]
        != source["parameter_result_hash"]
    ):
        raise ValueError("Frozen parameter-result hash mismatch")
    h2h3 = disc.load_protocol()
    expected = {
        "H2_SB1_FROZEN": {
            "slow_capture_fraction": 0.001,
            "slow_release_rate_s": 1.0e-6,
        },
        "H3_SB1_FROZEN": {
            "fast_to_slow_rate_s": 1.0e-7,
            "slow_to_fast_rate_s": 1.0e-6,
        },
    }
    for mechanism_id, values in expected.items():
        if disc.parameter_values(h2h3, mechanism_id) != values:
            raise ValueError(f"{mechanism_id} source parameters changed")
        if protocol["model_contract"][mechanism_id]["parameters"] != values:
            raise ValueError(f"{mechanism_id} prospective parameters changed")
    return h2h3


def forcing_expected_sha256() -> str:
    summary = yaml.safe_load(
        FORCING_SUMMARY_PATH.read_text(encoding="utf-8")
    )
    for scenario in summary["scenarios"]:
        if scenario["scenario_id"] == "MEASURED_NONZERO_BACKGROUND":
            return str(scenario["csv_sha256"])
    raise ValueError("Measured-background forcing summary is missing")


def read_measured_forcing(
    protocol: dict[str, Any], disc: Any
) -> pd.DataFrame:
    if sha256(MEASURED_FORCING_PATH) != forcing_expected_sha256():
        raise ValueError("Measured-background forcing checksum mismatch")
    raw = pd.read_csv(MEASURED_FORCING_PATH)
    required = {
        "time_utc",
        "minutes_from_exposure_start",
        "phase",
        "air_hto_bq_ml_water",
        "temperature_c",
        "relative_humidity_percent",
        "mixing_velocity_m_s",
        "precipitation_mm_interval",
        "light_state",
        "forcing_source",
        "assumption_set",
        "quality_flag",
    }
    if set(raw) != required:
        raise ValueError("Prospective forcing columns changed")
    if set(raw["forcing_source"]) != {"SYNTHETIC_CONTROLLED_EXPERIMENT"}:
        raise ValueError("Forcing source is not synthetic controlled experiment")
    if set(raw["assumption_set"]) != {"D3_PROSPECTIVE_ASSUMPTIONS_V2"}:
        raise ValueError("Forcing does not use the corrected assumption set")
    minutes = raw["minutes_from_exposure_start"].to_numpy(int)
    if (
        len(raw) != 1729
        or minutes[0] != 0
        or minutes[-1] != 8640
        or not np.all(np.diff(minutes) == 5)
    ):
        raise ValueError("Prospective forcing time axis is incomplete")

    time_utc = pd.to_datetime(raw["time_utc"], utc=True)
    time_local = time_utc.dt.tz_convert("Asia/Seoul")
    temperature = raw["temperature_c"].to_numpy(float)
    rh = raw["relative_humidity_percent"].to_numpy(float)
    vapour_density = np.asarray(
        [
            disc.actual_vapour_density_g_m3(float(t), float(h))
            for t, h in zip(temperature, rh, strict=True)
        ],
        dtype=float,
    )
    dewpoint = np.asarray(
        [
            disc.dewpoint_from_temperature_rh(float(t), float(h))
            for t, h in zip(temperature, rh, strict=True)
        ],
        dtype=float,
    )
    controlled = yaml.safe_load(
        H2H3_PROTOCOL_PATH.read_text(encoding="utf-8")
    )["controlled_conditions"]
    shortwave = np.where(
        raw["light_state"].to_numpy(str) == "LIGHT",
        float(controlled["shortwave_down_w_m2"]),
        0.0,
    )
    moisture = raw["air_hto_bq_ml_water"].to_numpy(float)
    return pd.DataFrame(
        {
            "time_utc": time_utc,
            "time_local": time_local,
            "hours_from_first_exposure_start": minutes / 60.0,
            "hours_after_final_exposure": minutes / 60.0 - 24.0,
            "air_temperature_c": temperature,
            "dewpoint_temperature_c": dewpoint,
            "relative_humidity_percent": rh,
            "surface_pressure_pa": float(controlled["surface_pressure_pa"]),
            "wind_speed_m_s": raw["mixing_velocity_m_s"].to_numpy(float),
            "shortwave_down_w_m2": shortwave,
            "longwave_down_w_m2": float(
                controlled["longwave_down_w_m2"]
            ),
            "total_cloud_cover_fraction": float(
                controlled["total_cloud_cover_fraction"]
            ),
            "precipitation_mm_interval": raw[
                "precipitation_mm_interval"
            ].to_numpy(float),
            "air_moisture_hto_bq_ml_water": moisture,
            "air_hto_bq_m3": moisture * vapour_density,
            "phase": raw["phase"].to_numpy(str),
            "forcing_evidence_class": EVIDENCE_CLASS,
        }
    )


def frozen_prediction_table() -> tuple[pd.DataFrame, pd.DataFrame]:
    protocol = load_classification_protocol()
    disc = load_discriminability_module()
    h2h3 = validate_source_contract(protocol, disc)
    forcing = read_measured_forcing(protocol, disc)
    disc.BASE_TIME = forcing.iloc[0]["time_local"]
    runner = disc.load_mechanism_runner()
    previous_leaf, _ = disc.configure_runner(
        runner, h2h3, "D3_SHORT_STEP_24H", 1.0
    )
    predictions: list[dict[str, Any]] = []
    qa_rows: list[dict[str, Any]] = []
    try:
        for mechanism_id in MECHANISMS:
            parameters = disc.parameter_values(h2h3, mechanism_id)
            model, qa = disc.simulate_with_ledger(
                runner, forcing, mechanism_id, parameters
            )
            values = disc.interpolate_field(
                model,
                np.asarray(COMPLETE_TIMES, dtype=float),
                "plant_body_tfwt_bq_l_water",
            )
            predictions.extend(
                {
                    "mechanism_id": mechanism_id,
                    "hours_after_exposure": float(hour),
                    "plant_body_tfwt_bq_l_water": float(value),
                    "observable": "total plant-body TFWT",
                    "parameter_refit_count": 0,
                    "latent_state_used": False,
                    "evidence_class": EVIDENCE_CLASS,
                }
                for hour, value in zip(COMPLETE_TIMES, values, strict=True)
            )
            qa_rows.append({"mechanism_id": mechanism_id, **qa})
    finally:
        runner.FROZEN_LEAF_PARAMETERS = previous_leaf
    qa_frame = pd.DataFrame(qa_rows)
    if (
        not qa_frame["finite_nonnegative_pass"].all()
        or not qa_frame["mass_conservation_pass"].all()
    ):
        raise ValueError("Frozen D3 truth prediction QA failed")
    return pd.DataFrame(predictions), qa_frame


def prediction_vectors(
    prediction_table: pd.DataFrame,
    times: tuple[float, ...] = COMPLETE_TIMES,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values: dict[str, np.ndarray] = {}
    for mechanism_id in MECHANISMS:
        indexed = (
            prediction_table[
                prediction_table["mechanism_id"] == mechanism_id
            ]
            .set_index("hours_after_exposure")
            .loc[list(times)]
        )
        values[mechanism_id] = indexed[
            "plant_body_tfwt_bq_l_water"
        ].to_numpy(float)
    return (
        np.asarray(times, dtype=float),
        values["H2_SB1_FROZEN"],
        values["H3_SB1_FROZEN"],
    )


def log10_rmse(observed: np.ndarray, predicted: np.ndarray) -> float:
    if np.any(observed <= 0) or np.any(predicted <= 0):
        raise ValueError("log10 RMSE inputs must be positive")
    return float(
        np.sqrt(np.mean((np.log10(observed) - np.log10(predicted)) ** 2))
    )


def classify_means(
    observed: np.ndarray,
    h2: np.ndarray,
    h3: np.ndarray,
    protocol: dict[str, Any],
) -> tuple[str, float, float]:
    h2_rmse = log10_rmse(observed, h2)
    h3_rmse = log10_rmse(observed, h3)
    inconclusive = float(
        protocol["classifier"][
            "absolute_rmse_difference_inconclusive_dex"
        ]["value"]
    )
    inadequate = float(
        protocol["classifier"]["both_model_rmse_inadequate_dex"]["value"]
    )
    if abs(h2_rmse - h3_rmse) < inconclusive:
        result = "DATA_INCONCLUSIVE"
    elif h2_rmse > inadequate and h3_rmse > inadequate:
        result = "BOTH_INADEQUATE"
    elif h2_rmse < h3_rmse:
        result = "H2_SUPPORTED_OVER_H3"
    else:
        result = "H3_SUPPORTED_OVER_H2"
    return result, h2_rmse, h3_rmse


def mean_one_lognormal(
    rng: np.random.Generator, cv: float, size: int | tuple[int, ...]
) -> np.ndarray:
    sigma = math.sqrt(math.log1p(float(cv) ** 2))
    mu = -0.5 * sigma**2
    return rng.lognormal(mu, sigma, size=size)
