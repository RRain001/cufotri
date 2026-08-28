from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from cteas_ufotri.dose.public import calculate_public_dose_step
from cteas_ufotri.dose.ufotri_manual_v4 import (
    MANUAL_ADULT_REFERENCE_DF_SV_BQ,
    MANUAL_SKIN_TO_INHALATION_FRACTION,
    SECONDS_PER_DAY,
    UFOTRIExposureInputError,
    UFOTRIFoodSpecificActivity,
    UFOTRIManualConsumptionRates,
    UFOTRIManualDosePolicy,
    UFOTRIManualExposureState,
    UFOTRIManualFoodSnapshot,
    advance_ufotri_manual_exposure,
    calculate_ufotri_manual_dose,
    ufotri_exposure_policy_boundary,
    ufotri_manual_adult_reference_policy,
)


def _load_machine_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "run_ufotri_inhalation_skin_ingestion_exposure_reconciliation_r1.py"
    )
    spec = importlib.util.spec_from_file_location("d5_machine_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _foods(
    *,
    green_hto: float = 30.0,
    green_obt: float = 5.0,
    beef_hto: float = 20.0,
    beef_obt: float = 10.0,
    milk_hto: float = 15.0,
    milk_obt: float = 7.0,
) -> UFOTRIManualFoodSnapshot:
    return UFOTRIManualFoodSnapshot(
        green_vegetable=UFOTRIFoodSpecificActivity(green_hto, green_obt),
        beef=UFOTRIFoodSpecificActivity(beef_hto, beef_obt),
        milk=UFOTRIFoodSpecificActivity(milk_hto, milk_obt),
    )


def _habits() -> UFOTRIManualConsumptionRates:
    return UFOTRIManualConsumptionRates(
        breathing_rate_m3_s=20.0 / SECONDS_PER_DAY,
        green_vegetable_kg_d=0.10,
        beef_kg_d=0.05,
        milk_kg_d=0.30,
        provenance_id="TEST_D5_HABITS",
    )


def _advance_day(parts: int = 1) -> UFOTRIManualExposureState:
    state = UFOTRIManualExposureState.zero(exposure_provenance_id="TEST_D5")
    for _ in range(parts):
        state = advance_ufotri_manual_exposure(
            state,
            dt_s=SECONDS_PER_DAY / parts,
            air_hto_bq_m3=100.0,
            foods=_foods(),
        )
    return state


def test_d5_machine_gate_passes() -> None:
    result = _load_machine_module().build_result()
    assert result["status"] == "PASS_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION"
    assert all(result["manual_equation_invariants"].values())
    assert all(result["policy_boundary_invariants"].values())
    assert not any(result["hard_boundaries"].values())


def test_eq106_literal_inhalation_and_skin_identity() -> None:
    state = _advance_day()
    habits = _habits()
    policy = ufotri_manual_adult_reference_policy()
    result = calculate_ufotri_manual_dose(state, habits=habits, policy=policy)
    expected_inhaled_bq = habits.breathing_rate_m3_s * state.air_hto_bq_s_m3
    expected_inhalation = expected_inhaled_bq * MANUAL_ADULT_REFERENCE_DF_SV_BQ
    assert result.inhaled_hto_bq == pytest.approx(expected_inhaled_bq)
    assert result.inhalation_dose_sv == pytest.approx(expected_inhalation)
    assert result.skin_absorption_dose_sv == pytest.approx(
        expected_inhalation * MANUAL_SKIN_TO_INHALATION_FRACTION
    )
    assert result.inhalation_dose_sv + result.skin_absorption_dose_sv == pytest.approx(
        expected_inhalation * 1.5
    )
    assert result.eq106_residual_sv == pytest.approx(0.0, abs=1.0e-24)


def test_eq107_uses_only_three_representative_food_classes_and_same_df_for_obt() -> None:
    state = _advance_day()
    habits = _habits()
    policy = ufotri_manual_adult_reference_policy()
    result = calculate_ufotri_manual_dose(state, habits=habits, policy=policy)
    expected_hto = (
        habits.green_vegetable_kg_d * state.green_vegetable_hto_bq_d_kg
        + habits.beef_kg_d * state.beef_hto_bq_d_kg
        + habits.milk_kg_d * state.milk_hto_bq_d_kg
    )
    expected_obt = (
        habits.green_vegetable_kg_d * state.green_vegetable_obt_bq_d_kg
        + habits.beef_kg_d * state.beef_obt_bq_d_kg
        + habits.milk_kg_d * state.milk_obt_bq_d_kg
    )
    expected = (expected_hto + expected_obt) * MANUAL_ADULT_REFERENCE_DF_SV_BQ
    assert result.ingested_hto_bq == pytest.approx(expected_hto)
    assert result.ingested_obt_bq == pytest.approx(expected_obt)
    assert result.ingestion_dose_sv == pytest.approx(expected)
    assert result.eq107_residual_sv == pytest.approx(0.0, abs=1.0e-24)
    boundary = ufotri_exposure_policy_boundary()
    assert boundary.manual_food_classes == ("green_vegetable", "beef", "milk")
    assert boundary.manual_drinking_water_in_eq107 is False
    assert boundary.manual_root_crop_in_eq107 is False
    assert boundary.manual_grain_in_eq107 is False
    assert boundary.manual_separate_obt_coefficient is False


def test_integrated_exposure_is_partition_invariant() -> None:
    one = _advance_day(1)
    hourly = _advance_day(24)
    quarter_hour = _advance_day(96)
    for field in (
        "elapsed_s",
        "air_hto_bq_s_m3",
        "green_vegetable_hto_bq_d_kg",
        "green_vegetable_obt_bq_d_kg",
        "beef_hto_bq_d_kg",
        "beef_obt_bq_d_kg",
        "milk_hto_bq_d_kg",
        "milk_obt_bq_d_kg",
    ):
        assert getattr(hourly, field) == pytest.approx(
            getattr(one, field), rel=1.0e-14, abs=1.0e-14
        )
        assert getattr(quarter_hour, field) == pytest.approx(
            getattr(one, field), rel=1.0e-14, abs=1.0e-14
        )
    policy = ufotri_manual_adult_reference_policy()
    habits = _habits()
    one_dose = calculate_ufotri_manual_dose(one, habits=habits, policy=policy)
    hourly_dose = calculate_ufotri_manual_dose(hourly, habits=habits, policy=policy)
    quarter_hour_dose = calculate_ufotri_manual_dose(
        quarter_hour, habits=habits, policy=policy
    )
    assert hourly_dose.total_effective_dose_sv == pytest.approx(
        one_dose.total_effective_dose_sv, rel=1.0e-14, abs=1.0e-24
    )
    assert quarter_hour_dose.total_effective_dose_sv == pytest.approx(
        one_dose.total_effective_dose_sv, rel=1.0e-14, abs=1.0e-24
    )


def test_zero_exposure_produces_zero_dose() -> None:
    zero_food = _foods(
        green_hto=0.0, green_obt=0.0, beef_hto=0.0, beef_obt=0.0,
        milk_hto=0.0, milk_obt=0.0,
    )
    state = advance_ufotri_manual_exposure(
        UFOTRIManualExposureState.zero(exposure_provenance_id="ZERO"),
        dt_s=3600.0,
        air_hto_bq_m3=0.0,
        foods=zero_food,
    )
    result = calculate_ufotri_manual_dose(
        state, habits=_habits(), policy=ufotri_manual_adult_reference_policy()
    )
    assert result.total_effective_dose_sv == 0.0
    assert result.ingested_hto_bq == 0.0
    assert result.ingested_obt_bq == 0.0


def test_manual_reference_policy_is_not_modern_hpa_policy() -> None:
    manual = ufotri_manual_adult_reference_policy()
    assert manual.dose_coefficient_sv_bq == 1.7e-11
    assert manual.ingested_obt_uses_hto_coefficient is True
    modern = calculate_public_dose_step(
        SECONDS_PER_DAY,
        100.0,
        {},
        {
            "hto_dose_coefficient_sv_bq": 1.8e-11,
            "obt_ingestion_dose_coefficient_sv_bq": 4.2e-11,
            "breathing_rate_m3_day": 20.0,
            "drinking_water_l_day": 0.0,
            "leafy_kg_day": 0.0,
            "root_crop_kg_day": 0.0,
            "grain_kg_day": 0.0,
            "milk_l_day": 0.0,
            "beef_kg_day": 0.0,
        },
        skin_to_inhalation_factor=0.5,
    )
    manual_state = advance_ufotri_manual_exposure(
        UFOTRIManualExposureState.zero(exposure_provenance_id="AIR_ONLY"),
        dt_s=SECONDS_PER_DAY,
        air_hto_bq_m3=100.0,
        foods=_foods(
            green_hto=0.0, green_obt=0.0, beef_hto=0.0, beef_obt=0.0,
            milk_hto=0.0, milk_obt=0.0,
        ),
    )
    manual_result = calculate_ufotri_manual_dose(
        manual_state,
        habits=UFOTRIManualConsumptionRates(
            breathing_rate_m3_s=20.0 / SECONDS_PER_DAY,
            green_vegetable_kg_d=0.0,
            beef_kg_d=0.0,
            milk_kg_d=0.0,
            provenance_id="AIR_ONLY_HABITS",
        ),
        policy=manual,
    )
    assert modern.total_effective_dose_sv == pytest.approx(100.0 * 20.0 * 1.8e-11 * 1.5)
    assert manual_result.total_effective_dose_sv == pytest.approx(
        100.0 * 20.0 * 1.7e-11 * 1.5
    )
    assert modern.total_effective_dose_sv != manual_result.total_effective_dose_sv


@pytest.mark.parametrize("bad_dt", [0.0, -1.0, float("nan"), float("inf")])
def test_exposure_accumulator_fails_closed_on_invalid_timestep(bad_dt: float) -> None:
    with pytest.raises(UFOTRIExposureInputError):
        advance_ufotri_manual_exposure(
            UFOTRIManualExposureState.zero(exposure_provenance_id="TEST"),
            dt_s=bad_dt,
            air_hto_bq_m3=1.0,
            foods=_foods(),
        )


@pytest.mark.parametrize("bad_value", [-1.0, float("nan"), float("inf")])
def test_exposure_accumulator_fails_closed_on_invalid_concentration(bad_value: float) -> None:
    with pytest.raises(UFOTRIExposureInputError):
        advance_ufotri_manual_exposure(
            UFOTRIManualExposureState.zero(exposure_provenance_id="TEST"),
            dt_s=3600.0,
            air_hto_bq_m3=bad_value,
            foods=_foods(),
        )


def test_manual_policy_requires_explicit_supported_semantics() -> None:
    with pytest.raises(UFOTRIExposureInputError, match="positive"):
        UFOTRIManualDosePolicy(
            dose_coefficient_sv_bq=0.0, coefficient_id="bad", source_reference="test"
        )
    with pytest.raises(UFOTRIExposureInputError, match="QF=1"):
        UFOTRIManualDosePolicy(
            dose_coefficient_sv_bq=1.7e-11,
            coefficient_id="bad-qf",
            source_reference="test",
            quality_factor=2.0,
        )
    with pytest.raises(UFOTRIExposureInputError, match="50%"):
        UFOTRIManualDosePolicy(
            dose_coefficient_sv_bq=1.7e-11,
            coefficient_id="bad-skin",
            source_reference="test",
            skin_to_inhalation_fraction=0.4,
        )
    with pytest.raises(UFOTRIExposureInputError, match="OBT"):
        UFOTRIManualDosePolicy(
            dose_coefficient_sv_bq=1.7e-11,
            coefficient_id="bad-obt",
            source_reference="test",
            ingested_obt_uses_hto_coefficient=False,
        )


def test_habits_and_food_inputs_are_explicit_and_nonnegative() -> None:
    with pytest.raises(UFOTRIExposureInputError):
        UFOTRIManualConsumptionRates(
            breathing_rate_m3_s=-1.0,
            green_vegetable_kg_d=0.0,
            beef_kg_d=0.0,
            milk_kg_d=0.0,
            provenance_id="BAD",
        )
    with pytest.raises(UFOTRIExposureInputError):
        UFOTRIFoodSpecificActivity(-1.0, 0.0)
    with pytest.raises(UFOTRIExposureInputError, match="provenance_id"):
        UFOTRIManualConsumptionRates(
            breathing_rate_m3_s=0.0,
            green_vegetable_kg_d=0.0,
            beef_kg_d=0.0,
            milk_kg_d=0.0,
            provenance_id="",
        )


def test_milk_is_mass_based_without_implicit_litre_conversion() -> None:
    state = UFOTRIManualExposureState(
        elapsed_s=SECONDS_PER_DAY,
        air_hto_bq_s_m3=0.0,
        green_vegetable_hto_bq_d_kg=0.0,
        green_vegetable_obt_bq_d_kg=0.0,
        beef_hto_bq_d_kg=0.0,
        beef_obt_bq_d_kg=0.0,
        milk_hto_bq_d_kg=10.0,
        milk_obt_bq_d_kg=2.0,
        exposure_provenance_id="MILK_MASS",
    )
    habits = UFOTRIManualConsumptionRates(
        breathing_rate_m3_s=0.0,
        green_vegetable_kg_d=0.0,
        beef_kg_d=0.0,
        milk_kg_d=0.5,
        provenance_id="MILK_MASS_HABITS",
    )
    result = calculate_ufotri_manual_dose(
        state, habits=habits, policy=ufotri_manual_adult_reference_policy()
    )
    assert result.milk_ingestion_dose_sv == pytest.approx(0.5 * 12.0 * 1.7e-11)
