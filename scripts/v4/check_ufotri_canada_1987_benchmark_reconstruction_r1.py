#!/usr/bin/env python3
"""Machine gate for the UFOTRI Canada 1987 benchmark reconstruction R1.

This stage reconstructs only what is recoverable from the repository's KfK 4605
manual transcription. It deliberately does not invent the missing raw field data,
hourly meteorology, or original-program numerics needed for a full replay.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
STAGE = "UFOTRI_CANADA_1987_BENCHMARK_RECONSTRUCTION_R1"

RELEASE_RATE_BQ_S = 1.9e9
RELEASE_DURATION_S = 30.0 * 60.0
RELEASE_ACTIVITY_BQ = RELEASE_RATE_BQ_S * RELEASE_DURATION_S
RELEASE_HEIGHT_M = 1.0
HT_DEPOSITION_VELOCITY_CM_S = 0.055
HT_DEPOSITION_VELOCITY_M_S = HT_DEPOSITION_VELOCITY_CM_S * 1.0e-2
HTO_DEPOSITION_VELOCITY_CM_S = 0.5
HTO_DEPOSITION_VELOCITY_M_S = HTO_DEPOSITION_VELOCITY_CM_S * 1.0e-2
MET_INSTRUMENT_HEIGHT_M = 2.75
INITIAL_SOIL_WATER_FRACTION = 0.20
PLANT_INORGANIC_WATER_G = 200.0
PLANT_ORGANIC_MATTER_G = 100.0
LEAF_AREA_INDEX_M2_M2 = 3.0
DAY_LEAF_DIFFUSION_RESISTANCE_S_CM = 4.0
NIGHT_LEAF_DIFFUSION_RESISTANCE_S_CM = 60.0
DAY_LEAF_DIFFUSION_RESISTANCE_S_M = DAY_LEAF_DIFFUSION_RESISTANCE_S_CM * 100.0
NIGHT_LEAF_DIFFUSION_RESISTANCE_S_M = NIGHT_LEAF_DIFFUSION_RESISTANCE_S_CM * 100.0


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _manual_anchor_gates(manual: str) -> dict[str, bool]:
    return {
        "canada_application_present": "# 5.2 The Canada-Experiment 1987" in manual,
        "chalk_river_site_present": "Chalk River Nuclear Laboratories" in manual,
        "reference_44_present": (
            "The Canadian HT Dispersion Experiment at Chalk River - June 1987: Summary Report"
            in manual
            and "Canadian Fusion Fuels Technology Project (1988)" in manual
        ),
        "release_rate_present": "1.9 \\times 10^{9}" in manual and "release rate" in manual,
        "half_hour_release_present": "duration was half an hour" in manual,
        "one_metre_release_height_present": "release height was 1 m above the ground" in manual,
        "stability_b_present": "stability class B" in manual,
        "ht_deposition_velocity_present": "0.055 \\, cm \\, s^{-1}" in manual,
        "hto_deposition_velocity_present": "0.5 cm s $^{-1}$" in manual,
        "met_height_present": "height of 2.75 m above the surface" in manual,
        "soil_water_start_present": "starting point 20%" in manual,
        "plant_water_present": "anorganic plant water content</td><td>200 g" in manual,
        "plant_organic_present": "organic plant matter</td><td>100 g" in manual,
        "lai_present": "leaf area index</td><td> $3" in manual,
        "day_resistance_present": "diffusion resistance during the day for a single leaf" in manual,
        "night_resistance_present": "diffusion resistance during the night for a single leaf" in manual,
        "hourly_met_window_present": (
            "averaged over one hour" in manual and "from June 9 to June 26" in manual
        ),
        "precip_event_total_only_present": (
            "amount of precipitation was only available as the sum of a single rain event of several hours"
            in manual
        ),
        "qualitative_intent_present": (
            "intention of the comparison was to proof, whether the model predicts qualitatively the time dependencies"
            in manual
        ),
        "precision_warning_present": (
            "a more precise reproduction of the measurement values would rather be a result by chance"
            in manual
        ),
    }


def _observable_contract(manual: str) -> list[dict[str, Any]]:
    return [
        {
            "figure": 21,
            "quantity": "HT_AIR_CONCENTRATION_DURING_PLUME_PASSAGE",
            "space": "PLUME_CENTERLINE_DISTANCE_SERIES",
            "manual_caption_present": "Figure 21. HT air concentrations during plume passage" in manual,
        },
        {
            "figure": 22,
            "quantity": "HT_SOIL_CONCENTRATION_AFTER_PLUME_PASSAGE",
            "space": "PLUME_CENTERLINE_DISTANCE_SERIES",
            "manual_caption_present": "Figure 22. HT soil concentrations after plume passage" in manual,
        },
        {
            "figure": 23,
            "quantity": "HTO_SOIL_CONCENTRATION_TIME_SERIES",
            "distance_m": 50,
            "manual_caption_present": "Figure 23. Time dependent HTO soil concentration in 50 m distance" in manual,
        },
        {
            "figure": 24,
            "quantity": "HTO_SOIL_CONCENTRATION_TIME_SERIES",
            "distance_m": 180,
            "manual_caption_present": "Figure 24. Time dependent HTO soil concentration in 180 m distance" in manual,
        },
        {
            "figure": 25,
            "quantity": "HTO_AIR_CONCENTRATION_TIME_SERIES",
            "distance_m": 50,
            "measurement_height_note": "FIRST_30_HOURS_INCLUDE_0_4_TO_1_M_MEASUREMENTS",
            "manual_caption_present": "Figure 25. Time dependent HTO air concentrations in 50 m distance" in manual,
        },
        {
            "figure": 26,
            "quantity": "HTO_AIR_CONCENTRATION_TIME_SERIES",
            "distance_m": 400,
            "measurement_height_m": 1.0,
            "manual_caption_present": "Figure 26. Time dependent HTO air concentrations in 400 m distance" in manual,
        },
        {
            "figure": 27,
            "quantity": "HTO_VEGETATION_WATER_CONCENTRATION_TIME_SERIES",
            "distance_m": 40,
            "manual_caption_present": "Figure 27. Time dependent HTO concentrations in vegetation water in $40\\mathrm{m}$ distance" in manual,
        },
        {
            "figure": 28,
            "quantity": "HTO_VEGETATION_WATER_CONCENTRATION_TIME_SERIES",
            "distance_m": None,
            "distance_ambiguity_m": [175, 180],
            "manual_text_175_m_present": "Fig. 28 for 175 m" in manual,
            "manual_caption_180_m_present": "Figure 28. Time dependent HTO concentrations in vegetation water in 180 m distance" in manual,
        },
    ]


def _unresolved_blockers() -> list[dict[str, Any]]:
    return [
        {
            "id": "CAN1987_REFERENCE_44_RAW_REPORT_AND_DATA",
            "reason": "Reference /44 is cited by KfK 4605, but the underlying Ogram summary report and raw data set are not present as benchmark input data in this repository.",
            "required_for_full_numeric_replay": True,
        },
        {
            "id": "CAN1987_RAW_HOURLY_MET_SERIES",
            "reason": "KfK 4605 states that hourly wind direction, wind speed, temperature, net solar radiation and relative humidity existed for nearly every hour from June 9 to June 26, but the numerical time series are not tabulated in the manual transcription.",
            "required_for_full_numeric_replay": True,
        },
        {
            "id": "CAN1987_RELEASE_CLOCK_ALIGNMENT",
            "reason": "The manual gives a half-hour release but does not provide the exact release timestamp needed to align the release with the missing hourly meteorological series.",
            "required_for_full_numeric_replay": True,
        },
        {
            "id": "CAN1987_PRECIPITATION_EVENT_TIMING",
            "reason": "Only the total precipitation of a several-hour rain event is described as available; an hourly precipitation allocation is not recoverable from the manual section.",
            "required_for_full_numeric_replay": True,
        },
        {
            "id": "CAN1987_RAW_MEASURED_AND_CALCULATED_SERIES",
            "reason": "Figures 21-28 show measured and calculated curves, but the repository transcription does not preserve authoritative raw point arrays or an unambiguous measured-vs-calculated series mapping.",
            "required_for_full_numeric_replay": True,
        },
        {
            "id": "CAN1987_SIGMA_PARAMETER_NUMERIC_PROVENANCE",
            "reason": "The Canada section names an S.C.K./C.E.N. Mol dispersion-parameter set but does not enumerate a Canada-specific numerical table; values from another benchmark section must not be silently substituted.",
            "required_for_full_numeric_replay": True,
        },
        {
            "id": "CAN1987_COMPLETE_EQ44_REEMISSION_RATE_RECOVERY",
            "reason": "The exact historical UFOTRI Eq. (44) engineering re-emission rate remains source-limited from Phase F and must not be promoted from provisional behaviour.",
            "required_for_full_numeric_replay": True,
        },
        {
            "id": "CAN1987_PRIMARY_ATMOS_NUMERICAL_EQUIVALENCE",
            "reason": "Original MUSEMET/UFOTRI executable numerical equivalence and the real CTEAS-Atmos HT binding remain unavailable/deferred.",
            "required_for_full_numeric_replay": True,
        },
    ]


def build_result() -> dict[str, Any]:
    manual = _text("ufotri_manual.md")
    roadmap = _text("docs/v4/roadmap/UFOTRI_REPLICATION_MASTER_PLAN.md")

    anchors = _manual_anchor_gates(manual)
    observables = _observable_contract(manual)
    blockers = _unresolved_blockers()

    static_inputs = {
        "release": {
            "chemical_form": "HT",
            "rate_bq_s": RELEASE_RATE_BQ_S,
            "duration_s": RELEASE_DURATION_S,
            "integrated_activity_bq": RELEASE_ACTIVITY_BQ,
            "height_m": RELEASE_HEIGHT_M,
        },
        "dispersion": {
            "pasquill_gifford_class": "B",
            "met_instrument_height_m": MET_INSTRUMENT_HEIGHT_M,
            "roughness_description": "SMOOTH_TERRAIN_ROUGHNESS_LENGTH_0_1_TO_1_M",
        },
        "deposition": {
            "ht_cm_s": HT_DEPOSITION_VELOCITY_CM_S,
            "ht_m_s": HT_DEPOSITION_VELOCITY_M_S,
            "reemitted_hto_cm_s": HTO_DEPOSITION_VELOCITY_CM_S,
            "reemitted_hto_m_s": HTO_DEPOSITION_VELOCITY_M_S,
        },
        "soil_plant": {
            "initial_soil_water_fraction": INITIAL_SOIL_WATER_FRACTION,
            "plant_inorganic_water_g": PLANT_INORGANIC_WATER_G,
            "plant_organic_matter_g": PLANT_ORGANIC_MATTER_G,
            "leaf_area_index_m2_m2": LEAF_AREA_INDEX_M2_M2,
            "day_leaf_diffusion_resistance_s_cm": DAY_LEAF_DIFFUSION_RESISTANCE_S_CM,
            "night_leaf_diffusion_resistance_s_cm": NIGHT_LEAF_DIFFUSION_RESISTANCE_S_CM,
            "day_leaf_diffusion_resistance_s_m": DAY_LEAF_DIFFUSION_RESISTANCE_S_M,
            "night_leaf_diffusion_resistance_s_m": NIGHT_LEAF_DIFFUSION_RESISTANCE_S_M,
        },
        "reemission": {
            "soil_day": "CALCULATED_EACH_HOUR_EXCEPT_RAIN",
            "soil_night_start_percent": 1.0,
            "soil_rain_start_percent": 3.0,
            "night_and_rain_rates_decrease_with_time": True,
        },
        "meteorology": {
            "nominal_window": "1987-06-09_TO_1987-06-26",
            "hourly_variables_described": [
                "wind_direction",
                "wind_speed",
                "temperature",
                "net_solar_radiation",
                "relative_humidity",
            ],
            "raw_hourly_values_recovered": False,
            "precipitation_hourly_values_recovered": False,
        },
    }

    figure_gates = {
        "all_eight_manual_captions_recovered": all(
            bool(item.get("manual_caption_present")) for item in observables
        ),
        "figure_28_distance_ambiguity_preserved": (
            observables[-1]["distance_m"] is None
            and observables[-1]["distance_ambiguity_m"] == [175, 180]
            and bool(observables[-1]["manual_text_175_m_present"])
            and bool(observables[-1]["manual_caption_180_m_present"])
        ),
    }

    conversion_gates = {
        "release_activity_exact": math.isclose(RELEASE_ACTIVITY_BQ, 3.42e12, rel_tol=0.0, abs_tol=1.0e-6),
        "ht_deposition_unit_conversion_exact": math.isclose(
            HT_DEPOSITION_VELOCITY_M_S, 5.5e-4, rel_tol=0.0, abs_tol=1.0e-15
        ),
        "hto_deposition_unit_conversion_exact": math.isclose(
            HTO_DEPOSITION_VELOCITY_M_S, 5.0e-3, rel_tol=0.0, abs_tol=1.0e-15
        ),
        "day_resistance_unit_conversion_exact": DAY_LEAF_DIFFUSION_RESISTANCE_S_M == 400.0,
        "night_resistance_unit_conversion_exact": NIGHT_LEAF_DIFFUSION_RESISTANCE_S_M == 6000.0,
    }

    repository_mapping = {
        "ht_branch_contract_present": (ROOT / "src/cteas_ufotri/coupling/ht_v4.py").is_file(),
        "ht_to_hto_soil_adapter_present": (ROOT / "src/cteas_ufotri/coupling/ht_to_hto_soil_v4.py").is_file(),
        "reemission_area_source_adapter_present": (ROOT / "src/cteas_ufotri/coupling/reemission_area_source_v4.py").is_file(),
        "g1_authorized_by_roadmap": STAGE in roadmap,
    }

    acceptance_policy = {
        "r1_acceptance": "RECOVERABLE_CONTRACT_RECONSTRUCTED_WITH_EXPLICIT_BLOCKERS",
        "manual_declared_target": "QUALITATIVE_TIME_DEPENDENCE_OF_AIR_SOIL_AND_VEGETATION_CONCENTRATIONS_OVER_SEVERAL_DAYS",
        "authoritative_pointwise_rmse_allowed": False,
        "chart_transcription_as_ground_truth_allowed": False,
        "silent_fill_of_missing_inputs_allowed": False,
        "empirical_reproduction_executed": False,
        "empirical_validation_complete": False,
        "full_numeric_replay_ready": False,
    }

    contract_gates = {
        "manual_anchors": all(anchors.values()),
        "figures": all(figure_gates.values()),
        "unit_conversions": all(conversion_gates.values()),
        "repository_mapping": all(repository_mapping.values()),
        "missing_inputs_explicit": len(blockers) >= 8 and all(
            bool(item["reason"]) and item["required_for_full_numeric_replay"] for item in blockers
        ),
        "fail_closed_acceptance": (
            acceptance_policy["full_numeric_replay_ready"] is False
            and acceptance_policy["authoritative_pointwise_rmse_allowed"] is False
            and acceptance_policy["chart_transcription_as_ground_truth_allowed"] is False
            and acceptance_policy["silent_fill_of_missing_inputs_allowed"] is False
        ),
    }

    status = (
        "PASS_SOURCE_LIMITED_CANADA_1987_BENCHMARK_RECONSTRUCTION"
        if all(contract_gates.values())
        else "FAIL_CANADA_1987_BENCHMARK_RECONSTRUCTION"
    )

    return {
        "stage": STAGE,
        "status": status,
        "manual_anchor_gates": anchors,
        "recovered_static_inputs": static_inputs,
        "observable_contract": observables,
        "figure_gates": figure_gates,
        "conversion_gates": conversion_gates,
        "repository_mapping": repository_mapping,
        "unresolved_blockers": blockers,
        "acceptance_policy": acceptance_policy,
        "contract_gates": contract_gates,
        "decision": {
            "benchmark_contract_reconstructed": status.startswith("PASS_"),
            "production_source_changed": False,
            "default_parameters_changed": False,
            "roadmap_changed_in_stage_pr": False,
            "full_numeric_replay_executed": False,
            "empirical_validation_complete": False,
            "reference_44_values_invented": False,
            "figure_28_distance_silently_resolved": False,
        },
        "non_claims": {
            "physical_accuracy": False,
            "production_readiness": False,
            "original_ufotri_executable_equivalence": False,
            "original_musemet_equivalence": False,
            "canada_1987_empirical_reproduction": False,
        },
    }


def main() -> int:
    result = build_result()
    print(f"G1_CANADA_1987_STATUS={result['status']}")
    print("G1_CANADA_1987_RESULT_JSON=" + json.dumps(result, sort_keys=True))
    return 0 if result["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
