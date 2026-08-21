from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "de3f56d4b89d0bffcd547c9ce1eca70a5b83f568"
V3_PACKAGE = REPO / "src/cteas_ufotri/plant/v3"


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


def test_public_pathway_source_scope_is_isolated() -> None:
    changed_source = sorted(path for path in changed_paths() if path.startswith("src/"))
    allowed = (
        "src/cteas_ufotri/plant/v3/",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_state.py",
        "src/cteas_ufotri/plant/obt_v3/",
    )
    assert changed_source
    assert all(path.startswith(allowed) for path in changed_source)


def test_legacy_default_and_external_activation_boundaries_are_unchanged() -> None:
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
