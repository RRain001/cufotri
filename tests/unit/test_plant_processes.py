from cteas_ufotri.config import load_configuration
from cteas_ufotri.coupling.integrator import advance
from cteas_ufotri.coupling.state import State
from cteas_ufotri.plant.obt import day_night_formation_rate_s
from cteas_ufotri.plant.tfwt import direct_leaf_flux_bq_m2_s
from cteas_ufotri.plant.leaf_exchange import bidirectional_leaf_exchange


def isolated_config():
    config = load_configuration("configs/default_parameters.yaml", "configs/test_case.yaml")
    config["physics"]["tritium_decay_constant_s"] = 0.0
    config["plant"]["obt_turnover_rate_s"] = 0.0
    return config


def test_no_root_uptake_does_not_increase_tfwt():
    config = isolated_config()
    config["plant"]["obt_formation_rate_s"] = 0.0
    final, _ = advance(State(0.01, 100.0), 600, 0, 0, 0, 0, config)
    assert final.plant_tfwt_bq_m2 == 0


def test_root_uptake_increases_tfwt_and_transpiration_removes_it():
    config = isolated_config()
    config["plant"]["obt_formation_rate_s"] = 0.0
    rooted, _ = advance(State(0.01, 100.0), 600, 0, 0, 0, 1e-7, config)
    assert rooted.plant_tfwt_bq_m2 > 0
    reduced, _ = advance(State(0.01, 0.0, 100.0), 600, 0, 0, 0, 1e-7, config)
    assert reduced.plant_tfwt_bq_m2 < 100.0


def test_obt_formation_is_internal_and_conservative():
    config = isolated_config()
    initial = State(0.01, 0.0, 100.0, 0.0)
    final, diagnostics = advance(initial, 600, 0, 0, 0, 0, config)
    assert final.plant_tfwt_bq_m2 < initial.plant_tfwt_bq_m2
    assert final.plant_obt_bq_m2 > 0
    assert abs(final.total_hto_bq_m2 - initial.total_hto_bq_m2) < 1e-12
    assert diagnostics.mass_balance.relative_error < 1e-12


def test_day_night_obt_multipliers_preserve_equal_day_night_average():
    base = 1.0e-6
    day = day_night_formation_rate_s(base, True, True, 1.5, 0.5)
    night = day_night_formation_rate_s(base, False, True, 1.5, 0.5)
    assert (day + night) / 2.0 == base


def test_direct_leaf_interface_is_disabled_by_default_but_replaceable():
    assert direct_leaf_flux_bq_m2_s(100.0, 0.01, False) == 0.0
    assert direct_leaf_flux_bq_m2_s(100.0, 0.01, True) == 1.0


def _leaf_exchange(air, plant, lai=2.0, is_day=True):
    return bidirectional_leaf_exchange(
        air,
        plant,
        293.15,
        288.15,
        lai,
        is_day,
        aerodynamic_resistance_s_m=50.0,
        boundary_resistance_s_m=50.0,
        stomatal_resistance_day_s_m=400.0,
        stomatal_resistance_night_s_m=6000.0,
        vpd_sensitivity_per_kpa=0.5,
        isotope_fractionation_liquid_to_vapour=1.1,
        water_density_kg_m3=1000.0,
    )


def test_bidirectional_leaf_exchange_sign_equilibrium_lai_and_night():
    reference = _leaf_exchange(0.0, 1.0e6)
    equilibrium_air = reference.equilibrium_air_concentration_bq_m3
    assert _leaf_exchange(equilibrium_air, 1.0e6).net_to_plant_bq_m2_s == 0.0
    assert _leaf_exchange(equilibrium_air * 2.0, 1.0e6).net_to_plant_bq_m2_s > 0.0
    assert _leaf_exchange(0.0, 1.0e6).net_to_plant_bq_m2_s < 0.0
    assert _leaf_exchange(100.0, 1.0e6, lai=0.0).net_to_plant_bq_m2_s == 0.0
    assert (
        _leaf_exchange(100.0, 0.0, is_day=False).conductance_m_s
        < _leaf_exchange(100.0, 0.0, is_day=True).conductance_m_s
    )


def test_bidirectional_leaf_release_preserves_surface_box_closure():
    config = isolated_config()
    config["plant"]["leaf_exchange_mode"] = "bidirectional_resistance"
    config["plant"]["obt_formation_rate_s"] = 0.0
    initial = State(0.01, 0.0, 100.0, 0.0)
    final, diagnostics = advance(
        initial,
        600.0,
        0.0,
        0.0,
        0.0,
        0.0,
        config,
        is_day=True,
        air_temperature_k=293.15,
        dewpoint_temperature_k=288.15,
    )
    assert diagnostics.net_leaf_exchange_bq_m2_s < 0.0
    assert diagnostics.leaf_release_bq_m2_s > 0.0
    assert final.plant_tfwt_bq_m2 < initial.plant_tfwt_bq_m2
    assert diagnostics.surface_box_mass_closure.relative_error < 1.0e-12
