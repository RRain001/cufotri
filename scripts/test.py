"""Small, predictable test entrypoint for manual-based box-model development."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import subprocess
import sys

QUICK_CASES = [
    "tests/unit/test_gaussian.py",
    "tests/unit/test_depletion.py",
    "tests/unit/test_wet_deposition.py",
    "tests/unit/test_multibox_soil.py",
    "tests/unit/test_tfwt_solver.py",
    "tests/unit/test_obt_solver.py",
    "tests/unit/test_balances.py",
    "tests/unit/test_public_dose.py",
    "tests/integration/test_short_case.py",
]
EXTERNAL_EXCLUSIONS = (
    "not external_sb1_data and not external_sb4_data and "
    "not external_era5_data and not private_reblinding_secret and "
    "not historical_review_context"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("level", choices=("quick", "model", "full"))
    args = parser.parse_args()
    if args.level == "quick":
        # Syntax-only AST pass is safe on read-only Docker worktree mounts.
        for source in Path("src").rglob("*.py"):
            ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        paths = QUICK_CASES
    elif args.level == "model":
        paths = ["tests/unit", "tests/integration"]
    else:
        paths = ["-m", EXTERNAL_EXCLUSIONS, "tests"]
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *paths], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
