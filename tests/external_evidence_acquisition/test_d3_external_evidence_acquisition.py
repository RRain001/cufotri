from __future__ import annotations

import copy
import csv
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
ACQUISITION = ROOT / "validation" / "external_evidence_acquisition" / "d3"
PROTOCOL = yaml.safe_load(
    (ACQUISITION / "d3_external_data_search_protocol.yaml").read_text(
        encoding="utf-8"
    )
)
INVENTORY = yaml.safe_load(
    (ACQUISITION / "d3_external_data_candidate_inventory.yaml").read_text(
        encoding="utf-8"
    )
)
REQUEST = yaml.safe_load(
    (ACQUISITION / "requested_file_contract.yaml").read_text(encoding="utf-8")
)
QC = yaml.safe_load(
    (ACQUISITION / "templates" / "quality_control_checklist.yaml").read_text(
        encoding="utf-8"
    )
)
MANIFEST_TEMPLATE = yaml.safe_load(
    (ACQUISITION / "templates" / "raw_manifest_template.yaml").read_text(
        encoding="utf-8"
    )
)

MISSING = set(PROTOCOL["candidate_inventory"]["missing_value_tokens"])
REQUIRED_FIELDS = set(PROTOCOL["candidate_inventory"]["required_fields"])
CRITERIA = list(PROTOCOL["scoring"]["criteria"])


def _assert_nonempty_known_or_missing(value: Any) -> None:
    assert value is not None
    if isinstance(value, str):
        assert value.strip()
        if value.startswith(("UNKNOWN_", "NOT_REPORTED_", "NOT_AVAILABLE_")):
            raise AssertionError("missing values must use an exact frozen token")


def _validate_candidate(candidate: dict[str, Any]) -> None:
    assert REQUIRED_FIELDS <= candidate.keys()
    for field in REQUIRED_FIELDS:
        _assert_nonempty_known_or_missing(candidate[field])

    assert set(candidate["criterion_scores"]) == set(CRITERIA)
    assert all(
        isinstance(score, int) and 0 <= score <= 2
        for score in candidate["criterion_scores"].values()
    )
    scores = candidate["criterion_scores"]
    groups = INVENTORY["score_aggregation"]
    assert candidate["exact_match_score"] == sum(
        scores[name] for name in groups["exact_match_score"]
    )
    assert candidate["forcing_completeness_score"] == sum(
        scores[name] for name in groups["forcing_completeness_score"]
    )
    assert candidate["observation_completeness_score"] == sum(
        scores[name] for name in groups["observation_completeness_score"]
    )
    assert candidate["licence_score"] == sum(
        scores[name] for name in groups["licence_score"]
    )
    assert candidate["overall_executability_score"] == sum(scores.values())

    tier = candidate["tier"]
    assert tier in PROTOCOL["candidate_tiers"]
    if tier == "TIER_A":
        assert candidate["crop"] == "soybean"
        assert 20 <= float(candidate["exposure_duration_h"]) <= 28
        assert scores["SAMPLE_0P2H_MATCH"] == 2
        assert scores["SAMPLE_48H_MATCH"] == 2
        assert scores["SAMPLE_120H_MATCH"] == 2
        assert scores["TOTAL_PLANT_BODY_TFWT"] == 2
        assert scores["AIR_HTO_FORCING_COMPLETENESS"] == 2
        assert scores["BACKGROUND_HTO_COMPLETENESS"] == 2
        assert scores["TEMPERATURE_RH_MIXING_COMPLETENESS"] == 2
        assert candidate["numeric_table_available"] or candidate["raw_data_available"]
        assert candidate["executable_status"] == "EXECUTABLE_FOR_FROZEN_D3"
    if tier == "TIER_B":
        assert candidate["executable_status"] != "EXECUTABLE_FOR_FULL_D3_VALIDATION"
        assert 12 <= float(candidate["exposure_duration_h"]) <= 48
    if tier == "NON_EXECUTABLE":
        assert not candidate["registry_eligible"]
        assert "EXECUTABLE_FOR_FROZEN_D3" not in candidate["executable_status"]

    if candidate["registry_eligible"]:
        assert candidate["licence"] not in MISSING
        assert candidate["redistribution_allowed"] is True
    if candidate["synthetic"]:
        assert not candidate["raw_data_available"]
        assert candidate["tier"] == "NON_EXECUTABLE"
        assert "EXECUTABLE" not in candidate["executable_status"].replace(
            "NON_EXECUTABLE", ""
        )
    if candidate["tfwt_observable"] == "OBT_ONLY":
        assert candidate["tier"] == "NON_EXECUTABLE"


def _validate_request(request: dict[str, Any]) -> None:
    if request["request_status"] == "DRAFT_READY_NOT_SENT":
        assert request["request_sent"] is False
    assert request["automatic_contact_authorized"] is False


def _validate_raw_tracking(paths: list[str]) -> None:
    assert not any(path.startswith("validation/external_local/") for path in paths)


def test_d3_candidate_inventory_schema() -> None:
    assert len(INVENTORY["candidates"]) == 8
    for candidate in INVENTORY["candidates"]:
        _validate_candidate(candidate)

    with (ACQUISITION / "d3_external_data_candidate_inventory.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(INVENTORY["candidates"])
    assert REQUIRED_FIELDS <= set(rows[0])
    assert all(None not in row for row in rows)


def test_candidate_tier_rules() -> None:
    counts = {
        tier: sum(c["tier"] == tier for c in INVENTORY["candidates"])
        for tier in PROTOCOL["candidate_tiers"]
    }
    assert counts == INVENTORY["tier_counts"]
    assert counts == {
        "TIER_A": 0,
        "TIER_B": 0,
        "TIER_C": 3,
        "NON_EXECUTABLE": 5,
    }


def test_non_executable_candidate_cannot_be_promoted() -> None:
    candidate = copy.deepcopy(INVENTORY["candidates"][3])
    candidate["registry_eligible"] = True
    with pytest.raises(AssertionError):
        _validate_candidate(candidate)


def test_unknown_fields_not_filled_with_guesses() -> None:
    for candidate in INVENTORY["candidates"]:
        for field in REQUIRED_FIELDS:
            _assert_nonempty_known_or_missing(candidate[field])
    candidate = copy.deepcopy(INVENTORY["candidates"][0])
    candidate["detection_limit"] = "UNKNOWN_ESTIMATED_FROM_FIGURE"
    with pytest.raises(AssertionError):
        _validate_candidate(candidate)


def test_raw_files_not_tracked_by_git() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "validation/external_local"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert not any("/raw/" in path for path in tracked)
    assert set(tracked) <= {
        "validation/external_local/.gitignore",
        "validation/external_local/README.md",
    }
    ignore = (ROOT / "validation" / "external_local" / ".gitignore").read_text(
        encoding="utf-8"
    )
    assert ignore.splitlines()[0] == "*"


def test_manifest_contains_sha256() -> None:
    file_contract = MANIFEST_TEMPLATE["files"][0]
    assert "sha256" in file_contract
    assert file_contract["sha256"] == "REQUIRED_64_LOWERCASE_HEX"
    assert re.fullmatch(r"[0-9a-f]{64}", "0" * 64)


def test_licence_required_before_registry() -> None:
    assert REQUEST["intake_boundary"]["licence_review_required"] is True
    assert REQUEST["intake_boundary"]["trusted_registry_change_authorized"] is False
    assert all(not candidate["registry_eligible"] for candidate in INVENTORY["candidates"])


def test_request_status_not_claimed_sent() -> None:
    _validate_request(REQUEST)
    email = (
        ROOT / "docs" / "v3" / "external_data" / "d3_data_request_email_draft.md"
    ).read_text(encoding="utf-8")
    assert "REQUEST_STATUS = DRAFT_READY_NOT_SENT" in email
    assert "It has not been sent" in email


def test_minimum_experiment_is_six_day_schedule() -> None:
    schedule = QC["minimum_schedule"]
    assert schedule["exposure_duration_h"]["required"] == 24
    assert schedule["post_exposure_followup_h"]["required"] == 120
    assert schedule["total_elapsed_h"]["required"] == 144
    assert 144 / 24 == 6


def test_extended_followup_is_optional() -> None:
    extended = QC["minimum_schedule"]["extended_120_day_followup"]
    assert extended == {"required": False, "status": "OPTIONAL"}
    package = (
        ROOT / "docs" / "v3" / "experiments" / "d3_experiment_commission_package.md"
    ).read_text(encoding="utf-8")
    assert "EXTENDED_120_DAY_FOLLOWUP=OPTIONAL" in package


def test_no_external_validation_run_before_registry() -> None:
    boundary = REQUEST["intake_boundary"]
    assert boundary["trusted_registry_change_authorized"] is False
    assert boundary["h2_h3_run_authorized"] is False
    assert boundary["observation_unblinding_authorized"] is False
    assert boundary["formal_external_validation_authorized"] is False


def test_acquisition_branch_not_production_gate_eligible() -> None:
    assert PROTOCOL["scope"]["production_gate_eligible"] is False
    assert REQUEST["intake_boundary"]["production_gate_eligible"] is False
    assert (
        REQUEST["intake_boundary"]["v3_physics_start_gate"]
        == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )


def test_public_raw_and_numeric_status_are_not_conflated() -> None:
    assert INVENTORY["public_raw_data_found"] is False
    assert INVENTORY["public_numeric_data_found"] is True
    assert INVENTORY["raw_file_download_count"] == 0


def test_emras_attachment_status_is_fail_closed() -> None:
    assert set(INVENTORY["emras_attachments"].values()) == {
        "REFERENCED_NOT_ACCESSIBLE"
    }


def test_attack_tier_a_without_air_hto_fails() -> None:
    candidate = copy.deepcopy(INVENTORY["candidates"][0])
    candidate["tier"] = "TIER_A"
    candidate["exposure_duration_h"] = 24
    candidate["executable_status"] = "EXECUTABLE_FOR_FROZEN_D3"
    candidate["criterion_scores"].update(
        {
            "EXPOSURE_24H_MATCH": 2,
            "SAMPLE_0P2H_MATCH": 2,
            "SAMPLE_48H_MATCH": 2,
            "SAMPLE_120H_MATCH": 2,
            "TOTAL_PLANT_BODY_TFWT": 2,
            "AIR_HTO_FORCING_COMPLETENESS": 0,
            "BACKGROUND_HTO_COMPLETENESS": 2,
            "TEMPERATURE_RH_MIXING_COMPLETENESS": 2,
        }
    )
    groups = INVENTORY["score_aggregation"]
    scores = candidate["criterion_scores"]
    candidate["exact_match_score"] = sum(
        scores[name] for name in groups["exact_match_score"]
    )
    candidate["forcing_completeness_score"] = sum(
        scores[name] for name in groups["forcing_completeness_score"]
    )
    candidate["overall_executability_score"] = sum(scores.values())
    with pytest.raises(AssertionError):
        _validate_candidate(candidate)


def test_attack_registry_without_licence_fails() -> None:
    candidate = copy.deepcopy(INVENTORY["candidates"][0])
    candidate["registry_eligible"] = True
    candidate["licence"] = "UNKNOWN"
    with pytest.raises(AssertionError):
        _validate_candidate(candidate)


def test_attack_obt_only_marked_d3_executable_fails() -> None:
    candidate = copy.deepcopy(INVENTORY["candidates"][0])
    candidate["tfwt_observable"] = "OBT_ONLY"
    candidate["tier"] = "TIER_A"
    candidate["executable_status"] = "EXECUTABLE_FOR_FROZEN_D3"
    with pytest.raises(AssertionError):
        _validate_candidate(candidate)


def test_attack_email_draft_marked_sent_fails() -> None:
    request = copy.deepcopy(REQUEST)
    request["request_sent"] = True
    with pytest.raises(AssertionError):
        _validate_request(request)


def test_attack_synthetic_csv_marked_real_experiment_fails() -> None:
    candidate = copy.deepcopy(INVENTORY["candidates"][0])
    candidate["synthetic"] = True
    candidate["raw_data_available"] = True
    candidate["tier"] = "TIER_A"
    candidate["executable_status"] = "EXECUTABLE_FOR_FROZEN_D3"
    with pytest.raises(AssertionError):
        _validate_candidate(candidate)


def test_attack_ignored_raw_file_added_to_git_fails() -> None:
    with pytest.raises(AssertionError):
        _validate_raw_tracking(
            ["validation/external_local/d3_candidate_D3C-001/raw/sbTbox.xls"]
        )
