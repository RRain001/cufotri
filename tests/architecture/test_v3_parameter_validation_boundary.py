from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTROL_PLANE = ROOT / "src/cteas_ufotri/parameters_v3"


def test_p7_6c1_control_plane_does_not_import_runtime_or_physics_modules() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in CONTROL_PLANE.glob("*.py")
    )
    assert "ParameterValidationRegistry" in source
    assert "cteas_ufotri.plant" not in source
    assert "cteas_ufotri.coupling" not in source
    assert "cteas_ufotri.v3_pipeline" not in source
    assert "ParameterDatabase" not in source


def test_runtime_owners_do_not_import_or_resolve_validation_registry() -> None:
    protected = (
        ROOT / "src/cteas_ufotri/plant/soil_v3",
        ROOT / "src/cteas_ufotri/v3_pipeline",
    )
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for directory in protected
        for path in directory.glob("*.py")
    )
    assert "ParameterValidationRegistry" not in source
    assert "parameters_v3.validation" not in source
