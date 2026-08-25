from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "6671f5793d04842bf2ceae4904f3c0cf30a0d7e0"
STAGE_TIP_SHA = "5ac5d5713b27f734676b2c3ff822c34a7ed2e95b"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def all_changed_paths() -> set[str]:
    """Return only the historical P6.2B-1 stage diff."""

    return set(
        git("diff", "--name-only", BASE_SHA, STAGE_TIP_SHA).splitlines()
    )


def test_only_new_resistance_package_is_added_under_src() -> None:
    changed = all_changed_paths()
    source_changes = sorted(path for path in changed if path.startswith("src/"))
    assert source_changes
    assert all(
        path.startswith("src/cteas_ufotri/plant/leaf_exchange_resistance/")
        for path in source_changes
    )
    assert git(
        "diff",
        "--name-only",
        BASE_SHA,
        STAGE_TIP_SHA,
        "--",
        "src/cteas_ufotri/plant/leaf_exchange.py",
    ) == ""


def test_configs_parameters_and_trusted_registry_are_unchanged() -> None:
    changed = all_changed_paths()
    forbidden = sorted(
        path
        for path in changed
        if path.startswith(("configs/", "parameters/"))
        or path.endswith("trusted_external_evidence_registry.yaml")
    )
    assert forbidden == []
    assert git(
        "diff", "--name-only", BASE_SHA, STAGE_TIP_SHA, "--", "configs"
    ) == ""


def test_default_leaf_exchange_behavior_is_unchanged() -> None:
    config = yaml.safe_load(
        (REPO / "configs/default_parameters.yaml").read_text(encoding="utf-8")
    )
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False


def test_resistance_package_has_no_solver_or_forbidden_module_imports() -> None:
    package = REPO / "src/cteas_ufotri/plant/leaf_exchange_resistance"
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in package.glob("*.py")
    )
    imports = [
        line
        for line in text.splitlines()
        if re.match(r"^\s*(from|import)\s+", line)
    ]
    assert not any(
        re.search(r"tfwt|obt|soil|dose|root", line, re.IGNORECASE)
        for line in imports
    )
    assert "production=False" in text
    assert not re.search(r"(?im)^\s*production\s*=\s*true\s*$", text)


def test_resistance_interface_is_explicitly_scoped() -> None:
    init_text = (
        REPO / "src/cteas_ufotri/plant/leaf_exchange_resistance/__init__.py"
    ).read_text(encoding="utf-8")
    resistance_text = (
        REPO / "src/cteas_ufotri/plant/leaf_exchange_resistance/resistance.py"
    ).read_text(encoding="utf-8")
    assert "ResistanceChain" in init_text
    assert "AtmosphericHTOForcing" in init_text
    assert "LeafExchangeFlux" in init_text
    assert "r_a + r_b + r_c" in resistance_text
    assert "1.0 / total" in resistance_text
    assert "no fallback is allowed" in resistance_text
