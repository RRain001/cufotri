#!/usr/bin/env python3
"""Validate and download ERA5 hourly time series for one geographic point."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

try:
    from .era5_catalogue import (
        DATASET,
        available_variables,
        date_limits,
        fetch_catalogue,
    )
except ImportError:  # Direct execution: python era5/download_era5_timeseries.py
    from era5_catalogue import (
        DATASET,
        available_variables,
        date_limits,
        fetch_catalogue,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KEY_FILE = PROJECT_ROOT / "era5_key.txt"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "era5"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--longitude", type=float, required=True, help="Longitude in [-180, 179.9]")
    parser.add_argument("--latitude", type=float, required=True, help="Latitude in [-90, 90]")
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--all-dates",
        action="store_true",
        help="Use the complete date range currently exposed by the live catalogue",
    )
    date_group.add_argument("--start-date", help="YYYY-MM-DD; requires --end-date")
    parser.add_argument("--end-date", help="YYYY-MM-DD; requires --start-date")
    variable_group = parser.add_mutually_exclusive_group(required=True)
    variable_group.add_argument(
        "--variable",
        action="append",
        help="Variable name; repeat this option or use comma-separated names",
    )
    variable_group.add_argument(
        "--all-variables",
        action="store_true",
        help="Download every variable currently exposed by the live catalogue",
    )
    parser.add_argument("--format", choices=("netcdf", "csv"), default="netcdf")
    parser.add_argument(
        "--chunk-years",
        type=int,
        default=10,
        help="Maximum calendar years per request (default: 10)",
    )
    parser.add_argument("--key-file", type=Path, default=DEFAULT_KEY_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--execute", action="store_true", help="Submit requests; otherwise only preview")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output file")
    return parser.parse_args()


def parse_key_file(path: Path) -> tuple[str, str]:
    if not path.is_file():
        raise ValueError(f"CDS key file not found: {path}")
    config: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition(":")
        if separator and name.strip().lower() in {"url", "key"}:
            config[name.strip().lower()] = value.strip()
    if not config.get("url") or not config.get("key"):
        raise ValueError(f"{path} must contain both 'url:' and 'key:' lines")
    return config["url"], config["key"]


def load_credentials(path: Path) -> tuple[str, str]:
    """Load CDS credentials from environment or an ignored local file."""
    environment_url = os.environ.get("CDSAPI_URL")
    environment_key = os.environ.get("CDSAPI_KEY")
    if environment_url or environment_key:
        if not environment_url or not environment_key:
            raise ValueError("CDSAPI_URL and CDSAPI_KEY must be set together")
        return environment_url, environment_key
    return parse_key_file(path)


def parse_date(value: str, option: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{option} must use YYYY-MM-DD: {value}") from exc


def flatten_variables(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        for name in value.split(","):
            name = name.strip()
            if name and name not in result:
                result.append(name)
    return result


def validate(
    args: argparse.Namespace,
    form: list[dict],
) -> tuple[list[str], dict[str, list[str]], date, date]:
    if not -180 <= args.longitude <= 179.9:
        raise ValueError("--longitude must be between -180 and 179.9")
    if not -90 <= args.latitude <= 90:
        raise ValueError("--latitude must be between -90 and 90")
    if args.chunk_years < 1:
        raise ValueError("--chunk-years must be at least 1")

    minimum_text, maximum_text = date_limits(form)
    minimum, maximum = date.fromisoformat(minimum_text), date.fromisoformat(maximum_text)
    if args.all_dates:
        if args.end_date:
            raise ValueError("--end-date cannot be combined with --all-dates")
        start, end = minimum, maximum
    else:
        if not args.end_date:
            raise ValueError("--end-date is required with --start-date")
        start = parse_date(args.start_date, "--start-date")
        end = parse_date(args.end_date, "--end-date")
    if start > end:
        raise ValueError("--start-date cannot be later than --end-date")
    if start < minimum or end > maximum:
        raise ValueError(f"Available date range is {minimum_text} to {maximum_text}")

    catalogue_variables = available_variables(form)
    requested = (
        [item["name"] for item in catalogue_variables]
        if args.all_variables
        else flatten_variables(args.variable)
    )
    groups_by_name = {item["name"]: item["group"] for item in catalogue_variables}
    unknown = [name for name in requested if name not in groups_by_name]
    if unknown:
        raise ValueError(
            "Unavailable variable(s): " + ", ".join(unknown)
            + ". Run list_available_data.py for the live list."
        )
    groups: dict[str, list[str]] = {}
    for name in requested:
        groups.setdefault(groups_by_name[name], []).append(name)
    return requested, groups, start, end


def split_date_range(start: date, end: date, chunk_years: int) -> list[tuple[date, date]]:
    """Split a date range into deterministic calendar-year chunks."""
    chunks: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(date(cursor.year + chunk_years - 1, 12, 31), end)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return chunks


def output_path(args: argparse.Namespace, group: str, start: date, end: date) -> Path:
    extension = "nc" if args.format == "netcdf" else "csv"
    return args.output_dir / f"era5_{group}_{start.isoformat()}_{end.isoformat()}.{extension}"


def unpack_csv_if_needed(target: Path) -> None:
    """Keep the CDS ZIP response and expose its single CSV member at target."""
    if not zipfile.is_zipfile(target):
        return
    archive = target.with_suffix(".zip")
    if archive.exists():
        raise FileExistsError(f"Cannot preserve ZIP because it already exists: {archive}")
    target.replace(archive)
    with zipfile.ZipFile(archive) as bundle:
        members = [name for name in bundle.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Expected one CSV in {archive}, found {len(members)}")
        with bundle.open(members[0]) as source, target.open("wb") as destination:
            shutil.copyfileobj(source, destination)
    print(f"Preserved CDS archive: {archive}")


def main() -> int:
    args = parse_args()
    try:
        _, form = fetch_catalogue()
        requested, groups, start, end = validate(args, form)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    chunks = split_date_range(start, end, args.chunk_years)
    print(f"Dataset: {DATASET}")
    print(f"Location: longitude={args.longitude}, latitude={args.latitude}")
    print(f"Dates: {start.isoformat()}/{end.isoformat()} (hourly, UTC)")
    print(f"Variables ({len(requested)}): {', '.join(requested)}")
    print(f"Chunks: {len(chunks)} (up to {args.chunk_years} calendar years each)")
    for group, variables in groups.items():
        print(f"[{group}] {len(variables)} variable(s): {', '.join(variables)}")
        for chunk_start, chunk_end in chunks:
            print(f"  Request -> {output_path(args, group, chunk_start, chunk_end)}")

    if not args.execute:
        print("Preview only. Add --execute to submit the request.")
        return 0

    try:
        url, key = load_credentials(args.key_file)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    try:
        import cdsapi
    except ModuleNotFoundError:
        print("Error: cdsapi is not installed. Run: python3 -m pip install -r era5/requirements.txt", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client(url=url, key=key)
    for group, variables in groups.items():
        for chunk_start, chunk_end in chunks:
            target = output_path(args, group, chunk_start, chunk_end)
            if target.exists() and not args.overwrite:
                print(f"Skip existing file: {target}")
                continue
            request = {
                "variable": variables,
                "location": {"longitude": args.longitude, "latitude": args.latitude},
                "date": [f"{chunk_start.isoformat()}/{chunk_end.isoformat()}"],
                "data_format": args.format,
            }
            print(
                f"Submitting [{group}] "
                f"{chunk_start.isoformat()}/{chunk_end.isoformat()}..."
            )
            client.retrieve(DATASET, request).download(str(target))
            if args.format == "csv":
                unpack_csv_if_needed(target)
            print(f"Downloaded: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
