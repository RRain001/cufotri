from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "1b3966d9f5de23fe226c27b50029163dc2c063e9"
PACKAGE = REPO / "src/cteas_ufotri/plant/soil_v3"


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


def test_source_is_isolated_to_soil_and_later_typed_v3_packages() -> None:
    changed_source = sorted(path for path in changed_paths() if path.startswith("src/"))

    assert changed_source
    allowed = (
        "src/cteas_ufotri/plant/soil_v3/",
        "src/cteas_ufotri/plant/root_v3/",
        "src/cteas_ufotri/plant/tfwt_v3/",
        "src/cteas_ufotri/plant/food_v3/",
        "src/cteas_ufotri/exposure/intake_v3/",
        "src/cteas_ufotri/exposure/dose_v3/",
        "src/cteas_ufotri/coupling/atmos_v3/",
        "src/cteas_ufotri/v3_pipeline/",
    )
    assert all(path.startswith(allowed) for path in changed_source)


def test_configs_parameters_registry_and_legacy_paths_are_unchanged() -> None:
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
        "src/cteas_ufotri/coupling/state.py",
        "src/cteas_ufotri/soil/hto_balance.py",
        "src/cteas_ufotri/soil/multibox.py",
    ):
        assert git("diff", "--name-only", BASE_SHA, "--", path) == ""

    config = yaml.safe_load(
        (REPO / "configs/default_parameters.yaml").read_text(encoding="utf-8")
    )
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False


def test_solver_consumes_fluxes_and_public_soil_api_only() -> None:
    solver_text = (PACKAGE / "soil_solver.py").read_text(encoding="utf-8")

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
    state_text = (PACKAGE / "soil_state.py").read_text(encoding="utf-8")
    solver_text = (PACKAGE / "soil_solver.py").read_text(encoding="utf-8")

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
