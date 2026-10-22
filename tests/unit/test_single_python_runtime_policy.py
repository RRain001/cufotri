"""Single Python-minor policy matches CTEAS-next's Python 3.11 runtime.

These tests prevent accidental reintroduction of 3.12/3.13 matrices or
unlocked dependency resolution in the live CUFOTRI research CI workflows.
"""

from pathlib import Path
import re
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


@pytest.mark.parametrize("filename", WORKFLOWS)
def test_actions_use_pinned_python_311_and_uv_lock(filename: str) -> None:
    path = ROOT / ".github/workflows" / filename
    text = path.read_text(encoding="utf-8")
    parsed = yaml.load(text, Loader=yaml.BaseLoader)

    assert "3.12" not in text and "3.13" not in text
    assert "matrix.python-version" not in text
    assert "uv sync --locked --extra test" in text

    jobs = parsed["jobs"]
    assert jobs
    for job in jobs.values():
        steps = job["steps"]
        python_steps = [
            step for step in steps
            if step.get("uses", "").startswith("actions/setup-python@")
        ]
        assert len(python_steps) == 1
        assert python_steps[0]["with"]["python-version"] == "3.11"

    versions = re.findall(r"python-version:\s*['\"]?([0-9]+\.[0-9]+)", text)
    assert versions == ["3.11"]


def test_smoke_workflow_has_one_job_and_no_version_matrix() -> None:
    path = ROOT / ".github/workflows/python-compatibility.yml"
    parsed = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    jobs = parsed["jobs"]
    assert list(jobs) == ["python-compatibility"]
    assert "strategy" not in jobs["python-compatibility"]
    assert jobs["python-compatibility"]["name"] == "Python 3.11 portable smoke"
