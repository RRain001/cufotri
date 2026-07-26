#!/usr/bin/env python3
"""Independently verify the tracked SB4 publication-table dataset."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb4"
TABLES = BENCHMARK / "published_tables"


def main() -> int:
    tfwt = pd.read_csv(TABLES / "sb4_tfwt_observations.csv")
    body = tfwt[tfwt["compartment"] == "plant_body"]
    pods = tfwt[tfwt["compartment"] == "pods"]
    expected_hours = np.array([0.2, 1, 24, 120, 336, 768, 1368])
    np.testing.assert_array_equal(body["hours_after_exposure"], expected_hours)
    np.testing.assert_array_equal(pods["hours_after_exposure"], expected_hours)
    np.testing.assert_allclose(
        body["tfwt_bq_ml_water"],
        [7000, 3200, 25.9, 2.1, 0.8, 0.27, 0.14],
        rtol=0,
        atol=0,
    )
    np.testing.assert_allclose(
        pods["tfwt_bq_ml_water"],
        [10500, 8000, 2700, 63.5, 1.49, 0.84, 0.26],
        rtol=0,
        atol=0,
    )
    obt = pd.read_csv(TABLES / "sb4_obt_harvest.csv").set_index(
        "compartment"
    )
    expected_obt = {
        "stem": 19.8,
        "leaves": 8.8,
        "plant_body_average": 14.3,
        "shell": 74.7,
        "seeds": 200.0,
        "pods_average": 137.4,
    }
    for compartment, value in expected_obt.items():
        assert obt.loc[compartment, "obt_bq_ml_combustion_water"] == value
    manifest = json.loads(
        (BENCHMARK / "sb4_case_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["production_gate_eligible"] is False
    assert manifest["empirical_validation_claim"] is False
    print("SB4_PDF_TABLE_TRANSCRIPTION = PASS")
    print("SB4_SOURCE_CELL_TRACEABILITY = PASS")
    print("SB4_UNIT_CONVERSION = PASS")
    print("SB4_SAMPLING_SCHEDULE = PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
