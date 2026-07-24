from __future__ import annotations

from copy import deepcopy
import math

import numpy as np

from ..atmosphere.depletion import segment_exponential_depletion
from ..dose.public import calculate_public_dose_step
from ..foodchain.model import AnimalState, step_animal
from ..plant.edible import edible_concentrations
from ..plant.leaf_exchange import bidirectional_leaf_exchange
from ..reemission.fluxes import (
    calibrate_ufotri_empirical_reemission,
    ufotri_empirical_soil_reemission_bq_m2_s,
)


BENCHMARK_CATEGORIES = {
    "analytic_benchmark",
    "manual_anchor",
    "literature_comparison",
    "physical_invariant",
    "integration_scenario",
    "regression_case",
}


def _numeric_record(
    category: str,
    computed: float,
    target: float,
    tolerance: float,
    *,
    source: str,
) -> dict[str, float | str | bool]:
    absolute_error = abs(computed - target)
    scale = max(abs(target), 1.0e-30)
    relative_error = absolute_error / scale
    return {
        "category": category,
        "computed": float(computed),
        "target": float(target),
        "absolute_error": float(absolute_error),
        "relative_error": float(relative_error),
        "tolerance": float(tolerance),
        "source": source,
        "pass": bool(relative_error <= tolerance),
    }


def _leaf_box_benchmark() -> dict[str, float | str | bool]:
    air_bq_m3 = 1000.0
    initial_bq_m3 = 200.0
    water_storage_m = 4.0e-4
    duration_s = 3600.0
    dt_s = 1.0
    exchange = bidirectional_leaf_exchange(
        air_bq_m3,
        initial_bq_m3,
        298.15,
        288.15,
        3.0,
        True,
        wind_speed_m_s=2.0,
        stability_class="D",
        roughness_length_m=0.1,
        canopy_height_m=0.5,
        wind_measurement_height_m=10.0,
        leaf_characteristic_length_m=0.05,
        air_kinematic_viscosity_m2_s=1.5e-5,
        water_vapour_diffusivity_m2_s=2.5e-5,
        stomatal_resistance_day_s_m=400.0,
        stomatal_resistance_night_s_m=6000.0,
        vpd_sensitivity_per_kpa=0.5,
        isotope_fractionation_liquid_to_vapour=1.1,
        water_density_kg_m3=1000.0,
    )
    equilibrium_factor = exchange.equilibrium_air_concentration_bq_m3 / initial_bq_m3
    rate_s = exchange.conductance_m_s * equilibrium_factor / water_storage_m
    equilibrium_plant_bq_m3 = air_bq_m3 / equilibrium_factor
    target = equilibrium_plant_bq_m3 + (
        initial_bq_m3 - equilibrium_plant_bq_m3
    ) * math.exp(-rate_s * duration_s)
    inventory = initial_bq_m3 * water_storage_m
    for _ in range(round(duration_s / dt_s)):
        concentration = inventory / water_storage_m
        inventory += dt_s * exchange.conductance_m_s * (
            air_bq_m3 - equilibrium_factor * concentration
        )
    record = _numeric_record(
        "analytic_benchmark",
        inventory / water_storage_m,
        target,
        5.0e-5,
        source="independent first-order box solution with fixed leaf conductance",
    )
    record["conductance_m_s"] = exchange.conductance_m_s
    record["first_order_rate_s"] = rate_s
    return record


def _animal_box_benchmark(base_config: dict) -> dict[str, float | str | bool]:
    animal = deepcopy(base_config["foodchain"])
    animal.update(
        obt_formation_rate_s=0.0,
        obt_turnover_rate_s=0.0,
        hto_excretion_rate_s=0.0,
        obt_excretion_rate_s=0.0,
        milk_hto_transfer_rate_s=0.0,
        milk_obt_transfer_rate_s=0.0,
        decay_rate_s=0.0,
    )
    input_bq_s = 0.01
    turnover_rate_s = 0.2 / 86400.0
    duration_s = 86400.0
    dt_s = 10.0
    state = AnimalState()
    for _ in range(round(duration_s / dt_s)):
        state, _ = step_animal(
            state,
            dt_s,
            0.0,
            0.0,
            0.0,
            animal,
            slaughter_rate_s=turnover_rate_s,
            feed_hto_input_bq_m2_s=input_bq_s,
            feed_obt_input_bq_m2_s=0.0,
        )
    target = input_bq_s / turnover_rate_s * (
        1.0 - math.exp(-turnover_rate_s * duration_s)
    )
    return _numeric_record(
        "analytic_benchmark",
        state.body_hto_bq,
        target,
        2.0e-5,
        source="independent constant-input first-order animal product box",
    )


def _dose_benchmark(
    base_config: dict, duration_days: float
) -> dict[str, float | str | bool]:
    age = base_config["dose"]["age_groups"]["adult"]
    concentrations = {
        "drinking_water_hto_bq_l": 30.0,
        "leafy_tfwt_bq_kg_fresh": 40.0,
        "leafy_obt_bq_kg_fresh": 5.0,
        "root_crop_tfwt_bq_kg_fresh": 20.0,
        "root_crop_obt_bq_kg_fresh": 4.0,
        "grain_tfwt_bq_kg_fresh": 10.0,
        "grain_obt_bq_kg_fresh": 8.0,
        "milk_hto_bq_l": 12.0,
        "milk_obt_bq_l": 3.0,
        "beef_hto_bq_kg": 15.0,
        "beef_obt_bq_kg": 7.0,
    }
    air = 25.0
    hto_bq_day = (
        air * age["breathing_rate_m3_day"] * 1.5
        + concentrations["drinking_water_hto_bq_l"] * age["drinking_water_l_day"]
        + concentrations["leafy_tfwt_bq_kg_fresh"] * age["leafy_kg_day"]
        + concentrations["root_crop_tfwt_bq_kg_fresh"] * age["root_crop_kg_day"]
        + concentrations["grain_tfwt_bq_kg_fresh"] * age["grain_kg_day"]
        + concentrations["milk_hto_bq_l"] * age["milk_l_day"]
        + concentrations["beef_hto_bq_kg"] * age["beef_kg_day"]
    )
    obt_bq_day = (
        concentrations["leafy_obt_bq_kg_fresh"] * age["leafy_kg_day"]
        + concentrations["root_crop_obt_bq_kg_fresh"] * age["root_crop_kg_day"]
        + concentrations["grain_obt_bq_kg_fresh"] * age["grain_kg_day"]
        + concentrations["milk_obt_bq_l"] * age["milk_l_day"]
        + concentrations["beef_obt_bq_kg"] * age["beef_kg_day"]
    )
    target = duration_days * (
        hto_bq_day * age["hto_dose_coefficient_sv_bq"]
        + obt_bq_day * age["obt_ingestion_dose_coefficient_sv_bq"]
    )
    computed = calculate_public_dose_step(
        duration_days * 86400.0,
        air,
        concentrations,
        age,
        skin_to_inhalation_factor=0.5,
    ).total_effective_dose_sv
    return _numeric_record(
        "analytic_benchmark",
        computed,
        target,
        1.0e-14,
        source=f"independent hand arithmetic for {duration_days:g} d exposure",
    )


def run_independent_benchmarks(
    base_config: dict,
) -> dict[str, dict[str, float | str | bool]]:
    source = 1000.0
    travel_s = 1200.0
    wet_rate_s = 2.0e-4
    wet = segment_exponential_depletion(
        source,
        travel_s,
        1.0,
        0.0,
        100.0,
        12,
        dry_enabled=False,
        wet_enabled=True,
        wet_scavenging_rate_s=wet_rate_s,
    )
    dry_rate_s = 1.0e-4
    competition = segment_exponential_depletion(
        source,
        travel_s,
        1.0,
        dry_rate_s * 100.0,
        100.0,
        12,
        wet_enabled=True,
        wet_scavenging_rate_s=wet_rate_s,
    )
    total_rate_s = dry_rate_s + wet_rate_s
    total_loss = source * (1.0 - math.exp(-total_rate_s * travel_s))

    inventory = 500.0
    reemission_rate_s = 0.1 / 3600.0
    reemission_target = inventory * math.exp(-reemission_rate_s * 6.0 * 3600.0)
    reemission_computed = inventory
    reemission_dt_s = 1.0
    for _ in range(round(6.0 * 3600.0 / reemission_dt_s)):
        production_flux = ufotri_empirical_soil_reemission_bq_m2_s(
            reemission_computed,
            1.0e-7,
            0.02,
            0.0,
            0.0,
            True,
            reference_evaporation_m_s=1.0e-7,
            reference_water_m=0.02,
            radiative_reference_fraction_h=0.10,
            diffusive_fraction_h=0.0,
            zt_half_life_h=1.0e30,
        )
        reemission_computed -= reemission_dt_s * production_flux

    food = edible_concentrations(80.0, 20.0, 2.0, 0.8, 1000.0)
    reemission_config = base_config["reemission"]
    calibration = calibrate_ufotri_empirical_reemission(
        reemission_config["empirical_reference_evaporation_m_s"],
        reemission_config["empirical_reference_water_m"],
        reemission_config["empirical_radiative_reference_fraction_h"],
        reemission_config["empirical_diffusive_fraction_h"],
    )
    anchor_inventory = 100.0
    total_day_flux = ufotri_empirical_soil_reemission_bq_m2_s(
        anchor_inventory,
        reemission_config["empirical_reference_evaporation_m_s"],
        reemission_config["empirical_reference_water_m"],
        0.0,
        0.0,
        True,
        reference_evaporation_m_s=reemission_config[
            "empirical_reference_evaporation_m_s"
        ],
        reference_water_m=reemission_config["empirical_reference_water_m"],
        radiative_reference_fraction_h=reemission_config[
            "empirical_radiative_reference_fraction_h"
        ],
        diffusive_fraction_h=reemission_config["empirical_diffusive_fraction_h"],
        zt_half_life_h=reemission_config["empirical_zt_half_life_h"],
    )
    animal = base_config["foodchain"]
    hto_loss_rate_s = sum(
        animal[name]
        for name in (
            "hto_excretion_rate_s",
            "milk_hto_transfer_rate_s",
            "obt_formation_rate_s",
            "decay_rate_s",
        )
    )
    obt_loss_rate_s = sum(
        animal[name]
        for name in (
            "obt_excretion_rate_s",
            "milk_obt_transfer_rate_s",
            "obt_turnover_rate_s",
            "decay_rate_s",
        )
    )
    adult = base_config["dose"]["age_groups"]["adult"]

    return {
        "analytic_wet_exponential_removal": _numeric_record(
            "analytic_benchmark",
            wet.source_after_bq_s,
            source * math.exp(-wet_rate_s * travel_s),
            1.0e-13,
            source="Q=Q0 exp(-lambda t)",
        ),
        "analytic_dry_competition_allocation": _numeric_record(
            "analytic_benchmark",
            competition.dry_depletion_bq_s,
            total_loss * dry_rate_s / total_rate_s,
            1.0e-13,
            source="competing first-order hazards, dry allocation",
        ),
        "analytic_wet_competition_allocation": _numeric_record(
            "analytic_benchmark",
            competition.wet_depletion_bq_s,
            total_loss * wet_rate_s / total_rate_s,
            1.0e-13,
            source="competing first-order hazards, wet allocation",
        ),
        "analytic_leaf_fixed_conductance_box": _leaf_box_benchmark(),
        "analytic_reemission_decay_box": _numeric_record(
            "analytic_benchmark",
            reemission_computed,
            reemission_target,
            2.0e-5,
            source="M=M0 exp(-kt), independent one-second integration",
        ),
        "analytic_animal_product_box": _animal_box_benchmark(base_config),
        "analytic_dose_one_day": _dose_benchmark(base_config, 1.0),
        "analytic_dose_one_year": _dose_benchmark(base_config, 365.0),
        "analytic_food_fresh_water_conversion": _numeric_record(
            "analytic_benchmark",
            food.tfwt_bq_m3_water,
            80.0 / (2.0 * 0.8 / 1000.0),
            1.0e-14,
            source="hand conversion from fresh mass and water fraction",
        ),
        "analytic_food_dry_mass_conversion": _numeric_record(
            "analytic_benchmark",
            food.obt_bq_kg_dry,
            20.0 / (2.0 * 0.2),
            1.0e-14,
            source="hand conversion from fresh mass and dry fraction",
        ),
        "manual_reemission_radiative_10_percent_h": _numeric_record(
            "manual_anchor",
            calibration.radiative_rate_s * 3600.0,
            0.10,
            1.0e-12,
            source="UFOTRI manual Eq. (44-1) calibration text",
        ),
        "manual_reemission_diffusive_1_percent_h": _numeric_record(
            "manual_anchor",
            calibration.diffusive_rate_s * 3600.0,
            0.01,
            1.0e-12,
            source="UFOTRI manual Eq. (44-2) calibration text",
        ),
        "manual_reemission_combined_day_rate": _numeric_record(
            "manual_anchor",
            total_day_flux / anchor_inventory * 3600.0,
            0.11,
            1.0e-12,
            source="UFOTRI manual radiative plus diffusive reference condition",
        ),
        "manual_animal_water_half_time_3_5_d": _numeric_record(
            "manual_anchor",
            math.log(2.0) / hto_loss_rate_s / 86400.0,
            3.5,
            0.05,
            source="UFOTRI manual dairy-cow water half-time",
        ),
        "manual_animal_obt_half_time_about_40_d": _numeric_record(
            "manual_anchor",
            math.log(2.0) / obt_loss_rate_s / 86400.0,
            40.0,
            0.15,
            source="UFOTRI manual cow organic-compartment half-time",
        ),
        "literature_hpa_adult_hto_coefficient": _numeric_record(
            "literature_comparison",
            adult["hto_dose_coefficient_sv_bq"],
            1.8e-11,
            1.0e-14,
            source="HPA-CRCE-004 Table 1",
        ),
        "literature_hpa_adult_obt_coefficient": _numeric_record(
            "literature_comparison",
            adult["obt_ingestion_dose_coefficient_sv_bq"],
            4.2e-11,
            1.0e-14,
            source="HPA-CRCE-004 Table 1",
        ),
    }


def benchmark_category_counts(
    results: dict[str, dict[str, float | str | bool]],
) -> dict[str, int]:
    return {
        category: sum(
            result.get("category") == category for result in results.values()
        )
        for category in sorted(BENCHMARK_CATEGORIES)
    }


def independent_benchmarks_pass(
    results: dict[str, dict[str, float | str | bool]],
) -> bool:
    counts = benchmark_category_counts(results)
    return (
        counts["analytic_benchmark"] >= 6
        and counts["manual_anchor"] + counts["literature_comparison"] >= 4
        and all(
            result.get("category") in BENCHMARK_CATEGORIES
            for result in results.values()
        )
        and all(bool(result.get("pass", False)) for result in results.values())
    )
