from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cteas_ufotri.config import load_configuration
from cteas_ufotri.crop.phenology import CropParameters, lai_at_time


def _crop(name="generic_crop"):
    config = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    return CropParameters.from_mapping(
        name, config["crops"]["parameters"][name]
    )


def _date(doy):
    return datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(days=doy - 1)


def test_required_crop_parameterizations_are_present_and_valid():
    config = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    required = {
        "grass",
        "leafy_vegetable",
        "root_vegetable",
        "cereal",
        "pasture",
        "generic_crop",
    }
    assert required <= set(config["crops"]["parameters"])
    for name in required:
        crop = CropParameters.from_mapping(
            name, config["crops"]["parameters"][name]
        )
        assert sum(crop.root_fraction_by_layer) == pytest.approx(1.0)


def test_piecewise_and_smooth_lai_have_season_boundaries_and_peak():
    crop = _crop()
    assert lai_at_time(_date(crop.growth_start_doy - 1), crop, "piecewise_growth_stage") == 0
    assert lai_at_time(_date(crop.growth_start_doy), crop, "piecewise_growth_stage") == 0
    middle = (crop.growth_start_doy + crop.harvest_doy) // 2
    assert lai_at_time(_date(middle), crop, "piecewise_growth_stage") == crop.max_lai
    assert 0 < lai_at_time(_date(middle), crop, "smooth_seasonal") <= crop.max_lai
    assert lai_at_time(_date(crop.harvest_doy), crop, "smooth_seasonal") == pytest.approx(0)
    assert lai_at_time(_date(crop.harvest_doy + 1), crop, "piecewise_growth_stage") == 0


def test_constant_and_external_lai_modes():
    crop = _crop()
    assert lai_at_time(_date(1), crop, "constant") == crop.constant_lai
    assert lai_at_time(_date(1), crop, "external_timeseries", external_lai=2.75) == 2.75
    with pytest.raises(ValueError, match="forcing"):
        lai_at_time(_date(1), crop, "external_timeseries")
