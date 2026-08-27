from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cteas_ufotri.coupling.atmos_v3 import AtmosphericHTOForcing
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.leaf_exchange_resistance.resistance import ResistanceChain
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
    ReplayDomainProvenance,
    SELECTED_OPERATOR_SPLIT,
    V4ReplayInputError,
    V4ReplayInputSystemOrchestrator,
    V4ReplayIntervalInput,
    V4SoilRootTFWTOBTIntegrator,
    V4SoilRootTFWTOBTState,
)


ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc
DT = 3600.0
SPATIAL = "unit-test-common-area"
TEST_HALF_LIFE_S = 1.0e12
TEST_KF_S = 2.0e-5
TEST_KR_S = 5.0e-6


def plant_provenance(*, spatial: str = SPATIAL) -> ForcingProvenance:
    return ForcingProvenance(
        source_id="SYNTHETIC_TEST_ONLY_PLANT",
        source_version="r1",
        artifact_sha256="a" * 64,
        spatial_reference=spatial,
        temporal_resolution_s=DT,
    )


def soil_state_provenance(*, spatial: str = SPATIAL) -> SoilV4Provenance:
    return SoilV4Provenance(
        source_id="SYNTHETIC_TEST_ONLY_SOIL_STATE",
        source_version="r1",
        artifact_sha256="b" * 64,
        spatial_reference=spatial,
        temporal_resolution_s=DT,
    )


def root_provenance() -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="SYNTHETIC_TEST_ONLY_ROOT_QW",
        source_locator="tests/v4/test_v4_replay_input_orchestration_r1.py",
        revision="r1",
        artifact_sha256="c" * 64,
        profile_context="SYNTHETIC_TEST_ONLY_EXPLICIT_Q_W",
    )


def domain_provenance(source_id: str, digest: str, *, spatial: str = SPATIAL, resolution: float = DT) -> ReplayDomainProvenance:
    return ReplayDomainProvenance(
        source_id=source_id,
        source_version="r1",
        artifact_sha256=digest * 64,
        spatial_reference=spatial,
        temporal_resolution_s=resolution,
        source_kind="SYNTHETIC_TEST",
    )


def make_state(
    *,
    timestamp: datetime | None = None,
    tfwt_inventory: float = 2.0,
    obt_inventory: float = 1.0,
    spatial: str = SPATIAL,
) -> V4SoilRootTFWTOBTState:
    time = timestamp or datetime(2026, 1, 1, tzinfo=UTC)
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=time,
        provenance=soil_state_provenance(spatial=spatial),
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        tfwt_inventory_bq_m2=tfwt_inventory,
        water_content_kg_m2=5.0,
        time=time,
        provenance=plant_provenance(spatial=spatial),
        area_basis="soil_surface_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        obt_inventory_bq_m2=obt_inventory,
        plant_mass_kg_m2=2.0,
        timestamp=time,
        provenance=plant_provenance(spatial=spatial),
        area_basis="soil_surface_area",
    )
    return V4SoilRootTFWTOBTState(soil_state=soil, tfwt_state=tfwt, obt_state=obt)


def resistance() -> ResistanceChain:
    return ResistanceChain.from_components(100.0, 100.0, 800.0)


def bio() -> PlantBiologicalForcing:
    return PlantBiologicalForcing(is_daylight=True)


def root_forcing(timestamp: datetime, fluxes: tuple[float, float, float] = (1.0e-7, 2.0e-7, 1.0e-7)) -> ThreeLayerRootWaterFluxForcingV4:
    return ThreeLayerRootWaterFluxForcingV4(
        plant_identifier="synthetic-soybean",
        timestamp=timestamp,
        water_uptake_fluxes_m_s=fluxes,
        provenance=root_provenance(),
    )


def atmos(
    timestamp: datetime,
    *,
    air: float,
    deposition: float = 0.0,
    precipitation: float = 0.0,
    spatial: str = SPATIAL,
) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        timestamp=timestamp,
        location="synthetic-common-support",
        air_hto_concentration=air,
        deposition_flux=deposition,
        temperature=298.15,
        humidity=0.55,
        wind_speed=2.0,
        precipitation=precipitation,
        source="SYNTHETIC_TEST_ONLY_REPLAY",
        provenance=plant_provenance(spatial=spatial),
    )


def make_input(
    timestamp: datetime,
    *,
    air: float = 0.5,
    equilibrium: float = 0.5,
    deposition: float = 0.0,
    precipitation: float = 0.0,
    soil: ThreeLayerSoilForcing | None = None,
    root: ThreeLayerRootWaterFluxForcingV4 | None = None,
    spatial: str = SPATIAL,
) -> V4ReplayIntervalInput:
    return V4ReplayIntervalInput(
        atmospheric_forcing=atmos(
            timestamp,
            air=air,
            deposition=deposition,
            precipitation=precipitation,
            spatial=spatial,
        ),
        interval_end=timestamp + timedelta(seconds=DT),
        soil_external_forcing=soil or ThreeLayerSoilForcing(timestamp=timestamp),
        soil_external_provenance=domain_provenance("SYNTHETIC_SOIL_EXTERNAL", "d", spatial=spatial),
        root_forcing=root or root_forcing(timestamp),
        biological_forcing=bio(),
        biological_provenance=domain_provenance("SYNTHETIC_BIOLOGICAL", "e", spatial=spatial),
        resistance=resistance(),
        equilibrium_air_concentration_bq_m3=equilibrium,
        leaf_exchange_provenance=domain_provenance("SYNTHETIC_LEAF_PARAMETERS", "f", spatial=spatial),
    )


def make_orchestrator() -> V4ReplayInputSystemOrchestrator:
    return V4ReplayInputSystemOrchestrator(
        soil_solver=ThreeLayerSoilStorageSolver(tritium_half_life_s=TEST_HALF_LIFE_S),
        obt_solver=OBTSolver(kf_s=TEST_KF_S, kr_s=TEST_KR_S),
    )


def make_reference() -> V4SoilRootTFWTOBTIntegrator:
    return V4SoilRootTFWTOBTIntegrator(
        soil_solver=ThreeLayerSoilStorageSolver(tritium_half_life_s=TEST_HALF_LIFE_S),
        obt_solver=OBTSolver(kf_s=TEST_KF_S, kr_s=TEST_KR_S),
    )


def test_new_orchestration_is_opt_in_and_does_not_reverse_import_into_v3_or_frozen_core() -> None:
    assert SELECTED_OPERATOR_SPLIT == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    replay_source = (ROOT / "src/cteas_ufotri/v4_integration/replay_input_orchestration.py").read_text(encoding="utf-8")
    frozen_source = (ROOT / "src/cteas_ufotri/v4_integration/soil_root_tfwt_obt.py").read_text(encoding="utf-8")
    assert "v3_pipeline" not in replay_source
    assert "replay_input_orchestration" not in frozen_source
    for path in (ROOT / "src/cteas_ufotri/v3_pipeline").glob("*.py"):
        assert "replay_input_orchestration" not in path.read_text(encoding="utf-8")


def test_zero_leaf_exchange_is_exactly_equivalent_to_frozen_four_module_integrator() -> None:
    state = make_state()
    base_soil = ThreeLayerSoilForcing(timestamp=state.timestamp)
    root = root_forcing(state.timestamp)
    biological = bio()

    reference = make_reference().advance(
        state,
        soil_forcing=base_soil,
        root_forcing=root,
        biological_forcing=biological,
        interval_seconds=DT,
    )
    replay = V4ReplayIntervalInput(
        atmospheric_forcing=atmos(state.timestamp, air=0.5, deposition=0.0),
        interval_end=state.timestamp + timedelta(seconds=DT),
        soil_external_forcing=base_soil,
        soil_external_provenance=domain_provenance("SYNTHETIC_SOIL_EXTERNAL", "d"),
        root_forcing=root,
        biological_forcing=biological,
        biological_provenance=domain_provenance("SYNTHETIC_BIOLOGICAL", "e"),
        resistance=resistance(),
        equilibrium_air_concentration_bq_m3=0.5,
        leaf_exchange_provenance=domain_provenance("SYNTHETIC_LEAF_PARAMETERS", "f"),
    )
    result = make_orchestrator().advance(state, replay)

    assert result.leaf_exchange_flux.air_to_leaf_flux_bq_m2_s == 0.0
    assert result.balance.leaf_exchange_transfer_bq_m2 == 0.0
    assert result.state == reference.state
    assert result.root_plan == reference.root_plan
    assert result.applied_soil_forcing == reference.applied_soil_forcing
    assert result.soil_result == reference.soil_result
    assert result.obt_result == reference.obt_result
    assert result.balance.soil_root_water_identity_residual_m == reference.balance.soil_root_water_identity_residual_m
    assert result.balance.soil_root_hto_identity_residual_bq_m2 == reference.balance.soil_root_hto_identity_residual_bq_m2
    assert result.balance.plant_residual_bq_m2 == reference.balance.plant_residual_bq_m2
    assert result.balance.coupled_residual_bq_m2 == reference.balance.coupled_residual_bq_m2


def test_same_interval_leaf_exchange_is_seen_by_obt_while_root_gain_remains_post_obt() -> None:
    state = make_state()
    result = make_orchestrator().advance(
        state,
        make_input(state.timestamp, air=1.5, equilibrium=0.5),
    )
    reference = make_reference().advance(
        state,
        soil_forcing=ThreeLayerSoilForcing(timestamp=state.timestamp),
        root_forcing=root_forcing(state.timestamp),
        biological_forcing=bio(),
        interval_seconds=DT,
    )

    assert result.balance.leaf_exchange_transfer_bq_m2 > 0.0
    assert result.tfwt_leaf_result.state.inventory() > state.tfwt_state.inventory()
    assert result.obt_result.balance.obt_formation_bq_m2 > reference.obt_result.balance.obt_formation_bq_m2
    expected_endpoint_tfwt = (
        result.tfwt_leaf_result.state.inventory()
        - result.obt_result.balance.tfwt_loss_bq_m2
        + result.root_plan.total_hto_transfer_bq_m2
    )
    assert result.state.tfwt_state.inventory() == pytest.approx(expected_endpoint_tfwt, abs=1.0e-12)
    assert result.balance.plant_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-10)
    assert result.balance.coupled_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-10)


def test_signed_leaf_reemission_is_external_loss_and_still_closes_balance() -> None:
    state = make_state(tfwt_inventory=3.0)
    result = make_orchestrator().advance(
        state,
        make_input(state.timestamp, air=0.4, equilibrium=0.5),
    )
    assert result.balance.leaf_exchange_transfer_bq_m2 < 0.0
    assert result.tfwt_leaf_result.state.inventory() < state.tfwt_state.inventory()
    assert result.balance.plant_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-10)
    assert result.balance.coupled_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-10)


def test_atmos_deposition_maps_only_to_l1_surface_boundary_and_precipitation_is_not_infiltration() -> None:
    state = make_state()
    replay = make_input(
        state.timestamp,
        deposition=2.0e-4,
        precipitation=1.0e-6,
        soil=ThreeLayerSoilForcing(timestamp=state.timestamp),
    )
    result = make_orchestrator().advance(state, replay)

    assert result.applied_soil_forcing.surface_deposition_flux_bq_m2_s == 2.0e-4
    assert result.applied_soil_forcing.surface_water_input_m_s == 0.0
    assert result.applied_soil_forcing.l1_l2_water_flux_m_s == 0.0
    assert result.applied_soil_forcing.l2_l3_water_flux_m_s == 0.0
    assert result.soil_result.global_balance.external_hto_input_bq_m2 == pytest.approx(2.0e-4 * DT, abs=1.0e-12)
    assert result.balance.coupled_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-10)


def test_explicit_non_atmos_soil_transport_is_preserved_without_hidden_derivation() -> None:
    state = make_state()
    base_soil = ThreeLayerSoilForcing(
        timestamp=state.timestamp,
        surface_water_input_m_s=2.0e-8,
        surface_water_loss_m_s=1.0e-8,
        l1_l2_water_flux_m_s=1.0e-8,
        l1_l2_hto_flux_bq_m2_s=1.0e-5,
        l2_l3_water_flux_m_s=-5.0e-9,
        l2_l3_hto_flux_bq_m2_s=-5.0e-6,
        lower_boundary_water_loss_m_s=2.0e-9,
        lower_boundary_hto_loss_bq_m2_s=1.0e-5,
        surface_reemission_hto_loss_bq_m2_s=5.0e-6,
    )
    result = make_orchestrator().advance(
        state,
        make_input(state.timestamp, deposition=2.0e-4, soil=base_soil),
    )
    assert result.applied_soil_forcing.surface_water_input_m_s == base_soil.surface_water_input_m_s
    assert result.applied_soil_forcing.l1_l2_hto_flux_bq_m2_s == base_soil.l1_l2_hto_flux_bq_m2_s
    assert result.applied_soil_forcing.l2_l3_hto_flux_bq_m2_s == base_soil.l2_l3_hto_flux_bq_m2_s
    assert result.applied_soil_forcing.lower_boundary_hto_loss_bq_m2_s == base_soil.lower_boundary_hto_loss_bq_m2_s
    assert result.applied_soil_forcing.surface_reemission_hto_loss_bq_m2_s == base_soil.surface_reemission_hto_loss_bq_m2_s
    assert result.balance.coupled_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-10)


def test_input_rejects_double_owned_surface_deposition_and_root_slots() -> None:
    time = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(V4ReplayInputError, match="exclusively owns surface deposition"):
        make_input(
            time,
            soil=ThreeLayerSoilForcing(timestamp=time, surface_deposition_flux_bq_m2_s=1.0e-6),
        )
    with pytest.raises(V4ReplayInputError, match="root_v4 owns the root plan"):
        make_input(
            time,
            soil=ThreeLayerSoilForcing(timestamp=time, root_water_extraction_m_s=(1.0e-8, 0.0, 0.0)),
        )


def test_interval_and_spatial_alignment_fail_closed_without_resampling_or_reconciliation() -> None:
    time = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(V4ReplayInputError, match="interval length"):
        V4ReplayIntervalInput(
            atmospheric_forcing=atmos(time, air=0.5),
            interval_end=time + timedelta(seconds=1800.0),
            soil_external_forcing=ThreeLayerSoilForcing(timestamp=time),
            soil_external_provenance=domain_provenance("SYNTHETIC_SOIL_EXTERNAL", "d"),
            root_forcing=root_forcing(time),
            biological_forcing=bio(),
            biological_provenance=domain_provenance("SYNTHETIC_BIOLOGICAL", "e"),
            resistance=resistance(),
            equilibrium_air_concentration_bq_m3=0.5,
            leaf_exchange_provenance=domain_provenance("SYNTHETIC_LEAF_PARAMETERS", "f"),
        )

    with pytest.raises(V4ReplayInputError, match="spatial_reference"):
        V4ReplayIntervalInput(
            atmospheric_forcing=atmos(time, air=0.5),
            interval_end=time + timedelta(seconds=DT),
            soil_external_forcing=ThreeLayerSoilForcing(timestamp=time),
            soil_external_provenance=domain_provenance("SYNTHETIC_SOIL_EXTERNAL", "d", spatial="different-support"),
            root_forcing=root_forcing(time),
            biological_forcing=bio(),
            biological_provenance=domain_provenance("SYNTHETIC_BIOLOGICAL", "e"),
            resistance=resistance(),
            equilibrium_air_concentration_bq_m3=0.5,
            leaf_exchange_provenance=domain_provenance("SYNTHETIC_LEAF_PARAMETERS", "f"),
        )


def test_state_spatial_support_must_match_replay_support() -> None:
    state = make_state(spatial="state-only-support")
    replay = make_input(state.timestamp, spatial=SPATIAL)
    with pytest.raises(V4ReplayInputError, match="state spatial_reference"):
        make_orchestrator().advance(state, replay)


def test_root_provenance_remains_independent_and_is_not_replaced_by_atmos_provenance() -> None:
    state = make_state()
    replay = make_input(state.timestamp)
    result = make_orchestrator().advance(state, replay)
    assert replay.root_forcing.provenance.source_id == "SYNTHETIC_TEST_ONLY_ROOT_QW"
    assert replay.atmospheric_forcing.provenance.source_id == "SYNTHETIC_TEST_ONLY_PLANT"
    assert replay.root_forcing.provenance is not replay.atmospheric_forcing.provenance
    assert result.root_plan.provenance == replay.root_forcing.provenance


def test_restart_and_deterministic_repeat_use_existing_composite_state_serialization() -> None:
    orchestrator = make_orchestrator()
    initial = make_state()
    replay0 = make_input(initial.timestamp, air=1.0, equilibrium=0.5, deposition=1.0e-4)
    first_a = orchestrator.advance(initial, replay0)
    first_b = orchestrator.advance(initial, replay0)
    assert first_b == first_a

    restarted = V4SoilRootTFWTOBTState.from_json(first_a.state.to_json())
    replay1 = make_input(restarted.timestamp, air=0.8, equilibrium=0.5, deposition=5.0e-5)
    direct_second = orchestrator.advance(first_a.state, replay1)
    restarted_second = orchestrator.advance(restarted, replay1)
    assert restarted_second == direct_second


def test_area_conversion_and_real_atmos_binding_are_not_part_of_r1() -> None:
    time = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(V4ReplayInputError, match="no area conversion"):
        replace(make_input(time), area_basis="plant_area")
    source = (ROOT / "src/cteas_ufotri/v4_integration/replay_input_orchestration.py").read_text(encoding="utf-8")
    assert "CTEAS-Atmos" in source
    assert "Richards" not in source
    assert "dynamic stom" in source
    assert "food" in source
