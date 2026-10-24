"""Live typed V3 food -> intake -> dose boundaries, not fixed Git stages.

Preserves public state interfaces, provisional parameters and import isolation.
Numerical behavior and budgets are tested separately in maintained modules.
"""

from pathlib import Path
import re

import yaml

REPO = Path(__file__).resolve().parents[2]
DOSE_PACKAGE = REPO / "src/cteas_ufotri/exposure/dose_v3"
FOOD_PACKAGE = REPO / "src/cteas_ufotri/plant/food_v3"
INTAKE_PACKAGE = REPO / "src/cteas_ufotri/exposure/intake_v3"


def test_default_leaf_transfer_remains_opt_in() -> None:
    config = yaml.safe_load(
        (REPO / "configs/default_parameters.yaml").read_text(encoding="utf-8")
    )
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False


def test_solver_consumes_intake_public_api_only() -> None:
    solver_text = (DOSE_PACKAGE / "dose_solver.py").read_text(encoding="utf-8")
    assert "intake_state.inventory()" in solver_text
    assert "intake_state.consumer()" in solver_text
    assert "intake_state.age_group()" in solver_text
    assert "intake_state.period()" in solver_text
    assert "intake_state.time()" in solver_text
    assert "intake_state.intake_inventory_bq" not in solver_text
    assert "intake_state.age_group_identifier" not in solver_text
    assert "intake_state.timestamp" not in solver_text
    assert "ParameterDatabase" not in solver_text
    imports = [line for line in solver_text.splitlines() if re.match(r"^\s*(from|import)\s+", line)]
    assert not any(
        re.search(r"tfwt|obt|soil|plant|food|atmosphere|cteas[-_]atmos|config|parameter|regulatory|risk|emergency", line, re.IGNORECASE)
        for line in imports
    )

def test_dose_state_and_parameter_contracts_are_explicit() -> None:
    state_text = (DOSE_PACKAGE / "dose_state.py").read_text(encoding="utf-8")
    solver_text = (DOSE_PACKAGE / "dose_solver.py").read_text(encoding="utf-8")
    for marker in (
        "consumer_identifier", "age_group_identifier", "pathway_identifier",
        "intake_inventory_bq", "dose_coefficient", "dose_coefficient_unit",
        "committed_dose_sv", "time_period", "timestamp", "provenance",
        "def inventory(", "def dose(", "def consumer(",
    ):
        assert marker in state_text
    for marker in (
        "radionuclide_identifier", "pathway_identifier", "dose_coefficient_unit",
        'parameter_status: str = "provisional"', "D [Sv] = I [Bq] * e [Sv/Bq]",
    ):
        assert marker in solver_text
    for forbidden in (
        "soil", "plant", "food", "regulatory", "risk", "emergency", "effective_dose",
    ):
        assert forbidden not in state_text.lower()

def test_food_solver_uses_public_plant_inventory_api_only() -> None:
    solver_text = (FOOD_PACKAGE / "food_transfer_solver.py").read_text(encoding="utf-8")
    assert "obt_state.inventory()" in solver_text
    assert "tfwt_state.inventory()" in solver_text
    assert "obt_inventory_bq_m2" not in solver_text
    assert "tfwt_inventory_bq_m2" not in solver_text
    assert "ParameterDatabase" not in solver_text
    assert "production=True" not in solver_text
    imports = [line for line in solver_text.splitlines() if re.match(r"^\s*(from|import)\s+", line)]
    assert not any(
        re.search(r"dose|ingestion|population|foodchain|cteas[-_]atmos", line, re.IGNORECASE)
        for line in imports
    )

def test_harvest_and_food_state_contracts_are_explicit() -> None:
    state_text = (FOOD_PACKAGE / "harvest_state.py").read_text(encoding="utf-8")
    solver_text = (FOOD_PACKAGE / "food_transfer_solver.py").read_text(encoding="utf-8")
    for marker in (
        "plant_identifier", "crop_identifier", "growth_stage", "harvest_fraction",
        "harvest_inventory_bq", "food_product_identifier", "timestamp", "provenance",
        "def inventory(", "def product(",
    ):
        assert marker in state_text
    assert "FoodInventory" in state_text
    assert 'parameter_status: str = "provisional"' in solver_text
    assert "harvest_area_m2" in solver_text
    assert "tfwt_harvest_fraction" in solver_text
    assert "dose_inventory" not in state_text
    assert "ingestion_inventory" not in state_text
    assert "population" not in state_text.lower()

def test_solver_consumes_food_inventory_public_api_only() -> None:
    solver_text = (INTAKE_PACKAGE / "intake_solver.py").read_text(encoding="utf-8")
    assert "food_inventory.inventory()" in solver_text
    assert "food_inventory.product()" in solver_text
    assert "food_inventory_bq" not in solver_text
    assert "obt_inventory_bq" not in solver_text
    assert "tfwt_inventory_bq" not in solver_text
    assert "ParameterDatabase" not in solver_text
    imports = [line for line in solver_text.splitlines() if re.match(r"^\s*(from|import)\s+", line)]
    assert not any(
        re.search(r"dose|ingestion|population|regulatory|foodchain|cteas[-_]atmos|ufotri", line, re.IGNORECASE)
        for line in imports
    )

def test_intake_state_and_parameter_contracts_are_explicit() -> None:
    state_text = (INTAKE_PACKAGE / "intake_state.py").read_text(encoding="utf-8")
    solver_text = (INTAKE_PACKAGE / "intake_solver.py").read_text(encoding="utf-8")
    for marker in (
        "consumer_identifier", "age_group_identifier", "food_product_identifier",
        "consumption_rate", "consumption_rate_unit", "intake_inventory_bq",
        "time_period", "timestamp", "provenance", "def inventory(",
        "def consumer(", "def food_product(",
    ):
        assert marker in state_text
    for marker in (
        "annual_consumption_amount", "consumption_unit", "food_product_mass_kg",
        'parameter_status: str = "provisional"', "I_food [Bq/year]", "C_food [Bq/kg]",
    ):
        assert marker in solver_text
    assert "dose" not in state_text.lower()
    assert "committed" not in state_text.lower()
    assert "regulatory" not in state_text.lower()
