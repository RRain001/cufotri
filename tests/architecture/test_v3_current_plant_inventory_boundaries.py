"""Current V3 soil/plant inventory and interface invariants, not frozen-stage approval.

Historical Git diff assertions for individual implementation stages are archived.
All current solver/public API and layer-isolation assertions here are copied from
the original tests; this file makes no external model-equivalence claim.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT_PACKAGE = REPO / "src/cteas_ufotri/plant/root_v3"
TFWT_PACKAGE = REPO / "src/cteas_ufotri/plant/tfwt_v3"
SOIL_PACKAGE = REPO / "src/cteas_ufotri/plant/soil_v3"
OBT_PACKAGE = REPO / "src/cteas_ufotri/plant/obt_v3"
V3_PACKAGE = REPO / "src/cteas_ufotri/plant/v3"


# Continuing V3 contracts, formerly test_v3_plant_pathway_boundary.py

def test_pathway_consumes_frozen_resistance_and_does_not_lookup_parameters() -> None:
    pathway_text = (V3_PACKAGE / "pathway.py").read_text(encoding="utf-8")
    assert "ResistanceState" in pathway_text
    assert "signed_leaf_exchange_flux" in pathway_text
    assert "ResistanceChain" not in pathway_text
    assert "total_resistance" not in pathway_text
    assert "exchange_coefficient" not in pathway_text
    assert "ParameterDatabase" not in pathway_text


def test_public_tfwt_api_and_future_obt_boundary_are_explicit() -> None:
    state_text = (V3_PACKAGE / "state.py").read_text(encoding="utf-8")
    validation_text = (V3_PACKAGE / "validation.py").read_text(encoding="utf-8")
    tfwt_state_text = (
        REPO / "src/cteas_ufotri/plant/tfwt_v3/tfwt_state.py"
    ).read_text(encoding="utf-8")

    assert "obt" in state_text
    assert "TFWTStorageSolver" not in state_text
    assert "OBT pathway is reserved and not implemented" in validation_text
    assert "def inventory(" in tfwt_state_text
    assert "def activity_concentration(" in tfwt_state_text
    assert "def advance(" in tfwt_state_text


def test_v3_source_has_no_production_activation_or_forbidden_solver_imports() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in V3_PACKAGE.glob("*.py")
    )
    imports = [
        line
        for line in source_text.splitlines()
        if re.match(r"^\s*(from|import)\s+", line)
    ]
    assert "production=True" not in source_text
    assert not any(
        re.search(r"soil|dose|root|foodchain|cteas[-_]atmos", line, re.IGNORECASE)
        for line in imports
    )


# Continuing OBT contracts, formerly test_obt_solver_boundary.py

def test_solver_uses_only_public_tfwt_methods() -> None:
    solver_text = (OBT_PACKAGE / "obt_solver.py").read_text(encoding="utf-8")

    assert "tfwt_state.inventory()" in solver_text
    assert "tfwt_state.activity_concentration()" in solver_text
    assert "tfwt_state.tfwt_" not in solver_text
    assert "tfwt_state.time" not in solver_text
    assert "ResistanceChain" not in solver_text
    assert "ParameterDatabase" not in solver_text
    assert "production=True" not in solver_text

    imports = [
        line
        for line in solver_text.splitlines()
        if re.match(r"^\s*(from|import)\s+", line)
    ]
    assert not any(
        re.search(r"soil|dose|root|foodchain|cteas[-_]atmos", line, re.IGNORECASE)
        for line in imports
    )


def test_obt_state_and_biological_forcing_contracts_are_explicit() -> None:
    state_text = (OBT_PACKAGE / "obt_state.py").read_text(encoding="utf-8")
    solver_text = (OBT_PACKAGE / "obt_solver.py").read_text(encoding="utf-8")
    validation_text = (OBT_PACKAGE / "validation.py").read_text(encoding="utf-8")

    for marker in (
        "plant_identifier",
        "crop",
        "growth_stage",
        "obt_inventory_bq_m2",
        "obt_concentration",
        "timestamp",
        "provenance",
    ):
        assert marker in state_text
    assert "class PlantBiologicalForcing" in solver_text
    assert "is_daylight" in solver_text
    assert "temperature_k" in solver_text
    assert "photosynthetic_activity" in solver_text
    assert "growth_stage" in validation_text


# Continuing SOIL contracts, formerly test_soil_hto_v3_boundary.py

def test_solver_consumes_fluxes_and_public_soil_api_only() -> None:
    solver_text = (SOIL_PACKAGE / "soil_solver.py").read_text(encoding="utf-8")

    assert "forcing.deposition_flux_bq_m2_s" in solver_text
    assert "forcing.transport_flux_bq_m2_s" in solver_text
    assert "state.inventory()" in solver_text
    assert "state.concentration()" in solver_text
    assert "state.soil_water_inventory_bq_m2" not in solver_text
    assert "root" not in solver_text.lower().split("__all__", 1)[0]
    assert "foodchain" not in solver_text.lower().split("__all__", 1)[0]
    assert "ParameterDatabase" not in solver_text
    assert "production=True" not in solver_text

    imports = [
        line
        for line in solver_text.splitlines()
        if re.match(r"^\s*(from|import)\s+", line)
    ]
    assert not any(
        re.search(
            r"root|plant|foodchain|dose|cteas[-_]atmos|obt|tfwt",
            line,
            re.IGNORECASE,
        )
        for line in imports
    )


def test_soil_state_and_decay_contracts_are_explicit() -> None:
    state_text = (SOIL_PACKAGE / "soil_state.py").read_text(encoding="utf-8")
    solver_text = (SOIL_PACKAGE / "soil_solver.py").read_text(encoding="utf-8")

    for marker in (
        "soil_identifier",
        "layer_id",
        "layer_depth_m",
        "soil_water_content",
        "soil_water_inventory_bq_m2",
        "soil_water_concentration",
        "timestamp",
        "provenance",
    ):
        assert marker in state_text
    assert "SoilState" in state_text
    assert "SoilStorageSolver" in solver_text
    assert "math.log(2.0) / self.tritium_half_life_s" in solver_text
    assert "class SoilForcing" in solver_text


# Continuing ROOT contracts, formerly test_root_uptake_v3_boundary.py

def test_root_solver_uses_public_soil_api_and_has_no_forbidden_solver_imports() -> None:
    solver_text = (ROOT_PACKAGE / "root_solver.py").read_text(encoding="utf-8")
    assert "soil_state.inventory()" in solver_text
    assert "soil_state.concentration()" in solver_text
    assert "soil_water_inventory_bq_m2" not in solver_text
    assert "ParameterDatabase" not in solver_text
    assert "production=True" not in solver_text
    imports = [
        line
        for line in solver_text.splitlines()
        if re.match(r"^\s*(from|import)\s+", line)
    ]
    assert not any(
        re.search(r"tfwt|obt|foodchain|dose|cteas[-_]atmos", line, re.IGNORECASE)
        for line in imports
    )


def test_root_state_and_equation_contracts_are_explicit() -> None:
    state_text = (ROOT_PACKAGE / "root_state.py").read_text(encoding="utf-8")
    solver_text = (ROOT_PACKAGE / "root_solver.py").read_text(encoding="utf-8")
    for marker in (
        "plant_identifier",
        "root_zone_identifier",
        "uptake_inventory_bq_m2",
        "uptake_flux_bq_m2_s",
        "timestamp",
        "provenance",
        "def inventory(",
        "def flux(",
    ):
        assert marker in state_text
    assert "J_root = k_root * C_soil" in solver_text
    assert 'parameter_status: str = "provisional"' in solver_text
    assert "ROOT_COEFFICIENT_UNIT" in solver_text
    assert "tfwt_inventory_bq_m2" not in state_text
    assert "obt_inventory_bq_m2" not in state_text
    assert "foodchain" not in state_text.lower()
    assert "dose" not in state_text.lower()


def test_tfwt_boundary_consumes_root_flux_without_activating_database() -> None:
    solver_text = (TFWT_PACKAGE / "tfwt_solver.py").read_text(encoding="utf-8")
    assert "RootFlux" in solver_text
    assert "root_uptake_flux" in solver_text
    assert "root_uptake_input_bq_m2" in solver_text
    assert "ParameterDatabase" not in solver_text
    assert "production=True" not in solver_text


# Continuing TFWT contracts, formerly test_tfwt_solver_boundary.py

def test_solver_consumes_flux_without_recomputing_resistance_or_activation() -> None:
    solver_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in TFWT_PACKAGE.glob("*.py")
    )
    assert "LeafExchangeFlux" in solver_text
    assert "RootFlux" in solver_text
    assert "root_uptake_flux" in solver_text
    assert "production=False" not in (
        TFWT_PACKAGE / "tfwt_solver.py"
    ).read_text(encoding="utf-8")
    assert "ResistanceChain" not in (
        TFWT_PACKAGE / "tfwt_solver.py"
    ).read_text(encoding="utf-8")
    assert "exchange_coefficient" not in (
        TFWT_PACKAGE / "tfwt_solver.py"
    ).read_text(encoding="utf-8")
    imports = [
        line
        for line in solver_text.splitlines()
        if re.match(r"^\s*(from|import)\s+", line)
    ]
    assert not any(
        re.search(r"obt|soil|dose|foodchain|cteas[-_]atmos", line, re.IGNORECASE)
        for line in imports
    )


def test_tfwt_state_and_solver_scope_markers_exist() -> None:
    state_text = (TFWT_PACKAGE / "tfwt_state.py").read_text(encoding="utf-8")
    solver_text = (TFWT_PACKAGE / "tfwt_solver.py").read_text(encoding="utf-8")
    assert "TFWTState" in state_text
    assert "tfwt_concentration_bq_kg_water" in state_text
    assert "tfwt_inventory_bq_m2" in state_text
    assert "provenance" in state_text
    assert "leaf_exchange_flux" in solver_text
    assert "new_inventory" in solver_text
    assert "no OBT state" in solver_text
