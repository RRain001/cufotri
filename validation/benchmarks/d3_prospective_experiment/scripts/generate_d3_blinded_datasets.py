#!/usr/bin/env python3
"""Generate blinded sample-level synthetic D3 datasets without exposing truth."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from d3_prospective_core import (  # noqa: E402
    BENCHMARK,
    CLASSIFICATION_PROTOCOL_PATH,
    COMPLETE_TIMES,
    LOCAL_ROOT,
    SYNTHETIC_STATUS,
    TRACKED_DATA_ROOT,
    frozen_prediction_table,
    load_classification_protocol,
    mean_one_lognormal,
    prediction_vectors,
    sha256,
)
from generate_d3_prospective_forcing import (  # noqa: E402
    ASSUMPTIONS_PATH,
    PROJECT_MARKER,
    assumption_value,
    load_assumptions,
)


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_TRUTH_PLAN = LOCAL_ROOT / "truth" / "truth_plan.yaml"
DEFAULT_TRUTH_KEY = LOCAL_ROOT / "truth" / "truth_key.yaml"
TRUTH_KEY_HASH_PATH = TRACKED_DATA_ROOT / "truth_key_sha256"
GENERATION_MANIFEST_PATH = TRACKED_DATA_ROOT / "generation_manifest.yaml"
PREDICTION_QA_PATH = BENCHMARK / "results" / "frozen_truth_prediction_qa.yaml"
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
TRUTH_KINDS = {
    "H2_SB1_FROZEN",
    "H3_SB1_FROZEN",
    "SYNTHETIC_OUT_OF_MODEL_CHALLENGE",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--truth-plan", type=Path, default=DEFAULT_TRUTH_PLAN)
    parser.add_argument("--truth-key", type=Path, default=DEFAULT_TRUTH_KEY)
    parser.add_argument(
        "--output-root", type=Path, default=TRACKED_DATA_ROOT
    )
    return parser.parse_args()


def assert_local_truth_boundary(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if tracked.returncode == 0:
        raise ValueError(f"Truth file is tracked by Git: {relative}")
    ignored = subprocess.run(
        ["git", "check-ignore", "--quiet", relative],
        cwd=ROOT,
        check=False,
    )
    if ignored.returncode != 0:
        raise ValueError(f"Truth file is not covered by Git ignore: {relative}")


def load_truth_plan(path: Path) -> dict[str, Any]:
    assert_local_truth_boundary(path)
    plan = yaml.safe_load(path.read_text(encoding="utf-8"))
    if (
        plan["plan_id"] != "D3_LOCAL_BLIND_TRUTH_PLAN_V1"
        or plan["tracked"] is not False
    ):
        raise ValueError("Local truth plan boundary changed")
    datasets = plan["datasets"]
    blind_ids = [str(item["dataset_blind_id"]) for item in datasets]
    truth_kinds = [str(item["truth_kind"]) for item in datasets]
    if (
        sorted(blind_ids) != ["A", "B", "C"]
        or len(set(blind_ids)) != 3
        or set(truth_kinds) != TRUTH_KINDS
    ):
        raise ValueError("Truth plan must contain three unique blinded datasets")
    return plan


def truth_vectors(
    protocol: dict[str, Any],
    prediction_table: Any,
) -> dict[str, np.ndarray]:
    times, h2, h3 = prediction_vectors(prediction_table)
    challenge = np.sqrt(h2 * h3)
    challenge_time = float(
        protocol["challenge_contract"]["systematic_deviation_time_h"]["value"]
    )
    challenge_factor = float(
        protocol["challenge_contract"]["systematic_deviation_factor"]["value"]
    )
    indices = np.where(np.isclose(times, challenge_time))[0]
    if len(indices) != 1:
        raise ValueError("Challenge deviation time is not in the sampling grid")
    challenge[int(indices[0])] *= challenge_factor
    return {
        "H2_SB1_FROZEN": h2,
        "H3_SB1_FROZEN": h3,
        "SYNTHETIC_OUT_OF_MODEL_CHALLENGE": challenge,
    }


def seed_for_truth(assumptions: dict[str, Any], truth_kind: str) -> int:
    key = {
        "H2_SB1_FROZEN": "h2_truth_seed",
        "H3_SB1_FROZEN": "h3_truth_seed",
        "SYNTHETIC_OUT_OF_MODEL_CHALLENGE": "challenge_seed",
    }[truth_kind]
    return int(assumption_value(assumptions["random_seeds"], key))


def sample_rows(
    assumptions: dict[str, Any],
    *,
    blind_id: str,
    truth: np.ndarray,
    seed: int,
    total_cv: float,
) -> list[dict[str, Any]]:
    measurement = assumptions["measurement_assumptions"]
    replicates = int(
        assumption_value(
            assumptions["biological_replicates"], "default_per_time"
        )
    )
    detection_limit = assumption_value(
        measurement, "assumed_detection_limit_bq_l"
    )
    analytical_cv = assumption_value(measurement, "analytical_cv")
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
        observation_multiplier = mean_one_lognormal(
            rng, total_cv, replicates
        )
        fresh_multiplier = mean_one_lognormal(rng, fresh_cv, replicates)
        dry_multiplier = mean_one_lognormal(
            rng, dry_fraction_cv, replicates
        )
        for replicate_index in range(replicates):
            value = float(expected * observation_multiplier[replicate_index])
            fresh_mass = round(
                float(fresh_mean * fresh_multiplier[replicate_index]), 2
            )
            dry_fraction = float(
                np.clip(
                    dry_fraction_mean * dry_multiplier[replicate_index],
                    0.05,
                    0.60,
                )
            )
            dry_mass = round(fresh_mass * dry_fraction, 2)
            water = round(fresh_mass - dry_mass, 2)
            sample_time = start + timedelta(
                hours=float(exposure_h + float(hour))
            )
            rows.append(
                {
                    "experiment_id": "D3-PROSPECTIVE-DRY-RUN-V2",
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
                    "tissue_water_ml": water,
                    "tfwt_bq_l_water": value,
                    "analytical_uncertainty": value * analytical_cv,
                    "detection_limit_bq_l": detection_limit,
                    "below_detection_limit": value < detection_limit,
                    "quality_flag": "OK",
                    "assumption_set": assumptions["assumption_set"],
                    "synthetic_status": SYNTHETIC_STATUS,
                }
            )
    return rows


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=DATASET_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def missing_replicate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in rows
        if not (
            float(row["hours_after_exposure"]) == 48.0
            and str(row["replicate_id"]).endswith("R05")
        )
    ]


def outlier_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = [dict(row) for row in rows]
    target = next(
        row
        for row in result
        if float(row["hours_after_exposure"]) == 48.0
        and str(row["replicate_id"]).endswith("R01")
    )
    target["tfwt_bq_l_water"] = float(target["tfwt_bq_l_water"]) * 10.0
    target["analytical_uncertainty"] = (
        float(target["analytical_uncertainty"]) * 10.0
    )
    target["quality_flag"] = "SYNTHETIC_OUTLIER_EXCLUDE"
    return result


def detection_limit_rows(
    rows: list[dict[str, Any]], detection_limit: float
) -> list[dict[str, Any]]:
    result = [dict(row) for row in rows]
    target = next(
        row
        for row in result
        if float(row["hours_after_exposure"]) == 72.0
        and str(row["replicate_id"]).endswith("R01")
    )
    target["tfwt_bq_l_water"] = 0.8 * detection_limit
    target["analytical_uncertainty"] = 0.08 * float(
        target["tfwt_bq_l_water"]
    )
    target["below_detection_limit"] = True
    target["quality_flag"] = "OK"
    return result


def manifest_entry(path: Path, blind_id: str) -> dict[str, Any]:
    with path.open(encoding="utf-8", newline="") as stream:
        row_count = sum(1 for _ in csv.DictReader(stream))
    return {
        "dataset_blind_id": blind_id,
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
        "row_count": row_count,
        "truth_disclosed": False,
    }


def generate(
    truth_plan_path: Path,
    truth_key_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    assumptions = load_assumptions(require_committed=True)
    protocol = load_classification_protocol()
    plan = load_truth_plan(truth_plan_path)
    assert_local_truth_boundary(truth_key_path)
    prediction_table, prediction_qa = frozen_prediction_table()
    vectors = truth_vectors(protocol, prediction_table)
    baseline_cv = assumption_value(
        assumptions["measurement_assumptions"], "combined_total_cv_target"
    )
    cv20 = 0.20
    detection_limit = assumption_value(
        assumptions["measurement_assumptions"],
        "assumed_detection_limit_bq_l",
    )
    dataset_entries: list[dict[str, Any]] = []
    variant_entries: list[dict[str, Any]] = []
    truth_entries: list[dict[str, Any]] = []
    for item in plan["datasets"]:
        blind_id = str(item["dataset_blind_id"])
        truth_kind = str(item["truth_kind"])
        seed = seed_for_truth(assumptions, truth_kind)
        baseline = sample_rows(
            assumptions,
            blind_id=blind_id,
            truth=vectors[truth_kind],
            seed=seed,
            total_cv=baseline_cv,
        )
        dataset_path = output_root / f"dataset_{blind_id}.csv"
        write_rows(dataset_path, baseline)
        dataset_entries.append(manifest_entry(dataset_path, blind_id))

        variants = {
            "cv20": sample_rows(
                assumptions,
                blind_id=blind_id,
                truth=vectors[truth_kind],
                seed=seed + 20,
                total_cv=cv20,
            ),
            "one_missing_replicate": missing_replicate_rows(baseline),
            "one_outlier": outlier_rows(baseline),
            "detection_limit": detection_limit_rows(
                baseline, detection_limit
            ),
        }
        for variant_id, rows in variants.items():
            path = (
                LOCAL_ROOT
                / "challenges"
                / f"{variant_id}_dataset_{blind_id}.csv"
            )
            write_rows(path, rows)
            entry = manifest_entry(path, blind_id)
            entry["variant_id"] = variant_id
            variant_entries.append(entry)

        truth_entries.append(
            {
                "dataset_blind_id": blind_id,
                "truth_kind": truth_kind,
                "seed": seed,
                "expected_result": item["expected_result"],
            }
        )

    truth_key = {
        "truth_key_id": "D3_LOCAL_TRUTH_KEY_V1",
        "tracked": False,
        "synthetic_status": SYNTHETIC_STATUS,
        "third_physical_model_claim": False,
        "datasets": truth_entries,
    }
    truth_key_path.parent.mkdir(parents=True, exist_ok=True)
    truth_key_path.write_text(
        yaml.safe_dump(truth_key, sort_keys=False), encoding="utf-8"
    )
    truth_hash = sha256(truth_key_path)
    TRUTH_KEY_HASH_PATH.write_text(f"{truth_hash}\n", encoding="utf-8")

    prediction_qa_rows = prediction_qa.to_dict(orient="records")
    PREDICTION_QA_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREDICTION_QA_PATH.write_text(
        yaml.safe_dump(
            {
                "status": "PASS_FROZEN_PREDICTION_QA",
                "parameter_refit_count": 0,
                "latent_state_used_for_classification": False,
                "rows": prediction_qa_rows,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    manifest = {
        "manifest_id": "D3_BLINDED_SYNTHETIC_GENERATION_V2",
        "evidence_class": "SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN",
        "synthetic_status": SYNTHETIC_STATUS,
        "licence": "SYNTHETIC_INTERNAL_TEST_DATA",
        "real_external_evidence": False,
        "empirical_validation_claim": False,
        "trusted_registry_eligible": False,
        "production_eligible": False,
        "formal_v3_physics": "NOT_STARTED",
        "v3_physics_start_gate": (
            "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        ),
        "assumption_set": assumptions["assumption_set"],
        "assumptions_sha256": sha256(ASSUMPTIONS_PATH),
        "classification_protocol_sha256": sha256(
            CLASSIFICATION_PROTOCOL_PATH
        ),
        "generator_sha256": sha256(Path(__file__)),
        "truth_key_sha256": truth_hash,
        "truth_mapping_disclosed": False,
        "datasets": dataset_entries,
        "local_untracked_variants": variant_entries,
        "prediction_qa_path": PREDICTION_QA_PATH.relative_to(ROOT).as_posix(),
    }
    GENERATION_MANIFEST_PATH.write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    return manifest


def main() -> int:
    args = parse_args()
    manifest = generate(args.truth_plan, args.truth_key, args.output_root)
    print(
        "BLINDED_DATASETS_GENERATED = "
        f'{len(manifest["datasets"])}; '
        f'TRUTH_MAPPING_DISCLOSED = {manifest["truth_mapping_disclosed"]}'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
