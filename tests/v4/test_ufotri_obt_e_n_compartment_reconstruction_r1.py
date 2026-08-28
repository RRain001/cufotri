from datetime import datetime, timedelta, timezone
import math

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_ufotri_v4 import (
    LONG_TERM_CONTEXT,
    NO_SEPARATE_EXCHANGEABLE_POOL,
    SHORT_TERM_CONTEXT,
    current_short_term_inventory_baseline,
    make_ufotri_obt_state_view,
    ufotri_long_term_ingestion_obt_profile,
    ufotri_obt_rate_reconciliation,
    ufotri_obt_role_map,
    ufotri_short_term_obt_profile,
)
from cteas_ufotri.plant.obt_v3 import (
    OBTParameters,
    OBTState,
    UFOTRI_OBT_DAYLIGHT_MULTIPLIER,
    UFOTRI_OBT_KF_S,
    UFOTRI_OBT_KR_S,
    UFOTRI_OBT_NIGHTTIME_MULTIPLIER,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState


UTC = timezone.utc


def _provenance() -> ForcingProvenance:
    return ForcingProvenance(
        source_id="B1_SYNTHETIC_STATE_ROLE_TEST",
        source_version="ufotri-obt-e-n-compartment-reconstruction-r1",
        artifact_sha256="b" * 64,
        spatial_reference="synthetic-plant-area",
        temporal_resolution_s=3600.0,
    )


def _states() -> tuple[TFWTState, OBTState]:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    provenance = _provenance()
    tfwt = TFWTState.from_inventory(
        plant_identifier="plant-1",
        crop="synthetic-crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=8.0,
        water_content_kg_m2=0.4,
        time=timestamp,
        provenance=provenance,
        area_basis="plant_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier="plant-1",
        crop="synthetic-crop",
        growth_stage="vegetative",
        obt_inventory_bq_m2=2.0,
        plant_mass_kg_m2=0.1,
        timestamp=timestamp,
        provenance=provenance,
        area_basis="plant_area",
    )
    return tfwt, obt


def test_exchangeable_obt_is_not_a_third_inventory_pool():
    role_map = ufotri_obt_role_map()

    assert NO_SEPARATE_EXCHANGEABLE_POOL is True
    assert role_map.exchangeable_obt_representation == "TFWTState"
    assert role_map.nonexchangeable_obt_representation == "OBTState"
    assert role_map.separate_exchangeable_obt_pool is False
    assert role_map.exchangeable_obt_extra_inventory_added is False
    assert role_map.double_counting_prohibited is True
    assert role_map.first_order_inventory_transfer_structure_recovered is True


def test_state_view_preserves_exactly_two_existing_food_components():
    tfwt, obt = _states()
    view = make_ufotri_obt_state_view(tfwt, obt)

    assert view.tfwt_state is tfwt
    assert view.nonexchangeable_obt_state is obt
    assert view.tfwt_inventory_bq_m2 == 8.0
    assert view.nonexchangeable_obt_inventory_bq_m2 == 2.0
    assert view.represented_food_components_bq_m2 == (2.0, 8.0)
    assert sum(view.represented_food_components_bq_m2) == 10.0


def test_state_view_fails_closed_on_mismatched_identity_time_or_area():
    tfwt, obt = _states()

    wrong_plant = OBTState.from_inventory(
        plant_identifier="other",
        crop=obt.crop,
        growth_stage=obt.growth_stage,
        obt_inventory_bq_m2=obt.inventory(),
        plant_mass_kg_m2=obt.plant_mass_kg_m2,
        timestamp=obt.timestamp,
        provenance=obt.provenance,
        area_basis=obt.area_basis,
    )
    with pytest.raises(ValueError, match="plant identifiers"):
        make_ufotri_obt_state_view(tfwt, wrong_plant)

    wrong_time = obt.with_inventory(
        obt_inventory_bq_m2=obt.inventory(),
        timestamp=obt.timestamp + timedelta(hours=1),
    )
    with pytest.raises(ValueError, match="timestamps"):
        make_ufotri_obt_state_view(tfwt, wrong_time)

    wrong_area = OBTState.from_inventory(
        plant_identifier=obt.plant_identifier,
        crop=obt.crop,
        growth_stage=obt.growth_stage,
        obt_inventory_bq_m2=obt.inventory(),
        plant_mass_kg_m2=obt.plant_mass_kg_m2,
        timestamp=obt.timestamp,
        provenance=obt.provenance,
        area_basis="soil_surface_area",
    )
    with pytest.raises(ValueError, match="area bases"):
        make_ufotri_obt_state_view(tfwt, wrong_area)


def test_short_term_section_2_2_6_values_are_exactly_recovered():
    profile = ufotri_short_term_obt_profile()

    assert profile.context == SHORT_TERM_CONTEXT
    assert profile.formation_per_hour == 0.0006
    assert profile.loss_per_hour == 0.003
    assert profile.formation_s_1 == 0.0006 / 3600.0
    assert profile.loss_s_1 == 0.003 / 3600.0
    assert profile.inventory_transfer_structure_recovered is True
    assert profile.controlled_daily_average_binding_authorized is True


def test_short_term_unknown_day_night_and_exact_original_parameters_remain_fail_closed():
    profile = ufotri_short_term_obt_profile()

    assert profile.daylight_multiplier is None
    assert profile.nighttime_multiplier is None
    assert profile.day_night_split_recovered is False
    assert profile.exact_original_parameterization_recovered is False
    assert set(profile.source_ambiguities) == {
        "NORMALIZED_DAY_NIGHT_FORMATION_MULTIPLIERS_NOT_RECOVERED",
        "SECTION_2_2_6_AND_EQ66_FORWARD_RATE_NUMBERS_NOT_IDENTICAL",
        "SECTION_2_2_6_AND_EQ65_LOSS_RATE_NUMBERS_NOT_IDENTICAL",
        "ORIGINAL_EXECUTABLE_PARAMETER_SELECTION_UNAVAILABLE",
    }


def test_frozen_short_term_inventory_baseline_is_exact_section_2_2_6_daily_average():
    profile = ufotri_short_term_obt_profile()
    parameters = current_short_term_inventory_baseline()

    assert isinstance(parameters, OBTParameters)
    assert parameters.kf_s == UFOTRI_OBT_KF_S == profile.formation_s_1
    assert parameters.kr_s == UFOTRI_OBT_KR_S == profile.loss_s_1
    assert parameters.daylight_multiplier == UFOTRI_OBT_DAYLIGHT_MULTIPLIER == 1.0
    assert parameters.nighttime_multiplier == UFOTRI_OBT_NIGHTTIME_MULTIPLIER == 1.0
    assert profile.day_night_split_recovered is False
    assert profile.exact_original_parameterization_recovered is False


def test_long_term_eq65_reverse_rate_is_ln2_over_ten_days():
    profile = ufotri_long_term_ingestion_obt_profile()

    assert profile.context == LONG_TERM_CONTEXT
    assert math.isclose(
        profile.obt_to_hto_d_1,
        math.log(2.0) / 10.0,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )
    assert math.isclose(
        profile.obt_to_hto_h_1,
        math.log(2.0) / 10.0 / 24.0,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )


def test_long_term_eq66_forward_rate_is_reconstructed_from_manual_mass_basis():
    profile = ufotri_long_term_ingestion_obt_profile()
    independent = (
        (math.log(2.0) / 10.0)
        * 0.1
        * 9.0
        / (0.4 * 13.0)
    )

    assert math.isclose(
        profile.hto_to_obt_d_1_exact_from_stated_masses,
        independent,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )
    assert math.isclose(
        profile.hto_to_obt_d_1_exact_from_stated_masses,
        0.012,
        rel_tol=0.0,
        abs_tol=5.0e-6,
    )
    assert profile.hto_to_obt_d_1_manual_rounded == 0.012


def test_hourly_section_and_eq65_66_are_related_but_not_numerically_identical():
    rates = ufotri_obt_rate_reconciliation()

    assert math.isclose(rates.eq66_forward_h_1, 0.0004998657552114991, rel_tol=0.0, abs_tol=1.0e-15)
    assert math.isclose(rates.eq65_loss_h_1, 0.0028881132523331052, rel_tol=0.0, abs_tol=1.0e-15)
    assert math.isclose(rates.forward_relative_difference_vs_eq66, 0.20032227401961734, rel_tol=0.0, abs_tol=1.0e-14)
    assert math.isclose(rates.loss_relative_difference_vs_eq65, 0.03874042944005375, rel_tol=0.0, abs_tol=1.0e-14)
    assert rates.numerically_identical is False


def test_short_term_and_long_term_profiles_are_not_interchangeable_defaults():
    short = ufotri_short_term_obt_profile()
    long = ufotri_long_term_ingestion_obt_profile()

    assert short.context != long.context
    assert short.source_section == "KfK4605_2.2.6"
    assert long.source_section == "KfK4605_3.3.3_Eq65_66"
    assert long.current_short_term_solver_binding_authorized is False
    assert long.downstream_stage == "UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1"
    assert not math.isclose(short.loss_per_hour * 24.0, long.obt_to_hto_d_1)


def test_state_view_type_checks_fail_before_semantic_mapping():
    tfwt, obt = _states()

    with pytest.raises(TypeError, match="tfwt_state"):
        make_ufotri_obt_state_view(object(), obt)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="nonexchangeable_obt_state"):
        make_ufotri_obt_state_view(tfwt, object())  # type: ignore[arg-type]
