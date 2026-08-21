"""Executable protection checks for the P5.6 architecture reconciliation."""

from pathlib import Path
import subprocess

from cteas_ufotri.parameters import ParameterDatabase


ROOT = Path(__file__).resolve().parents[2]
BASE_MAIN_SHA = "6671f5793d04842bf2ceae4904f3c0cf30a0d7e0"
AUDIT_TARGET_SHA = "3e6ac7bcc10b9ea7e5b896e3e8aa4e6d9d1d3cfa"
REPORT = ROOT / "docs/v3/reports/v3_p5_6_architecture_reconciliation_report.md"
BOUNDARY = ROOT / "docs/v3/architecture/framework_vs_physics_boundary.md"
ROADMAP = ROOT / "docs/v3/roadmap/v3_physics_roadmap.md"
STATUS = ROOT / "docs/implementation_status.md"
README = ROOT / "README.md"
DATABASE_DIR = ROOT / "parameters/databases"
PHYSICS_FILES = (
    ROOT / "src/cteas_ufotri/leaf_exchange/physics.py",
    ROOT / "src/cteas_ufotri/soil/physics.py",
    ROOT / "src/cteas_ufotri/food_chain/physics.py",
    ROOT / "src/cteas_ufotri/dose/physics.py",
)
UNIT_FILES = (
    ROOT / "tests/unit/test_leaf_exchange.py",
    ROOT / "tests/unit/test_soil_layer.py",
    ROOT / "tests/unit/test_food_chain.py",
    ROOT / "tests/unit/test_dose.py",
)


def _git_names(revision: str, *paths: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", revision, "--", *paths],
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


def test_ufotri_parameter_imported_is_false() -> None:
    database_paths = sorted(DATABASE_DIR.glob("*.yaml"))
    assert database_paths

    active_validated = []
    for path in database_paths:
        database = ParameterDatabase.load(path)
        assert database.list_parameters()
        for name in database.list_parameters():
            entry = database.get_entry(name)
            provenance = database.get_provenance(name)
            if (
                entry.value is not None
                and entry.status == "ACTIVE"
                and entry.confidence == "validated"
                and provenance.source_status == "validated"
                and provenance.production_allowed
                and provenance.applicability["status"] == "applicable"
            ):
                active_validated.append((path.name, name))

    assert active_validated == []
    report = REPORT.read_text(encoding="utf-8")
    assert "UFOTRI_PARAMETER_IMPORTED = FALSE" in report
    assert "UFOTRI_VALIDATED_DATABASE = ABSENT" in report


def test_active_validated_database_is_false() -> None:
    source_registry = (ROOT / "parameters/parameter_sources.yaml").read_text(
        encoding="utf-8"
    )
    assert "UFOTRI_VALIDATED:" in source_registry
    assert "status: external_reference_required" in source_registry
    assert "production_allowed: false" in source_registry

    placeholder = ParameterDatabase.load(
        DATABASE_DIR / "ufotri_leaf_exchange.yaml"
    )
    assert all(
        placeholder.get_entry(name).value is None
        for name in placeholder.list_parameters()
    )


def test_formal_physics_has_not_started() -> None:
    for path in PHYSICS_FILES:
        source = path.read_text(encoding="utf-8")
        assert "class FrameworkOnlyPhysics" in source
        assert "PHYSICS_PENDING_UFOTRI_MIGRATION" in source

    report = REPORT.read_text(encoding="utf-8")
    boundary = BOUNDARY.read_text(encoding="utf-8")
    assert "V3_FORMAL_PHYSICS = NOT_STARTED" in report
    assert "PHYSICS_READY = FALSE" in report
    assert "Formal V3 physics has not started" in boundary


def test_synthetic_kernels_are_framework_test_only() -> None:
    for path in UNIT_FILES:
        source = path.read_text(encoding="utf-8")
        assert 'TEST_CLASSIFICATION = "FRAMEWORK_TEST_ONLY"' in source
        assert 'SYNTHETIC_KERNEL_STATUS = "NOT_VALIDATED_UFOTRI_PHYSICS"' in source

    for path in PHYSICS_FILES:
        source = path.read_text(encoding="utf-8")
        assert "TEST_ONLY" in source

    boundary = BOUNDARY.read_text(encoding="utf-8")
    assert "not UFOTRI equations" in boundary
    assert "FRAMEWORK_TEST_ONLY" in boundary


def test_p56_protects_source_configuration_parameters_and_registry() -> None:
    protected = (
        "src",
        "configs",
        "parameters",
        "schemas",
        "validation/v3/policy/trusted_external_evidence_registry.yaml",
    )
    assert _git_names(AUDIT_TARGET_SHA, *protected) == set()
    assert _untracked_names(*protected) == set()

    assert _git_names(BASE_MAIN_SHA, "configs") == set()
    assert _git_names(
        BASE_MAIN_SHA,
        "validation/v3/policy/trusted_external_evidence_registry.yaml",
    ) == set()


def test_reconciliation_documents_agree() -> None:
    report = REPORT.read_text(encoding="utf-8")
    status = STATUS.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")

    assert "UFOTRI_PHYSICS_IMPLEMENTED = FALSE" in report
    assert "UFOTRI_PARAMETER_IMPORTED = FALSE" in report
    assert "UFOTRI_VALIDATED_DATABASE = ABSENT" in report
    assert "UFOTRI_PHYSICS_IMPLEMENTATION = NOT_STARTED" in status
    assert "UFOTRI_VALIDATED_DATABASE = ABSENT" in status
    assert "UFOTRI_PHYSICS_IMPLEMENTATION = NOT_STARTED" in readme
    assert "UFOTRI_VALIDATED_DATABASE = ABSENT" in readme
    assert "UFOTRI_PHYSICS_IMPLEMENTED: false" in roadmap
    assert "UFOTRI_PARAMETER_IMPORTED: false" in roadmap

    assert "P5_6_STATUS = PASS_RECONCILED" in report
    for marker in (
        "P5_STATUS = COMPLETE_WITH_RECLASSIFICATION",
        "FRAMEWORK_READY = TRUE",
        "PHYSICS_READY = FALSE",
        "NEXT_PHASE = UFOTRI_PARAMETER_AND_PHYSICS_IMPLEMENTATION",
    ):
        assert marker in report
        assert marker in status or marker in readme or marker in roadmap
