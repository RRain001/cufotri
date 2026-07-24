import numpy as np

from cteas_ufotri.config import load_configuration
from cteas_ufotri.coupling.integrator import advance
from cteas_ufotri.coupling.reference_solver import (
    solve_coupled_step_reference,
    solve_linear_inventory_reference,
)
from cteas_ufotri.coupling.state import State


def test_internal_transfer_conserves_without_boundaries():
    result = solve_linear_inventory_reference(
        (100.0, 10.0, 5.0), 86400.0, 0.0,
        0.0, 1e-6, 0.0, 0.0, 2e-6, 3e-6, 0.0,
    )
    assert result.success
    assert np.isclose(result.y[:, -1].sum(), 115.0, rtol=1e-10)


def test_refined_explicit_solution_converges_to_coupled_scipy_reference():
    config = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    initial = State(0.01, 100.0, 20.0, 5.0)
    reference = solve_coupled_step_reference(
        initial,
        600.0,
        10.0,
        0.0,
        1e-8,
        2e-8,
        config,
        atmospheric_dry_deposition_bq_m2_s=0.05,
    )
    explicit = initial
    for _ in range(60):
        explicit, _ = advance(
            explicit,
            10.0,
            10.0,
            0.0,
            1e-8,
            2e-8,
            config,
            atmospheric_dry_deposition_bq_m2_s=0.05,
        )
    assert np.allclose(
        [
            explicit.soil_water_m,
            explicit.soil_hto_bq_m2,
            explicit.plant_tfwt_bq_m2,
            explicit.plant_obt_bq_m2,
        ],
        [
            reference.soil_water_m,
            reference.soil_hto_bq_m2,
            reference.plant_tfwt_bq_m2,
            reference.plant_obt_bq_m2,
        ],
        rtol=2e-5,
        atol=1e-8,
    )


def test_coupled_scipy_reference_supports_empirical_reemission():
    config = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    config["reemission"]["mode"] = "ufotri_empirical"
    result = solve_coupled_step_reference(
        State(0.01, 1000.0, 10.0, 1.0),
        600.0,
        0.0,
        0.0,
        2e-8,
        1e-8,
        config,
        elapsed_since_release_s=3600.0,
        is_day=True,
    )
    assert result.soil_hto_bq_m2 < 1000.0
    assert min(
        result.soil_water_m,
        result.soil_hto_bq_m2,
        result.plant_tfwt_bq_m2,
        result.plant_obt_bq_m2,
    ) >= 0.0
