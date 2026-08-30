from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path

import pytest

from cteas_ufotri.atmosphere.ufotri_native_v4 import (
    NativePrimaryTransportResult,
    NativeSpeciesPolicy,
    TritiumAtmosphericForm,
    kfk4605_iter_benchmark_policy,
    transport_straight_segment,
)
from cteas_ufotri.coupling.atmos_v3.forcing import AtmosphericHTOForcing
from cteas_ufotri.coupling.ht_v4 import (
    AtmosphericHTForcing,
    GaseousTritiumSpecies,
    HTContractError,
    HTForcingSourceKind,
)
from cteas_ufotri.coupling.ufotri_native_atmos_forcing_v4 import (
    NativeForcingContext,
    UFOTRINativeForcingAdapterError,
    adapt_native_ht_forcing,
    adapt_native_hto_forcing,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _load_machine_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "run_ufotri_native_atmospheric_forcing_adapter_r1.py"
    )
    spec = importlib.util.spec_from_file_location("h3_native_forcing_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _context(*, interval_s: float = 3600.0) -> NativeForcingContext:
    return NativeForcingContext(
        start_utc=T0,
        end_utc=T0 + timedelta(seconds=interval_s),
        source_id="H3_TEST_NATIVE",
        provenance_id="H3_TEST_NATIVE_PROVENANCE",
        source_version="h3-r1",
        artifact_sha256="b" * 64,
        spatial_support="source-relative-receptor-1000m-centreline",
        concentration_sampling_height_m=1.0,
        air_temperature_k=283.15,
        relative_humidity=0.65,
        wind_speed_m_s=5.0,
        precipitation_m_s=0.0,
        creation_time_utc=T0,
    )


def _transport(policy: NativeSpeciesPolicy) -> NativePrimaryTransportResult:
    return transport_straight_segment(
        source_bq_s=1.0e8,
        downwind_m=1000.0,
        crosswind_m=0.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        receptor_height_m=1.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=policy,
    )


def test_machine_gate_passes() -> None:
    result = _load_machine_module().build_result()
    assert result["status"] == "PASS_UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER"
    assert all(result["checks"].values())
    assert not any(result["forbidden_claims"].values())


def test_native_ht_maps_to_e1_with_explicit_native_source_kind_and_then_e2() -> None:
    native = _transport(kfk4605_iter_benchmark_policy(TritiumAtmosphericForm.HT))
    adapted = adapt_native_ht_forcing(
        result=native,
        context=_context(),
        gaseous_species=GaseousTritiumSpecies.HT,
    )

    assert isinstance(adapted.forcing, AtmosphericHTForcing)
    assert adapted.forcing.source_kind is HTForcingSourceKind.UFOTRI_NATIVE
    assert adapted.forcing.air_ht_concentration_bq_m3 == native.air_concentration_bq_m3
    assert (
        adapted.forcing.surface_ht_deposition_flux_bq_m2_s
        == native.dry_surface_flux_bq_m2_s
    )
    assert adapted.soil_boundary.deposited_ht_bq_m2 == pytest.approx(
        native.dry_surface_flux_bq_m2_s * 3600.0
    )
    assert adapted.soil_conversion.generated_hto_bq_m2 == pytest.approx(
        adapted.soil_boundary.deposited_ht_bq_m2
    )
    assert adapted.soil_conversion.residual_ht_bq_m2 == 0.0
    assert adapted.soil_conversion.ledger.activity_residual_bq_m2 == 0.0


def test_native_source_kind_is_not_replay_synthetic_or_cteas_atmos() -> None:
    assert HTForcingSourceKind.UFOTRI_NATIVE.value == "ufotri_native"
    assert HTForcingSourceKind.UFOTRI_NATIVE is not HTForcingSourceKind.REPLAY
    assert HTForcingSourceKind.UFOTRI_NATIVE is not HTForcingSourceKind.SYNTHETIC
    assert HTForcingSourceKind.UFOTRI_NATIVE is not HTForcingSourceKind.REAL_CTEAS_ATMOS


def test_real_cteas_atmos_remains_fail_closed_after_native_extension() -> None:
    with pytest.raises(HTContractError, match="CTEAS-Atmos"):
        AtmosphericHTForcing(
            start_utc=T0,
            end_utc=T0 + timedelta(hours=1),
            species=GaseousTritiumSpecies.HT,
            air_ht_concentration_bq_m3=1.0,
            surface_ht_deposition_flux_bq_m2_s=0.0,
            source_kind=HTForcingSourceKind.REAL_CTEAS_ATMOS,
            source_id="ct",
            provenance_id="ct",
            spatial_support="cell",
            concentration_sampling_height_m=1.0,
        )


def test_native_hto_dry_only_maps_to_existing_p7_forcing_without_ht_alias() -> None:
    native = _transport(
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HTO,
            dry_deposition_velocity_m_s=1.8e-2,
        )
    )
    context = _context()
    adapted = adapt_native_hto_forcing(result=native, context=context)

    assert isinstance(adapted.forcing, AtmosphericHTOForcing)
    assert adapted.forcing.air_hto_concentration == native.air_concentration_bq_m3
    assert adapted.forcing.deposition_flux == native.dry_surface_flux_bq_m2_s
    assert adapted.forcing.source == "UFOTRI_NATIVE"
    assert adapted.forcing.provenance.source_id == context.source_id
    assert adapted.forcing.provenance.spatial_reference == context.spatial_support
    assert adapted.forcing.provenance.temporal_resolution_s == 3600.0
    assert adapted.forcing.metadata is not None
    assert adapted.forcing.metadata.model_name == "UFOTRI_NATIVE_MUSEMET_GAUSSIAN"
    assert native.atmospheric_ht_to_hto_generated_bq_s == 0.0


def test_hto_wet_source_loss_without_local_surface_flux_fails_closed() -> None:
    native = _transport(
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HTO,
            dry_deposition_velocity_m_s=1.8e-2,
            hto_washout_coefficient_s_1=1.0e-4,
        )
    )
    assert native.wet_source_loss_bq_s > 0.0
    with pytest.raises(UFOTRINativeForcingAdapterError, match="explicit local wet surface"):
        adapt_native_hto_forcing(result=native, context=_context())


def test_explicit_hto_wet_surface_flux_is_added_once_and_source_loss_not_relabelled() -> None:
    native = _transport(
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HTO,
            dry_deposition_velocity_m_s=1.8e-2,
            hto_washout_coefficient_s_1=1.0e-4,
        )
    )
    explicit_wet_flux = 2.0e-4
    adapted = adapt_native_hto_forcing(
        result=native,
        context=_context(),
        wet_surface_deposition_flux_bq_m2_s=explicit_wet_flux,
    )
    assert adapted.forcing.deposition_flux == pytest.approx(
        native.dry_surface_flux_bq_m2_s + explicit_wet_flux
    )
    assert adapted.native_wet_source_loss_bq_s == native.wet_source_loss_bq_s
    assert adapted.explicit_wet_surface_flux_bq_m2_s == explicit_wet_flux
    assert not adapted.wet_source_to_surface_spatial_closure_claimed
    assert adapted.ledger.mapped_total_surface_flux_bq_m2_s == pytest.approx(
        adapted.ledger.native_dry_surface_flux_bq_m2_s
        + adapted.ledger.explicit_wet_surface_flux_bq_m2_s
    )


def test_nonzero_wet_surface_flux_is_rejected_if_native_source_has_no_wet_loss() -> None:
    native = _transport(
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HTO,
            dry_deposition_velocity_m_s=1.8e-2,
        )
    )
    with pytest.raises(UFOTRINativeForcingAdapterError, match="wet source loss is zero"):
        adapt_native_hto_forcing(
            result=native,
            context=_context(),
            wet_surface_deposition_flux_bq_m2_s=1.0e-5,
        )


def test_species_specific_adapters_fail_closed_on_crossed_chemical_form() -> None:
    ht_native = _transport(kfk4605_iter_benchmark_policy(TritiumAtmosphericForm.HT))
    hto_native = _transport(
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HTO,
            dry_deposition_velocity_m_s=1.8e-2,
        )
    )
    with pytest.raises(UFOTRINativeForcingAdapterError, match="HTO adapter requires"):
        adapt_native_hto_forcing(result=ht_native, context=_context())
    with pytest.raises(UFOTRINativeForcingAdapterError, match="HT adapter requires"):
        adapt_native_ht_forcing(
            result=hto_native,
            context=_context(),
            gaseous_species=GaseousTritiumSpecies.HT,
        )


def test_atmospheric_ht_to_hto_generation_is_rejected_at_adapter_boundary() -> None:
    invalid = NativePrimaryTransportResult(
        species=TritiumAtmosphericForm.HT,
        air_concentration_bq_m3=1.0,
        dry_surface_flux_bq_m2_s=1.0e-4,
        effective_source_bq_s=10.0,
        dry_source_loss_bq_s=1.0,
        wet_source_loss_bq_s=0.0,
        atmospheric_ht_to_hto_generated_bq_s=0.1,
        source_depletion_residual_bq_s=0.0,
    )
    with pytest.raises(UFOTRINativeForcingAdapterError, match="must not create atmospheric HTO"):
        adapt_native_ht_forcing(
            result=invalid,
            context=_context(),
            gaseous_species=GaseousTritiumSpecies.HT,
        )


def test_context_requires_explicit_valid_interval_units_support_and_provenance() -> None:
    context = _context(interval_s=1800.0)
    assert context.interval_seconds == 1800.0
    assert context.hto_provenance.temporal_resolution_s == 1800.0
    assert context.hto_metadata.time_resolution == 1800.0

    with pytest.raises(UFOTRINativeForcingAdapterError, match="SHA-256"):
        NativeForcingContext(
            start_utc=T0,
            end_utc=T0 + timedelta(hours=1),
            source_id="bad",
            provenance_id="bad",
            source_version="bad",
            artifact_sha256="not-a-digest",
            spatial_support="cell",
            concentration_sampling_height_m=1.0,
            air_temperature_k=283.15,
            relative_humidity=0.5,
            wind_speed_m_s=1.0,
            precipitation_m_s=0.0,
            creation_time_utc=T0,
        )


def test_adapter_api_does_not_own_h4_physics_or_cteas_backend() -> None:
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "cteas_ufotri"
        / "coupling"
        / "ufotri_native_atmos_forcing_v4.py"
    )
    text = module_path.read_text(encoding="utf-8")
    assert "building_wake" not in text
    assert "thermal_lift" not in text
    assert "plume_rise" not in text
    assert "REAL_CTEAS_ATMOS" not in text
