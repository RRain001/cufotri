from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cteas_ufotri.config import load_configuration
from cteas_ufotri.provenance import (
    merged_config_sha256,
    v2_named_provenance,
    validate_v2_named_provenance,
)


REGISTRY_YAML = ROOT / "docs/v2/validation/v2_validation_registry.yaml"
REGISTRY_CSV = ROOT / "docs/v2/validation/v2_validation_registry.csv"
LIMITATIONS = ROOT / "docs/v2/v2_candidate_limitations.yaml"
EXAMPLE_CASE = ROOT / "validation/cases/example_zero_source.yaml"
REFERENCE_TYPES = {
    "ANALYTIC",
    "MANUAL_ANCHOR",
    "LITERATURE_NUMERIC",
    "EXPERIMENT",
    "FIELD_OBSERVATION",
    "REFERENCE_MODEL",
    "SITE_CASE",
    "INTERNAL_REGRESSION",
}
STATUSES = {
    "READY",
    "PARTIAL",
    "BLOCKED_EXTERNAL_DATA",
    "NOT_STARTED",
    "OUT_OF_SCOPE",
}
EXTERNAL_TYPES = {
    "EXPERIMENT",
    "FIELD_OBSERVATION",
    "REFERENCE_MODEL",
    "SITE_CASE",
}
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
LIMITATION_CLOSURES = {
    "M_REEM_MANUAL_FIDELITY": {
        "VAL_REEM_RAIN_START_3_PERCENT",
        "VAL_REEM_CONCENTRATION_DEPENDENT_DIFF",
    },
    "M_MULTIBOX_STANDALONE": {"VAL_MULTIBOX_COUPLING_READINESS"},
    "M_ERA5_EXTENSION": {"VAL_FORCING_72H_OBS"},
    "M_RELEASE_DURATION": {"VAL_SOURCE_SCENARIO_TAXONOMY"},
    "M_PROJECT_PARAMETERS": {"VAL_PARAMETER_PRIORITIES"},
}
EXPECTED_EVIDENCE_COUNTS = {
    "analytic": 10,
    "manual_anchor": 5,
    "literature_numeric": 2,
    "physical_invariant": 5,
    "integration": 9,
    "regression": 1,
}
EXPECTED_CANDIDATE_COMMIT = "f097115cbfc052baa18f1e49a1207fa6b3523cff"
EXPECTED_V1_COMMIT = "6918440faa3455b848f43589784672f3bfabfe3d"
REQUIRED_EXAMPLE_ARTIFACTS = {
    "resolved_config.yaml",
    "provenance.json",
    "model_output.csv",
    "reference_output.csv",
    "metrics.json",
    "validation_report.md",
    "plots",
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _load_registry() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    yaml_payload = yaml.safe_load(REGISTRY_YAML.read_text(encoding="utf-8"))
    if not isinstance(yaml_payload, dict) or not isinstance(
        yaml_payload.get("records"), list
    ):
        raise ValueError("Registry YAML records list is missing")
    yaml_records = [
        {key: str(value) for key, value in record.items()}
        for record in yaml_payload["records"]
    ]
    with REGISTRY_CSV.open(newline="", encoding="utf-8") as stream:
        csv_records = list(csv.DictReader(stream))
    return yaml_records, csv_records


def _verify_registry() -> list[dict[str, str]]:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/sync_v2_validation_registry.py"),
            "--check",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    yaml_records, csv_records = _load_registry()
    if yaml_records != csv_records:
        raise ValueError("Registry YAML and CSV records differ")
    if not yaml_records:
        raise ValueError("Validation registry is empty")
    identifiers = [record["validation_id"] for record in yaml_records]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Validation registry IDs are not unique")
    for record in yaml_records:
        if set(record) != set(FIELDS):
            raise ValueError(
                f"Registry fields mismatch for {record.get('validation_id')}"
            )
        empty = [field for field in FIELDS if not record[field].strip()]
        if empty:
            raise ValueError(
                f"Empty registry fields for {record['validation_id']}: {empty}"
            )
        if record["reference_type"] not in REFERENCE_TYPES:
            raise ValueError(
                f"Invalid reference type for {record['validation_id']}"
            )
        if record["status"] not in STATUSES:
            raise ValueError(f"Invalid status for {record['validation_id']}")
        if record["unit"] in {"", "unknown", "unspecified"}:
            raise ValueError(f"Unit is not explicit for {record['validation_id']}")
        if record["metric"] in {"", "unknown", "unspecified"}:
            raise ValueError(f"Metric is not explicit for {record['validation_id']}")
        if record["threshold"] in {"", "unknown", "unspecified"}:
            raise ValueError(
                f"Threshold is not explicit for {record['validation_id']}"
            )
        if (
            record["reference_type"] in EXTERNAL_TYPES
            and record["data_location"] == "external_not_committed"
            and record["status"] != "BLOCKED_EXTERNAL_DATA"
        ):
            raise ValueError(
                f"Missing external evidence must be blocked: "
                f"{record['validation_id']}"
            )
    evidence_counts = {name: 0 for name in EXPECTED_EVIDENCE_COUNTS}
    for record in yaml_records:
        match = re.search(r"evidence_class=([a-z_]+)", record["notes"])
        if match and match.group(1) in evidence_counts:
            evidence_counts[match.group(1)] += 1
    if evidence_counts != EXPECTED_EVIDENCE_COUNTS:
        raise ValueError(
            f"Existing evidence migration counts differ: {evidence_counts}"
        )
    # Internal evidence remains clearly separated from empirical evidence.
    for record in yaml_records:
        if "evidence_class=integration" in record["notes"] and (
            record["reference_type"] != "INTERNAL_REGRESSION"
        ):
            raise ValueError("Integration evidence is misclassified as external")
        if "evidence_class=regression" in record["notes"] and (
            record["reference_type"] != "INTERNAL_REGRESSION"
        ):
            raise ValueError("Regression evidence is misclassified as external")
    return yaml_records


def _verify_limitations(records: list[dict[str, str]]) -> None:
    payload = yaml.safe_load(LIMITATIONS.read_text(encoding="utf-8"))
    identifiers = {
        limitation["id"] for limitation in payload.get("limitations", [])
    }
    if identifiers != set(LIMITATION_CLOSURES):
        raise ValueError("Candidate limitation IDs differ from closure matrix")
    registry_ids = {record["validation_id"] for record in records}
    missing = {
        limitation: sorted(closures - registry_ids)
        for limitation, closures in LIMITATION_CLOSURES.items()
        if not closures <= registry_ids
    }
    if missing:
        raise ValueError(f"Candidate limitation closure entries missing: {missing}")


def _verify_provenance() -> None:
    config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/test_case.yaml",
    )
    provenance = {
        **v2_named_provenance(config),
        "merged_config_sha256": merged_config_sha256(config),
    }
    validate_v2_named_provenance(provenance, config)
    if len(v2_named_provenance(config)) != 12:
        raise ValueError("Named V2 provenance field count differs from 12")


def _verify_runner() -> None:
    runner = ROOT / "scripts/run_v2_validation_case.py"
    dry_run = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--case",
            str(EXAMPLE_CASE),
            "--dry-run",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if "VALIDATION_CASE_DRY_RUN = READY" not in dry_run.stdout:
        raise ValueError("Example validation dry-run is not ready")
    with tempfile.TemporaryDirectory(prefix="v2_validation_readiness_") as tmp:
        output = Path(tmp) / "example"
        completed = subprocess.run(
            [
                sys.executable,
                str(runner),
                "--case",
                str(EXAMPLE_CASE),
                "--output",
                str(output),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        if "VALIDATION_CASE_RESULT = PASS" not in completed.stdout:
            raise ValueError("Example validation case did not pass")
        missing = sorted(
            name for name in REQUIRED_EXAMPLE_ARTIFACTS if not (output / name).exists()
        )
        if missing:
            raise ValueError(f"Example validation artifacts missing: {missing}")
        metrics = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
        if metrics.get("result") != "PASS":
            raise ValueError("Example metrics result is not PASS")
        provenance = json.loads(
            (output / "provenance.json").read_text(encoding="utf-8")
        )
        if provenance.get("candidate_tag_commit") != EXPECTED_CANDIDATE_COMMIT:
            raise ValueError("Runner candidate tag provenance differs")
        if not any((output / "plots").iterdir()):
            raise ValueError("Example validation plots are empty")


def _tracked_and_untracked_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return [ROOT / value.decode("utf-8") for value in result.split(b"\0") if value]


def _verify_repository_hygiene() -> None:
    forbidden_names = {
        ".env",
        ".cdsapirc",
        "auth.json",
        "id_rsa",
        "id_ed25519",
    }
    sensitive = []
    large = []
    private_key_paths = []
    private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
    for path in _tracked_and_untracked_paths():
        if path.name in forbidden_names:
            sensitive.append(str(path.relative_to(ROOT)))
        if path.is_file() and path.stat().st_size > 5 * 1024 * 1024:
            large.append(str(path.relative_to(ROOT)))
        if path.is_file() and path.stat().st_size <= 1024 * 1024:
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if private_key_marker in content:
                private_key_paths.append(str(path.relative_to(ROOT)))
    if sensitive or private_key_paths:
        raise ValueError(
            "Sensitive files detected by path/content; "
            f"paths={sorted(set(sensitive + private_key_paths))}"
        )
    if large:
        raise ValueError(f"Large tracked/unignored files detected: {large}")


def _verify_tags() -> None:
    candidate = _git(
        "rev-parse", "ufotri-environmental-pathways-v2-candidate^{}"
    )
    v1 = _git("rev-parse", "formal-minimal-baseline-v1^{}")
    if candidate != EXPECTED_CANDIDATE_COMMIT:
        raise ValueError("Candidate tag moved")
    if v1 != EXPECTED_V1_COMMIT:
        raise ValueError("V1 tag moved")


def _verify_parameter_priorities() -> None:
    path = ROOT / "docs/v2/validation/v2_parameter_validation_priorities.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        required = {
            "parameter",
            "value",
            "unit",
            "source_grade",
            "source",
            "applicability",
            "uncertainty",
            "site_specific",
            "validation_priority",
            "active_cases",
        }
        if set(reader.fieldnames or []) != required:
            raise ValueError("Parameter-priority columns differ from contract")
    if not rows or any(not all(row.values()) for row in rows):
        raise ValueError("Parameter-priority registry is empty or incomplete")
    if not {"HIGH", "MEDIUM", "LOW"} <= {
        row["validation_priority"] for row in rows
    }:
        raise ValueError("Parameter priorities do not cover HIGH/MEDIUM/LOW")
    if not {"true", "false"} <= {row["site_specific"] for row in rows}:
        raise ValueError("Parameter registry does not distinguish site specificity")


def main() -> None:
    records = _verify_registry()
    _verify_limitations(records)
    _verify_provenance()
    _verify_parameter_priorities()
    _verify_runner()
    _verify_repository_hygiene()
    _verify_tags()
    print("FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY")


if __name__ == "__main__":
    main()
