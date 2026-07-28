#!/usr/bin/env python3
"""Classify the D3 V3 opaque datasets without any truth or secret access."""

from __future__ import annotations

import math
from pathlib import Path
import sys
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from d3_true_reblinding_v3_common import (  # noqa: E402
    CLASSIFICATION_MANIFEST_PATH,
    CLASSIFICATION_RESULTS_PATH,
    CLASSIFICATION_ROOT,
    ROOT,
    aggregate_primary_means,
    classify_means,
    git_output,
    load_blinded_dataset,
    load_generation_manifest,
    load_protocol,
    sha256,
    validate_dataset_hashes,
    write_csv,
)
from validate_d3_true_reblinding_v3 import (  # noqa: E402
    validate_preclassification,
)


RESULT_COLUMNS = (
    "dataset_blind_id",
    "classification_result",
    "h2_log10_rmse",
    "h3_log10_rmse",
    "absolute_rmse_difference_dex",
    "classifier_observable",
    "classification_times_h",
    "parameter_refit_count",
    "latent_state_used",
    "dataset_sha256",
    "protocol_sha256",
)


def run_classification() -> dict[str, Any]:
    if CLASSIFICATION_ROOT.exists():
        raise FileExistsError(
            "V3 blind classification already exists; retry is prohibited"
        )
    validate_preclassification(
        classifier_worktree=True,
        require_tracked=True,
    )
    protocol = load_protocol(require_clean=True)
    manifest = load_generation_manifest(require_clean=True)
    dataset_hashes = validate_dataset_hashes(
        protocol, manifest, require_clean=True
    )
    rows: list[dict[str, Any]] = []
    for entry in sorted(
        manifest["datasets"], key=lambda item: item["dataset_blind_id"]
    ):
        blind_id = str(entry["dataset_blind_id"])
        frame = load_blinded_dataset(ROOT / str(entry["path"]), blind_id)
        means = aggregate_primary_means(frame, protocol)
        result, h2_rmse, h3_rmse = classify_means(means, protocol)
        difference = (
            abs(h2_rmse - h3_rmse)
            if math.isfinite(h2_rmse) and math.isfinite(h3_rmse)
            else float("nan")
        )
        rows.append(
            {
                "dataset_blind_id": blind_id,
                "classification_result": result,
                "h2_log10_rmse": h2_rmse,
                "h3_log10_rmse": h3_rmse,
                "absolute_rmse_difference_dex": difference,
                "classifier_observable": "total plant-body TFWT",
                "classification_times_h": "0.2;48;120",
                "parameter_refit_count": 0,
                "latent_state_used": False,
                "dataset_sha256": dataset_hashes[blind_id],
                "protocol_sha256": sha256(
                    ROOT
                    / "validation"
                    / "benchmarks"
                    / "d3_prospective_experiment"
                    / "preregistration"
                    / "d3_true_reblinding_v3_protocol.yaml"
                ),
            }
        )
    write_csv(CLASSIFICATION_RESULTS_PATH, RESULT_COLUMNS, rows)
    result_hash = sha256(CLASSIFICATION_RESULTS_PATH)
    classification_manifest = {
        "manifest_id": "D3_TRUE_BLIND_CLASSIFICATION_V3",
        "status": "COMPLETED_PREUNBLINDING",
        "preclassification_commit": git_output("rev-parse", "HEAD"),
        "classification_attempt": 1,
        "retry_permitted": False,
        "truth_key_accessed": False,
        "secret_accessed": False,
        "truth_mapping_disclosed": False,
        "classifier_observable": "total plant-body TFWT",
        "classification_times_h": [0.2, 48, 120],
        "parameter_refit_count": 0,
        "latent_state_used": False,
        "classification_result_sha256": result_hash,
        "sealed_generation_secret_sha256": manifest[
            "sealed_generation_secret_sha256"
        ],
        "real_external_evidence": False,
        "trusted_registry_eligible": False,
        "production_eligible": False,
        "formal_v3_physics": "NOT_STARTED",
        "v3_physics_start_gate": (
            "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        ),
    }
    CLASSIFICATION_MANIFEST_PATH.write_text(
        yaml.safe_dump(classification_manifest, sort_keys=False),
        encoding="utf-8",
    )
    return classification_manifest


def main() -> int:
    manifest = run_classification()
    print(
        "TRUE_BLIND_CLASSIFICATION_STATUS = COMPLETED_PREUNBLINDING; "
        f'CLASSIFICATION_ATTEMPT = {manifest["classification_attempt"]}; '
        "TRUTH_KEY_ACCESSED = False"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
