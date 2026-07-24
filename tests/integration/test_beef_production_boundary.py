from __future__ import annotations

from pathlib import Path

import pytest

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration


ROOT = Path(__file__).resolve().parents[2]


def _full_dose_case() -> dict:
    return load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/v2/v2_full_adult_dose.yaml",
    )


def test_formal_beef_dose_uses_produced_and_inventory_limited_product():
    config = _full_dose_case()
    frame = run_short_case(config)
    final = frame.iloc[-1]
    produced = final["beef_produced_hto_bq_m2"] + final[
        "beef_produced_obt_bq_m2"
    ]
    consumed = final["beef_consumed_hto_bq_m2"] + final[
        "beef_consumed_obt_bq_m2"
    ]
    stored = final["beef_product_hto_bq_m2"] + final[
        "beef_product_obt_bq_m2"
    ]
    assert produced > 0.0
    assert consumed > 0.0
    assert stored > 0.0
    assert consumed <= produced
    assert final["meat_dose_sv"] > 0.0
    assert produced == pytest.approx(
        final["animal_slaughter_bq_m2"],
        rel=1.0e-12,
    )
    assert produced == pytest.approx(
        consumed + stored + final["beef_product_decay_bq_m2"],
        rel=1.0e-12,
    )
    assert frame["beef_product_activity_residual_bq_m2"].abs().max() < 1.0e-12
    assert frame["animal_product_activity_residual_bq_m2"].abs().max() < 1.0e-12


def test_beef_mode_off_has_no_product_and_no_meat_dose():
    config = _full_dose_case()
    config["foodchain"]["animal_products"]["beef"]["mode"] = "off"
    frame = run_short_case(config)
    final = frame.iloc[-1]
    assert final["beef_produced_hto_bq_m2"] == 0.0
    assert final["beef_produced_obt_bq_m2"] == 0.0
    assert final["beef_product_mass_kg_m2"] == 0.0
    assert final["beef_product_hto_bq_m2"] == 0.0
    assert final["beef_product_obt_bq_m2"] == 0.0
    assert final["meat_dose_sv"] == 0.0


def test_consumption_stops_when_production_and_inventory_are_unavailable():
    config = _full_dose_case()
    config["foodchain"]["animal_products"]["beef"]["turnover_rate_d-1"] = 0.0
    frame = run_short_case(config)
    assert frame["beef_consumed_hto_bq_m2"].iloc[-1] == 0.0
    assert frame["beef_consumed_obt_bq_m2"].iloc[-1] == 0.0
    assert frame["meat_dose_sv"].iloc[-1] == 0.0


def test_product_limited_meat_dose_is_below_unbounded_body_surrogate():
    config = _full_dose_case()
    frame = run_short_case(config)
    conservative = frame["meat_dose_sv"].iloc[-1]
    age = config["dose"]["age_groups"][config["dose"]["active_age_group"]]
    edible_mass_kg_m2 = (
        config["foodchain"]["animal_products"]["beef"][
            "edible_meat_mass_kg_per_head"
        ]
        / config["foodchain"]["animal_support_area_m2"]
    )
    day_fraction = config["time_step_seconds"] / 86400.0
    unbounded_surrogate = (
        (
            frame["animal_body_hto_bq_m2"] / edible_mass_kg_m2
            * age["beef_kg_day"]
            * day_fraction
            * age["hto_dose_coefficient_sv_bq"]
        )
        + (
            frame["animal_body_obt_bq_m2"] / edible_mass_kg_m2
            * age["beef_kg_day"]
            * day_fraction
            * age["obt_ingestion_dose_coefficient_sv_bq"]
        )
    ).sum()
    assert conservative > 0.0
    assert conservative < unbounded_surrogate
