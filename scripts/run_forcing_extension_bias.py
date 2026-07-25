#!/usr/bin/env python3
"""Compare complete observed forcing with the frozen 48 h + 24 h extension."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration, load_yaml
from cteas_ufotri.meteorology.era5_reader import (
    prepare_hourly_forcing,
    read_era5,
)
from cteas_ufotri.provenance import merged_config_sha256, v2_named_provenance
from scripts.check_validation_forcing_completeness import check_forcing
from scripts.run_v2_end_to_end import hybrid_era5_forcing


ROOT = Path(__file__).resolve().parents[1]


def _repo_path(value: str, manifest_path: Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    repository_candidate = ROOT / candidate
    if repository_candidate.exists():
        return repository_candidate
    return manifest_path.parent / candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _relative_difference(observed: float, extended: float) -> float:
    if extended == 0.0:
        return 0.0 if observed == 0.0 else math.inf
    return (observed - extended) / abs(extended)


def _metrics(
    observed: pd.DataFrame,
    extended: pd.DataFrame,
    observables: list[dict[str, str]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    time_seconds = (
        pd.to_datetime(observed["time"], utc=True)
        - pd.to_datetime(observed["time"], utc=True).iloc[0]
    ).dt.total_seconds().to_numpy()
    for observable in observables:
        column = observable["column"]
        observed_values = observed[column].astype(float).to_numpy()
        extended_values = extended[column].astype(float).to_numpy()
        denominator = max(float(np.mean(np.abs(extended_values))), 1.0e-300)
        observed_peak_index = int(np.argmax(observed_values))
        extended_peak_index = int(np.argmax(extended_values))
        records.append(
            {
                "column": column,
                "unit": observable["unit"],
                "observed_final": float(observed_values[-1]),
                "extended_final": float(extended_values[-1]),
                "final_relative_difference": _relative_difference(
                    float(observed_values[-1]),
                    float(extended_values[-1]),
                ),
                "normalized_rmse": float(
                    np.sqrt(np.mean((observed_values - extended_values) ** 2))
                    / denominator
                ),
                "peak_ratio": (
                    float(np.max(observed_values) / np.max(extended_values))
                    if float(np.max(extended_values)) != 0.0
                    else None
                ),
                "time_to_peak_difference_s": float(
                    time_seconds[observed_peak_index]
                    - time_seconds[extended_peak_index]
                ),
            }
        )
    return records


def _write_plots(
    observed: pd.DataFrame,
    extended: pd.DataFrame,
    observables: list[dict[str, str]],
    directory: Path,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    time = pd.to_datetime(observed["time"], utc=True)
    for observable in observables:
        column = observable["column"]
        fig, axis = plt.subplots(figsize=(8, 4.5))
        axis.plot(time, observed[column], label="72 h observed forcing")
        axis.plot(
            time,
            extended[column],
            linestyle="--",
            label="48 h observed + 24 h deterministic extension",
        )
        axis.set_xlabel("UTC")
        axis.set_ylabel(f"{column} [{observable['unit']}]")
        axis.legend(fontsize=8)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(directory / f"{column}.png", dpi=140)
        plt.close(fig)


def run_forcing_bias_case(manifest_path: Path, output_directory: Path) -> str:
    case = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if case.get("validation_mode") != "forcing_extension_bias":
        raise ValueError("Not a forcing-extension-bias case")
    model = case["model"]
    observed_path = _repo_path(model["observed_forcing"], manifest_path)
    baseline_path = _repo_path(model["baseline_observed_forcing"], manifest_path)
    mapping_path = _repo_path(model["mapping_config"], manifest_path)
    expected_checksums = model["checksums_sha256"]
    for label, path in {
        "observed_forcing": observed_path,
        "baseline_observed_forcing": baseline_path,
    }.items():
        if not path.is_file():
            return _write_blocked(output_directory, f"Missing forcing: {path}")
        if _sha256(path) != expected_checksums[label]:
            raise ValueError(f"Checksum mismatch for {label}: {path}")

    completeness = check_forcing(
        observed_path,
        expected_hours=72,
        time_column="valid_time",
        status_column="forcing_status",
    )
    if completeness["status"] != "PASS_FULLY_OBSERVED":
        return _write_blocked(
            output_directory,
            "Observed forcing does not contain 72 observed consecutive hours",
        )

    default_path = _repo_path(model["default_config"], manifest_path)
    case_path = _repo_path(model["case_config"], manifest_path)
    config = load_configuration(default_path, case_path)
    mapping = load_yaml(mapping_path)
    raw_observed = read_era5(observed_path, mapping)
    observed_forcing = prepare_hourly_forcing(
        raw_observed,
        config["physics"]["fallback_shortwave_absorptivity"],
        config["physics"]["fallback_net_longwave_loss_w_m2"],
        accumulation_semantics=mapping.get("accumulation_semantics", "interval"),
    )
    extended_forcing = hybrid_era5_forcing(config, baseline_path)
    observed_output = run_short_case(config, observed_forcing)
    extended_output = run_short_case(config, extended_forcing)
    for frame in (observed_output, extended_output):
        frame["cumulative_wet_deposition_bq"] = frame[
            "surface_wet_input_bq"
        ].astype(float).cumsum()
        frame["cumulative_dry_deposition_bq"] = frame[
            "surface_dry_input_bq"
        ].astype(float).cumsum()

    output_directory.mkdir(parents=True, exist_ok=True)
    observed_output.to_csv(output_directory / "model_output.csv", index=False)
    extended_output.to_csv(output_directory / "reference_output.csv", index=False)
    (output_directory / "resolved_config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )
    metric_records = _metrics(
        observed_output,
        extended_output,
        case["observables"],
    )
    payload = {
        "validation_id": case["validation_id"],
        "result": "PASS",
        "forcing_completeness": completeness,
        "interpretation": (
            "PASS denotes forcing completeness and successful comparison only; "
            "it is not site or external model validation."
        ),
        "metrics": metric_records,
    }
    (output_directory / "metrics.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    provenance = {
        "validation_id": case["validation_id"],
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git("rev-parse", "HEAD"),
        "candidate_tag": "ufotri-environmental-pathways-v2-candidate",
        "candidate_tag_commit": _git(
            "rev-parse", "ufotri-environmental-pathways-v2-candidate^{}"
        ),
        "merged_config_sha256": merged_config_sha256(config),
        "input_checksums_sha256": {
            "validation_case": _sha256(manifest_path),
            "observed_forcing": _sha256(observed_path),
            "baseline_observed_forcing": _sha256(baseline_path),
            "mapping_config": _sha256(mapping_path),
        },
        "forcing": {
            "observed": "72/72 observed hourly ERA5 time-series rows",
            "reference": "48 h ERA5 plus documented deterministic 24 h extension",
        },
        **v2_named_provenance(config),
    }
    (output_directory / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_plots(
        observed_output,
        extended_output,
        case["observables"],
        output_directory / "plots",
    )
    lines = [
        f"# Forcing extension bias: {case['validation_id']}",
        "",
        "`RESULT = PASS_72_OF_72_OBSERVED`",
        "",
        "This is a forcing sensitivity comparison, not site validation.",
        "",
        "| Observable | Unit | Final relative difference | NRMSE | Peak ratio | Peak-time difference (s) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for record in metric_records:
        peak_ratio = (
            "n/a" if record["peak_ratio"] is None else f"{record['peak_ratio']:.6g}"
        )
        lines.append(
            f"| {record['column']} | {record['unit']} | "
            f"{record['final_relative_difference']:.6g} | "
            f"{record['normalized_rmse']:.6g} | {peak_ratio} | "
            f"{record['time_to_peak_difference_s']:.6g} |"
        )
    (output_directory / "validation_report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return "PASS"


def _write_blocked(output_directory: Path, reason: str) -> str:
    output_directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "result": "BLOCKED_EXTERNAL_DATA",
        "reason": reason,
    }
    (output_directory / "metrics.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_directory / "validation_report.md").write_text(
        "# Forcing extension bias\n\n"
        "`RESULT = BLOCKED_EXTERNAL_DATA`\n\n"
        f"{reason}\n",
        encoding="utf-8",
    )
    return "BLOCKED_EXTERNAL_DATA"
