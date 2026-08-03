from __future__ import annotations

import inspect
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from validation.external_input_requirements import (
    DATASET_REQUIREMENTS,
    InputStatus,
    check_dataset,
    dataset_root,
)


ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable
MARKER_EXPRESSION = (
    "not external_sb1_data and not external_sb4_data and "
    "not external_era5_data and not private_reblinding_secret"
)


def _clean_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("CTEAS_EXTERNAL_EVIDENCE_ROOT", None)
    environment.pop("CTEAS_ERA5_INPUT_ROOT", None)
    return environment


def _run(*arguments: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, *arguments],
        cwd=ROOT,
        env=_clean_environment(),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def test_external_markers_are_registered_and_public_tests_remain_selectable() -> None:
    markers = _run("-m", "pytest", "--markers")
    assert markers.returncode == 0
    for marker in (
        "external_sb1_data",
        "external_sb4_data",
        "external_era5_data",
        "private_reblinding_secret",
    ):
        assert marker in markers.stdout

    public = _run("-m", "pytest", "--collect-only", "-vv", "-m", MARKER_EXPRESSION)
    assert public.returncode == 0
    assert "test_sb4_transfer_thresholds_frozen" in public.stdout
    assert "test_independent_chamber_era5_boundary_alignment" not in public.stdout


def test_required_paths_and_environment_resolution_are_stable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    assert DATASET_REQUIREMENTS["SB1"].environment_variable == (
        "CTEAS_EXTERNAL_EVIDENCE_ROOT"
    )
    assert DATASET_REQUIREMENTS["SB4"].environment_variable == (
        "CTEAS_EXTERNAL_EVIDENCE_ROOT"
    )
    assert DATASET_REQUIREMENTS["ERA5_ACCEPTANCE"].required_paths == (
        "era5_surface_2025-06-01_2025-06-02.csv",
    )
    assert any(
        path.endswith("emras_soybean_sb1/references/IAEA-emras-tritium-wg.pdf")
        for path in DATASET_REQUIREMENTS["SB1"].required_paths
    )
    assert any(
        path.endswith("emras_soybean_sb4/generated_forcing/sb4_forcing_manifest.json")
        for path in DATASET_REQUIREMENTS["SB4"].required_paths
    )
    assert not any(
        "tests/data" in path or "synthetic" in path
        for requirement in DATASET_REQUIREMENTS.values()
        for path in requirement.required_paths
    )

    external_root = tmp_path / "external-root"
    monkeypatch.setenv("CTEAS_EXTERNAL_EVIDENCE_ROOT", str(external_root))
    assert dataset_root(ROOT, "SB1") == external_root / "emras_soybean_sb1"
    assert check_dataset(ROOT, "SB1").status is InputStatus.MISSING


def test_missing_input_is_portable_skip_and_strict_failure() -> None:
    node = (
        "tests/independent_review_sb1/test_emras_soybean_sb1_independent_review.py::"
        "test_independent_chamber_era5_boundary_alignment"
    )
    portable = _run("-m", "pytest", "-q", "-rs", node)
    assert portable.returncode == 0
    assert "SKIP_EXTERNAL_SB1_INPUT_NOT_AVAILABLE" in portable.stdout

    strict = _run("-m", "pytest", "-q", "--require-external-inputs", node)
    assert strict.returncode != 0
    strict_output = strict.stdout + strict.stderr
    assert "DATASET = SB1" in strict_output
    assert "MISSING_FILES =" in strict_output
    assert "sb1_forcing_primary.csv" in strict_output


def test_incomplete_or_invalid_input_is_not_skipped(tmp_path: Path) -> None:
    incomplete_root = tmp_path / "incomplete-root"
    (incomplete_root / "emras_soybean_sb1").mkdir(parents=True)
    environment = _clean_environment()
    environment["CTEAS_EXTERNAL_EVIDENCE_ROOT"] = str(incomplete_root)
    incomplete = subprocess.run(
        [PYTHON, "-c", "from pathlib import Path; from validation.external_input_requirements import check_dataset; print(check_dataset(Path.cwd(), 'SB1').status)"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    # The subprocess above does not receive the required repository path through
    # argv; check the same status directly to keep the assertion explicit.
    external_root = tmp_path / "malformed-root"
    dataset = external_root / "emras_soybean_sb1"
    (dataset / "references" / "IAEA-emras-tritium-wg.pdf").mkdir(parents=True)
    assert incomplete.returncode == 0
    assert incomplete.stdout.strip() == "INCOMPLETE"
    environment = _clean_environment()
    environment["CTEAS_EXTERNAL_EVIDENCE_ROOT"] = str(external_root)
    result = subprocess.run(
        [
            PYTHON,
            "-m",
            "pytest",
            "-q",
            "tests/independent_review_sb1/test_emras_soybean_sb1_independent_review.py::"
            "test_independent_pdf_tfwt_values",
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "STATUS = INVALID" in output
    assert "INVALID_FILES" in output
    assert "SKIP_EXTERNAL_SB1_INPUT_NOT_AVAILABLE" not in output


def test_resolver_does_not_search_other_worktrees_or_download_inputs(tmp_path: Path) -> None:
    alternate_worktree = tmp_path / "other-worktree"
    (alternate_worktree / "validation" / "external_local" / "emras_soybean_sb1").mkdir(
        parents=True
    )
    assert check_dataset(ROOT, "SB1").status is InputStatus.MISSING
    source = inspect.getsource(sys.modules["validation.external_input_requirements"])
    lowered = source.lower()
    assert "rglob" not in lowered
    assert "path.home" not in lowered
    assert "requests" not in lowered
    assert "urllib" not in lowered
    assert "download(" not in lowered


@pytest.mark.parametrize(
    "script_arguments",
    (
        ("scripts/verify_acceptance.py", "--recompute"),
        ("scripts/verify_v2_acceptance.py", "--recompute"),
        ("scripts/verify_v3_compatibility.py",),
        ("scripts/verify_v3_architecture_readiness.py",),
    ),
)
def test_era5_verifiers_report_stable_missing_input_status(
    script_arguments: tuple[str, ...],
) -> None:
    result = _run(*script_arguments)
    assert result.returncode == 2
    output = result.stdout + result.stderr
    assert "STATUS = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT" in output
    assert "DATASET = ERA5_ACCEPTANCE" in output
    assert "MISSING_FILES =" in output
    assert "era5_surface_2025-06-01_2025-06-02.csv" in output


def test_external_gate_and_physics_gate_remain_fail_closed() -> None:
    unblocking = _run("scripts/verify_v3_external_evidence_unblocking.py")
    assert unblocking.returncode == 0
    unblocking_output = unblocking.stdout + unblocking.stderr
    assert "READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA" in unblocking_output
    assert "LOCAL_INTAKE_STATUS = READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA" in unblocking_output

    physics = _run("scripts/verify_v3_physics_start_gate.py")
    assert physics.returncode == 0
    physics_output = physics.stdout + physics.stderr
    assert "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA" in physics_output


def test_sb4_thresholds_are_unchanged() -> None:
    protocol = yaml.safe_load(
        (
            ROOT
            / "validation/benchmarks/emras_soybean_sb4/preregistration/"
            "sb4_transfer_protocol.yaml"
        ).read_text(encoding="utf-8")
    )
    assert protocol["support_criteria"] == {
        "overall_log10_rmse_improvement_minimum_dex": 0.50,
        "late_log10_rmse_improvement_minimum_dex": 0.50,
        "early_prediction_factor_limit": 3.0,
        "early_log10_error_worsening_maximum_dex": 0.25,
        "both_chamber_profiles_required": True,
        "forcing_scenarios_required_per_profile": 5,
        "require_finite_nonnegative": True,
        "mass_closure_absolute_tolerance_bq_m2": 1.0e-6,
        "internal_transfer_absolute_tolerance_bq_m2": 1.0e-9,
        "pods_log10_rmse_worsening_maximum_dex": 0.50,
        "obt_absolute_log10_error_worsening_maximum_dex": 0.50,
    }
