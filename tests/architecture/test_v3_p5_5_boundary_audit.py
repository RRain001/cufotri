"""Executable checks for the P5.5 repository boundary audit."""

from pathlib import Path
import subprocess

from cteas_ufotri.parameters import ParameterDatabase


ROOT = Path(__file__).resolve().parents[2]
P54_SHA = "9e783acb0734d40347e845f1cf17d10f10cef9ab"
REPORT = ROOT / "docs/v3/reports/v3_p5_5_boundary_audit_report.md"
LEAF_AUDIT = ROOT / "docs/v3/audit/leaf_exchange_boundary_audit.md"
SOIL_AUDIT = ROOT / "docs/v3/audit/soil_boundary_audit.md"
FOOD_DOSE_AUDIT = ROOT / "docs/v3/audit/foodchain_dose_boundary_audit.md"
PARAM_AUDIT = ROOT / "docs/v3/audit/ufotri_parameter_import_audit.md"
GIT_AUDIT = ROOT / "docs/v3/audit/p5_5_git_boundary_report.md"
LEAF_PHYSICS = ROOT / "src/cteas_ufotri/leaf_exchange/physics.py"
SOIL_PHYSICS = ROOT / "src/cteas_ufotri/soil/physics.py"
SOIL_MULTIBOX = ROOT / "src/cteas_ufotri/soil/multibox.py"
FOOD_PHYSICS = ROOT / "src/cteas_ufotri/food_chain/physics.py"
DOSE_PHYSICS = ROOT / "src/cteas_ufotri/dose/physics.py"
PLACEHOLDER_DB = ROOT / "parameters/databases/ufotri_leaf_exchange.yaml"


def _git_names(*paths: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", P54_SHA, "--", *paths],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def _untracked_names(*paths: str) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", *paths],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def test_leaf_and_soil_audits_record_actual_numerical_harnesses() -> None:
    leaf_source = LEAF_PHYSICS.read_text(encoding="utf-8")
    soil_source = SOIL_PHYSICS.read_text(encoding="utf-8")
    multibox_source = SOIL_MULTIBOX.read_text(encoding="utf-8")
    leaf_audit = LEAF_AUDIT.read_text(encoding="utf-8")
    soil_audit = SOIL_AUDIT.read_text(encoding="utf-8")

    assert "class SyntheticLinearLeafExchangePhysics" in leaf_source
    assert "target_tfwt_inventory" in leaf_source
    assert "class SyntheticTransportKernel" in soil_source
    assert "advance_three_box_soil" in multibox_source
    assert "diffusion" in multibox_source
    assert "root_uptake" in multibox_source
    assert "TEST_ONLY_TFWT_NUMERICAL_EVOLUTION = PRESENT" in leaf_audit
    assert "EXISTING_THREE_BOX_TRANSPORT_ROOT_DIFFUSION = PRESENT_IN_MAIN_BASELINE" in soil_audit


def test_food_chain_and_dose_tests_are_classified_from_actual_content() -> None:
    food_source = FOOD_PHYSICS.read_text(encoding="utf-8")
    dose_source = DOSE_PHYSICS.read_text(encoding="utf-8")
    food_tests = (ROOT / "tests/unit/test_food_chain.py").read_text(encoding="utf-8")
    dose_tests = (ROOT / "tests/unit/test_dose.py").read_text(encoding="utf-8")
    audit = FOOD_DOSE_AUDIT.read_text(encoding="utf-8")

    assert "class SyntheticTransferKernel" in food_source
    assert "class SyntheticDoseKernel" in dose_source
    assert "SyntheticTransferKernel" in food_tests
    assert "SyntheticDoseKernel" in dose_tests
    assert "pytest.approx" in food_tests
    assert "pytest.approx" in dose_tests
    assert "PREMATURE_PHYSICS_TEST" in audit


def test_parameter_import_audit_is_backed_by_loader_and_file_content() -> None:
    database = ParameterDatabase.load(PLACEHOLDER_DB)
    assert database.list_parameters()
    assert all(
        database.get_entry(name).value is None for name in database.list_parameters()
    )
    audit = PARAM_AUDIT.read_text(encoding="utf-8")
    assert "UFOTRI_PARAMETER_IMPORTED = FALSE" in audit
    assert "VALIDATED_UFOTRI_VALUE_PRESENT = FALSE" in audit


def test_p55_does_not_modify_protected_paths() -> None:
    protected = (
        "src",
        "configs",
        "parameters",
        "schemas",
        "validation/v3/policy/trusted_external_evidence_registry.yaml",
    )
    assert _git_names(*protected) == set()
    assert _untracked_names(*protected) == set()


def test_git_audit_reports_cumulative_and_p54_delta_boundaries() -> None:
    audit = GIT_AUDIT.read_text(encoding="utf-8")
    for marker in (
        "39 changed paths relative to main",
        "P5_4_DELTA_PROTECTED_PATH_CHANGE = 0",
        "CONFIG_CHANGE = 0",
        "VALIDATED_DATABASE_CHANGE = 0",
        "NO_MERGE = TRUE",
        "NO_REBASE = TRUE",
    ):
        assert marker in audit


def test_final_classification_requires_roadmap_reclassification() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for marker in (
        "V3_P5_5_STATUS = REQUIRES_PHASE_RECLASSIFICATION",
        "P5_5_RESULT = REQUIRES_PHASE_RECLASSIFICATION",
        "NEXT = UPDATE_ROADMAP",
        "UFOTRI_PHYSICS_IMPLEMENTED = FALSE",
        "UFOTRI_PARAMETER_IMPORTED = FALSE",
        "V3_FORMAL_PHYSICS = NOT_STARTED",
        "SRC_CHANGE = 0",
        "CONFIG_CHANGE = 0",
        "SCHEMA_CHANGE = 0",
        "TRUSTED_REGISTRY_CHANGE = 0",
    ):
        assert marker in report
