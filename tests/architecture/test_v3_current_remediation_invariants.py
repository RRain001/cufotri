from __future__ import annotations

from pathlib import Path
import re
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
SELECTION = ROOT / "docs/v3/physics/p7_8b2_physics_selection.yaml"
PHYSICAL_CONSTANTS = (
    ROOT / "docs/v3/parameter_evidence/physical_constant_validation_registry.yaml"
)
PIPELINE_RUNNER = ROOT / "src/cteas_ufotri/v3_pipeline/pipeline_runner.py"
ATMOS_FORCING = ROOT / "src/cteas_ufotri/coupling/atmos_v3/forcing.py"


def _yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_current_selection_remains_fail_closed_for_activation() -> None:
    payload = _yaml(SELECTION)
    scope = payload["selection_scope"]
    governance = payload["governance"]

    assert payload["status"] == "PASS_PHYSICS_SELECTION"
    assert scope["implementation_started"] is False
    assert scope["solver_changes"] is False
    assert scope["numerical_coupling_changes"] is False
    assert scope["active_parameters"] == 0
    assert scope["calibration_started"] is False
    assert scope["ufotri_active_database"] is False
    assert scope["v3_physics_ready"] is False
    assert governance["selected_equations_are_implemented"] is False
    assert governance["selected_parameters_have_values"] is False
    assert governance["selected_models_are_runtime_admissible"] is False
    assert governance["direct_activation_forbidden"] is True


def test_validated_physical_constant_provenance_resolves_to_real_git_objects() -> None:
    payload = _yaml(PHYSICAL_CONSTANTS)
    records = list(payload["parameters"]) + list(payload["evidence_records"])

    for record in records:
        provenance = record["provenance"]
        revision = provenance["revision"]
        path = provenance["file"]
        assert re.fullmatch(r"[0-9a-f]{40}", revision)
        _git("cat-file", "-e", f"{revision}:{path}")


def test_runtime_owners_do_not_import_parameter_or_adoption_control_plane() -> None:
    runtime_roots = (
        ROOT / "src/cteas_ufotri/plant",
        ROOT / "src/cteas_ufotri/exposure",
        ROOT / "src/cteas_ufotri/coupling",
        ROOT / "src/cteas_ufotri/v3_pipeline",
    )
    offenders: list[str] = []
    for runtime_root in runtime_roots:
        for path in runtime_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            # Preserve P7.6D's real runtime-import invariant without its
            # frozen historical Git-SHA stage checks.
            if (
                re.search(r"(?:from|import)\s+.*parameters_v3", text)
                or "physics_adoption" in text
                or "p7_6d_physics_adoption" in text
            ):
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_current_pipeline_capability_boundaries_are_explicit_in_source() -> None:
    pipeline = PIPELINE_RUNNER.read_text(encoding="utf-8")
    forcing = ATMOS_FORCING.read_text(encoding="utf-8")

    # Biological forcing is a runner-level parameter in the frozen baseline;
    # this is not a claim of timestep-varying day/night physiology.
    assert "biological_forcing: PlantBiologicalForcing" in pipeline
    assert "self.parameters.biological_forcing" in pipeline

    # The integrated Atmos -> Soil adapter supplies deposition only. The
    # standalone SoilStorageSolver still owns the signed-transport interface.
    adapter_match = re.search(
        r"def to_soil_forcing\(self\).*?return SoilForcing\((.*?)\)",
        forcing,
        re.DOTALL,
    )
    assert adapter_match is not None
    adapter_body = adapter_match.group(1)
    assert "deposition_flux_bq_m2_s=self.deposition_flux" in adapter_body
    assert "transport_flux" not in adapter_body


def test_current_parameter_control_plane_never_imports_physics_or_values() -> None:
    """Replace historical fixed-commit P7.6C stage-diff checks with live isolation."""
    package = ROOT / "src/cteas_ufotri/parameters_v3"
    sources = {file.name: file.read_text(encoding="utf-8")
               for file in package.glob("*.py")}
    combined = "\n".join(sources.values())
    for token in ("cteas_ufotri.plant", "cteas_ufotri.soil",
                  "cteas_ufotri.exposure", "cteas_ufotri.coupling",
                  "cteas_ufotri.v3_pipeline", "ParameterDatabase"):
        assert token not in combined, token

    # A candidate/evidence registry must not secretly contain production
    # values, regardless of the old P7.6C review's historical commit IDs.
    candidate = sources["candidate.py"] + sources["validation_gate.py"]
    for forbidden in ("reported_value", "normalized_value", "production=True"):
        assert forbidden not in candidate

    feasibility = sources["validation_feasibility.py"]
    for forbidden in ("ParameterDatabase", "selected_value",
                      "validated_parameter_values", "production=True"):
        assert forbidden not in feasibility

    registry = (
        ROOT / "docs/v3/parameter_evidence/parameter_candidate_registry.yaml"
    ).read_text(encoding="utf-8")
    assert "reported_value" not in registry
    assert "normalized_value" not in registry
    assert "active_parameters: 0" in registry
    assert "validated_parameters: 0" in registry


def test_fresh_control_plane_imports_do_not_activate_solving_packages() -> None:
    """A fresh Python interpreter catches transitive imports, not only strings."""
    import sys
    for module in ("registry", "validation_gate"):
        source = (
            "import sys, importlib; "
            f"importlib.import_module('cteas_ufotri.parameters_v3.{module}'); "
            "bad = [name for name in sys.modules "
            "if name.startswith('cteas_ufotri.') and "
            "any(key in name for key in "
            "('.plant', '.soil', '.foodchain', '.dose', '.v3_pipeline'))]; "
            "raise SystemExit(1 if bad else 0)"
        )
        subprocess.run(
            [sys.executable, "-c", source], cwd=ROOT,
            check=True, text=True, capture_output=True
        )


def test_frozen_mass_basis_annotation_is_not_imported_into_runtime() -> None:
    """Preserve the V3.1 runtime separation, not its old immutable Git blobs."""
    old_paths = (
        "src/cteas_ufotri/v3_pipeline/pipeline_runner.py",
        "src/cteas_ufotri/plant/leaf_exchange_resistance/resistance.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
        "src/cteas_ufotri/plant/obt_v3/obt_solver.py",
        "src/cteas_ufotri/plant/soil_v3/soil_solver.py",
        "src/cteas_ufotri/plant/root_v3/root_solver.py",
        "src/cteas_ufotri/plant/food_v3/food_transfer_solver.py",
        "src/cteas_ufotri/plant/food_v3/harvest_state.py",
    )
    for relative in old_paths:
        assert "mass_basis_v3_1" not in (ROOT / relative).read_text(encoding="utf-8")
