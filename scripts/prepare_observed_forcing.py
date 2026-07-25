#!/usr/bin/env python3
"""Combine consecutive ERA5 CSV downloads without modifying raw inputs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_observed_forcing(
    inputs: list[Path],
    output: Path,
    manifest_output: Path,
    expected_hours: int,
) -> dict:
    if not inputs:
        raise ValueError("At least one input CSV is required")
    if expected_hours <= 0:
        raise ValueError("expected_hours must be positive")

    frames: list[pd.DataFrame] = []
    columns: list[str] | None = None
    source_records: list[dict[str, object]] = []
    for path in inputs:
        frame = pd.read_csv(path)
        if "valid_time" not in frame.columns:
            raise ValueError(f"Missing valid_time column: {path}")
        if columns is None:
            columns = list(frame.columns)
        elif list(frame.columns) != columns:
            raise ValueError(f"Column order differs from the first input: {path}")
        frames.append(frame)
        source_records.append(
            {
                "path": str(path),
                "rows": len(frame),
                "sha256": sha256(path),
            }
        )

    combined = pd.concat(frames, ignore_index=True)
    times = pd.to_datetime(combined["valid_time"], utc=True, errors="raise")
    if times.duplicated().any():
        raise ValueError("Combined forcing contains duplicate timestamps")
    if not times.is_monotonic_increasing:
        raise ValueError("Combined forcing timestamps are not increasing")
    if len(combined) != expected_hours:
        raise ValueError(
            f"Combined forcing has {len(combined)} rows; {expected_hours} required"
        )
    expected_grid = pd.date_range(
        times.iloc[0],
        periods=expected_hours,
        freq="h",
        tz="UTC",
    )
    if not times.reset_index(drop=True).equals(pd.Series(expected_grid)):
        raise ValueError("Combined forcing is not a complete consecutive hourly grid")
    for coordinate in ("latitude", "longitude"):
        if coordinate in combined and combined[coordinate].nunique(dropna=False) != 1:
            raise ValueError(f"Combined forcing spans multiple {coordinate} values")

    combined["forcing_status"] = "observed"
    output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output, index=False)

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "output": str(output),
        "output_sha256": sha256(output),
        "expected_hours": expected_hours,
        "actual_hours": len(combined),
        "start_utc": times.iloc[0].isoformat(),
        "end_utc": times.iloc[-1].isoformat(),
        "time_zone": "UTC",
        "forcing_status": {"observed": len(combined)},
        "missing_hours": 0,
        "sources": source_records,
        "raw_inputs_modified": False,
    }
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--expected-hours", type=int, required=True)
    arguments = parser.parse_args()
    result = prepare_observed_forcing(
        arguments.input,
        arguments.output,
        arguments.manifest_output,
        arguments.expected_hours,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    print("PREPARE_OBSERVED_FORCING_STATUS = PASS")


if __name__ == "__main__":
    main()
