from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
import math
from pathlib import Path

import pytest

from cteas_ufotri.coupling.atmos_v3.forcing import AtmosphericHTOForcing
from cteas_ufotri.coupling.ht_v4 import (
    AIR_HT_CONCENTRATION_UNIT,
    HT_SURFACE_DEPOSITION_AMOUNT_UNIT,
    HT_SURFACE_DEPOSITION_FLUX_UNIT,
    AtmosphericHTForcing,
    GaseousTritiumSpecies,
    HTContractError,
    HTForcingSourceKind,
    HTSoilDepositionBoundary,
    ht_branch_ownership,
    ht_manual_evidence_profile,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _forcing(
    *,
    duration_s: float = 3600.0,
    concentration: float = 100.0,
    deposition_flux: float = 2.0e-4,
    species: GaseousTritiumSpecies = GaseousTritiumSpecies.HT,
    source_kind: HTForcingSourceKind = HTForcingSourceKind.SYNTHETIC,
) -> AtmosphericHTForcing:
    return AtmosphericHTForcing(
        start_utc=T0,
        end_utc=T0 + timedelta(seconds=duration_s),
        species=species,
        air_ht_concentration_bq_m3=concentration,
        surface_ht_deposition_flux_bq_m2_s=deposition_flux,
        source_kind=source_kind,
        source_id="E1_SYNTHETIC",
        provenance_id="E1_SYNTHETIC_PROVENANCE",
        spatial_support="synthetic_cell_0",
        concentration_sampling_height_m=1.5,
    )


def _load_machine_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "run_ufotri_ht_branch_reconciliation_r1.py"
    )
    spec = importlib.util.spec_from_file_location("e1_ht_machine_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_e1_machine_gate_passes() -> None:
    result = _load_machine_module().build_result()
    assert result["status"] == "PASS_UFOTRI_HT_BRANCH_RECONCILIATION"
    assert all(result["contract"]["contract_gates"].values())
    assert all(result["manual_evidence"]["manual_evidence_gates"].values())
    assert not any(result["hard_boundaries"].values())


def test_ht_and_t2_are_explicit_manual_species() -> None:
    assert _forcing(species=GaseousTritiumSpecies.HT).species.value == "HT"
    assert _forcing(species=GaseousTritiumSpecies.T2).species.value == "T2"


@pytest.mark.parametrize("bad_species", ["HTO", "TOTAL_TRITIUM", "DT", ""])
def test_unspecified_or_nonmanual_species_fail_closed(bad_species: str) -> None:
    with pytest.raises(HTContractError, match="species"):
        AtmosphericHTForcing(
            start_utc=T0,
            end_utc=T0 + timedelta(hours=1),
            species=bad_species,  # type: ignore[arg-type]
            air_ht_concentration_bq_m3=1.0,
            surface_ht_deposition_flux_bq_m2_s=0.0,
            source_kind=HTForcingSourceKind.SYNTHETIC,
            source_id="bad",
            provenance_id="bad",
            spatial_support="cell",
            concentration_sampling_height_m=1.5,
        )


def test_ht_units_are_distinct_and_exact() -> None:
    forcing = _forcing()
    assert forcing.concentration_unit == AIR_HT_CONCENTRATION_UNIT == "Bq m-3"
    assert (
        forcing.deposition_flux_unit
        == HT_SURFACE_DEPOSITION_FLUX_UNIT
        == "Bq m-2 s-1"
    )
    boundary = forcing.to_soil_deposition_boundary()
    assert boundary.amount_unit == HT_SURFACE_DEPOSITION_AMOUNT_UNIT == "Bq m-2"


def test_surface_flux_integrates_to_ht_amount_without_hto_conversion() -> None:
    forcing = _forcing(duration_s=1800.0, deposition_flux=3.0e-4)
    boundary = forcing.to_soil_deposition_boundary()
    assert boundary.deposited_ht_bq_m2 == pytest.approx(0.54)
    assert boundary.converted_to_hto_bq_m2 == 0.0
    assert boundary.species is GaseousTritiumSpecies.HT
    assert not hasattr(boundary, "deposited_hto_bq_m2")


def test_partitioned_flux_integration_matches_whole_interval() -> None:
    whole = _forcing(duration_s=3600.0, deposition_flux=2.0e-4)
    whole_amount = whole.to_soil_deposition_boundary().deposited_ht_bq_m2

    total = 0.0
    for index in range(4):
        record = AtmosphericHTForcing(
            start_utc=T0 + timedelta(minutes=15 * index),
            end_utc=T0 + timedelta(minutes=15 * (index + 1)),
            species=GaseousTritiumSpecies.HT,
            air_ht_concentration_bq_m3=100.0,
            surface_ht_deposition_flux_bq_m2_s=2.0e-4,
            source_kind=HTForcingSourceKind.REPLAY,
            source_id="partition",
            provenance_id="partition",
            spatial_support="cell",
            concentration_sampling_height_m=1.5,
        )
        total += record.to_soil_deposition_boundary().deposited_ht_bq_m2

    assert total == pytest.approx(whole_amount, rel=0.0, abs=1.0e-15)


def test_real_cteas_atmos_binding_fails_closed_in_e1() -> None:
    with pytest.raises(HTContractError, match="deferred to E4"):
        _forcing(source_kind=HTForcingSourceKind.REAL_CTEAS_ATMOS)


def test_existing_hto_forcing_remains_separate_type() -> None:
    assert AtmosphericHTForcing is not AtmosphericHTOForcing
    ht_names = set(AtmosphericHTForcing.__dataclass_fields__)
    hto_names = set(AtmosphericHTOForcing.__dataclass_fields__)
    assert "air_ht_concentration_bq_m3" in ht_names
    assert "air_hto_concentration" in hto_names
    assert "air_ht_concentration_bq_m3" not in hto_names
    assert "air_hto_concentration" not in ht_names


def test_manual_benchmark_evidence_is_visible_but_not_activated() -> None:
    p = ht_manual_evidence_profile()
    assert p.benchmark_ht_dry_deposition_velocity_cm_s == 0.05
    assert p.benchmark_ht_dry_deposition_velocity_m_s == pytest.approx(5.0e-4)
    assert p.benchmark_air_oxidation_fraction_d_1 == 0.005
    assert p.benchmark_air_oxidation_rate_s_1 == pytest.approx(0.005 / 86400.0)
    assert p.benchmark_ht_soil_diffusion_cm2_s == 5.0e-2
    assert p.benchmark_ht_soil_diffusion_m2_s == pytest.approx(5.0e-6)
    assert p.benchmark_hto_dry_deposition_velocity_cm_s == 1.8
    assert p.benchmark_hto_soil_diffusion_cm2_s == 2.0e-5
    assert p.ht_deposition_depends_on_soil_type_and_moisture
    assert p.deposited_ht_rapidly_converts_via_microorganisms
    assert p.only_transformed_ht_remains_in_soil
    assert not p.atmospheric_oxidation_owned_by_e1
    assert not p.soil_conversion_owned_by_e1
    assert not p.production_parameter_activation


def test_stage_ownership_is_machine_readable() -> None:
    ownership = ht_branch_ownership()
    assert ownership.e1_contract_and_mapping
    assert not ownership.e1_ht_to_hto_soil_conversion
    assert not ownership.e1_secondary_hto_reemission
    assert not ownership.e1_real_atmos_binding
    assert ownership.e2_owns_ht_to_hto_soil_conversion
    assert ownership.e3_owns_ht_derived_hto_reemission
    assert ownership.e4_owns_real_ht_atmos_binding
    assert not ownership.hto_forcing_reused_for_ht


@pytest.mark.parametrize(
    "kwargs",
    [
        {"air_ht_concentration_bq_m3": -1.0},
        {"air_ht_concentration_bq_m3": math.nan},
        {"surface_ht_deposition_flux_bq_m2_s": -1.0},
        {"surface_ht_deposition_flux_bq_m2_s": math.inf},
        {"concentration_sampling_height_m": -1.0},
    ],
)
def test_numeric_inputs_fail_closed(kwargs: dict[str, float]) -> None:
    values = dict(
        start_utc=T0,
        end_utc=T0 + timedelta(hours=1),
        species=GaseousTritiumSpecies.HT,
        air_ht_concentration_bq_m3=1.0,
        surface_ht_deposition_flux_bq_m2_s=0.0,
        source_kind=HTForcingSourceKind.SYNTHETIC,
        source_id="test",
        provenance_id="test",
        spatial_support="cell",
        concentration_sampling_height_m=1.5,
    )
    values.update(kwargs)
    with pytest.raises(HTContractError):
        AtmosphericHTForcing(**values)


def test_non_utc_and_invalid_intervals_fail_closed() -> None:
    local = timezone(timedelta(hours=9))
    with pytest.raises(HTContractError, match="UTC"):
        AtmosphericHTForcing(
            start_utc=datetime(2026, 1, 1, tzinfo=local),
            end_utc=datetime(2026, 1, 1, 1, tzinfo=local),
            species=GaseousTritiumSpecies.HT,
            air_ht_concentration_bq_m3=1.0,
            surface_ht_deposition_flux_bq_m2_s=0.0,
            source_kind=HTForcingSourceKind.SYNTHETIC,
            source_id="test",
            provenance_id="test",
            spatial_support="cell",
            concentration_sampling_height_m=1.5,
        )

    with pytest.raises(HTContractError, match="later"):
        _forcing(duration_s=0.0)


def test_wrong_units_fail_closed() -> None:
    with pytest.raises(HTContractError, match="concentration_unit"):
        AtmosphericHTForcing(
            start_utc=T0,
            end_utc=T0 + timedelta(hours=1),
            species=GaseousTritiumSpecies.HT,
            air_ht_concentration_bq_m3=1.0,
            surface_ht_deposition_flux_bq_m2_s=0.0,
            source_kind=HTForcingSourceKind.SYNTHETIC,
            source_id="test",
            provenance_id="test",
            spatial_support="cell",
            concentration_sampling_height_m=1.5,
            concentration_unit="Bq m-2",
        )


def test_e1_soil_boundary_refuses_preconverted_hto() -> None:
    with pytest.raises(HTContractError, match="must not create HTO"):
        HTSoilDepositionBoundary(
            start_utc=T0,
            end_utc=T0 + timedelta(hours=1),
            species=GaseousTritiumSpecies.HT,
            deposited_ht_bq_m2=1.0,
            source_kind=HTForcingSourceKind.SYNTHETIC,
            provenance_id="test",
            spatial_support="cell",
            converted_to_hto_bq_m2=0.1,
        )
