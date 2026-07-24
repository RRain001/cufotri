from __future__ import annotations

from cteas_ufotri.analysis.wet_sensitivity import wet_parameter_sensitivity
from cteas_ufotri.config import load_configuration


def test_declared_wet_parameter_grid_reaches_food_and_dose():
    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/test_case.yaml",
    )
    records = wet_parameter_sensitivity(config)
    assert len(records) == 12
    for record in records:
        assert record["wet_plume_loss_bq"] == record["wet_surface_input_bq"]
        assert min(
            record["soil_hto_bq_m2"],
            record["plant_tfwt_bq_m2"],
            record["plant_obt_bq_m2"],
            record["food_tfwt_bq_kg_fresh"],
            record["food_obt_bq_kg_fresh"],
            record["plant_ingestion_dose_sv"],
        ) > 0.0
    for b_value in (0.6, 0.8, 1.0):
        subset = sorted(
            (record for record in records if record["b"] == b_value),
            key=lambda record: record["a"],
        )
        wet_losses = [record["wet_plume_loss_bq"] for record in subset]
        assert wet_losses == sorted(wet_losses)
        assert len(set(wet_losses)) == len(wet_losses)
