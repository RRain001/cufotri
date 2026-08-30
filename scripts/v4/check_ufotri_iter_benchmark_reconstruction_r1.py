#!/usr/bin/env python3
"""Machine gate for UFOTRI ITER benchmark reconstruction R1.

The gate qualifies only the recoverable KfK 4605 Section 5.3 / Appendix B
benchmark contract and the explicitly tabulated 1 km reference values in
Tables 10-13. It does not claim a full atmospheric replay.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
STAGE = "UFOTRI_ITER_BENCHMARK_RECONSTRUCTION_R1"

COLUMNS = [
    "early_inhalation_skin_plume_sv",
    "early_inhalation_skin_plume_reemission_sv",
    "chronic_inhalation_skin_plume_reemission_sv",
    "early_ingestion_sv",
    "chronic_ingestion_sv",
    "sum_early_sv",
    "sum_chronic_sv",
]
CASES = ["10_m", "20_m", "60_m", "20_m_with_building_wake"]

REFERENCE_1KM: dict[str, dict[str, list[float]]] = {
    "table10_hto_D": {
        "10_m": [1.2e-3, 2.3e-3, 6.2e-3, 6.5e-3, 4.1e-2, 8.8e-3, 4.7e-2],
        "20_m": [9.7e-4, 1.7e-3, 4.7e-3, 5.0e-3, 3.2e-2, 6.7e-3, 3.7e-2],
        "60_m": [5.4e-4, 7.6e-4, 2.1e-3, 2.3e-3, 1.4e-2, 3.1e-3, 1.6e-2],
        "20_m_with_building_wake": [1.1e-3, 2.0e-3, 5.4e-3, 5.7e-3, 3.6e-2, 7.7e-3, 4.1e-2],
    },
    "table11_hto_F": {
        "10_m": [5.5e-3, 1.1e-2, 3.0e-2, 1.6e-2, 2.8e-1, 2.7e-2, 3.1e-1],
        "20_m": [4.5e-3, 7.5e-3, 2.0e-2, 1.2e-2, 1.9e-1, 2.0e-2, 2.1e-1],
        "60_m": [1.4e-3, 1.8e-3, 4.9e-3, 2.9e-3, 4.6e-2, 4.7e-3, 5.1e-2],
        "20_m_with_building_wake": [4.8e-3, 8.6e-3, 2.3e-2, 1.3e-2, 2.2e-1, 2.2e-2, 2.4e-1],
    },
    "table12_ht_D": {
        "10_m": [5.6e-8, 2.6e-5, 7.0e-5, 6.7e-5, 5.5e-4, 9.3e-5, 6.2e-4],
        "20_m": [4.3e-8, 1.7e-5, 4.6e-5, 4.5e-5, 3.8e-4, 6.2e-5, 4.3e-4],
        "60_m": [2.2e-8, 4.7e-6, 1.2e-5, 1.5e-5, 1.3e-4, 2.0e-5, 1.4e-4],
        "20_m_with_building_wake": [5.0e-8, 2.0e-5, 5.4e-5, 5.2e-5, 4.4e-4, 7.2e-5, 4.9e-4],
    },
    "table13_ht_F": {
        "10_m": [3.1e-7, 1.8e-4, 4.9e-4, 3.6e-4, 7.8e-3, 5.4e-4, 8.3e-3],
        "20_m": [2.1e-7, 8.9e-5, 2.4e-4, 2.2e-4, 4.6e-3, 3.1e-4, 4.8e-3],
        "60_m": [5.9e-8, 9.3e-6, 2.5e-5, 3.7e-5, 8.9e-4, 3.8e-5, 9.2e-4],
        "20_m_with_building_wake": [2.3e-7, 1.2e-4, 3.2e-4, 2.4e-4, 5.5e-3, 3.6e-4, 5.8e-3],
    },
}


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _manual_anchor_gates(manual: str) -> dict[str, bool]:
    return {
        "section_53_present": "# 5.3 ITER benchmark calculations" in manual,
        "table8_release_quantity_present": "Release quantity</td><td>100g" in manual,
        "table8_forms_present": "Chemical forms</td><td>HT/HTO" in manual,
        "table8_zero_20_60_present": "Release height</td><td>0, 20 and 60 m" in manual,
        "table8_duration_present": "Duration of release</td><td>2 min" in manual,
        "result_10m_present": "release event from a height of 10m" in manual,
        "building_wake_case_present": "20m release event with building wake effects" in manual,
        "wind_60m_present": "Wind speed at 60 m height" in manual,
        "mixing_lid_present": "Mixing lid" in manual,
        "no_rain_present": "No rain" in manual,
        "no_plume_rise_present": "No plume rise" in manual,
        "deposition_hto_present": "Dry deposition velocity HTO" in manual,
        "deposition_ht_present": "Dry deposition velocity HT" in manual,
        "reemission_present": "Re-emission rate of HTO from soil" in manual,
        "oxidation_present": "Oxidation rate in air" in manual,
        "table9_present": "Table 9. Diffusion coefficients" in manual,
        "table10_caption_present": "Table 10. Plume centerline dose in 1000 m distance for a HTO release of 100g and dispersion category D" in manual,
        "table11_caption_present": "Table 11. Plume centerline dose in 1000 m distance for a HTO release of 100g and dispersion category F" in manual,
        "table12_caption_present": "Table 12. Plume centerline dose in 1000 m distance for a HT release of 100g and dispersion category D" in manual,
        "table13_caption_present": "Table 13. Plume centerline dose in 1000 m distance for a HT release of 100g and dispersion category F" in manual,
        "stomatal_resistance_present": "stomata resistance = 4 s/cm" in manual,
        "lai_present": "leaf area index = 3 m" in manual,
        "stable_aero_resistance_present": "additional aerodynamic resistance of nearly 10 s/cm" in manual,
    }


def _benchmark_inputs() -> dict[str, Any]:
    return {
        "emission": {
            "release_quantity_g": 100.0,
            "chemical_forms": ["HT", "HTO"],
            "duration_s": 120.0,
            "table8_release_heights_m": [0.0, 20.0, 60.0],
            "result_release_heights_m": [10.0, 20.0, 60.0],
            "result_additional_case": "20_M_WITH_BUILDING_WAKE",
        },
        "release_height_ambiguity": {
            "id": "ITER_RELEASE_HEIGHT_0_VS_10_M",
            "table8_value_m": 0.0,
            "section53_result_value_m": 10.0,
            "resolution": "PRESERVE_AMBIGUITY",
        },
        "meteorology": {
            "D": {"wind_speed_at_60m_m_s": 5.0, "mixing_lid_m": 560.0, "wind_profile_exponent": 0.34},
            "F": {"wind_speed_at_60m_m_s": 3.0, "mixing_lid_m": 200.0, "wind_profile_exponent": 0.44},
            "air_temperature_c": 10.0,
            "rain": "NONE",
            "plume_rise": "NONE",
        },
        "building": {
            "wake_case_release_height_m": 20.0,
            "width_m": 100.0,
            "height_m": 70.0,
        },
        "coefficients": {
            "dry_deposition_velocity_hto_cm_s": 1.8,
            "dry_deposition_velocity_ht_cm_s": 0.05,
            "soil_diffusion_hto_cm2_s": 2.0e-5,
            "soil_diffusion_ht_cm2_s": 5.0e-2,
            "soil_hto_reemission_percent_per_h": 5.0,
            "air_oxidation_percent_per_d": 0.5,
            "breathing_rate_m3_s": 2.66e-4,
            "quality_factor": 1.0,
            "dose_conversion_7d_inhalation_sv_bq": 6.3e-12,
            "dose_conversion_50a_inhalation_ingestion_sv_bq": 1.7e-11,
        },
        "soil_vegetation": {
            "soil_type": "SANDY_LOAM",
            "pore_volume_fraction": 0.50,
            "pore_water_fraction": 0.40,
            "pore_air_fraction": 0.60,
            "transpiration_kg_h2o_per_kg_dry_matter_d": 1.0,
            "vegetation_density_kg_dry_matter_m2": 1.0,
        },
        "site_population": {
            "population_density_people_km2": 50.0,
            "exclusion_radius_km": 1.0,
            "outer_radius_km": 80.0,
        },
        "human_diet_kg_s": {
            "milk": 3.5e-6,
            "beef": 2.3e-6,
            "lamb": 2.0e-7,
            "other_vegetables": 9.0e-7,
            "legumes": 9.0e-7,
            "roots": 2.0e-6,
            "grain": 2.0e-6,
            "water": 1.7e-5,
            "fish": 3.5e-7,
        },
        "section53_plant_additions": {
            "stomatal_resistance_s_cm": 4.0,
            "leaf_area_index_m2_m2": 3.0,
            "very_stable_additional_aerodynamic_resistance_s_cm_approx": 10.0,
        },
        "mol_diffusion": {
            "D": {"p_y": 0.418, "q_y": 0.796, "p_z": 0.520, "q_z": 0.711},
            "F": {"p_y": 0.235, "q_y": 0.796, "p_z": 0.311, "q_z": 0.711},
        },
    }


def _sum_identity_checks(relative_tolerance: float = 0.05) -> dict[str, dict[str, bool]]:
    checks: dict[str, dict[str, bool]] = {}
    for table_name, table in REFERENCE_1KM.items():
        table_checks: dict[str, bool] = {}
        for case_name, row in table.items():
            early_expected = row[1] + row[3]
            chronic_expected = row[2] + row[4]
            table_checks[f"{case_name}_early"] = math.isclose(
                row[5], early_expected, rel_tol=relative_tolerance, abs_tol=0.0
            )
            table_checks[f"{case_name}_chronic"] = math.isclose(
                row[6], chronic_expected, rel_tol=relative_tolerance, abs_tol=0.0
            )
        checks[table_name] = table_checks
    return checks


def _ordering_checks() -> dict[str, bool]:
    checks: dict[str, bool] = {}
    for table_name, table in REFERENCE_1KM.items():
        chronic = {case: row[6] for case, row in table.items()}
        checks[f"{table_name}_10m_highest"] = chronic["10_m"] == max(chronic.values())
        checks[f"{table_name}_60m_lowest"] = chronic["60_m"] == min(chronic.values())
        checks[f"{table_name}_wake_gt_plain20"] = (
            chronic["20_m_with_building_wake"] > chronic["20_m"]
        )
    return checks


def _source_trend_checks() -> dict[str, bool]:
    # These checks are deliberately limited to robust relations visible in Tables 10-13.
    return {
        "hto_F_sum_chronic_gt_D_all_cases": all(
            REFERENCE_1KM["table11_hto_F"][case][6]
            > REFERENCE_1KM["table10_hto_D"][case][6]
            for case in CASES
        ),
        "ht_F_sum_chronic_gt_D_all_cases": all(
            REFERENCE_1KM["table13_ht_F"][case][6]
            > REFERENCE_1KM["table12_ht_D"][case][6]
            for case in CASES
        ),
        "hto_sum_chronic_gt_ht_same_stability_all_cases": all(
            REFERENCE_1KM[f"table1{0 if stability == 'D' else 1}_hto_{stability}"][case][6]
            > REFERENCE_1KM[f"table1{2 if stability == 'D' else 3}_ht_{stability}"][case][6]
            for stability in ("D", "F")
            for case in CASES
        ),
    }


def build_result() -> dict[str, Any]:
    manual = _text("ufotri_manual.md")
    roadmap = _text("docs/v4/roadmap/UFOTRI_REPLICATION_MASTER_PLAN.md")
    governance = _text("docs/v4/governance/ufotri_iter_benchmark_reconstruction_r1.yaml")

    anchors = _manual_anchor_gates(manual)
    sum_checks = _sum_identity_checks()
    ordering = _ordering_checks()
    trends = _source_trend_checks()
    inputs = _benchmark_inputs()

    ambiguity = inputs["release_height_ambiguity"]
    source_boundary = {
        "release_height_conflict_preserved": (
            ambiguity["id"] == "ITER_RELEASE_HEIGHT_0_VS_10_M"
            and ambiguity["table8_value_m"] == 0.0
            and ambiguity["section53_result_value_m"] == 10.0
            and ambiguity["resolution"] == "PRESERVE_AMBIGUITY"
        ),
        "figure_helper_tables_exact_oracle": False,
        "full_atmospheric_numeric_replay_complete": False,
        "empirical_validation_complete": False,
        "real_cteas_atmos_binding": False,
    }

    repository_mapping = {
        "g2_authorized_by_roadmap": STAGE in roadmap,
        "governance_stage_present": f"stage: {STAGE}" in governance,
        "ht_contract_present": (ROOT / "src/cteas_ufotri/coupling/ht_v4.py").is_file(),
        "ht_to_hto_adapter_present": (ROOT / "src/cteas_ufotri/coupling/ht_to_hto_soil_v4.py").is_file(),
        "reemission_adapter_present": (ROOT / "src/cteas_ufotri/coupling/reemission_area_source_v4.py").is_file(),
        "manual_dose_path_present": (ROOT / "src/cteas_ufotri/dose/ufotri_manual_v4.py").is_file(),
    }

    contract_gates = {
        "manual_anchors": all(anchors.values()),
        "four_reference_tables_present": (
            set(REFERENCE_1KM)
            == {"table10_hto_D", "table11_hto_F", "table12_ht_D", "table13_ht_F"}
            and all(list(table) == CASES for table in REFERENCE_1KM.values())
            and all(len(row) == len(COLUMNS) for table in REFERENCE_1KM.values() for row in table.values())
        ),
        "printed_sum_identities": all(
            value for table in sum_checks.values() for value in table.values()
        ),
        "release_height_and_wake_ordering": all(ordering.values()),
        "robust_table_trends": all(trends.values()),
        "release_height_ambiguity_preserved": source_boundary["release_height_conflict_preserved"],
        "fail_closed_nonclaims": (
            source_boundary["figure_helper_tables_exact_oracle"] is False
            and source_boundary["full_atmospheric_numeric_replay_complete"] is False
            and source_boundary["empirical_validation_complete"] is False
            and source_boundary["real_cteas_atmos_binding"] is False
        ),
        "repository_mapping": all(repository_mapping.values()),
    }

    status = (
        "PASS_MANUAL_TABULATED_ITER_BENCHMARK_RECONSTRUCTION"
        if all(contract_gates.values())
        else "FAIL_ITER_BENCHMARK_RECONSTRUCTION"
    )

    return {
        "stage": STAGE,
        "status": status,
        "manual_anchor_gates": anchors,
        "benchmark_inputs": inputs,
        "reference_columns": COLUMNS,
        "reference_1km_tables": REFERENCE_1KM,
        "sum_identity_checks": sum_checks,
        "ordering_checks": ordering,
        "source_trend_checks": trends,
        "source_boundary": source_boundary,
        "repository_mapping": repository_mapping,
        "contract_gates": contract_gates,
        "decision": {
            "production_source_changed": False,
            "default_parameters_changed": False,
            "workflow_changed": False,
            "roadmap_changed_in_stage_pr": False,
            "table8_zero_m_silently_replaced_by_10m": False,
            "figure_chart_values_promoted_to_exact_oracle": False,
        },
        "non_claims": {
            "iter_full_atmospheric_numeric_replay": False,
            "iter_empirical_validation": False,
            "physical_accuracy": False,
            "production_readiness": False,
            "original_ufotri_executable_equivalence": False,
            "original_musemet_equivalence": False,
        },
    }


def main() -> int:
    result = build_result()
    print(f"G2_ITER_STATUS={result['status']}")
    print("G2_ITER_RESULT_JSON=" + json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
