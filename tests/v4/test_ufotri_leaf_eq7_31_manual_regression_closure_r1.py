import math
from pathlib import Path

import pytest

from cteas_ufotri.plant.leaf_ufotri_v4 import (
    build_ufotri_eq7_25_manual_resistance_state,
    manual_canopy_resistance_s_m,
    saturated_vapour_density_kg_m3,
    ufotri_eq25_wind_profile,
    ufotri_eq27_30_analytic_interval_transfer,
    ufotri_manual_leaf_geometry,
)


ROOT = Path(__file__).resolve().parents[2]


def _manual_profile_term(*, z_m: float, d_m: float, z0_m: float, monin_m: float) -> float:
    """Independent literal oracle for UFOTRI KfK 4605 Eq. (22)-(24)."""

    log_term = math.log((z_m - d_m) / z0_m)
    if math.isinf(monin_m):
        return log_term
    if monin_m > 0.0:
        return log_term + 4.7 * z_m / monin_m
    phi_m = (1.0 - 15.0 * z_m / monin_m) ** -0.25
    inverse_phi = 1.0 / phi_m
    return (
        log_term
        - 2.0 * math.log(0.5 * (1.0 + inverse_phi))
        + 2.0 * math.atan(inverse_phi)
        - math.log(0.5 * (1.0 + inverse_phi**2))
        - math.pi / 2.0
    )


def _manual_eq25_oracle(
    *,
    station_wind_m_s: float,
    station_height_m: float,
    exponent: float,
    canopy_height_m: float,
    monin_m: float,
    von_karman: float = 0.4,
) -> dict[str, float]:
    geometry = ufotri_manual_leaf_geometry(canopy_height_m)
    wind_100m = station_wind_m_s * (100.0 / station_height_m) ** exponent
    reference_term = _manual_profile_term(
        z_m=100.0,
        d_m=geometry.displacement_height_m,
        z0_m=geometry.roughness_length_m,
        monin_m=monin_m,
    )
    vegetation_term = _manual_profile_term(
        z_m=canopy_height_m,
        d_m=geometry.displacement_height_m,
        z0_m=geometry.roughness_length_m,
        monin_m=monin_m,
    )
    u_star = von_karman * wind_100m / reference_term
    vegetation_wind = u_star / von_karman * vegetation_term
    return {
        "wind_100m": wind_100m,
        "u_star": u_star,
        "vegetation_wind": vegetation_wind,
        "ra": vegetation_wind / u_star**2,
        "rb": 2.0 / (von_karman * u_star),
    }


def _advance_concentration(
    *,
    c0: float,
    chi: float,
    dt_s: float,
    water_content_kg_m2: float,
    temperature_k: float,
    resistance_s_m: float,
    alpha: float = 1.1,
) -> float:
    return ufotri_eq27_30_analytic_interval_transfer(
        air_concentration_bq_m3=chi,
        initial_tfwt_concentration_bq_kg_water=c0,
        plant_water_content_kg_m2=water_content_kg_m2,
        temperature_k=temperature_k,
        total_resistance_s_m=resistance_s_m,
        isotope_fractionation_liquid_to_vapour=alpha,
        interval_seconds=dt_s,
    ).next_tfwt_concentration_bq_kg_water


def test_manual_default_canopy_numbers_close_eq14_and_branch_rules():
    # KfK 4605 Section 2.2.2: 4 s cm^-1 daytime, 60 s cm^-1
    # nighttime, and mean LAI=3.  One s/cm is 100 s/m.
    day_stomatal_s_m = 4.0 * 100.0
    night_stomatal_s_m = 60.0 * 100.0
    lai = 3.0

    day = manual_canopy_resistance_s_m(
        lai=lai,
        is_day=True,
        soil_available_water_exhausted=False,
        precipitation_m_s=0.0,
        stomatal_resistance_day_s_m=day_stomatal_s_m,
        stomatal_resistance_night_s_m=night_stomatal_s_m,
    )
    night = manual_canopy_resistance_s_m(
        lai=lai,
        is_day=False,
        soil_available_water_exhausted=False,
        precipitation_m_s=0.0,
        stomatal_resistance_day_s_m=day_stomatal_s_m,
        stomatal_resistance_night_s_m=night_stomatal_s_m,
    )
    exhausted = manual_canopy_resistance_s_m(
        lai=lai,
        is_day=True,
        soil_available_water_exhausted=True,
        precipitation_m_s=0.0,
        stomatal_resistance_day_s_m=day_stomatal_s_m,
        stomatal_resistance_night_s_m=night_stomatal_s_m,
    )
    day_rain = manual_canopy_resistance_s_m(
        lai=lai,
        is_day=True,
        soil_available_water_exhausted=False,
        precipitation_m_s=1.0e-7,
        stomatal_resistance_day_s_m=day_stomatal_s_m,
        stomatal_resistance_night_s_m=night_stomatal_s_m,
    )
    night_rain = manual_canopy_resistance_s_m(
        lai=lai,
        is_day=False,
        soil_available_water_exhausted=False,
        precipitation_m_s=1.0e-7,
        stomatal_resistance_day_s_m=day_stomatal_s_m,
        stomatal_resistance_night_s_m=night_stomatal_s_m,
    )

    assert day == pytest.approx(400.0 / 3.0)
    assert night == pytest.approx(2000.0)
    assert exhausted == pytest.approx(night)
    assert day_rain == 0.0
    assert night_rain == pytest.approx(night)
    assert night / day == pytest.approx(15.0)


def test_manual_geometry_closes_z0_d_flqh_and_minimum_height():
    geometry = ufotri_manual_leaf_geometry(3.0)
    assert geometry.roughness_length_m == pytest.approx(0.3)
    assert geometry.displacement_height_m == pytest.approx(1.8)
    assert geometry.area_source_emission_height_m == pytest.approx(2.4)

    low = ufotri_manual_leaf_geometry(0.75)
    assert low.roughness_length_m == pytest.approx(0.075)
    assert low.displacement_height_m == pytest.approx(0.45)
    assert low.area_source_emission_height_m == pytest.approx(1.0)


@pytest.mark.parametrize("monin_m", [math.inf, 50.0, -50.0])
def test_eq18_21_22_25_match_independent_manual_oracle(monin_m: float):
    inputs = dict(
        station_wind_speed_m_s=5.0,
        station_height_m=10.0,
        station_to_100m_power_exponent=0.2,
        canopy_height_m=2.0,
        explicit_monin_obukhov_length_m=monin_m,
        monin_obukhov_source_id="A3_MANUAL_LITERAL_ORACLE",
        monin_obukhov_source_version="KfK4605-2.2.2",
    )
    actual = ufotri_eq25_wind_profile(**inputs)
    oracle = _manual_eq25_oracle(
        station_wind_m_s=5.0,
        station_height_m=10.0,
        exponent=0.2,
        canopy_height_m=2.0,
        monin_m=monin_m,
    )

    assert actual.wind_100m_m_s == pytest.approx(oracle["wind_100m"], rel=1e-13)
    assert actual.friction_velocity_m_s == pytest.approx(oracle["u_star"], rel=1e-13)
    assert actual.vegetation_wind_speed_m_s == pytest.approx(
        oracle["vegetation_wind"], rel=1e-13
    )
    assert actual.aerodynamic_resistance_s_m == pytest.approx(oracle["ra"], rel=1e-13)

    resistance = build_ufotri_eq7_25_manual_resistance_state(
        lai=3.0,
        is_day=True,
        soil_available_water_exhausted=False,
        precipitation_m_s=0.0,
        stomatal_resistance_day_s_m=400.0,
        stomatal_resistance_night_s_m=6000.0,
        **inputs,
    )
    assert resistance.boundary_layer_resistance_s_m == pytest.approx(
        oracle["rb"], rel=1e-13
    )
    assert resistance.aerodynamic_resistance_s_m == pytest.approx(
        oracle["ra"], rel=1e-13
    )


def test_stable_eq23_oracle_uses_actual_z_not_z_minus_d_in_stability_term():
    actual = ufotri_eq25_wind_profile(
        station_wind_speed_m_s=5.0,
        station_height_m=10.0,
        station_to_100m_power_exponent=0.2,
        canopy_height_m=2.0,
        explicit_monin_obukhov_length_m=50.0,
        monin_obukhov_source_id="A3_STABLE_HEIGHT_ORACLE",
        monin_obukhov_source_version="KfK4605-Eq23",
    )
    manual = _manual_eq25_oracle(
        station_wind_m_s=5.0,
        station_height_m=10.0,
        exponent=0.2,
        canopy_height_m=2.0,
        monin_m=50.0,
    )

    # Reconstruct the superseded A2 interpretation only to prove that this
    # regression distinguishes z/L from (z-d)/L rather than being tautological.
    geometry = actual.geometry
    wind_100m = 5.0 * 10.0**0.2
    old_reference = math.log((100.0 - geometry.displacement_height_m) / geometry.roughness_length_m) + (
        4.7 * (100.0 - geometry.displacement_height_m) / 50.0
    )
    old_vegetation = math.log((2.0 - geometry.displacement_height_m) / geometry.roughness_length_m) + (
        4.7 * (2.0 - geometry.displacement_height_m) / 50.0
    )
    old_u_star = 0.4 * wind_100m / old_reference
    old_wind = old_u_star / 0.4 * old_vegetation

    assert actual.vegetation_wind_speed_m_s == pytest.approx(
        manual["vegetation_wind"], rel=1e-13
    )
    assert not math.isclose(
        actual.vegetation_wind_speed_m_s,
        old_wind,
        rel_tol=1e-3,
        abs_tol=0.0,
    )


def test_eq27_31_match_independent_closed_form_with_manual_fractionation_1_1():
    chi = 100.0
    c0 = 0.0
    mu = 1.5
    temperature_k = 293.15
    resistance = 120.0
    alpha = 1.1
    dt_s = 3600.0
    rho = saturated_vapour_density_kg_m3(temperature_k)
    k_ex = rho / (alpha * mu * resistance)
    target = alpha * chi / rho
    expected_next = target * (1.0 - math.exp(-k_ex * dt_s))

    uptake = ufotri_eq27_30_analytic_interval_transfer(
        air_concentration_bq_m3=chi,
        initial_tfwt_concentration_bq_kg_water=c0,
        plant_water_content_kg_m2=mu,
        temperature_k=temperature_k,
        total_resistance_s_m=resistance,
        isotope_fractionation_liquid_to_vapour=alpha,
        interval_seconds=dt_s,
    )
    assert uptake.exchange_rate_constant_s_1 == pytest.approx(k_ex, rel=1e-13)
    assert uptake.target_tfwt_concentration_bq_kg_water == pytest.approx(target, rel=1e-13)
    assert uptake.next_tfwt_concentration_bq_kg_water == pytest.approx(
        expected_next, rel=1e-13
    )

    decay = ufotri_eq27_30_analytic_interval_transfer(
        air_concentration_bq_m3=0.0,
        initial_tfwt_concentration_bq_kg_water=expected_next,
        plant_water_content_kg_m2=mu,
        temperature_k=temperature_k,
        total_resistance_s_m=resistance,
        isotope_fractionation_liquid_to_vapour=alpha,
        interval_seconds=dt_s,
    )
    expected_decay = expected_next * math.exp(-k_ex * dt_s)
    expected_reemit_fraction = 1.0 - math.exp(-k_ex * dt_s)
    assert decay.next_tfwt_concentration_bq_kg_water == pytest.approx(
        expected_decay, rel=1e-13
    )
    assert decay.eq31_zero_air_reemission_fraction == pytest.approx(
        expected_reemit_fraction, rel=1e-13
    )
    assert decay.eq31_zero_air_reemission_percent == pytest.approx(
        100.0 * expected_reemit_fraction, rel=1e-13
    )


def test_constant_forcing_converges_monotonically_without_target_overshoot():
    chi = 75.0
    mu = 1.2
    temperature_k = 293.15
    resistance = 150.0
    alpha = 1.1
    dt_s = 3600.0
    target = alpha * chi / saturated_vapour_density_kg_m3(temperature_k)
    concentration = 0.0
    history: list[float] = []
    for _ in range(48):
        concentration = _advance_concentration(
            c0=concentration,
            chi=chi,
            dt_s=dt_s,
            water_content_kg_m2=mu,
            temperature_k=temperature_k,
            resistance_s_m=resistance,
            alpha=alpha,
        )
        history.append(concentration)

    assert all(left < right for left, right in zip(history, history[1:]))
    assert all(0.0 < value < target for value in history)
    assert abs(target - history[-1]) < abs(target - history[0])


def test_manual_figure8_additivity_constant_exposure_equals_shifted_pulse_sum():
    """Close the manual's stated additive behavior for long-duration releases.

    KfK 4605 Section 2.2.2 says the constant 40-interval envelope can be
    obtained by adding four curves, each produced by ten intervals of constant
    HTO followed by clean air.  The system is linear, so this is a strong
    manual-semantic regression independent of original UFOTRI executable data.
    """

    chi = 25.0
    mu = 1.5
    temperature_k = 293.15
    resistance = 140.0
    alpha = 1.1
    dt_s = 3600.0
    intervals = 40
    block = 10

    continuous: list[float] = []
    c = 0.0
    for _ in range(intervals):
        c = _advance_concentration(
            c0=c,
            chi=chi,
            dt_s=dt_s,
            water_content_kg_m2=mu,
            temperature_k=temperature_k,
            resistance_s_m=resistance,
            alpha=alpha,
        )
        continuous.append(c)

    component_histories: list[list[float]] = []
    for block_index in range(4):
        start = block_index * block
        stop = start + block
        component: list[float] = []
        c_component = 0.0
        for index in range(intervals):
            forcing = chi if start <= index < stop else 0.0
            c_component = _advance_concentration(
                c0=c_component,
                chi=forcing,
                dt_s=dt_s,
                water_content_kg_m2=mu,
                temperature_k=temperature_k,
                resistance_s_m=resistance,
                alpha=alpha,
            )
            component.append(c_component)
        component_histories.append(component)

    superposed = [
        sum(component[index] for component in component_histories)
        for index in range(intervals)
    ]
    assert superposed == pytest.approx(continuous, rel=2e-13, abs=2e-13)


def test_a3_remains_an_opt_in_leaf_fidelity_closure_not_rc1_or_v2_rewrite():
    historical = (ROOT / "src" / "cteas_ufotri" / "plant" / "leaf_exchange.py").read_text()
    rc1_resistance = (
        ROOT
        / "src"
        / "cteas_ufotri"
        / "plant"
        / "leaf_exchange_resistance"
        / "resistance.py"
    ).read_text()
    rc1_tfwt = (
        ROOT / "src" / "cteas_ufotri" / "plant" / "tfwt_v3" / "tfwt_solver.py"
    ).read_text()

    assert "leaf_ufotri_v4" not in historical
    assert "leaf_ufotri_v4" not in rc1_resistance
    assert "leaf_ufotri_v4" not in rc1_tfwt
    assert "sherwood = 0.664" in historical
    assert "def signed_leaf_exchange_flux" in rc1_resistance
    assert "leaf_transfer = leaf_flux * interval" in rc1_tfwt
