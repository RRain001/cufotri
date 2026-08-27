"""V4 root total-uptake UFOTRI ET boundary decision R1 governance tests."""

from __future__ import annotations

from pathlib import Path

import yaml

from cteas_ufotri.meteorology.fallback_fluxes import (
    penman_ufotri_components_m_s,
    partition_evapotranspiration,
)

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_root_total_uptake_ufotri_et_boundary_decision_r1.yaml"


def decision() -> dict:
    return yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))


def test_decision_selects_eq39_without_promoting_project_aerodynamic_coefficient() -> None:
    data = decision()
    assert data["status"] == "PASS_BOUNDARY_DECISION"
    assert data["candidate_modes"]["FULL_PENMAN_EQ38"]["disposition"] == "NOT_SELECTED_PROVISIONAL_AERODYNAMIC_COEFFICIENT"
    assert data["candidate_modes"]["EQUILIBRIUM_RADIATION_EQ39"]["disposition"] == "SELECTED_CONTROLLED_BASELINE"
    assert data["selected_boundary"]["aerodynamic_coefficient_w_m2_pa"] == 0.0


def test_existing_eq39_compatible_path_produces_root_uptake_equal_to_transpiration() -> None:
    total, radiation, aerodynamic = penman_ufotri_components_m_s(
        temperature_k=293.15,
        dewpoint_k=288.15,
        wind_m_s=2.0,
        net_radiation_w_m2=300.0,
        latent_heat_j_kg=2_450_000.0,
        water_density_kg_m3=1000.0,
        psychrometric_constant_pa_k=66.0,
        aerodynamic_coefficient_w_m2_pa=0.0,
    )
    assert total == radiation
    assert aerodynamic == 0.0
    fluxes = partition_evapotranspiration(
        potential_total_m_s=total,
        lai=3.0,
        water_m=0.01,
        maximum_water_m=0.02,
        wilting_water_m=0.004,
        shading_mode="radiation_term_only",
        radiation_component_m_s=radiation,
        aerodynamic_component_m_s=aerodynamic,
    )
    assert fluxes.plant_transpiration_m_s >= 0.0
    assert fluxes.root_uptake_m_s == fluxes.plant_transpiration_m_s


def test_decision_keeps_production_resolution_and_hard_boundaries_false() -> None:
    data = decision()
    state = data["state_after_decision"]
    assert state["ufotri_20_40_40_controlled_profile_active"] is True
    assert state["root_q_w_production_input_resolved"] is False
    assert state["full_penman_eq38_production_active"] is False
    assert state["eq39_controlled_baseline_selected"] is True
    assert state["full_hydrology"] is False
    assert state["real_cteas_atmos_binding"] is False
    assert data["authorization"]["implementation_authorized"] is True
    assert data["authorization"]["production_activation_authorized"] is False
    assert all(value is False for value in data["hard_boundaries"].values())
