from __future__ import annotations

from copy import deepcopy

from ..case import run_short_case


WET_A_VALUES = (1.0e-5, 2.0e-5, 5.0e-5, 1.0e-4)
WET_B_VALUES = (0.6, 0.8, 1.0)


def wet_parameter_sensitivity(base_config: dict) -> list[dict[str, float]]:
    """Run the declared 4 x 3 wet-scavenging uncertainty grid."""

    records: list[dict[str, float]] = []
    for a_value in WET_A_VALUES:
        for b_value in WET_B_VALUES:
            config = deepcopy(base_config)
            config["duration_hours"] = 48.0
            config["time_step_seconds"] = 3600
            config["source"]["release_duration_hours"] = 48.0
            config["synthetic_forcing"].update(
                rain_start_hour=0.0,
                rain_end_hour=48.0,
                rain_rate_m_s=1.0e-6,
            )
            depletion = config["atmosphere"]["depletion"]
            depletion["wet_scavenging_mode"] = "precipitation_power_law"
            depletion["wet_scavenging_parameter_set"] = "sensitivity_grid"
            depletion["power_law_a_s"] = a_value
            depletion["power_law_b"] = b_value
            config["crops"]["active_crop"] = "leafy_vegetable"
            config["crops"]["lai_mode"] = "smooth_seasonal"
            config["crops"]["edible_compartments_enabled"] = True
            config["plant"]["leaf_exchange_mode"] = "off"
            config["dose"]["enabled"] = True
            frame = run_short_case(config)
            final = frame.iloc[-1]
            records.append(
                {
                    "a": a_value,
                    "b": b_value,
                    "wet_plume_loss_bq": float(final["plume_wet_loss_bq"]),
                    "wet_surface_input_bq": float(
                        final["surface_wet_input_bq"]
                    ),
                    "soil_hto_bq_m2": float(final["soil_hto_inventory"]),
                    "plant_tfwt_bq_m2": float(final["plant_tfwt_inventory"]),
                    "plant_obt_bq_m2": float(final["plant_obt_inventory"]),
                    "food_tfwt_bq_kg_fresh": float(
                        final["leafy_tfwt_bq_kg_fresh"]
                    ),
                    "food_obt_bq_kg_fresh": float(
                        final["leafy_obt_bq_kg_fresh"]
                    ),
                    "plant_ingestion_dose_sv": float(
                        final["plant_ingestion_dose_sv"]
                    ),
                }
            )
    return records
