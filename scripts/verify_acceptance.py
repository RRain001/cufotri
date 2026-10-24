#!/usr/bin/env python3
"""Verify saved artifacts or recompute the formal minimal acceptance cases."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration, load_yaml
from cteas_ufotri.meteorology.era5_reader import prepare_hourly_forcing, read_era5
from cteas_ufotri.outputs.diagnostics import (
    create_validation_figures,
    write_atmosphere_spatial_outputs,
    write_validation_report,
)
from cteas_ufotri.outputs.writer import write_results

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from validation.adapters.csv_adapter import sha256
from validation.external_input_requirements import (
    InputStatus,
    check_dataset,
    resolve_dataset_file,
)


REQUIRED_COLUMNS = {
    "air_hto_concentration",
    "soil_water_storage",
    "soil_hto_inventory",
    "plant_tfwt_inventory",
    "plant_obt_inventory",
    "total_reemission_flux",
    "surface_box_absolute_residual_bq_m2",
    "surface_box_relative_residual",
    "raw_wind_speed_m_s",
    "effective_wind_speed_m_s",
    "calm_wind_applied",
    "plume_source_before_depletion_bq_s",
    "plume_source_after_depletion_bq_s",
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
LEGACY_CASES = {
    "rural_stack_short_case": 288,
    "rural_stack_short_case_era5": 288,
    "rural_stack_advanced_modes": 144,
}


def git_value(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


def verify_case(directory: Path, expected_steps: int, *, formal: bool) -> str:
    missing_files = REQUIRED_FILES - {path.name for path in directory.iterdir()}
    if missing_files:
        raise ValueError(f"{directory}: missing files {sorted(missing_files)}")
    frame = pd.read_csv(directory / "results.csv")
    if len(frame) != expected_steps:
        raise ValueError(f"{directory}: expected {expected_steps} rows, got {len(frame)}")
    required = REQUIRED_COLUMNS if formal else {
        "air_hto_concentration",
        "soil_hto_inventory",
        "plant_tfwt_inventory",
        "plant_obt_inventory",
        "total_reemission_flux",
        "mass_balance_error",
        "mass_balance_relative_error",
    }
    missing_columns = required - set(frame.columns)
    if missing_columns:
        raise ValueError(f"{directory}: missing columns {sorted(missing_columns)}")
    numeric = frame[list(required)].select_dtypes(include=[np.number])
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError(f"{directory}: non-finite result")
    residual_name = (
        "surface_box_relative_residual" if formal else "mass_balance_relative_error"
    )
    maximum_relative = float(frame[residual_name].max())
    if maximum_relative > 1.0e-6:
        raise ValueError(f"{directory}: surface-box residual {maximum_relative:.6e}")
    return (
        f"{directory.name}: steps={len(frame)}, "
        f"max_surface_box_relative={maximum_relative:.6e}, "
        f"artifacts={len(REQUIRED_FILES)}"
    )


def write_case(config: dict, output: Path, forcing: pd.DataFrame | None, label: str) -> None:
    frame = run_short_case(config, forcing)
    write_results(frame, output)
    create_validation_figures(frame, output)
    write_atmosphere_spatial_outputs(config, output)
    write_validation_report(frame, output, config["name"], label, config)


def dependency_versions() -> dict[str, str]:
    versions = {}
    for package in ("numpy", "pandas", "scipy", "matplotlib", "PyYAML"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def recompute(root: Path, era5_path: Path) -> list[str]:
    started = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory(prefix="cteas_ufotri_acceptance_") as tmp:
        output_root = Path(tmp)
        basic = load_configuration(
            root / "configs/default_parameters.yaml", root / "configs/test_case.yaml"
        )
        advanced = load_configuration(
            root / "configs/default_parameters.yaml",
            root / "configs/advanced_test_case.yaml",
        )
        mapping = load_yaml(root / "configs/era5_mapping.yaml")
        raw = read_era5(era5_path, mapping)
        forcing = prepare_hourly_forcing(
            raw,
            basic["physics"]["fallback_shortwave_absorptivity"],
            basic["physics"]["fallback_net_longwave_loss_w_m2"],
            accumulation_semantics=mapping.get("accumulation_semantics", "interval"),
        )
        cases: list[tuple[str, dict, pd.DataFrame | None, str]] = [
            ("synthetic_basic_48h", basic, None, "deterministic synthetic forcing"),
            ("era5_basic_48h", basic, forcing, f"ERA5 {era5_path.name}"),
            ("advanced_reemission_24h", advanced, None, "advanced synthetic forcing"),
        ]
        runoff = load_configuration(
            root / "configs/default_parameters.yaml", root / "configs/test_case.yaml"
        )
        runoff["name"] = "runoff_rain_hto_1h"
        runoff["duration_hours"] = 1
        runoff["soil"]["runoff_enabled"] = True
        runoff["soil"]["infiltration_capacity_m_s"] = 1.0e-5
        runoff["soil"]["rain_hto_concentration_bq_m3"] = 1000.0
        runoff["synthetic_forcing"]["rain_start_hour"] = 0.0
        runoff["synthetic_forcing"]["rain_end_hour"] = 1.0
        runoff["synthetic_forcing"]["rain_rate_m_s"] = 1.0e-4
        calm = load_configuration(
            root / "configs/default_parameters.yaml", root / "configs/test_case.yaml"
        )
        calm["name"] = "calm_wind_1h"
        calm["duration_hours"] = 1
        calm["synthetic_forcing"]["mean_wind_m_s"] = 0.0
        calm["synthetic_forcing"]["wind_amplitude_m_s"] = 0.0
        cases.extend([
            ("runoff_rain_hto_1h", runoff, None, "runoff HTO boundary forcing"),
            ("calm_wind_1h", calm, None, "calm-wind boundary forcing"),
        ])
        summaries = []
        for name, config, case_forcing, label in cases:
            directory = output_root / name
            write_case(config, directory, case_forcing, label)
            expected = int(config["duration_hours"] * 3600 / config["time_step_seconds"])
            summaries.append(verify_case(directory, expected, formal=True))
        finished = datetime.now(timezone.utc)
        provenance = {
            "git_head": git_value(root, "rev-parse", "HEAD"),
            "git_worktree_status": git_value(root, "status", "--short"),
            "config_sha256": {
                path.name: sha256(path)
                for path in (
                    root / "configs/default_parameters.yaml",
                    root / "configs/test_case.yaml",
                    root / "configs/advanced_test_case.yaml",
                    root / "configs/era5_mapping.yaml",
                )
            },
            "inputs": {
                "era5_path": str(era5_path.resolve()),
                "era5_sha256": sha256(era5_path),
            },
            "python": platform.python_version(),
            "dependencies": dependency_versions(),
            "model_modes": {
                "chemical": "HTO-only",
                "soil": basic["soil"]["layer_model"],
                "calm_wind": basic["atmosphere"]["calm_wind"]["mode"],
                "depletion": basic["atmosphere"]["depletion"],
                "feedback_delay_s": basic["coupling"]["reemission_feedback_delay_s"],
                "lai_shading": basic["evapotranspiration"]["lai_shading_mode"],
            },
            "internal_time_step_s": basic["time_step_seconds"],
            "started_utc": started.isoformat(),
            "finished_utc": finished.isoformat(),
            "temporary_output_directory": str(output_root),
        }
        (output_root / "provenance.json").write_text(
            json.dumps(provenance, indent=2), encoding="utf-8"
        )
        if not (output_root / "provenance.json").is_file():
            raise ValueError("Provenance was not written")
        summaries.append(
            "provenance: git/config/input/runtime metadata recorded in temporary output"
        )
        return summaries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recompute", action="store_true")
    parser.add_argument(
        "--era5",
        default=None,
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.recompute:
        if args.era5 is None:
            input_check = check_dataset(root, "ERA5_ACCEPTANCE")
            era5_path = resolve_dataset_file(root, "ERA5_ACCEPTANCE")
        else:
            era5_path = Path(args.era5)
            if not era5_path.is_absolute():
                era5_path = root / era5_path
            input_check = None
            if not era5_path.is_file():
                print("STATUS = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT")
                print("DATASET = ERA5_ACCEPTANCE")
                print(f"MISSING_FILES = [{str(era5_path)!r}]")
                return 2
        if input_check is not None and input_check.status is not InputStatus.AVAILABLE:
            print("STATUS = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT")
            print("DATASET = ERA5_ACCEPTANCE")
            print(f"MISSING_FILES = {list(input_check.missing_files)!r}")
            return 2
    try:
        if args.recompute:
            summaries = recompute(root, era5_path)
        else:
            output_root = root / "outputs"
            summaries = [
                verify_case(output_root / name, steps, formal=False)
                for name, steps in LEGACY_CASES.items()
            ]
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    for summary in summaries:
        print(f"PASS: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
