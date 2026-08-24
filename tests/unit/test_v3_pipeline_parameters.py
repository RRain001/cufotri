from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from cteas_ufotri.v3_pipeline import (
    PipelineInputError,
    V3PipelineParameters,
)
from tests.integration.test_v3_pipeline import make_parameters


def test_pipeline_parameters_are_explicit_and_immutable() -> None:
    parameters = make_parameters()

    assert parameters.interval_seconds == pytest.approx(10.0)
    assert parameters.root_parameters.parameter_status == "provisional"
    assert parameters.dose_parameters.parameter_status == "provisional"
    with pytest.raises(FrozenInstanceError):
        parameters.interval_seconds = 20.0  # type: ignore[misc]


def test_pipeline_parameters_reject_nonpositive_interval() -> None:
    values = make_parameters().__dict__
    values["interval_seconds"] = 0.0

    with pytest.raises(PipelineInputError):
        V3PipelineParameters(**values)


def test_pipeline_requires_explicit_consumer_and_root_zone_identifiers() -> None:
    values = make_parameters().__dict__
    values["consumer_identifier"] = ""
    with pytest.raises(PipelineInputError):
        V3PipelineParameters(**values)
