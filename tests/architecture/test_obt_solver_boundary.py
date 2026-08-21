from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "8164b0b4a7e0a32aa34aac130cfb3809d4cbc354"
PACKAGE = REPO / "src/cteas_ufotri/plant/obt_v3"


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


def test_source_is_isolated_to_new_obt_v3_package() -> None:
    changed_source = sorted(path for path in changed_paths() if path.startswith("src/"))

    assert changed_source
    assert all(path.startswith("src/cteas_ufotri/plant/obt_v3/") for path in changed_source)


def test_configs_parameters_registry_and_legacy_v1_v2_paths_are_unchanged() -> None:
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
    ):
        assert git("diff", "--name-only", BASE_SHA, "--", path) == ""

    config = yaml.safe_load(
        (REPO / "configs/default_parameters.yaml").read_text(encoding="utf-8")
    )
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False


def test_solver_uses_only_public_tfwt_methods() -> None:
    solver_text = (PACKAGE / "obt_solver.py").read_text(encoding="utf-8")

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
    state_text = (PACKAGE / "obt_state.py").read_text(encoding="utf-8")
    solver_text = (PACKAGE / "obt_solver.py").read_text(encoding="utf-8")
    validation_text = (PACKAGE / "validation.py").read_text(encoding="utf-8")

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
