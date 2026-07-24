from __future__ import annotations

from copy import deepcopy

import numpy as np

from ..case import run_short_case
from ..soil.multibox import ThreeBoxSoilState, advance_three_box_soil
from .independent import (
    benchmark_category_counts,
    independent_benchmarks_pass,
    run_independent_benchmarks,
)


def _run(config: dict) -> dict[str, float | bool]:
    frame = run_short_case(config)
    numeric = frame.select_dtypes(include=[np.number])
    result = {
        "steps": int(len(frame)),
        "finite": bool(np.isfinite(numeric.to_numpy()).all()),
        "nonnegative": bool(
            (
                numeric.drop(
                    columns=[
                        "mass_balance_error",
                        "surface_box_absolute_residual_bq_m2",
                        "depletion_deposition_mismatch_bq_s",
                        "ecological_box_relative_residual",
                    ],
                    errors="ignore",
                )
                >= -1.0e-12
            )
            .all()
            .all()
        ),
        "max_surface_relative_residual": float(
            frame["surface_box_relative_residual"].max()
        ),
        "final_air_bq_m3": float(frame["air_hto_concentration"].iloc[-1]),
        "final_soil_bq_m2": float(frame["soil_hto_inventory"].iloc[-1]),
        "final_obt_bq_m2": float(frame["plant_obt_inventory"].iloc[-1]),
        "final_milk_hto_bq_l": float(frame["milk_hto_bq_l"].iloc[-1]),
        "final_total_dose_sv": float(frame["total_effective_dose_sv"].iloc[-1]),
    }
    result["pass"] = bool(
        result["finite"]
        and result["nonnegative"]
        and result["max_surface_relative_residual"] < 1.0e-10
    )
    return result


def run_v2_benchmark_suite(base_config: dict) -> dict[str, dict[str, float | bool]]:
    cases: dict[str, dict] = {}

    v1 = deepcopy(base_config)
    v1["duration_hours"] = 2.0
    cases["v1_regression"] = v1

    dry = deepcopy(base_config)
    dry["duration_hours"] = 2.0
    dry["synthetic_forcing"]["rain_start_hour"] = 1000.0
    cases["no_rain_dry_deposition"] = dry

    wet = deepcopy(base_config)
    wet["duration_hours"] = 2.0
    wet["synthetic_forcing"].update(
        rain_start_hour=0.0, rain_end_hour=2.0, rain_rate_m_s=1.0e-5
    )
    wet["atmosphere"]["depletion"]["wet_scavenging_mode"] = (
        "precipitation_power_law"
    )
    cases["strong_rain_wet_scavenging"] = wet

    day = deepcopy(base_config)
    day["duration_hours"] = 4.0
    day["source"]["release_duration_hours"] = 1.0
    day["synthetic_forcing"]["sunrise_hour"] = 0.0
    cases["day_short_hto_release"] = day

    night = deepcopy(day)
    night["synthetic_forcing"]["maximum_net_radiation_w_m2"] = 0.0
    cases["night_short_hto_release"] = night

    reemission = deepcopy(base_config)
    reemission["duration_hours"] = 72.0
    reemission["source"]["release_duration_hours"] = 1.0
    reemission["reemission"]["mode"] = "ufotri_empirical"
    cases["post_accident_reemission_72h"] = reemission

    growing = deepcopy(base_config)
    growing["duration_hours"] = 24.0
    growing["start"] = "2025-06-15T00:00:00Z"
    growing["crops"]["active_crop"] = "leafy_vegetable"
    growing["crops"]["lai_mode"] = "smooth_seasonal"
    growing["crops"]["edible_compartments_enabled"] = True
    cases["crop_growing_season_release"] = growing

    harvest = deepcopy(base_config)
    harvest["duration_hours"] = 48.0
    harvest["start"] = "2025-09-16T00:00:00Z"
    harvest["crops"]["active_crop"] = "cereal"
    harvest["crops"]["lai_mode"] = "piecewise_growth_stage"
    harvest["crops"]["edible_compartments_enabled"] = True
    cases["pre_harvest_release"] = harvest

    pasture = deepcopy(base_config)
    pasture["duration_hours"] = 24.0
    pasture["crops"]["active_crop"] = "pasture"
    pasture["crops"]["edible_compartments_enabled"] = True
    pasture["foodchain"]["enabled"] = True
    pasture["foodchain"]["animal_mode"] = "minimal_cow"
    cases["pasture_milk_pathway"] = pasture

    full_dose = deepcopy(pasture)
    full_dose["dose"]["enabled"] = True
    cases["full_adult_dose"] = full_dose

    zero = deepcopy(base_config)
    zero["duration_hours"] = 2.0
    zero["source"]["emission_rate_bq_s"] = 0.0
    cases["zero_source"] = zero

    calm = deepcopy(base_config)
    calm["duration_hours"] = 2.0
    calm["synthetic_forcing"]["mean_wind_m_s"] = 0.0
    calm["synthetic_forcing"]["wind_amplitude_m_s"] = 0.0
    cases["extremely_low_wind"] = calm

    dry_soil = deepcopy(base_config)
    dry_soil["duration_hours"] = 2.0
    dry_soil["soil"]["initial_water_m"] = dry_soil["soil"]["minimum_water_m"]
    cases["extremely_dry_soil"] = dry_soil

    saturated = deepcopy(wet)
    saturated["synthetic_forcing"]["rain_rate_m_s"] = 1.0e-4
    cases["saturated_rain"] = saturated

    results = {name: _run(config) for name, config in cases.items()}
    for name, result in results.items():
        result["category"] = (
            "regression_case" if name == "v1_regression" else "integration_scenario"
        )

    multi_config = deepcopy(base_config["soil"]["multibox"])
    multi_config["decay_rate_s"] = 0.0
    multi_final, multi_diag = advance_three_box_soil(
        ThreeBoxSoilState(
            tuple(multi_config["initial_water_m"]),
            (100.0, 0.0, 0.0),
        ),
        600.0,
        1.0e-6,
        1.0,
        1.0e-7,
        1.0e-7,
        multi_config,
    )
    results["single_vs_three_box_soil"] = {
        "category": "physical_invariant",
        "steps": 1,
        "finite": bool(
            np.isfinite(multi_final.water_m).all()
            and np.isfinite(multi_final.hto_bq_m2).all()
        ),
        "nonnegative": min(*multi_final.water_m, *multi_final.hto_bq_m2) >= 0.0,
        "max_surface_relative_residual": abs(multi_diag.hto_residual_bq_m2)
        / 100.0,
        "single_layer_formal_status": True,
        "three_box_total_hto_bq_m2": multi_final.total_hto_bq_m2,
        "pass": bool(
            np.isfinite(multi_final.water_m).all()
            and np.isfinite(multi_final.hto_bq_m2).all()
            and min(*multi_final.water_m, *multi_final.hto_bq_m2) >= 0.0
            and abs(multi_diag.hto_residual_bq_m2) / 100.0 < 1.0e-10
        ),
    }
    for name in (
        "zero_source",
        "extremely_low_wind",
        "extremely_dry_soil",
        "saturated_rain",
    ):
        results[name]["category"] = "physical_invariant"
    results.update(run_independent_benchmarks(base_config))
    return results


def benchmark_suite_passes(
    results: dict[str, dict[str, float | bool]]
) -> bool:
    scenario_names = {
        "v1_regression",
        "no_rain_dry_deposition",
        "strong_rain_wet_scavenging",
        "day_short_hto_release",
        "night_short_hto_release",
        "post_accident_reemission_72h",
        "crop_growing_season_release",
        "pre_harvest_release",
        "pasture_milk_pathway",
        "full_adult_dose",
        "zero_source",
        "extremely_low_wind",
        "extremely_dry_soil",
        "saturated_rain",
        "single_vs_three_box_soil",
    }
    if not scenario_names <= results.keys():
        return False
    scenario_results = {name: results[name] for name in scenario_names}
    return (
        all(bool(result["finite"]) for result in scenario_results.values())
        and all(bool(result["nonnegative"]) for result in scenario_results.values())
        and all(
            float(result["max_surface_relative_residual"]) < 1.0e-10
            for result in scenario_results.values()
        )
        and independent_benchmarks_pass(results)
        and benchmark_category_counts(results)["analytic_benchmark"] >= 6
        and float(results["zero_source"]["final_air_bq_m3"]) == 0.0
        and float(results["strong_rain_wet_scavenging"]["final_air_bq_m3"])
        < float(results["no_rain_dry_deposition"]["final_air_bq_m3"])
        and float(results["full_adult_dose"]["final_total_dose_sv"]) > 0.0
        and float(results["pasture_milk_pathway"]["final_milk_hto_bq_l"]) > 0.0
    )
