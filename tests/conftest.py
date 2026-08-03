"""Repository-wide pytest controls for declared external inputs."""

from __future__ import annotations

from pathlib import Path

import pytest

from validation.external_input_requirements import (
    InputCheck,
    InputStatus,
    check_dataset,
)


MARKER_DATASETS = {
    "external_sb1_data": "SB1",
    "external_sb4_data": "SB4",
    "external_era5_data": "ERA5_ACCEPTANCE",
    "private_reblinding_secret": "D3_PRIVATE_REBLIND_SECRET",
}
SKIP_REASONS = {
    "SB1": "SKIP_EXTERNAL_SB1_INPUT_NOT_AVAILABLE",
    "SB4": "SKIP_EXTERNAL_SB4_INPUT_NOT_AVAILABLE",
    "ERA5_ACCEPTANCE": "SKIP_EXTERNAL_ERA5_INPUT_NOT_AVAILABLE",
    "D3_PRIVATE_REBLIND_SECRET": "SKIP_PRIVATE_SECRET_NOT_AVAILABLE",
}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--require-external-inputs",
        action="store_true",
        default=False,
        help="Fail marked tests when declared external inputs are unavailable.",
    )


def pytest_configure(config: pytest.Config) -> None:
    for marker in MARKER_DATASETS:
        config.addinivalue_line(
            "markers", f"{marker}: requires the declared external input dataset"
        )


def _failure_message(check: InputCheck) -> str:
    # Keep this formatting stable for reports and machine-oriented tests.
    missing = list(check.missing_paths)
    invalid = list(check.invalid_paths)
    return (
        f"DATASET = {check.requirement.dataset_id}; "
        f"STATUS = {check.status}; "
        f"MISSING_FILES = {missing}; "
        f"INVALID_FILES = {invalid}; "
        f"ROOT = {check.root}"
    )


def pytest_runtest_setup(item: pytest.Item) -> None:
    repo_root = Path(str(item.config.rootpath))
    for marker_name, dataset_id in MARKER_DATASETS.items():
        if not item.get_closest_marker(marker_name):
            continue
        check = check_dataset(repo_root, dataset_id)
        if check.status is InputStatus.AVAILABLE:
            continue
        message = _failure_message(check)
        if (
            check.status is InputStatus.MISSING
            and not item.config.getoption("--require-external-inputs")
        ):
            pytest.skip(f"{SKIP_REASONS[dataset_id]}; {message}")
        pytest.fail(message)
