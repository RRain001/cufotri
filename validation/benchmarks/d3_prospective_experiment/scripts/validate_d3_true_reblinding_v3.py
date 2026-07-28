#!/usr/bin/env python3
"""Validate the D3 V3 preclassification snapshot and secret boundary."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from d3_true_reblinding_v3_common import (  # noqa: E402
    PRIVATE_ROOT,
    ROOT,
    SECRET_COMMITMENT_PATH,
    SECRET_PATH,
    TRUTH_KEY_PATH,
    load_generation_manifest,
    load_protocol,
    load_scan,
    scan_for_new_truth_associations,
    sha256,
    validate_dataset_hashes,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--classifier-worktree",
        action="store_true",
        help="Require the private V3 secret directory to be absent.",
    )
    parser.add_argument(
        "--require-tracked",
        action="store_true",
        help="Require the generated preclassification files to be tracked.",
    )
    return parser.parse_args()


def is_tracked(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    return (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )


def is_ignored(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    return (
        subprocess.run(
            ["git", "check-ignore", "--quiet", relative],
            cwd=ROOT,
            check=False,
        ).returncode
        == 0
    )


def validate_private_boundary(*, classifier_worktree: bool) -> None:
    if classifier_worktree:
        files = (
            [item for item in PRIVATE_ROOT.rglob("*") if item.is_file()]
            if PRIVATE_ROOT.exists()
            else []
        )
        if files:
            raise ValueError(
                "Classifier worktree contains the V3 private secret boundary"
            )
        return
    for path in (SECRET_PATH, TRUTH_KEY_PATH):
        if not path.is_file():
            raise FileNotFoundError(f"Missing private V3 file: {path.name}")
        if is_tracked(path) or not is_ignored(path):
            raise ValueError(f"Private V3 file escaped ignore boundary: {path}")
    commitment = SECRET_COMMITMENT_PATH.read_text(
        encoding="utf-8"
    ).strip()
    if sha256(SECRET_PATH) != commitment:
        raise ValueError("Private secret does not match tracked commitment")


def validate_preclassification(
    *,
    classifier_worktree: bool,
    require_tracked: bool,
) -> None:
    protocol = load_protocol(require_clean=require_tracked)
    manifest = load_generation_manifest(require_clean=require_tracked)
    hashes = validate_dataset_hashes(
        protocol, manifest, require_clean=require_tracked
    )
    stored_scan = load_scan()
    recomputed = scan_for_new_truth_associations(sorted(hashes), hashes)
    if recomputed != stored_scan or recomputed["status"] != "PASS":
        raise ValueError("Preclassification contamination scan is stale")
    validate_private_boundary(classifier_worktree=classifier_worktree)


def main() -> int:
    args = parse_args()
    validate_preclassification(
        classifier_worktree=args.classifier_worktree,
        require_tracked=args.require_tracked,
    )
    print(
        "TRUE_REBLINDING_PRECLASSIFICATION_STATUS = PASS; "
        f'PRIVATE_SECRET_PRESENT = {not args.classifier_worktree}'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
