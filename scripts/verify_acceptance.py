#!/usr/bin/env python3
"""Verify all generated CTEAS_UFOTRI acceptance artifacts."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
    "air_hto_concentration",
    "soil_water_storage",
    "soil_hto_inventory",
    "soil_hto_concentration",
    "soil_evaporation",
    "plant_transpiration",
    "root_water_uptake",
    "deep_drainage",
    "plant_tfwt_inventory",
    "plant_tfwt_concentration",
    "plant_obt_inventory",
    "soil_reemission_flux",
    "plant_reemission_flux",
    "total_reemission_flux",
    "mass_balance_error",
    "mass_balance_relative_error",
}
REQUIRED_FILES = {
    "results.csv",
    "atmosphere_grid.csv",
    "air_concentration.png",
    "centreline_air_concentration.png",
    "soil_hto.png",
    "plant_hto.png",
    "reemission.png",
    "mass_balance.png",
    "validation_report.md",
}
CASES = {
    "rural_stack_short_case": 288,
    "rural_stack_short_case_era5": 288,
    "rural_stack_advanced_modes": 144,
}


def verify_case(directory: Path, expected_steps: int) -> str:
    missing_files = REQUIRED_FILES - {path.name for path in directory.iterdir()}
    if missing_files:
        raise ValueError(f"{directory}: missing files {sorted(missing_files)}")
    frame = pd.read_csv(directory / "results.csv")
    if len(frame) != expected_steps:
        raise ValueError(f"{directory}: expected {expected_steps} rows, got {len(frame)}")
    missing_columns = REQUIRED_COLUMNS - set(frame.columns)
    if missing_columns:
        raise ValueError(f"{directory}: missing columns {sorted(missing_columns)}")
    numeric = frame[list(REQUIRED_COLUMNS)].select_dtypes(include=[np.number])
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError(f"{directory}: non-finite result")
    physical = numeric.drop(columns=["mass_balance_error"])
    if (physical < -1.0e-12).any().any():
        raise ValueError(f"{directory}: negative physical result")
    maximum_relative = float(frame["mass_balance_relative_error"].max())
    if maximum_relative > 1.0e-6:
        raise ValueError(
            f"{directory}: mass-balance relative error {maximum_relative:.6e}"
        )
    return (
        f"{directory.name}: steps={len(frame)}, "
        f"max_mass_relative={maximum_relative:.6e}, artifacts={len(REQUIRED_FILES)}"
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "outputs"
    try:
        summaries = [
            verify_case(root / case_name, expected_steps)
            for case_name, expected_steps in CASES.items()
        ]
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    for summary in summaries:
        print(f"PASS: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
