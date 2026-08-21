"""P6.2A architecture tests: specification only, no V3 implementation."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "6671f5793d04842bf2ceae4904f3c0cf30a0d7e0"
PARAMETER_REQUIREMENTS = (
    REPO / "validation/external_evidence_acquisition/leaf_exchange_parameter_requirements.yaml"
)
MODEL_SPEC = REPO / "docs/v3/physics/leaf_exchange_model.md"
EQUATION_SPEC = REPO / "docs/v3/physics/leaf_exchange_equations.md"
SOURCE_AUDIT = REPO / "docs/v3/ufotri_database/leaf_exchange_physics_source_audit.md"
REGRESSION_CONTRACT = REPO / "docs/v3/regression/leaf_exchange_regression_contract.md"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _all_changed_paths() -> set[str]:
    tracked = set(_git("diff", "--name-only", BASE_SHA).splitlines())
    untracked = set(
        _git("ls-files", "--others", "--exclude-standard").splitlines()
    )
    return tracked | untracked


def test_no_v3_leaf_exchange_implementation_or_protected_changes() -> None:
    changed = _all_changed_paths()
    protected_prefixes = ("src/", "configs/", "parameters/", "schemas/")
    protected = sorted(
        path
        for path in changed
        if path.startswith(protected_prefixes)
        or path.endswith("trusted_external_evidence_registry.yaml")
    )
    assert protected == []
    assert not (REPO / "src/leaf_exchange").exists()
    assert _git("diff", "--name-only", BASE_SHA, "--", "src/cteas_ufotri/plant/leaf_exchange.py") == ""


def test_required_specification_artifacts_exist() -> None:
    for path in (
        SOURCE_AUDIT,
        MODEL_SPEC,
        EQUATION_SPEC,
        PARAMETER_REQUIREMENTS,
        REGRESSION_CONTRACT,
    ):
        assert path.is_file(), path


def test_no_active_ufotri_parameter_or_import() -> None:
    text = PARAMETER_REQUIREMENTS.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    assert data["database"]["imported"] is False
    assert data["database"]["active"] is False
    assert data["database"]["validated"] is False
    assert data["parameter_contract"]["active_transition_allowed"] is False
    assert data["validation_gate"]["imported_parameters_present"] is False
    assert data["validation_gate"]["active_parameters_present"] is False
    assert not re.search(r"(?im)^\s*status:\s*ACTIVE\s*$", text)
    assert not re.search(r"(?im)^\s*validated:\s*true\s*$", text)

    required_names = {
        "leaf_exchange_resistance",
        "stomatal_resistance",
        "boundary_layer_resistance",
        "exchange_coefficient",
        "obt_formation_rate",
        "obt_loss_rate",
    }
    assert required_names <= set(data["parameters"])
    required_dimensions = {"crop", "growth_stage", "temperature", "humidity"}
    for parameter in data["parameters"].values():
        assert parameter["type"] == "table"
        assert required_dimensions <= set(parameter["dimensions"])
        assert parameter["value"] is None
        assert parameter["status"] == "REQUIRED"
        assert parameter["imported"] is False
        assert parameter["validated"] is False
        assert parameter["source"]["status"] == "NOT_VALIDATED"


def test_default_model_behavior_and_default_configuration_are_unchanged() -> None:
    config_path = REPO / "configs/default_parameters.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False
    assert _git("diff", "--name-only", BASE_SHA, "--", "configs/default_parameters.yaml") == ""


def test_plant_state_and_atmospheric_forcing_contract_are_specified() -> None:
    model = MODEL_SPEC.read_text(encoding="utf-8")
    required_model_terms = (
        "PlantState",
        "tfwt_inventory_bq_m2",
        "obt_inventory_bq_m2",
        "biomass_dry_kg_m2",
        "water_content_kg_m2",
        "AtmosphericHTOForcing",
        "air_hto_concentration",
        "relative_humidity",
        "shortwave_radiation",
        "wind_speed",
        "boundary_layer_height",
        "LeafExchangeModule",
        "leaf_TFWT_change",
        "leaf_OBT_change",
        "leaf_reemission",
        "DESIGN_ONLY_NOT_IMPLEMENTED",
        "LEAF_EXCHANGE_IMPLEMENTATION = FALSE",
    )
    for term in required_model_terms:
        assert term in model, term


def test_equation_contract_covers_resistance_dynamics_obt_and_conservation() -> None:
    equations = EQUATION_SPEC.read_text(encoding="utf-8")
    for term in (
        "r_tot = r_a + r_b + r_c",
        "g_ex  = 1 / r_tot",
        "F_air_to_leaf",
        "F_stomatal",
        "F_cuticular",
        "dI_TFWT/dt",
        "F_TFWT_to_OBT",
        "k_OBT",
        "k_loss,OBT",
        "F_reemission",
        "d(I_TFWT + I_OBT)/dt",
        "SPECIFICATION_ONLY_NO_RUNNABLE_CODE",
    ):
        assert term in equations, term
    assert "0.06% h^-1" in equations
    assert "0.3% h^-1" in equations


def test_source_audit_keeps_manual_evidence_separate_from_validation() -> None:
    audit = SOURCE_AUDIT.read_text(encoding="utf-8")
    for classification in (
        "EXPLICIT_FROM_UFOTRI",
        "DERIVED_FROM_UFOTRI",
        "ASSUMPTION",
        "MISSING",
    ):
        assert classification in audit
    for source_marker in (
        "§2.2.2",
        "Eq. 27",
        "Eq. 28",
        "Eq. 29",
        "Eq. 30",
        "Eq. 31",
        "Eq. 32",
        "§2.2.6",
        "0.06% h^-1",
        "0.3% h^-1",
        "crop × growth_stage × temperature × humidity",
    ):
        assert source_marker in audit, source_marker
    assert "not a validated parameter" in audit
    assert "UFOTRI_PARAMETER_IMPORTED = FALSE" in audit


def test_existing_v1_v2_plant_paths_are_not_modified() -> None:
    paths = (
        "src/cteas_ufotri/plant/leaf_exchange.py",
        "src/cteas_ufotri/plant/tfwt.py",
        "src/cteas_ufotri/plant/obt.py",
        "src/cteas_ufotri/coupling/state.py",
    )
    assert _git("diff", "--name-only", BASE_SHA, "--", *paths) == ""


def test_regression_contract_is_future_specification_only() -> None:
    contract = REGRESSION_CONTRACT.read_text(encoding="utf-8")
    for case in ("Case A", "Case B", "Case C"):
        assert case in contract
    assert "P6_2B_BENCHMARK_SPECIFICATION_ONLY" in contract
    assert "LEAF_EXCHANGE_REGRESSION_RESULTS = NOT_EXECUTED" in contract
    assert "LEAF_EXCHANGE_NUMERICAL_IMPLEMENTATION = FALSE" in contract
    assert "No numerical trajectory" in contract
