#!/usr/bin/env python3
"""Fail-closed intake checker for a local IAEA EMRAS soybean package."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import yaml


REQUIRED_MANIFEST_FIELDS = {
    "dataset_id",
    "licence_use_permitted",
    "redistribution_permitted",
    "meteorology_file",
    "air_hto_file",
    "plant_observation_file",
    "mixing_ventilation_file",
    "uncertainty_file",
    "detection_limit_file",
    "checksums_sha256",
}


def _load_mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def inspect_local_package(case_path: Path, local_root: Path) -> dict[str, Any]:
    case = _load_mapping(case_path)
    if case.get("status") != "DRAFT_NOT_PREREGISTERED":
        raise ValueError("Soybean template status must remain DRAFT_NOT_PREREGISTERED")
    manifest_path = local_root / "soybean_emras" / "manifest.yaml"
    if not manifest_path.is_file():
        return {
            "status": "BLOCKED_EXTERNAL_DATA",
            "missing": ["local soybean_emras/manifest.yaml"],
            "calibration_permitted": False,
        }
    manifest = _load_mapping(manifest_path)
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    if manifest.get("licence_use_permitted") is not True:
        missing.append("documented licence_use_permitted=true")
    checksums = manifest.get("checksums_sha256", {})
    if not isinstance(checksums, dict):
        missing.append("checksums_sha256 mapping")
        checksums = {}
    for field in (
        "meteorology_file",
        "air_hto_file",
        "plant_observation_file",
        "mixing_ventilation_file",
        "uncertainty_file",
        "detection_limit_file",
    ):
        relative = manifest.get(field)
        if not isinstance(relative, str) or not (manifest_path.parent / relative).is_file():
            missing.append(field)
        elif relative not in checksums:
            missing.append(f"checksum for {relative}")
    if missing:
        return {
            "status": "BLOCKED_EXTERNAL_DATA",
            "missing": sorted(set(missing)),
            "calibration_permitted": False,
        }
    return {
        "status": "READY_FOR_PREREGISTRATION",
        "missing": [],
        "calibration_permitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        type=Path,
        default=Path("validation/cases/soybean_emras_template.yaml"),
    )
    parser.add_argument(
        "--local-root",
        type=Path,
        default=Path("validation/external_local"),
    )
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    try:
        result = inspect_local_package(
            arguments.case.resolve(),
            arguments.local_root.resolve(),
        )
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        print(f"SOYBEAN_ADAPTER_STATUS = FAIL_CLOSED; reason={exc}", file=sys.stderr)
        return 1
    print(f"SOYBEAN_ADAPTER_STATUS = {result['status']}")
    print(f"CALIBRATION_PERMITTED = {str(result['calibration_permitted']).upper()}")
    if result["missing"]:
        print("MISSING_INPUTS = " + ", ".join(result["missing"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
