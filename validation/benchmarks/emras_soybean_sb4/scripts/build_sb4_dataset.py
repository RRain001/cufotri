#!/usr/bin/env python3
"""Build the checksum manifest for the traced SB4 publication tables."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb4"
TABLES = BENCHMARK / "published_tables"
PDF = (
    ROOT
    / "validation"
    / "external_local"
    / "emras_soybean_sb1"
    / "references"
    / "IAEA-emras-tritium-wg.pdf"
)
EXPECTED_PDF_SHA256 = (
    "15b2591d82d8276c83030327d6a65d3f5a2e2ec3b11429d63b7c39461f50d211"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def page_text(page: int) -> str:
    result = subprocess.run(
        [
            "pdftotext",
            "-f",
            str(page),
            "-l",
            str(page),
            "-layout",
            str(PDF),
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def verify_source_cells() -> None:
    if sha256(PDF) != EXPECTED_PDF_SHA256:
        raise ValueError("SB4 source PDF checksum mismatch")
    page_105 = page_text(105)
    page_287 = page_text(287)
    page_290 = page_text(290)
    required_105 = (
        "Table 5.2. Observed and normalized TFWT concentrations for SB4",
        "7000",
        "3200",
        "25.9",
        "63.5",
        "10500",
        "8000",
        "2700",
        "Table 5.3. Observed non-exchangeable",
        "19.8",
        "200.0",
        "137.4",
    )
    required_287 = (
        "Table I.4.2. Fresh biomass",
        "545.8",
        "914.6",
        "392.8",
        "162.6",
        "Table I.4.3. Dry biomass",
        "174.3",
        "303.5",
        "109.5",
        "44.5",
        "1194.5",
        "1687.1",
        "876.0",
        "193.9",
        "329.2",
        "617.1",
        "261.2",
        "79.4",
    )
    required_290 = (
        "Table I.4.10. Requested concentrations for experiment SB4",
        "0.2",
        "1368",
    )
    for text, required in (
        (page_105, required_105),
        (page_287, required_287),
        (page_290, required_290),
    ):
        missing = [value for value in required if value not in text]
        if missing:
            raise ValueError(f"Missing source cells: {missing}")


def verify_tables() -> None:
    tfwt = pd.read_csv(TABLES / "sb4_tfwt_observations.csv")
    obt = pd.read_csv(TABLES / "sb4_obt_harvest.csv")
    biomass = pd.read_csv(TABLES / "sb4_biomass.csv")
    schedule = pd.read_csv(TABLES / "sb4_sampling_schedule.csv")
    if len(tfwt) != 14 or tfwt["compartment"].value_counts().to_dict() != {
        "plant_body": 7,
        "pods": 7,
    }:
        raise ValueError("SB4 TFWT row contract failed")
    if len(obt) != 6 or len(biomass) != 16 or len(schedule) != 14:
        raise ValueError("SB4 OBT, biomass or schedule row contract failed")
    if not (
        tfwt["tfwt_bq_l_water"].to_numpy(float)
        == tfwt["tfwt_bq_ml_water"].to_numpy(float) * 1000.0
    ).all():
        raise ValueError("SB4 TFWT Bq/mL to Bq/L conversion failed")
    if not (
        obt["obt_bq_l_combustion_water"].to_numpy(float)
        == obt["obt_bq_ml_combustion_water"].to_numpy(float) * 1000.0
    ).all():
        raise ValueError("SB4 OBT Bq/mL to Bq/L conversion failed")
    if set(tfwt["verification_status"]) != {"VERIFIED_CELL_BY_CELL"}:
        raise ValueError("SB4 TFWT cells are not fully verified")
    metadata = yaml.safe_load(
        (TABLES / "sb4_experiment_metadata.yaml").read_text(encoding="utf-8")
    )
    if metadata["reported_mean_air_moisture_hto_bq_ml"] != 52700:
        raise ValueError("SB4 reported chamber mean mismatch")


def main() -> int:
    verify_source_cells()
    verify_tables()
    tracked = sorted(path for path in TABLES.iterdir() if path.is_file())
    manifest = {
        "case_id": "EMRAS_SOYBEAN_SB4_PDF_ERA5_V1",
        "evidence_class": (
            "HYBRID_LITERATURE_REANALYSIS_RECONSTRUCTED_CHAMBER"
        ),
        "source_document_sha256": EXPECTED_PDF_SHA256,
        "published_table_checksums": {
            path.name: sha256(path) for path in tracked
        },
        "tfwt_observation_count": 14,
        "obt_observation_count": 6,
        "biomass_cell_count": 16,
        "sampling_schedule_count": 14,
        "empirical_validation_claim": False,
        "production_gate_eligible": False,
    }
    (BENCHMARK / "sb4_case_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("SB4_PUBLICATION_DATASET = PASS")
    print("SB4_TFWT_OBSERVATION_COUNT = 14")
    print("SB4_OBT_OBSERVATION_COUNT = 6")
    print("SB4_BIOMASS_CELL_COUNT = 16")
    print("SB4_SAMPLING_SCHEDULE_COUNT = 14")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
