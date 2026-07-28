#!/usr/bin/env python3
"""Generate preregistered synthetic D3 chamber forcing for dry-run use."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "d3_prospective_experiment"
ASSUMPTIONS_PATH = (
    BENCHMARK
    / "preregistration"
    / "d3_prospective_experiment_assumptions.yaml"
)
DEFAULT_OUTPUT_ROOT = (
    ROOT / "validation" / "external_local" / "d3_prospective_experiment"
)
DEFAULT_SUMMARY_PATH = BENCHMARK / "results" / "forcing_quality_summary.yaml"
PROJECT_MARKER = "PROJECT_ASSUMPTION_NOT_LITERATURE_FACT"
FORCING_SOURCE = "SYNTHETIC_CONTROLLED_EXPERIMENT"
FORCING_COLUMNS = (
    "time_utc",
    "minutes_from_exposure_start",
    "phase",
    "air_hto_bq_ml_water",
    "temperature_c",
    "relative_humidity_percent",
    "mixing_velocity_m_s",
    "precipitation_mm_interval",
    "light_state",
    "forcing_source",
    "assumption_set",
    "quality_flag",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH
    )
    return parser.parse_args()


def assumption_value(mapping: dict[str, Any], key: str) -> float:
    item = mapping[key]
    if item.get("status") != PROJECT_MARKER:
        raise ValueError(f"{key} is not marked as a project assumption")
    value = item["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} is not a numeric project assumption")
    return float(value)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_assumptions(*, require_committed: bool = True) -> dict[str, Any]:
    assumptions = yaml.safe_load(ASSUMPTIONS_PATH.read_text(encoding="utf-8"))
    if (
        assumptions["assumption_set"] != "D3_PROSPECTIVE_ASSUMPTIONS_V1"
        or assumptions["status"]
        != "FROZEN_BEFORE_SYNTHETIC_PROSPECTIVE_EXECUTION"
    ):
        raise ValueError("D3 prospective assumptions are not frozen")
    boundary = assumptions["evidence_boundary"]
    if (
        boundary["evidence_class"]
        != "SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN"
        or boundary["real_external_evidence"]
        or boundary["empirical_validation_claim"]
        or boundary["trusted_registry_eligible"]
        or boundary["production_eligible"]
        or boundary["formal_v3_physics"] != "NOT_STARTED"
        or boundary["v3_physics_start_gate"]
        != "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    ):
        raise ValueError("D3 prospective evidence boundary changed")
    if require_committed:
        relative = ASSUMPTIONS_PATH.relative_to(ROOT).as_posix()
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
            raise ValueError("Assumptions differ from committed HEAD")
    return assumptions


def standardized_noise(
    rng: np.random.Generator, count: int, *, clip: float = 2.5
) -> np.ndarray:
    values = np.clip(rng.normal(size=count), -clip, clip)
    values -= float(values.mean())
    standard_deviation = float(values.std(ddof=0))
    if standard_deviation == 0:
        raise ValueError("Degenerate synthetic control noise")
    return values / standard_deviation


def bounded_control_series(
    rng: np.random.Generator,
    count: int,
    target: float,
    band: float,
) -> np.ndarray:
    values = standardized_noise(rng, count)
    values /= max(float(np.max(np.abs(values))), 1.0)
    result = target + 0.8 * band * values
    result += target - float(result.mean())
    if np.max(np.abs(result - target)) > band + 1.0e-12:
        raise ValueError("Synthetic chamber control exceeded its band")
    return result


def generate_forcing(
    assumptions: dict[str, Any],
    *,
    strict_zero_background: bool,
) -> list[dict[str, Any]]:
    exposure = assumptions["exposure_conditions"]
    interval_min = int(assumption_value(exposure, "forcing_interval_min"))
    exposure_h = assumption_value(exposure, "exposure_duration_h")
    followup_h = assumption_value(exposure, "post_exposure_followup_h")
    setpoint = assumption_value(
        exposure, "air_moisture_hto_setpoint_bq_ml_water"
    )
    setpoint_cv = assumption_value(exposure, "setpoint_variability_cv")
    temperature_target = assumption_value(exposure, "temperature_target_c")
    temperature_band = assumption_value(
        exposure, "temperature_control_band_c"
    )
    rh_target = assumption_value(
        exposure, "relative_humidity_target_percent"
    )
    rh_band = assumption_value(
        exposure, "relative_humidity_control_band_percent"
    )
    mixing_target = assumption_value(
        exposure, "mixing_velocity_target_m_s"
    )
    mixing_band = assumption_value(
        exposure, "mixing_velocity_control_band_m_s"
    )
    precipitation = assumption_value(
        exposure, "precipitation_mm_interval"
    )
    background_target_fraction = assumption_value(
        exposure, "post_exposure_background_target_fraction"
    )
    maximum_background_fraction = assumption_value(
        exposure, "maximum_acceptable_background_fraction"
    )
    light_hours = assumption_value(exposure, "light_hours_per_day")

    total_minutes = int(round((exposure_h + followup_h) * 60))
    minutes = np.arange(0, total_minutes + interval_min, interval_min, dtype=int)
    exposure_mask = minutes < int(round(exposure_h * 60))
    exposure_count = int(exposure_mask.sum())
    if exposure_count != int(round(exposure_h * 60 / interval_min)):
        raise ValueError("Exposure forcing interval count is incomplete")

    seed = int(
        assumption_value(assumptions["random_seeds"], "forcing_seed")
    )
    rng = np.random.default_rng(seed)
    exposure_noise = standardized_noise(rng, exposure_count)
    exposure_hto = setpoint * (1.0 + setpoint_cv * exposure_noise)
    exposure_hto += setpoint - float(exposure_hto.mean())
    if np.any(exposure_hto <= 0):
        raise ValueError("Synthetic exposure HTO must remain positive")

    post_count = len(minutes) - exposure_count
    if strict_zero_background:
        background = np.zeros(post_count, dtype=float)
    else:
        background_noise = standardized_noise(rng, post_count)
        background = setpoint * background_target_fraction * (
            1.0 + 0.10 * background_noise
        )
        background = np.clip(
            background,
            setpoint * 0.0005,
            setpoint * maximum_background_fraction,
        )
        if np.any(background <= 0):
            raise ValueError("Measured-background scenario cannot be silent zero")

    hto = np.concatenate([exposure_hto, background])
    temperature = bounded_control_series(
        rng, len(minutes), temperature_target, temperature_band
    )
    rh = bounded_control_series(rng, len(minutes), rh_target, rh_band)
    mixing = bounded_control_series(
        rng, len(minutes), mixing_target, mixing_band
    )
    start = datetime.fromisoformat(
        exposure["experiment_start_utc"].replace("Z", "+00:00")
    ).astimezone(timezone.utc)
    assumption_set = assumptions["assumption_set"]
    rows: list[dict[str, Any]] = []
    for index, minute in enumerate(minutes):
        current = start + timedelta(minutes=int(minute))
        phase = (
            "CONTROLLED_EXPOSURE"
            if bool(exposure_mask[index])
            else "POST_EXPOSURE_BACKGROUND"
        )
        hour_of_day = (int(minute) / 60.0) % 24.0
        rows.append(
            {
                "time_utc": current.isoformat().replace("+00:00", "Z"),
                "minutes_from_exposure_start": int(minute),
                "phase": phase,
                "air_hto_bq_ml_water": float(hto[index]),
                "temperature_c": float(temperature[index]),
                "relative_humidity_percent": float(rh[index]),
                "mixing_velocity_m_s": float(mixing[index]),
                "precipitation_mm_interval": precipitation,
                "light_state": "LIGHT" if hour_of_day < light_hours else "DARK",
                "forcing_source": FORCING_SOURCE,
                "assumption_set": assumption_set,
                "quality_flag": "SYNTHETIC_PROJECT_ASSUMPTION_OK",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FORCING_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def forcing_summary(
    assumptions: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    scenario_id: str,
    csv_path: Path,
) -> dict[str, Any]:
    exposure_rows = [
        row for row in rows if row["phase"] == "CONTROLLED_EXPOSURE"
    ]
    background_rows = [
        row for row in rows if row["phase"] == "POST_EXPOSURE_BACKGROUND"
    ]
    setpoint = assumption_value(
        assumptions["exposure_conditions"],
        "air_moisture_hto_setpoint_bq_ml_water",
    )
    exposed = np.asarray(
        [row["air_hto_bq_ml_water"] for row in exposure_rows], dtype=float
    )
    background = np.asarray(
        [row["air_hto_bq_ml_water"] for row in background_rows], dtype=float
    )

    def mean_and_range(field: str) -> dict[str, float]:
        values = np.asarray([row[field] for row in rows], dtype=float)
        return {
            "mean": float(values.mean()),
            "minimum": float(values.min()),
            "maximum": float(values.max()),
        }

    try:
        csv_path_label = csv_path.relative_to(ROOT).as_posix()
    except ValueError:
        csv_path_label = csv_path.as_posix()

    return {
        "scenario_id": scenario_id,
        "forcing_source": FORCING_SOURCE,
        "assumption_set": assumptions["assumption_set"],
        "evidence_class": "SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN",
        "real_external_evidence": False,
        "csv_path": csv_path_label,
        "csv_sha256": sha256(csv_path),
        "row_count": len(rows),
        "exposure_row_count": len(exposure_rows),
        "post_exposure_row_count": len(background_rows),
        "actual_exposure_mean": float(exposed.mean()),
        "actual_exposure_mean_relative_error": float(
            abs(exposed.mean() - setpoint) / setpoint
        ),
        "actual_exposure_cv": float(exposed.std(ddof=0) / exposed.mean()),
        "maximum_setpoint_deviation": float(
            np.max(np.abs(exposed - setpoint))
        ),
        "post_exposure_background_mean": float(background.mean()),
        "post_exposure_background_mean_fraction": float(
            background.mean() / setpoint
        ),
        "post_exposure_background_maximum_fraction": float(
            background.max() / setpoint
        ),
        "temperature_c": mean_and_range("temperature_c"),
        "relative_humidity_percent": mean_and_range(
            "relative_humidity_percent"
        ),
        "mixing_velocity_m_s": mean_and_range("mixing_velocity_m_s"),
    }


def generate_outputs(
    output_root: Path,
    summary_path: Path,
    *,
    require_committed_assumptions: bool = True,
) -> dict[str, Any]:
    assumptions = load_assumptions(
        require_committed=require_committed_assumptions
    )
    forcing_dir = output_root / "forcing"
    measured_path = forcing_dir / "d3_forcing_measured_background.csv"
    zero_path = forcing_dir / "d3_forcing_zero_background.csv"
    measured = generate_forcing(assumptions, strict_zero_background=False)
    strict_zero = generate_forcing(assumptions, strict_zero_background=True)
    write_csv(measured_path, measured)
    write_csv(zero_path, strict_zero)
    summary = {
        "summary_id": "D3_PROSPECTIVE_FORCING_QUALITY_V1",
        "status": "PASS_SYNTHETIC_CONTROLLED_FORCING",
        "project_assumption_status": PROJECT_MARKER,
        "scenarios": [
            forcing_summary(
                assumptions,
                measured,
                scenario_id="MEASURED_NONZERO_BACKGROUND",
                csv_path=measured_path,
            ),
            forcing_summary(
                assumptions,
                strict_zero,
                scenario_id="STRICT_ZERO_BACKGROUND_SENSITIVITY",
                csv_path=zero_path,
            ),
        ],
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        yaml.safe_dump(summary, sort_keys=False), encoding="utf-8"
    )
    return summary


def main() -> int:
    args = parse_args()
    summary = generate_outputs(args.output_root, args.summary_path)
    for scenario in summary["scenarios"]:
        print(
            f'{scenario["scenario_id"]}: '
            f'mean={scenario["actual_exposure_mean"]:.6f}, '
            f'cv={scenario["actual_exposure_cv"]:.6f}, '
            f'background_fraction='
            f'{scenario["post_exposure_background_mean_fraction"]:.6f}'
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
