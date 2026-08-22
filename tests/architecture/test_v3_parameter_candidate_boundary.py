from __future__ import annotations

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "838634f3af85e205fb15e10cbf15ee298ad4f017"
PACKAGE = ROOT / "src/cteas_ufotri/parameters_v3"
REGISTRY = ROOT / "docs/v3/parameter_evidence/parameter_candidate_registry.yaml"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def changed_paths() -> set[str]:
    return set(git("diff", "--name-only", BASE_SHA).splitlines()) | set(
        git("ls-files", "--others", "--exclude-standard").splitlines()
    )


def test_candidate_source_isolated_to_parameter_control_plane() -> None:
    changed_source = sorted(path for path in changed_paths() if path.startswith("src/"))
    assert changed_source
    assert all(path.startswith("src/cteas_ufotri/parameters_v3/") for path in changed_source)


def test_physics_pipeline_and_protected_paths_are_unchanged() -> None:
    changed = changed_paths()
    forbidden_prefixes = (
        "configs/",
        "parameters/",
        "src/cteas_ufotri/plant/",
        "src/cteas_ufotri/soil/",
        "src/cteas_ufotri/foodchain/",
        "src/cteas_ufotri/atmosphere/",
        "src/cteas_ufotri/dose/",
        "src/cteas_ufotri/coupling/",
        "src/cteas_ufotri/v3_pipeline/",
    )
    assert not sorted(path for path in changed if path.startswith(forbidden_prefixes))


def test_candidate_control_plane_has_no_solver_or_runtime_value_imports() -> None:
    source_text = "\n".join(
        (PACKAGE / filename).read_text(encoding="utf-8")
        for filename in ("candidate.py", "validation_gate.py")
    )
    assert not re.search(
        r"(?:from|import)\s+(?:\.\.|cteas_ufotri\.)?(?:plant|soil|foodchain|dose|coupling|v3_pipeline)",
        source_text,
    )
    assert "ParameterDatabase" not in source_text
    assert "reported_value" not in source_text
    assert "normalized_value" not in source_text


def test_candidate_registry_contains_no_parameter_values() -> None:
    text = REGISTRY.read_text(encoding="utf-8")
    assert "reported_value" not in text
    assert "normalized_value" not in text
    assert "active_parameters: 0" in text
    assert "validated_parameters: 0" in text


def test_model_modules_do_not_import_candidate_control_plane() -> None:
    protected_roots = (
        ROOT / "src/cteas_ufotri/plant",
        ROOT / "src/cteas_ufotri/soil",
        ROOT / "src/cteas_ufotri/foodchain",
        ROOT / "src/cteas_ufotri/dose",
        ROOT / "src/cteas_ufotri/v3_pipeline",
    )
    import_pattern = re.compile(r"(?:import|from)\s+.*parameters_v3")
    matches = [
        str(path)
        for root in protected_roots
        if root.exists()
        for path in root.rglob("*.py")
        if import_pattern.search(path.read_text(encoding="utf-8"))
    ]
    assert matches == []


def test_fresh_candidate_gate_import_does_not_load_solver_modules() -> None:
    code = (
        "import sys; "
        "import cteas_ufotri.parameters_v3.validation_gate; "
        "bad = [name for name in sys.modules if name.startswith('cteas_ufotri.') "
        "and any(token in name for token in ('.plant', '.soil', '.foodchain', '.dose', '.v3_pipeline'))]; "
        "print(bad); raise SystemExit(1 if bad else 0)"
    )
    subprocess.run(
        [".venv/bin/python", "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
