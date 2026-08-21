from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "70ff7291a8f12359514107bfb9b17bc1d679f529"
PACKAGE = REPO / "src/cteas_ufotri/plant/food_v3"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def changed_paths() -> set[str]:
    return set(git("diff", "--name-only", BASE_SHA).splitlines()) | set(
        git("ls-files", "--others", "--exclude-standard").splitlines()
    )


def test_source_scope_is_new_food_v3_only() -> None:
    changed_source = sorted(path for path in changed_paths() if path.startswith("src/"))
    assert changed_source
    assert all(path.startswith("src/cteas_ufotri/plant/food_v3/") for path in changed_source)


def test_protected_paths_and_dose_boundary_are_clean() -> None:
    changed = changed_paths()
    forbidden = sorted(
        path
        for path in changed
        if path.startswith(("configs/", "parameters/"))
        or path.endswith("trusted_external_evidence_registry.yaml")
    )
    assert forbidden == []
    for path in (
        "src/cteas_ufotri/plant/leaf_exchange.py",
        "src/cteas_ufotri/plant/tfwt.py",
        "src/cteas_ufotri/plant/obt.py",
        "src/cteas_ufotri/plant/soil_v3/",
        "src/cteas_ufotri/plant/root_v3/",
        "src/cteas_ufotri/plant/tfwt_v3/",
        "src/cteas_ufotri/plant/obt_v3/",
        "src/cteas_ufotri/coupling/state.py",
        "src/cteas_ufotri/dose/",
    ):
        assert git("diff", "--name-only", BASE_SHA, "--", path) == ""

    config = yaml.safe_load(
        (REPO / "configs/default_parameters.yaml").read_text(encoding="utf-8")
    )
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False


def test_food_solver_uses_public_plant_inventory_api_only() -> None:
    solver_text = (PACKAGE / "food_transfer_solver.py").read_text(encoding="utf-8")
    assert "obt_state.inventory()" in solver_text
    assert "tfwt_state.inventory()" in solver_text
    assert "obt_inventory_bq_m2" not in solver_text
    assert "tfwt_inventory_bq_m2" not in solver_text
    assert "ParameterDatabase" not in solver_text
    assert "production=True" not in solver_text
    imports = [
        line
        for line in solver_text.splitlines()
        if re.match(r"^\s*(from|import)\s+", line)
    ]
    assert not any(
        re.search(
            r"dose|ingestion|population|foodchain|cteas[-_]atmos",
            line,
            re.IGNORECASE,
        )
        for line in imports
    )


def test_harvest_and_food_state_contracts_are_explicit() -> None:
    state_text = (PACKAGE / "harvest_state.py").read_text(encoding="utf-8")
    solver_text = (PACKAGE / "food_transfer_solver.py").read_text(encoding="utf-8")
    for marker in (
        "plant_identifier",
        "crop_identifier",
        "growth_stage",
        "harvest_fraction",
        "harvest_inventory_bq",
        "food_product_identifier",
        "timestamp",
        "provenance",
        "def inventory(",
        "def product(",
    ):
        assert marker in state_text
    assert "FoodInventory" in state_text
    assert 'parameter_status: str = "provisional"' in solver_text
    assert "harvest_area_m2" in solver_text
    assert "tfwt_harvest_fraction" in solver_text
    assert "dose_inventory" not in state_text
    assert "ingestion_inventory" not in state_text
    assert "population" not in state_text.lower()
