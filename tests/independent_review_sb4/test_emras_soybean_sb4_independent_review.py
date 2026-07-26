from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
from functools import lru_cache
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd
import pytest
import xarray as xr
import yaml


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb4"
SB1_BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb1"
SB1_MECHANISMS = (
    ROOT / "validation" / "benchmarks" / "emras_soybean_sb1_mechanisms"
)
TABLES = BENCHMARK / "published_tables"
REPORTS = BENCHMARK / "reports"
LOCAL = ROOT / "validation" / "external_local" / "emras_soybean_sb4"
SB1_LOCAL = ROOT / "validation" / "external_local" / "emras_soybean_sb1"
GENERATED = LOCAL / "generated_forcing"
PROCESSED = LOCAL / "era5_processed"
PDF = SB1_LOCAL / "references" / "IAEA-emras-tritium-wg.pdf"
RAW = SB1_LOCAL / "era5_raw"
PROTOCOL_PATH = (
    BENCHMARK / "preregistration" / "sb4_transfer_protocol.yaml"
)
FROZEN_PARAMETER_PATH = (
    SB1_MECHANISMS / "reports" / "frozen_mechanism_parameters.yaml"
)
PROTOCOL = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))
BASELINE = "d08d9d81f3ef10b11c2431e7bebe2f802c56cd18"
REVIEW_TARGET = "b540387087cecedee2a3d2a078657e0b313a2c8e"
PARAMETER_SOURCE_COMMIT = (
    "4b79f62741db4d4b51f4d608df33d2e13c499636"
)
EXPECTED_PARAMETER_FILE_SHA256 = (
    "9224d4019d1e71f28f653699125c09328ae95af8bfc39a71442dc9dc355dc2d9"
)
EXPECTED_PARAMETER_RESULT_HASH = (
    "f95f27fe6ce601af688c1a40d3b23619d11374e0c4151d8c1a702d0c6a2160a9"
)
EXPECTED_PDF_SHA256 = (
    "15b2591d82d8276c83030327d6a65d3f5a2e2ec3b11429d63b7c39461f50d211"
)
PROFILE_IDS = (
    "CONSTANT_REPORTED_MEAN",
    "SCALED_SB1_OBSERVED_SHAPE",
)
RUN_IDS = tuple(f"RUN_{index:02d}" for index in range(1, 8))
MECHANISMS = (
    "H0_CURRENT_SINGLE_POOL",
    "H2_SB1_FROZEN",
    "H3_SB1_FROZEN",
)
SOURCE_MECHANISMS = {
    "H0_CURRENT_SINGLE_POOL": "H0_CURRENT_SINGLE_POOL",
    "H2_SB1_FROZEN": "H2_PARALLEL_FAST_SLOW_RESIDUAL",
    "H3_SB1_FROZEN": "H3_REVERSIBLE_FAST_SLOW_EXCHANGE",
}
EXPOSURE_START = pd.Timestamp("2001-08-09T09:30:00+09:00")
EXPOSURE_END = pd.Timestamp("2001-08-09T10:30:00+09:00")
HARVEST = pd.Timestamp("2001-10-05T10:30:00+09:00")
POD_START = pd.Timestamp("2001-07-10T00:00:00+09:00")
DOWNLOAD_START_UTC = pd.Timestamp("2001-05-20T15:00:00Z")
DOWNLOAD_END_UTC = pd.Timestamp("2001-10-06T14:00:00Z")
RAW_NAME = "era5_surface_2001-05-20_2001-10-06.nc"


def _git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@lru_cache(maxsize=3)
def _pdf_page_text(page: int) -> str:
    if not PDF.is_file():
        pytest.skip("Independent source PDF is not locally available")
    executable = shutil.which("pdftotext")
    if executable is None:
        pytest.skip("pdftotext is required for direct PDF review")
    completed = subprocess.run(
        [
            executable,
            "-f",
            str(page),
            "-l",
            str(page),
            "-layout",
            str(PDF),
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _tfwt_rows(block: str) -> tuple[list[float], list[float], list[float]]:
    hours: list[float] = []
    values: list[float] = []
    normalized: list[float] = []
    expected = {"0.2", "1", "24", "120", "336", "768", "1368"}
    for line in block.splitlines():
        tokens = line.split()
        if len(tokens) < 3 or tokens[-3] not in expected:
            continue
        hours.append(float(tokens[-3]))
        values.append(float(tokens[-2]))
        normalized.append(float(tokens[-1]))
    return hours, values, normalized


def _pdf_tfwt() -> dict[str, tuple[list[float], list[float], list[float]]]:
    text = _pdf_page_text(105)
    section = text.split("Table 5.2.", 1)[1].split("Table 5.3.", 1)[0]
    body, pods = section.split("In the pods (shell and seeds)", 1)
    return {"plant_body": _tfwt_rows(body), "pods": _tfwt_rows(pods)}


def _pdf_obt_values() -> list[float]:
    text = _pdf_page_text(105)
    section = text.split("Table 5.3.", 1)[1]
    line = next(
        candidate
        for candidate in section.splitlines()
        if candidate.strip().startswith("SB4 ")
    )
    tokens = line.split()
    numeric = [float(token) for token in tokens[-8:]]
    return [
        numeric[0],
        numeric[1],
        numeric[2],
        numeric[4],
        numeric[5],
        numeric[6],
    ]


def _pdf_biomass_values() -> dict[tuple[str, str], list[float]]:
    text = _pdf_page_text(287)
    result: dict[tuple[str, str], list[float]] = {}
    definitions = (
        ("exposure", "fresh", "Table I.4.2.", "Table I.4.3."),
        ("exposure", "dry", "Table I.4.3.", "Table I.4.4."),
        ("harvest", "fresh", "Table I.4.4.", "Table I.4.5."),
        ("harvest", "dry", "Table I.4.5.", None),
    )
    for stage, basis, start, end in definitions:
        section = text.split(start, 1)[1]
        if end is not None:
            section = section.split(end, 1)[0]
        line = next(
            candidate
            for candidate in section.splitlines()
            if candidate.strip().startswith("SB4 ")
        )
        tokens = line.split()
        result[(stage, basis)] = [float(value) for value in tokens[-5:-1]]
    return result


def _log_metrics(frame: pd.DataFrame) -> dict[str, float]:
    observed = frame["observed_bq_l_water"].to_numpy(float)
    predicted = frame["predicted_bq_l_water"].to_numpy(float)
    if (
        not np.isfinite(observed).all()
        or not np.isfinite(predicted).all()
        or (observed <= 0).any()
        or (predicted <= 0).any()
    ):
        raise AssertionError("metrics require finite positive inputs")
    residual = np.log10(predicted / observed)
    absolute = np.abs(residual)
    return {
        "log10_rmse": float(np.sqrt(np.mean(residual**2))),
        "log10_mean_bias": float(np.mean(residual)),
        "median_predicted_to_observed_ratio": float(
            np.median(predicted / observed)
        ),
        "factor_2_coverage": float(
            np.mean(absolute <= math.log10(2.0))
        ),
        "factor_10_coverage": float(np.mean(absolute <= 1.0)),
    }


def _predictions() -> pd.DataFrame:
    return pd.read_csv(REPORTS / "sb4_transfer_predictions.csv")


def _prediction_subset(
    predictions: pd.DataFrame,
    mechanism_id: str,
    profile_id: str,
    run_id: str,
    compartment: str = "plant_body",
) -> pd.DataFrame:
    return predictions[
        (predictions["mechanism_id"] == mechanism_id)
        & (predictions["profile_id"] == profile_id)
        & (predictions["run_id"] == run_id)
        & (predictions["compartment"] == compartment)
    ]


def _early_pass(reference: pd.DataFrame, candidate: pd.DataFrame) -> bool:
    criteria = PROTOCOL["support_criteria"]
    reference = reference[
        reference["hours_after_exposure"].isin([0.2, 1.0])
    ]
    candidate = candidate[
        candidate["hours_after_exposure"].isin([0.2, 1.0])
    ]
    ratio = (
        candidate["predicted_bq_l_water"].to_numpy(float)
        / candidate["observed_bq_l_water"].to_numpy(float)
    )
    factor_pass = bool(
        np.all(
            (ratio >= 1.0 / criteria["early_prediction_factor_limit"])
            & (ratio <= criteria["early_prediction_factor_limit"])
        )
    )
    candidate_error = np.abs(
        np.log10(
            candidate["predicted_bq_l_water"].to_numpy(float)
            / candidate["observed_bq_l_water"].to_numpy(float)
        )
    )
    reference_error = np.abs(
        np.log10(
            reference["predicted_bq_l_water"].to_numpy(float)
            / reference["observed_bq_l_water"].to_numpy(float)
        )
    )
    worsening = float(np.max(candidate_error - reference_error))
    return bool(
        factor_pass
        or worsening
        <= criteria["early_log10_error_worsening_maximum_dex"]
    )


def _validate_parameter_contract(protocol: dict[str, Any]) -> None:
    source = protocol["sb1_parameter_source"]
    if not protocol["no_sb4_parameter_refit"]:
        raise ValueError("SB4 parameter refit must remain disabled")
    if protocol["sb4_parameter_refit_count"] != 0:
        raise ValueError("SB4 parameter refit count must remain zero")
    if _sha256(FROZEN_PARAMETER_PATH) != source["frozen_parameter_file_sha256"]:
        raise ValueError("frozen parameter checksum mismatch")
    frozen = yaml.safe_load(FROZEN_PARAMETER_PATH.read_text(encoding="utf-8"))
    if (
        frozen["mechanism_parameter_result_hash"]
        != source["mechanism_parameter_result_hash"]
    ):
        raise ValueError("parameter-result hash mismatch")
    expected = {
        "H2_SB1_FROZEN": (
            "H2_PARALLEL_FAST_SLOW_RESIDUAL",
            {"slow_capture_fraction": 0.001, "slow_release_rate_s": 1.0e-6},
        ),
        "H3_SB1_FROZEN": (
            "H3_REVERSIBLE_FAST_SLOW_EXCHANGE",
            {"fast_to_slow_rate_s": 1.0e-7, "slow_to_fast_rate_s": 1.0e-6},
        ),
    }
    for target, (source_id, parameters) in expected.items():
        declared = protocol["mechanisms"][target]
        if declared["selected_from_sb4"]:
            raise ValueError("parameter selected from SB4")
        if declared["parameters"] != parameters:
            raise ValueError("parameters differ from frozen SB1 values")
        if frozen["candidates"][source_id]["parameters"] != parameters:
            raise ValueError("parameters differ from source file")


def _validate_protocol_roles(protocol: dict[str, Any]) -> None:
    for endpoint in ("pods", "obt"):
        definition = protocol["observations"][endpoint]
        if definition["used_for_parameter_selection"]:
            raise ValueError(f"{endpoint} cannot be used for selection")
        if definition["positive_selection_evidence"]:
            raise ValueError(f"{endpoint} cannot be positive evidence")


def _validate_forcing_manifest_contract(manifest: dict[str, Any]) -> None:
    if manifest["total_forcing_files"] != 14:
        raise ValueError("forcing count mismatch")
    if len(manifest["era5_raw_checksums"]) != 5:
        raise ValueError("raw input count mismatch")
    for item in manifest["scenarios"].values():
        if item["chamber_profile_evidence_class"] != "RECONSTRUCTED":
            raise ValueError("profile provenance is not reconstructed")


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_mechanism_runner() -> Any:
    scripts = SB1_MECHANISMS / "scripts"
    sys.path.insert(0, str(scripts))
    sys.path.insert(0, str(SB1_MECHANISMS))
    runner = _load_module(
        scripts / "run_mechanism_discrimination.py",
        "sb1_mechanism_runner_for_independent_sb4_review",
    )
    sb1 = runner.sb1
    sb1.EXPOSURE_START = EXPOSURE_START
    sb1.EXPOSURE_END = EXPOSURE_END
    sb1.HARVEST = HARVEST
    sb1.POD_START = POD_START
    sb1.EXPOSURE_BODY_WATER_M = 0.0009826
    sb1.EXPOSURE_BODY_DRY_G_M2 = 477.8
    sb1.HARVEST_BODY_DRY_G_M2 = 946.3
    sb1.HARVEST_POD_FRESH_G_M2 = 1069.9
    sb1.HARVEST_POD_DRY_G_M2 = 340.6
    sb1.HARVEST_POD_WATER_M = (1069.9 - 340.6) / 1000.0 / 1000.0
    return runner


def _load_review_forcing(path: Path) -> pd.DataFrame:
    forcing = pd.read_csv(path)
    forcing["time_utc"] = pd.to_datetime(forcing["time_utc"], utc=True)
    forcing["time_local"] = forcing["time_utc"].dt.tz_convert("Asia/Seoul")
    forcing = forcing[
        forcing["time_local"].between(EXPOSURE_START, HARVEST)
    ].copy()
    forcing = forcing.sort_values("time_utc").reset_index(drop=True)
    steps = forcing["time_utc"].diff().dropna().dt.total_seconds()
    assert not forcing["time_utc"].duplicated().any()
    assert (steps == 300).all()
    exposure = forcing["phase"] == "CHAMBER_EXPOSURE"
    assert set(
        forcing.loc[exposure, "chamber_profile_evidence_class"]
    ) == {"RECONSTRUCTED"}
    return forcing


def _simulate_review_case(
    runner: Any,
    forcing: pd.DataFrame,
    source_id: str,
    parameters: dict[str, float],
) -> dict[str, float | int]:
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

    elif source_id == "H3_REVERSIBLE_FAST_SLOW_EXCHANGE":
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

    else:
        module = None
        original = None

    if module is not None:
        module.transfer = audited_transfer
    try:
        model = runner.simulate(forcing, source_id, parameters, 1368.0)
    finally:
        if module is not None:
            module.transfer = original

    numeric = model.select_dtypes(include=[np.number])
    inventory = numeric.filter(regex="_inventory_bq_m2$")
    concentration = numeric.filter(regex="_bq_l_")
    return {
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
        "maximum_internal_transfer_ledger_residual_abs_bq_m2": max(ledger),
        "maximum_internal_state_sum_roundoff_abs_bq_m2": float(
            model["internal_transfer_residual_abs_bq_m2"].max()
        ),
    }


@pytest.fixture(scope="module")
def independently_recomputed_runs() -> pd.DataFrame:
    manifest = json.loads(
        (GENERATED / "sb4_forcing_manifest.json").read_text(encoding="utf-8")
    )
    runner = _load_mechanism_runner()
    rows: list[dict[str, Any]] = []
    for profile_id in PROFILE_IDS:
        for run_id in RUN_IDS:
            item = manifest["scenarios"][f"{profile_id}:{run_id}"]
            forcing = _load_review_forcing(ROOT / item["path"])
            for mechanism_id in MECHANISMS:
                source_id = SOURCE_MECHANISMS[mechanism_id]
                parameters = PROTOCOL["mechanisms"][mechanism_id]["parameters"]
                rows.append(
                    {
                        "mechanism_id": mechanism_id,
                        "profile_id": profile_id,
                        "run_id": run_id,
                        **_simulate_review_case(
                            runner, forcing, source_id, parameters
                        ),
                    }
                )
    return pd.DataFrame(rows)


def _forcing_pass_count(
    mechanism_id: str,
    profile_id: str,
    recomputed_runs: pd.DataFrame,
) -> int:
    predictions = _predictions()
    criteria = PROTOCOL["support_criteria"]
    count = 0
    for run_id in RUN_IDS:
        reference = _prediction_subset(
            predictions,
            "H0_CURRENT_SINGLE_POOL",
            profile_id,
            run_id,
        )
        candidate = _prediction_subset(
            predictions, mechanism_id, profile_id, run_id
        )
        reference_overall = _log_metrics(reference)
        candidate_overall = _log_metrics(candidate)
        reference_late = _log_metrics(
            reference[
                reference["hours_after_exposure"].isin([768.0, 1368.0])
            ]
        )
        candidate_late = _log_metrics(
            candidate[
                candidate["hours_after_exposure"].isin([768.0, 1368.0])
            ]
        )
        mass = recomputed_runs[
            (recomputed_runs["mechanism_id"] == mechanism_id)
            & (recomputed_runs["profile_id"] == profile_id)
            & (recomputed_runs["run_id"] == run_id)
        ].iloc[0]
        mass_pass = bool(
            mass["maximum_formal_mass_closure_abs_bq_m2"]
            <= criteria["mass_closure_absolute_tolerance_bq_m2"]
            and mass[
                "maximum_internal_transfer_ledger_residual_abs_bq_m2"
            ]
            <= criteria["internal_transfer_absolute_tolerance_bq_m2"]
            and mass["nan_count"] == 0
            and mass["inf_count"] == 0
            and mass["negative_inventory_count"] == 0
            and mass["negative_concentration_count"] == 0
        )
        passed = bool(
            reference_overall["log10_rmse"]
            - candidate_overall["log10_rmse"]
            >= criteria["overall_log10_rmse_improvement_minimum_dex"]
            and reference_late["log10_rmse"]
            - candidate_late["log10_rmse"]
            >= criteria["late_log10_rmse_improvement_minimum_dex"]
            and _early_pass(reference, candidate)
            and mass_pass
        )
        count += int(passed)
    return count


def _assert_selection_claims(
    selection: dict[str, Any], recomputed_runs: pd.DataFrame
) -> None:
    supported: list[str] = []
    for mechanism_id in ("H2_SB1_FROZEN", "H3_SB1_FROZEN"):
        profile_support: list[bool] = []
        for profile_id in PROFILE_IDS:
            count = _forcing_pass_count(
                mechanism_id, profile_id, recomputed_runs
            )
            claimed = selection["candidate_results"][mechanism_id][
                "profiles"
            ][profile_id]
            if claimed["forcing_pass_count"] != count:
                raise AssertionError("forged forcing pass count")
            profile_support.append(
                count
                >= PROTOCOL["support_criteria"][
                    "forcing_scenarios_required_per_profile"
                ]
            )
        if all(profile_support):
            supported.append(mechanism_id)
    expected = (
        "MULTIPLE_SLOW_MECHANISMS_TRANSFER_SUPPORTED"
        if supported == ["H2_SB1_FROZEN", "H3_SB1_FROZEN"]
        else "INDEPENDENT_RECOMPUTATION_DID_NOT_SUPPORT_BOTH"
    )
    if selection["sb4_transfer_status"] != expected:
        raise AssertionError("forged transfer selection")


def test_review_sb4_tfwt_values_from_pdf() -> None:
    extracted = _pdf_tfwt()
    tracked = pd.read_csv(TABLES / "sb4_tfwt_observations.csv")
    for compartment in ("plant_body", "pods"):
        subset = tracked[tracked["compartment"] == compartment]
        hours, values, normalized = extracted[compartment]
        np.testing.assert_array_equal(
            subset["hours_after_exposure"].to_numpy(float), hours
        )
        np.testing.assert_array_equal(
            subset["tfwt_bq_ml_water"].to_numpy(float), values
        )
        np.testing.assert_allclose(
            subset["normalized_tfwt"].to_numpy(float),
            normalized,
            rtol=0.0,
            atol=0.0,
        )


def test_review_sb4_obt_values_from_pdf() -> None:
    tracked = pd.read_csv(TABLES / "sb4_obt_harvest.csv")
    np.testing.assert_array_equal(
        tracked["obt_bq_ml_combustion_water"].to_numpy(float),
        _pdf_obt_values(),
    )


def test_review_sb4_biomass_values_from_pdf() -> None:
    tracked = pd.read_csv(TABLES / "sb4_biomass.csv")
    extracted = _pdf_biomass_values()
    component_order = ["stem", "leaves", "shell", "seed"]
    for keys, values in extracted.items():
        subset = tracked[
            (tracked["stage"] == keys[0])
            & (tracked["mass_basis"] == keys[1])
        ].set_index("component")
        actual = [float(subset.loc[item, "value"]) for item in component_order]
        np.testing.assert_array_equal(actual, values)


def test_review_sb4_sampling_schedule_from_pdf() -> None:
    text = _pdf_page_text(290).split("I.4.3.4.", 1)[0]
    expected_hours = [0.2, 1.0, 24.0, 120.0, 336.0, 768.0, 1368.0]
    for value in expected_hours:
        assert str(int(value) if value.is_integer() else value) in text
    schedule = pd.read_csv(TABLES / "sb4_sampling_schedule.csv")
    assert len(schedule) == 14
    counts = schedule["hours_after_exposure"].value_counts().to_dict()
    assert counts == {value: 2 for value in expected_hours}
    assert "Aug 9" in text and "Oct 5" in text


def test_review_sb4_mean_chamber_hto_from_pdf() -> None:
    text = _pdf_page_text(105)
    assert "5.27×104 Bq/mL for SB4" in text.replace(" ", " ", 0)
    metadata = yaml.safe_load(
        (TABLES / "sb4_experiment_metadata.yaml").read_text(encoding="utf-8")
    )
    assert metadata["reported_mean_air_moisture_hto_bq_ml"] == 52700
    assert str(metadata["exposure_date"]) == "2001-08-09"
    assert str(metadata["harvest_date"]) == "2001-10-05"


def test_review_sb4_units_from_pdf() -> None:
    tfwt = pd.read_csv(TABLES / "sb4_tfwt_observations.csv")
    obt = pd.read_csv(TABLES / "sb4_obt_harvest.csv")
    np.testing.assert_array_equal(
        tfwt["tfwt_bq_l_water"], tfwt["tfwt_bq_ml_water"] * 1000.0
    )
    np.testing.assert_array_equal(
        obt["obt_bq_l_combustion_water"],
        obt["obt_bq_ml_combustion_water"] * 1000.0,
    )
    assert "TFWT (Bq/mL)" in _pdf_page_text(105)


def test_review_sb4_constant_profile_mean() -> None:
    profiles = pd.read_csv(GENERATED / "sb4_chamber_profiles.csv")
    constant = profiles[
        profiles["profile_id"] == "CONSTANT_REPORTED_MEAN"
    ]
    assert set(constant["air_moisture_hto_bq_ml_water"]) == {52700.0}
    mean = float(
        np.trapezoid(
            constant["air_moisture_hto_bq_ml_water"],
            constant["minutes_from_exposure_start"],
        )
        / 60.0
    )
    assert math.isclose(mean, 52700.0, abs_tol=1.0e-9)


def test_review_sb4_scaled_profile_mean() -> None:
    profiles = pd.read_csv(GENERATED / "sb4_chamber_profiles.csv")
    scaled = profiles[
        profiles["profile_id"] == "SCALED_SB1_OBSERVED_SHAPE"
    ]
    mean = float(
        np.trapezoid(
            scaled["air_moisture_hto_bq_ml_water"],
            scaled["minutes_from_exposure_start"],
        )
        / 60.0
    )
    assert math.isclose(mean, 52700.0, abs_tol=1.0e-9)


def test_review_sb4_scaled_profile_shape_preserved() -> None:
    profiles = pd.read_csv(GENERATED / "sb4_chamber_profiles.csv")
    scaled = profiles[
        profiles["profile_id"] == "SCALED_SB1_OBSERVED_SHAPE"
    ].sort_values("minutes_from_exposure_start")
    source = pd.read_csv(
        SB1_BENCHMARK
        / "published_tables"
        / "sb1_chamber_conditions_5min.csv"
    )
    source = source[
        source["minutes_from_exposure_start"].between(0, 60)
    ].sort_values("minutes_from_exposure_start")
    raw = source["air_moisture_hto_bq_ml_water"].to_numpy(
        dtype=float, copy=True
    )
    raw[0] = 0.0
    actual = scaled["air_moisture_hto_bq_ml_water"].to_numpy(float)
    nonzero = raw > 0
    ratios = actual[nonzero] / raw[nonzero]
    assert np.ptp(ratios) <= 1.0e-12
    assert actual[0] == 0.0


def test_review_sb4_profiles_marked_reconstructed() -> None:
    profiles = pd.read_csv(GENERATED / "sb4_chamber_profiles.csv")
    manifest = json.loads(
        (GENERATED / "sb4_forcing_manifest.json").read_text(encoding="utf-8")
    )
    assert set(profiles["profile_evidence_class"]) == {"RECONSTRUCTED"}
    assert not profiles["sb4_observed_curve_claim"].astype(bool).any()
    _validate_forcing_manifest_contract(manifest)


def test_review_sb4_input_snapshot_read_only() -> None:
    files = [PDF, *sorted(RAW.rglob("*.nc"))]
    assert len(files) == 6
    if ROOT.name == "CETAS_ufotri_sb4_independent_review":
        for path in files:
            mode = path.stat().st_mode
            assert mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0


def test_review_sb4_era5_raw_checksums() -> None:
    sb1_manifest = json.loads(
        (SB1_BENCHMARK / "sb1_case_manifest.json").read_text(encoding="utf-8")
    )
    assert _sha256(PDF) == EXPECTED_PDF_SHA256
    assert sb1_manifest["source_document_sha256"] == EXPECTED_PDF_SHA256
    for relative, checksum in sb1_manifest[
        "era5_raw_file_checksums"
    ].items():
        assert _sha256(ROOT / relative) == checksum


def test_review_sb4_era5_time_coverage() -> None:
    for point in sorted(path.name for path in PROCESSED.iterdir()):
        qa = json.loads(
            (PROCESSED / point / "era5_qa_summary.json").read_text(
                encoding="utf-8"
            )
        )
        assert qa["actual_hourly_timestamps"] == 3336
        assert qa["expected_hourly_timestamps"] == 3336
        assert qa["duplicate_timestamp_count"] == 0
        assert qa["missing_timestamp_count"] == 0
        assert qa["nan_count"] == 0
        assert qa["inf_count"] == 0


def test_review_sb4_era5_interval_semantics() -> None:
    for point in sorted(path.name for path in PROCESSED.iterdir()):
        with xr.open_dataset(
            PROCESSED / point / RAW_NAME, engine="netcdf4"
        ) as dataset:
            assert dataset["tp"].attrs["units"] == "m"
            assert dataset["ssrd"].attrs["units"] == "J m**-2"
            assert dataset["strd"].attrs["units"] == "J m**-2"
            source = dataset[["tp", "ssrd", "strd"]].to_dataframe().reset_index()
        source["time_utc"] = pd.to_datetime(source["valid_time"], utc=True)
        source = source[
            source["time_utc"].between(
                DOWNLOAD_START_UTC, DOWNLOAD_END_UTC
            )
        ].sort_values("time_utc")
        processed = pd.read_csv(
            PROCESSED / point / "era5_hourly_processed.csv"
        )
        np.testing.assert_allclose(
            processed["precipitation_mm_interval"],
            source["tp"].to_numpy(float) * 1000.0,
            rtol=0.0,
            atol=1.0e-12,
        )
        np.testing.assert_allclose(
            processed["shortwave_down_w_m2"],
            source["ssrd"].to_numpy(float) / 3600.0,
            rtol=0.0,
            atol=1.0e-12,
        )
        np.testing.assert_allclose(
            processed["longwave_down_w_m2"],
            source["strd"].to_numpy(float) / 3600.0,
            rtol=0.0,
            atol=1.0e-12,
        )
        assert set(processed["accumulation_semantics"]) == {
            "PREVIOUS_1H_INTERVAL_ENDING_AT_VALID_TIME"
        }


def test_review_sb4_five_point_forcing_generated() -> None:
    expected_points = {
        "CENTRE",
        "NORTH_0P25",
        "SOUTH_0P25",
        "EAST_0P25",
        "WEST_0P25",
    }
    assert {path.name for path in PROCESSED.iterdir()} == expected_points
    manifest = json.loads(
        (GENERATED / "sb4_forcing_manifest.json").read_text(encoding="utf-8")
    )
    assert set(manifest["era5_raw_checksums"]) == expected_points
    assert manifest["total_forcing_files"] == 14
    assert len(manifest["scenarios"]) == 14


def test_review_sb4_h2_parameters_bound_to_sb1() -> None:
    _validate_parameter_contract(PROTOCOL)
    assert PROTOCOL["mechanisms"]["H2_SB1_FROZEN"]["parameters"] == {
        "slow_capture_fraction": 0.001,
        "slow_release_rate_s": 1.0e-6,
    }


def test_review_sb4_h3_parameters_bound_to_sb1() -> None:
    _validate_parameter_contract(PROTOCOL)
    assert PROTOCOL["mechanisms"]["H3_SB1_FROZEN"]["parameters"] == {
        "fast_to_slow_rate_s": 1.0e-7,
        "slow_to_fast_rate_s": 1.0e-6,
    }


def test_review_sb4_parameter_result_hash() -> None:
    source = PROTOCOL["sb1_parameter_source"]
    assert source["frozen_parameter_commit"] == PARAMETER_SOURCE_COMMIT
    assert source["frozen_parameter_file_sha256"] == (
        EXPECTED_PARAMETER_FILE_SHA256
    )
    assert source["mechanism_parameter_result_hash"] == (
        EXPECTED_PARAMETER_RESULT_HASH
    )
    committed = _git(
        "show",
        f"{PARAMETER_SOURCE_COMMIT}:"
        "validation/benchmarks/emras_soybean_sb1_mechanisms/"
        "reports/frozen_mechanism_parameters.yaml",
    ).stdout.encode()
    assert hashlib.sha256(committed).hexdigest() == (
        EXPECTED_PARAMETER_FILE_SHA256
    )


def test_review_sb4_no_refit_path() -> None:
    predictions = _predictions()
    script = (
        BENCHMARK / "scripts" / "run_sb4_transfer_test.py"
    ).read_text(encoding="utf-8")
    assert PROTOCOL["no_sb4_parameter_refit"] is True
    assert PROTOCOL["sb4_parameter_refit_count"] == 0
    assert set(predictions["sb4_parameter_refit_count"]) == {0}
    assert "argparse" not in script
    assert "os.environ" not in script


def test_review_sb4_no_parameter_selection() -> None:
    predictions = _predictions()
    assert not predictions["selected_from_sb4"].astype(bool).any()
    assert all(
        not PROTOCOL["mechanisms"][mechanism]["selected_from_sb4"]
        for mechanism in ("H2_SB1_FROZEN", "H3_SB1_FROZEN")
    )


def test_review_sb4_run_matrix_complete() -> None:
    predictions = _predictions()
    combinations = predictions[
        ["mechanism_id", "profile_id", "run_id"]
    ].drop_duplicates()
    assert len(combinations) == 42
    assert combinations.duplicated().sum() == 0
    assert len(predictions) == 3 * 2 * 7 * 2 * 7
    assert set(combinations["mechanism_id"]) == set(MECHANISMS)
    assert set(combinations["profile_id"]) == set(PROFILE_IDS)
    assert set(combinations["run_id"]) == set(RUN_IDS)


def test_review_sb4_all_metrics_recomputed_from_predictions() -> None:
    predictions = _predictions()
    stored = pd.read_csv(REPORTS / "sb4_transfer_metrics.csv")
    partition_hours = {
        "overall": None,
        "early": {0.2, 1.0},
        "mid": {24.0, 120.0, 336.0},
        "late": {768.0, 1368.0},
    }
    for keys, frame in predictions.groupby(
        ["mechanism_id", "profile_id", "run_id", "compartment"]
    ):
        for partition, hours in partition_hours.items():
            subset = (
                frame
                if hours is None
                else frame[frame["hours_after_exposure"].isin(hours)]
            )
            expected = _log_metrics(subset)
            row = stored[
                (stored["mechanism_id"] == keys[0])
                & (stored["profile_id"] == keys[1])
                & (stored["run_id"] == keys[2])
                & (stored["compartment"] == keys[3])
                & (stored["partition"] == partition)
            ].iloc[0]
            for metric, value in expected.items():
                assert math.isclose(
                    float(row[metric]), value, rel_tol=0.0, abs_tol=1.0e-12
                )


def test_review_sb4_run01_metrics_match_frozen_targets() -> None:
    predictions = _predictions()
    expected = {
        ("CONSTANT_REPORTED_MEAN", "H0_CURRENT_SINGLE_POOL"): 1.5369617596153613,
        ("CONSTANT_REPORTED_MEAN", "H2_SB1_FROZEN"): 0.35418743716847134,
        ("CONSTANT_REPORTED_MEAN", "H3_SB1_FROZEN"): 0.36716455180514657,
        ("SCALED_SB1_OBSERVED_SHAPE", "H0_CURRENT_SINGLE_POOL"): 1.5370137934646093,
        ("SCALED_SB1_OBSERVED_SHAPE", "H2_SB1_FROZEN"): 0.35457994393210984,
        ("SCALED_SB1_OBSERVED_SHAPE", "H3_SB1_FROZEN"): 0.3670559438976269,
    }
    for (profile_id, mechanism_id), target in expected.items():
        frame = _prediction_subset(
            predictions, mechanism_id, profile_id, "RUN_01"
        )
        assert math.isclose(
            _log_metrics(frame)["log10_rmse"],
            target,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        )


def test_review_sb4_selection_recomputed(
    independently_recomputed_runs: pd.DataFrame,
) -> None:
    counts = {
        (mechanism, profile): _forcing_pass_count(
            mechanism, profile, independently_recomputed_runs
        )
        for mechanism in ("H2_SB1_FROZEN", "H3_SB1_FROZEN")
        for profile in PROFILE_IDS
    }
    assert set(counts.values()) == {7}
    selection = json.loads(
        (REPORTS / "sb4_transfer_selection.json").read_text(encoding="utf-8")
    )
    _assert_selection_claims(selection, independently_recomputed_runs)


def test_review_sb4_pods_and_obt_are_veto_only() -> None:
    _validate_protocol_roles(PROTOCOL)
    assert PROTOCOL["observations"]["pods"]["role"] == (
        "STRUCTURAL_TRANSFER_DIAGNOSTIC"
    )
    assert PROTOCOL["observations"]["obt"]["role"] == (
        "CONSISTENCY_CHECK_ONLY"
    )


def test_review_sb4_mass_balance_42_runs(
    independently_recomputed_runs: pd.DataFrame,
) -> None:
    assert len(independently_recomputed_runs) == 42
    assert (
        independently_recomputed_runs[
            "maximum_formal_mass_closure_abs_bq_m2"
        ].max()
        <= PROTOCOL["support_criteria"][
            "mass_closure_absolute_tolerance_bq_m2"
        ]
    )


def test_review_sb4_internal_transfer_ledger_zero(
    independently_recomputed_runs: pd.DataFrame,
) -> None:
    assert (
        independently_recomputed_runs[
            "maximum_internal_transfer_ledger_residual_abs_bq_m2"
        ].max()
        == 0.0
    )


def test_review_sb4_roundoff_not_used_to_relax_tolerance(
    independently_recomputed_runs: pd.DataFrame,
) -> None:
    assert (
        independently_recomputed_runs[
            "maximum_internal_state_sum_roundoff_abs_bq_m2"
        ].max()
        > PROTOCOL["support_criteria"][
            "internal_transfer_absolute_tolerance_bq_m2"
        ]
    )
    assert (
        PROTOCOL["support_criteria"][
            "internal_transfer_absolute_tolerance_bq_m2"
        ]
        == 1.0e-9
    )


def test_review_sb4_all_states_finite_nonnegative(
    independently_recomputed_runs: pd.DataFrame,
) -> None:
    for column in (
        "nan_count",
        "inf_count",
        "negative_inventory_count",
        "negative_concentration_count",
    ):
        assert independently_recomputed_runs[column].sum() == 0


def test_review_sb4_attack_modified_h2_parameter_fails() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["mechanisms"]["H2_SB1_FROZEN"]["parameters"][
        "slow_capture_fraction"
    ] = 0.002
    with pytest.raises(ValueError, match="differ from frozen"):
        _validate_parameter_contract(forged)


def test_review_sb4_attack_selected_from_sb4_fails() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["mechanisms"]["H3_SB1_FROZEN"]["selected_from_sb4"] = True
    with pytest.raises(ValueError, match="selected from SB4"):
        _validate_parameter_contract(forged)


def test_review_sb4_attack_observed_profile_spoof_fails() -> None:
    manifest = json.loads(
        (GENERATED / "sb4_forcing_manifest.json").read_text(encoding="utf-8")
    )
    forged = copy.deepcopy(manifest)
    first = next(iter(forged["scenarios"].values()))
    first["chamber_profile_evidence_class"] = "OBSERVED"
    with pytest.raises(ValueError, match="not reconstructed"):
        _validate_forcing_manifest_contract(forged)


def test_review_sb4_attack_forged_forcing_count_fails(
    independently_recomputed_runs: pd.DataFrame,
) -> None:
    selection = json.loads(
        (REPORTS / "sb4_transfer_selection.json").read_text(encoding="utf-8")
    )
    forged = copy.deepcopy(selection)
    forged["candidate_results"]["H3_SB1_FROZEN"]["profiles"][
        "CONSTANT_REPORTED_MEAN"
    ]["forcing_pass_count"] = 6
    with pytest.raises(AssertionError, match="forged forcing pass count"):
        _assert_selection_claims(forged, independently_recomputed_runs)


def test_review_sb4_attack_pods_positive_evidence_fails() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["observations"]["pods"]["used_for_parameter_selection"] = True
    forged["observations"]["pods"]["positive_selection_evidence"] = True
    with pytest.raises(ValueError, match="pods cannot be used"):
        _validate_protocol_roles(forged)


def test_review_sb4_protocol_chronology() -> None:
    assert (
        _git(
            "merge-base",
            "--is-ancestor",
            "e7ff0d26968a2ae39b332a33e9d88afe355ab064",
            "31df826",
            check=False,
        ).returncode
        == 0
    )


def test_review_sb4_formal_boundaries_unchanged() -> None:
    changed = _git(
        "diff",
        "--name-only",
        f"{BASELINE}...HEAD",
        "--",
        "src",
        "configs",
    ).stdout.splitlines()
    assert changed == []
    trusted = (
        "validation/v3/policy/trusted_external_evidence_registry.yaml"
    )
    assert (
        _git(
            "diff",
            "--quiet",
            f"{BASELINE}...HEAD",
            "--",
            trusted,
            check=False,
        ).returncode
        == 0
    )


def test_review_sb4_not_production_gate_eligible() -> None:
    selection = json.loads(
        (REPORTS / "sb4_transfer_selection.json").read_text(encoding="utf-8")
    )
    assert selection["empirical_validation_claim"] is False
    assert selection["production_gate_eligible"] is False
    assert selection["formal_v3_physics"] == "NOT_STARTED"
    assert selection["v3_physics_start_gate"] == (
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )
