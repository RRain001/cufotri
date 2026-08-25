"""P7.6D control-plane source and runtime-isolation tests."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "e27badfe7aabb5a030607e8604c73e0598322a0f"
STAGE_TIP_SHA = "1f26819cb641fb908f04b8e776f788f8e311770e"


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def changed_paths() -> set[str]:
    return set(git("diff", "--name-only", BASE_SHA, STAGE_TIP_SHA).splitlines())


def test_p7_6d_source_is_control_plane_only() -> None:
    changed_source = sorted(path for path in changed_paths() if path.startswith("src/"))
    assert changed_source == ["src/cteas_ufotri/parameters_v3/physics_adoption.py"]


def test_no_solver_or_numerical_coupling_files_changed() -> None:
    forbidden_prefixes = (
        "configs/", "parameters/", "src/cteas_ufotri/plant/",
        "src/cteas_ufotri/exposure/", "src/cteas_ufotri/coupling/",
        "src/cteas_ufotri/v3_pipeline/",
    )
    assert not sorted(path for path in changed_paths() if path.startswith(forbidden_prefixes))


def test_runtime_owners_do_not_import_p7_6d_control_plane() -> None:
    runtime_roots = (
        ROOT / "src/cteas_ufotri/plant",
        ROOT / "src/cteas_ufotri/exposure",
        ROOT / "src/cteas_ufotri/coupling",
        ROOT / "src/cteas_ufotri/v3_pipeline",
    )
    needles = ("physics_adoption", "p7_6d_physics_adoption")
    offenders = [
        str(path.relative_to(ROOT))
        for root in runtime_roots
        if root.exists()
        for path in root.rglob("*.py")
        if any(needle in path.read_text(encoding="utf-8") for needle in needles)
    ]
    assert offenders == []


def test_changed_docs_are_decision_artifacts_only() -> None:
    changed = changed_paths()
    forbidden = {"docs/equations/plant.md", "docs/equations/soil.md", "docs/equations/coupling.md"}
    assert not changed & forbidden
    assert "docs/v3/physics/p7_6d_physics_adoption_decision.yaml" in changed
    assert "docs/v3/physics/p7_6d_redesign_priority_matrix.yaml" in changed
