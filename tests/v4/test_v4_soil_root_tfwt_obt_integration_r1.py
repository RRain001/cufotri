from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_v3 import OBTState, OBTSolver, PlantBiologicalForcing
from cteas_ufotri.plant.root_v4 import (
    RootWaterFluxProvenanceV4,
    ThreeLayerRootWaterFluxForcingV4,
)
from cteas_ufotri.plant.soil_v4 import (
    SoilV4Provenance,
    ThreeLayerSoilForcing,
    ThreeLayerSoilState,
    ThreeLayerSoilStorageSolver,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.v4_integration import (
    SELECTED_OPERATOR_SPLIT,
    V4IntegrationError,
    V4SoilRootTFWTOBTIntegrator,
    V4SoilRootTFWTOBTState,
)


ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc
DT = 3600.0
TEST_HALF_LIFE_S = 1.0e12
TEST_KF_S = 2.0e-5
TEST_KR_S = 5.0e-6


def plant_provenance() -> ForcingProvenance:
    return ForcingProvenance(
        source_id="SYNTHETIC_TEST_ONLY_PLANT",
        source_version="r1",
        artifact_sha256="a" * 64,
        spatial_reference="unit-test-common-area",
        temporal_resolution_s=DT,
    )


def soil_provenance() -> SoilV4Provenance:
    return SoilV4Provenance(
        source_id="SYNTHETIC_TEST_ONLY_SOIL",
        source_version="r1",
        artifact_sha256="b" * 64,
        spatial_reference="unit-test-common-area",
        temporal_resolution_s=DT,
    )


def root_provenance() -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="SYNTHETIC_TEST_ONLY_ROOT_QW",
        source_locator="tests/v4/test_v4_soil_root_tfwt_obt_integration_r1.py",
        revision="r1",
        artifact_sha256="c" * 64,
        profile_context="SYNTHETIC_TEST_ONLY_EXPLICIT_Q_W",
    )


def make_state(
    *,
    timestamp: datetime | None = None,
    tfwt_inventory: float = 2.0,
    obt_inventory: float = 1.0,
    area_basis: str = "soil_surface_area",
) -> V4SoilRootTFWTOBTState:
    time = timestamp or datetime(2026, 1, 1, tzinfo=UTC)
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=time,
        provenance=soil_provenance(),
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        tfwt_inventory_bq_m2=tfwt_inventory,
        water_content_kg_m2=5.0,
        time=time,
        provenance=plant_provenance(),
        area_basis=area_basis,
    )
    obt = OBTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        obt_inventory_bq_m2=obt_inventory,
        plant_mass_kg_m2=2.0,
        timestamp=time,
        provenance=plant_provenance(),
        area_basis=area_basis,
    )
    return V4SoilRootTFWTOBTState(soil_state=soil, tfwt_state=tfwt, obt_state=obt)


def make_integrator(*, kf_s: float = TEST_KF_S, kr_s: float = TEST_KR_S) -> V4SoilRootTFWTOBTIntegrator:
    return V4SoilRootTFWTOBTIntegrator(
        soil_solver=ThreeLayerSoilStorageSolver(tritium_half_life_s=TEST_HALF_LIFE_S),
        obt_solver=OBTSolver(kf_s=kf_s, kr_s=kr_s),
    )


def root_forcing(timestamp: datetime, fluxes: tuple[float, float, float] = (1.0e-7, 2.0e-7, 1.0e-7)) -> ThreeLayerRootWaterFluxForcingV4:
    return ThreeLayerRootWaterFluxForcingV4(
        plant_identifier="synthetic-soybean",
        timestamp=timestamp,
        water_uptake_fluxes_m_s=fluxes,
        provenance=root_provenance(),
    )


def soil_forcing(timestamp: datetime, **kwargs: object) -> ThreeLayerSoilForcing:
    return ThreeLayerSoilForcing(timestamp=timestamp, **kwargs)


def bio() -> PlantBiologicalForcing:
    return PlantBiologicalForcing(is_daylight=True)


def advance_once(
    integrator: V4SoilRootTFWTOBTIntegrator,
    state: V4SoilRootTFWTOBTState,
    *,
    soil: ThreeLayerSoilForcing | None = None,
    root: ThreeLayerRootWaterFluxForcingV4 | None = None,
):
    return integrator.advance(
        state,
        soil_forcing=soil or soil_forcing(state.timestamp),
        root_forcing=root or root_forcing(state.timestamp),
        biological_forcing=bio(),
        interval_seconds=DT,
    )


def test_selected_split_and_public_scope_are_frozen() -> None:
    assert SELECTED_OPERATOR_SPLIT == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    source = (ROOT / "src/cteas_ufotri/v4_integration/soil_root_tfwt_obt.py").read_text(encoding="utf-8")
    assert "v3_pipeline" not in source
    assert "UFOTRI_ROOT_REFERENCE_EVIDENCE_V4" not in source
    assert "root_v4.reference" not in source
    for path in (ROOT / "src/cteas_ufotri/v3_pipeline").glob("*.py"):
        assert "v4_integration" not in path.read_text(encoding="utf-8")


def test_composite_state_requires_timestamp_identity_and_explicit_common_area_basis() -> None:
    good = make_state()
    mismatched_time = good.tfwt_state.with_inventory(
        tfwt_inventory_bq_m2=good.tfwt_state.inventory(),
        time=good.timestamp + timedelta(seconds=1),
    )
    with pytest.raises(V4IntegrationError, match="interval-start timestamp"):
        V4SoilRootTFWTOBTState(
            soil_state=good.soil_state,
            tfwt_state=mismatched_time,
            obt_state=good.obt_state,
        )

    plant_area_tfwt = replace(good.tfwt_state, area_basis="plant_area")
    with pytest.raises(V4IntegrationError, match="area_basis"):
        V4SoilRootTFWTOBTState(
            soil_state=good.soil_state,
            tfwt_state=plant_area_tfwt,
            obt_state=good.obt_state,
        )


def test_integrator_rejects_prepopulated_soil_root_slots_to_prevent_double_application() -> None:
    state = make_state()
    forcing = soil_forcing(
        state.timestamp,
        root_water_extraction_m_s=(1.0e-8, 0.0, 0.0),
    )
    with pytest.raises(V4IntegrationError, match="root_v4 owns the single root transfer plan"):
        advance_once(make_integrator(), state, soil=forcing)


def test_one_root_plan_is_applied_once_to_soil_sink_and_endpoint_tfwt_gain() -> None:
    state = make_state()
    result = advance_once(make_integrator(), state)
    transfer = result.root_plan.total_hto_transfer_bq_m2

    assert transfer > 0.0
    assert result.applied_soil_forcing.root_water_extraction_m_s == result.root_plan.water_uptake_fluxes_m_s
    assert result.applied_soil_forcing.root_hto_extraction_bq_m2_s == result.root_plan.hto_uptake_fluxes_bq_m2_s
    assert result.soil_result.global_balance.external_hto_loss_bq_m2 == pytest.approx(transfer, abs=1.0e-12)
    expected_tfwt = state.tfwt_state.inventory() - result.obt_result.balance.tfwt_loss_bq_m2 + transfer
    assert result.state.tfwt_state.inventory() == pytest.approx(expected_tfwt, abs=1.0e-12)
    assert result.balance.soil_root_hto_identity_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-12)
    assert result.balance.plant_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-12)
    assert result.balance.coupled_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-10)


def test_root_only_pulse_enters_tfwt_endpoint_but_not_same_interval_obt() -> None:
    integrator = make_integrator()
    state0 = make_state(tfwt_inventory=0.0, obt_inventory=0.0)
    first = advance_once(integrator, state0)

    assert first.root_plan.total_hto_transfer_bq_m2 > 0.0
    assert first.obt_result.balance.obt_formation_bq_m2 == pytest.approx(0.0, abs=1.0e-12)
    assert first.state.tfwt_state.inventory() == pytest.approx(first.root_plan.total_hto_transfer_bq_m2, abs=1.0e-12)
    assert first.state.obt_state.inventory() == pytest.approx(0.0, abs=1.0e-12)

    second = advance_once(integrator, first.state)
    assert second.obt_result.balance.obt_formation_bq_m2 > 0.0
    assert second.state.obt_state.inventory() > 0.0


def test_obt_cannot_borrow_same_interval_root_transfer_to_cover_tfwt_overdraw() -> None:
    state = make_state(tfwt_inventory=0.01, obt_inventory=0.0)
    aggressive_obt = make_integrator(kf_s=1.0, kr_s=0.0)
    with pytest.raises(V4IntegrationError, match="exceeds interval-start TFWT"):
        advance_once(aggressive_obt, state)


def test_external_soil_terms_and_internal_root_transfer_close_coupled_hto_balance() -> None:
    state = make_state()
    forcing = soil_forcing(
        state.timestamp,
        surface_water_input_m_s=2.0e-8,
        surface_water_loss_m_s=1.0e-8,
        surface_deposition_flux_bq_m2_s=2.0e-4,
        l1_l2_water_flux_m_s=1.0e-8,
        l1_l2_hto_flux_bq_m2_s=1.0e-5,
        l2_l3_water_flux_m_s=-5.0e-9,
        l2_l3_hto_flux_bq_m2_s=-5.0e-6,
        lower_boundary_water_loss_m_s=2.0e-9,
        lower_boundary_hto_loss_bq_m2_s=1.0e-5,
        surface_reemission_hto_loss_bq_m2_s=5.0e-6,
    )
    result = advance_once(make_integrator(), state, soil=forcing)

    assert result.soil_result.global_balance.external_hto_input_bq_m2 > 0.0
    assert result.balance.soil_nonroot_external_hto_loss_bq_m2 > 0.0
    assert result.balance.soil_decay_loss_bq_m2 >= 0.0
    assert result.balance.plant_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-10)
    assert result.balance.coupled_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-10)
    assert result.soil_result.global_balance.interlayer_hto_cancellation_bq_m2 == pytest.approx(0.0, abs=1.0e-12)


def test_composite_json_roundtrip_and_restart_equivalence() -> None:
    integrator = make_integrator()
    initial = make_state()
    first = advance_once(integrator, initial)
    restarted_state = V4SoilRootTFWTOBTState.from_json(first.state.to_json())
    assert restarted_state == first.state

    direct_second = advance_once(integrator, first.state)
    restarted_second = advance_once(integrator, restarted_state)
    assert restarted_second.state == direct_second.state
    assert restarted_second.root_plan == direct_second.root_plan
    assert restarted_second.balance == direct_second.balance


def test_deterministic_repeat_is_exact_for_identical_inputs() -> None:
    integrator = make_integrator()
    state = make_state()
    first = advance_once(integrator, state)
    second = advance_once(integrator, state)
    assert second == first


def test_root_forcing_plant_identity_is_fail_closed() -> None:
    state = make_state()
    wrong = ThreeLayerRootWaterFluxForcingV4(
        plant_identifier="different-plant",
        timestamp=state.timestamp,
        water_uptake_fluxes_m_s=(1.0e-7, 2.0e-7, 1.0e-7),
        provenance=root_provenance(),
    )
    with pytest.raises(V4IntegrationError, match="plant_identifier"):
        advance_once(make_integrator(), state, root=wrong)
