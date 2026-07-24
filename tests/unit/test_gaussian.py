import numpy as np

from cteas_ufotri.atmosphere.gaussian import (
    geographic_offset_m,
    point_source_ground_concentration,
    rectangular_area_source_concentration,
    rotate_to_wind,
    vertical_reflection_factor,
)
from cteas_ufotri.atmosphere.dispersion_parameters import (
    classify_pasquill_gifford,
)


def test_gaussian_invariants():
    args = (1e9, 1000.0, 0.0, 3.0, 85.0, "D")
    centre = point_source_ground_concentration(*args)
    offset = point_source_ground_concentration(1e9, 1000, 200, 3, 85, "D")
    assert point_source_ground_concentration(1e9, -1, 0, 3, 85, "D") == 0
    assert centre > offset >= 0
    assert np.isclose(point_source_ground_concentration(2e9, *args[1:]), 2 * centre)
    assert point_source_ground_concentration(0, *args[1:]) == 0


def test_area_source_is_linear_and_quadrature_converges():
    coarse = rectangular_area_source_concentration(
        10.0, 1500.0, 0.0, 3.0, 1000.0, 800.0, quadrature_x=8, quadrature_y=8
    )
    fine = rectangular_area_source_concentration(
        10.0, 1500.0, 0.0, 3.0, 1000.0, 800.0, quadrature_x=24, quadrature_y=24
    )
    doubled = rectangular_area_source_concentration(
        20.0, 1500.0, 0.0, 3.0, 1000.0, 800.0, quadrature_x=24, quadrature_y=24
    )
    assert coarse > 0
    assert abs(coarse - fine) / fine < 0.03
    assert np.isclose(doubled, 2.0 * fine)


def test_mixing_layer_and_geographic_rotation():
    no_top = vertical_reflection_factor(50.0, 100.0)
    with_top = vertical_reflection_factor(50.0, 100.0, 500.0, 4)
    assert with_top >= no_top
    east, north = geographic_offset_m(117.0, 32.0, 117.01, 32.0)
    assert east > 900 and abs(north) < 1e-9
    downwind, crosswind = rotate_to_wind(east, north, 270.0)
    assert downwind > 0 and abs(crosswind) < 1e-9


def test_turner_stability_classification():
    assert classify_pasquill_gifford(1.0, 500.0) == "A"
    assert classify_pasquill_gifford(4.0, 200.0) == "C"
    assert classify_pasquill_gifford(1.0, -20.0, 0.1) == "F"
    assert classify_pasquill_gifford(2.5, -20.0, 0.1) == "E"
    assert classify_pasquill_gifford(2.5, -20.0, 0.8) == "D"


def test_far_field_concentration_decreases_after_plume_maximum():
    concentrations = [
        point_source_ground_concentration(1e9, distance, 0, 3, 85, "D")
        for distance in (5000.0, 10000.0, 20000.0)
    ]
    assert concentrations[0] > concentrations[1] > concentrations[2] > 0
