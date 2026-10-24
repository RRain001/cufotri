"""Live V3 atmospheric, pipeline and validation framework contracts.

The current invariants below are AST-equivalent copies of the non-historical
tests in three frozen stage-specific suites. The old Git-diff and immutable
SHA approval tests are recoverable via archive/cufotri-p7d-base-20261024.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO
ATMOS_PACKAGE = REPO / "src/cteas_ufotri/coupling/atmos_v3"
PACKAGE = REPO / "src/cteas_ufotri/v3_pipeline"
VALIDATION_SOURCE = REPO / "src/cteas_ufotri/validation_v3"

# Current interface checks from tests/architecture/test_atmos_v3_boundary.py
def test_interface_has_explicit_fields_units_and_metadata_contract() -> None:
    forcing_text = (ATMOS_PACKAGE / "forcing.py").read_text(encoding="utf-8")
    metadata_text = (ATMOS_PACKAGE / "metadata.py").read_text(encoding="utf-8")
    validation_text = (ATMOS_PACKAGE / "validation.py").read_text(encoding="utf-8")
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
        for path in ATMOS_PACKAGE.glob("*.py")
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
        for path in ATMOS_PACKAGE.glob("*.py")
    )
    assert "production=True" not in source_text
    assert "ParameterDatabase" not in source_text
    assert "UFOTRI_PARAMETER_IMPORTED" not in source_text
    assert "UFOTRI_ACTIVE_DATABASE" not in source_text



# Current interface checks from tests/architecture/test_v3_pipeline_boundary.py
def test_pipeline_imports_only_existing_typed_modules() -> None:
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.py"))
    imports = [line for line in source_text.splitlines() if re.match(r"^\s*(from|import)\s+", line)]
    assert not any(
        re.search(r"parameterdatabase|ufotri|calmet|calpuff|cteas[-_]atmos|subprocess|yaml|xarray|netcdf|pandas", line, re.IGNORECASE)
        for line in imports
    )
    assert "from ..coupling.atmos_v3" in source_text
    assert "from ..plant.soil_v3" in source_text
    assert "from ..plant.tfwt_v3" in source_text
    assert "from ..exposure.dose_v3" in source_text


def test_pipeline_has_no_local_physics_equations_or_parameter_database() -> None:
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.py"))
    assert "ParameterDatabase" not in source_text
    assert "production=True" not in source_text
    assert "D [Sv]" not in source_text
    assert "J_root" not in source_text
    assert "exp(" not in source_text



# Current interface checks from tests/architecture/test_p7_7a_validation_framework_boundary.py
def test_validation_package_does_not_import_runtime_owners() -> None:
    forbidden_tokens = (
        "cteas_ufotri.plant", "cteas_ufotri.soil", "cteas_ufotri.exposure",
        "cteas_ufotri.coupling", "cteas_ufotri.v3_pipeline", "ParameterDatabase",
        "UFOTRI_ACTIVE_DATABASE",
    )
    offenders = []
    for path in VALIDATION_SOURCE.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}:{token}")
    assert offenders == []


def test_p7_7b_runner_is_the_only_explicit_runtime_caller() -> None:
    """Execution is isolated to the additive benchmark adapter, not owners."""

    runner = (VALIDATION_SOURCE / "benchmark_runner.py").read_text(encoding="utf-8")
    registry = (VALIDATION_SOURCE / "benchmark_registry.py").read_text(encoding="utf-8")
    writer = (VALIDATION_SOURCE / "benchmark_result_writer.py").read_text(encoding="utf-8")

    assert "V3PipelineRunner" in runner
    assert "SoilStorageSolver" in runner
    assert "TFWTStorageSolver" in runner
    assert "OBTSolver" in runner
    assert "RootUptakeSolver" in runner
    assert "ParameterDatabase" not in runner
    assert "UFOTRI_ACTIVE_DATABASE" not in runner
    assert "ParameterDatabase" not in registry
    assert "ParameterDatabase" not in writer


def test_case_values_are_declared_in_yaml_not_benchmark_loader() -> None:
    loader = (VALIDATION_SOURCE / "benchmarks.py").read_text(encoding="utf-8")
    manifest = ROOT / "configs/v3/validation/p7_7a_baseline_benchmarks.yaml"

    assert manifest.is_file()
    assert "100.0" not in loader
    assert "0.001" not in loader
