from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path

import pytest

from cteas_ufotri.atmosphere.ufotri_native_process_v4 import (
    KFK5194HTOWashoutMode,
    kfk5194_species_policy,
    transport_straight_segment_reconciled,
)
from cteas_ufotri.atmosphere.ufotri_native_v4 import TritiumAtmosphericForm
from cteas_ufotri.coupling.ht_v4 import GaseousTritiumSpecies
from cteas_ufotri.coupling.ufotri_native_atmos_forcing_v4 import NativeForcingContext
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.leaf_exchange_resistance.resistance import ResistanceChain
from cteas_ufotri.plant.obt_v3 import PlantBiologicalForcing
from cteas_ufotri.plant.root_v4 import (
    RootWaterFluxProvenanceV4,
    ThreeLayerRootWaterFluxForcingV4,
)
from cteas_ufotri.plant.soil_v4 import ThreeLayerSoilForcing
from cteas_ufotri.v4_integration.native_atmosphere_to_dose_v4 import (
    NativeAtmosphereToDoseQualificationError,
    compose_native_atmosphere_replay_input,
)
from cteas_ufotri.v4_integration.replay_input_orchestration import (
    ReplayDomainProvenance,
    V4ReplayIntervalInput,
)
from cteas_ufotri.coupling.atmos_v3 import AtmosphericHTOForcing


UTC = timezone.utc
SPATIAL = "h5-unit-support"


def _load_machine_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "run_ufotri_native_atmosphere_to_dose_qualification_r1.py"
    )
    spec = importlib.util.spec_from_file_location("ufotri_h5_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _forcing_provenance(dt_s: float) -> ForcingProvenance:
    return ForcingProvenance(
        source_id="H5_UNIT",
        source_version="r1",
        artifact_sha256="a" * 64,
        spatial_reference=SPATIAL,
        temporal_resolution_s=dt_s,
    )


def _domain(source_id: str, dt_s: float) -> ReplayDomainProvenance:
    return ReplayDomainProvenance(
        source_id=source_id,
        source_version="r1",
        artifact_sha256="b" * 64,
        spatial_reference=SPATIAL,
        temporal_resolution_s=dt_s,
        source_kind="SYNTHETIC_TEST",
    )


def _template(start: datetime, dt_s: float) -> V4ReplayIntervalInput:
    atmos = AtmosphericHTOForcing(
        timestamp=start,
        location=SPATIAL,
        air_hto_concentration=0.0,
        deposition_flux=0.0,
        temperature=298.15,
        humidity=0.5,
        wind_speed=5.0,
        precipitation=0.0,
        source="H5_TEMPLATE",
        provenance=_forcing_provenance(dt_s),
    )
    return V4ReplayIntervalInput(
        atmospheric_forcing=atmos,
        interval_end=start + timedelta(seconds=dt_s),
        soil_external_forcing=ThreeLayerSoilForcing(timestamp=start),
        soil_external_provenance=_domain("H5_SOIL", dt_s),
        root_forcing=ThreeLayerRootWaterFluxForcingV4(
            plant_identifier="h5-unit-plant",
            timestamp=start,
            water_uptake_fluxes_m_s=(0.0, 0.0, 0.0),
            provenance=RootWaterFluxProvenanceV4(
                source_id="H5_ROOT",
                source_locator="tests/v4/test_ufotri_native_atmosphere_to_dose_qualification_r1.py",
                revision="r1",
                artifact_sha256="c" * 64,
                profile_context="H5_UNIT",
            ),
        ),
        biological_forcing=PlantBiologicalForcing(is_daylight=True),
        biological_provenance=_domain("H5_BIO", dt_s),
        resistance=ResistanceChain.from_components(100.0, 100.0, 800.0),
        equilibrium_air_concentration_bq_m3=0.0,
        leaf_exchange_provenance=_domain("H5_LEAF", dt_s),
    )


def _context(start: datetime, dt_s: float) -> NativeForcingContext:
    return NativeForcingContext(
        start_utc=start,
        end_utc=start + timedelta(seconds=dt_s),
        source_id="H5_UNIT_NATIVE",
        provenance_id="H5_UNIT_PROVENANCE",
        source_version="r1",
        artifact_sha256="d" * 64,
        spatial_support=SPATIAL,
        concentration_sampling_height_m=1.0,
        air_temperature_k=298.15,
        relative_humidity=0.5,
        wind_speed_m_s=5.0,
        precipitation_m_s=0.0,
        creation_time_utc=start,
        quality_flag="H5_UNIT",
    )


def _native(species: TritiumAtmosphericForm, source_bq_s: float):
    policy = kfk5194_species_policy(
        species=species,
        dry_deposition_velocity_m_s=(1.8e-2 if species is TritiumAtmosphericForm.HTO else 5.0e-4),
        precipitation_mm_h=0.0,
        mode=KFK5194HTOWashoutMode.POWER_LAW,
    )
    return transport_straight_segment_reconciled(
        source_bq_s=source_bq_s,
        downwind_m=1000.0,
        crosswind_m=0.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        receptor_height_m=1.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=policy,
    )


def test_h5_machine_gate_passes() -> None:
    result = _load_machine_module().build_result()
    assert result["status"] == "PASS_UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION"
    assert all(result["invariants"].values())
    assert not any(result["forbidden_claims"].values())
    assert result["next_stage_after_clean_closure"] == "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2"


def test_h5_composition_keeps_primary_and_ht_derived_deposition_visible() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    composition = compose_native_atmosphere_replay_input(
        template=_template(start, 3600.0),
        native_hto_result=_native(TritiumAtmosphericForm.HTO, 1.0e8),
        native_ht_result=_native(TritiumAtmosphericForm.HT, 5.0e7),
        context=_context(start, 3600.0),
        gaseous_ht_species=GaseousTritiumSpecies.HT,
    )
    assert composition.ledger.primary_hto_surface_flux_bq_m2_s > 0.0
    assert composition.ledger.ht_derived_hto_surface_flux_bq_m2_s > 0.0
    assert composition.ledger.combined_hto_surface_flux_bq_m2_s == pytest.approx(
        composition.ledger.primary_hto_surface_flux_bq_m2_s
        + composition.ledger.ht_derived_hto_surface_flux_bq_m2_s
    )
    assert composition.replay_input.atmospheric_forcing.deposition_flux == pytest.approx(
        composition.ledger.combined_hto_surface_flux_bq_m2_s
    )
    assert composition.ledger.atmospheric_ht_to_hto_generated_bq_s == 0.0


def test_secondary_air_does_not_create_an_implicit_surface_deposition_term() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    common = dict(
        template=_template(start, 3600.0),
        native_hto_result=_native(TritiumAtmosphericForm.HTO, 1.0e8),
        native_ht_result=_native(TritiumAtmosphericForm.HT, 5.0e7),
        context=_context(start, 3600.0),
    )
    baseline = compose_native_atmosphere_replay_input(**common)
    secondary = compose_native_atmosphere_replay_input(
        **common,
        secondary_hto_air_bq_m3=12.5,
    )
    assert secondary.ledger.combined_hto_air_bq_m3 == pytest.approx(
        baseline.ledger.combined_hto_air_bq_m3 + 12.5
    )
    assert secondary.ledger.combined_hto_surface_flux_bq_m2_s == pytest.approx(
        baseline.ledger.combined_hto_surface_flux_bq_m2_s
    )


def test_crossed_species_and_context_mismatch_fail_closed() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(NativeAtmosphereToDoseQualificationError):
        compose_native_atmosphere_replay_input(
            template=_template(start, 3600.0),
            native_hto_result=_native(TritiumAtmosphericForm.HT, 5.0e7),
            context=_context(start, 3600.0),
        )
    with pytest.raises(NativeAtmosphereToDoseQualificationError):
        compose_native_atmosphere_replay_input(
            template=_template(start, 3600.0),
            native_hto_result=_native(TritiumAtmosphericForm.HTO, 1.0e8),
            context=_context(start, 1800.0),
        )
