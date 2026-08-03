from __future__ import annotations

import hashlib
import inspect
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest
import yaml

from validation import external_input_requirements
from validation.external_input_requirements import (
    DATASET_REQUIREMENTS,
    InputStatus,
    check_dataset,
)


ROOT = Path(__file__).resolve().parents[2]
MAPPING_PATH = (
    ROOT
    / "validation"
    / "external_evidence_acquisition"
    / "d3"
    / "d3_ufotri_manual_data_field_mapping.yaml"
)
CONTRACT_PATH = (
    ROOT
    / "validation"
    / "external_evidence_acquisition"
    / "d3"
    / "requested_file_contract.yaml"
)
BASE_MAIN = "f5d18886f3a635cd6c3a813d820b1f3b3e52dd3a"
ORIGINAL_MAPPING_HEAD = "b88a251f08069329d53290ccf7510080199f0561"
FAILED_REVIEW_HEAD = "fb1c3a20994fc17d2579058ff968c05d561f0a2a"
REMEDIATION_HEAD = "29f59c83cb2ed6b8c4111799a3e3878c8b568b72"
REVIEW_TARGET = "0164a99cae30ab44411fe98be9ea9cc512c51966"
STRICT_MARKER_EXPRESSION = (
    "external_sb1_data or external_sb4_data or external_era5_data"
)
EXTERNAL_MARKER_PATTERN = re.compile(
    r"@pytest\.mark\.(?:external_sb1_data|external_sb4_data|"
    r"external_era5_data|private_reblinding_secret)"
)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def clean_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("CTEAS_EXTERNAL_EVIDENCE_ROOT", None)
    environment.pop("CTEAS_ERA5_INPUT_ROOT", None)
    return environment


def collected_count(output: str) -> int:
    total = 0
    for line in output.splitlines():
        match = re.search(r":\s+(\d+)$", line)
        if match:
            total += int(match.group(1))
    return total


def test_review_target_chain_and_fresh_worktree_identity() -> None:
    assert git("cat-file", "-t", REVIEW_TARGET).stdout.strip() == "commit"
    for parent, child in (
        (BASE_MAIN, ORIGINAL_MAPPING_HEAD),
        (ORIGINAL_MAPPING_HEAD, FAILED_REVIEW_HEAD),
        (FAILED_REVIEW_HEAD, REMEDIATION_HEAD),
        (REMEDIATION_HEAD, REVIEW_TARGET),
        (REVIEW_TARGET, "HEAD"),
    ):
        assert git("merge-base", "--is-ancestor", parent, child).returncode == 0
    assert Path(git("rev-parse", "--show-toplevel").stdout.strip()) == ROOT


def test_manual_sha_counts_and_r1_anchors() -> None:
    mapping = yaml.safe_load(MAPPING_PATH.read_text(encoding="utf-8"))
    fields = mapping["fields"]
    by_id = {field["field_id"]: field for field in fields}
    assert hashlib.sha256((ROOT / "ufotri_manual.md").read_bytes()).hexdigest() == (
        "82c7c7f07975553a51e7ba1666a912f80096e5af4fc138aba6f45a120e6d3562"
    )
    assert len(fields) == 100
    expected = {
        "MANUAL_EXPLICIT": 36,
        "MANUAL_DERIVED": 10,
        "D3_DESIGN_SPECIFIC": 34,
        "MODERN_QA_REQUIRED": 17,
        "NOT_APPLICABLE_CONTROLLED_CHAMBER": 7,
        "UNRESOLVED_NO_SOURCE": 3,
    }
    assert {
        category: sum(category in field["category"] for field in fields)
        for category in expected
    } == expected
    assert by_id["release_rate"]["manual_reference"] == "5.2.2 Table 3"
    assert by_id["soil_layer_depths"]["manual_reference"] == (
        "2.2.3; 2.2.4; 2.2.5"
    )
    assert "Figure 13" not in by_id["soil_layer_depths"]["manual_reference"]
    assert by_id["root_hto_uptake_flux"]["manual_reference"] == (
        "2.2.3; Equation (37); 2.2.5"
    )


def test_all_manual_fields_have_traceable_manual_or_explicit_nonmanual_status() -> None:
    mapping = yaml.safe_load(MAPPING_PATH.read_text(encoding="utf-8"))
    manual_text = (ROOT / "ufotri_manual.md").read_text(encoding="utf-8")
    explicit = [
        field for field in mapping["fields"] if "MANUAL_EXPLICIT" in field["category"]
    ]
    derived = [
        field for field in mapping["fields"] if "MANUAL_DERIVED" in field["category"]
    ]
    assert len(explicit) == 36
    assert len(derived) == 10
    for field in [*explicit, *derived]:
        reference = str(field["manual_reference"])
        assert reference not in {"NO_MANUAL_AUTHORITY", "None"}
        assert any(
            anchor in reference
            for anchor in ("2.2.", "5.2.", "5.3", "Appendix B", "Equation", "Figure", "Table")
        )
    assert "# 2.2.3 Soil/Atmosphere Exchange Processes and Transport in Soil" in manual_text
    assert "# 2.2.5 Uptake of HTO by the Plant Root System" in manual_text


def test_unresolved_contract_is_exactly_three_and_fail_closed() -> None:
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    expected_ids = {
        "cultivar_specific_resistance_parameter",
        "chamber_mixing_to_outdoor_wind_transform",
        "root_zone_hto_transfer_function",
    }
    unresolved = contract["unresolved_items"]
    assert {item["field_id"] for item in unresolved} == expected_ids
    assert len(unresolved) == 3
    for item in unresolved:
        assert item["action"] == "DEFER_UNRESOLVED"
        assert item["default"] is None
        assert item["model_use_authorized"] is False
        assert item["acceptance_use_authorized"] is False
        assert item["trusted_registry_use_authorized"] is False


def test_medium_and_replicate_semantics_are_not_rewritten() -> None:
    mapping = yaml.safe_load(MAPPING_PATH.read_text(encoding="utf-8"))
    boundary = mapping["frozen_d3_boundary"]
    qc = yaml.safe_load(
        (
            ROOT
            / "validation/external_evidence_acquisition/d3/templates/"
            "quality_control_checklist.yaml"
        ).read_text(encoding="utf-8")
    )
    assert boundary["exposure_setpoint_bq_per_ml_air_moisture_water"] == 5270
    assert qc["sampling"]["planned_biological_replicates_per_primary_time"] == 5
    assert qc["sampling"]["minimum_uncensored_replicates_per_primary_time"] == 3
    commission = (
        ROOT / "docs/v3/experiments/d3_experiment_commission_package.md"
    ).read_text(encoding="utf-8")
    assert "5270 Bq/mL air-moisture water" in commission
    assert "Five biological replicates per destructive sampling time" in commission
    assert "Three uncensored biological replicates are a minimum analytical" in commission
    assert "not the recommended" in commission
    relevant = " ".join(
        (
            ROOT / relative
        ).read_text(encoding="utf-8")
        for relative in (
            "docs/v3/experiments/d3_ufotri_manual_derived_data_requirements.md",
            "docs/v3/experiments/d3_prospective_experiment_dry_run_report.md",
            "docs/v3/benchmarks/h2_h3_minimum_discriminating_experiment_spec.md",
        )
    )
    assert not re.search(
        r"recommended(?: design)?[^.]{0,60}\b(?:3|three)\b", relevant, re.IGNORECASE
    )


def test_public_contract_tests_are_unmarked_and_markers_are_registered() -> None:
    marker_names = (
        "external_sb1_data",
        "external_sb4_data",
        "external_era5_data",
        "private_reblinding_secret",
    )
    for relative in ("pyproject.toml", "tests/conftest.py"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for marker in marker_names:
            assert marker in text
    public_paths = (
        "tests/external_evidence_acquisition/test_d3_external_evidence_acquisition.py",
        "tests/external_evidence_acquisition/test_d3_ufotri_manual_data_mapping.py",
        "tests/external_evidence_acquisition/test_d3_ufotri_manual_data_mapping_remediation_r1.py",
        "tests/external_evidence_acquisition/test_external_input_test_portability_r1.py",
        "tests/independent_review_d3_true_reblinding/test_d3_true_reblinding_independent_review.py",
        "tests/prospective_experiment/test_d3_prospective_experiment.py",
    )
    for relative in public_paths:
        assert not EXTERNAL_MARKER_PATTERN.search(
            (ROOT / relative).read_text(encoding="utf-8")
        ), relative


def test_strict_external_marker_selection_is_49() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-m",
            STRICT_MARKER_EXPRESSION,
        ],
        cwd=ROOT,
        env=clean_environment(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert collected_count(result.stdout) == 49


def test_resolver_negative_statuses_and_illegal_env_are_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("CTEAS_EXTERNAL_EVIDENCE_ROOT", raising=False)
    assert check_dataset(ROOT, "SB1").status is InputStatus.MISSING
    external_root = tmp_path / "external-root"
    dataset = external_root / "emras_soybean_sb1"
    dataset.mkdir(parents=True)
    monkeypatch.setenv("CTEAS_EXTERNAL_EVIDENCE_ROOT", str(external_root))
    assert check_dataset(ROOT, "SB1").status is InputStatus.INCOMPLETE
    dataset.rmdir()
    dataset.write_text("not a directory", encoding="utf-8")
    assert check_dataset(ROOT, "SB1").status is InputStatus.INVALID
    illegal = tmp_path / "illegal-explicit-root"
    monkeypatch.setenv("CTEAS_EXTERNAL_EVIDENCE_ROOT", str(illegal))
    result = check_dataset(ROOT, "SB1")
    assert result.status is InputStatus.MISSING
    assert result.root == illegal / "emras_soybean_sb1"


def test_invalid_input_is_not_converted_to_a_skip(tmp_path: Path) -> None:
    external_root = tmp_path / "invalid-root"
    external_root.mkdir()
    (external_root / "emras_soybean_sb1").write_text(
        "not a directory", encoding="utf-8"
    )
    environment = clean_environment()
    environment["CTEAS_EXTERNAL_EVIDENCE_ROOT"] = str(external_root)
    node = (
        "tests/independent_review_sb1/test_emras_soybean_sb1_independent_review.py::"
        "test_independent_chamber_era5_boundary_alignment"
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", node],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "STATUS = INVALID" in output
    assert "SKIP_EXTERNAL_SB1_INPUT_NOT_AVAILABLE" not in output


def test_resolver_has_no_other_worktree_home_cache_or_network_search() -> None:
    source = inspect.getsource(external_input_requirements).lower()
    assert "rglob" not in source
    assert "path.home" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "download(" not in source
    assert set(DATASET_REQUIREMENTS) == {
        "SB1",
        "SB4",
        "ERA5_ACCEPTANCE",
        "D3_PRIVATE_REBLIND_SECRET",
    }


@pytest.mark.parametrize(
    "arguments",
    (
        ("scripts/verify_acceptance.py", "--recompute"),
        ("scripts/verify_v2_acceptance.py", "--recompute"),
        ("scripts/verify_v3_compatibility.py",),
        ("scripts/verify_v3_architecture_readiness.py",),
    ),
)
def test_era5_verifiers_exit_two_before_numeric_logic(
    arguments: tuple[str, ...],
) -> None:
    result = subprocess.run(
        [sys.executable, *arguments],
        cwd=ROOT,
        env=clean_environment(),
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 2
    assert "STATUS = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT" in output
    assert "DATASET = ERA5_ACCEPTANCE" in output
    assert "era5_surface_2025-06-01_2025-06-02.csv" in output


def test_public_true_reblinding_contract_has_no_private_payload() -> None:
    root = ROOT / "validation/benchmarks/d3_prospective_experiment/reblinding_v3"
    generation = yaml.safe_load(
        (root / "generation_manifest_v3.yaml").read_text(encoding="utf-8")
    )
    classification = yaml.safe_load(
        (root / "classification/blind_classification_manifest_v3.yaml").read_text(
            encoding="utf-8"
        )
    )
    unblinding = yaml.safe_load(
        (root / "unblinding/unblinding_manifest_v3.yaml").read_text(encoding="utf-8")
    )
    commitment = (root / "sealed_generation_secret_sha256").read_text(
        encoding="utf-8"
    ).strip()
    assert re.fullmatch(r"[0-9a-f]{64}", commitment)
    assert generation["real_external_evidence"] is False
    assert classification["truth_key_accessed"] is False
    assert classification["secret_accessed"] is False
    assert unblinding["sealed_generation_secret_sha256_verified"] is True
    private = ROOT / "validation/external_local/d3_prospective_reblind_v3"
    assert not (private / "sealed_generation_secret.json").is_file()
    assert not (private / "truth_key_v3.json").is_file()
    tracked = git("ls-files").stdout.splitlines()
    assert not any(path.endswith("sealed_generation_secret.json") for path in tracked)
    assert not any(path.endswith("truth_key_v3.json") for path in tracked)


def test_reblinding_public_classification_and_unblinding_code_is_unchanged() -> None:
    changed = set(
        git(
            "diff",
            "--name-only",
            REMEDIATION_HEAD,
            REVIEW_TARGET,
        ).stdout.splitlines()
    )
    assert "validation/benchmarks/d3_prospective_experiment/scripts/generate_d3_true_reblinding_v3.py" not in changed
    assert "validation/benchmarks/d3_prospective_experiment/scripts/classify_d3_true_reblinding_v3.py" not in changed
    assert "validation/benchmarks/d3_prospective_experiment/scripts/unblind_d3_true_reblinding_v3.py" not in changed
    assert "validation/benchmarks/d3_prospective_experiment/scripts/d3_true_reblinding_v3_common.py" in changed
    assert "dataset_root" in git(
        "diff",
        REMEDIATION_HEAD,
        REVIEW_TARGET,
        "--",
        "validation/benchmarks/d3_prospective_experiment/scripts/d3_true_reblinding_v3_common.py",
    ).stdout


def test_model_configs_registry_and_frozen_parameter_scope_are_unchanged() -> None:
    for pathspec in (
        "src",
        "configs",
        "validation/v3/policy/trusted_external_evidence_registry.yaml",
        "validation/benchmarks/emras_soybean_sb1_mechanisms/reports/frozen_mechanism_parameters.yaml",
        "validation/benchmarks/emras_soybean_sb4/preregistration/sb4_transfer_protocol.yaml",
    ):
        assert git(
            "diff",
            "--quiet",
            BASE_MAIN,
            REVIEW_TARGET,
            "--",
            pathspec,
        ).returncode == 0, pathspec


def test_no_tracked_raw_external_payload_or_v3_tag_was_added() -> None:
    tracked = git("ls-files").stdout.splitlines()
    allowed_external_local = {
        "validation/external_local/.gitignore",
        "validation/external_local/README.md",
    }
    assert not any(
        path.startswith("validation/external_local/")
        and path not in allowed_external_local
        for path in tracked
    )
    assert not any(
        path.endswith((".nc", ".pdf", "sealed_generation_secret.json", "truth_key_v3.json"))
        for path in tracked
    )
    changed = git(
        "diff",
        "--name-only",
        REMEDIATION_HEAD,
        REVIEW_TARGET,
    ).stdout.splitlines()
    assert not any(
        path.endswith((".nc", ".pdf", "sealed_generation_secret.json", "truth_key_v3.json"))
        or "external_local" in path
        for path in changed
    )
    assert not any("v3" in tag.lower() for tag in git("tag", "--list").stdout.splitlines())


def test_no_broad_catch_or_broad_catch_and_skip_was_added() -> None:
    diff = git("diff", REMEDIATION_HEAD, REVIEW_TARGET).stdout
    added = "\n".join(line for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    assert not re.search(r"^\+.*except\s*(Exception|:)", diff, re.MULTILINE)
    assert "pytest.skip" in added
    assert "check.status is InputStatus.MISSING" in added


def test_public_request_manifest_templates_and_gate_boundary_remain_closed() -> None:
    mapping = yaml.safe_load(MAPPING_PATH.read_text(encoding="utf-8"))
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    manifest = yaml.safe_load(
        (
            ROOT
            / "validation/external_evidence_acquisition/d3/templates/raw_manifest_template.yaml"
        ).read_text(encoding="utf-8")
    )
    request = yaml.safe_load(
        (
            ROOT
            / "validation/external_evidence_acquisition/d3/requested_file_contract.yaml"
        ).read_text(encoding="utf-8")
    )
    assert request["request_status"] == "DRAFT_READY_NOT_SENT"
    assert request["intake_boundary"]["trusted_registry_change_authorized"] is False
    assert "plant_material" in request["required_data_groups"]
    assert manifest["files"][0]["immutable_read_only_copy"] == "REQUIRED_BOOLEAN"
    assert manifest["files"][0]["sha256"] == "REQUIRED_64_LOWERCASE_HEX"
    assert contract["intake_boundary"]["trusted_registry_change_authorized"] is False
    boundary = mapping["frozen_d3_boundary"]
    assert boundary["real_external_evidence"] is False
    assert boundary["formal_v3_physics"] == "NOT_STARTED"
    assert boundary["v3_physics_start_gate"] == (
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )


def test_external_gate_scripts_remain_fail_closed() -> None:
    unblocking = subprocess.run(
        [sys.executable, "scripts/verify_v3_external_evidence_unblocking.py"],
        cwd=ROOT,
        env=clean_environment(),
        capture_output=True,
        text=True,
        check=False,
    )
    physics = subprocess.run(
        [sys.executable, "scripts/verify_v3_physics_start_gate.py"],
        cwd=ROOT,
        env=clean_environment(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert unblocking.returncode == 0
    assert physics.returncode == 0
    assert "READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA" in (
        unblocking.stdout + unblocking.stderr
    )
    assert "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA" in (
        physics.stdout + physics.stderr
    )
