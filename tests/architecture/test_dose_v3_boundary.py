from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
BASE_SHA = "a6200569154b90ab90c8dc9c5332b70401da8ec1"
PACKAGE = REPO / "src/cteas_ufotri/exposure/dose_v3"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def changed_paths() -> set[str]:
    return set(git("diff", "--name-only", BASE_SHA).splitlines()) | set(
        git("ls-files", "--others", "--exclude-standard").splitlines()
    )


def test_source_scope_is_intake_and_new_dose_v3_only() -> None:
    changed_source = sorted(
        path
        for path in changed_paths()
        if path.startswith("src/")
        and not path.startswith("src/cteas_ufotri/parameters_v3/")
    )
    assert changed_source
    allowed = (
        "src/cteas_ufotri/exposure/intake_v3/",
        "src/cteas_ufotri/exposure/dose_v3/",
        "src/cteas_ufotri/coupling/atmos_v3/",
        "src/cteas_ufotri/v3_pipeline/",
    )
    assert all(path.startswith(allowed) for path in changed_source)


def test_protected_paths_and_assessment_boundary_are_clean() -> None:
    changed = changed_paths()
    forbidden = sorted(
        path
        for path in changed
        if path.startswith(("configs/", "parameters/"))
        or path.endswith("trusted_external_evidence_registry.yaml")
    )
    assert forbidden == []
    for path in (
        "src/cteas_ufotri/plant",
        "src/cteas_ufotri/soil",
        "src/cteas_ufotri/foodchain",
        "src/cteas_ufotri/atmosphere",
        "src/cteas_ufotri/coupling/integrator.py",
        "src/cteas_ufotri/coupling/mass_balance.py",
        "src/cteas_ufotri/coupling/reference_solver.py",
        "src/cteas_ufotri/coupling/state.py",
        "src/cteas_ufotri/dose",
        "src/cteas_ufotri/case.py",
        "src/cteas_ufotri/config.py",
    ):
        assert git("diff", "--name-only", BASE_SHA, "--", path) == ""
    config = yaml.safe_load(
        (REPO / "configs/default_parameters.yaml").read_text(encoding="utf-8")
    )
    assert config["plant"]["leaf_exchange_mode"] == "off"
    assert config["plant"]["direct_leaf_uptake_enabled"] is False


def test_solver_consumes_intake_public_api_only() -> None:
    solver_text = (PACKAGE / "dose_solver.py").read_text(encoding="utf-8")
    assert "intake_state.inventory()" in solver_text
    assert "intake_state.consumer()" in solver_text
    assert "intake_state.age_group()" in solver_text
    assert "intake_state.period()" in solver_text
    assert "intake_state.time()" in solver_text
    assert "intake_state.intake_inventory_bq" not in solver_text
    assert "intake_state.age_group_identifier" not in solver_text
    assert "intake_state.timestamp" not in solver_text
    assert "ParameterDatabase" not in solver_text
    imports = [
        line
        for line in solver_text.splitlines()
        if re.match(r"^\s*(from|import)\s+", line)
    ]
    assert not any(
        re.search(
            r"tfwt|obt|soil|plant|food|atmosphere|cteas[-_]atmos|config|parameter|regulatory|risk|emergency",
            line,
            re.IGNORECASE,
        )
        for line in imports
    )


def test_dose_state_and_parameter_contracts_are_explicit() -> None:
    state_text = (PACKAGE / "dose_state.py").read_text(encoding="utf-8")
    solver_text = (PACKAGE / "dose_solver.py").read_text(encoding="utf-8")
    for marker in (
        "consumer_identifier",
        "age_group_identifier",
        "pathway_identifier",
        "intake_inventory_bq",
        "dose_coefficient",
        "dose_coefficient_unit",
        "committed_dose_sv",
        "time_period",
        "timestamp",
        "provenance",
        "def inventory(",
        "def dose(",
        "def consumer(",
    ):
        assert marker in state_text
    for marker in (
        "radionuclide_identifier",
        "pathway_identifier",
        "dose_coefficient_unit",
        'parameter_status: str = "provisional"',
        "D [Sv] = I [Bq] * e [Sv/Bq]",
    ):
        assert marker in solver_text
    for forbidden in (
        "soil",
        "plant",
        "food",
        "regulatory",
        "risk",
        "emergency",
        "effective_dose",
    ):
        assert forbidden not in state_text.lower()
