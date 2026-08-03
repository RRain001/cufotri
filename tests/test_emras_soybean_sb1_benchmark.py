from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys

import jsonschema
import numpy as np
import pandas as pd
import pytest
import yaml

from validation.external_input_requirements import dataset_root


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb1"
TABLES = BENCHMARK / "published_tables"
LOCAL = dataset_root(ROOT, "SB1")
GENERATED = LOCAL / "generated_forcing"
SCRIPT_DIR = BENCHMARK / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
build = importlib.import_module("build_sb1_dataset")
runner = importlib.import_module("run_sb1_benchmark")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def forcing() -> pd.DataFrame:
    path = GENERATED / "sb1_forcing_primary.csv"
    if not path.is_file():
        pytest.skip("local ERA5-derived forcing is not present")
    frame = pd.read_csv(path)
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
    return frame


def test_sb1_published_table_schema() -> None:
    for stem in ("sb1_chamber_conditions", "sb1_tfwt_observations"):
        frame = pd.read_csv(TABLES / f"{stem}_5min.csv") if stem.endswith(
            "conditions"
        ) else pd.read_csv(TABLES / f"{stem}.csv")
        schema = json.loads((BENCHMARK / "schemas" / f"{stem}.schema.json").read_text())
        validator = jsonschema.Draft202012Validator(schema)
        for row in frame.replace({np.nan: None}).to_dict(orient="records"):
            validator.validate(row)


def test_sb1_tfwt_transcription_values() -> None:
    frame = pd.read_csv(TABLES / "sb1_tfwt_observations.csv")
    body = frame[frame["compartment"] == "plant_body"]
    assert body["tfwt_bq_ml_water"].tolist() == [
        9580.0, 1050.0, 3.92, 1.32, 0.33, 0.11, 0.06, 0.06
    ]
    assert len(frame) == 11


def test_sb1_obt_transcription_values() -> None:
    frame = pd.read_csv(TABLES / "sb1_obt_harvest.csv").dropna(
        subset=["obt_bq_ml_combustion_water"]
    )
    assert dict(zip(frame["compartment"], frame["obt_bq_ml_combustion_water"])) == {
        "stem": 18.0,
        "leaves": 14.0,
        "plant_body_average": 16.0,
        "shell": 0.83,
        "seeds": 0.50,
        "pods_average": 0.67,
    }


def test_sb1_chamber_timestamp_order() -> None:
    frame = pd.read_csv(TABLES / "sb1_chamber_conditions_5min.csv")
    assert frame["minutes_from_exposure_start"].tolist() == list(range(-5, 66, 5))


@pytest.mark.external_sb1_data
def test_sb1_chamber_profile_mean() -> None:
    summary = build.chamber_profiles()
    assert summary["raw_profile_mean_bq_ml_water"] == pytest.approx(75612.5)
    assert summary["reported_mean_bq_ml_water"] == 77700.0
    assert abs(summary["relative_difference"]) < 0.05


@pytest.mark.external_sb1_data
def test_sb1_air_moisture_to_air_volume_conversion() -> None:
    profile = pd.read_csv(GENERATED / "sb1_chamber_profiles.csv")
    row = profile.loc[profile["minutes_from_exposure_start"] == 30].iloc[0]
    assert row["air_hto_bq_m3_air"] == pytest.approx(
        row["air_moisture_hto_bq_ml_water"]
        * row["actual_vapour_density_g_m3"]
    )


def test_sb1_bq_ml_to_bq_l_conversion() -> None:
    tfwt = pd.read_csv(TABLES / "sb1_tfwt_observations.csv")
    assert np.allclose(tfwt["tfwt_bq_l_water"], tfwt["tfwt_bq_ml_water"] * 1000)


@pytest.mark.external_sb1_data
def test_sb1_forcing_phase_continuity() -> None:
    frame = forcing()
    differences = frame["time_utc"].diff().dropna().dt.total_seconds()
    assert (differences == 300).all()
    assert frame["phase"].isin(
        ["PRE_EXPOSURE_OUTDOOR", "CHAMBER_EXPOSURE", "POST_EXPOSURE_OUTDOOR"]
    ).all()


def test_sb1_era5_no_missing_hours() -> None:
    report = pd.read_csv(BENCHMARK / "reports" / "era5_spatial_sensitivity.csv")
    assert len(report) == 5
    assert (report["actual_hourly_timestamps"] == 3336).all()
    assert report[["duplicate_timestamp_count", "missing_timestamp_count",
                   "nan_count", "inf_count"]].to_numpy().sum() == 0


def test_sb1_local_utc_round_trip() -> None:
    schedule = pd.read_csv(TABLES / "sb1_sampling_schedule.csv")
    local_as_utc = pd.to_datetime(schedule["sample_datetime_local"], utc=True)
    recorded_utc = pd.to_datetime(schedule["sample_datetime_utc"], utc=True)
    assert local_as_utc.equals(recorded_utc)


def test_sb1_calibration_holdout_disjoint() -> None:
    protocol = yaml.safe_load(
        (BENCHMARK / "preregistration" / "sb1_benchmark_protocol.yaml").read_text()
    )
    calibration = set(protocol["calibration"]["hours_after_exposure"])
    holdout_a = set(protocol["pseudo_holdout_a"]["hours_after_exposure"])
    holdout_b = set(protocol["pseudo_holdout_b"]["hours_after_exposure"])
    assert calibration.isdisjoint(holdout_a)
    assert calibration.isdisjoint(holdout_b)


def test_sb1_benchmark_not_production_gate_eligible() -> None:
    manifest = json.loads((BENCHMARK / "sb1_case_manifest.json").read_text())
    assert manifest["production_gate_eligible"] is False
    assert manifest["trusted_registry_eligible"] is False


def test_sb1_manifest_checksum_reproducible() -> None:
    manifest = json.loads((BENCHMARK / "sb1_case_manifest.json").read_text())
    for name, expected in manifest["published_table_checksums"].items():
        assert sha256(TABLES / name) == expected


@pytest.mark.external_sb1_data
def test_sb1_model_run_finite_nonnegative() -> None:
    path = GENERATED / "sb1_forcing_primary.csv"
    if not path.is_file():
        pytest.skip("local ERA5-derived forcing is not present")
    parameters = {
        item["name"]: float(item["initial"])
        for item in yaml.safe_load(runner.PROTOCOL.read_text())[
            "calibration_parameters"
        ]
    }
    result = runner.run_model(runner.load_forcing("RUN_01"), parameters, 1.0)
    numeric = result.select_dtypes(include=[np.number])
    assert not np.isinf(numeric.to_numpy()).any()
    inventory = numeric.filter(regex="inventory")
    assert (inventory.fillna(0).to_numpy() >= -1.0e-12).all()
    assert numeric["surface_box_residual_bq_m2"].abs().max() < 1.0e-6


def test_sb1_coordinate_status_not_claimed_exact() -> None:
    manifest = json.loads((BENCHMARK / "sb1_case_manifest.json").read_text())
    assert manifest["coordinate_status"] == "PROVISIONAL_INSTITUTIONAL_LOCATION"


def test_sb1_spatial_sensitivity_points_generated() -> None:
    report = pd.read_csv(BENCHMARK / "reports" / "era5_spatial_sensitivity.csv")
    assert set(report["point_id"]) == {
        "CENTRE", "NORTH_0P25", "SOUTH_0P25", "EAST_0P25", "WEST_0P25"
    }
