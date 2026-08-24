from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "b31e80ba4532262c20b4dadca24ec26d3d8029a7"
PACKAGE = REPO / "src/cteas_ufotri/v3_pipeline"


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


def test_pipeline_source_scope_isolated_to_new_package() -> None:
    changed_source = sorted(path for path in changed_paths() if path.startswith("src/"))
    assert changed_source
    assert all(path.startswith("src/cteas_ufotri/v3_pipeline/") for path in changed_source)


def test_protected_paths_and_default_activation_are_unchanged() -> None:
    changed = changed_paths()
    forbidden = sorted(
        path
        for path in changed
        if path.startswith(("configs/", "parameters/"))
        or path.endswith("trusted_external_evidence_registry.yaml")
    )
    assert forbidden == []
    for path in (
        "src/cteas_ufotri/plant",
        "src/cteas_ufotri/soil",
        "src/cteas_ufotri/foodchain",
        "src/cteas_ufotri/atmosphere",
        "src/cteas_ufotri/dose",
        "src/cteas_ufotri/coupling/integrator.py",
        "src/cteas_ufotri/coupling/mass_balance.py",
        "src/cteas_ufotri/coupling/reference_solver.py",
        "src/cteas_ufotri/coupling/state.py",
        "src/cteas_ufotri/coupling/atmos_v3",
    ):
        assert git("diff", "--name-only", BASE_SHA, "--", path) == ""

    config = yaml.safe_load(
        (REPO / "configs/default_parameters.yaml").read_text(encoding="utf-8")
    )
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False


def test_pipeline_imports_only_existing_typed_modules() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in PACKAGE.glob("*.py")
    )
    imports = [
        line
        for line in source_text.splitlines()
        if re.match(r"^\s*(from|import)\s+", line)
    ]
    assert not any(
        re.search(
            r"parameterdatabase|ufotri|calmet|calpuff|cteas[-_]atmos|subprocess|yaml|xarray|netcdf|pandas",
            line,
            re.IGNORECASE,
        )
        for line in imports
    )
    assert "from ..coupling.atmos_v3" in source_text
    assert "from ..plant.soil_v3" in source_text
    assert "from ..plant.tfwt_v3" in source_text
    assert "from ..exposure.dose_v3" in source_text


def test_pipeline_has_no_local_physics_equations_or_parameter_database() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in PACKAGE.glob("*.py")
    )
    assert "ParameterDatabase" not in source_text
    assert "production=True" not in source_text
    assert "D [Sv]" not in source_text
    assert "J_root" not in source_text
    assert "exp(" not in source_text
