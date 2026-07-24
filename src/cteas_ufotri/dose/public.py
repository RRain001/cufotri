from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DoseIncrement:
    inhalation_dose_sv: float
    skin_absorption_dose_sv: float
    drinking_water_dose_sv: float
    plant_ingestion_dose_sv: float
    milk_dose_sv: float
    meat_dose_sv: float
    total_hto_dose_sv: float
    total_obt_dose_sv: float
    total_effective_dose_sv: float


def calculate_public_dose_step(
    dt_s: float,
    air_hto_bq_m3: float,
    concentrations: dict[str, float],
    age_parameters: dict,
    *,
    skin_to_inhalation_factor: float,
) -> DoseIncrement:
    """Calculate one receptor/time-step research-screening dose increment."""
    if dt_s <= 0:
        raise ValueError("Dose time step must be positive")
    if skin_to_inhalation_factor < 0:
        raise ValueError("Skin absorption factor must be non-negative")
    hto_dc = float(age_parameters["hto_dose_coefficient_sv_bq"])
    obt_dc = float(age_parameters["obt_ingestion_dose_coefficient_sv_bq"])
    if min(hto_dc, obt_dc) < 0:
        raise ValueError("Dose coefficients must be non-negative")
    day_fraction = dt_s / 86400.0
    inhaled_bq = (
        max(air_hto_bq_m3, 0.0)
        * float(age_parameters["breathing_rate_m3_day"])
        * day_fraction
    )
    inhalation = inhaled_bq * hto_dc
    skin = inhalation * skin_to_inhalation_factor
    water = (
        max(concentrations.get("drinking_water_hto_bq_l", 0.0), 0.0)
        * float(age_parameters["drinking_water_l_day"])
        * day_fraction
        * hto_dc
    )

    plant_hto_bq = day_fraction * sum(
        max(concentrations.get(key, 0.0), 0.0)
        * float(age_parameters[rate])
        for key, rate in (
            ("leafy_tfwt_bq_kg_fresh", "leafy_kg_day"),
            ("root_crop_tfwt_bq_kg_fresh", "root_crop_kg_day"),
            ("grain_tfwt_bq_kg_fresh", "grain_kg_day"),
        )
    )
    plant_obt_bq = day_fraction * sum(
        max(concentrations.get(key, 0.0), 0.0)
        * float(age_parameters[rate])
        for key, rate in (
            ("leafy_obt_bq_kg_fresh", "leafy_kg_day"),
            ("root_crop_obt_bq_kg_fresh", "root_crop_kg_day"),
            ("grain_obt_bq_kg_fresh", "grain_kg_day"),
        )
    )
    milk_hto_bq = (
        max(concentrations.get("milk_hto_bq_l", 0.0), 0.0)
        * float(age_parameters["milk_l_day"])
        * day_fraction
    )
    milk_obt_bq = (
        max(concentrations.get("milk_obt_bq_l", 0.0), 0.0)
        * float(age_parameters["milk_l_day"])
        * day_fraction
    )
    meat_hto_bq = (
        max(concentrations.get("beef_hto_bq_kg", 0.0), 0.0)
        * float(age_parameters["beef_kg_day"])
        * day_fraction
    )
    meat_obt_bq = (
        max(concentrations.get("beef_obt_bq_kg", 0.0), 0.0)
        * float(age_parameters["beef_kg_day"])
        * day_fraction
    )
    plant = plant_hto_bq * hto_dc + plant_obt_bq * obt_dc
    milk = milk_hto_bq * hto_dc + milk_obt_bq * obt_dc
    meat = meat_hto_bq * hto_dc + meat_obt_bq * obt_dc
    total_hto = (
        inhalation
        + skin
        + water
        + (plant_hto_bq + milk_hto_bq + meat_hto_bq) * hto_dc
    )
    total_obt = (plant_obt_bq + milk_obt_bq + meat_obt_bq) * obt_dc
    return DoseIncrement(
        inhalation,
        skin,
        water,
        plant,
        milk,
        meat,
        total_hto,
        total_obt,
        total_hto + total_obt,
    )

