from __future__ import annotations

import numpy as np
import pytest

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration
from cteas_ufotri.soil.multibox import (
    ThreeBoxSoilState,
    advance_three_box_soil,
)


def _config():
    return load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )["soil"]["multibox"]


def test_three_box_zero_forcing_is_finite_nonnegative_and_closed():
    config = _config()
    config["interlayer_drainage_rate_s"] = [0.0, 0.0]
    config["deep_leakage_rate_s"] = 0.0
    config["diffusive_exchange_m_s"] = 0.0
    config["decay_rate_s"] = 0.0
    initial = ThreeBoxSoilState((0.01, 0.025, 0.0375), (10.0, 20.0, 30.0))
    final, diagnostics = advance_three_box_soil(
        initial, 600.0, 0.0, 0.0, 0.0, 0.0, config
    )
    assert final == initial
    assert diagnostics.water_residual_m == pytest.approx(0.0)
    assert diagnostics.hto_residual_bq_m2 == pytest.approx(0.0)


def test_three_box_routes_water_hto_root_uptake_and_deep_leakage():
    initial = ThreeBoxSoilState((0.019, 0.039, 0.059), (100.0, 50.0, 25.0))
    final, diagnostics = advance_three_box_soil(
        initial,
        600.0,
        2.0e-5,
        3.0,
        1.0e-7,
        3.0e-7,
        _config(),
    )
    assert diagnostics.surface_evaporation_m_s > 0.0
    assert diagnostics.root_uptake_m_s == pytest.approx(
        (0.6e-7, 1.2e-7, 1.2e-7)
    )
    assert min(diagnostics.downward_water_m_s) > 0.0
    assert diagnostics.deep_leakage_m_s > 0.0
    assert abs(diagnostics.water_residual_m) < 1.0e-12
    assert abs(diagnostics.hto_residual_bq_m2) < 1.0e-10
    assert np.isfinite(final.water_m).all()
    assert np.isfinite(final.hto_bq_m2).all()
    assert min(final.water_m) >= 0.0
    assert min(final.hto_bq_m2) >= 0.0


def test_only_surface_layer_evaporates_and_diffusion_is_optional():
    config = _config()
    config["interlayer_drainage_rate_s"] = [0.0, 0.0]
    config["deep_leakage_rate_s"] = 0.0
    config["decay_rate_s"] = 0.0
    initial = ThreeBoxSoilState((0.01, 0.025, 0.0375), (100.0, 0.0, 0.0))
    no_diff, _ = advance_three_box_soil(
        initial, 600.0, 0.0, 0.0, 1.0e-6, 0.0, {**config, "diffusive_exchange_m_s": 0.0}
    )
    with_diff, diagnostics = advance_three_box_soil(
        initial, 600.0, 0.0, 0.0, 1.0e-6, 0.0, config
    )
    assert no_diff.hto_bq_m2[1] == 0.0
    assert with_diff.hto_bq_m2[1] > 0.0
    assert diagnostics.surface_evaporation_hto_bq_m2_s > 0.0
    assert abs(diagnostics.hto_residual_bq_m2) < 1.0e-10


def test_formal_short_case_rejects_experimental_three_box_selection():
    config = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    config["soil"]["layer_model"] = "surface_root_deep_3box"
    with pytest.raises(
        ValueError,
        match="experimental standalone soil API",
    ):
        run_short_case(config)
