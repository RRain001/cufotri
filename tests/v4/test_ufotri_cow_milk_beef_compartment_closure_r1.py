from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import math
from pathlib import Path

import pytest

from cteas_ufotri.foodchain.ufotri_cow_milk_beef_v4 import (
    MANUAL_GRASS_SURROGATE_ONLY,
    UFOTRIAnimalInputError,
    UFOTRICowMilkBeefForcing,
    UFOTRICowMilkBeefSolver,
    UFOTRICowMilkBeefState,
    slaughter_to_beef,
    ufotri_cow_milk_beef_manual_profile,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
DAY_S = 86400.0


def _state() -> UFOTRICowMilkBeefState:
    return UFOTRICowMilkBeefState(
        timestamp=T0,
        grass_hto_bq_m2=100.0,
        grass_obt_bq_m2=50.0,
        cow_hto_bq_m2=25.0,
        cow_obt_bq_m2=10.0,
    )


def _forcing(atmosphere: float = 1000.0) -> UFOTRICowMilkBeefForcing:
    return UFOTRICowMilkBeefForcing(
        atmosphere_hto_inventory_bq_m2=atmosphere,
        atmosphere_provenance="SYNTHETIC_D4_CONTROLLED_COLUMN",
    )


def _vector(state: UFOTRICowMilkBeefState) -> tuple[float, ...]:
    return (
        state.grass_hto_bq_m2,
        state.grass_obt_bq_m2,
        state.cow_hto_bq_m2,
        state.cow_obt_bq_m2,
        state.milk_hto_bq_m2,
        state.milk_obt_bq_m2,
        state.beef_hto_bq_m2,
        state.beef_obt_bq_m2,
    )


def _load_machine_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "run_ufotri_cow_milk_beef_compartment_closure_r1.py"
    )
    spec = importlib.util.spec_from_file_location("d4_machine_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d4_machine_gate_passes() -> None:
    result = _load_machine_module().build_result()
    assert result["status"] == "PASS_UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE"
    assert all(result["profile"]["profile_gates"].values())
    assert all(result["numerical"]["numerical_gates"].values())
    assert not any(result["hard_boundaries"].values())


def test_manual_profile_preserves_equation_rates_and_hard_boundaries() -> None:
    p = ufotri_cow_milk_beef_manual_profile()
    assert p.cow_water_to_atmosphere_d_1 == 0.03
    assert p.cow_water_to_soil1_d_1 == 0.13
    assert p.grass_obt_to_milk_obt_d_1 == 0.0017
    assert p.cow_obt_to_milk_obt_d_1 == 0.0021
    assert p.cow_hto_to_milk_hto_d_1 == 0.039
    assert p.cow_hto_to_milk_obt_d_1 == 0.0013
    assert p.cow_obt_to_cow_hto_d_1 == 0.015
    assert p.cow_hto_to_cow_obt_d_1 == 0.0011
    assert p.grass_obt_to_cow_obt_d_1 == 0.0033
    assert p.grass_hto_to_cow_hto_d_1 == 0.024
    assert p.grass_obt_to_cow_hto_d_1 == 0.021
    assert p.grass_hto_to_grass_obt_d_1 == 0.012
    assert p.grass_obt_to_grass_hto_d_1 == 0.043
    assert p.eq86_heading_ocr_ambiguous
    assert p.eq86_role_resolved_from_compartment_indices_and_context
    assert not p.project_external_feed_activated
    assert not p.project_drinking_water_activated
    assert not p.project_support_area_normalization_activated
    assert not p.continuous_beef_turnover_activated
    assert not p.edible_beef_mass_default_activated
    assert not p.production_binding_authorized
    assert not p.original_numerical_discretization_recovered


def test_eq98_exact_geometry_and_manual_rounding_are_both_visible() -> None:
    p = ufotri_cow_milk_beef_manual_profile()
    assert p.atmosphere_to_cow_hto_eq98_exact_d_1 == pytest.approx(4.875e-5)
    assert p.atmosphere_to_cow_hto_manual_rounded_d_1 == 4.9e-5
    assert p.atmosphere_to_cow_hto_eq98_exact_d_1 != p.atmosphere_to_cow_hto_manual_rounded_d_1


def test_eq105_2_closes_with_animal_and_milk_loss_terms() -> None:
    p = ufotri_cow_milk_beef_manual_profile()
    assert p.grass_obt_eq105_2_reconstructed_d_1 == pytest.approx(0.043)
    assert p.grass_obt_overall_loss_d_1 == pytest.approx(
        p.grass_obt_to_grass_hto_d_1
        + p.grass_obt_to_cow_obt_d_1
        + p.grass_obt_to_cow_hto_d_1
        + p.grass_obt_to_milk_obt_d_1
    )


def test_manual_rounded_rate_tensions_are_not_renormalized() -> None:
    p = ufotri_cow_milk_beef_manual_profile()
    assert p.cow_hto_total_hazard_d_1 == pytest.approx(0.2014)
    assert p.cow_obt_total_hazard_d_1 == pytest.approx(0.0171)
    assert p.cow_hto_total_hazard_d_1 != pytest.approx(p.cow_water_overall_loss_exact_d_1)
    assert p.cow_obt_total_hazard_d_1 != pytest.approx(p.cow_obt_overall_loss_exact_d_1)


def test_eq98_is_animal_inventory_input_and_balance_closes() -> None:
    p = ufotri_cow_milk_beef_manual_profile()
    state = UFOTRICowMilkBeefState(timestamp=T0)
    result = UFOTRICowMilkBeefSolver(p).advance(state, _forcing(1000.0), DAY_S)
    assert result.balance.eq98_atmosphere_input_bq_m2 == pytest.approx(0.049)
    assert result.state.cow_hto_bq_m2 > 0.0
    assert not hasattr(result, "dose_sv")
    assert abs(result.balance.residual_bq_m2) <= 1.0e-12


def test_full_transfer_system_conserves_activity_with_explicit_boundaries() -> None:
    result = UFOTRICowMilkBeefSolver(
        ufotri_cow_milk_beef_manual_profile()
    ).advance(_state(), _forcing(), DAY_S)
    b = result.balance
    assert b.cow_to_atmosphere_boundary_bq_m2 > 0.0
    assert b.cow_to_soil1_boundary_bq_m2 > 0.0
    assert result.state.milk_hto_bq_m2 > 0.0
    assert result.state.milk_obt_bq_m2 > 0.0
    assert abs(b.residual_bq_m2) <= 1.0e-11
    assert b.initial_internal_bq_m2 + b.eq98_atmosphere_input_bq_m2 == pytest.approx(
        b.cow_to_atmosphere_boundary_bq_m2
        + b.cow_to_soil1_boundary_bq_m2
        + b.final_internal_bq_m2,
        abs=1.0e-11,
    )


def test_grass_obt_reaches_all_eq104_97_85_and_eq105_2_receivers() -> None:
    state = UFOTRICowMilkBeefState(timestamp=T0, grass_obt_bq_m2=100.0)
    result = UFOTRICowMilkBeefSolver(
        ufotri_cow_milk_beef_manual_profile()
    ).advance(state, _forcing(0.0), 3600.0)
    assert result.state.grass_hto_bq_m2 > 0.0
    assert result.state.cow_hto_bq_m2 > 0.0
    assert result.state.cow_obt_bq_m2 > 0.0
    assert result.state.milk_obt_bq_m2 > 0.0


def test_deterministic_repeat() -> None:
    solver = UFOTRICowMilkBeefSolver(ufotri_cow_milk_beef_manual_profile())
    a = solver.advance(_state(), _forcing(), DAY_S)
    b = solver.advance(_state(), _forcing(), DAY_S)
    assert a == b


def test_restart_equivalence_on_same_numerical_grid() -> None:
    solver = UFOTRICowMilkBeefSolver(
        ufotri_cow_milk_beef_manual_profile(), numerical_step_seconds=3600.0
    )
    whole = solver.advance(_state(), _forcing(), DAY_S)
    first = solver.advance(_state(), _forcing(), DAY_S / 2.0)
    second = solver.advance(first.state, _forcing(), DAY_S / 2.0)
    assert _vector(whole.state) == pytest.approx(_vector(second.state), abs=1.0e-12)


def test_hourly_partition_equals_one_day_for_hourly_numerical_grid() -> None:
    solver = UFOTRICowMilkBeefSolver(
        ufotri_cow_milk_beef_manual_profile(), numerical_step_seconds=3600.0
    )
    whole = solver.advance(_state(), _forcing(), DAY_S)
    state = _state()
    for _ in range(24):
        state = solver.advance(state, _forcing(), 3600.0).state
    assert _vector(whole.state) == pytest.approx(_vector(state), abs=1.0e-12)


def test_timestep_refinement_monotonically_approaches_225s_reference() -> None:
    p = ufotri_cow_milk_beef_manual_profile()
    duration = 30.0 * DAY_S
    reference = UFOTRICowMilkBeefSolver(
        p, numerical_step_seconds=225.0
    ).advance(_state(), _forcing(), duration).state
    ref = _vector(reference)

    errors: list[float] = []
    for step in (3600.0, 1800.0, 900.0, 450.0):
        candidate = UFOTRICowMilkBeefSolver(
            p, numerical_step_seconds=step
        ).advance(_state(), _forcing(), duration).state
        vec = _vector(candidate)
        scale = max(max(abs(v) for v in ref), 1.0)
        errors.append(max(abs(a - b) for a, b in zip(vec, ref)) / scale)

    assert errors[0] > errors[1] > errors[2] > errors[3] > 0.0
    assert errors[-1] < 0.01


def test_zero_inventory_with_zero_atmosphere_stays_zero() -> None:
    state = UFOTRICowMilkBeefState(timestamp=T0)
    result = UFOTRICowMilkBeefSolver(
        ufotri_cow_milk_beef_manual_profile()
    ).advance(state, _forcing(0.0), DAY_S)
    assert result.state.total_internal_bq_m2 == 0.0
    assert result.balance.residual_bq_m2 == 0.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"external_feed_hto_bq_m2_s": 1.0},
        {"external_feed_obt_bq_m2_s": 1.0},
        {"external_drinking_water_hto_bq_m2_s": 1.0},
        {"feed_mode": "V2_PROJECT_FEED"},
    ],
)
def test_project_feed_and_drinking_water_assumptions_fail_closed(kwargs: dict[str, object]) -> None:
    with pytest.raises(UFOTRIAnimalInputError):
        UFOTRICowMilkBeefForcing(
            atmosphere_hto_inventory_bq_m2=0.0,
            atmosphere_provenance="synthetic",
            **kwargs,
        )


def test_explicit_slaughter_moves_activity_to_beef_without_loss() -> None:
    state = UFOTRICowMilkBeefState(
        timestamp=T0,
        cow_hto_bq_m2=80.0,
        cow_obt_bq_m2=20.0,
        beef_hto_bq_m2=3.0,
        beef_obt_bq_m2=2.0,
    )
    final, balance = slaughter_to_beef(state, 0.25)
    assert final.cow_hto_bq_m2 == 60.0
    assert final.cow_obt_bq_m2 == 15.0
    assert final.beef_hto_bq_m2 == 23.0
    assert final.beef_obt_bq_m2 == 7.0
    assert balance.cow_activity_removed_bq_m2 == 25.0
    assert balance.beef_activity_added_bq_m2 == 25.0
    assert balance.total_residual_bq_m2 == 0.0
    assert final.total_internal_bq_m2 == state.total_internal_bq_m2


@pytest.mark.parametrize("fraction", [-0.1, 1.1, math.nan])
def test_invalid_slaughter_fraction_fails_closed(fraction: float) -> None:
    with pytest.raises(UFOTRIAnimalInputError):
        slaughter_to_beef(_state(), fraction)


def test_invalid_state_forcing_and_interval_fail_closed() -> None:
    with pytest.raises(UFOTRIAnimalInputError):
        UFOTRICowMilkBeefState(timestamp=T0, cow_hto_bq_m2=-1.0)
    with pytest.raises(UFOTRIAnimalInputError):
        UFOTRICowMilkBeefForcing(
            atmosphere_hto_inventory_bq_m2=math.nan,
            atmosphere_provenance="synthetic",
        )
    with pytest.raises(UFOTRIAnimalInputError):
        UFOTRICowMilkBeefForcing(
            atmosphere_hto_inventory_bq_m2=0.0,
            atmosphere_provenance="",
        )
    solver = UFOTRICowMilkBeefSolver(ufotri_cow_milk_beef_manual_profile())
    with pytest.raises(UFOTRIAnimalInputError):
        solver.advance(_state(), _forcing(), 0.0)
    with pytest.raises(UFOTRIAnimalInputError):
        UFOTRICowMilkBeefSolver(
            ufotri_cow_milk_beef_manual_profile(),
            numerical_step_seconds=0.0,
        )


def test_feed_mode_constant_is_manual_only() -> None:
    assert MANUAL_GRASS_SURROGATE_ONLY == "MANUAL_EQ99_GRASS_SURROGATE_ONLY"
