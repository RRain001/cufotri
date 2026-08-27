"""V4 UFOTRI Eq.39 total root-water uptake implementation R1 tests."""

from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path

import pytest
import yaml

from cteas_ufotri.meteorology.derived_variables import saturation_curve_slope_pa_k
from cteas_ufotri.plant.root_v4 import (
    RootV4InputError,
    RootV4UnitError,
    RootWaterFluxProvenanceV4,
    ThreeLayerRootFluxSolverV4,
    UFOTRIEq39RootUptakeInputV4,
    UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS,
    ufotri_eq39_potential_total_m_s,
    ufotri_eq39_root_uptake,
)
from cteas_ufotri.plant.soil_v4 import SoilV4Provenance, ThreeLayerSoilState

UTC = timezone.utc
TIMESTAMP = datetime(2026, 1, 1, 12, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_root_total_uptake_ufotri_eq39_implementation_r1.yaml"


def provenance(label: str) -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id=f"TEST_{label}",
        source_locator="tests/v4/test_v4_root_total_uptake_ufotri_eq39_implementation_r1.py",
        revision="r1",
        artifact_sha256=hashlib.sha256(label.encode("utf-8")).hexdigest(),
        profile_context=f"UFOTRI_EQ39_{label}",
    )


def eq39_input(**overrides: object) -> UFOTRIEq39RootUptakeInputV4:
    data: dict[str, object] = {
        "plant_identifier": "synthetic-soybean",
        "timestamp": TIMESTAMP,
        "temperature_k": 293.15,
        "net_radiation_w_m2": 300.0,
        "lai": 3.0,
        "soil_water_m": 0.01,
        "maximum_water_m": 0.02,
        "wilting_water_m": 0.004,
        "latent_heat_j_kg": 2_450_000.0,
        "water_density_kg_m3": 1000.0,
        "psychrometric_constant_pa_k": 66.0,
        "meteorology_provenance": provenance("METEOROLOGY"),
        "case_provenance": provenance("CASE"),
        "physical_constants_provenance": provenance("CONSTANTS"),
    }
    data.update(overrides)
    return UFOTRIEq39RootUptakeInputV4(**data)  # type: ignore[arg-type]


def soil_state() -> ThreeLayerSoilState:
    return ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=TIMESTAMP,
        provenance=SoilV4Provenance(
            source_id="SYNTHETIC_SOIL",
            source_version="r1",
            artifact_sha256="b" * 64,
            spatial_reference="soil_surface_area",
            temporal_resolution_s=1800.0,
        ),
    )


def test_eq39_is_direct_radiation_formula_without_wind_or_dewpoint_inputs() -> None:
    inputs = eq39_input()
    field_names = {item.name for item in fields(UFOTRIEq39RootUptakeInputV4)}
    assert "wind_m_s" not in field_names
    assert "dewpoint_k" not in field_names
    assert "aerodynamic_coefficient_w_m2_pa" not in field_names

    delta = float(saturation_curve_slope_pa_k(inputs.temperature_k))
    expected = (
        delta
        * inputs.net_radiation_w_m2
        / (delta + inputs.psychrometric_constant_pa_k)
        / inputs.latent_heat_j_kg
        / inputs.water_density_kg_m3
    )
    actual = ufotri_eq39_potential_total_m_s(inputs)
    assert math.isclose(actual, expected, rel_tol=1.0e-15, abs_tol=0.0)


def test_eq39_root_uptake_identity_and_exact_20_40_40_distribution() -> None:
    result = ufotri_eq39_root_uptake(eq39_input(), output_provenance=provenance("OUTPUT"))
    assert result.aerodynamic_coefficient_w_m2_pa == 0.0
    assert result.root_uptake_m_s == result.plant_transpiration_m_s
    assert result.root_uptake_m_s > 0.0
    assert UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS == (0.2, 0.4, 0.4)
    expected = tuple(result.root_uptake_m_s * fraction for fraction in (0.2, 0.4, 0.4))
    assert result.layer_forcing.water_uptake_fluxes_m_s == expected
    assert math.isclose(
        sum(result.layer_forcing.water_uptake_fluxes_m_s),
        result.root_uptake_m_s,
        rel_tol=1.0e-15,
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"net_radiation_w_m2": 0.0},
        {"net_radiation_w_m2": -50.0},
        {"soil_water_m": 0.004},
        {"soil_water_m": 0.0},
    ],
)
def test_zero_energy_or_wilting_boundary_yields_zero_root_forcing(overrides: dict[str, float]) -> None:
    result = ufotri_eq39_root_uptake(eq39_input(**overrides), output_provenance=provenance("OUTPUT"))
    assert result.root_uptake_m_s == 0.0
    assert result.layer_forcing.water_uptake_fluxes_m_s == (0.0, 0.0, 0.0)


@pytest.mark.parametrize(
    "overrides",
    [
        {"temperature_k": 0.0},
        {"temperature_k": float("nan")},
        {"lai": -0.1},
        {"soil_water_m": -0.001},
        {"maximum_water_m": 0.0},
        {"wilting_water_m": -0.001},
        {"wilting_water_m": 0.03},
        {"latent_heat_j_kg": 0.0},
        {"water_density_kg_m3": -1.0},
        {"psychrometric_constant_pa_k": 0.0},
    ],
)
def test_invalid_physical_domain_fails_closed(overrides: dict[str, float]) -> None:
    with pytest.raises(RootV4InputError):
        eq39_input(**overrides)


def test_wrong_units_fail_closed() -> None:
    with pytest.raises(RootV4UnitError):
        eq39_input(temperature_unit="degC")
    with pytest.raises(RootV4UnitError):
        eq39_input(net_radiation_unit="J m^-2")
    with pytest.raises(RootV4UnitError):
        eq39_input(water_storage_unit="kg m^-2")


def test_utc_and_independent_provenance_are_preserved() -> None:
    inputs = eq39_input()
    output = provenance("OUTPUT")
    result = ufotri_eq39_root_uptake(inputs, output_provenance=output)
    assert inputs.timestamp == TIMESTAMP
    assert inputs.meteorology_provenance.source_id == "TEST_METEOROLOGY"
    assert inputs.case_provenance.source_id == "TEST_CASE"
    assert inputs.physical_constants_provenance.source_id == "TEST_CONSTANTS"
    assert result.layer_forcing.timestamp == TIMESTAMP
    assert result.layer_forcing.provenance == output


def test_eq39_path_is_deterministic() -> None:
    inputs = eq39_input()
    output = provenance("OUTPUT")
    first = ufotri_eq39_root_uptake(inputs, output_provenance=output)
    second = ufotri_eq39_root_uptake(inputs, output_provenance=output)
    assert first == second


def test_eq39_to_20_40_40_to_root_solver_preserves_j_q_c_and_ledgers() -> None:
    result = ufotri_eq39_root_uptake(eq39_input(), output_provenance=provenance("OUTPUT"))
    soil = soil_state()
    plan = ThreeLayerRootFluxSolverV4().plan(
        soil,
        result.layer_forcing,
        interval_seconds=1800.0,
    )
    for transfer, layer in zip(plan.layer_transfers, soil.layers, strict=True):
        assert math.isclose(
            transfer.hto_uptake_flux_bq_m2_s,
            transfer.water_uptake_flux_m_s * layer.hto_concentration_bq_m3_water,
            rel_tol=1.0e-15,
        )
    assert math.isclose(
        plan.total_water_transfer_m,
        result.root_uptake_m_s * 1800.0,
        rel_tol=1.0e-15,
    )
    assert plan.max_abs_water_balance_residual_m <= 1.0e-15
    assert plan.max_abs_hto_balance_residual_bq_m2 <= 1.0e-12


def test_governance_closes_only_root_qw_construction_not_full_model_readiness() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    assert data["stage"] == "V4_ROOT_TOTAL_UPTAKE_UFOTRI_EQ39_IMPLEMENTATION_R1"
    exit_state = data["exit_state_if_all_gates_pass"]
    assert exit_state["eq39_controlled_baseline_active"] is True
    assert exit_state["ufotri_20_40_40_controlled_profile_active"] is True
    assert exit_state["root_q_w_production_input_resolved"] is True
    assert exit_state["full_model_production_ready"] is False
    assert exit_state["full_penman_eq38_production_active"] is False
    assert exit_state["ufotri_reference_layer_rates_active"] is False
    assert exit_state["short_term_3h_delay_active"] is False
    assert exit_state["full_hydrology"] is False
    assert exit_state["real_cteas_atmos_binding"] is False
    assert all(value is False for value in data["hard_boundaries"].values())
