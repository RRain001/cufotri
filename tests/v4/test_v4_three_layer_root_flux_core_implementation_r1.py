from datetime import datetime, timedelta, timezone

import pytest

from cteas_ufotri.plant.root_v3 import RootUptakeSolver as V3RootUptakeSolver
from cteas_ufotri.plant.root_v4 import (
    RootV4InputError,
    RootV4ProvenanceError,
    RootV4UnitError,
    RootWaterFluxProvenanceV4,
    ThreeLayerRootFluxSolverV4,
    ThreeLayerRootWaterFluxForcingV4,
    UFOTRI_ROOT_REFERENCE_EVIDENCE_V4,
)
from cteas_ufotri.plant.soil_v4 import SoilV4Provenance, ThreeLayerSoilState


T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
SOIL_PROVENANCE = SoilV4Provenance(
    source_id="synthetic-three-layer-soil",
    source_version="r1",
    artifact_sha256="1" * 64,
    spatial_reference="synthetic-soil-column",
    temporal_resolution_s=3600.0,
)
ROOT_PROVENANCE = RootWaterFluxProvenanceV4(
    source_id="synthetic-root-water-flux",
    source_locator="tests/v4/test_v4_three_layer_root_flux_core_implementation_r1.py",
    revision="r1",
    artifact_sha256="a" * 64,
    profile_context="synthetic_test",
)


def reference_state() -> ThreeLayerSoilState:
    return ThreeLayerSoilState.from_inventories(
        soil_identifier="root-v4-reference-column",
        water_inventories_m=(0.0125, 0.0250, 0.0375),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=T0,
        provenance=SOIL_PROVENANCE,
    )


def forcing(
    q: tuple[float, float, float] = (1.0e-7, 2.0e-7, 3.0e-7),
    **kwargs: object,
) -> ThreeLayerRootWaterFluxForcingV4:
    return ThreeLayerRootWaterFluxForcingV4(
        plant_identifier="soybean-test",
        timestamp=T0,
        water_uptake_fluxes_m_s=q,
        provenance=ROOT_PROVENANCE,
        **kwargs,
    )


def test_layer_flux_equation_and_interval_ledger_are_exact() -> None:
    state = reference_state()
    plan = ThreeLayerRootFluxSolverV4().plan(state, forcing(), 60.0)

    assert tuple(item.layer_id for item in plan.layer_transfers) == ("L1", "L2", "L3")
    assert tuple(item.soil_hto_concentration_bq_m3_water for item in plan.layer_transfers) == pytest.approx(
        (800.0, 800.0, 800.0)
    )
    assert plan.water_uptake_fluxes_m_s == pytest.approx((1.0e-7, 2.0e-7, 3.0e-7))
    assert plan.hto_uptake_fluxes_bq_m2_s == pytest.approx((8.0e-5, 1.6e-4, 2.4e-4))
    assert tuple(item.water_transfer_m for item in plan.layer_transfers) == pytest.approx(
        (6.0e-6, 1.2e-5, 1.8e-5)
    )
    assert tuple(item.hto_transfer_bq_m2 for item in plan.layer_transfers) == pytest.approx(
        (0.0048, 0.0096, 0.0144)
    )
    assert plan.total_water_transfer_m == pytest.approx(3.6e-5)
    assert plan.total_hto_transfer_bq_m2 == pytest.approx(0.0288)
    assert plan.max_abs_water_balance_residual_m < 1.0e-15
    assert plan.max_abs_hto_balance_residual_bq_m2 < 1.0e-12


def test_root_core_is_non_mutating_and_deterministic() -> None:
    state = reference_state()
    before = state.to_mapping()
    solver = ThreeLayerRootFluxSolverV4()
    first = solver.plan(state, forcing(), 60.0)
    second = solver.plan(state, forcing(), 60.0)
    assert first == second
    assert state.to_mapping() == before
    assert first.soil_identifier == state.soil_identifier
    assert first.timestamp_start == state.timestamp
    assert first.timestamp_end == state.timestamp + timedelta(seconds=60.0)


def test_zero_water_flux_is_valid_zero_transfer() -> None:
    plan = ThreeLayerRootFluxSolverV4().plan(reference_state(), forcing((0.0, 0.0, 0.0)), 3600.0)
    assert plan.total_water_transfer_m == 0.0
    assert plan.total_hto_transfer_bq_m2 == 0.0
    assert plan.hto_uptake_fluxes_bq_m2_s == (0.0, 0.0, 0.0)


def test_interval_start_time_alignment_fails_closed() -> None:
    state = reference_state()
    shifted = ThreeLayerRootWaterFluxForcingV4(
        plant_identifier="soybean-test",
        timestamp=T0 + timedelta(seconds=1),
        water_uptake_fluxes_m_s=(1.0e-7, 2.0e-7, 3.0e-7),
        provenance=ROOT_PROVENANCE,
    )
    with pytest.raises(RootV4InputError, match="forcing.timestamp"):
        ThreeLayerRootFluxSolverV4().plan(state, shifted, 60.0)
    with pytest.raises(RootV4InputError, match="interval_semantics"):
        forcing(interval_semantics="midpoint")
    with pytest.raises(RootV4InputError, match="strictly positive"):
        ThreeLayerRootFluxSolverV4().plan(state, forcing(), 0.0)


def test_non_utc_and_bad_units_fail_closed() -> None:
    with pytest.raises(RootV4InputError, match="UTC"):
        ThreeLayerRootWaterFluxForcingV4(
            plant_identifier="soybean-test",
            timestamp=datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=8))),
            water_uptake_fluxes_m_s=(1.0e-7, 2.0e-7, 3.0e-7),
            provenance=ROOT_PROVENANCE,
        )
    with pytest.raises(RootV4UnitError):
        forcing(water_flux_unit="mm h^-1")


def test_q_w_must_be_explicit_nonnegative_triplet() -> None:
    with pytest.raises(RootV4InputError):
        forcing((-1.0e-7, 0.0, 0.0))
    with pytest.raises(RootV4InputError):
        ThreeLayerRootWaterFluxForcingV4(
            plant_identifier="soybean-test",
            timestamp=T0,
            water_uptake_fluxes_m_s=(1.0e-7, 2.0e-7),  # type: ignore[arg-type]
            provenance=ROOT_PROVENANCE,
        )


def test_provenance_is_mandatory_and_sha_is_strict() -> None:
    with pytest.raises(RootV4ProvenanceError):
        RootWaterFluxProvenanceV4(
            source_id="",
            source_locator="fixture",
            revision="r1",
            artifact_sha256="a" * 64,
            profile_context="synthetic_test",
        )
    with pytest.raises(RootV4ProvenanceError, match="SHA-256"):
        RootWaterFluxProvenanceV4(
            source_id="source",
            source_locator="fixture",
            revision="r1",
            artifact_sha256="not-a-sha",
            profile_context="synthetic_test",
        )


def test_root_water_overdraw_fails_before_any_state_application() -> None:
    state = reference_state()
    with pytest.raises(RootV4InputError, match="exhaust layer water"):
        ThreeLayerRootFluxSolverV4().plan(state, forcing((0.02, 0.0, 0.0)), 1.0)
    assert state == reference_state()


def test_transfer_plan_exposes_exact_soil_sink_identity_without_applying_it() -> None:
    plan = ThreeLayerRootFluxSolverV4().plan(reference_state(), forcing(), 60.0)
    assert plan.water_uptake_fluxes_m_s == tuple(
        item.water_uptake_flux_m_s for item in plan.layer_transfers
    )
    assert plan.hto_uptake_fluxes_bq_m2_s == tuple(
        item.hto_uptake_flux_bq_m2_s for item in plan.layer_transfers
    )
    assert all(item.remaining_water_if_applied_m > 0.0 for item in plan.layer_transfers)
    assert all(item.remaining_hto_if_applied_bq_m2 >= 0.0 for item in plan.layer_transfers)


def test_ufotri_reference_fixture_is_evidence_not_runtime_forcing() -> None:
    evidence = UFOTRI_ROOT_REFERENCE_EVIDENCE_V4
    assert evidence.layer_ids == ("L1", "L2", "L3")
    assert evidence.long_term_layer_water_uptake_fraction == pytest.approx((0.20, 0.40, 0.40))
    assert sum(evidence.long_term_layer_water_uptake_fraction) == pytest.approx(1.0)
    assert evidence.long_term_transfer_rate_d_minus_1 == pytest.approx((0.026, 0.026, 0.017))
    assert evidence.short_term_transpiration_to_root_delay_h == pytest.approx(3.0)
    assert evidence.runtime_activation is False
    assert evidence.long_term_status == "REFERENCE_EVIDENCE_NOT_ACTIVE_PARAMETERIZATION"
    assert evidence.short_term_status == "REFERENCE_EVIDENCE_NOT_RUNTIME_ACTIVATION"
    assert not hasattr(evidence, "to_forcing")


def test_v4_root_core_is_isolated_from_v3_solver_and_pipeline() -> None:
    assert V3RootUptakeSolver is not ThreeLayerRootFluxSolverV4
    assert "root_v3" in V3RootUptakeSolver.__module__
    assert "root_v4" in ThreeLayerRootFluxSolverV4.__module__
    assert not hasattr(ThreeLayerRootFluxSolverV4, "advance_pipeline")
