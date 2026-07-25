from __future__ import annotations

import csv
from pathlib import Path

import yaml

from scripts.check_validation_forcing_completeness import check_forcing
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
