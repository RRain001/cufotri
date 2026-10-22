"""Require one Python 3.11 Docker/uv runtime for all CUFOTRI GitHub workflows.

The production stage never includes the test toolchain; execution checks run
in GitHub Actions. This contract test guards against a second host interpreter.
"""

from pathlib import Path
import tomllib

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = (
    "v3-integration-gate.yml",
    "v3-remediation-ci.yml",
    "python-compatibility.yml",
    "external-evidence.yml",
)


def test_only_python_311_is_supported() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["requires-python"] == ">=3.11,<3.12"
    assert (ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.11"
    lock_header = (ROOT / "uv.lock").read_text(encoding="utf-8").splitlines()[:8]
    assert 'requires-python = "==3.11.*"' in lock_header


def test_docker_has_separate_locked_verify_and_minimal_runtime() -> None:
    df = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "python:3.11-slim-bookworm" in df
    assert "uv==0.13.5" in df
    assert "uv sync --locked --no-dev --no-editable" in df
    assert "uv sync --locked --extra test" in df
    assert "AS verification" in df
    assert "AS runtime" in df
    assert "USER 10001:10001" in df
    assert 'ENTRYPOINT ["python", "-m", "cteas_ufotri.cli"]' in df
    ignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert "validation/external_local/**" in ignore
    assert ".venv/" in ignore
    assert "era5_key.txt" in ignore


@pytest.mark.parametrize("filename", WORKFLOWS)
def test_actions_run_python_tests_in_docker_only(filename: str) -> None:
    path = ROOT / ".github/workflows" / filename
    source = path.read_text(encoding="utf-8")
    parsed = yaml.load(source, Loader=yaml.BaseLoader)

    assert "3.12" not in source and "3.13" not in source
    assert "matrix.python-version" not in source
    assert "actions/setup-python@" not in source
    assert "python -m pip install" not in source
    assert "docker build --progress=plain --target verification" in source
    assert "cufotri:verification-${{ github.sha }}" in source
    assert "docker run --rm" in source
    assert parsed["jobs"]


def test_single_smoke_job_and_required_docker_conservation_gates() -> None:
    path = ROOT / ".github/workflows/python-compatibility.yml"
    parsed = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    jobs = parsed["jobs"]
    assert list(jobs) == ["python-compatibility"]
    assert "strategy" not in jobs["python-compatibility"]
    assert jobs["python-compatibility"]["name"] == "Python 3.11 portable smoke"

    protected = (ROOT / ".github/workflows/v3-integration-gate.yml").read_text()
    assert "Run portable current integration test suite" in protected
    assert "Run current and frozen-boundary invariants explicitly" in protected
    assert "run_system_sensitivity_screening_r1.py" in protected
    assert "run_root_operator_split_comparison_r1.py" in protected
    assert "run_soil_root_tfwt_obt_integration_r1.py" in protected
    assert "run_replay_input_orchestration_r1.py" in protected
    assert "run_food_intake_dose_endpoint_adapter_r1.py" in protected
    assert "--entrypoint /bin/bash" in protected
