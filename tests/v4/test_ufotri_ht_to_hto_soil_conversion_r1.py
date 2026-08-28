from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path

import pytest

from cteas_ufotri.coupling.ht_to_hto_soil_v4 import (
    HT_TO_HTO_SOIL_CONVERSION_SEMANTICS,
    HTToHTOSoilConversionError,
    HTToHTOSoilConversionResult,
    convert_deposited_ht_to_soil_hto,
    project_ht_derived_hto_into_soil_forcing,
)
from cteas_ufotri.coupling.ht_v4 import (
    AtmosphericHTForcing,
    GaseousTritiumSpecies,
    HTForcingSourceKind,
    ht_manual_evidence_profile,
)
from cteas_ufotri.plant.soil_v4.soil_solver import (
    ThreeLayerSoilForcing,
    ThreeLayerSoilStorageSolver,
)
from cteas_ufotri.plant.soil_v4.soil_state import (
    SoilV4Provenance,
    ThreeLayerSoilState,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
TRITIUM_HALF_LIFE_S = 12.32 * 365.25 * 86400.0


def _ht_forcing(
    *,
    start: datetime = T0,
    duration_s: float = 3600.0,
    flux: float = 2.0e-4,
    species: GaseousTritiumSpecies = GaseousTritiumSpecies.HT,
    source_kind: HTForcingSourceKind = HTForcingSourceKind.SYNTHETIC,
) -> AtmosphericHTForcing:
    return AtmosphericHTForcing(
        start_utc=start,
        end_utc=start + timedelta(seconds=duration_s),
        species=species,
        air_ht_concentration_bq_m3=100.0,
        surface_ht_deposition_flux_bq_m2_s=flux,
        source_kind=source_kind,
        source_id="E2_TEST_HT",
        provenance_id="E2_TEST_HT_PROVENANCE",
        spatial_support="synthetic_cell_0",
        concentration_sampling_height_m=1.5,
    )


def _conversion(**kwargs):
    forcing = _ht_forcing(**kwargs)
    return convert_deposited_ht_to_soil_hto(
        forcing.to_soil_deposition_boundary()
    )


def _load_machine_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "run_ufotri_ht_to_hto_soil_conversion_r1.py"
    )
    spec = importlib.util.spec_from_file_location("e2_ht_conversion_machine_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _state() -> ThreeLayerSoilState:
    provenance = SoilV4Provenance(
        source_id="E2_TEST_SOIL",
        source_version="r1",
        artifact_sha256="b" * 64,
        spatial_reference="synthetic_cell_0",
        temporal_resolution_s=3600.0,
    )
    return ThreeLayerSoilState.from_inventories(
        soil_identifier="E2_TEST_SOIL",
        water_inventories_m=(0.05, 0.10, 0.15),
        hto_inventories_bq_m2=(0.0, 0.0, 0.0),
        timestamp=T0,
        provenance=provenance,
    )


def test_e2_machine_gate_passes() -> None:
    result = _load_machine_module().build_result()
    assert result["status"] == "PASS_UFOTRI_HT_TO_HTO_SOIL_CONVERSION"
    assert all(result["conversion"]["conversion_gates"].values())
    assert all(result["projection"]["projection_gates"].values())
    assert all(result["manual_evidence"]["manual_evidence_gates"].values())
    assert not any(result["hard_boundaries"].values())


def test_eq1_eq2_boundary_is_one_to_one_activity_conversion() -> None:
    conversion = _conversion(duration_s=1800.0, flux=3.0e-4)
    assert conversion.conversion_semantics == HT_TO_HTO_SOIL_CONVERSION_SEMANTICS
    assert conversion.input_ht_bq_m2 == pytest.approx(0.54)
    assert conversion.generated_hto_bq_m2 == pytest.approx(0.54)
    assert conversion.residual_ht_bq_m2 == 0.0
    assert conversion.conversion_fraction == 1.0
    assert conversion.generated_hto_flux_bq_m2_s == pytest.approx(3.0e-4)
    assert conversion.ledger.activity_residual_bq_m2 == pytest.approx(0.0)


@pytest.mark.parametrize(
    "species",
    [GaseousTritiumSpecies.HT, GaseousTritiumSpecies.T2],
)
def test_ht_and_t2_preserve_species_provenance_while_activity_is_conserved(
    species: GaseousTritiumSpecies,
) -> None:
    conversion = _conversion(species=species)
    assert conversion.species is species
    assert conversion.provenance_id == "E2_TEST_HT_PROVENANCE"
    assert conversion.spatial_support == "synthetic_cell_0"
    assert conversion.input_ht_bq_m2 == pytest.approx(
        conversion.generated_hto_bq_m2
    )


def test_one_hour_and_four_quarter_hour_conversion_are_additive() -> None:
    whole = _conversion(duration_s=3600.0, flux=2.0e-4)
    parts = [
        _conversion(
            start=T0 + timedelta(minutes=15 * index),
            duration_s=900.0,
            flux=2.0e-4,
            source_kind=HTForcingSourceKind.REPLAY,
        )
        for index in range(4)
    ]
    assert sum(item.generated_hto_bq_m2 for item in parts) == pytest.approx(
        whole.generated_hto_bq_m2,
        rel=0.0,
        abs=1.0e-15,
    )


def test_projection_adds_ht_derived_hto_without_overwriting_primary_hto() -> None:
    conversion = _conversion()
    base = ThreeLayerSoilForcing(
        timestamp=T0,
        surface_water_input_m_s=1.0e-8,
        surface_deposition_flux_bq_m2_s=3.0e-4,
        lower_boundary_water_loss_m_s=2.0e-9,
    )
    projection = project_ht_derived_hto_into_soil_forcing(
        base_forcing=base,
        conversion=conversion,
        interval_seconds=3600.0,
    )
    assert projection.primary_hto_surface_flux_bq_m2_s == pytest.approx(3.0e-4)
    assert projection.ht_derived_hto_surface_flux_bq_m2_s == pytest.approx(2.0e-4)
    assert projection.combined_hto_surface_flux_bq_m2_s == pytest.approx(5.0e-4)
    assert projection.forcing.surface_deposition_flux_bq_m2_s == pytest.approx(5.0e-4)
    assert projection.forcing.surface_water_input_m_s == base.surface_water_input_m_s
    assert (
        projection.forcing.lower_boundary_water_loss_m_s
        == base.lower_boundary_water_loss_m_s
    )
    assert projection.ht_provenance_id == conversion.provenance_id


def test_projected_ht_derived_hto_enters_existing_l1_inventory_and_global_ledger() -> None:
    conversion = _conversion()
    base = ThreeLayerSoilForcing(
        timestamp=T0,
        surface_deposition_flux_bq_m2_s=3.0e-4,
    )
    projection = project_ht_derived_hto_into_soil_forcing(
        base_forcing=base,
        conversion=conversion,
        interval_seconds=3600.0,
    )
    result = ThreeLayerSoilStorageSolver(
        tritium_half_life_s=TRITIUM_HALF_LIFE_S
    ).advance(_state(), projection.forcing, 3600.0)

    expected_external = (3.0e-4 + 2.0e-4) * 3600.0
    assert result.global_balance.external_hto_input_bq_m2 == pytest.approx(
        expected_external
    )
    assert result.state.layers[0].hto_inventory_bq_m2 > 0.0
    assert result.state.layers[1].hto_inventory_bq_m2 == 0.0
    assert result.state.layers[2].hto_inventory_bq_m2 == 0.0
    assert result.global_balance.hto_residual_bq_m2 == pytest.approx(
        0.0,
        abs=1.0e-10,
    )


def test_zero_ht_deposition_maps_to_zero_generated_hto() -> None:
    conversion = _conversion(flux=0.0)
    assert conversion.input_ht_bq_m2 == 0.0
    assert conversion.generated_hto_bq_m2 == 0.0
    assert conversion.generated_hto_flux_bq_m2_s == 0.0
    assert conversion.ledger.activity_residual_bq_m2 == 0.0


def test_manual_deposition_conditions_remain_upstream_not_new_e2_kinetics() -> None:
    evidence = ht_manual_evidence_profile()
    conversion = _conversion()
    assert evidence.ht_deposition_depends_on_soil_type_and_moisture
    assert evidence.deposited_ht_rapidly_converts_via_microorganisms
    assert evidence.only_transformed_ht_remains_in_soil
    assert conversion.generated_hto_flux_bq_m2_s == pytest.approx(
        _ht_forcing().surface_ht_deposition_flux_bq_m2_s
    )
    assert not hasattr(conversion, "microbial_half_life_s")
    assert not hasattr(conversion, "oxidation_rate_s_1")


def test_e2_does_not_apply_atmospheric_oxidation_reemission_or_production_defaults() -> None:
    conversion = _conversion()
    assert not conversion.atmospheric_ht_oxidation_applied
    assert not conversion.secondary_hto_reemission_generated
    assert not conversion.production_parameter_activation


def test_manual_path_refuses_partial_conversion_or_retained_soil_ht_pool() -> None:
    with pytest.raises(HTToHTOSoilConversionError, match="complete retained-HT"):
        HTToHTOSoilConversionResult(
            start_utc=T0,
            end_utc=T0 + timedelta(hours=1),
            species=GaseousTritiumSpecies.HT,
            source_kind=HTForcingSourceKind.SYNTHETIC,
            provenance_id="test",
            spatial_support="cell",
            input_ht_bq_m2=1.0,
            generated_hto_bq_m2=0.8,
            residual_ht_bq_m2=0.2,
            generated_hto_flux_bq_m2_s=0.8 / 3600.0,
        )


def test_manual_path_refuses_invented_conversion_fraction() -> None:
    with pytest.raises(HTToHTOSoilConversionError, match="fraction is fixed to 1"):
        HTToHTOSoilConversionResult(
            start_utc=T0,
            end_utc=T0 + timedelta(hours=1),
            species=GaseousTritiumSpecies.HT,
            source_kind=HTForcingSourceKind.SYNTHETIC,
            provenance_id="test",
            spatial_support="cell",
            input_ht_bq_m2=1.0,
            generated_hto_bq_m2=1.0,
            residual_ht_bq_m2=0.0,
            generated_hto_flux_bq_m2_s=1.0 / 3600.0,
            conversion_fraction=0.5,
        )


def test_projection_fails_closed_on_interval_mismatch() -> None:
    with pytest.raises(HTToHTOSoilConversionError, match="interval_seconds"):
        project_ht_derived_hto_into_soil_forcing(
            base_forcing=ThreeLayerSoilForcing(timestamp=T0),
            conversion=_conversion(),
            interval_seconds=1800.0,
        )


def test_projection_fails_closed_on_timestamp_mismatch() -> None:
    with pytest.raises(HTToHTOSoilConversionError, match="timestamp"):
        project_ht_derived_hto_into_soil_forcing(
            base_forcing=ThreeLayerSoilForcing(
                timestamp=T0 + timedelta(hours=1)
            ),
            conversion=_conversion(),
            interval_seconds=3600.0,
        )


def test_wrong_boundary_type_fails_closed() -> None:
    with pytest.raises(HTToHTOSoilConversionError, match="reviewed E1"):
        convert_deposited_ht_to_soil_hto(object())  # type: ignore[arg-type]
