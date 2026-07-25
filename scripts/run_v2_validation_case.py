from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "cteas_ufotri_matplotlib")
)
os.environ.setdefault(
    "XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "cteas_ufotri_cache")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration
from cteas_ufotri.provenance import (
    merged_config_sha256,
    v2_named_provenance,
)
from validation.adapters.csv_adapter import read_reference_csv, sha256
from validation import metrics as validation_metrics

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
SCENARIO_TYPES = {
    "CONTINUOUS_ROUTINE",
    "FINITE_ROUTINE_WINDOW",
    "ACCIDENT_PULSE",
    "ACCIDENT_TIME_SERIES",
    "POST_RELEASE_FOLLOWUP",
}
SCENARIO_FIELDS = {
    "release_scenario_type",
    "release_start",
    "release_end",
    "source_rate_basis",
    "post_release_duration",
}
METRIC_FUNCTIONS = {
    "absolute_error": validation_metrics.absolute_error,
    "relative_error": validation_metrics.relative_error,
    "bias": validation_metrics.bias,
    "normalized_mean_bias": validation_metrics.normalized_mean_bias,
    "rmse": validation_metrics.rmse,
    "normalized_rmse": validation_metrics.normalized_rmse,
    "correlation": validation_metrics.correlation,
    "peak_ratio": validation_metrics.peak_ratio,
}


def _repo_path(value: str, manifest_path: Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    repo_candidate = ROOT / candidate
    if repo_candidate.exists():
        return repo_candidate
    return manifest_path.parent / candidate


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_manifest(case: dict[str, Any]) -> None:
    required = {
        "validation_id",
        "reference_type",
        "release_scenario",
        "model",
        "reference",
        "observables",
    }
    missing = sorted(required - set(case))
    if missing:
        raise ValueError(f"Validation case fields missing: {missing}")
    if case["reference_type"] not in REFERENCE_TYPES:
        raise ValueError("Unsupported validation reference_type")
    scenario = case["release_scenario"]
    if set(scenario) != SCENARIO_FIELDS:
        raise ValueError(
            "Release scenario must contain exactly: "
            + ", ".join(sorted(SCENARIO_FIELDS))
        )
    if scenario["release_scenario_type"] not in SCENARIO_TYPES:
        raise ValueError("Unsupported release_scenario_type")
    start = datetime.fromisoformat(
        str(scenario["release_start"]).replace("Z", "+00:00")
    )
    end = datetime.fromisoformat(
        str(scenario["release_end"]).replace("Z", "+00:00")
    )
    if end <= start:
        raise ValueError("release_end must be after release_start")
    for key in ("source_rate_basis", "post_release_duration"):
        if not str(scenario[key]).strip():
            raise ValueError(f"Release scenario {key} must be explicit")
    model = case["model"]
    if not {"default_config", "case_config", "overrides"} <= set(model):
        raise ValueError("Model configuration contract is incomplete")
    reference = case["reference"]
    required_reference = {
        "name",
        "version",
        "citation",
        "data_file",
        "licence",
        "checksum_sha256",
    }
    if not required_reference <= set(reference):
        raise ValueError("Reference metadata contract is incomplete")
    if not case["observables"]:
        raise ValueError("At least one observable is required")
    for observable in case["observables"]:
        required_observable = {
            "model_column",
            "reference_column",
            "unit",
            "metric",
            "threshold",
            "unit_conversion",
        }
        if not required_observable <= set(observable):
            raise ValueError("Observable contract is incomplete")
        if observable["metric"] not in METRIC_FUNCTIONS:
            raise ValueError(f"Unsupported metric: {observable['metric']}")
        if not str(observable["unit"]).strip():
            raise ValueError("Observable unit must be explicit")
        if float(observable["threshold"]) < 0.0:
            raise ValueError("Metric threshold must be non-negative")


def _metric_value(
    metric_name: str,
    model_values: list[float],
    reference_values: list[float],
) -> float:
    function = METRIC_FUNCTIONS[metric_name]
    if metric_name in {"absolute_error", "relative_error"}:
        return float(function(model_values[-1], reference_values[-1]))
    return float(function(model_values, reference_values))


def _write_plots(
    model: pd.DataFrame,
    reference: pd.DataFrame,
    observables: list[dict[str, Any]],
    directory: Path,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for observable in observables:
        model_column = observable["model_column"]
        reference_column = observable["reference_column"]
        fig, axis = plt.subplots(figsize=(7, 4))
        axis.plot(
            range(len(model)),
            model[model_column],
            label="model",
        )
        if len(reference) == len(model):
            axis.plot(
                range(len(reference)),
                reference[reference_column],
                color="black",
                linestyle="--",
                label="reference",
            )
        else:
            reference_value = float(reference[reference_column].iloc[-1])
            axis.axhline(
                reference_value,
                color="black",
                linestyle="--",
                label="reference",
            )
        axis.set_xlabel("model step")
        axis.set_ylabel(f"{model_column} [{observable['unit']}]")
        axis.legend()
        fig.tight_layout()
        fig.savefig(directory / f"{model_column}.png", dpi=130)
        plt.close(fig)


def run_case(manifest_path: Path, output_directory: Path, dry_run: bool = False) -> str:
    with manifest_path.open(encoding="utf-8") as stream:
        case = yaml.safe_load(stream)
    if not isinstance(case, dict):
        raise ValueError("Validation case must be a YAML mapping")
    if case.get("validation_mode") == "forcing_extension_bias":
        if dry_run:
            print(
                "VALIDATION_CASE_DRY_RUN = READY; "
                f"validation_id={case['validation_id']}"
            )
            return "READY"
        from scripts.run_forcing_extension_bias import run_forcing_bias_case

        result = run_forcing_bias_case(manifest_path, output_directory)
        print(
            f"VALIDATION_CASE_RESULT = {result}; "
            f"validation_id={case['validation_id']}"
        )
        return result
    _validate_manifest(case)

    model_specification = case["model"]
    default_path = _repo_path(model_specification["default_config"], manifest_path)
    case_path = _repo_path(model_specification["case_config"], manifest_path)
    if not default_path.is_file() or not case_path.is_file():
        raise FileNotFoundError("Model configuration input is missing")
    config = load_configuration(default_path, case_path)
    config = _deep_merge(config, model_specification["overrides"])
    # Re-run the configuration validator on a temporary YAML pair without
    # mutating repository configuration.
    with tempfile.TemporaryDirectory(prefix="v2_validation_config_") as temporary:
        temporary_path = Path(temporary)
        empty_base = temporary_path / "base.yaml"
        resolved_case = temporary_path / "case.yaml"
        empty_base.write_text("{}\n", encoding="utf-8")
        resolved_case.write_text(
            yaml.safe_dump(config, sort_keys=False),
            encoding="utf-8",
        )
        config = load_configuration(empty_base, resolved_case)

    reference_path = _repo_path(case["reference"]["data_file"], manifest_path)
    if dry_run:
        status = (
            "READY"
            if reference_path.is_file()
            and sha256(reference_path) == case["reference"]["checksum_sha256"]
            else "BLOCKED_EXTERNAL_DATA"
        )
        print(
            f"VALIDATION_CASE_DRY_RUN = {status}; "
            f"validation_id={case['validation_id']}"
        )
        return status
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "plots").mkdir(exist_ok=True)
    required_columns = {
        observable["reference_column"] for observable in case["observables"]
    }
    try:
        reference = read_reference_csv(
            reference_path,
            required_columns,
            case["reference"]["checksum_sha256"],
        )
    except FileNotFoundError:
        metrics_payload = {
            "validation_id": case["validation_id"],
            "result": "BLOCKED_EXTERNAL_DATA",
            "reason": f"Reference data missing: {reference_path}",
            "metrics": [],
        }
        (output_directory / "metrics.json").write_text(
            json.dumps(metrics_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        (output_directory / "validation_report.md").write_text(
            "# Validation report\n\n"
            f"`RESULT = BLOCKED_EXTERNAL_DATA`\n\n"
            f"Reference data is missing: `{reference_path}`.\n",
            encoding="utf-8",
        )
        return "BLOCKED_EXTERNAL_DATA"

    model = run_short_case(config)
    missing_model = sorted(
        {
            observable["model_column"] for observable in case["observables"]
        }
        - set(model.columns)
    )
    if missing_model:
        raise ValueError(f"Model output columns missing: {missing_model}")
    model.to_csv(output_directory / "model_output.csv", index=False)
    reference.to_csv(output_directory / "reference_output.csv", index=False)
    (output_directory / "resolved_config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )

    metric_records = []
    results: list[str] = []
    for observable in case["observables"]:
        if len(reference) == len(model):
            model_values = [
                float(value) for value in model[observable["model_column"]]
            ]
            reference_values = [
                float(value) for value in reference[
                    observable["reference_column"]
                ]
            ]
        else:
            model_values = [float(model[observable["model_column"]].iloc[-1])]
            reference_values = [
                float(reference[observable["reference_column"]].iloc[-1])
            ]
        value = _metric_value(
            observable["metric"], model_values, reference_values
        )
        if not math.isfinite(value):
            metric_result = "INCONCLUSIVE"
        elif value <= float(observable["threshold"]):
            metric_result = "PASS"
        else:
            metric_result = "FAIL"
        results.append(metric_result)
        metric_records.append(
            {
                "model_column": observable["model_column"],
                "reference_column": observable["reference_column"],
                "unit": observable["unit"],
                "unit_conversion": observable["unit_conversion"],
                "metric": observable["metric"],
                "value": value,
                "threshold": float(observable["threshold"]),
                "comparison": "<=",
                "result": metric_result,
            }
        )
    if "FAIL" in results:
        result = "FAIL"
    elif "INCONCLUSIVE" in results:
        result = "INCONCLUSIVE"
    else:
        result = "PASS"
    metrics_payload = {
        "validation_id": case["validation_id"],
        "result": result,
        "metrics": metric_records,
    }
    (output_directory / "metrics.json").write_text(
        json.dumps(metrics_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    candidate_commit = _git(
        "rev-parse", "ufotri-environmental-pathways-v2-candidate^{}"
    )
    provenance = {
        "validation_id": case["validation_id"],
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git("rev-parse", "HEAD"),
        "candidate_tag": "ufotri-environmental-pathways-v2-candidate",
        "candidate_tag_commit": candidate_commit,
        "merged_config_sha256": merged_config_sha256(config),
        "input_checksums_sha256": {
            "validation_case": _file_sha256(manifest_path),
            "default_config": _file_sha256(default_path),
            "case_config": _file_sha256(case_path),
            "reference": _file_sha256(reference_path),
        },
        "reference": {
            **case["reference"],
            "reference_type": case["reference_type"],
        },
        "release_scenario": case["release_scenario"],
        "observables": [
            {
                "model_column": item["model_column"],
                "reference_column": item["reference_column"],
                "unit": item["unit"],
                "unit_conversion": item["unit_conversion"],
            }
            for item in case["observables"]
        ],
        **v2_named_provenance(config),
    }
    (output_directory / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_plots(model, reference, case["observables"], output_directory / "plots")
    report_lines = [
        f"# Validation report: {case['validation_id']}",
        "",
        f"`RESULT = {result}`",
        "",
        f"- Reference type: `{case['reference_type']}`",
        f"- Reference: {case['reference']['name']} ({case['reference']['version']})",
        f"- Model commit: `{provenance['git_commit']}`",
        f"- Candidate tag commit: `{candidate_commit}`",
        f"- Effective configuration SHA-256: `{provenance['merged_config_sha256']}`",
        "",
        "| Observable | Unit | Metric | Value | Threshold | Result |",
        "|---|---|---|---:|---:|---|",
    ]
    for record in metric_records:
        report_lines.append(
            f"| {record['model_column']} | {record['unit']} | "
            f"{record['metric']} | {record['value']:.12g} | "
            f"{record['threshold']:.12g} | {record['result']} |"
        )
    report_lines.extend(
        [
            "",
            "This result evaluates only the declared case and is not a claim of "
            "site calibration or regulatory validation.",
        ]
    )
    (output_directory / "validation_report.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )
    print(f"VALIDATION_CASE_RESULT = {result}; validation_id={case['validation_id']}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    if not arguments.dry_run and arguments.output is None:
        parser.error("--output is required unless --dry-run is used")
    output = arguments.output or Path(tempfile.gettempdir()) / "unused_validation_output"
    result = run_case(arguments.case.resolve(), output.resolve(), arguments.dry_run)
    if result in {"FAIL", "INCONCLUSIVE"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
