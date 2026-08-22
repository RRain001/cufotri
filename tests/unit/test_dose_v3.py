from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from cteas_ufotri.exposure.dose_v3 import (
    COMMITTED_DOSE_UNIT,
    DOSE_COEFFICIENT_UNIT,
    DoseInputError,
    DoseParameterError,
    DoseParameters,
    DoseSolver,
    DoseUnitError,
)
from cteas_ufotri.exposure.intake_v3 import IntakeState
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance


PROVENANCE = ForcingProvenance(
    source_id="p6-6b-dose-unit-test",
    source_version="1",
    artifact_sha256="d" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=1.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def intake(
    inventory_bq: float,
    *,
    age_group: str = "adult",
    consumer: str = "consumer-001",
) -> IntakeState:
    return IntakeState.from_annual_inventory(
        consumer_identifier=consumer,
        age_group_identifier=age_group,
        food_product_identifier="food-001",
        consumption_rate=1.0,
        intake_inventory_bq=inventory_bq,
        timestamp=START,
        provenance=PROVENANCE,
    )


def parameters(
    *,
    coefficient: float = 0.25,
    age_group: str = "adult",
    pathway: str = "food-ingestion",
) -> DoseParameters:
    return DoseParameters(
        age_group_identifier=age_group,
        radionuclide_identifier="H-3",
        pathway_identifier=pathway,
        dose_coefficient=coefficient,
        dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
        provenance=PROVENANCE,
    )


def test_positive_intake_and_coefficient_produce_positive_dose() -> None:
    state = DoseSolver().advance(intake(4.0), parameters(coefficient=0.25))

    assert state.inventory() == pytest.approx(4.0)
    assert state.dose() == pytest.approx(1.0)
    assert state.dose_coefficient_unit == DOSE_COEFFICIENT_UNIT
    assert state.committed_dose_unit == COMMITTED_DOSE_UNIT
    assert state.consumer() == "consumer-001"


def test_zero_intake_produces_zero_dose() -> None:
    state = DoseSolver().advance(intake(0.0), parameters(coefficient=0.25))

    assert state.inventory() == pytest.approx(0.0)
    assert state.dose() == pytest.approx(0.0)


def test_dose_equation_closes_with_zero_residual() -> None:
    state = DoseSolver().advance(intake(7.5), parameters(coefficient=0.04))

    residual = state.dose() - state.inventory() * state.dose_coefficient
    assert residual == pytest.approx(0.0, abs=1.0e-18)


def test_adult_and_child_coefficients_remain_separate_states() -> None:
    adult = DoseSolver().advance(
        intake(4.0, age_group="adult"),
        parameters(age_group="adult", coefficient=0.25),
    )
    child = DoseSolver().advance(
        intake(4.0, age_group="child"),
        parameters(age_group="child", coefficient=0.5),
    )

    assert adult.age_group_identifier == "adult"
    assert child.age_group_identifier == "child"
    assert adult is not child
    assert adult.dose() == pytest.approx(1.0)
    assert child.dose() == pytest.approx(2.0)
    with pytest.raises(DoseInputError, match="age groups"):
        DoseSolver().advance(
            intake(1.0, age_group="adult"),
            parameters(age_group="child"),
        )


def test_dose_state_is_immutable_and_has_no_upstream_or_assessment_fields() -> None:
    state = DoseSolver().advance(intake(1.0), parameters())

    with pytest.raises(FrozenInstanceError):
        state.committed_dose_sv = 0.0  # type: ignore[misc]
    assert not hasattr(state, "soil")
    assert not hasattr(state, "plant")
    assert not hasattr(state, "food")
    assert not hasattr(state, "regulatory_status")
    assert not hasattr(state, "risk")
    assert not hasattr(state, "emergency_criteria")


def test_dose_requires_explicit_provisional_parameters() -> None:
    with pytest.raises(DoseParameterError, match="provisional"):
        DoseParameters(
            age_group_identifier="adult",
            radionuclide_identifier="H-3",
            pathway_identifier="food-ingestion",
            dose_coefficient=0.25,
            dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
            provenance=PROVENANCE,
            parameter_status="validated",
        )
    with pytest.raises(DoseParameterError, match="non-negative"):
        parameters(coefficient=-0.1)


def test_dose_rejects_implicit_coefficient_unit_conversion() -> None:
    with pytest.raises(DoseUnitError, match="Sv/Bq"):
        DoseParameters(
            age_group_identifier="adult",
            radionuclide_identifier="H-3",
            pathway_identifier="food-ingestion",
            dose_coefficient=0.25,
            dose_coefficient_unit="Sv/kg",
            provenance=PROVENANCE,
        )
