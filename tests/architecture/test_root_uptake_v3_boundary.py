from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "d38ae03536b5e9fd027012f0b2e68402310551c7"
ROOT_PACKAGE = REPO / "src/cteas_ufotri/plant/root_v3"
TFWT_PACKAGE = REPO / "src/cteas_ufotri/plant/tfwt_v3"


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


def test_source_scope_is_root_and_existing_tfwt_v3_only() -> None:
    changed_source = sorted(path for path in changed_paths() if path.startswith("src/"))
    assert changed_source
    allowed = (
        "src/cteas_ufotri/plant/root_v3/",
        "src/cteas_ufotri/plant/tfwt_v3/",
        "src/cteas_ufotri/plant/food_v3/",
    )
    assert all(path.startswith(allowed) for path in changed_source)


def test_protected_configs_parameters_registry_and_legacy_paths_are_clean() -> None:
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
        "src/cteas_ufotri/coupling/state.py",
    ):
        assert git("diff", "--name-only", BASE_SHA, "--", path) == ""

    config = yaml.safe_load(
        (REPO / "configs/default_parameters.yaml").read_text(encoding="utf-8")
    )
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False


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
