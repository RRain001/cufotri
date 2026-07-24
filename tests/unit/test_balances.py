from copy import deepcopy

from cteas_ufotri.config import load_configuration
from cteas_ufotri.coupling.integrator import advance
from cteas_ufotri.coupling.state import State
from cteas_ufotri.soil.water_balance import update_water_bucket
from cteas_ufotri.soil.hto_balance import concentration_bq_m3


def config():
    return load_configuration("configs/default_parameters.yaml", "configs/test_case.yaml")


def test_bucket_storage_and_overflow():
    quiet = update_water_bucket(0.01, 0, 0, 0, 3600, 0.0005, 0.02)
    assert quiet.water_m == 0.01
    wet = update_water_bucket(0.019, 1e-6, 0, 0, 3600, 0.0005, 0.02)
    assert wet.water_m == 0.02
    assert wet.drainage_m_s > 0


def test_rain_below_capacity_has_no_drainage():
    balance = update_water_bucket(
        0.01, 1e-6, 0.0, 0.0, 100.0, 0.0005, 0.02
    )
    assert balance.water_m == 0.0101
    assert balance.drainage_m_s == 0.0


def test_deposition_and_internal_obt_transfer_conserve():
    cfg = config()
    initial = State(0.01, 100.0, 50.0, 20.0)
    final, diag = advance(initial, 600, 10.0, 0, 0, 0, cfg)
    assert final.soil_hto_bq_m2 > initial.soil_hto_bq_m2
    assert diag.mass_balance.relative_error < 1e-12


def test_no_input_or_output_preserves_hto_inventory():
    cfg = config()
    cfg["physics"]["tritium_decay_constant_s"] = 0.0
    cfg["plant"]["obt_formation_rate_s"] = 0.0
    cfg["plant"]["obt_turnover_rate_s"] = 0.0
    initial = State(0.01, 100.0, 20.0, 5.0)
    final, diagnostics = advance(initial, 600.0, 0.0, 0.0, 0.0, 0.0, cfg)
    assert final == initial
    assert diagnostics.mass_balance.residual_bq_m2 == 0.0


def test_evaporation_removes_water_and_proportional_hto():
    cfg = config()
    cfg["physics"]["tritium_decay_constant_s"] = 0
    cfg["plant"]["obt_formation_rate_s"] = 0
    initial = State(0.01, 100.0)
    final, diag = advance(initial, 100, 0, 0, 1e-6, 0, cfg)
    assert final.soil_water_m < initial.soil_water_m
    assert final.soil_hto_bq_m2 < initial.soil_hto_bq_m2
    assert diag.mass_balance.relative_error < 1e-12


def test_rainwater_hto_is_external_input():
    cfg = config()
    initial = State(0.01)
    final, diag = advance(
        initial, 100.0, 0.0, 1e-6, 0.0, 0.0, cfg,
        rain_hto_concentration_bq_m3=2000.0,
    )
    assert final.soil_hto_bq_m2 == 0.2
    assert diag.mass_balance.relative_error < 1e-12


def test_soil_concentration_identity():
    assert concentration_bq_m3(250.0, 0.01, 1e-12) == 25000.0


def test_infiltration_excess_becomes_optional_runoff():
    balance = update_water_bucket(
        0.01,
        precipitation_m_s=1e-4,
        requested_evaporation_m_s=0.0,
        requested_transpiration_m_s=0.0,
        dt_s=60.0,
        minimum_water_m=0.0005,
        maximum_water_m=0.02,
        runoff_enabled=True,
        infiltration_capacity_m_s=1e-5,
    )
    assert balance.runoff_m_s == 9e-5
    assert balance.drainage_m_s == 0.0


def test_empirical_reemission_mode_preserves_system_balance():
    cfg = config()
    cfg["reemission"]["mode"] = "ufotri_empirical"
    initial = State(0.01, 1000.0)
    final, diagnostics = advance(
        initial, 600.0, 0.0, 0.0, 2e-8, 0.0, cfg,
        elapsed_since_release_s=0.0,
        is_day=True,
    )
    assert final.soil_hto_bq_m2 < initial.soil_hto_bq_m2
    assert diagnostics.soil_reemission_bq_m2_s > 0
    assert diagnostics.mass_balance.relative_error < 1e-12
