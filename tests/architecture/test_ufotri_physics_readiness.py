"""Independent architecture checks for the V3-P5.2 readiness boundary."""

from dataclasses import fields
import inspect
from pathlib import Path
import subprocess

import pytest

from cteas_ufotri.leaf_exchange.model import LeafExchangeModel
from cteas_ufotri.leaf_exchange.state import LeafExchangeForcing, LeafExchangeState
from cteas_ufotri.parameters import ParameterDatabase
from cteas_ufotri.parameters.exceptions import ParameterUnavailableError
from cteas_ufotri.soil.model import SoilModel
from cteas_ufotri.soil.state import SoilForcing


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/v3/reports/v3_p5_2_physics_readiness_report.md"
ATMOSPHERIC_CONTRACT = (
    ROOT / "docs/v3/interfaces/atmospheric_hto_forcing_contract.md"
)
PLACEHOLDER_DB = ROOT / "parameters/databases/ufotri_leaf_exchange.yaml"


def _git_names(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def test_v3_interfaces_are_unchanged() -> None:
    assert [field.name for field in fields(LeafExchangeForcing)] == [
        "hto_air_concentration",
        "air_temperature",
        "relative_humidity",
    ]
    assert [field.name for field in fields(LeafExchangeState)] == [
        "hto_air_concentration",
        "air_temperature",
        "relative_humidity",
        "tfwt_activity",
        "obt_activity",
        "leaf_water_mass",
        "dry_matter_mass",
        "current_time",
        "delta_t",
    ]
    assert [field.name for field in fields(SoilForcing)] == [
        "hto_air_concentration",
        "deposition_flux",
    ]
    assert list(inspect.signature(LeafExchangeModel.advance).parameters) == [
        "self",
        "state",
        "forcing",
        "dt",
    ]
    assert list(inspect.signature(SoilModel.advance).parameters) == [
        "self",
        "soil_state",
        "forcing",
        "dt",
    ]


def test_placeholder_parameters_are_rejected() -> None:
    database = ParameterDatabase.load(PLACEHOLDER_DB)
    entries = [database.get_entry(name) for name in database.list_parameters()]
    assert entries
    assert all(entry.value is None for entry in entries)
    with pytest.raises(ParameterUnavailableError):
        database.get(entries[0].name)


def test_atmospheric_contract_declares_required_boundary() -> None:
    contract = ATMOSPHERIC_CONTRACT.read_text(encoding="utf-8")
    for field in (
        "`time`",
        "`air_concentration_bq_m3`",
        "`temperature_k`",
        "`relative_humidity`",
        "`precipitation_m_s`",
        "`radiation_w_m2`",
        "`boundary_layer_height_m`",
        "`deposition_flux_bq_m2_s`",
    ):
        assert field in contract
    assert "`AtmosphericHTOForcing`" in contract
    assert "Gaussian model" not in contract.split("## Proposed record", 1)[1].split(
        "## Current implementation comparison", 1
    )[0]
    assert "CALPUFF" not in contract.split("## Proposed record", 1)[1].split(
        "## Current implementation comparison", 1
    )[0]


def test_p52_does_not_change_source_config_or_trusted_registry() -> None:
    protected_paths = (
        "src",
        "configs",
        "validation/v3/policy/trusted_external_evidence_registry.yaml",
    )
    assert _git_names("--", *protected_paths) == set()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", *protected_paths],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert untracked.stdout.strip() == ""


def test_report_declares_readiness_boundary() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for marker in (
        "P5.2_STATUS = PASS_ARCHITECTURE_READY",
        "UFOTRI_PARAMETERS_IMPORTED = FALSE",
        "UFOTRI_PHYSICS_IMPLEMENTED = FALSE",
        "V3_FORMAL_PHYSICS = NOT_STARTED",
        "MAIN_BEHAVIOR_CHANGED = FALSE",
        "SRC_DIFF = 0",
        "CONFIG_DIFF = 0",
        "TRUSTED_REGISTRY_DIFF = 0",
        "V2 legacy path",
        "TO_BE_FROZEN_IN_P6",
    ):
        assert marker in report
