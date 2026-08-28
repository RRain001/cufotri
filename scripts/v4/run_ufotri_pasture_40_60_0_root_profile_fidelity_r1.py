#!/usr/bin/env python3
"""Machine-visible D2 qualification for the UFOTRI pasture 40/60/0 profile."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any

from cteas_ufotri.plant.root_v4 import (
    RootWaterFluxProvenanceV4,
    ThreeLayerRootFluxSolverV4,
    UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS,
    ufotri_three_layer_root_water_flux_forcing,
)
from cteas_ufotri.plant.root_v4.pasture_profile import (
    UFOTRI_PASTURE_ROOT_PROFILE_ID,
    UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS,
    ufotri_pasture_three_layer_root_water_flux_forcing,
)
from cteas_ufotri.plant.soil_v4 import SoilV4Provenance, ThreeLayerSoilState

UTC = timezone.utc
STAGE = "UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY_R1"
TIMESTAMP = datetime(2026, 1, 1, tzinfo=UTC)
TOTAL_Q_M_S = 4.0e-8
INTERVAL_S = 1800.0


def _root_provenance(profile_context: str) -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="SYNTHETIC_D2_EXPLICIT_TOTAL_ROOT_UPTAKE",
        source_locator="scripts/v4/run_ufotri_pasture_40_60_0_root_profile_fidelity_r1.py",
        revision="r1",
        artifact_sha256="d" * 64,
        profile_context=profile_context,
    )


def _soil_state(concentrations: tuple[float, float, float]) -> ThreeLayerSoilState:
    water = (0.10, 0.15, 0.20)
    hto = tuple(c * w for c, w in zip(concentrations, water, strict=True))
    return ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-d2-soil",
        water_inventories_m=water,
        hto_inventories_bq_m2=hto,
        timestamp=TIMESTAMP,
        provenance=SoilV4Provenance(
            source_id="SYNTHETIC_D2_SOIL",
            source_version="r1",
            artifact_sha256="e" * 64,
            spatial_reference="soil_surface_area",
            temporal_resolution_s=INTERVAL_S,
        ),
    )


def build_result() -> dict[str, Any]:
    pasture_forcing = ufotri_pasture_three_layer_root_water_flux_forcing(
        total_water_uptake_flux_m_s=TOTAL_Q_M_S,
        plant_identifier="synthetic-pasture",
        timestamp=TIMESTAMP,
        provenance=_root_provenance(UFOTRI_PASTURE_ROOT_PROFILE_ID),
    )
    crop_forcing = ufotri_three_layer_root_water_flux_forcing(
        total_water_uptake_flux_m_s=TOTAL_Q_M_S,
        plant_identifier="synthetic-crop",
        timestamp=TIMESTAMP,
        provenance=_root_provenance("UFOTRI_CROP_20_40_40_CONTROL"),
    )

    solver = ThreeLayerRootFluxSolverV4()
    equal_soil = _soil_state((100.0, 100.0, 100.0))
    unequal_soil = _soil_state((100.0, 200.0, 300.0))
    pasture_equal = solver.plan(equal_soil, pasture_forcing, INTERVAL_S)
    crop_equal = solver.plan(equal_soil, crop_forcing, INTERVAL_S)
    pasture_unequal = solver.plan(unequal_soil, pasture_forcing, INTERVAL_S)

    expected_unequal_hto = sum(
        q * c * INTERVAL_S
        for q, c in zip(
            pasture_forcing.water_uptake_fluxes_m_s,
            (100.0, 200.0, 300.0),
            strict=True,
        )
    )

    invariants = {
        "pasture_fractions_exact": UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS
        == (0.4, 0.6, 0.0),
        "pasture_fractions_sum_to_one": math.isclose(
            sum(UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS),
            1.0,
            rel_tol=0.0,
            abs_tol=0.0,
        ),
        "existing_crop_20_40_40_unchanged": UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS
        == (0.2, 0.4, 0.4),
        "pasture_layer_fluxes_exact": pasture_forcing.water_uptake_fluxes_m_s
        == (1.6e-8, 2.4e-8, 0.0),
        "crop_and_pasture_total_water_flux_equal": math.isclose(
            sum(pasture_forcing.water_uptake_fluxes_m_s),
            sum(crop_forcing.water_uptake_fluxes_m_s),
            rel_tol=1.0e-15,
        ),
        "pasture_l3_flux_exact_zero": pasture_forcing.water_uptake_fluxes_m_s[2] == 0.0,
        "layer_allocation_differs_from_crop_profile": pasture_forcing.water_uptake_fluxes_m_s
        != crop_forcing.water_uptake_fluxes_m_s,
        "equal_concentration_total_hto_transfer_equal": math.isclose(
            pasture_equal.total_hto_transfer_bq_m2,
            crop_equal.total_hto_transfer_bq_m2,
            rel_tol=1.0e-15,
            abs_tol=1.0e-18,
        ),
        "pasture_total_water_transfer_identity": math.isclose(
            pasture_equal.total_water_transfer_m,
            TOTAL_Q_M_S * INTERVAL_S,
            rel_tol=1.0e-15,
        ),
        "pasture_j_equals_q_times_c": all(
            math.isclose(
                transfer.hto_uptake_flux_bq_m2_s,
                transfer.water_uptake_flux_m_s
                * layer.hto_concentration_bq_m3_water,
                rel_tol=1.0e-15,
                abs_tol=0.0,
            )
            for transfer, layer in zip(
                pasture_unequal.layer_transfers,
                unequal_soil.layers,
                strict=True,
            )
        ),
        "unequal_concentration_hto_transfer_identity": math.isclose(
            pasture_unequal.total_hto_transfer_bq_m2,
            expected_unequal_hto,
            rel_tol=1.0e-15,
            abs_tol=1.0e-18,
        ),
        "pasture_water_ledger_closed": pasture_unequal.max_abs_water_balance_residual_m
        <= 1.0e-15,
        "pasture_hto_ledger_closed": pasture_unequal.max_abs_hto_balance_residual_bq_m2
        <= 1.0e-12,
        "forcing_contract_unchanged": pasture_forcing.interval_semantics == "start",
    }
    if not all(invariants.values()):
        failed = sorted(key for key, value in invariants.items() if not value)
        raise RuntimeError(f"D2 machine gate failed: {failed}")

    return {
        "schema_version": "v1",
        "stage": STAGE,
        "status": "PASS_PASTURE_ROOT_PROFILE_FIDELITY",
        "source_kind": "MANUAL_DIRECT_PROFILE_WITH_SYNTHETIC_NUMERICAL_GATE",
        "pasture_profile_id": UFOTRI_PASTURE_ROOT_PROFILE_ID,
        "pasture_fractions": UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS,
        "crop_control_fractions": UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS,
        "total_water_uptake_flux_m_s": TOTAL_Q_M_S,
        "pasture_layer_water_fluxes_m_s": pasture_forcing.water_uptake_fluxes_m_s,
        "crop_layer_water_fluxes_m_s": crop_forcing.water_uptake_fluxes_m_s,
        "equal_concentration_total_hto_transfer_bq_m2": pasture_equal.total_hto_transfer_bq_m2,
        "unequal_concentration_total_hto_transfer_bq_m2": pasture_unequal.total_hto_transfer_bq_m2,
        "invariants": invariants,
        "hard_boundaries": {
            "existing_20_40_40_source_changed": False,
            "root_solver_changed": False,
            "total_uptake_inferred": False,
            "production_parameter_activation": False,
            "calibration": False,
            "empirical_validation": False,
            "physical_accuracy_claim": False,
            "real_cteas_atmos_binding": False,
            "original_executable_equivalence": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    text = json.dumps(result, indent=2, sort_keys=True)
    print(f"D2_PASTURE_ROOT_PROFILE_STATUS={result['status']}")
    print(f"D2_PASTURE_ROOT_PROFILE_RESULT_JSON={json.dumps(result, sort_keys=True)}")
    if args.output is not None:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
