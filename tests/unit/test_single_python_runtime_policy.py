"""Keep Python 3.11, Docker reproducibility and the *simplified* CI policy."""
from pathlib import Path
import tomllib

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = (
    "v3-integration-gate.yml",
    "python-compatibility.yml",
    "external-evidence.yml",
)


def _workflow(name: str):
    return yaml.load((ROOT / ".github/workflows" / name).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_only_locked_python311_supported():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["requires-python"] == ">=3.11,<3.12"
    assert (ROOT / ".python-version").read_text().strip() == "3.11"
    assert 'requires-python = "==3.11.*"' in (ROOT / "uv.lock").read_text().splitlines()[:8]


def test_verification_and_runtime_images_stay_isolated():
    df = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    for token in ("python:3.11-slim-bookworm", "uv==0.13.5",
                  "uv sync --locked --no-dev --no-editable",
                  "uv sync --locked --extra test",
                  "AS verification-deps", "AS verification",
                  "AS runtime", "USER 10001:10001",
                  'ENTRYPOINT ["python", "-m", "cteas_ufotri.cli"]'):
        assert token in df
    ignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    for token in ("validation/external_local/**", ".venv/", "era5_key.txt"):
        assert token in ignore


@pytest.mark.parametrize("filename", WORKFLOWS)
def test_pinned_python_git_actions_remain_docker_only(filename):
    text = (ROOT / ".github/workflows" / filename).read_text(encoding="utf-8")
    workflow = _workflow(filename)
    assert "3.12" not in text and "3.13" not in text
    assert "actions/setup-python@" not in text
    assert "python -m pip install" not in text
    assert "docker/setup-buildx-action@v3" in text
    assert "docker/build-push-action@v6" in text
    assert "target: verification" in text
    assert "cache-from: type=gha,scope=cufotri-py311-deps-v1" in text
    assert "docker run --rm" in text
    assert workflow["jobs"]


def test_normal_pr_runs_quick_while_version_full_is_dispatch_only():
    quick = _workflow("python-compatibility.yml")
    assert "pull_request" in quick["on"]
    assert "workflow_dispatch" in quick["on"]
    assert list(quick["jobs"]) == ["python-compatibility"]
    assert quick["jobs"]["python-compatibility"]["name"] == "Python 3.11 portable smoke"
    source = (ROOT / ".github/workflows/python-compatibility.yml").read_text()
    assert "python scripts/test.py quick" in source

    full = _workflow("v3-integration-gate.yml")
    assert set(full["on"]) == {"workflow_dispatch"}
    assert list(full["jobs"]) == ["integration-gate"]
    comprehensive = (ROOT / ".github/workflows/v3-integration-gate.yml").read_text()
    assert comprehensive.count("python scripts/test.py full") == 1
    assert "pytest tests" not in comprehensive
