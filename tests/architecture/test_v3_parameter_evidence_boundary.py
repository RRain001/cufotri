from __future__ import annotations

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "61effab2958eb38c985fd6df6829cc4e13427dc2"
PACKAGE = ROOT / "src/cteas_ufotri/parameters_v3"


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


def test_new_production_source_isolated_to_parameter_control_plane() -> None:
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


def test_registry_source_has_no_solver_imports() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in PACKAGE.glob("*.py")
    )
    assert not re.search(
        r"(?:from|import)\s+(?:\.\.|cteas_ufotri\.)?(?:plant|soil|exposure|coupling)",
        source_text,
    )
    assert "ParameterDatabase" not in source_text
    assert "ACTIVE" in source_text


def test_importing_registry_does_not_import_v3_solver_modules() -> None:
    code = (
        "import sys; "
        "import cteas_ufotri.parameters_v3.registry; "
        "bad = [name for name in sys.modules if name.startswith('cteas_ufotri.') "
        "and any(token in name for token in ('.plant', '.exposure', '.coupling'))]; "
        "print(bad); raise SystemExit(1 if bad else 0)"
    )
    subprocess.run(
        [".venv/bin/python", "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
