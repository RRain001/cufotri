"""Independent assertions for D1 food-chain/post-RC1 reconciliation."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/run_ufotri_v2_continuous_foodchain_post_rc1_reconciliation_r1.py"
STATUS_PREFIX = "UFOTRI_V2_CONTINUOUS_FOODCHAIN_POST_RC1_STATUS="
RESULT_PREFIX = "UFOTRI_V2_CONTINUOUS_FOODCHAIN_POST_RC1_RESULT_JSON="
EXPECTED_STATUS = "PASS_V2_CONTINUOUS_FOODCHAIN_POST_RC1_RECONCILIATION"


@lru_cache(maxsize=1)
def _result() -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, (
        "D1 machine reconciliation failed.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}"
    )
    status_line = next(
        line for line in completed.stdout.splitlines() if line.startswith(STATUS_PREFIX)
    )
    result_line = next(
        line for line in completed.stdout.splitlines() if line.startswith(RESULT_PREFIX)
    )
    assert status_line == STATUS_PREFIX + EXPECTED_STATUS
    return json.loads(result_line.split("=", 1)[1])


def _by_role() -> dict[str, dict[str, object]]:
    return {item["role"]: item for item in _result()["role_matrix"]}


def test_d1_machine_gate_and_all_named_gates_pass() -> None:
    result = _result()
    assert result["stage"] == "UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1"
    assert result["status"] == EXPECTED_STATUS
    assert all(result["gates"].values())


def test_d1_frozen_v2_evidence_is_resolved_and_preserved_on_main() -> None:
    evidence = _result()["v2_evidence"]
    assert evidence["tag"] == "ufotri-environmental-pathways-v2-candidate"
    assert evidence["annotated_tag_object_sha"] == "11eb90096b2c08a0b40c7cf7f2917d473535e8c7"
    assert evidence["resolved_commit_sha"] == "f097115cbfc052baa18f1e49a1207fa6b3523cff"
    assert evidence["resolved_commit_sha"] == evidence["expected_commit_sha"]
    assert all(evidence["current_blob_checks"].values())
    assert all(evidence["historical_blob_checks"].values())
    assert all(evidence["preserved_byte_identity"].values())


def test_d1_manual_roles_have_explicit_noninflated_dispositions() -> None:
    roles = _by_role()
    assert roles["VEGETABLE_HTO_OBT"]["manual_equations"] == "65-66"
    assert roles["GRASS_ATMOS_SOIL"]["manual_equations"] == "67-81"
    assert roles["COW_WATER_BOUNDARY_LOSS"]["manual_equations"] == "82-84"
    assert roles["MILK_HTO_OBT"]["manual_equations"] == "85-91"
    assert roles["COW_OBT_FORMATION_TURNOVER"]["manual_equations"] == "92-97"
    assert roles["COW_INHALATION_SKIN_UPTAKE"]["manual_equations"] == "98"
    assert roles["GRASS_TO_COW_AND_GRASS_BALANCE"]["manual_equations"] == "99-105-2"
    assert roles["PUBLIC_INHALATION_SKIN_DOSE"]["manual_equations"] == "106"
    assert roles["PUBLIC_INGESTION_DOSE"]["manual_equations"] == "107"

    assert roles["COW_INHALATION_SKIN_UPTAKE"]["disposition"] == (
        "MISSING_IN_V2_ANIMAL_CORE_REQUIRES_D4"
    )
    assert roles["POST_RC1_TERMINAL_FOOD_ENDPOINT"]["disposition"] == (
        "KEEP_FROZEN_DEFAULT_PARALLEL_COMPATIBILITY_PATH"
    )


def test_d1_parameter_provenance_split_does_not_promote_project_values() -> None:
    split = _result()["parameter_origin_split"]
    manual = split["manual_or_manual_converted_candidates"]
    project = split["project_or_application_extensions_not_manual_truth"]
    assert "milk_production_l_day=15.5" in manual
    assert "cow_obt_turnover_rate=0.015 d^-1" in manual
    assert "animal_support_area_m2=4000" in project
    assert "beef_continuous_herd_turnover_rate=0.002 d^-1" in project
    assert "separate_modern_OBT_ingestion_dose_coefficient" in project


def test_d1_reconciliation_only_and_next_stage_partition_are_fail_closed() -> None:
    result = _result()
    decision = result["implementation_decision"]
    assert decision["d1_existing_source_change"] is False
    assert decision["v2_topology_direct_activation"] is False
    assert decision["v2_parameters_direct_activation"] is False
    assert decision["continuous_ufotri_path_required_later"] is True
    assert decision["continuous_ufotri_path_mode"] == "OPT_IN_PARALLEL_COMPATIBILITY_PATH"
    assert decision["rc1_terminal_harvest_default_removed"] is False
    assert decision["rc1_terminal_harvest_default_changed"] is False
    assert decision["historical_v2_mass_closure_is_original_ufotri_algorithm"] is False

    assert result["next_stages"] == [
        "UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY_R1",
        "UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE_R1",
        "UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1",
        "UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1",
    ]
    assert all(value is False for value in result["hard_boundaries"].values())
