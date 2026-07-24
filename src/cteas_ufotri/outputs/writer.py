from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_results(frame: pd.DataFrame, output_directory: str | Path) -> Path:
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "results.csv"
    frame.to_csv(target, index=False)
    return target
