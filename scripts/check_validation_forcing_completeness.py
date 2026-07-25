from __future__ import annotations

import argparse
from datetime import timedelta
import json
from pathlib import Path

import pandas as pd


ALLOWED_STATUS = {"observed", "interpolated", "repeated", "extended"}


def check_forcing(
    path: Path,
    expected_hours: int,
    time_column: str | None = None,
    status_column: str | None = None,
    default_status: str = "observed",
) -> dict:
    if expected_hours <= 0:
        raise ValueError("expected_hours must be positive")
    if default_status not in ALLOWED_STATUS:
        raise ValueError("Unsupported default forcing status")
    frame = pd.read_csv(path)
    selected_time = time_column or (
        "time" if "time" in frame.columns else "valid_time"
    )
    if selected_time not in frame.columns:
        raise ValueError("Forcing time column is missing")
    times = pd.to_datetime(frame[selected_time], utc=True, errors="raise")
    if times.duplicated().any():
        raise ValueError("Forcing contains duplicate timestamps")
    if not times.is_monotonic_increasing:
        raise ValueError("Forcing timestamps are not increasing")
    if status_column:
        if status_column not in frame.columns:
            raise ValueError("Requested forcing status column is missing")
        statuses = frame[status_column].astype(str).str.lower()
    else:
        statuses = pd.Series([default_status] * len(frame), index=frame.index)
    unknown = sorted(set(statuses) - ALLOWED_STATUS)
    if unknown:
        raise ValueError(f"Unknown forcing statuses: {unknown}")
    start = times.iloc[0]
    expected_grid = pd.date_range(start, periods=expected_hours, freq="h", tz="UTC")
    indexed_status = pd.Series(statuses.to_numpy(), index=times)
    aligned = indexed_status.reindex(expected_grid)
    missing_count = int(aligned.isna().sum())
    status_counts = {
        status: int((aligned == status).sum()) for status in sorted(ALLOWED_STATUS)
    }
    observed_count = status_counts["observed"]
    complete_grid = missing_count == 0
    all_observed = complete_grid and observed_count == expected_hours
    status = "PASS_FULLY_OBSERVED" if all_observed else "BLOCKED_EXTERNAL_DATA"
    return {
        "status": status,
        "input": str(path),
        "time_column": selected_time,
        "status_column": status_column or f"implicit:{default_status}",
        "expected_start_utc": start.isoformat(),
        "expected_end_utc": (
            start + timedelta(hours=expected_hours - 1)
        ).isoformat(),
        "expected_hours": expected_hours,
        "input_rows": len(frame),
        "missing_grid_hours": missing_count,
        "status_counts": status_counts,
        "complete_hourly_grid": complete_grid,
        "fully_observed": all_observed,
        "rule": (
            "interpolated, repeated, and extended rows are never counted as observed"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected-hours", type=int, required=True)
    parser.add_argument("--time-column")
    parser.add_argument("--status-column")
    parser.add_argument(
        "--default-status",
        choices=sorted(ALLOWED_STATUS),
        default="observed",
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    result = check_forcing(
        arguments.input,
        arguments.expected_hours,
        arguments.time_column,
        arguments.status_column,
        arguments.default_status,
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"FORCING_COMPLETENESS_STATUS = {result['status']}")


if __name__ == "__main__":
    main()
