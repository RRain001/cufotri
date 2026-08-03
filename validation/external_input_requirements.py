"""Fail-closed discovery of inputs that are intentionally outside Git.

The resolver has two deliberately small search scopes: an explicitly supplied
environment path, or the current worktree's documented ignored path.  It never
walks other worktrees, the user's home directory, or the network.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import os
from pathlib import Path


class InputStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    INCOMPLETE = "INCOMPLETE"
    INVALID = "INVALID"


@dataclass(frozen=True)
class DatasetRequirement:
    dataset_id: str
    environment_variable: str
    canonical_root: str
    required_paths: tuple[str, ...]


@dataclass(frozen=True)
class InputCheck:
    requirement: DatasetRequirement
    root: Path
    status: InputStatus
    missing_paths: tuple[str, ...]
    invalid_paths: tuple[str, ...]

    @property
    def available(self) -> bool:
        return self.status is InputStatus.AVAILABLE

    def machine_readable_missing(self) -> str:
        return "[" + ", ".join(repr(path) for path in self.missing_paths) + "]"

    @property
    def missing_files(self) -> tuple[str, ...]:
        return tuple(
            str(_input_path_from_dataset_root(self.root, self.requirement.dataset_id, path))
            for path in self.missing_paths
        )


_POINTS = ("CENTRE", "NORTH_0P25", "SOUTH_0P25", "EAST_0P25", "WEST_0P25")
_RAW_NAME = "era5_surface_2001-05-20_2001-10-06.nc"
_SB1_REQUIRED = (
    "emras_soybean_sb1/references/IAEA-emras-tritium-wg.pdf",
    "emras_soybean_sb1/generated_forcing/sb1_chamber_profiles.csv",
    "emras_soybean_sb1/generated_forcing/sb1_chamber_profile_summary.json",
    "emras_soybean_sb1/generated_forcing/sb1_forcing_primary.csv",
    "emras_soybean_sb1/outputs/calibration_grid.csv",
    *tuple(
        f"emras_soybean_sb1/era5_raw/{point}/{_RAW_NAME}"
        for point in _POINTS
    ),
    *tuple(
        f"emras_soybean_sb1/era5_processed/{point}/{_RAW_NAME}"
        for point in _POINTS
    ),
    *tuple(
        f"emras_soybean_sb1/era5_processed/{point}/era5_hourly_processed.csv"
        for point in _POINTS
    ),
)
_SB4_SCENARIOS = tuple(
    f"{profile}_run_{run:02d}.csv"
    for profile in ("constant_reported_mean", "scaled_sb1_observed_shape")
    for run in range(1, 8)
)
_SB4_REQUIRED = (
    "emras_soybean_sb1/references/IAEA-emras-tritium-wg.pdf",
    *tuple(
        f"emras_soybean_sb1/era5_raw/{point}/{_RAW_NAME}"
        for point in _POINTS
    ),
    *tuple(
        f"emras_soybean_sb1/era5_processed/{point}/{_RAW_NAME}"
        for point in _POINTS
    ),
    *tuple(
        f"emras_soybean_sb1/era5_processed/{point}/era5_hourly_processed.csv"
        for point in _POINTS
    ),
    *tuple(
        f"emras_soybean_sb4/generated_forcing/{name}"
        for name in ("sb4_chamber_profiles.csv", "sb4_forcing_manifest.json")
    ),
    *tuple(
        f"emras_soybean_sb4/generated_forcing/sb4_{name}"
        for name in _SB4_SCENARIOS
    ),
)


DATASET_REQUIREMENTS: dict[str, DatasetRequirement] = {
    "SB1": DatasetRequirement(
        dataset_id="SB1",
        environment_variable="CTEAS_EXTERNAL_EVIDENCE_ROOT",
        canonical_root="validation/external_local",
        required_paths=_SB1_REQUIRED,
    ),
    "SB4": DatasetRequirement(
        dataset_id="SB4",
        environment_variable="CTEAS_EXTERNAL_EVIDENCE_ROOT",
        canonical_root="validation/external_local",
        required_paths=_SB4_REQUIRED,
    ),
    "D3_PRIVATE_REBLIND_SECRET": DatasetRequirement(
        dataset_id="D3_PRIVATE_REBLIND_SECRET",
        environment_variable="CTEAS_EXTERNAL_EVIDENCE_ROOT",
        canonical_root="validation/external_local",
        required_paths=(
            "d3_prospective_reblind_v3/sealed_generation_secret.json",
            "d3_prospective_reblind_v3/truth_key_v3.json",
        ),
    ),
    "ERA5_ACCEPTANCE": DatasetRequirement(
        dataset_id="ERA5_ACCEPTANCE",
        environment_variable="CTEAS_ERA5_INPUT_ROOT",
        canonical_root="data/era5",
        required_paths=("era5_surface_2025-06-01_2025-06-02.csv",),
    ),
}


def _base_root(repo_root: Path, requirement: DatasetRequirement) -> Path:
    configured = os.environ.get(requirement.environment_variable)
    if configured:
        candidate = Path(configured)
        return candidate if candidate.is_absolute() else repo_root / candidate
    return repo_root / requirement.canonical_root


def dataset_root(repo_root: Path, dataset_id: str) -> Path:
    """Return the current-worktree or explicitly configured dataset root."""

    requirement = DATASET_REQUIREMENTS[dataset_id]
    base = _base_root(repo_root, requirement)
    dataset_directory = {
        "SB1": "emras_soybean_sb1",
        "SB4": "emras_soybean_sb4",
        "D3_PRIVATE_REBLIND_SECRET": "d3_prospective_reblind_v3",
    }.get(dataset_id)
    if dataset_directory is not None:
        return base / dataset_directory
    return base


def _relative_required_path(dataset_id: str, path: str) -> str:
    if dataset_id == "SB1":
        return path.removeprefix("emras_soybean_sb1/")
    if dataset_id == "SB4":
        return path.removeprefix("emras_soybean_sb4/")
    if dataset_id == "D3_PRIVATE_REBLIND_SECRET":
        return path.removeprefix("d3_prospective_reblind_v3/")
    return path


def _input_path_from_dataset_root(
    root: Path, dataset_id: str, declared: str
) -> Path:
    if dataset_id == "SB4" and declared.startswith("emras_soybean_sb1/"):
        return root.parent / "emras_soybean_sb1" / declared.removeprefix(
            "emras_soybean_sb1/"
        )
    return root / _relative_required_path(dataset_id, declared)


def check_dataset(repo_root: Path, dataset_id: str) -> InputCheck:
    """Check only the declared files for one external dataset."""

    requirement = DATASET_REQUIREMENTS[dataset_id]
    base = _base_root(repo_root, requirement)
    root = dataset_root(repo_root, dataset_id)
    if not base.exists():
        return InputCheck(
            requirement, root, InputStatus.MISSING, requirement.required_paths, ()
        )
    if not base.is_dir():
        return InputCheck(
            requirement, root, InputStatus.INVALID, requirement.required_paths, (str(base),)
        )
    if not root.exists():
        return InputCheck(
            requirement, root, InputStatus.MISSING, requirement.required_paths, ()
        )
    if not root.is_dir():
        return InputCheck(
            requirement, root, InputStatus.INVALID, requirement.required_paths, (str(root),)
        )

    missing: list[str] = []
    invalid: list[str] = []
    for declared in requirement.required_paths:
        path = _input_path_from_dataset_root(root, dataset_id, declared)
        if not path.exists():
            missing.append(declared)
        elif not path.is_file():
            invalid.append(declared)
    if invalid:
        status = InputStatus.INVALID
    elif missing:
        status = InputStatus.INCOMPLETE
    else:
        status = InputStatus.AVAILABLE
    return InputCheck(requirement, root, status, tuple(missing), tuple(invalid))


def resolve_dataset_file(repo_root: Path, dataset_id: str) -> Path:
    """Resolve the sole declared file for a dataset used by a verifier."""

    requirement = DATASET_REQUIREMENTS[dataset_id]
    if len(requirement.required_paths) != 1:
        raise ValueError(f"{dataset_id} does not define exactly one file")
    return _base_root(repo_root, requirement) / requirement.required_paths[0]
