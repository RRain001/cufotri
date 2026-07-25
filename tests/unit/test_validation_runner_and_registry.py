from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import yaml

from scripts.check_validation_forcing_completeness import check_forcing
from scripts.prepare_observed_forcing import prepare_observed_forcing
from scripts.run_v2_validation_case import run_case


ROOT = Path(__file__).resolve().parents[2]


def test_registry_yaml_and_csv_are_identical_and_unique():
    yaml_records = yaml.safe_load(
        (
            ROOT / "docs/v2/validation/v2_validation_registry.yaml"
        ).read_text(encoding="utf-8")
    )["records"]
    with (
        ROOT / "docs/v2/validation/v2_validation_registry.csv"
    ).open(newline="", encoding="utf-8") as stream:
        csv_records = list(csv.DictReader(stream))
    yaml_records = [
        {key: str(value) for key, value in record.items()}
        for record in yaml_records
    ]
    assert yaml_records == csv_records
    identifiers = [record["validation_id"] for record in yaml_records]
    assert len(identifiers) == len(set(identifiers))


def test_example_validation_case_dry_run_and_full_run(tmp_path):
    case = ROOT / "validation/cases/example_zero_source.yaml"
    assert run_case(case, tmp_path / "unused", dry_run=True) == "READY"
    output = tmp_path / "report"
    assert run_case(case, output) == "PASS"
    assert {
        "resolved_config.yaml",
        "provenance.json",
        "model_output.csv",
        "reference_output.csv",
        "metrics.json",
        "validation_report.md",
        "plots",
    } <= {path.name for path in output.iterdir()}
    assert len(list((output / "plots").glob("*.png"))) == 3


def test_missing_reference_is_blocked_not_passed(tmp_path):
    case_path = ROOT / "validation/cases/example_zero_source.yaml"
    case = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    case["reference"]["data_file"] = str(tmp_path / "missing.csv")
    missing_case = tmp_path / "missing_reference.yaml"
    missing_case.write_text(
        yaml.safe_dump(case, sort_keys=False),
        encoding="utf-8",
    )
    output = tmp_path / "blocked"
    assert run_case(missing_case, output) == "BLOCKED_EXTERNAL_DATA"
    metrics = yaml.safe_load((output / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["result"] == "BLOCKED_EXTERNAL_DATA"


def test_forcing_completeness_distinguishes_observed_and_extended(tmp_path):
    forcing = tmp_path / "forcing.csv"
    forcing.write_text(
        "time,status,value\n"
        "2025-01-01T00:00:00Z,observed,1\n"
        "2025-01-01T01:00:00Z,observed,2\n"
        "2025-01-01T02:00:00Z,extended,2\n",
        encoding="utf-8",
    )
    result = check_forcing(
        forcing,
        expected_hours=3,
        time_column="time",
        status_column="status",
    )
    assert result["complete_hourly_grid"]
    assert result["status_counts"]["observed"] == 2
    assert result["status_counts"]["extended"] == 1
    assert result["status"] == "BLOCKED_EXTERNAL_DATA"


def test_forcing_completeness_passes_only_full_observed_grid(tmp_path):
    forcing = tmp_path / "forcing.csv"
    forcing.write_text(
        "time,status\n"
        "2025-01-01T00:00:00Z,observed\n"
        "2025-01-01T01:00:00Z,observed\n",
        encoding="utf-8",
    )
    result = check_forcing(
        forcing,
        expected_hours=2,
        time_column="time",
        status_column="status",
    )
    assert result["status"] == "PASS_FULLY_OBSERVED"


def test_prepare_observed_forcing_combines_consecutive_raw_inputs(tmp_path):
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    first.write_text(
        "valid_time,t2m,latitude,longitude\n"
        "2025-01-01T00:00:00Z,290,32,117.25\n"
        "2025-01-01T01:00:00Z,291,32,117.25\n",
        encoding="utf-8",
    )
    second.write_text(
        "valid_time,t2m,latitude,longitude\n"
        "2025-01-01T02:00:00Z,292,32,117.25\n",
        encoding="utf-8",
    )
    output = tmp_path / "combined.csv"
    manifest = tmp_path / "manifest.json"
    result = prepare_observed_forcing(
        [first, second],
        output,
        manifest,
        expected_hours=3,
    )
    combined = pd.read_csv(output)
    assert list(combined["forcing_status"]) == ["observed"] * 3
    assert result["missing_hours"] == 0
    assert result["raw_inputs_modified"] is False


def test_forcing_bias_case_dry_run_dispatches_without_external_output(tmp_path):
    case = ROOT / "validation/cases/full_observed_72h.yaml"
    assert run_case(case, tmp_path / "unused", dry_run=True) == "READY"


def test_external_dataset_inventory_and_blocked_manifests_are_explicit():
    inventory_path = (
        ROOT / "docs/v2/validation/evidence/external_dataset_inventory.csv"
    )
    with inventory_path.open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
        assert stream.closed is False
    assert records
    assert set(records[0]) == {
        "dataset_id",
        "title",
        "source",
        "doi_or_url",
        "license",
        "redistribution_allowed",
        "process",
        "variables",
        "time_resolution",
        "units",
        "uncertainty",
        "detection_limit",
        "completeness",
        "applicability",
        "selection_status",
        "rejection_reason",
    }
    assert all(record["selection_status"] == "BLOCKED_EXTERNAL_DATA" for record in records)

    for name in (
        "leaf_uptake_depuration_external_001.yaml",
        "air_soil_plant_field_external_001.yaml",
    ):
        payload = yaml.safe_load(
            (ROOT / "validation/cases" / name).read_text(encoding="utf-8")
        )
        assert payload["case_status"] == "BLOCKED_EXTERNAL_DATA"
        assert payload["execution"]["permitted"] is False
        assert payload["blocking_reasons"]
