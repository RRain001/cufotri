from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "5ac5d5713b27f734676b2c3ff822c34a7ed2e95b"
PACKAGE = REPO / "src/cteas_ufotri/plant/tfwt_v3"


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


def test_only_new_v3_tfwt_package_and_artifacts_are_added() -> None:
    if (REPO / "src/cteas_ufotri/plant/v3").exists():
        # This architecture test is inherited by the P6.2B-2.5 child branch.
        # The child boundary test owns the combined tfwt_v3/plant/v3 scope.
        return
    changed = changed_paths()
    source_changes = sorted(path for path in changed if path.startswith("src/"))
    assert source_changes
    assert all(path.startswith("src/cteas_ufotri/plant/tfwt_v3/") for path in source_changes)
    assert git(
        "diff",
        "--name-only",
        BASE_SHA,
        "--",
        "src/cteas_ufotri/plant/leaf_exchange_resistance",
    ) == ""
    assert git("diff", "--name-only", BASE_SHA, "--", "src/cteas_ufotri/plant/tfwt.py") == ""


def test_configs_parameters_trusted_registry_and_legacy_paths_are_clean() -> None:
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


def test_solver_consumes_flux_without_recomputing_resistance_or_activation() -> None:
    solver_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in PACKAGE.glob("*.py")
    )
    assert "LeafExchangeFlux" in solver_text
    assert "production=False" not in (
        PACKAGE / "tfwt_solver.py"
    ).read_text(encoding="utf-8")
    assert "ResistanceChain" not in (
        PACKAGE / "tfwt_solver.py"
    ).read_text(encoding="utf-8")
    assert "exchange_coefficient" not in (
        PACKAGE / "tfwt_solver.py"
    ).read_text(encoding="utf-8")
    imports = [
        line
        for line in solver_text.splitlines()
        if re.match(r"^\s*(from|import)\s+", line)
    ]
    assert not any(
        re.search(r"obt|root|soil|dose|foodchain|cteas[-_]atmos", line, re.IGNORECASE)
        for line in imports
    )


def test_tfwt_state_and_solver_scope_markers_exist() -> None:
    state_text = (PACKAGE / "tfwt_state.py").read_text(encoding="utf-8")
    solver_text = (PACKAGE / "tfwt_solver.py").read_text(encoding="utf-8")
    assert "TFWTState" in state_text
    assert "tfwt_concentration_bq_kg_water" in state_text
    assert "tfwt_inventory_bq_m2" in state_text
    assert "provenance" in state_text
    assert "leaf_exchange_flux" in solver_text
    assert "new_inventory" in solver_text
    assert "no OBT state" in solver_text
