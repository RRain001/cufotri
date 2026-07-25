#!/usr/bin/env python3
"""Independent reference for a bounded Gaussian-to-dose HTO pathway case.

This module intentionally does not import any implementation from
``cteas_ufotri``. It parses the validation manifest independently and applies
the equations documented beside this file.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[3]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rural_sigma(distance_m: float, stability_class: str) -> tuple[float, float]:
    coefficients = {
        "A": (0.22, 0.20, 0.0),
        "B": (0.16, 0.12, 0.0),
        "C": (0.11, 0.08, 0.0002),
        "D": (0.08, 0.06, 0.0015),
        "E": (0.06, 0.03, 0.0003),
        "F": (0.04, 0.016, 0.0003),
    }
    ay, az, bz = coefficients[stability_class.upper()]
    return (
        ay * distance_m / math.sqrt(1.0 + 0.0001 * distance_m),
        az * distance_m / math.sqrt(1.0 + bz * distance_m),
    )


def competing_depletion(
    source_bq_s: float,
    travel_time_s: float,
    dry_rate_s: float,
    wet_rate_s: float,
) -> tuple[float, float, float]:
    total_rate = dry_rate_s + wet_rate_s
    if source_bq_s <= 0.0 or total_rate == 0.0:
        return max(source_bq_s, 0.0), 0.0, 0.0
    remaining = source_bq_s * math.exp(-total_rate * travel_time_s)
    total_loss = source_bq_s - remaining
    return (
        remaining,
        total_loss * dry_rate_s / total_rate,
        total_loss * wet_rate_s / total_rate,
    )


def gaussian_ground_centerline(
    source_bq_s: float,
    downwind_m: float,
    wind_m_s: float,
    effective_height_m: float,
    stability_class: str,
) -> float:
    if source_bq_s <= 0.0:
        return 0.0
    sigma_y, sigma_z = rural_sigma(downwind_m, stability_class)
    vertical = 2.0 * math.exp(
        -0.5 * (effective_height_m / sigma_z) ** 2
    )
    return (
        source_bq_s
        * vertical
        / (2.0 * math.pi * wind_m_s * sigma_y * sigma_z)
    )


def simple_dose_increment(
    dt_s: float,
    air_hto_bq_m3: float,
    breathing_rate_m3_day: float,
    hto_coefficient_sv_bq: float,
    skin_to_inhalation_factor: float,
    *,
    food_hto_bq_kg: float = 0.0,
    food_obt_bq_kg: float = 0.0,
    food_intake_kg_day: float = 0.0,
    obt_coefficient_sv_bq: float = 0.0,
) -> dict[str, float]:
    day_fraction = dt_s / 86400.0
    inhaled_bq = air_hto_bq_m3 * breathing_rate_m3_day * day_fraction
    inhalation = inhaled_bq * hto_coefficient_sv_bq
    skin = inhalation * skin_to_inhalation_factor
    ingested_hto_bq = food_hto_bq_kg * food_intake_kg_day * day_fraction
    ingested_obt_bq = food_obt_bq_kg * food_intake_kg_day * day_fraction
    ingestion = (
        ingested_hto_bq * hto_coefficient_sv_bq
        + ingested_obt_bq * obt_coefficient_sv_bq
    )
    return {
        "inhalation_dose_sv": inhalation,
        "skin_absorption_dose_sv": skin,
        "ingestion_dose_sv": ingestion,
        "total_effective_dose_sv": inhalation + skin + ingestion,
    }


def run_reference(case_path: Path) -> pd.DataFrame:
    case = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    overrides = case["model"]["overrides"]
    source = overrides["source"]
    atmosphere = overrides["atmosphere"]
    depletion = atmosphere["depletion"]
    site = overrides["site"]
    deposition = overrides["deposition"]
    soil = overrides["soil"]
    plant = overrides["plant"]
    physics = overrides["physics"]
    dose = overrides["dose"]
    adult = dose["age_groups"]["adult"]
    forcing = overrides["synthetic_forcing"]

    dt = float(overrides["time_step_seconds"])
    steps = int(float(overrides["duration_hours"]) * 3600.0 / dt)
    release_seconds = float(source["release_duration_hours"]) * 3600.0
    wind = float(forcing["mean_wind_m_s"])
    height = float(source["stack_height_m"]) + float(
        atmosphere["fixed_plume_rise_m"]
    )
    reference_height = float(atmosphere["wind_reference_height_m"])
    plume_wind = wind * (
        max(height, reference_height) / reference_height
    ) ** float(atmosphere["rural_wind_profile_exponent"])
    downwind = float(site["receptor_downwind_m"])
    travel_time = downwind / plume_wind
    dry_rate = float(atmosphere["deposition_velocity_m_s"]) / float(
        depletion["mixing_height_m"]
    )
    wet_rate = float(depletion["constant_scavenging_coefficient_s"])
    ecological_area = float(deposition["ecological_reference_area_m2"])
    decay = float(physics["tritium_decay_constant_s"])
    leaf_velocity = float(plant["direct_leaf_velocity_m_s"])
    formation_rate = float(plant["obt_formation_rate_s"])
    turnover_rate = float(plant["obt_turnover_rate_s"])

    soil_hto = 0.0
    tfwt = 0.0
    obt = 0.0
    cumulative_dry = 0.0
    cumulative_wet = 0.0
    dose_totals = {
        "inhalation_dose_sv": 0.0,
        "skin_absorption_dose_sv": 0.0,
        "total_effective_dose_sv": 0.0,
    }
    cumulative_input_bq_m2 = 0.0
    cumulative_decay_bq_m2 = 0.0
    rows: list[dict[str, float | str]] = []
    start = datetime.fromisoformat(
        str(overrides["start"]).replace("Z", "+00:00")
    )

    for index in range(steps):
        elapsed = index * dt
        stack_release = (
            float(source["emission_rate_bq_s"])
            if elapsed < release_seconds
            else 0.0
        )
        remaining, dry_loss, wet_loss = competing_depletion(
            stack_release,
            travel_time,
            dry_rate,
            wet_rate,
        )
        air = gaussian_ground_centerline(
            remaining,
            downwind,
            plume_wind,
            height,
            atmosphere["stability_class"],
        )
        dry_flux = dry_loss / ecological_area
        wet_flux = wet_loss / ecological_area
        soil_decay = decay * soil_hto
        tfwt_decay = decay * tfwt
        obt_decay = decay * obt
        leaf_uptake = leaf_velocity * air
        formation = formation_rate * tfwt
        turnover = turnover_rate * obt

        soil_hto += dt * (dry_flux + wet_flux - soil_decay)
        tfwt += dt * (
            leaf_uptake + turnover - formation - tfwt_decay
        )
        obt += dt * (formation - turnover - obt_decay)
        cumulative_dry += dry_loss * dt
        cumulative_wet += wet_loss * dt
        cumulative_input_bq_m2 += dt * (
            dry_flux + wet_flux + leaf_uptake
        )
        cumulative_decay_bq_m2 += dt * (
            soil_decay + tfwt_decay + obt_decay
        )

        dose_increment = simple_dose_increment(
            dt,
            air,
            float(adult["breathing_rate_m3_day"]),
            float(adult["hto_dose_coefficient_sv_bq"]),
            float(dose["skin_to_inhalation_factor"]),
        )
        for name in dose_totals:
            dose_totals[name] += dose_increment[name]
        residual = (
            cumulative_input_bq_m2
            - soil_hto
            - tfwt
            - obt
            - cumulative_decay_bq_m2
        )
        rows.append(
            {
                "time": (
                    start + timedelta(seconds=(index + 1) * dt)
                ).astimezone(timezone.utc).isoformat(),
                "air_hto_concentration": air,
                "dry_depletion_bq_s": dry_loss,
                "wet_depletion_bq_s": wet_loss,
                "cumulative_dry_deposition_bq": cumulative_dry,
                "cumulative_wet_deposition_bq": cumulative_wet,
                "soil_hto_inventory": soil_hto,
                "plant_tfwt_inventory": tfwt,
                "plant_obt_inventory": obt,
                "inhalation_dose_sv": dose_totals["inhalation_dose_sv"],
                "total_effective_dose_sv": dose_totals[
                    "total_effective_dose_sv"
                ],
                "activity_residual_bq_m2": residual,
            }
        )
    return pd.DataFrame(rows)


def write_outputs(case_path: Path, output_path: Path, provenance_path: Path) -> None:
    frame = run_reference(case_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    git_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    provenance = {
        "reference_model": "independent_pathway_reference",
        "reference_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_head_at_execution": git_head,
        "case": str(case_path.relative_to(ROOT)),
        "case_sha256": sha256(case_path),
        "implementation": str(Path(__file__).relative_to(ROOT)),
        "implementation_sha256": sha256(Path(__file__)),
        "output": str(output_path.relative_to(ROOT)),
        "output_sha256": sha256(output_path),
        "formal_model_imported": False,
        "notes": (
            "Independent equations and explicit Euler boxes; no cteas_ufotri "
            "module imported."
        ),
    }
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    arguments = parser.parse_args()
    write_outputs(
        arguments.case.resolve(),
        arguments.output.resolve(),
        arguments.provenance.resolve(),
    )
    print("INDEPENDENT_REFERENCE_GENERATION_STATUS = PASS")


if __name__ == "__main__":
    main()
