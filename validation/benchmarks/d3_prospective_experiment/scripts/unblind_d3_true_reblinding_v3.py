#!/usr/bin/env python3
"""Unblind the single D3 V3 realization after classification is committed."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from d3_true_reblinding_v3_common import (  # noqa: E402
    CLASSIFICATION_MANIFEST_PATH,
    CLASSIFICATION_RESULTS_PATH,
    ROOT,
    SECRET_COMMITMENT_PATH,
    SECRET_PATH,
    TRUTH_KEY_PATH,
    UNBLINDING_COMPARISON_PATH,
    UNBLINDING_MANIFEST_PATH,
    UNBLINDING_ROOT,
    git_output,
    load_generation_manifest,
    sha256,
    write_csv,
)
from generate_d3_true_reblinding_v3 import (  # noqa: E402
    mapping_from_secret,
)


COMPARISON_COLUMNS = (
    "dataset_blind_id",
    "truth_class",
    "expected_result",
    "actual_result",
    "expectation_pass",
    "h2_log10_rmse",
    "h3_log10_rmse",
    "absolute_rmse_difference_dex",
)


def read_classification_rows() -> dict[str, dict[str, str]]:
    with CLASSIFICATION_RESULTS_PATH.open(
        encoding="utf-8", newline=""
    ) as stream:
        rows = {
            str(row["dataset_blind_id"]): dict(row)
            for row in csv.DictReader(stream)
        }
    if len(rows) != 3:
        raise ValueError("Classification result count changed")
    return rows


def expected_result(truth_class: str) -> str:
    return {
        "H2_SB1_FROZEN": "H2_SUPPORTED_OVER_H3",
        "H3_SB1_FROZEN": "H3_SUPPORTED_OVER_H2",
        "SYNTHETIC_OUT_OF_MODEL_CHALLENGE": "DATA_INCONCLUSIVE",
    }[truth_class]


def unblind_once() -> dict[str, Any]:
    if UNBLINDING_ROOT.exists():
        raise FileExistsError("V3 unblinding already exists")
    manifest = load_generation_manifest(require_clean=True)
    classification = yaml.safe_load(
        CLASSIFICATION_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    if (
        classification["manifest_id"] != "D3_TRUE_BLIND_CLASSIFICATION_V3"
        or classification["status"] != "COMPLETED_PREUNBLINDING"
        or classification["classification_attempt"] != 1
        or classification["retry_permitted"]
        or classification["truth_key_accessed"]
        or classification["secret_accessed"]
        or classification["truth_mapping_disclosed"]
    ):
        raise ValueError("V3 classification manifest is not pre-unblinding")
    if (
        sha256(CLASSIFICATION_RESULTS_PATH)
        != classification["classification_result_sha256"]
    ):
        raise ValueError("V3 classification checksum mismatch")
    current_head = git_output("rev-parse", "HEAD")
    preclassification = str(classification["preclassification_commit"])
    ancestry = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            preclassification,
            current_head,
        ],
        cwd=ROOT,
        check=False,
    )
    if ancestry.returncode != 0 or preclassification == current_head:
        raise ValueError(
            "Classification commit does not follow preclassification"
        )
    commitment = SECRET_COMMITMENT_PATH.read_text(
        encoding="utf-8"
    ).strip()
    if (
        commitment != manifest["sealed_generation_secret_sha256"]
        or sha256(SECRET_PATH) != commitment
    ):
        raise ValueError("Sealed secret does not match tracked commitment")
    secret = json.loads(SECRET_PATH.read_text(encoding="utf-8"))
    truth_key = json.loads(TRUTH_KEY_PATH.read_text(encoding="utf-8"))
    derived_mapping = mapping_from_secret(secret)
    recorded_mapping = {
        str(item["dataset_blind_id"]): str(item["class"])
        for item in truth_key["mapping"]
    }
    if (
        truth_key["tracked"]
        or truth_key["sealed_generation_secret_sha256"] != commitment
        or recorded_mapping != derived_mapping
    ):
        raise ValueError("Private truth key does not match sealed secret")
    classified = read_classification_rows()
    if set(classified) != set(derived_mapping):
        raise ValueError("Classified blind IDs do not match truth commitment")
    comparisons: list[dict[str, Any]] = []
    for blind_id in sorted(derived_mapping):
        truth_class = derived_mapping[blind_id]
        expected = expected_result(truth_class)
        actual = classified[blind_id]["classification_result"]
        comparisons.append(
            {
                "dataset_blind_id": blind_id,
                "truth_class": truth_class,
                "expected_result": expected,
                "actual_result": actual,
                "expectation_pass": actual == expected,
                "h2_log10_rmse": classified[blind_id]["h2_log10_rmse"],
                "h3_log10_rmse": classified[blind_id]["h3_log10_rmse"],
                "absolute_rmse_difference_dex": classified[blind_id][
                    "absolute_rmse_difference_dex"
                ],
            }
        )
    write_csv(
        UNBLINDING_COMPARISON_PATH,
        COMPARISON_COLUMNS,
        comparisons,
    )
    pass_count = sum(bool(item["expectation_pass"]) for item in comparisons)
    status = (
        "PASS_TRUE_REBLINDING"
        if pass_count == len(comparisons)
        else "FAIL_OR_INCONCLUSIVE_SINGLE_REALIZATION"
    )
    unblinding_manifest = {
        "manifest_id": "D3_TRUE_REBLINDING_UNBLINDING_V3",
        "status": status,
        "generation_attempt": 1,
        "classification_attempt": 1,
        "regeneration_or_retry_permitted": False,
        "preclassification_commit": preclassification,
        "classification_commit": current_head,
        "sealed_generation_secret_sha256_verified": True,
        "truth_key_matches_sealed_secret": True,
        "expectation_pass_count": pass_count,
        "expectation_total_count": len(comparisons),
        "comparison_sha256": sha256(UNBLINDING_COMPARISON_PATH),
        "real_external_evidence": False,
        "trusted_registry_eligible": False,
        "production_eligible": False,
        "formal_v3_physics": "NOT_STARTED",
        "v3_physics_start_gate": (
            "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        ),
    }
    UNBLINDING_MANIFEST_PATH.write_text(
        yaml.safe_dump(unblinding_manifest, sort_keys=False),
        encoding="utf-8",
    )
    return unblinding_manifest


def main() -> int:
    manifest = unblind_once()
    print(
        f'TRUE_REBLINDING_RESULT = {manifest["status"]}; '
        f'EXPECTATIONS = {manifest["expectation_pass_count"]}/'
        f'{manifest["expectation_total_count"]}; '
        "GENERATION_ATTEMPTS = 1"
    )
    return (
        0
        if manifest["status"] == "PASS_TRUE_REBLINDING"
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
