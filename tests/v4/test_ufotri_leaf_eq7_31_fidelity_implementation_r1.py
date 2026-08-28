from datetime import datetime, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.leaf_ufotri_v4 import (
    EXPLICIT_MONIN_OBUKHOV_METHOD,
    GOLDER_ESTIMATOR_ID,
    advance_tfwt_with_ufotri_analytic_leaf_exchange,
    build_ufotri_eq7_25_resistance_chain,
    manual_canopy_resistance_s_m,
    saturated_vapour_density_kg_m3,
    ufotri_eq21_boundary_resistance_s_m,
    ufotri_eq25_wind_profile,
    ufotri_eq27_30_analytic_interval_transfer,
    ufotri_eq27_equilibrium_air_concentration_bq_m3,
    ufotri_manual_leaf_geometry,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState


ROOT = Path(__file__).resolve().parents[2]


def _provenance() -> ForcingProvenance:
    return ForcingProvenance(
        source_id="UFOTRI_A2_SYNTHETIC_TEST",
        source_version="r1",
        artifact_sha256="a" * 64,
        spatial_reference="synthetic-plant-area",
        temporal_resolution_s=3600.0,
    )


def _analytic(**overrides):
    values = {
        "air_concentration_bq_m3": 100.0,
        "initial_tfwt_concentration_bq_kg_water": 10.0,
        "plant_water_content_kg_m2": 1.5,
        "temperature_k": 293.15,
        "total_resistance_s_m": 120.0,
        "isotope_fractionation_liquid_to_vapour": 1.1,
        "interval_seconds": 3600.0,
    }
    values.update(overrides)
    return ufotri_eq27_30_analytic_interval_transfer(**values)


def test_manual_canopy_rules_day_night_soil_water_and_rain():
    common = {
        "lai": 2.0,
        "precipitation_m_s": 0.0,
        "stomatal_resistance_day_s_m": 100.0,
        "stomatal_resistance_night_s_m": 1500.0,
    }
    assert manual_canopy_resistance_s_m(
        is_day=True,
        soil_available_water_exhausted=False,
        **common,
    ) == pytest.approx(50.0)
    assert manual_canopy_resistance_s_m(
        is_day=False,
        soil_available_water_exhausted=False,
        **common,
    ) == pytest.approx(750.0)
    assert manual_canopy_resistance_s_m(
        is_day=True,
        soil_available_water_exhausted=True,
        **common,
    ) == pytest.approx(750.0)
    assert manual_canopy_resistance_s_m(
        is_day=True,
        soil_available_water_exhausted=False,
        **{**common, "precipitation_m_s": 1.0e-6},
    ) == 0.0
    assert manual_canopy_resistance_s_m(
        is_day=False,
        soil_available_water_exhausted=False,
        **{**common, "precipitation_m_s": 1.0e-6},
    ) == pytest.approx(750.0)


def test_manual_canopy_path_has_no_vpd_parameter_and_fails_closed_for_zero_lai():
    with pytest.raises(ValueError, match="lai must be positive"):
        manual_canopy_resistance_s_m(
            lai=0.0,
            is_day=True,
            soil_available_water_exhausted=False,
            precipitation_m_s=0.0,
            stomatal_resistance_day_s_m=100.0,
            stomatal_resistance_night_s_m=1500.0,
        )


def test_manual_geometry_matches_recovered_ufotri_ratios_and_flqh_floor():
    geometry = ufotri_manual_leaf_geometry(2.0)
    assert geometry.roughness_length_m == pytest.approx(0.2)
    assert geometry.displacement_height_m == pytest.approx(1.2)
    assert geometry.area_source_emission_height_m == pytest.approx(1.6)
    short = ufotri_manual_leaf_geometry(0.5)
    assert short.area_source_emission_height_m == pytest.approx(1.0)


def test_eq21_boundary_resistance_is_exact_manual_relation():
    assert ufotri_eq21_boundary_resistance_s_m(
        0.5,
        von_karman_constant=0.4,
    ) == pytest.approx(10.0)


def test_eq25_two_step_neutral_mapping_uses_explicit_power_exponent_and_length_source():
    result = ufotri_eq25_wind_profile(
        station_wind_speed_m_s=5.0,
        station_height_m=10.0,
        station_to_100m_power_exponent=0.2,
        canopy_height_m=2.0,
        explicit_monin_obukhov_length_m=math.inf,
        monin_obukhov_source_id="MANUAL_TEST_NEUTRAL",
        monin_obukhov_source_version="r1",
    )
    expected_100m = 5.0 * (100.0 / 10.0) ** 0.2
    assert result.wind_100m_m_s == pytest.approx(expected_100m)
    assert result.monin_obukhov.method == EXPLICIT_MONIN_OBUKHOV_METHOD
    assert result.monin_obukhov.source_id == "MANUAL_TEST_NEUTRAL"
    assert result.monin_obukhov.exact_original_ufotri_logic is False
    assert result.friction_velocity_m_s > 0.0
    assert result.vegetation_wind_speed_m_s > 0.0
    assert result.aerodynamic_resistance_s_m == pytest.approx(
        result.vegetation_wind_speed_m_s / result.friction_velocity_m_s**2
    )


def test_eq25_golder_route_is_named_literature_approximation_not_original_logic():
    result = ufotri_eq25_wind_profile(
        station_wind_speed_m_s=5.0,
        station_height_m=10.0,
        station_to_100m_power_exponent=0.2,
        canopy_height_m=2.0,
        monin_obukhov_estimator_id=GOLDER_ESTIMATOR_ID,
        stability_class="D",
    )
    assert math.isinf(result.monin_obukhov.length_m)
    assert result.monin_obukhov.method == GOLDER_ESTIMATOR_ID
    assert result.monin_obukhov.source_id == "GOLDER_1972_LITERATURE_APPROXIMATION"
    assert result.monin_obukhov.exact_original_ufotri_logic is False


def test_eq25_rejects_missing_or_ambiguous_monin_obukhov_source():
    common = dict(
        station_wind_speed_m_s=5.0,
        station_height_m=10.0,
        station_to_100m_power_exponent=0.2,
        canopy_height_m=2.0,
    )
    with pytest.raises(ValueError, match="exactly one Monin-Obukhov route"):
        ufotri_eq25_wind_profile(**common)
    with pytest.raises(ValueError, match="exactly one Monin-Obukhov route"):
        ufotri_eq25_wind_profile(
            **common,
            explicit_monin_obukhov_length_m=math.inf,
            monin_obukhov_source_id="x",
            monin_obukhov_source_version="1",
            monin_obukhov_estimator_id=GOLDER_ESTIMATOR_ID,
            stability_class="D",
        )


def test_eq7_25_builder_projects_manual_components_onto_frozen_resistance_chain():
    result = build_ufotri_eq7_25_resistance_chain(
        lai=2.0,
        is_day=True,
        soil_available_water_exhausted=False,
        precipitation_m_s=0.0,
        stomatal_resistance_day_s_m=100.0,
        stomatal_resistance_night_s_m=1500.0,
        station_wind_speed_m_s=5.0,
        station_height_m=10.0,
        station_to_100m_power_exponent=0.2,
        canopy_height_m=2.0,
        explicit_monin_obukhov_length_m=math.inf,
        monin_obukhov_source_id="MANUAL_TEST_NEUTRAL",
        monin_obukhov_source_version="r1",
    )
    assert result.canopy_resistance_s_m == pytest.approx(50.0)
    assert result.boundary_layer_resistance_s_m == pytest.approx(
        2.0 / (0.4 * result.wind.friction_velocity_m_s)
    )
    assert result.chain.total_resistance == pytest.approx(
        result.wind.aerodynamic_resistance_s_m
        + result.boundary_layer_resistance_s_m
        + result.canopy_resistance_s_m
    )
    assert result.chain.exchange_velocity == pytest.approx(
        1.0 / result.chain.total_resistance
    )


def test_eq27_equilibrium_uses_saturated_vapour_density_on_tfwt_mass_basis():
    rho_v = saturated_vapour_density_kg_m3(293.15)
    equilibrium = ufotri_eq27_equilibrium_air_concentration_bq_m3(
        tfwt_concentration_bq_kg_water=250.0,
        temperature_k=293.15,
        isotope_fractionation_liquid_to_vapour=1.1,
    )
    assert equilibrium == pytest.approx(250.0 * rho_v / 1.1)


def test_eq27_30_analytic_transfer_closes_inventory_and_exposes_mean_signed_flux():
    result = _analytic()
    expected_transfer = 1.5 * (
        result.next_tfwt_concentration_bq_kg_water
        - result.initial_tfwt_concentration_bq_kg_water
    )
    assert result.leaf_transfer_bq_m2 == pytest.approx(expected_transfer)
    assert result.mean_leaf_exchange_flux_bq_m2_s * 3600.0 == pytest.approx(
        result.leaf_transfer_bq_m2
    )
    assert result.as_leaf_exchange_flux().air_to_leaf_flux_bq_m2_s == pytest.approx(
        result.mean_leaf_exchange_flux_bq_m2_s
    )
    assert 0.0 < result.attenuation < 1.0
    assert result.exchange_rate_constant_s_1 > 0.0


def test_eq27_30_fixed_point_has_zero_transfer():
    rho_v = saturated_vapour_density_kg_m3(293.15)
    target = 1.1 * 100.0 / rho_v
    result = _analytic(initial_tfwt_concentration_bq_kg_water=target)
    assert result.target_tfwt_concentration_bq_kg_water == pytest.approx(target)
    assert result.next_tfwt_concentration_bq_kg_water == pytest.approx(target)
    assert result.leaf_transfer_bq_m2 == pytest.approx(0.0, abs=1.0e-12)


def test_eq27_30_restart_split_is_equivalent_to_one_full_interval():
    full = _analytic(interval_seconds=3600.0)
    first = _analytic(interval_seconds=1800.0)
    second = _analytic(
        interval_seconds=1800.0,
        initial_tfwt_concentration_bq_kg_water=(
            first.next_tfwt_concentration_bq_kg_water
        ),
    )
    assert second.next_tfwt_concentration_bq_kg_water == pytest.approx(
        full.next_tfwt_concentration_bq_kg_water,
        rel=1.0e-13,
        abs=1.0e-13,
    )
    assert first.leaf_transfer_bq_m2 + second.leaf_transfer_bq_m2 == pytest.approx(
        full.leaf_transfer_bq_m2,
        rel=1.0e-13,
        abs=1.0e-13,
    )


def test_eq31_zero_air_reemission_diagnostic_matches_same_analytic_decay():
    result = _analytic(
        air_concentration_bq_m3=0.0,
        initial_tfwt_concentration_bq_kg_water=1000.0,
    )
    expected_fraction = 1.0 - math.exp(
        -result.exchange_rate_constant_s_1 * 3600.0
    )
    assert result.leaf_transfer_bq_m2 < 0.0
    assert result.eq31_zero_air_reemission_fraction == pytest.approx(expected_fraction)
    assert result.eq31_zero_air_reemission_percent == pytest.approx(
        100.0 * expected_fraction
    )
    assert result.next_tfwt_concentration_bq_kg_water == pytest.approx(
        1000.0 * result.attenuation
    )


def test_exact_leaf_operator_projects_through_existing_tfwt_storage_without_loss():
    state = TFWTState.from_inventory(
        plant_identifier="a2-leaf-test",
        crop="test_crop",
        growth_stage="test_stage",
        tfwt_inventory_bq_m2=15.0,
        water_content_kg_m2=1.5,
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        provenance=_provenance(),
    )
    step = advance_tfwt_with_ufotri_analytic_leaf_exchange(
        state,
        air_concentration_bq_m3=100.0,
        temperature_k=293.15,
        total_resistance_s_m=120.0,
        isotope_fractionation_liquid_to_vapour=1.1,
        interval_seconds=3600.0,
    )
    analytic = step.analytic_leaf_transfer
    assert step.tfwt_step.balance.leaf_exchange_input_bq_m2 == pytest.approx(
        analytic.leaf_transfer_bq_m2
    )
    assert step.tfwt_step.balance.residual_bq_m2 == pytest.approx(0.0, abs=1.0e-12)
    assert step.state.tfwt_concentration_bq_kg_water == pytest.approx(
        analytic.next_tfwt_concentration_bq_kg_water
    )


def test_a2_is_opt_in_and_does_not_modify_frozen_rc1_or_historical_v2_sources():
    historical = (ROOT / "src" / "cteas_ufotri" / "plant" / "leaf_exchange.py").read_text()
    resistance = (
        ROOT
        / "src"
        / "cteas_ufotri"
        / "plant"
        / "leaf_exchange_resistance"
        / "resistance.py"
    ).read_text()
    tfwt = (
        ROOT / "src" / "cteas_ufotri" / "plant" / "tfwt_v3" / "tfwt_solver.py"
    ).read_text()
    assert "leaf_ufotri_v4" not in historical
    assert "leaf_ufotri_v4" not in resistance
    assert "leaf_ufotri_v4" not in tfwt
    assert "sherwood = 0.664" in historical
    assert "def signed_leaf_exchange_flux" in resistance
    assert "leaf_transfer = leaf_flux * interval" in tfwt
