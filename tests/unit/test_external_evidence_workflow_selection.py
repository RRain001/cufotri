"""Offline contract tests for the manually dispatched external-evidence workflow.

These verify dispatch/readiness semantics. They do not simulate scientific data
availability or assert that absent private evidence has passed qualification.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from validation.external_input_requirements import DATASET_REQUIREMENTS


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/external-evidence.yml"


def _read_workflow() -> dict:
    # PyYAML's BaseLoader leaves YAML's 'on' mapping key as a string.
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_external_workflow_is_manual_only_and_default_is_readiness_audit() -> None:
    workflow = _read_workflow()
    assert set(workflow["on"]) == {"workflow_dispatch"}
    inputs = workflow["on"]["workflow_dispatch"]["inputs"]
    assert inputs["mode"]["default"] == "audit"
    assert inputs["mode"]["options"] == ["audit", "strict"]
    assert inputs["dataset"]["default"] == "ALL"
    assert inputs["dataset"]["options"] == ["ALL", *DATASET_REQUIREMENTS]
    assert "refs/heads/main" in workflow["jobs"]["external-evidence"]["if"]


def test_strict_workflow_requires_explicit_inputs_and_only_selected_markers() -> None:
    workflow = _read_workflow()
    steps = workflow["jobs"]["external-evidence"]["steps"]
    readiness = next(step for step in steps if "Audit declared datasets" in step["name"])
    strict = next(step for step in steps if step["name"] == "Run strictly selected external test markers")
    assert readiness["env"]["EVIDENCE_TARGET"] == "${{ inputs.dataset }}"
    assert "selected_inputs_available" in readiness["run"]
    assert "mode == \"strict\" and not ready" in readiness["run"]
    assert strict["if"] == "inputs.mode == 'strict'"
    assert "--require-external-inputs" in strict["run"]
    assert "external_sb1_data" in strict["run"]
    assert "external_sb4_data" in strict["run"]
    assert "external_era5_data" in strict["run"]
    assert "private_reblinding_secret" in strict["run"]
