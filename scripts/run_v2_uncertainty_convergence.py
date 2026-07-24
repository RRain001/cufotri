from __future__ import annotations

import argparse
import json
from pathlib import Path

from cteas_ufotri.analysis.full_model_uncertainty import (
    run_full_model_lhs_convergence,
)
from cteas_ufotri.config import load_configuration


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/v2/v2_full_adult_dose.yaml",
    )
    result = run_full_model_lhs_convergence(
        config,
        config["uncertainty"]["parameters"],
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
