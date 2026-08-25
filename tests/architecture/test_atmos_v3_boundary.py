from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "0ff463336409e74814d7d676577178b2e3680adc"
STAGE_TIP_SHA = "b31e80ba4532262c20b4dadca24ec26d3d8029a7"
PACKAGE = REPO / "src/cteas_ufotri/coupling/atmos_v3"


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
    """Return only the historical P7 stage diff, never later descendant work."""

    return set(
        git("diff", "--name-only", BASE_SHA, STAGE_TIP_SHA).splitlines()
    )


def test_p7_source_scope_is_atmospheric_interface_only() -> None:
    changed_source = sorted(
        path
        for path in changed_paths()
        if path.startswith("src/")
        and not path.startswith("src/cteas_ufotri/parameters_v3/")
    )
    assert changed_source
    allowed = (
        "src/cteas_ufotri/coupling/atmos_v3/",
        "src/cteas_ufotri/v3_pipeline/",
    )
    assert all(path.startswith(allowed) for path in changed_source)


def test_protected_runtime_paths_and_default_activation_are_unchanged() -> None:
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
        "src/cteas_ufotri/case.py",
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/coupling/integrator.py",
        "src/cteas_ufotri/coupling/mass_balance.py",
        "src/cteas_ufotri/coupling/reference_solver.py",
        "src/cteas_ufotri/coupling/state.py",
    ):
        assert git(
            "diff", "--name-only", BASE_SHA, STAGE_TIP_SHA, "--", path
        ) == ""

    config = yaml.safe_load(
        (REPO / "configs/default_parameters.yaml").read_text(encoding="utf-8")
    )
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False


def test_interface_has_explicit_fields_units_and_metadata_contract() -> None:
    forcing_text = (PACKAGE / "forcing.py").read_text(encoding="utf-8")
    metadata_text = (PACKAGE / "metadata.py").read_text(encoding="utf-8")
    validation_text = (PACKAGE / "validation.py").read_text(encoding="utf-8")
    for marker in (
        "timestamp",
        "location",
        "air_hto_concentration",
        "air_ht0_concentration",
        "deposition_flux",
        "temperature",
        "humidity",
        "wind_speed",
        "precipitation",
        "source",
        "provenance",
        "to_leaf_forcing",
        "to_soil_forcing",
    ):
        assert marker in forcing_text
    for marker in (
        "model_name",
        "version",
        "grid_definition",
        "time_resolution",
        "source_dataset",
        "creation_time",
        "quality_flag",
    ):
        assert marker in metadata_text
    for marker in (
        "Bq m^-3",
        "Bq m^-2 s^-1",
        "K",
        "m s^-1",
        "TIME_RESOLUTION_UNIT",
    ):
        assert marker in validation_text


def test_import_boundary_allows_only_leaf_and_soil_adapters() -> None:
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
            r"tfwt|obt|dose|foodchain|root|calmet|calpuff|cteas[-_]atmos|yaml|netcdf|xarray|pandas",
            line,
            re.IGNORECASE,
        )
        for line in imports
    )
    assert "from ...plant.leaf_exchange_resistance" in source_text
    assert "from ...plant.soil_v3" in source_text


def test_forcing_does_not_activate_ufotri_or_existing_default_path() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in PACKAGE.glob("*.py")
    )
    assert "production=True" not in source_text
    assert "ParameterDatabase" not in source_text
    assert "UFOTRI_PARAMETER_IMPORTED" not in source_text
    assert "UFOTRI_ACTIVE_DATABASE" not in source_text
