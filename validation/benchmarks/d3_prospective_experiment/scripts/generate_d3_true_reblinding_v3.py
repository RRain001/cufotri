#!/usr/bin/env python3
"""Generate exactly one private D3 V3 true-reblinding realization."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from typing import Any

import numpy as np
import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from d3_prospective_core import (  # noqa: E402
    COMPLETE_TIMES,
    frozen_prediction_table,
    mean_one_lognormal,
    prediction_vectors,
)
from d3_true_reblinding_v3_common import (  # noqa: E402
    BLINDED_ROOT,
    CONTAMINATION_SCAN_PATH,
    DATASET_COLUMNS,
    GENERATION_MANIFEST_PATH,
    OPAQUE_ID_PATTERN,
    PRIVATE_ROOT,
    PROTOCOL_PATH,
    ROOT,
    SECRET_COMMITMENT_PATH,
    SECRET_PATH,
    SYNTHETIC_STATUS,
    TRUTH_KEY_PATH,
    V3_ROOT,
    load_protocol,
    scan_for_new_truth_associations,
    sha256,
    write_scan,
)
from generate_d3_prospective_forcing import (  # noqa: E402
    assumption_value,
    load_assumptions,
)


TRUTH_CLASSES = (
    "H2_SB1_FROZEN",
    "H3_SB1_FROZEN",
    "SYNTHETIC_OUT_OF_MODEL_CHALLENGE",
)
OPAQUE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def write_private_json_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def assert_private_ignored(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if tracked.returncode == 0:
        raise ValueError(f"Private V3 file is tracked: {relative}")
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", relative],
        cwd=ROOT,
        check=False,
    )
    if ignored.returncode != 0:
        raise ValueError(f"Private V3 file is not ignored: {relative}")


def create_secret() -> dict[str, Any]:
    if SECRET_PATH.exists() or TRUTH_KEY_PATH.exists() or V3_ROOT.exists():
        raise FileExistsError(
            "V3 realization already exists; regeneration is prohibited"
        )
    payload = {
        "secret_id": "D3_TRUE_REBLINDING_SEALED_SECRET_V3",
        "generation_attempt": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "blind_permutation_secret_hex": secrets.token_hex(32),
        "opaque_id_generation_secret_hex": secrets.token_hex(32),
        "h2_observation_noise_secret_hex": secrets.token_hex(32),
        "h3_observation_noise_secret_hex": secrets.token_hex(32),
        "challenge_observation_noise_secret_hex": secrets.token_hex(32),
    }
    write_private_json_once(SECRET_PATH, payload)
    os.chmod(SECRET_PATH, 0o600)
    assert_private_ignored(SECRET_PATH)
    return payload


def hmac_digest(secret_hex: str, label: str) -> bytes:
    return hmac.new(
        bytes.fromhex(secret_hex),
        label.encode("utf-8"),
        hashlib.sha256,
    ).digest()


def opaque_ids_from_secret(secret: dict[str, Any]) -> list[str]:
    key = str(secret["opaque_id_generation_secret_hex"])
    result: list[str] = []
    index = 0
    while len(result) < 3:
        digest = hmac_digest(key, f"opaque-slot:{index}")
        candidate = "".join(
            OPAQUE_ALPHABET[value % len(OPAQUE_ALPHABET)]
            for value in digest[:6]
        )
        index += 1
        if (
            candidate not in result
            and candidate not in {"A", "B", "C"}
            and OPAQUE_ID_PATTERN.fullmatch(candidate)
        ):
            result.append(candidate)
    return sorted(result)


def mapping_from_secret(secret: dict[str, Any]) -> dict[str, str]:
    opaque_ids = opaque_ids_from_secret(secret)
    permutation_key = str(secret["blind_permutation_secret_hex"])
    permuted_truths = sorted(
        TRUTH_CLASSES,
        key=lambda item: hmac_digest(permutation_key, item),
    )
    return dict(zip(opaque_ids, permuted_truths, strict=True))


def observation_seed(secret: dict[str, Any], truth_class: str) -> int:
    key = {
        "H2_SB1_FROZEN": "h2_observation_noise_secret_hex",
        "H3_SB1_FROZEN": "h3_observation_noise_secret_hex",
        "SYNTHETIC_OUT_OF_MODEL_CHALLENGE": (
            "challenge_observation_noise_secret_hex"
        ),
    }[truth_class]
    digest = hmac_digest(str(secret[key]), "numpy-pcg64-seed")
    return int.from_bytes(digest[:16], "big")


def truth_vectors(protocol: dict[str, Any]) -> dict[str, np.ndarray]:
    prediction_table, _ = frozen_prediction_table()
    times, h2, h3 = prediction_vectors(prediction_table)
    if not np.allclose(
        times, np.asarray(COMPLETE_TIMES, dtype=float), rtol=0, atol=0
    ):
        raise ValueError("Frozen prediction time grid changed")
    primary_indices = [
        int(np.where(np.isclose(times, target))[0][0])
        for target in (0.2, 48.0, 120.0)
    ]
    frozen = protocol["classifier"][
        "frozen_primary_predictions_bq_l_water"
    ]
    np.testing.assert_allclose(
        h2[primary_indices],
        np.asarray(frozen["H2_SB1_FROZEN"], dtype=float),
        rtol=0,
        atol=1.0e-12,
    )
    np.testing.assert_allclose(
        h3[primary_indices],
        np.asarray(frozen["H3_SB1_FROZEN"], dtype=float),
        rtol=0,
        atol=1.0e-12,
    )
    challenge = np.sqrt(h2 * h3)
    target = float(
        protocol["challenge_contract"]["systematic_deviation_time_h"]
    )
    factor = float(
        protocol["challenge_contract"]["systematic_deviation_factor"]
    )
    index = int(np.where(np.isclose(times, target))[0][0])
    challenge[index] *= factor
    return {
        "H2_SB1_FROZEN": h2,
        "H3_SB1_FROZEN": h3,
        "SYNTHETIC_OUT_OF_MODEL_CHALLENGE": challenge,
    }


def sample_rows(
    assumptions: dict[str, Any],
    *,
    blind_id: str,
    truth: np.ndarray,
    seed: int,
) -> list[dict[str, Any]]:
    measurement = assumptions["measurement_assumptions"]
    replicates = int(
        assumption_value(
            assumptions["biological_replicates"], "default_per_time"
        )
    )
    total_cv = assumption_value(measurement, "combined_total_cv_target")
    analytical_cv = assumption_value(measurement, "analytical_cv")
    detection_limit = assumption_value(
        measurement, "assumed_detection_limit_bq_l"
    )
    fresh_mean = assumption_value(measurement, "sample_fresh_mass_mean_g")
    fresh_cv = assumption_value(measurement, "sample_fresh_mass_cv")
    dry_fraction_mean = assumption_value(
        measurement, "sample_dry_fraction_mean"
    )
    dry_fraction_cv = assumption_value(
        measurement, "sample_dry_fraction_cv"
    )
    start = datetime.fromisoformat(
        assumptions["exposure_conditions"]["experiment_start_utc"].replace(
            "Z", "+00:00"
        )
    ).astimezone(timezone.utc)
    exposure_h = assumption_value(
        assumptions["exposure_conditions"], "exposure_duration_h"
    )
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for time_index, (hour, expected) in enumerate(
        zip(COMPLETE_TIMES, truth, strict=True)
    ):
        observation = mean_one_lognormal(rng, total_cv, replicates)
        fresh = mean_one_lognormal(rng, fresh_cv, replicates)
        dry = mean_one_lognormal(rng, dry_fraction_cv, replicates)
        for replicate_index in range(replicates):
            value = float(expected * observation[replicate_index])
            fresh_mass = round(float(fresh_mean * fresh[replicate_index]), 2)
            dry_fraction = float(
                np.clip(
                    dry_fraction_mean * dry[replicate_index],
                    0.05,
                    0.60,
                )
            )
            dry_mass = round(fresh_mass * dry_fraction, 2)
            sample_time = start + timedelta(
                hours=float(exposure_h + float(hour))
            )
            rows.append(
                {
                    "experiment_id": "D3-PROSPECTIVE-TRUE-REBLIND-V3",
                    "dataset_blind_id": blind_id,
                    "chamber_id": "D3-SYNTHETIC-CHAMBER-01",
                    "replicate_id": (
                        f"{blind_id}-T{time_index + 1:02d}-"
                        f"R{replicate_index + 1:02d}"
                    ),
                    "sample_datetime_utc": sample_time.isoformat().replace(
                        "+00:00", "Z"
                    ),
                    "hours_after_exposure": float(hour),
                    "organ": "combined_stem_and_leaf",
                    "fresh_mass_g": fresh_mass,
                    "dry_mass_g": dry_mass,
                    "tissue_water_ml": round(fresh_mass - dry_mass, 2),
                    "tfwt_bq_l_water": value,
                    "analytical_uncertainty": value * analytical_cv,
                    "detection_limit_bq_l": detection_limit,
                    "below_detection_limit": value < detection_limit,
                    "quality_flag": "OK",
                    "assumption_set": "D3_PROSPECTIVE_ASSUMPTIONS_V2",
                    "synthetic_status": SYNTHETIC_STATUS,
                }
            )
    return rows


def write_dataset(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=DATASET_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def generate_once() -> dict[str, Any]:
    protocol = load_protocol(require_clean=True)
    assumptions = load_assumptions(require_committed=True)
    secret = create_secret()
    secret_commitment = sha256(SECRET_PATH)
    mapping = mapping_from_secret(secret)
    vectors = truth_vectors(protocol)
    datasets: list[dict[str, Any]] = []
    for blind_id in sorted(mapping):
        rows = sample_rows(
            assumptions,
            blind_id=blind_id,
            truth=vectors[mapping[blind_id]],
            seed=observation_seed(secret, mapping[blind_id]),
        )
        path = BLINDED_ROOT / f"dataset_{blind_id}.csv"
        write_dataset(path, rows)
        datasets.append(
            {
                "dataset_blind_id": blind_id,
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path),
                "row_count": len(rows),
                "truth_disclosed": False,
            }
        )

    truth_key = {
        "truth_key_id": "D3_TRUE_REBLINDING_TRUTH_KEY_V3",
        "tracked": False,
        "sealed_generation_secret_sha256": secret_commitment,
        "mapping": [
            {"dataset_blind_id": item, "class": mapping[item]}
            for item in sorted(mapping)
        ],
    }
    write_private_json_once(TRUTH_KEY_PATH, truth_key)
    os.chmod(TRUTH_KEY_PATH, 0o600)
    assert_private_ignored(TRUTH_KEY_PATH)

    SECRET_COMMITMENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SECRET_COMMITMENT_PATH.write_text(
        secret_commitment + "\n", encoding="utf-8"
    )
    manifest = {
        "manifest_id": "D3_TRUE_REBLINDING_GENERATION_V3",
        "status": "FROZEN_PRECLASSIFICATION",
        "generation_attempt": 1,
        "maximum_generation_attempts": 1,
        "regeneration_permitted": False,
        "protocol_sha256": sha256(PROTOCOL_PATH),
        "generator_sha256": sha256(Path(__file__)),
        "forcing_sha256": protocol["source_contract"][
            "measured_forcing_sha256"
        ],
        "sealed_generation_secret_sha256": secret_commitment,
        "truth_mapping_disclosed": False,
        "secret_values_disclosed": False,
        "observation_realization_reused": False,
        "blind_ids_reused": False,
        "datasets": datasets,
        "real_external_evidence": False,
        "trusted_registry_eligible": False,
        "production_eligible": False,
        "formal_v3_physics": "NOT_STARTED",
        "v3_physics_start_gate": (
            "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        ),
    }
    GENERATION_MANIFEST_PATH.write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    hashes = {
        str(item["dataset_blind_id"]): str(item["sha256"])
        for item in datasets
    }
    scan = scan_for_new_truth_associations(sorted(mapping), hashes)
    write_scan(scan)
    if scan["status"] != "PASS":
        raise ValueError("Preclassification contamination scan failed")
    return manifest


def main() -> int:
    manifest = generate_once()
    print(
        "TRUE_REBLINDING_GENERATION_STATUS = FROZEN_PRECLASSIFICATION; "
        f'DATASETS = {len(manifest["datasets"])}; GENERATION_ATTEMPT = 1'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
