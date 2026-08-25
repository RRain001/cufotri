from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "be183807d56f0b02f85b67b5276098fcee7bc17e"
STAGE_TIP_SHA = "a6200569154b90ab90c8dc9c5332b70401da8ec1"
PACKAGE = REPO / "src/cteas_ufotri/exposure/intake_v3"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def changed_paths() -> set[str]:
    return set(git("diff", "--name-only", BASE_SHA, STAGE_TIP_SHA).splitlines())


def test_source_scope_is_intake_and_later_typed_v3_only() -> None:
    changed_source = sorted(
        path for path in changed_paths()
        if path.startswith("src/")
        and not path.startswith("src/cteas_ufotri/parameters_v3/")
    )
    assert changed_source
    allowed = (
        "src/cteas_ufotri/exposure/intake_v3/",
        "src/cteas_ufotri/exposure/dose_v3/",
        "src/cteas_ufotri/coupling/atmos_v3/",
        "src/cteas_ufotri/v3_pipeline/",
    )
    assert all(path.startswith(allowed) for path in changed_source)


def test_protected_paths_and_downstream_result_boundary_are_clean() -> None:
    changed = changed_paths()
    forbidden = sorted(
        path for path in changed
        if path.startswith(("configs/", "parameters/"))
        or path.endswith("trusted_external_evidence_registry.yaml")
    )
    assert forbidden == []
    assert git("diff", "--name-only", BASE_SHA, STAGE_TIP_SHA, "--", "src/cteas_ufotri/plant") == ""
    assert git("diff", "--name-only", BASE_SHA, STAGE_TIP_SHA, "--", "src/cteas_ufotri/dose") == ""
    config = yaml.safe_load(
        (REPO / "configs/default_parameters.yaml").read_text(encoding="utf-8")
    )
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False


def test_solver_consumes_food_inventory_public_api_only() -> None:
    solver_text = (PACKAGE / "intake_solver.py").read_text(encoding="utf-8")
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
    state_text = (PACKAGE / "intake_state.py").read_text(encoding="utf-8")
    solver_text = (PACKAGE / "intake_solver.py").read_text(encoding="utf-8")
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
