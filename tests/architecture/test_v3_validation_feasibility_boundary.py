"""P7.6C-3 source and runtime isolation tests."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "f0195c77d0521ec4ade9892e88318856934a3243"
STAGE_TIP_SHA = "e27badfe7aabb5a030607e8604c73e0598322a0f"
FEASIBILITY_SOURCE = ROOT / "src/cteas_ufotri/parameters_v3/validation_feasibility.py"


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def changed_paths() -> set[str]:
    return set(git("diff", "--name-only", BASE_SHA, STAGE_TIP_SHA).splitlines())


def test_p7_6c3_source_is_control_plane_only() -> None:
    changed_source = sorted(path for path in changed_paths() if path.startswith("src/"))
    assert changed_source
    assert all(path.startswith("src/cteas_ufotri/parameters_v3/") for path in changed_source)


def test_no_solver_physics_or_numerical_coupling_changes() -> None:
    forbidden_prefixes = (
        "configs/", "parameters/", "src/cteas_ufotri/plant/",
        "src/cteas_ufotri/exposure/", "src/cteas_ufotri/coupling/",
        "src/cteas_ufotri/v3_pipeline/",
    )
    assert not sorted(path for path in changed_paths() if path.startswith(forbidden_prefixes))


def test_runtime_owners_do_not_import_feasibility_control_plane() -> None:
    runtime_roots = (
        ROOT / "src/cteas_ufotri/plant",
        ROOT / "src/cteas_ufotri/exposure",
        ROOT / "src/cteas_ufotri/coupling",
        ROOT / "src/cteas_ufotri/v3_pipeline",
    )
    offenders = [
        str(path.relative_to(ROOT))
        for root in runtime_roots
        if root.exists()
        for path in root.rglob("*.py")
        if "parameters_v3" in path.read_text(encoding="utf-8")
        or "validation_feasibility" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_feasibility_source_has_no_runtime_value_resolution() -> None:
    source = FEASIBILITY_SOURCE.read_text(encoding="utf-8")
    assert "ParameterDatabase" not in source
    assert "production=True" not in source
    assert "selected_value" not in source
    assert "validated_parameter_values" not in source
