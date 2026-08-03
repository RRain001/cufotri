from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
ACQUISITION = ROOT / "validation" / "external_evidence_acquisition" / "d3"
MAPPING_PATH = ACQUISITION / "d3_ufotri_manual_data_field_mapping.yaml"
CONTRACT_PATH = ACQUISITION / "requested_file_contract.yaml"
MAPPING = yaml.safe_load(MAPPING_PATH.read_text(encoding="utf-8"))
FIELDS = MAPPING["fields"]
FIELD_BY_ID = {field["field_id"]: field for field in FIELDS}


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_manual_mapping_r1_anchors_and_counts() -> None:
    assert len(FIELDS) == 100
    expected_counts = {
        "MANUAL_EXPLICIT": 36,
        "MANUAL_DERIVED": 10,
        "D3_DESIGN_SPECIFIC": 34,
        "MODERN_QA_REQUIRED": 17,
        "NOT_APPLICABLE_CONTROLLED_CHAMBER": 7,
        "UNRESOLVED_NO_SOURCE": 3,
    }
    actual_counts = {
        category: sum(category in field["category"] for field in FIELDS)
        for category in expected_counts
    }
    assert actual_counts == expected_counts
    assert sum(actual_counts.values()) == 107
    assert FIELD_BY_ID["release_rate"]["manual_reference"] == "5.2.2 Table 3"
    assert FIELD_BY_ID["soil_layer_depths"]["manual_reference"] == (
        "2.2.3; 2.2.4; 2.2.5"
    )
    assert "Figure 13" not in FIELD_BY_ID["soil_layer_depths"][
        "manual_reference"
    ]
    assert FIELD_BY_ID["root_hto_uptake_flux"]["manual_reference"] == (
        "2.2.3; Equation (37); 2.2.5"
    )


def test_unresolved_items_contract_is_traceable_and_fail_closed() -> None:
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    unresolved = contract["unresolved_items"]
    expected_ids = {
        "cultivar_specific_resistance_parameter",
        "chamber_mixing_to_outdoor_wind_transform",
        "root_zone_hto_transfer_function",
    }
    assert len(unresolved) == 3
    assert {item["field_id"] for item in unresolved} == expected_ids
    for item in unresolved:
        assert item["category"] == "UNRESOLVED_NO_SOURCE"
        assert item["action"] == "DEFER_UNRESOLVED"
        assert item["requirement"] == "defer_unresolved"
        assert item["optional"] is True
        assert item["default"] is None
        assert item["model_use_authorized"] is False
        assert item["acceptance_use_authorized"] is False
        assert item["trusted_registry_use_authorized"] is False
        assert item["future_resolution"]["allowed_sources"] == [
            "LABORATORY_DEFINITION",
            "APPROVED_ALTERNATIVE",
        ]
        assert item["future_resolution"]["approval_required"] is True


def test_medium_terminology_is_clarified_without_rewriting_history() -> None:
    historical_docs = (
        ROOT / "docs" / "implementation_status.md",
        ROOT / "docs" / "v3" / "benchmarks"
        / "h2_h3_minimum_discriminating_experiment_spec.md",
        ROOT / "docs" / "v3" / "external_data"
        / "d3_external_evidence_acquisition_report.md",
        ROOT / "docs" / "v3" / "experiments"
        / "d3_prospective_experiment_dry_run_report.md",
    )
    for path in historical_docs:
        text = path.read_text(encoding="utf-8")
        assert "HTO_IN_CHAMBER_AIR_MOISTURE" in text
        assert "air-moisture water" in text
        assert "liquid culture" in text
    derived = (
        ROOT / "docs" / "v3" / "experiments"
        / "d3_ufotri_manual_derived_data_requirements.md"
    ).read_text(encoding="utf-8")
    assert "5270 Bq/mL water" in derived
    assert "5270 Bq/mL air-moisture water" in derived


def test_replicate_semantics_keep_five_as_plan_and_three_as_limited_minimum() -> None:
    boundary = MAPPING["frozen_d3_boundary"]
    assert boundary["biological_replicates_per_primary_time"] == 5
    qc = yaml.safe_load(
        (ACQUISITION / "templates" / "quality_control_checklist.yaml")
        .read_text(encoding="utf-8")
    )
    assert qc["sampling"]["planned_biological_replicates_per_primary_time"] == 5
    assert qc["sampling"]["minimum_uncensored_replicates_per_primary_time"] == 3
    commission = (
        ROOT / "docs" / "v3" / "experiments"
        / "d3_experiment_commission_package.md"
    ).read_text(encoding="utf-8")
    assert (
        "Five biological replicates per destructive sampling time are the current"
        in commission
    )
    assert "Three uncensored biological replicates are a minimum analytical" in commission
    assert "not the recommended" in commission
    spec = (
        ROOT / "docs" / "v3" / "benchmarks"
        / "h2_h3_minimum_discriminating_experiment_spec.md"
    ).read_text(encoding="utf-8")
    spec_flat = " ".join(spec.split())
    assert "planned design uses five" in spec_flat
    assert "does not reduce the allocated plant count" in spec_flat
    assert "same evidence grade" in spec_flat


def test_public_true_reblinding_check_has_no_private_key_fixture_dependency() -> None:
    private_relative = (
        "validation/external_local/d3_prospective_reblind_v3/"
        "sealed_generation_secret.json"
    )
    assert git(
        "ls-files", "--error-unmatch", private_relative
    ).returncode != 0
    assert git("check-ignore", "--quiet", private_relative).returncode == 0
    tracked_paths = git("ls-files").stdout.splitlines()
    assert not any(path.endswith("sealed_generation_secret.json") for path in tracked_paths)
    source = (
        ROOT / "tests" / "independent_review_d3_true_reblinding"
        / "test_d3_true_reblinding_independent_review.py"
    ).read_text(encoding="utf-8")
    public_section = source.split(
        "def test_review_public_secret_integrity_is_portable()", 1
    )[1].split("def test_review_private_secret_matches_commitment_when_available()", 1)[0]
    assert "PRIVATE_SECRET_PATH.is_file()" not in public_section
    assert "SKIP_PRIVATE_SECRET_NOT_AVAILABLE" in source
    commitment_path = (
        ROOT / "validation" / "benchmarks" / "d3_prospective_experiment"
        / "reblinding_v3" / "sealed_generation_secret_sha256"
    )
    commitment = commitment_path.read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"[0-9a-f]{64}", commitment)


def test_remediation_keeps_external_gate_closed_and_does_not_claim_portability() -> None:
    boundary = MAPPING["frozen_d3_boundary"]
    assert boundary["real_external_evidence"] is False
    assert boundary["formal_v3_physics"] == "NOT_STARTED"
    assert boundary["v3_physics_start_gate"] == (
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )
    status = (ROOT / "docs" / "implementation_status.md").read_text(
        encoding="utf-8"
    )
    assert "D3_REAL_EXTERNAL_EVIDENCE = FALSE" in status
    assert "D3_FORMAL_V3_PHYSICS = NOT_STARTED" in status
    assert "D3_FULL_PYTEST = PASS_693_OF_693" not in status
    assert "D3_ACCEPTANCE_AND_VERIFIERS = PASS_WITH_PHYSICS_GATE_BLOCKED" not in status
    report = (
        ROOT / "docs" / "v3" / "experiments"
        / "d3_ufotri_manual_data_mapping_remediation_r1.md"
    ).read_text(encoding="utf-8")
    assert "D3_UFOTRI_MANUAL_DATA_MAPPING_REMEDIATION_R1 = HOLD_UNRESOLVED" in report
    assert "D3_SCOPED_REMEDIATION_SELF_CHECK = PASS_SELF_CHECK" in report
    assert "PORTABLE_RECOMPUTE_STATUS = BLOCKED_MISSING_REQUIRED_EXTERNAL_ERA5_INPUT" in report
    assert "INDEPENDENT_REREVIEW = NOT_STARTED" in report
    assert "MERGE_RECOMMENDATION = DO_NOT_MERGE" in report
