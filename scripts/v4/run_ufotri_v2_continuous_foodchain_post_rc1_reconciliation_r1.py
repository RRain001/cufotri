#!/usr/bin/env python3
"""Machine-visible D1 reconciliation of the retained V2 food-chain with post-RC1.

This stage is semantic/governance-only.  It proves which historical V2 artifacts
are still byte-identical, maps their recoverable topology to KfK 4605 food-chain
roles, records project extensions and missing manual roles, and preserves the
frozen V4 terminal-harvest endpoint as the default/fallback path.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STAGE = "UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1"
STATUS = "PASS_V2_CONTINUOUS_FOODCHAIN_POST_RC1_RECONCILIATION"
V2_TAG = "ufotri-environmental-pathways-v2-candidate"
V2_TAG_OBJECT_SHA = "11eb90096b2c08a0b40c7cf7f2917d473535e8c7"
V2_COMMIT_SHA = "f097115cbfc052baa18f1e49a1207fa6b3523cff"

EXPECTED_BLOBS = {
    "src/cteas_ufotri/case.py": "54c3155810a119b796dea0b1480e4a559fed5b0e",
    "src/cteas_ufotri/foodchain/model.py": "fc9b9a6b440fd0da8a00f93455c594607c3cc635",
    "src/cteas_ufotri/dose/public.py": "e7ac3c125dcb53583a3015b002e545cb2cfc8f91",
    "src/cteas_ufotri/plant/food_v3/food_transfer_solver.py": "2061ed157df0b59fff194ad41034b5ae7f3ee7c7",
    "src/cteas_ufotri/exposure/intake_v3/intake_solver.py": "1c0f6019d733183ba57265a96f41a4fcda909e04",
    "src/cteas_ufotri/v4_integration/food_intake_dose_endpoint.py": "c715ec905904c1391095fc84c2465045815664ab",
    "docs/v2/manual_equation_inventory.md": "937337e4e9c714377a2fb7bbe641d737b2b2274b",
}

HISTORICAL_V2_PATHS = (
    "src/cteas_ufotri/case.py",
    "src/cteas_ufotri/foodchain/model.py",
    "src/cteas_ufotri/dose/public.py",
)

ROLE_MATRIX: list[dict[str, Any]] = [
    {
        "role": "VEGETABLE_HTO_OBT",
        "manual_equations": "65-66",
        "historical_anchor": "foodchain.model.plant_food_outputs + plant TFWT/OBT states",
        "disposition": "RETAINABLE_CONCENTRATION_PROJECTION_REQUIRES_D3_MANUAL_CLOSURE",
        "reason": (
            "V2 projects TFWT/OBT into fresh-food concentrations, but D1 does not "
            "treat that projection alone as a full reconstruction of the manual vegetable system."
        ),
        "next_owner": "UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE_R1",
    },
    {
        "role": "GRASS_ATMOS_SOIL",
        "manual_equations": "67-81",
        "historical_anchor": "case.run_short_case + foodchain.model.plant_food_outputs",
        "disposition": "PARTIAL_TOPOLOGY_REQUIRES_D2_D3",
        "reason": (
            "The continuous pasture concentration route survives, but manual pasture "
            "40/60/0 root distribution and explicit grass/soil fidelity remain separate closures."
        ),
        "next_owner": "UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY_R1",
    },
    {
        "role": "COW_WATER_BOUNDARY_LOSS",
        "manual_equations": "82-84",
        "historical_anchor": "foodchain.model.step_animal",
        "disposition": "RETAINABLE_TOPOLOGY_PARAMETER_SPLIT_REQUIRED",
        "reason": (
            "Animal HTO/OBT inventories, water input and excretion boundaries are useful, "
            "but support-area normalization and intake habits are project choices."
        ),
        "next_owner": "UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1",
    },
    {
        "role": "MILK_HTO_OBT",
        "manual_equations": "85-91",
        "historical_anchor": "foodchain.model.step_animal milk outputs",
        "disposition": "RETAINABLE_TOPOLOGY_MANUAL_RATE_PROVENANCE_REQUIRED",
        "reason": (
            "Separate milk HTO/OBT outputs and manual-converted transfer rates are retained, "
            "but must be isolated from project herd geometry and modern consumption assumptions."
        ),
        "next_owner": "UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1",
    },
    {
        "role": "COW_OBT_FORMATION_TURNOVER",
        "manual_equations": "92-97",
        "historical_anchor": "foodchain.model.step_animal formation/turnover",
        "disposition": "RETAINABLE_TOPOLOGY_MANUAL_RATE_PROVENANCE_REQUIRED",
        "reason": (
            "The two-pool animal HTO/OBT topology is compatible with the manual role, "
            "subject to D4 equation-level verification and parameter provenance separation."
        ),
        "next_owner": "UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1",
    },
    {
        "role": "COW_INHALATION_SKIN_UPTAKE",
        "manual_equations": "98",
        "historical_anchor": "NONE_IN_foodchain.model.step_animal",
        "disposition": "MISSING_IN_V2_ANIMAL_CORE_REQUIRES_D4",
        "reason": (
            "Public inhalation/skin dose in dose.public is not the animal uptake term in Eq.98; "
            "the two roles must not be conflated."
        ),
        "next_owner": "UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1",
    },
    {
        "role": "GRASS_TO_COW_AND_GRASS_BALANCE",
        "manual_equations": "99-105-2",
        "historical_anchor": "case.run_short_case -> plant_food_outputs -> step_animal",
        "disposition": "RETAINABLE_CONTINUOUS_COUPLING_PARAMETER_SPLIT_REQUIRED",
        "reason": (
            "The continuous pasture-to-animal feed route is structurally useful, while "
            "feed amount, representative support area and beef turnover are not manual-exact."
        ),
        "next_owner": "UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1",
    },
    {
        "role": "PUBLIC_INHALATION_SKIN_DOSE",
        "manual_equations": "106",
        "historical_anchor": "dose.public.calculate_public_dose_step",
        "disposition": "RETAINABLE_PATHWAY_TOPOLOGY_PARAMETER_POLICY_CORRECTION_REQUIRED",
        "reason": (
            "V2 explicitly separates inhalation and skin diagnostics, but modern age-specific "
            "coefficients are an application extension rather than original UFOTRI parameter truth."
        ),
        "next_owner": "UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1",
    },
    {
        "role": "PUBLIC_INGESTION_DOSE",
        "manual_equations": "107",
        "historical_anchor": "dose.public.calculate_public_dose_step",
        "disposition": "RETAINABLE_PATHWAY_TOPOLOGY_PARAMETER_POLICY_CORRECTION_REQUIRED",
        "reason": (
            "Plant, milk, meat and drinking-water ingestion topology is useful; the manual uses "
            "an adult HTO coefficient and treats ingested OBT as HTO, whereas V2 supports a "
            "separate modern OBT ingestion coefficient."
        ),
        "next_owner": "UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1",
    },
    {
        "role": "POST_RC1_TERMINAL_FOOD_ENDPOINT",
        "manual_equations": "PROJECT_BOUNDARY_NOT_UFOTRI_CONTINUOUS_FOODCHAIN",
        "historical_anchor": "v4_integration.V4FoodIntakeDoseEndpointAdapter",
        "disposition": "KEEP_FROZEN_DEFAULT_PARALLEL_COMPATIBILITY_PATH",
        "reason": (
            "The RC1 one-way terminal harvest/intake/dose diagnostic is a stable project boundary. "
            "D2-D5 may add an opt-in continuous UFOTRI path but must not silently replace it."
        ),
        "next_owner": "NONE_RETAIN_DEFAULT",
    },
]

PARAMETER_ORIGIN_SPLIT = {
    "manual_or_manual_converted_candidates": [
        "milk_production_l_day=15.5",
        "hto_excretion_rate=0.16 d^-1",
        "obt_excretion_rate=0.002 d^-1",
        "milk_hto_transfer_rate=0.039 d^-1",
        "milk_obt_transfer_rate=0.0021 d^-1",
        "cow_obt_formation_rate=0.0011 d^-1",
        "cow_obt_turnover_rate=0.015 d^-1",
        "public_skin_to_inhalation_factor=0.5",
    ],
    "project_or_application_extensions_not_manual_truth": [
        "feed_intake_kg_fresh_day=50",
        "drinking_water_l_day=50",
        "animal_support_area_m2=4000",
        "beef_edible_meat_mass_kg_per_head=200",
        "beef_continuous_herd_turnover_rate=0.002 d^-1",
        "age_specific_modern_dose_coefficients",
        "separate_modern_OBT_ingestion_dose_coefficient",
        "terminal_harvest_fraction_and_annual_consumption_adapter_inputs",
    ],
}

NEXT_STAGES = [
    "UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY_R1",
    "UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE_R1",
    "UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1",
    "UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1",
]


def _run_git(*args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _current_bytes(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def _historical_bytes(path: str) -> bytes:
    return _run_git("show", f"{V2_TAG}:{path}")


def _text(path: str) -> str:
    return _current_bytes(path).decode("utf-8")


def build_result() -> dict[str, Any]:
    resolved_v2_commit = _run_git("rev-parse", f"{V2_TAG}^{{commit}}").decode().strip()
    current_blob_checks = {
        path: _git_blob_sha(_current_bytes(path)) == expected
        for path, expected in EXPECTED_BLOBS.items()
    }
    historical_blob_checks = {
        path: _git_blob_sha(_historical_bytes(path)) == EXPECTED_BLOBS[path]
        for path in HISTORICAL_V2_PATHS
    }
    preserved_byte_identity = {
        path: _historical_bytes(path) == _current_bytes(path)
        for path in HISTORICAL_V2_PATHS
    }

    foodchain_text = _text("src/cteas_ufotri/foodchain/model.py")
    dose_text = _text("src/cteas_ufotri/dose/public.py")
    case_text = _text("src/cteas_ufotri/case.py")
    endpoint_text = _text("src/cteas_ufotri/v4_integration/food_intake_dose_endpoint.py")
    food_v3_text = _text("src/cteas_ufotri/plant/food_v3/food_transfer_solver.py")
    intake_v3_text = _text("src/cteas_ufotri/exposure/intake_v3/intake_solver.py")
    manual_text = _text("docs/v2/manual_equation_inventory.md")

    manual_ranges = ("(65)-(66)", "(67)-(81)", "(82)-(84)", "(85)-(91)", "(92)-(97)", "(98)", "(99)-(105-2)", "(106)", "(107)")
    manual_coverage = {anchor: anchor in manual_text for anchor in manual_ranges}

    gates = {
        "v2_tag_resolves_to_frozen_commit": resolved_v2_commit == V2_COMMIT_SHA,
        "all_current_evidence_blobs_match_lock": all(current_blob_checks.values()),
        "historical_v2_core_blobs_match_lock": all(historical_blob_checks.values()),
        "historical_v2_core_preserved_byte_identical_on_main": all(preserved_byte_identity.values()),
        "v2_continuous_driver_still_calls_foodchain_and_step_dose": (
            "plant_food_outputs(" in case_text
            and "step_animal(" in case_text
            and "step_beef_product(" in case_text
            and "calculate_public_dose_step(" in case_text
        ),
        "animal_milk_beef_topology_present": (
            "class AnimalState" in foodchain_text
            and "def step_animal(" in foodchain_text
            and "class BeefProductState" in foodchain_text
            and "def step_beef_product(" in foodchain_text
        ),
        "continuous_daily_dose_semantics_present": (
            "def calculate_public_dose_step(" in dose_text
            and "day_fraction = dt_s / 86400.0" in dose_text
            and "inhalation_dose_sv" in dose_text
            and "skin_absorption_dose_sv" in dose_text
            and "milk_dose_sv" in dose_text
            and "meat_dose_sv" in dose_text
        ),
        "rc1_endpoint_remains_terminal_one_way_non_sink": (
            "Opt-in V4 terminal food -> intake -> dose diagnostic adapter" in endpoint_text
            and "It does not mutate replay state" in endpoint_text
            and "downstream_branch_is_environmental_mass_sink: bool = False" in endpoint_text
            and "source_state_mutated: bool = False" in endpoint_text
        ),
        "rc1_food_and_intake_remain_event_annual_boundary": (
            "Advance one explicit plant-to-food transfer event" in food_v3_text
            and "Convert one food-product inventory into one annual intake state" in intake_v3_text
        ),
        "manual_eq65_107_inventory_coverage_complete": all(manual_coverage.values()),
        "manual_imperfect_balance_boundary_explicit": (
            "equilibrium-oriented daily transfer" in manual_text
            and "explicitly imperfect balances" in manual_text
        ),
        "eq98_animal_gap_explicit": any(
            item["role"] == "COW_INHALATION_SKIN_UPTAKE"
            and item["disposition"] == "MISSING_IN_V2_ANIMAL_CORE_REQUIRES_D4"
            for item in ROLE_MATRIX
        ),
        "parameter_origin_split_explicit": (
            len(PARAMETER_ORIGIN_SPLIT["manual_or_manual_converted_candidates"]) > 0
            and len(PARAMETER_ORIGIN_SPLIT["project_or_application_extensions_not_manual_truth"]) > 0
        ),
        "d2_d5_dependency_partition_complete": len(NEXT_STAGES) == 4,
        "no_existing_source_change_authorized_in_d1": True,
        "rc1_default_preserved": True,
    }

    status = STATUS if all(gates.values()) else "FAIL_V2_CONTINUOUS_FOODCHAIN_POST_RC1_RECONCILIATION"
    return {
        "schema_version": "v1",
        "stage": STAGE,
        "status": status,
        "source_kind": "MANUAL_AND_FROZEN_REPOSITORY_EVIDENCE",
        "v2_evidence": {
            "tag": V2_TAG,
            "annotated_tag_object_sha": V2_TAG_OBJECT_SHA,
            "resolved_commit_sha": resolved_v2_commit,
            "expected_commit_sha": V2_COMMIT_SHA,
            "historical_paths": list(HISTORICAL_V2_PATHS),
            "current_blob_checks": current_blob_checks,
            "historical_blob_checks": historical_blob_checks,
            "preserved_byte_identity": preserved_byte_identity,
        },
        "role_matrix": ROLE_MATRIX,
        "parameter_origin_split": PARAMETER_ORIGIN_SPLIT,
        "implementation_decision": {
            "d1_existing_source_change": False,
            "v2_topology_direct_activation": False,
            "v2_parameters_direct_activation": False,
            "continuous_ufotri_path_required_later": True,
            "continuous_ufotri_path_mode": "OPT_IN_PARALLEL_COMPATIBILITY_PATH",
            "rc1_terminal_harvest_default_removed": False,
            "rc1_terminal_harvest_default_changed": False,
            "historical_v2_mass_closure_is_original_ufotri_algorithm": False,
        },
        "next_stages": NEXT_STAGES,
        "gates": gates,
        "hard_boundaries": {
            "calibration": False,
            "empirical_validation": False,
            "physical_accuracy_claim": False,
            "production_parameter_activation": False,
            "modern_dose_coefficients_as_original_ufotri": False,
            "separate_obt_dose_coefficient_as_original_ufotri": False,
            "beef_inventory_turnover_as_original_ufotri": False,
            "animal_support_area_as_original_ufotri": False,
            "real_cteas_atmos_binding": False,
            "original_executable_equivalence": False,
        },
    }


def main() -> int:
    result = build_result()
    print(f"UFOTRI_V2_CONTINUOUS_FOODCHAIN_POST_RC1_STATUS={result['status']}")
    print(
        "UFOTRI_V2_CONTINUOUS_FOODCHAIN_POST_RC1_RESULT_JSON="
        + json.dumps(result, sort_keys=True, separators=(",", ":"))
    )
    return 0 if result["status"] == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
