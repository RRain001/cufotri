"""Shared fail-closed helpers for the D3 V3 true-reblinding dry run."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "d3_prospective_experiment"
PROTOCOL_PATH = (
    BENCHMARK
    / "preregistration"
    / "d3_true_reblinding_v3_protocol.yaml"
)
V3_ROOT = BENCHMARK / "reblinding_v3"
BLINDED_ROOT = V3_ROOT / "blinded"
GENERATION_MANIFEST_PATH = V3_ROOT / "generation_manifest_v3.yaml"
SECRET_COMMITMENT_PATH = V3_ROOT / "sealed_generation_secret_sha256"
CONTAMINATION_SCAN_PATH = (
    V3_ROOT / "preclassification_contamination_scan.json"
)
CLASSIFICATION_ROOT = V3_ROOT / "classification"
CLASSIFICATION_RESULTS_PATH = (
    CLASSIFICATION_ROOT / "blind_classification_results_v3.csv"
)
CLASSIFICATION_MANIFEST_PATH = (
    CLASSIFICATION_ROOT / "blind_classification_manifest_v3.yaml"
)
UNBLINDING_ROOT = V3_ROOT / "unblinding"
UNBLINDING_COMPARISON_PATH = (
    UNBLINDING_ROOT / "unblinding_comparison_v3.csv"
)
UNBLINDING_MANIFEST_PATH = (
    UNBLINDING_ROOT / "unblinding_manifest_v3.yaml"
)
PRIVATE_ROOT = (
    ROOT / "validation" / "external_local" / "d3_prospective_reblind_v3"
)
SECRET_PATH = PRIVATE_ROOT / "sealed_generation_secret.json"
TRUTH_KEY_PATH = PRIVATE_ROOT / "truth_key_v3.json"
PRIMARY_TIMES = (0.2, 48.0, 120.0)
COMPLETE_TIMES = (0.2, 1.0, 6.0, 24.0, 48.0, 72.0, 120.0)
SYNTHETIC_STATUS = "SYNTHETIC_NOT_EXTERNAL_EVIDENCE"
OPAQUE_ID_PATTERN = re.compile(r"^[A-Z2-9]{6}$")
TRUTH_ASSOCIATION_PATTERN = re.compile(
    r"(?:^|[^A-Z0-9_])"
    r"(?:H2|H3|CHALLENGE|TRUTH_KIND|EXPECTED_RESULT|TRUTH_MAPPING)"
    r"(?:$|[^A-Z0-9_])",
    re.IGNORECASE,
)
DATASET_COLUMNS = (
    "experiment_id",
    "dataset_blind_id",
    "chamber_id",
    "replicate_id",
    "sample_datetime_utc",
    "hours_after_exposure",
    "organ",
    "fresh_mass_g",
    "dry_mass_g",
    "tissue_water_ml",
    "tfwt_bq_l_water",
    "analytical_uncertainty",
    "detection_limit_bq_l",
    "below_detection_limit",
    "quality_flag",
    "assumption_set",
    "synthetic_status",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def require_tracked_clean(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if (
        subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", relative],
            cwd=ROOT,
            check=False,
        ).returncode
        != 0
    ):
        raise ValueError(f"Tracked reblinding input changed: {relative}")


def load_protocol(*, require_clean: bool = True) -> dict[str, Any]:
    if require_clean:
        require_tracked_clean(PROTOCOL_PATH)
    protocol = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if (
        protocol["protocol_id"] != "D3_TRUE_REBLINDING_V3_PROTOCOL"
        or protocol["status"]
        != "FROZEN_BEFORE_PRIVATE_SECRET_GENERATION"
    ):
        raise ValueError("V3 true-reblinding protocol is not frozen")
    changes = protocol["frozen_change_contract"]
    if any(
        changes[key]
        for key in (
            "model_parameters_changed",
            "forcing_changed",
            "classification_rule_changed",
            "primary_times_changed",
            "challenge_definition_changed",
            "observation_realization_reused",
            "blind_ids_reused",
        )
    ):
        raise ValueError("Frozen V3 reblinding change contract was altered")
    boundary = protocol["evidence_boundary"]
    if (
        boundary["real_external_evidence"]
        or boundary["empirical_validation_claim"]
        or boundary["trusted_registry_eligible"]
        or boundary["production_eligible"]
        or boundary["formal_v3_physics"] != "NOT_STARTED"
        or boundary["h2_h3_formal_selection"] != "NOT_AUTHORIZED"
        or boundary["v3_physics_start_gate"]
        != "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    ):
        raise ValueError("V3 reblinding evidence boundary changed")
    model = protocol["model_contract"]
    if model != {
        "H2_SB1_FROZEN": {
            "slow_capture_fraction": 0.001,
            "slow_release_rate_s": 1.0e-6,
        },
        "H3_SB1_FROZEN": {
            "fast_to_slow_rate_s": 1.0e-7,
            "slow_to_fast_rate_s": 1.0e-6,
        },
        "parameter_refit": False,
        "parameter_bound_expansion": False,
    }:
        raise ValueError("Frozen H2/H3 parameter contract changed")
    sampling = protocol["sampling_contract"]
    if (
        tuple(float(item) for item in sampling["classification_times_h"])
        != PRIMARY_TIMES
        or tuple(float(item) for item in sampling["complete_times_h"])
        != COMPLETE_TIMES
        or sampling["diagnostic_times_allowed_for_classification"]
        or int(sampling["biological_replicates_per_time"]) != 5
    ):
        raise ValueError("Frozen V3 sampling contract changed")
    classifier = protocol["classifier"]
    if (
        float(classifier["absolute_rmse_difference_inconclusive_dex"])
        != 0.15
        or float(classifier["both_model_rmse_inadequate_dex"]) != 0.50
        or classifier["primary_metric"] != "log10 RMSE"
    ):
        raise ValueError("Frozen V3 classifier contract changed")
    single = protocol["single_realization_contract"]
    if (
        int(single["generation_attempt"]) != 1
        or int(single["maximum_generation_attempts"]) != 1
        or single["retry_until_expected_result"]
        or single["regeneration_after_preclassification"]
        or single["regeneration_after_classification"]
    ):
        raise ValueError("Single-realization contract changed")
    for key, expected in (
        ("assumptions_file", protocol["source_contract"]["assumptions_sha256"]),
        (
            "v2_classification_protocol_file",
            protocol["source_contract"]["v2_classification_protocol_sha256"],
        ),
        (
            "forcing_summary_file",
            protocol["source_contract"]["forcing_summary_sha256"],
        ),
        (
            "frozen_parameter_file",
            protocol["source_contract"]["frozen_parameter_file_sha256"],
        ),
    ):
        source_path = ROOT / protocol["source_contract"][key]
        if sha256(source_path) != expected:
            raise ValueError(f"Frozen source checksum changed: {key}")
    return protocol


def dataset_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    entries = manifest.get("datasets")
    if not isinstance(entries, list) or len(entries) != 3:
        raise ValueError("V3 generation manifest must bind three datasets")
    return entries


def load_generation_manifest(
    *, require_clean: bool = True
) -> dict[str, Any]:
    if require_clean:
        require_tracked_clean(GENERATION_MANIFEST_PATH)
        require_tracked_clean(SECRET_COMMITMENT_PATH)
        require_tracked_clean(CONTAMINATION_SCAN_PATH)
    manifest = yaml.safe_load(
        GENERATION_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    if (
        manifest["manifest_id"] != "D3_TRUE_REBLINDING_GENERATION_V3"
        or manifest["status"] != "FROZEN_PRECLASSIFICATION"
        or manifest["generation_attempt"] != 1
        or manifest["truth_mapping_disclosed"]
        or manifest["secret_values_disclosed"]
        or manifest["real_external_evidence"]
        or manifest["trusted_registry_eligible"]
        or manifest["production_eligible"]
    ):
        raise ValueError("V3 generation manifest is not fail closed")
    commitment = SECRET_COMMITMENT_PATH.read_text(
        encoding="utf-8"
    ).strip()
    if (
        not re.fullmatch(r"[0-9a-f]{64}", commitment)
        or manifest["sealed_generation_secret_sha256"] != commitment
    ):
        raise ValueError("Sealed-secret commitment is invalid")
    ids = [str(item["dataset_blind_id"]) for item in dataset_entries(manifest)]
    if (
        len(set(ids)) != 3
        or any(not OPAQUE_ID_PATTERN.fullmatch(item) for item in ids)
        or set(ids) & {"A", "B", "C"}
    ):
        raise ValueError("V3 opaque blind IDs are invalid")
    return manifest


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"Invalid boolean value: {value}")
    return normalized == "true"


def load_blinded_dataset(path: Path, blind_id: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if tuple(frame.columns) != DATASET_COLUMNS:
        raise ValueError(f"Dataset {blind_id} columns changed")
    if len(frame) != 35:
        raise ValueError(f"Dataset {blind_id} row count changed")
    if set(frame["dataset_blind_id"].astype(str)) != {blind_id}:
        raise ValueError(f"Dataset {blind_id} contains a different blind ID")
    if set(frame["synthetic_status"]) != {SYNTHETIC_STATUS}:
        raise ValueError(f"Dataset {blind_id} synthetic status changed")
    if set(frame["organ"]) != {"combined_stem_and_leaf"}:
        raise ValueError(f"Dataset {blind_id} observable changed")
    if set(frame["hours_after_exposure"].astype(float)) != set(COMPLETE_TIMES):
        raise ValueError(f"Dataset {blind_id} time grid changed")
    counts = frame.groupby("hours_after_exposure").size()
    if set(counts.astype(int)) != {5}:
        raise ValueError(f"Dataset {blind_id} replicate count changed")
    frame["below_detection_limit"] = frame[
        "below_detection_limit"
    ].map(parse_bool)
    numeric = frame[
        [
            "hours_after_exposure",
            "fresh_mass_g",
            "dry_mass_g",
            "tissue_water_ml",
            "tfwt_bq_l_water",
            "analytical_uncertainty",
            "detection_limit_bq_l",
        ]
    ].to_numpy(float)
    if not np.isfinite(numeric).all() or np.any(numeric[:, 4] <= 0):
        raise ValueError(f"Dataset {blind_id} contains invalid numeric data")
    return frame


def validate_dataset_hashes(
    protocol: dict[str, Any],
    manifest: dict[str, Any],
    *,
    require_clean: bool,
) -> dict[str, str]:
    prior = {
        str(item)
        for version in protocol["prior_dataset_hashes"].values()
        for item in version
    }
    result: dict[str, str] = {}
    for entry in dataset_entries(manifest):
        blind_id = str(entry["dataset_blind_id"])
        path = ROOT / str(entry["path"])
        if require_clean:
            require_tracked_clean(path)
        actual = sha256(path)
        if actual != str(entry["sha256"]):
            raise ValueError(f"Dataset {blind_id} checksum mismatch")
        if actual in prior:
            raise ValueError("V3 dataset reused a V1/V2 realization")
        load_blinded_dataset(path, blind_id)
        result[blind_id] = actual
    if len(set(result.values())) != 3:
        raise ValueError("V3 datasets must have distinct hashes")
    return result


def aggregate_primary_means(
    frame: pd.DataFrame, protocol: dict[str, Any]
) -> np.ndarray | None:
    minimum = int(
        protocol["sampling_contract"][
            "minimum_uncensored_replicates_per_primary_time"
        ]
    )
    means: list[float] = []
    for hour in PRIMARY_TIMES:
        selected = frame[np.isclose(frame["hours_after_exposure"], hour)]
        selected = selected[selected["quality_flag"] == "OK"]
        selected = selected[~selected["below_detection_limit"]]
        values = selected["tfwt_bq_l_water"].to_numpy(float)
        if len(values) < minimum:
            return None
        means.append(float(np.mean(values)))
    return np.asarray(means, dtype=float)


def log10_rmse(observed: np.ndarray, predicted: np.ndarray) -> float:
    if np.any(observed <= 0) or np.any(predicted <= 0):
        raise ValueError("log10 RMSE inputs must remain positive")
    return float(
        np.sqrt(np.mean((np.log10(observed) - np.log10(predicted)) ** 2))
    )


def classify_means(
    observed: np.ndarray | None, protocol: dict[str, Any]
) -> tuple[str, float, float]:
    if observed is None:
        return "DATA_INCONCLUSIVE", float("nan"), float("nan")
    predictions = protocol["classifier"][
        "frozen_primary_predictions_bq_l_water"
    ]
    h2 = np.asarray(predictions["H2_SB1_FROZEN"], dtype=float)
    h3 = np.asarray(predictions["H3_SB1_FROZEN"], dtype=float)
    h2_rmse = log10_rmse(observed, h2)
    h3_rmse = log10_rmse(observed, h3)
    inconclusive = float(
        protocol["classifier"][
            "absolute_rmse_difference_inconclusive_dex"
        ]
    )
    inadequate = float(
        protocol["classifier"]["both_model_rmse_inadequate_dex"]
    )
    if abs(h2_rmse - h3_rmse) < inconclusive:
        result = "DATA_INCONCLUSIVE"
    elif h2_rmse > inadequate and h3_rmse > inadequate:
        result = "BOTH_INADEQUATE"
    elif h2_rmse < h3_rmse:
        result = "H2_SUPPORTED_OVER_H3"
    else:
        result = "H3_SUPPORTED_OVER_H2"
    return result, h2_rmse, h3_rmse


def repository_scan_paths() -> list[Path]:
    tracked = [
        ROOT / line
        for line in git_output("ls-files").splitlines()
        if line
    ]
    generated = list(V3_ROOT.rglob("*")) if V3_ROOT.exists() else []
    result: dict[str, Path] = {}
    for path in tracked + generated:
        if not path.is_file():
            continue
        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            continue
        if relative.parts[:2] == ("validation", "external_local"):
            continue
        result[relative.as_posix()] = path
    return [result[key] for key in sorted(result)]


def scan_for_new_truth_associations(
    opaque_ids: list[str], dataset_hashes: dict[str, str]
) -> dict[str, Any]:
    contaminated = False
    for path in repository_scan_paths():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line in text.splitlines():
            upper = line.upper()
            if any(item in upper for item in opaque_ids):
                if TRUTH_ASSOCIATION_PATTERN.search(upper):
                    contaminated = True
                    break
        if contaminated:
            break
    return {
        "scan_id": "D3_V3_PRECLASSIFICATION_CONTAMINATION_SCAN",
        "opaque_ids": sorted(opaque_ids),
        "dataset_sha256": {
            key: dataset_hashes[key] for key in sorted(dataset_hashes)
        },
        "status": "FAIL" if contaminated else "PASS",
    }


def write_scan(scan: dict[str, Any]) -> None:
    CONTAMINATION_SCAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTAMINATION_SCAN_PATH.write_text(
        json.dumps(scan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_scan() -> dict[str, Any]:
    scan = json.loads(CONTAMINATION_SCAN_PATH.read_text(encoding="utf-8"))
    if (
        set(scan)
        != {"scan_id", "opaque_ids", "dataset_sha256", "status"}
        or scan["scan_id"]
        != "D3_V3_PRECLASSIFICATION_CONTAMINATION_SCAN"
        or scan["status"] != "PASS"
    ):
        raise ValueError("Preclassification contamination scan did not pass")
    return scan


def write_csv(
    path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
