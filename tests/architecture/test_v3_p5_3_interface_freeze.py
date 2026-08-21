"""Independent architecture review for V3-P5.3."""

from pathlib import Path
import subprocess

from cteas_ufotri.parameters import ParameterDatabase


ROOT = Path(__file__).resolve().parents[2]
P52_SHA = "c6a58b6c40ef05e2557b5201decfc40a38997045"
ATMOSPHERIC = ROOT / "docs/v3/interfaces/atmospheric_hto_forcing_contract.md"
PLANT = ROOT / "docs/v3/architecture/plant_pathway_architecture.md"
PLANT_ADR = ROOT / "docs/v3/architecture/ADR-010-plant-dual-pathway-model.md"
FLUX = ROOT / "docs/v3/architecture/leaf_exchange_flux_contract.md"
PARAMETERS = ROOT / "docs/v3/architecture/parameter_database_ufotri_capability_audit.md"
REGRESSION = ROOT / "docs/v3/validation/ufotri_physics_regression_contract.md"
REPORT = ROOT / "docs/v3/reports/v3_p5_3_interface_freeze_report.md"
PLACEHOLDER_DB = ROOT / "parameters/databases/ufotri_leaf_exchange.yaml"


def _git_names(*paths: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", P52_SHA, "--", *paths],
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


def test_atmospheric_contract_exists_and_forbids_provider_coupling() -> None:
    contract = ATMOSPHERIC.read_text(encoding="utf-8")
    for field in (
        "`time`",
        "`air_hto_concentration`",
        "`air_temperature`",
        "`relative_humidity`",
        "`precipitation`",
        "`shortwave_radiation`",
        "`longwave_radiation`",
        "`wind_speed`",
        "`boundary_layer_height`",
        "`surface_deposition_flux`",
    ):
        assert field in contract
    assert "Gaussian" in contract and "CALPUFF" in contract
    assert "must not know" in contract
    assert "FAIL_CLOSED" in contract


def test_plant_pathways_are_independent_until_plant_state() -> None:
    plant = PLANT.read_text(encoding="utf-8")
    adr = PLANT_ADR.read_text(encoding="utf-8")
    for text in (plant, adr):
        assert "PlantState" in text
        assert "Leaf pathway" in text or "leaf_exchange" in text
        assert "Root pathway" in text or "root uptake" in text
        assert "soil module owns plant" in text
        assert "leaf module owns soil" in text
    assert "FORBIDDEN" in plant
    assert "independent until the plant integration seam" in adr


def test_leaf_exchange_flux_is_design_only_and_physics_protocol_is_unchanged() -> None:
    flux = FLUX.read_text(encoding="utf-8")
    for field in (
        "air_to_leaf_flux",
        "stomatal_flux",
        "cuticular_flux",
        "tfwt_to_obt_flux",
        "decay_flux",
    ):
        assert f"`{field}`" in flux
    assert "DESIGN_ONLY_NOT_IMPLEMENTED" in flux
    assert _git_names("src/cteas_ufotri/leaf_exchange/physics.py") == set()


def test_parameter_capability_is_audited_without_activating_values() -> None:
    audit = PARAMETERS.read_text(encoding="utf-8")
    for capability in (
        "Scalar",
        "Unit",
        "Source provenance",
        "Hash",
        "Uncertainty",
        "Table",
        "Crop dependent",
        "Growth stage dependent",
        "Temperature function",
        "Interpolation",
    ):
        assert capability in audit
    database = ParameterDatabase.load(PLACEHOLDER_DB)
    assert database.list_parameters()
    assert all(
        database.get_entry(name).value is None for name in database.list_parameters()
    )
    assert _git_names(
        "src/cteas_ufotri/parameters",
        "schemas",
        "parameters",
    ) == set()


def test_no_production_config_trusted_registry_or_v2_source_change() -> None:
    protected = (
        "src",
        "configs",
        "validation/v3/policy/trusted_external_evidence_registry.yaml",
    )
    assert _git_names(*protected) == set()
    assert _untracked_names(*protected) == set()


def test_regression_contract_freezes_three_benchmarks_without_tolerance() -> None:
    contract = REGRESSION.read_text(encoding="utf-8")
    for marker in (
        "Benchmark A: constant HTO",
        "Benchmark B: step release / HTO pulse",
        "Benchmark C: diurnal cycle",
        "TFWT(t)",
        "OBT(t)",
        "uptake",
        "release",
        "decay",
        "day/night response",
        "TO_BE_FROZEN_IN_P6",
    ):
        assert marker in contract
    assert "tolerance =" not in contract


def test_report_freezes_p5_3_scope() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for marker in (
        "P5.3_STATUS = PASS_INTERFACE_FREEZE",
        "ATMOSPHERIC_HTO_FORCING = FROZEN",
        "PLANT_DUAL_PATHWAY = FROZEN",
        "LEAF_EXCHANGE_FLUX = DESIGN_ONLY_NOT_IMPLEMENTED",
        "PARAMETER_SCHEMA_CHANGED = FALSE",
        "UFOTRI_PARAMETERS_IMPORTED = FALSE",
        "UFOTRI_PHYSICS_IMPLEMENTED = FALSE",
        "V3_FORMAL_PHYSICS = NOT_STARTED",
        "MAIN_BEHAVIOR_CHANGED = FALSE",
        "SRC_DIFF = 0",
        "CONFIG_DIFF = 0",
        "TRUSTED_REGISTRY_DIFF = 0",
        "TO_BE_FROZEN_IN_P6",
    ):
        assert marker in report
