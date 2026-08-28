#!/usr/bin/env python3
"""Machine-visible C1 gate for UFOTRI Eq. (33)-(37) hydrology reconstruction."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math

from cteas_ufotri.plant.soil_ufotri_v4 import (
    HydraulicRelationProvenance,
    INTERFACE_CONDUCTIVITY_RULE,
    TabulatedSoilHydraulicRelation,
    UFOTRIHydraulicProfile,
    build_ufotri_eq33_37_interlayer_fluxes,
    project_ufotri_hydrology_to_soil_forcing,
    ufotri_eq33_total_potential_head_m,
    ufotri_eq35_water_flux_m_s,
)
from cteas_ufotri.plant.soil_v4 import (
    SoilV4Provenance,
    ThreeLayerSoilForcing,
    ThreeLayerSoilState,
    ThreeLayerSoilStorageSolver,
)


STAGE = "UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1"
HALF_LIFE_S = 388_789_632.0


def _soil(theta: tuple[float, float, float]) -> ThreeLayerSoilState:
    thickness = (0.05, 0.10, 0.15)
    water = tuple(a * b for a, b in zip(theta, thickness, strict=True))
    concentration = (10.0, 20.0, 30.0)
    hto = tuple(a * b for a, b in zip(concentration, water, strict=True))
    return ThreeLayerSoilState.from_inventories(
        soil_identifier="c1-machine-gate",
        water_inventories_m=water,
        hto_inventories_bq_m2=hto,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        provenance=SoilV4Provenance(
            source_id="SYNTHETIC_C1_MACHINE_GATE",
            source_version="r1",
            artifact_sha256="d" * 64,
            spatial_reference="synthetic-common-soil-surface-area",
            temporal_resolution_s=60.0,
        ),
    )


def _relation(
    head: tuple[float, float],
    conductivity: float,
) -> TabulatedSoilHydraulicRelation:
    return TabulatedSoilHydraulicRelation(
        theta=(0.10, 0.30),
        matric_head_m=head,
        hydraulic_conductivity_m_s=(conductivity, conductivity),
        provenance=HydraulicRelationProvenance(
            source_id="SYNTHETIC_C1_CONSTITUTIVE_TABLE",
            source_version="r1",
            source_locator="scripts/v4/run_ufotri_eq33_37_soil_hydrology_reconstruction_r1.py",
        ),
    )


def build_result() -> dict[str, object]:
    eq33 = ufotri_eq33_total_potential_head_m(
        matric_head_m=-2.0,
        osmotic_head_m=-0.2,
        gravitational_head_m=1.0,
        pressure_or_gas_head_m=0.1,
    )
    gravity_q = ufotri_eq35_water_flux_m_s(
        hydraulic_conductivity_m_s=1.0e-6,
        potential_gradient_m_per_m=0.0,
    )

    uniform_state = _soil((0.20, 0.20, 0.20))
    uniform_flux = build_ufotri_eq33_37_interlayer_fluxes(
        uniform_state,
        UFOTRIHydraulicProfile.uniform(_relation((-1.0, -1.0), 1.0e-8)),
    )
    forcing = project_ufotri_hydrology_to_soil_forcing(
        ThreeLayerSoilForcing(timestamp=uniform_state.timestamp),
        uniform_flux,
    )
    step = ThreeLayerSoilStorageSolver(tritium_half_life_s=HALF_LIFE_S).advance(
        uniform_state,
        forcing,
        60.0,
    )

    capillary_state = _soil((0.10, 0.20, 0.30))
    capillary_flux = build_ufotri_eq33_37_interlayer_fluxes(
        capillary_state,
        UFOTRIHydraulicProfile.uniform(_relation((-1.0, 0.0), 1.0e-6)),
    )

    gates = {
        "eq33_additive_identity": math.isclose(eq33, -1.1, rel_tol=0.0, abs_tol=1.0e-15),
        "eq35_gravity_direction": math.isclose(gravity_q, 1.0e-6, rel_tol=0.0, abs_tol=1.0e-18),
        "uniform_profile_downward": (
            uniform_flux.l1_l2_water_flux_m_s > 0.0
            and uniform_flux.l2_l3_water_flux_m_s > 0.0
        ),
        "capillary_profile_upward": (
            capillary_flux.l1_l2_water_flux_m_s < 0.0
            and capillary_flux.l2_l3_water_flux_m_s < 0.0
        ),
        "upwind_hto_sign_tracks_water": (
            capillary_flux.l1_l2_hto_flux_bq_m2_s < 0.0
            and capillary_flux.l2_l3_hto_flux_bq_m2_s < 0.0
        ),
        "frozen_soil_water_balance": abs(step.global_balance.water_residual_m) <= 1.0e-15,
        "frozen_soil_hto_balance": abs(step.global_balance.hto_residual_bq_m2) <= 1.0e-12,
        "interlayer_cancellation": (
            abs(step.global_balance.interlayer_water_cancellation_m) <= 1.0e-18
            and abs(step.global_balance.interlayer_hto_cancellation_bq_m2) <= 1.0e-18
        ),
        "implementation_choice_labeled": (
            uniform_flux.interface_conductivity_rule == INTERFACE_CONDUCTIVITY_RULE
        ),
        "root_sink_not_inferred": not hasattr(uniform_flux, "root_water_extraction_m_s"),
    }
    status = "PASS_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION" if all(gates.values()) else "HOLD_C1_GATE_FAILED"
    result: dict[str, object] = {
        "schema_version": "v1",
        "stage": STAGE,
        "status": status,
        "gates": gates,
        "diagnostics": {
            "eq33_total_head_m": eq33,
            "eq35_gravity_flux_m_s": gravity_q,
            "uniform_l1_l2_water_flux_m_s": uniform_flux.l1_l2_water_flux_m_s,
            "uniform_l2_l3_water_flux_m_s": uniform_flux.l2_l3_water_flux_m_s,
            "capillary_l1_l2_water_flux_m_s": capillary_flux.l1_l2_water_flux_m_s,
            "capillary_l2_l3_water_flux_m_s": capillary_flux.l2_l3_water_flux_m_s,
            "water_balance_residual_m": step.global_balance.water_residual_m,
            "hto_balance_residual_bq_m2": step.global_balance.hto_residual_bq_m2,
        },
        "hard_boundaries": {
            "built_in_constitutive_parameterization": False,
            "original_executable_curve_recovered": False,
            "root_sink_inferred": False,
            "generic_modern_richards_solver": False,
            "calibration": False,
            "empirical_validation": False,
            "production_hydrology": False,
            "real_cteas_atmos_binding": False,
            "frozen_soil_v4_modified": False,
        },
    }
    if status != "PASS_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION":
        raise RuntimeError(json.dumps(gates, sort_keys=True))
    return result


def main() -> int:
    result = build_result()
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    print(f"UFOTRI_EQ33_37_SOIL_HYDROLOGY_STATUS={result['status']}")
    print(f"UFOTRI_EQ33_37_SOIL_HYDROLOGY_RESULT_JSON={encoded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
