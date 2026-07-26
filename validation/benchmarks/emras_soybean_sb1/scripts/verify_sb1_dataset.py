#!/usr/bin/env python3
"""Fail-closed verification for the tracked SB1 publication dataset."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import jsonschema
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb1"
TABLES = BENCHMARK / "published_tables"
LOCAL = ROOT / "validation" / "external_local" / "emras_soybean_sb1"
PDF_SHA256 = "15b2591d82d8276c83030327d6a65d3f5a2e2ec3b11429d63b7c39461f50d211"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    pdf = LOCAL / "references" / "IAEA-emras-tritium-wg.pdf"
    require(pdf.is_file(), f"Missing source PDF: {pdf}")
    require(sha256(pdf) == PDF_SHA256, "Source PDF checksum changed")

    chamber = pd.read_csv(TABLES / "sb1_chamber_conditions_5min.csv")
    require(len(chamber) == 15, "Expected 15 chamber rows from 09:25 to 10:35")
    require(
        chamber["minutes_from_exposure_start"].tolist() == list(range(-5, 66, 5)),
        "Chamber timestamps are not ordered five-minute points",
    )
    require(
        chamber.loc[
            chamber["minutes_from_exposure_start"].isin([-5, 0]),
            "air_moisture_hto_bq_ml_water",
        ].isna().all(),
        "Published 09:25/09:30 dashes must remain missing",
    )
    require(
        chamber.loc[
            chamber["minutes_from_exposure_start"] == 5,
            "air_moisture_hto_bq_ml_water",
        ].iloc[0] == 7050,
        "Table I.4.6 09:35 value mismatch",
    )
    require(
        chamber.loc[
            chamber["minutes_from_exposure_start"] == 30,
            "air_moisture_hto_bq_ml_water",
        ].iloc[0] == 104000,
        "Table I.4.6 10:00 value mismatch",
    )

    tfwt = pd.read_csv(TABLES / "sb1_tfwt_observations.csv")
    require(len(tfwt) == 11, "Expected 11 SB1 TFWT observations")
    require((tfwt["tfwt_bq_l_water"] == 1000 * tfwt["tfwt_bq_ml_water"]).all(),
            "TFWT Bq/mL to Bq/L conversion mismatch")
    expected_body = {
        0.2: 9580.0,
        1.0: 1050.0,
        24.0: 3.92,
        120.0: 1.32,
        336.0: 0.33,
        936.0: 0.11,
        1608.0: 0.06,
        2280.0: 0.06,
    }
    actual_body = dict(
        tfwt.loc[tfwt["compartment"] == "plant_body", [
            "hours_after_exposure", "tfwt_bq_ml_water"
        ]].to_numpy()
    )
    require(actual_body == expected_body, "Table 5.1 plant-body values mismatch")

    obt = pd.read_csv(TABLES / "sb1_obt_harvest.csv")
    require(len(obt) == 8, "Expected 8 requested SB1 OBT records")
    reported_obt = obt["obt_bq_ml_combustion_water"].notna()
    require(
        np.allclose(
            obt.loc[reported_obt, "obt_bq_l_combustion_water"],
            1000 * obt.loc[reported_obt, "obt_bq_ml_combustion_water"],
        ),
        "OBT Bq/mL to Bq/L conversion mismatch",
    )
    expected_obt = {
        "stem": 18.0,
        "leaves": 14.0,
        "plant_body_average": 16.0,
        "shell": 0.83,
        "seeds": 0.5,
        "pods_average": 0.67,
    }
    actual_obt = dict(
        obt.loc[reported_obt, [
            "compartment", "obt_bq_ml_combustion_water"
        ]].to_numpy()
    )
    require(actual_obt == expected_obt, "Table 5.3 SB1 OBT values mismatch")

    biomass = pd.read_csv(TABLES / "sb1_biomass.csv")
    require(len(biomass) == 12, "Expected 12 SB1 biomass component records")
    exposure = biomass[biomass["stage"] == "exposure"]
    fresh = exposure[exposure["mass_basis"] == "fresh"]["value"].sum()
    dry = exposure[exposure["mass_basis"] == "dry"]["value"].sum()
    require(np.isclose(fresh - dry, 788.2), "Exposure plant water mass mismatch")

    schedule = pd.read_csv(TABLES / "sb1_sampling_schedule.csv")
    require(len(schedule) == 11, "Expected 11 compartment sampling rows")
    local = pd.to_datetime(schedule["sample_datetime_local"], utc=True)
    utc = pd.to_datetime(schedule["sample_datetime_utc"], utc=True)
    require((local == utc).all(), "Local/UTC sampling round trip failed")

    protocol = yaml.safe_load(
        (BENCHMARK / "preregistration" / "sb1_benchmark_protocol.yaml").read_text()
    )
    calibration = set(protocol["calibration"]["hours_after_exposure"])
    holdout = set(protocol["pseudo_holdout_a"]["hours_after_exposure"])
    require(calibration.isdisjoint(holdout), "Calibration and holdout overlap")
    require(
        protocol["production_gate_eligible"] is False,
        "Benchmark must not be production-gate eligible",
    )

    manifest_path = BENCHMARK / "sb1_case_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (BENCHMARK / "schemas" / "sb1_case_manifest.schema.json").read_text()
    )
    jsonschema.Draft202012Validator(schema).validate(manifest)
    require(
        manifest["source_document_sha256"] == PDF_SHA256,
        "Manifest source checksum mismatch",
    )
    for filename, checksum in manifest["published_table_checksums"].items():
        require(sha256(TABLES / filename) == checksum, f"Checksum mismatch: {filename}")

    print("PDF_TABLE_TRANSCRIPTION = PASS")
    print("SOURCE_CELL_TRACEABILITY = PASS")
    print("UNIT_CONVERSION = PASS")
    print("CHAMBER_TIME_SERIES = PASS")
    print("CASE_MANIFEST_SCHEMA = PASS")
    print("CHECKSUM_STATUS = PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, jsonschema.ValidationError) as exc:
        print(f"SB1 dataset verification failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
