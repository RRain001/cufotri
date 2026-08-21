from __future__ import annotations

from datetime import datetime, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.dose import (
    AgeGroup,
    ConsumptionPathway,
    DoseCoefficient,
    DoseLedger,
    DoseLedgerError,
    DoseModel,
    DoseModelError,
    DoseParameterError,
    DoseParameters,
    DosePhysicsResult,
    DoseState,
    DoseStateError,
    SyntheticDoseKernel,
    ZeroDoseKernel,
    calculate,
)
from cteas_ufotri.food_chain import HarvestProduct
from cteas_ufotri.parameters import ParameterDatabase, ParameterUnavailableError
from cteas_ufotri.parameters.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]
PARAMETER_NAME = "dose.coefficient"


def _source_registry() -> SourceRegistry:
    return SourceRegistry.from_file(ROOT / "parameters" / "parameter_sources.yaml")


def _database(*, placeholder: bool = False, value: float = 1.0e-12) -> ParameterDatabase:
    if placeholder:
        entry = {
            "name": PARAMETER_NAME,
            "value": None,
            "unit": "PENDING_VALIDATION",
            "category": "dose",
            "source": "UFOTRI_VALIDATED",
            "reference": "TEST_ONLY placeholder",
            "confidence": "placeholder_pending_validation",
            "applicability": {
                "status": "pending_validation",
                "scope": "test_only",
            },
            "transform": "IDENTITY",
            "bounds": None,
        }
    else:
        entry = {
            "name": PARAMETER_NAME,
            "value": value,
            "unit": "Sv Bq-1",
            "category": "dose",
            "source": "PROJECT_CUSTOM",
            "reference": "TEST_ONLY synthetic parameter",
            "confidence": "internal_default",
            "applicability": {"status": "applicable", "scope": "test_only"},
            "transform": "IDENTITY",
            "bounds": {
                "lower": 0.0,
                "upper": 1.0,
                "lower_inclusive": True,
                "upper_inclusive": True,
            },
        }
    return ParameterDatabase.from_mapping(
        {"schema_version": "1.0", "parameters": [entry]},
        source_registry=_source_registry(),
    )


def _parameters() -> DoseParameters:
    return DoseParameters.from_database(_database())


def _coefficient() -> DoseCoefficient:
    return DoseCoefficient.from_database(
        _database(),
        radionuclide="test-radionuclide",
        parameter_name=PARAMETER_NAME,
    )


def _pathway() -> ConsumptionPathway:
    return ConsumptionPathway(
        food_id="unlisted-food",
        food_activity=100.0,
        consumption_rate=0.01,
        exposure_duration=60.0,
        age_group=AgeGroup.ADULT,
    )


def test_dose_state_initialization_and_explicit_units() -> None:
    pathway = _pathway()
    coefficient = _coefficient()
    state = DoseState(
        radionuclide="test-radionuclide",
        pathway=pathway,
        age_group=AgeGroup.ADULT,
        intake_activity=pathway.intake_activity,
        dose_coefficient=coefficient,
        committed_dose=6.0e-11,
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert state.intake_activity == pytest.approx(60.0)
    assert state.coefficient_value == pytest.approx(1.0e-12)
    assert state.dose_coefficient.unit == "Sv Bq-1"
    assert state.committed_dose == pytest.approx(6.0e-11)


def test_age_group_interface_contains_only_declared_labels() -> None:
    assert {group.value for group in AgeGroup} == {"infant", "child", "adult"}
    assert not hasattr(AgeGroup, "consumption_rate")
    assert not hasattr(AgeGroup, "dose_coefficient")
    assert AgeGroup.coerce("child") is AgeGroup.CHILD


def test_consumption_pathway_is_generic_and_computes_interface_intake() -> None:
    pathway = _pathway()

    assert pathway.food_id == "unlisted-food"
    assert pathway.intake_activity == pytest.approx(60.0)
    assert pathway.age_group is AgeGroup.ADULT


def test_consumption_pathway_accepts_a_food_product_boundary_record() -> None:
    product = HarvestProduct(
        crop_id="crop-product",
        harvest_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        edible_activity=25.0,
        edible_mass=0.5,
    )
    pathway = ConsumptionPathway.from_product(
        product,
        consumption_rate=0.01,
        exposure_duration=10.0,
        age_group=AgeGroup.CHILD,
    )

    assert pathway.food_id == "crop-product"
    assert pathway.food_activity == pytest.approx(50.0)
    assert pathway.intake_activity == pytest.approx(5.0)
    assert pathway.age_group is AgeGroup.CHILD


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ConsumptionPathway("food", -1.0, 1.0, 1.0, AgeGroup.ADULT),
        lambda: ConsumptionPathway("food", 1.0, math.nan, 1.0, AgeGroup.ADULT),
        lambda: ConsumptionPathway("food", 1.0, 1.0, math.inf, AgeGroup.ADULT),
        lambda: ConsumptionPathway("food", 1.0, 1.0, 1.0, "elder"),
    ],
)
def test_invalid_pathway_values_fail_closed(factory) -> None:
    with pytest.raises(DoseStateError):
        factory()


def test_valid_coefficient_keeps_parameter_provenance_and_placeholder_status() -> None:
    coefficient = _coefficient()

    assert coefficient.status == "PLACEHOLDER"
    assert coefficient.parameter_name == PARAMETER_NAME
    assert coefficient.provenance_mapping()["source_provenance"]["source"] == "PROJECT_CUSTOM"
    assert len(_parameters().database_hash) == 64


def test_placeholder_coefficient_fails_closed() -> None:
    with pytest.raises(ParameterUnavailableError, match="placeholder"):
        DoseParameters.from_database(_database(placeholder=True))
    with pytest.raises(ParameterUnavailableError, match="placeholder"):
        DoseCoefficient.from_database(
            _database(placeholder=True),
            radionuclide="test-radionuclide",
            parameter_name=PARAMETER_NAME,
        )


def test_missing_provenance_and_invalid_coefficient_unit_fail_closed() -> None:
    with pytest.raises(DoseStateError, match="provenance"):
        DoseCoefficient(
            radionuclide="test-radionuclide",
            coefficient=1.0e-12,
            unit="Sv Bq-1",
            source_provenance={},
        )
    with pytest.raises(DoseStateError, match="unit"):
        DoseCoefficient(
            radionuclide="test-radionuclide",
            coefficient=1.0e-12,
            unit="Bq",
            source_provenance={"source": "TEST_ONLY"},
        )


def test_invalid_parameter_namespace_and_unit_fail_closed() -> None:
    with pytest.raises(DoseParameterError, match="namespace"):
        DoseParameters.from_database(
            _database(), parameter_names={"dose_coefficient": "soil.coefficient"}
        )

    document = _database().to_mapping()
    document["parameters"][0]["unit"] = "Sv"
    bad_database = ParameterDatabase.from_mapping(
        document, source_registry=_source_registry()
    )
    with pytest.raises(DoseParameterError, match="expected"):
        DoseParameters.from_database(bad_database)


def test_zero_dose_kernel_closes_activity_without_claiming_dose_physics() -> None:
    model = DoseModel(parameters=_parameters(), physics=ZeroDoseKernel())
    state, ledger = model.calculate(_pathway(), _coefficient())

    assert state.committed_dose == pytest.approx(0.0)
    assert ledger.input_activity == pytest.approx(60.0)
    assert ledger.consumption_transfer == pytest.approx(60.0)
    assert ledger.dose_coefficient == pytest.approx(1.0e-12)
    assert ledger.closure == pytest.approx(0.0)
    assert ledger.status == "TEST_ONLY_ZERO_DOSE"


def test_synthetic_dose_kernel_is_deterministic_and_nonnegative() -> None:
    model = DoseModel(parameters=_parameters(), physics=SyntheticDoseKernel())
    first, first_ledger = model.calculate(_pathway(), _coefficient())
    repeat, repeat_ledger = model.calculate(_pathway(), _coefficient())

    assert first == repeat
    assert first_ledger == repeat_ledger
    assert first.committed_dose == pytest.approx(60.0e-12)
    assert first_ledger.dose_identity_error == pytest.approx(0.0, abs=1.0e-24)
    assert first_ledger.closure == pytest.approx(0.0, abs=1.0e-12)
    assert first.committed_dose >= 0.0


def test_functional_calculate_and_provenance() -> None:
    state, ledger = calculate(
        _pathway(),
        _coefficient(),
        _parameters(),
        kernel=SyntheticDoseKernel(),
    )
    provenance = DoseModel(parameters=_parameters(), physics=SyntheticDoseKernel()).provenance(
        _coefficient()
    )

    assert state.committed_dose == pytest.approx(6.0e-11)
    assert ledger.status == "TEST_ONLY_SYNTHETIC"
    assert provenance["implementation_status"] == "FRAMEWORK_COMPLETE"
    assert provenance["physics_equivalence"] == "NOT_CLAIMED"
    assert provenance["regulatory_assessment"] == "NOT_IMPLEMENTED"


def test_default_physics_is_fail_closed() -> None:
    with pytest.raises(RuntimeError, match="physics kernel"):
        DoseModel(parameters=_parameters()).calculate(_pathway(), _coefficient())


def test_state_consistency_and_invalid_physics_result_fail_closed() -> None:
    pathway = _pathway()
    coefficient = _coefficient()
    with pytest.raises(DoseStateError, match="intake_activity"):
        DoseState(
            radionuclide="test-radionuclide",
            pathway=pathway,
            age_group=AgeGroup.ADULT,
            intake_activity=1.0,
            dose_coefficient=coefficient,
            committed_dose=0.0,
            time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

    with pytest.raises(DoseStateError):
        DosePhysicsResult(
            consumption_transfer=-1.0,
            calculated_dose=0.0,
            uncertainty=0.0,
            status="TEST_ONLY",
        ).validate()


def test_ledger_rejects_nonfinite_or_unclosed_values() -> None:
    with pytest.raises(DoseLedgerError):
        DoseLedger(float("nan"), 0.0, 0.0, 0.0)
    with pytest.raises(DoseLedgerError):
        DoseLedger(1.0, 0.0, 1.0e-12, 0.0, closure=1.0).assert_closed()
