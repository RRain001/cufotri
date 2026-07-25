from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "docs/v2/validation/v2_validation_registry.yaml"
CSV_PATH = ROOT / "docs/v2/validation/v2_validation_registry.csv"
FIELDS = [
    "validation_id",
    "module",
    "process",
    "reference_type",
    "reference_name",
    "reference_version",
    "citation",
    "data_location",
    "input_config",
    "runner",
    "expected_output",
    "unit",
    "metric",
    "threshold",
    "status",
    "last_run_commit",
    "result_artifact",
    "notes",
]


def load_records() -> list[dict[str, str]]:
    payload = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise ValueError("Registry YAML must contain a records list")
    records = payload["records"]
    for index, record in enumerate(records, start=1):
        missing = [field for field in FIELDS if field not in record]
        extra = sorted(set(record) - set(FIELDS))
        if missing or extra:
            raise ValueError(
                f"Registry record {index} fields mismatch; "
                f"missing={missing}, extra={extra}"
            )
        for field in FIELDS:
            record[field] = str(record[field])
    return records


def render_csv(records: list[dict[str, str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return stream.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    expected = render_csv(load_records())
    if arguments.write:
        CSV_PATH.write_text(expected, encoding="utf-8")
        print(f"WROTE_VALIDATION_REGISTRY_CSV = {CSV_PATH}")
        return
    if not CSV_PATH.is_file():
        raise SystemExit("Validation registry CSV is missing")
    actual = CSV_PATH.read_text(encoding="utf-8")
    if actual != expected:
        raise SystemExit(
            "Validation registry CSV differs from YAML; run with --write"
        )
    print("VALIDATION_REGISTRY_SYNC_STATUS = PASS")


if __name__ == "__main__":
    main()
