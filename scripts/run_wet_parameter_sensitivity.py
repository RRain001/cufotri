#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cteas_ufotri.analysis.wet_sensitivity import wet_parameter_sensitivity
from cteas_ufotri.config import load_configuration


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/test_case.yaml",
    )
    records = wet_parameter_sensitivity(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"PASS: wrote {len(records)} wet-parameter sensitivity records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
