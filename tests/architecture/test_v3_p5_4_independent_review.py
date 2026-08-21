"""Independent architecture checks for the V3-P5.4 review boundary."""

from pathlib import Path
import subprocess

from cteas_ufotri.parameters import ParameterDatabase


ROOT = Path(__file__).resolve().parents[2]
P53_SHA = "14e490759459b5beedff1c71591d1aa5f7d1776a"
ATMOSPHERIC = ROOT / "docs/v3/interfaces/atmospheric_hto_forcing_contract.md"
ATMOS_REVIEW = ROOT / "docs/v3/reviews/atmospheric_interface_review.md"
PLANT_REVIEW = ROOT / "docs/v3/reviews/plant_pathway_review.md"
INTERFACE_REVIEW = ROOT / "docs/v3/reviews/interface_consistency_review.md"
PARAMETER_REVIEW = ROOT / "docs/v3/reviews/parameter_database_review.md"
PHYSICS_REVIEW = ROOT / "docs/v3/reviews/physics_migration_boundary_review.md"
PLANT_ADR = ROOT / "docs/v3/architecture/ADR-010-plant-dual-pathway-model.md"
PARAMETER_ADR = ROOT / "docs/v3/architecture/ADR-011-parameter-database-extension.md"
FLUX = ROOT / "docs/v3/architecture/leaf_exchange_flux_contract.md"
REGRESSION = ROOT / "docs/v3/validation/ufotri_physics_regression_contract.md"
REPORT = ROOT / "docs/v3/reports/v3_p5_4_independent_architecture_review.md"
PLACEHOLDER_DB = ROOT / "parameters/databases/ufotri_leaf_exchange.yaml"
LEAF_PHYSICS = ROOT / "src/cteas_ufotri/leaf_exchange/physics.py"
SOIL_MODEL = ROOT / "src/cteas_ufotri/soil/model.py"


def _git_names(*paths: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", P53_SHA, "--", *paths],
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


def test_interface_consistency_is_explicit_across_reviews() -> None:
    atmospheric = ATMOSPHERIC.read_text(encoding="utf-8")
    for field in (
        "`time`",
        "`air_hto_concentration`",
        "`air_temperature`",
        "`relative_humidity`",
        "`surface_deposition_flux`",
    ):
        assert field in atmospheric
    assert "Timezone-aware UTC" in atmospheric
    assert "artifact_sha256" in atmospheric
    assert "FAIL_CLOSED" in atmospheric

    flux = FLUX.read_text(encoding="utf-8")
    for field in (
        "air_to_leaf_flux",
        "stomatal_flux",
        "cuticular_flux",
        "tfwt_to_obt_flux",
        "decay_flux",
    ):
        assert f"`{field}`" in flux

    interface_review = INTERFACE_REVIEW.read_text(encoding="utf-8")
    assert "PASS_WITH_DECLARED_P6_PREREQUISITES" in interface_review
    assert "Internal TFWT-to-OBT transfer" in interface_review


def test_atmospheric_review_covers_raw_cteas_atmos_outputs() -> None:
    review = ATMOS_REVIEW.read_text(encoding="utf-8")
    for finding in (
        "3D air-concentration field",
        "Surface concentration",
        "Surface deposition flux",
        "Meteorology",
        "spatial sampling/aggregation adapter",
        "RAW_3D_OUTPUT_DIRECT_COMPATIBILITY = FALSE",
    ):
        assert finding in review


def test_plant_pathway_review_and_adr_agree() -> None:
    review = PLANT_REVIEW.read_text(encoding="utf-8")
    adr = PLANT_ADR.read_text(encoding="utf-8")
    for text in (review, adr):
        assert "PlantState" in text
        assert "leaf_exchange" in text
        assert "soil" in text
        assert "soil module owns plant = FORBIDDEN" in text
        assert "leaf module owns soil = FORBIDDEN" in text
    assert "Root uptake" in review
    assert "independent until the plant integration seam" in adr


def test_parameter_stress_review_is_fail_closed_without_schema_change() -> None:
    review = PARAMETER_REVIEW.read_text(encoding="utf-8")
    for capability in (
        "Scalar parameter",
        "Table parameter",
        "Crop-specific parameter",
        "Growth-stage parameter",
        "Unit conversion",
        "Uncertainty/provenance",
        "Temperature function",
        "Interpolation",
    ):
        assert capability in review
    assert "PARAMETER_DATABASE_FULL_UFOTRI_READY = FALSE" in review
    assert "ADR-011" in review
    assert "Do not modify the P5.1 schema" in PARAMETER_ADR.read_text(encoding="utf-8")

    database = ParameterDatabase.load(PLACEHOLDER_DB)
    assert database.list_parameters()
    assert all(
        database.get_entry(name).value is None for name in database.list_parameters()
    )


def test_physics_migration_boundary_review_preserves_nonimplementation() -> None:
    review = PHYSICS_REVIEW.read_text(encoding="utf-8")
    assert "LEAF_EXCHANGE_FLUX_SEAM = SUFFICIENT_FOR_P6_DESIGN" in review
    assert "LEAF_EXCHANGE_PHYSICS = NOT_IMPLEMENTED" in review
    assert "SOIL_THREE_LAYER_COMPATIBILITY = STRUCTURAL_ONLY" in review
    assert "PLANT_STATE_INTERFACE_BREAK_REQUIRED = FALSE" in review
    assert "class LeafExchangeFlux" not in LEAF_PHYSICS.read_text(encoding="utf-8")
    assert "PHYSICS_PENDING_UFOTRI_MIGRATION" in LEAF_PHYSICS.read_text(encoding="utf-8")
    assert "SEAM_ONLY_NO_ROOT_UPTAKE" in SOIL_MODEL.read_text(encoding="utf-8")
    assert "root_uptake_status" in SOIL_MODEL.read_text(encoding="utf-8")


def test_regression_readiness_contains_all_required_cases() -> None:
    contract = REGRESSION.read_text(encoding="utf-8")
    for marker in (
        "Benchmark A: constant HTO",
        "Benchmark B: step release / HTO pulse",
        "Benchmark C: diurnal cycle",
        "TFWT(t)",
        "OBT(t)",
        "TO_BE_FROZEN_IN_P6",
    ):
        assert marker in contract


def test_no_p54_production_schema_or_v2_change() -> None:
    protected = (
        "src",
        "configs",
        "schemas",
        "parameters",
        "validation/v3/policy/trusted_external_evidence_registry.yaml",
    )
    assert _git_names(*protected) == set()
    assert _untracked_names(*protected) == set()


def test_report_declares_independent_review_acceptance() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for marker in (
        "V3_P5_4_STATUS = PASS_INDEPENDENT_ARCHITECTURE_REVIEW",
        "UFOTRI_PHYSICS_IMPLEMENTED = FALSE",
        "UFOTRI_PARAMETER_IMPORTED = FALSE",
        "V3_FORMAL_PHYSICS = NOT_STARTED",
        "SRC_CHANGE = 0",
        "CONFIG_CHANGE = 0",
        "TRUSTED_REGISTRY_CHANGE = 0",
        "P5.1_SHA = 92772160a236ee7e0038107038c384c3e74580cb",
        "P5.2_SHA = c6a58b6c40ef05e2557b5201decfc40a38997045",
        "P5.3_SHA = 14e490759459b5beedff1c71591d1aa5f7d1776a",
    ):
        assert marker in report
