from __future__ import annotations

import pytest

from cteas_ufotri.config import load_configuration
from cteas_ufotri.dose.public import calculate_public_dose_step


def _dose_config():
    return load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )["dose"]


def test_age_groups_and_coefficient_provenance_are_configured():
    dose = _dose_config()
    assert {"adult", "child", "infant"} == set(dose["age_groups"])
    assert dose["coefficient_source"]
    assert dose["coefficient_version"]
    assert (
        dose["age_groups"]["infant"]["hto_dose_coefficient_sv_bq"]
        > dose["age_groups"]["adult"]["hto_dose_coefficient_sv_bq"]
    )


def test_pathway_and_chemical_form_decomposition_sums_exactly():
    dose = _dose_config()
    concentrations = {
        "drinking_water_hto_bq_l": 10.0,
        "leafy_tfwt_bq_kg_fresh": 11.0,
        "leafy_obt_bq_kg_fresh": 12.0,
        "root_crop_tfwt_bq_kg_fresh": 13.0,
        "root_crop_obt_bq_kg_fresh": 14.0,
        "grain_tfwt_bq_kg_fresh": 15.0,
        "grain_obt_bq_kg_fresh": 16.0,
        "milk_hto_bq_l": 17.0,
        "milk_obt_bq_l": 18.0,
        "beef_hto_bq_kg": 19.0,
        "beef_obt_bq_kg": 20.0,
    }
    result = calculate_public_dose_step(
        86400.0,
        100.0,
        concentrations,
        dose["age_groups"]["adult"],
        skin_to_inhalation_factor=0.5,
    )
    assert result.inhalation_dose_sv > 0.0
    assert result.skin_absorption_dose_sv == pytest.approx(
        0.5 * result.inhalation_dose_sv
    )
    assert min(
        result.drinking_water_dose_sv,
        result.plant_ingestion_dose_sv,
        result.milk_dose_sv,
        result.meat_dose_sv,
        result.total_hto_dose_sv,
        result.total_obt_dose_sv,
    ) > 0.0
    assert result.total_effective_dose_sv == pytest.approx(
        result.total_hto_dose_sv + result.total_obt_dose_sv
    )
    assert result.total_effective_dose_sv == pytest.approx(
        result.inhalation_dose_sv
        + result.skin_absorption_dose_sv
        + result.drinking_water_dose_sv
        + result.plant_ingestion_dose_sv
        + result.milk_dose_sv
        + result.meat_dose_sv
    )


def test_zero_exposure_gives_zero_dose():
    dose = _dose_config()
    result = calculate_public_dose_step(
        600.0,
        0.0,
        {},
        dose["age_groups"]["child"],
        skin_to_inhalation_factor=0.5,
    )
    assert result.total_effective_dose_sv == 0.0

