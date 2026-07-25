from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_reference_csv(
    path: Path,
    required_columns: set[str],
    expected_sha256: str,
) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Reference data missing: {path}")
    actual_hash = sha256(path)
    if actual_hash != expected_sha256:
        raise ValueError(
            f"Reference checksum mismatch: expected {expected_sha256}, "
            f"got {actual_hash}"
        )
    frame = pd.read_csv(path)
    missing = sorted(required_columns - set(frame.columns))
    if missing:
        raise ValueError(f"Reference columns missing: {missing}")
    return frame
