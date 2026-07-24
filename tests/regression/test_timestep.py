from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration


def test_timestep_refinement_is_stable():
    coarse = load_configuration("configs/default_parameters.yaml", "configs/test_case.yaml")
    coarse["duration_hours"] = 2
    coarse["time_step_seconds"] = 600
    fine = load_configuration("configs/default_parameters.yaml", "configs/test_case.yaml")
    fine["duration_hours"] = 2
    fine["time_step_seconds"] = 300
    a = run_short_case(coarse).iloc[-1]["soil_hto_inventory"]
    b = run_short_case(fine).iloc[-1]["soil_hto_inventory"]
    assert abs(a - b) / b < 0.02
