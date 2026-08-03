from __future__ import annotations

from functools import lru_cache
import hashlib
import inspect
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest
import xarray as xr
import yaml

from validation.external_input_requirements import dataset_root


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb1"
TABLES = BENCHMARK / "published_tables"
LOCAL = dataset_root(ROOT, "SB1")
GENERATED = LOCAL / "generated_forcing"
PROCESSED = LOCAL / "era5_processed"
OUTPUTS = LOCAL / "outputs"
PDF = LOCAL / "references" / "IAEA-emras-tritium-wg.pdf"
PDF_SHA256 = "15b2591d82d8276c83030327d6a65d3f5a2e2ec3b11429d63b7c39461f50d211"
RUNNER_DIR = BENCHMARK / "scripts"
sys.path.insert(0, str(RUNNER_DIR))
import run_sb1_benchmark as runner  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_local(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"independent local input is absent: {path}")


@lru_cache(maxsize=None)
def pdf_page_text(page: int) -> str:
    require_local(PDF)
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is required for independent PDF review")
    result = subprocess.run(
        [
            "pdftotext",
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
    return result.stdout


def parse_scientific(token: str) -> float:
    compact = token.replace(" ", "").replace("−", "-")
    match = re.fullmatch(r"([0-9.]+)×10([0-9]+)", compact)
    if match:
        return float(match.group(1)) * 10 ** int(match.group(2))
    return float(compact)


def table_section(text: str, start: str, end: str | None) -> str:
    section = text.split(start, 1)[1]
    return section.split(end, 1)[0] if end else section


@pytest.mark.external_sb1_data
def test_independent_pdf_tfwt_values() -> None:
    assert sha256(PDF) == PDF_SHA256
    text = table_section(pdf_page_text(105), "Table 5.1.", "Table 5.2.")
    body_text, pod_text = text.split("In the pods (shell and seeds)", 1)
    pattern = re.compile(
        r"(?m)^.*?\s+([0-9]+(?:\.[0-9]+)?)\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s+([0-9.]+E[+-][0-9]+)\s*$"
    )
    pdf_body = [(float(h), float(value)) for h, value, _ in pattern.findall(body_text)]
    pdf_pods = [(float(h), float(value)) for h, value, _ in pattern.findall(pod_text)]
    csv = pd.read_csv(TABLES / "sb1_tfwt_observations.csv")
    body = list(
        csv.loc[csv["compartment"] == "plant_body", [
            "hours_after_exposure", "tfwt_bq_ml_water"
        ]].itertuples(index=False, name=None)
    )
    pods = list(
        csv.loc[csv["compartment"] == "pods", [
            "hours_after_exposure", "tfwt_bq_ml_water"
        ]].itertuples(index=False, name=None)
    )
    assert pdf_body == body
    assert pdf_pods == pods


@pytest.mark.external_sb1_data
def test_independent_pdf_obt_values() -> None:
    text = table_section(pdf_page_text(105), "Table 5.3.", None)
    line = re.search(r"(?m)^SB1\s+(.+)$", text).group(1)
    tokens = re.findall(r"[0-9.]+(?:E[+-][0-9]+|×10[0-9]+)?", line)
    pdf_values = [parse_scientific(token) for token in tokens]
    assert pdf_values == pytest.approx(
        [77700, 18, 14, 16, 2.06e-4, 0.83, 0.5, 0.67, 8.63e-6]
    )
    csv = pd.read_csv(TABLES / "sb1_obt_harvest.csv")
    concentration = csv.dropna(subset=["obt_bq_ml_combustion_water"])
    assert concentration["obt_bq_ml_combustion_water"].tolist() == pytest.approx(
        [18, 14, 16, 0.83, 0.5, 0.67]
    )
    normalized = csv.loc[
        csv["compartment"].isin(
            ["normalized_body_average", "normalized_pods_average"]
        ),
        "normalized_obt",
    ]
    assert normalized.tolist() == pytest.approx([2.06e-4, 8.63e-6])


@pytest.mark.external_sb1_data
def test_independent_pdf_chamber_values() -> None:
    text = table_section(pdf_page_text(289), "Table I.4.6.", "Table I.4.7.")
    pattern = re.compile(
        r"(?m)^\s*(\d{2}:\d{2})(?: \((?:start|end)\))?\s+"
        r"([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+"
        r"([–-]|[0-9.]+\s*×\s*10[0-9]+)\s*$"
    )
    parsed = pattern.findall(text)
    assert len(parsed) == 15
    pdf = pd.DataFrame(
        [
            {
                "time": time,
                "temperature": float(t),
                "rh": float(rh),
                "klux": float(klux),
                "hto": np.nan if hto in {"–", "-"} else parse_scientific(hto),
            }
            for time, t, rh, klux, hto in parsed
        ]
    )
    csv = pd.read_csv(TABLES / "sb1_chamber_conditions_5min.csv")
    assert pdf["time"].tolist() == pd.to_datetime(csv["time_local"]).dt.strftime(
        "%H:%M"
    ).tolist()
    assert pdf[["temperature", "rh", "klux"]].to_numpy() == pytest.approx(
        csv[[
            "air_temperature_c",
            "relative_humidity_percent",
            "illuminance_klux",
        ]].to_numpy()
    )
    assert pdf["hto"].to_numpy() == pytest.approx(
        csv["air_moisture_hto_bq_ml_water"].to_numpy(), nan_ok=True
    )


@pytest.mark.external_sb1_data
def test_independent_pdf_biomass_values() -> None:
    text = pdf_page_text(287)
    expected: dict[tuple[str, str], list[float]] = {}
    for number, stage, basis, count, next_number in (
        ("I.4.2", "exposure", "fresh", 2, "I.4.3"),
        ("I.4.3", "exposure", "dry", 2, "I.4.4"),
        ("I.4.4", "harvest", "fresh", 4, "I.4.5"),
        ("I.4.5", "harvest", "dry", 4, None),
    ):
        section = table_section(
            text,
            f"Table {number}.",
            f"Table {next_number}." if next_number else None,
        )
        row = re.search(r"(?m)^\s*SB1\s+(.+)$", section).group(1)
        values = [
            float(token)
            for token in row.split()
            if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", token)
        ]
        expected[(stage, basis)] = values[:count]
    csv = pd.read_csv(TABLES / "sb1_biomass.csv")
    for key, values in expected.items():
        selected = csv[(csv["stage"] == key[0]) & (csv["mass_basis"] == key[1])]
        assert selected["value"].tolist() == pytest.approx(values)


@pytest.mark.external_sb1_data
def test_unreported_chamber_hto_not_claimed_observed_zero() -> None:
    text = table_section(pdf_page_text(289), "Table I.4.6.", "Table I.4.7.")
    assert re.search(r"09:30 \(start\).+–\s*$", text, re.MULTILINE)
    source = pd.read_csv(TABLES / "sb1_chamber_conditions_5min.csv")
    at_start = source.loc[source["minutes_from_exposure_start"] == 0].iloc[0]
    assert pd.isna(at_start["air_moisture_hto_bq_ml_water"])
    assert at_start["source_status"] == "NOT_REPORTED_BOUNDARY_ASSUMPTION_REQUIRED"
    generated = pd.read_csv(GENERATED / "sb1_chamber_profiles.csv")
    boundary = generated.loc[generated["minutes_from_exposure_start"] == 0].iloc[0]
    assert boundary["air_moisture_hto_bq_ml_water"] == 0
    assert boundary["boundary_assumption"] == "ASSUMED_ZERO_AT_EVAPORATION_START"


def test_independent_sampling_datetime_mapping() -> None:
    schedule = pd.read_csv(TABLES / "sb1_sampling_schedule.csv")
    expected_local = {
        0.2: "2001-07-02T10:40:00+09:00",
        1.0: "2001-07-02T11:30:00+09:00",
        24.0: "2001-07-03T10:30:00+09:00",
        120.0: "2001-07-07T10:30:00+09:00",
        336.0: "2001-07-16T10:30:00+09:00",
        936.0: "2001-08-10T10:30:00+09:00",
        1608.0: "2001-09-07T10:30:00+09:00",
        2280.0: "2001-10-05T10:30:00+09:00",
    }
    body = schedule[schedule["compartment"] == "plant_body"]
    actual = dict(zip(body["hours_after_exposure"], body["sample_datetime_local"]))
    assert actual == expected_local


@pytest.mark.external_sb1_data
def test_independent_elapsed_hours_mapping() -> None:
    text = table_section(pdf_page_text(289), "Table I.4.9.", None)
    elapsed = [
        float(value)
        for value in re.findall(
            r"(?m)^\s*(?:July|Aug|Sep|Oct|\d{2}:\d{2}).*?\s"
            r"([0-9]+(?:\.[0-9]+)?)\s+(?:Plant|Plan)",
            text,
        )
    ]
    assert elapsed == [0.2, 1, 24, 120, 336, 936, 1608, 2280]
    end = pd.Timestamp("2001-07-02T10:30:00+09:00")
    for hours in elapsed:
        expected = (
            pd.Timestamp("2001-07-02T10:40:00+09:00")
            if hours == 0.2
            else end + pd.Timedelta(hours=hours)
        )
        rows = pd.read_csv(TABLES / "sb1_sampling_schedule.csv")
        recorded = pd.Timestamp(
            rows.loc[rows["hours_after_exposure"] == hours, "sample_datetime_local"].iloc[0]
        )
        assert recorded == expected


def test_independent_local_utc_round_trip() -> None:
    seoul = ZoneInfo("Asia/Seoul")
    local = pd.Timestamp("2001-07-02T09:30:00").to_pydatetime().replace(tzinfo=seoul)
    assert local.utcoffset().total_seconds() == 9 * 3600
    utc = pd.Timestamp(local).tz_convert("UTC")
    assert utc.isoformat() == "2001-07-02T00:30:00+00:00"
    assert utc.tz_convert("Asia/Seoul") == pd.Timestamp(local)


@pytest.mark.external_sb1_data
def test_independent_chamber_era5_boundary_alignment() -> None:
    forcing = pd.read_csv(GENERATED / "sb1_forcing_primary.csv")
    local = pd.to_datetime(forcing["time_local"], utc=True).dt.tz_convert("Asia/Seoul")
    forcing = forcing.assign(local=local).set_index("local")
    assert forcing.loc["2001-07-02T09:25:00+09:00", "phase"] == "PRE_EXPOSURE_OUTDOOR"
    assert forcing.loc["2001-07-02T09:30:00+09:00", "phase"] == "CHAMBER_EXPOSURE"
    assert forcing.loc["2001-07-02T10:30:00+09:00", "phase"] == "CHAMBER_EXPOSURE"
    assert forcing.loc["2001-07-02T10:35:00+09:00", "phase"] == "POST_EXPOSURE_OUTDOOR"
    times = pd.to_datetime(forcing["time_utc"], utc=True)
    assert (times.diff().dropna().dt.total_seconds() == 300).all()


def independent_chamber_mean(include_1035: bool = False) -> float:
    chamber = pd.read_csv(TABLES / "sb1_chamber_conditions_5min.csv")
    stop = 65 if include_1035 else 60
    selected = chamber[
        chamber["minutes_from_exposure_start"].between(0, stop)
    ].copy()
    selected.loc[
        selected["minutes_from_exposure_start"] == 0,
        "air_moisture_hto_bq_ml_water",
    ] = 0.0
    return float(
        np.trapezoid(
            selected["air_moisture_hto_bq_ml_water"],
            selected["minutes_from_exposure_start"],
        )
        / stop
    )


def test_independent_chamber_trapezoid_mean() -> None:
    assert independent_chamber_mean() == pytest.approx(75612.5)


def test_independent_mean_constrained_scale() -> None:
    assert 77700.0 / independent_chamber_mean() == pytest.approx(
        1.0276078690692676
    )


@pytest.mark.external_sb1_data
def test_1035_value_excluded_from_exposure_mean() -> None:
    assert independent_chamber_mean(include_1035=True) != pytest.approx(75612.5)
    summary = json.loads(
        (GENERATED / "sb1_chamber_profile_summary.json").read_text()
    )
    assert summary["integration_method"] == "trapezoidal over 09:30-10:30 local"


def independent_vapour_density(temperature_c: float, rh_percent: float) -> float:
    temperature_k = temperature_c + 273.15
    saturation_pa = 610.78 * math.exp(
        17.2694 * temperature_c / (temperature_c + 237.29)
    )
    saturation_g_m3 = saturation_pa / (461.5 * temperature_k) * 1000.0
    return saturation_g_m3 * rh_percent / 100.0


@pytest.mark.external_sb1_data
def test_independent_vapour_density_reference_points() -> None:
    generated = pd.read_csv(GENERATED / "sb1_chamber_profiles.csv")
    for minute in (10, 30, 60):
        row = generated.loc[
            generated["minutes_from_exposure_start"] == minute
        ].iloc[0]
        expected = independent_vapour_density(
            row["air_temperature_c"], row["relative_humidity_percent"]
        )
        assert row["actual_vapour_density_g_m3"] == pytest.approx(expected)


@pytest.mark.external_sb1_data
def test_independent_air_hto_unit_conversion() -> None:
    generated = pd.read_csv(GENERATED / "sb1_chamber_profiles.csv")
    for minute in (10, 30, 60):
        row = generated.loc[
            generated["minutes_from_exposure_start"] == minute
        ].iloc[0]
        expected_bq_m3_air = (
            row["air_moisture_hto_bq_ml_water"]
            * row["actual_vapour_density_g_m3"]
        )
        assert row["air_hto_bq_m3_air"] == pytest.approx(expected_bq_m3_air)


def raw_and_processed(point: str) -> tuple[xr.Dataset, pd.DataFrame]:
    netcdf = PROCESSED / point / "era5_surface_2001-05-20_2001-10-06.nc"
    csv = PROCESSED / point / "era5_hourly_processed.csv"
    require_local(netcdf)
    require_local(csv)
    dataset = xr.open_dataset(netcdf, engine="netcdf4")
    frame = pd.read_csv(csv)
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
    return dataset, frame


def aligned_raw(dataset: xr.Dataset, frame: pd.DataFrame, variable: str) -> np.ndarray:
    raw_time = pd.to_datetime(dataset["valid_time"].values, utc=True)
    series = pd.Series(dataset[variable].values, index=raw_time)
    return series.loc[pd.DatetimeIndex(frame["time_utc"])].to_numpy(float)


@pytest.mark.external_sb1_data
def test_independent_era5_interval_semantics() -> None:
    dataset, frame = raw_and_processed("CENTRE")
    try:
        for variable, units in (("tp", "m"), ("ssrd", "J m**-2"), ("strd", "J m**-2")):
            assert dataset[variable].attrs["GRIB_stepType"] == "accum"
            assert dataset[variable].attrs["GRIB_stepUnits"] == 1
            assert dataset[variable].attrs["units"] == units
        raw = aligned_raw(dataset, frame, "ssrd")
        assert frame["shortwave_down_w_m2"].iloc[100] == pytest.approx(
            raw[100] / 3600.0
        )
    finally:
        dataset.close()


@pytest.mark.external_sb1_data
def test_independent_precipitation_total() -> None:
    dataset, frame = raw_and_processed("CENTRE")
    try:
        raw = aligned_raw(dataset, frame, "tp")
        assert frame["precipitation_mm_interval"].sum() == pytest.approx(
            raw.sum() * 1000.0
        )
        assert frame["precipitation_mm_interval"].sum() == pytest.approx(
            646.7812061309814
        )
    finally:
        dataset.close()


@pytest.mark.external_sb1_data
def test_independent_shortwave_conversion() -> None:
    dataset, frame = raw_and_processed("CENTRE")
    try:
        raw = aligned_raw(dataset, frame, "ssrd")
        assert frame["shortwave_down_w_m2"].to_numpy() == pytest.approx(raw / 3600.0)
    finally:
        dataset.close()


@pytest.mark.external_sb1_data
def test_independent_longwave_conversion() -> None:
    dataset, frame = raw_and_processed("CENTRE")
    try:
        raw = aligned_raw(dataset, frame, "strd")
        assert frame["longwave_down_w_m2"].to_numpy() == pytest.approx(raw / 3600.0)
    finally:
        dataset.close()


@pytest.mark.external_sb1_data
def test_independent_five_point_time_coverage() -> None:
    for point in ("CENTRE", "NORTH_0P25", "SOUTH_0P25", "EAST_0P25", "WEST_0P25"):
        _, frame = raw_and_processed(point)
        assert len(frame) == 3336
        assert not frame["time_utc"].duplicated().any()
        assert frame["time_utc"].iloc[0] == pd.Timestamp("2001-05-20T15:00:00Z")
        assert frame["time_utc"].iloc[-1] == pd.Timestamp("2001-10-06T14:00:00Z")
        assert frame.select_dtypes(include=[np.number]).notna().all().all()


def protocol() -> dict:
    return yaml.safe_load(
        (BENCHMARK / "preregistration" / "sb1_benchmark_protocol.yaml").read_text()
    )


def test_independent_calibration_holdout_disjoint() -> None:
    frozen = protocol()
    calibration = set(frozen["calibration"]["hours_after_exposure"])
    holdout_a = set(frozen["pseudo_holdout_a"]["hours_after_exposure"])
    holdout_b = set(frozen["pseudo_holdout_b"]["hours_after_exposure"])
    assert calibration.isdisjoint(holdout_a)
    assert calibration.isdisjoint(holdout_b)


@pytest.mark.external_sb1_data
def test_independent_parameter_grid_7_by_7() -> None:
    grid = pd.read_csv(OUTPUTS / "calibration_grid.csv")
    assert len(grid) == 49
    assert grid["leaf_stomatal_resistance_day_s_m"].nunique() == 7
    assert grid["leaf_characteristic_length_m"].nunique() == 7


def independent_log_metrics(frame: pd.DataFrame) -> dict[str, float]:
    observed = frame["observed_bq_l_water"].to_numpy(float)
    predicted = frame["predicted_bq_l_water"].to_numpy(float)
    residual = np.log10(predicted) - np.log10(observed)
    ratio = predicted / observed
    return {
        "log10_rmse": float(np.sqrt(np.mean(residual**2))),
        "log10_mean_bias": float(np.mean(residual)),
        "median_predicted_to_observed_ratio": float(np.median(ratio)),
        "factor_2_coverage": float(np.mean((ratio >= 0.5) & (ratio <= 2))),
        "factor_10_coverage": float(np.mean((ratio >= 0.1) & (ratio <= 10))),
    }


@pytest.mark.external_sb1_data
def test_independent_optimum_selected_from_calibration_only() -> None:
    grid = pd.read_csv(OUTPUTS / "calibration_grid.csv")
    optimum = grid.loc[grid["log10_rmse"].idxmin()]
    result = json.loads((BENCHMARK / "reports" / "calibration_result.json").read_text())
    assert optimum["leaf_stomatal_resistance_day_s_m"] == 800
    assert optimum["leaf_characteristic_length_m"] == 0.1
    assert result["best_parameters"] == {
        "leaf_stomatal_resistance_day_s_m": 800.0,
        "leaf_characteristic_length_m": 0.1,
    }
    calibration = pd.read_csv(
        BENCHMARK / "reports" / "calibration_predictions_frozen.csv"
    )
    recomputed = independent_log_metrics(calibration)
    for name, value in recomputed.items():
        assert result["calibration_metrics"][name] == pytest.approx(value)


def git_commit_for(path: Path) -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", str(path.relative_to(ROOT))],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_independent_parameter_freeze_precedes_holdout() -> None:
    protocol_commit = git_commit_for(
        BENCHMARK / "preregistration" / "sb1_benchmark_protocol.yaml"
    )
    parameter_commit = git_commit_for(
        BENCHMARK / "reports" / "calibrated_parameter_set.yaml"
    )
    holdout_commit = git_commit_for(
        BENCHMARK / "reports" / "pseudo_holdout_predictions.csv"
    )
    assert protocol_commit.startswith("edd8889")
    assert parameter_commit.startswith("0e1cb72")
    assert holdout_commit.startswith("9c191f0")
    for earlier, later in (
        (protocol_commit, parameter_commit),
        (parameter_commit, holdout_commit),
    ):
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", earlier, later],
            cwd=ROOT,
            check=False,
        )
        assert completed.returncode == 0


def test_independent_pseudo_holdout_metrics() -> None:
    predictions = pd.read_csv(BENCHMARK / "reports" / "pseudo_holdout_predictions.csv")
    primary = predictions[predictions["run_id"] == "RUN_01"]
    for compartment, expected in (
        (
            "plant_body",
            {
                "log10_rmse": 2.610971968938851,
                "median_predicted_to_observed_ratio": 0.0019847751183623328,
            },
        ),
        (
            "pods",
            {
                "log10_rmse": 1.141618900813427,
                "median_predicted_to_observed_ratio": 0.07161749526921166,
            },
        ),
    ):
        actual = independent_log_metrics(primary[primary["compartment"] == compartment])
        for name, value in expected.items():
            assert actual[name] == pytest.approx(value)


def test_independent_adapter_has_no_observation_nudging() -> None:
    source = inspect.getsource(runner.run_model)
    assert "observed" not in source
    assert "nudg" not in source.lower()
    assert "predicted_bq_l_water" not in source


def test_independent_adapter_has_no_hidden_slow_pool() -> None:
    source = inspect.getsource(runner)
    assert "slow_pool" not in source
    assert "slow_release" not in source
    assert "PROVISIONAL_GENERIC_EDIBLE_COMPARTMENT" in source


def test_independent_structural_underprediction_values() -> None:
    predictions = pd.read_csv(BENCHMARK / "reports" / "pseudo_holdout_predictions.csv")
    primary = predictions[
        (predictions["run_id"] == "RUN_01")
        & (predictions["compartment"] == "plant_body")
    ].set_index("hours_after_exposure")
    assert primary.loc[936, "predicted_bq_l_water"] == pytest.approx(1.292608, rel=1e-6)
    assert primary.loc[936, "observed_bq_l_water"] == 110
    assert primary.loc[2280, "predicted_bq_l_water"] == pytest.approx(
        0.051075, rel=1e-5
    )
    assert primary.loc[2280, "observed_bq_l_water"] == 60
    calibration = pd.read_csv(
        BENCHMARK / "reports" / "calibration_predictions_frozen.csv"
    ).set_index("hours_after_exposure")
    assert calibration.loc[24, "predicted_bq_l_water"] == pytest.approx(
        10.34699, rel=1e-5
    )
    assert calibration.loc[24, "observed_bq_l_water"] == 3920
