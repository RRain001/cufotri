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


def test_runtime_owners_do_not_import_parameter_validation_control_plane() -> None:
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
            if re.search(r"(?:from|import)\s+.*parameters_v3", text):
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
