#!/usr/bin/env python3
"""List the variables and request limits currently exposed by CDS."""

from __future__ import annotations

import argparse
import json

from era5_catalogue import DATASET, available_variables, date_limits, fetch_catalogue


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    metadata, form = fetch_catalogue()
    variables = available_variables(form)
    start, end = date_limits(form)
    result = {
        "dataset": DATASET,
        "title": metadata["title"],
        "catalogue_updated": metadata.get("updated"),
        "available_dates": {"start": start, "end": end},
        "temporal_resolution": "hourly",
        "formats": ["netcdf", "csv"],
        "variables": variables,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(result["title"])
    print(f"Dataset: {DATASET}")
    print(f"Available dates: {start} to {end} (UTC, hourly)")
    print("Atmospheric/surface grid: 0.25 degrees; wave grid: 0.5 degrees")
    print(f"Variables: {len(variables)}\n")
    for group, heading in (("surface", "Surface / single-level"), ("wave", "Wave")):
        print(f"[{heading}]")
        for item in variables:
            if item["group"] == group:
                print(f"  {item['name']:<58} {item['label']}")
        print()


if __name__ == "__main__":
    main()
