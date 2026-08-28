"""Independent manual-semantic tests for C1 Eq. (33)-(37) reconstruction."""

from __future__ import annotations

from datetime import datetime, timezone
import math

import pytest

from cteas_ufotri.plant.soil_ufotri_v4 import (
    HydraulicRelationProvenance,
    INTERFACE_CONDUCTIVITY_RULE,
    TabulatedSoilHydraulicRelation,
    UFOTRIHydraulicProfile,
    UFOTRISoilHydrologyError,
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


UTC = timezone.utc
HALF_LIFE_S = 388_789_632.0


def _hydraulic_provenance() -> HydraulicRelationProvenance:
    return HydraulicRelationProvenance(
        source_id="SYNTHETIC_C1_CONSTITUTIVE_TABLE",
        source_version="r1",
        source_locator="tests/v4/test_ufotri_eq33_37_soil_hydrology_reconstruction_r1.py",
    )


def _soil_provenance() -> SoilV4Provenance:
    return SoilV4Provenance(
        source_id="SYNTHETIC_C1_SOIL_STATE",
        source_version="r1",
        artifact_sha256="a" * 64,
        spatial_reference="synthetic-common-soil-surface-area",
        temporal_resolution_s=3600.0,
    )


def _state(
    theta: tuple[float, float, float],
    concentrations: tuple[float, float, float] = (10.0, 20.0, 30.0),
) -> ThreeLayerSoilState:
    thicknesses = (0.05, 0.10, 0.15)
    water = tuple(value * thickness for value, thickness in zip(theta, thicknesses, strict=True))
    hto = tuple(c * w for c, w in zip(concentrations, water, strict=True))
    return ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-c1-soil",
        water_inventories_m=water,
        hto_inventories_bq_m2=hto,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        provenance=_soil_provenance(),
    )


def _relation(
    *,
    theta: tuple[float, ...] = (0.10, 0.40),
    head: tuple[float, ...] = (-1.0, -1.0),
    conductivity: tuple[float, ...] = (1.0e-6, 1.0e-6),
) -> TabulatedSoilHydraulicRelation:
    return TabulatedSoilHydraulicRelation(
        theta=theta,
        matric_head_m=head,
        hydraulic_conductivity_m_s=conductivity,
        provenance=_hydraulic_provenance(),
    )


def test_eq33_is_an_independent_additive_identity() -> None:
    expected = -2.5 + -0.3 + 1.25 + 0.05
    actual = ufotri_eq33_total_potential_head_m(
        matric_head_m=-2.5,
        osmotic_head_m=-0.3,
        gravitational_head_m=1.25,
        pressure_or_gas_head_m=0.05,
    )
    assert actual == expected


def test_eq35_equal_non_gravitational_potential_gives_downward_gravity_flux() -> None:
    assert ufotri_eq35_water_flux_m_s(
        hydraulic_conductivity_m_s=2.0e-6,
        potential_gradient_m_per_m=0.0,
    ) == pytest.approx(2.0e-6, rel=0.0, abs=1.0e-18)


def test_uniform_head_profile_generates_gravity_drainage_and_upwind_hto() -> None:
    state = _state((0.20, 0.20, 0.20))
    fluxes = build_ufotri_eq33_37_interlayer_fluxes(
        state,
        UFOTRIHydraulicProfile.uniform(_relation()),
    )
    assert fluxes.theta == pytest.approx((0.20, 0.20, 0.20))
    assert fluxes.layer_center_depth_m == pytest.approx((0.025, 0.10, 0.225))
    assert fluxes.l1_l2_water_flux_m_s == pytest.approx(1.0e-6)
    assert fluxes.l2_l3_water_flux_m_s == pytest.approx(1.0e-6)
    assert fluxes.l1_l2_hto_flux_bq_m2_s == pytest.approx(1.0e-5)
    assert fluxes.l2_l3_hto_flux_bq_m2_s == pytest.approx(2.0e-5)
    assert fluxes.interface_conductivity_rule == INTERFACE_CONDUCTIVITY_RULE


def test_wetter_lower_layers_can_generate_signed_upward_capillary_flux() -> None:
    relation = _relation(
        theta=(0.10, 0.30),
        head=(-1.0, 0.0),
        conductivity=(1.0e-6, 1.0e-6),
    )
    state = _state((0.10, 0.20, 0.30))
    fluxes = build_ufotri_eq33_37_interlayer_fluxes(
        state,
        UFOTRIHydraulicProfile.uniform(relation),
    )
    # Independent manual arithmetic with depth positive downward:
    # L1-L2: dPsi/dz = 0.5 / 0.075 = 6.666..., q=-K*(grad-1)<0.
    expected_q12 = -1.0e-6 * ((-0.5 - -1.0) / (0.10 - 0.025) - 1.0)
    expected_q23 = -1.0e-6 * ((0.0 - -0.5) / (0.225 - 0.10) - 1.0)
    assert fluxes.l1_l2_water_flux_m_s == pytest.approx(expected_q12)
    assert fluxes.l2_l3_water_flux_m_s == pytest.approx(expected_q23)
    assert fluxes.l1_l2_water_flux_m_s < 0.0
    assert fluxes.l2_l3_water_flux_m_s < 0.0
    # Negative/upward flow uses the lower layer as HTO donor.
    assert fluxes.l1_l2_hto_flux_bq_m2_s == pytest.approx(expected_q12 * 20.0)
    assert fluxes.l2_l3_hto_flux_bq_m2_s == pytest.approx(expected_q23 * 30.0)


def test_constitutive_relation_is_explicit_and_fails_closed_outside_domain() -> None:
    relation = _relation()
    assert relation.matric_potential_head_m(0.25) == pytest.approx(-1.0)
    assert relation.conductivity_m_s(0.25) == pytest.approx(1.0e-6)
    with pytest.raises(UFOTRISoilHydrologyError, match="outside supplied constitutive domain"):
        relation.conductivity_m_s(0.05)


def test_invalid_or_ambiguous_constitutive_tables_fail_closed() -> None:
    with pytest.raises(UFOTRISoilHydrologyError, match="strictly increasing"):
        _relation(theta=(0.20, 0.20))
    with pytest.raises(UFOTRISoilHydrologyError, match="cannot be negative"):
        _relation(conductivity=(1.0e-6, -1.0e-6))


def test_projection_preserves_external_boundaries_and_eq37_root_sink() -> None:
    state = _state((0.20, 0.20, 0.20))
    fluxes = build_ufotri_eq33_37_interlayer_fluxes(
        state,
        UFOTRIHydraulicProfile.uniform(_relation()),
    )
    base = ThreeLayerSoilForcing(
        timestamp=state.timestamp,
        surface_water_input_m_s=2.0e-8,
        surface_water_loss_m_s=3.0e-9,
        surface_deposition_flux_bq_m2_s=4.0e-9,
        lower_boundary_water_loss_m_s=5.0e-9,
        lower_boundary_hto_loss_bq_m2_s=6.0e-9,
        surface_reemission_hto_loss_bq_m2_s=7.0e-9,
        root_water_extraction_m_s=(1.0e-9, 2.0e-9, 3.0e-9),
        root_hto_extraction_bq_m2_s=(4.0e-9, 5.0e-9, 6.0e-9),
    )
    projected = project_ufotri_hydrology_to_soil_forcing(base, fluxes)
    assert projected.surface_water_input_m_s == base.surface_water_input_m_s
    assert projected.surface_water_loss_m_s == base.surface_water_loss_m_s
    assert projected.lower_boundary_water_loss_m_s == base.lower_boundary_water_loss_m_s
    assert projected.root_water_extraction_m_s == base.root_water_extraction_m_s
    assert projected.root_hto_extraction_bq_m2_s == base.root_hto_extraction_bq_m2_s
    assert projected.l1_l2_water_flux_m_s == fluxes.l1_l2_water_flux_m_s
    assert projected.l2_l3_hto_flux_bq_m2_s == fluxes.l2_l3_hto_flux_bq_m2_s


def test_projection_refuses_to_double_count_existing_interlayer_forcing() -> None:
    state = _state((0.20, 0.20, 0.20))
    fluxes = build_ufotri_eq33_37_interlayer_fluxes(
        state,
        UFOTRIHydraulicProfile.uniform(_relation()),
    )
    occupied = ThreeLayerSoilForcing(timestamp=state.timestamp, l1_l2_water_flux_m_s=1.0e-12)
    with pytest.raises(UFOTRISoilHydrologyError, match="double count"):
        project_ufotri_hydrology_to_soil_forcing(occupied, fluxes)


def test_generated_internal_fluxes_close_frozen_soil_inventory_balance() -> None:
    state = _state((0.20, 0.20, 0.20))
    fluxes = build_ufotri_eq33_37_interlayer_fluxes(
        state,
        UFOTRIHydraulicProfile.uniform(
            _relation(conductivity=(1.0e-8, 1.0e-8))
        ),
    )
    forcing = project_ufotri_hydrology_to_soil_forcing(
        ThreeLayerSoilForcing(timestamp=state.timestamp),
        fluxes,
    )
    result = ThreeLayerSoilStorageSolver(tritium_half_life_s=HALF_LIFE_S).advance(
        state,
        forcing,
        60.0,
    )
    assert abs(result.global_balance.water_residual_m) <= 1.0e-15
    assert abs(result.global_balance.hto_residual_bq_m2) <= 1.0e-12
    assert abs(result.global_balance.interlayer_water_cancellation_m) <= 1.0e-18
    assert abs(result.global_balance.interlayer_hto_cancellation_bq_m2) <= 1.0e-18


def test_no_original_constitutive_parameters_or_root_sink_are_inferred() -> None:
    # C1 has no factory that silently chooses a soil curve. A relation is a
    # required argument to the profile, and root extraction remains absent from
    # the generated flux result by construction.
    with pytest.raises(TypeError):
        UFOTRIHydraulicProfile()  # type: ignore[call-arg]
    assert not hasattr(
        build_ufotri_eq33_37_interlayer_fluxes(_state((0.20, 0.20, 0.20)), UFOTRIHydraulicProfile.uniform(_relation())),
        "root_water_extraction_m_s",
    )
