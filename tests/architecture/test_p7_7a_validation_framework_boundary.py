"""P7.7A source, solver, and runtime-isolation tests."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "1f26819cb641fb908f04b8e776f788f8e311770e"
VALIDATION_SOURCE = ROOT / "src/cteas_ufotri/validation_v3"


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


def test_p7_7a_source_is_an_additive_validation_control_plane() -> None:
    changed_source = sorted(path for path in changed_paths() if path.startswith("src/"))

    assert changed_source
    assert all(path.startswith("src/cteas_ufotri/validation_v3/") for path in changed_source)


def test_no_solver_parameter_or_numerical_coupling_files_changed() -> None:
    forbidden_prefixes = (
        "configs/v2/",
        "parameters/",
        "src/cteas_ufotri/atmosphere/",
        "src/cteas_ufotri/plant/",
        "src/cteas_ufotri/soil/",
        "src/cteas_ufotri/exposure/",
        "src/cteas_ufotri/coupling/",
        "src/cteas_ufotri/v3_pipeline/",
        "src/cteas_ufotri/parameters_v3/",
    )

    assert not sorted(
        path for path in changed_paths() if path.startswith(forbidden_prefixes)
    )


def test_validation_package_does_not_import_runtime_owners() -> None:
    forbidden_tokens = (
        "cteas_ufotri.plant",
        "cteas_ufotri.soil",
        "cteas_ufotri.exposure",
        "cteas_ufotri.coupling",
        "cteas_ufotri.v3_pipeline",
        "ParameterDatabase",
        "UFOTRI_ACTIVE_DATABASE",
    )
    offenders = []
    for path in VALIDATION_SOURCE.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}:{token}")
    assert offenders == []


def test_p7_7b_runner_is_the_only_explicit_runtime_caller() -> None:
    """Execution is isolated to the additive benchmark adapter, not owners."""

    runner = (VALIDATION_SOURCE / "benchmark_runner.py").read_text(encoding="utf-8")
    registry = (VALIDATION_SOURCE / "benchmark_registry.py").read_text(encoding="utf-8")
    writer = (VALIDATION_SOURCE / "benchmark_result_writer.py").read_text(encoding="utf-8")

    assert "V3PipelineRunner" in runner
    assert "SoilStorageSolver" in runner
    assert "TFWTStorageSolver" in runner
    assert "OBTSolver" in runner
    assert "RootUptakeSolver" in runner
    assert "ParameterDatabase" not in runner
    assert "UFOTRI_ACTIVE_DATABASE" not in runner
    assert "ParameterDatabase" not in registry
    assert "ParameterDatabase" not in writer


def test_case_values_are_declared_in_yaml_not_benchmark_loader() -> None:
    loader = (VALIDATION_SOURCE / "benchmarks.py").read_text(encoding="utf-8")
    manifest = ROOT / "configs/v3/validation/p7_7a_baseline_benchmarks.yaml"

    assert manifest.is_file()
    assert "100.0" not in loader
    assert "0.001" not in loader
