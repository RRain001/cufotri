#!/usr/bin/env python3
"""Machine-visible UFOTRI OBT compartment numerical qualification R1.

B2 qualifies the B1 state-role reconstruction without changing the frozen
``obt_v3`` solver or V4 operator split. Two manual-supported rate contexts are
run side by side:

* Section 2.2.6 daily-average hourly rates (the existing controlled baseline);
* Section 3.3.3 Eq. (65)-(66) rates converted to hourly/second units.

The comparison is diagnostic. Neither profile is promoted to recovered original
executable truth, and the missing original day/night multipliers remain
unresolved.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any

from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_ufotri_v4 import (
    NO_SEPARATE_EXCHANGEABLE_POOL,
    current_short_term_inventory_baseline,
    ufotri_long_term_ingestion_obt_profile,
    ufotri_obt_rate_reconciliation,
    ufotri_obt_role_map,
    ufotri_short_term_obt_profile,
)
from cteas_ufotri.plant.obt_v3 import (
    OBTParameters,
    OBTState,
    OBTSolver,
    PlantBiologicalForcing,
)
from cteas_ufotri.plant.root_v4 import (
    RootWaterFluxProvenanceV4,
    ThreeLayerRootWaterFluxForcingV4,
)
from cteas_ufotri.plant.soil_v4 import (
    SoilV4Provenance,
    ThreeLayerSoilForcing,
    ThreeLayerSoilState,
    ThreeLayerSoilStorageSolver,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.v4_integration import (
    SELECTED_OPERATOR_SPLIT,
    V4SoilRootTFWTOBTIntegrator,
    V4SoilRootTFWTOBTState,
)


UTC = timezone.utc
STAGE = "UFOTRI_OBT_COMPARTMENT_CONSERVATION_NUMERICAL_INTEGRATION_R1"
PASS_STATUS = "PASS_OBT_COMPARTMENT_CONSERVATION_NUMERICAL_INTEGRATION"
SECTION_2_2_6_PROFILE = "SECTION_2_2_6_DAILY_AVERAGE_CONTROLLED_BASELINE"
EQ65_66_PROFILE = "EQ65_66_DERIVED_HOURLY_COMPARISON"
DURATION_S = 24.0 * 3600.0
TRITIUM_HALF_LIFE_S = 388_789_632.0
ROOT_Q_W_M_S = (1.0e-8, 2.0e-8, 1.0e-8)
REF_DT_S = 225.0
REFINEMENT_DTS_S = (3600.0, 1800.0, 900.0, 450.0)
QUALIFICATION_DT_S = 1800.0
BALANCE_TOL = 1.0e-10
ANALYTIC_TOL = 1.0e-12


@dataclass(frozen=True)
class QualificationProfile:
    identifier: str
    parameters: OBTParameters
    source_context: str
    interpretation: str
    recovered_original_executable_truth: bool = False
    production_parameter_profile: bool = False


def section_2_2_6_profile() -> QualificationProfile:
    short = ufotri_short_term_obt_profile()
    return QualificationProfile(
        identifier=SECTION_2_2_6_PROFILE,
        parameters=current_short_term_inventory_baseline(),
        source_context=short.context,
        interpretation="RECOVERED_DAILY_AVERAGE_CONTROLLED_BASELINE",
    )


def eq65_66_profile() -> QualificationProfile:
    long_term = ufotri_long_term_ingestion_obt_profile()
    return QualificationProfile(
        identifier=EQ65_66_PROFILE,
        parameters=OBTParameters(
            kf_s=long_term.hto_to_obt_h_1_exact_from_stated_masses / 3600.0,
            kr_s=long_term.obt_to_hto_h_1 / 3600.0,
            daylight_multiplier=1.0,
            nighttime_multiplier=1.0,
        ),
        source_context=long_term.context,
        interpretation="EQ65_66_RATE_CONTEXT_CONVERTED_FOR_CONTROLLED_COMPARISON_ONLY",
    )


def qualification_profiles() -> tuple[QualificationProfile, QualificationProfile]:
    return section_2_2_6_profile(), eq65_66_profile()


def plant_provenance(dt_s: float, profile_id: str) -> ForcingProvenance:
    return ForcingProvenance(
        source_id="SYNTHETIC_B2_OBT_QUALIFICATION_PLANT",
        source_version=f"b2-{profile_id.lower()}",
        artifact_sha256="a" * 64,
        spatial_reference="synthetic-common-soil-surface-area",
        temporal_resolution_s=dt_s,
    )


def soil_provenance(dt_s: float, profile_id: str) -> SoilV4Provenance:
    return SoilV4Provenance(
        source_id="SYNTHETIC_B2_OBT_QUALIFICATION_SOIL",
        source_version=f"b2-{profile_id.lower()}",
        artifact_sha256="b" * 64,
        spatial_reference="synthetic-common-soil-surface-area",
        temporal_resolution_s=dt_s,
    )


def root_provenance(profile_id: str) -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="SYNTHETIC_B2_OBT_QUALIFICATION_ROOT_QW",
        source_locator="scripts/v4/run_ufotri_obt_compartment_conservation_numerical_integration_r1.py",
        revision=f"b2-{profile_id.lower()}",
        artifact_sha256="c" * 64,
        profile_context="SYNTHETIC_EXPLICIT_Q_W_NOT_PRODUCTION",
    )


def initial_state(dt_s: float, profile_id: str) -> V4SoilRootTFWTOBTState:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=timestamp,
        provenance=soil_provenance(dt_s, profile_id),
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        tfwt_inventory_bq_m2=2.0,
        water_content_kg_m2=5.0,
        time=timestamp,
        provenance=plant_provenance(dt_s, profile_id),
        area_basis="soil_surface_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        obt_inventory_bq_m2=0.0,
        plant_mass_kg_m2=2.0,
        timestamp=timestamp,
        provenance=plant_provenance(dt_s, profile_id),
        area_basis="soil_surface_area",
    )
    return V4SoilRootTFWTOBTState(
        soil_state=soil,
        tfwt_state=tfwt,
        obt_state=obt,
    )


def integrator(profile: QualificationProfile) -> V4SoilRootTFWTOBTIntegrator:
    return V4SoilRootTFWTOBTIntegrator(
        soil_solver=ThreeLayerSoilStorageSolver(
            tritium_half_life_s=TRITIUM_HALF_LIFE_S
        ),
        obt_solver=OBTSolver(parameters=profile.parameters),
    )


def run_chain_case(
    profile: QualificationProfile,
    dt_s: float,
    *,
    restart_at_half: bool = False,
) -> dict[str, Any]:
    steps = int(round(DURATION_S / dt_s))
    if not math.isclose(steps * dt_s, DURATION_S, rel_tol=0.0, abs_tol=1.0e-9):
        raise RuntimeError("dt must divide the 24 h integration window")

    model = integrator(profile)
    state = initial_state(dt_s, profile.identifier)
    max_root_identity = 0.0
    max_plant_residual = 0.0
    max_coupled_residual = 0.0
    max_soil_residual = 0.0

    for index in range(steps):
        if restart_at_half and index == steps // 2:
            state = V4SoilRootTFWTOBTState.from_json(state.to_json())
        soil_forcing = ThreeLayerSoilForcing(timestamp=state.timestamp)
        root_forcing = ThreeLayerRootWaterFluxForcingV4(
            plant_identifier=state.plant_identifier,
            timestamp=state.timestamp,
            water_uptake_fluxes_m_s=ROOT_Q_W_M_S,
            provenance=root_provenance(profile.identifier),
        )
        result = model.advance(
            state,
            soil_forcing=soil_forcing,
            root_forcing=root_forcing,
            biological_forcing=PlantBiologicalForcing(
                is_daylight=(index % 24) < 12
            ),
            interval_seconds=dt_s,
        )
        max_root_identity = max(
            max_root_identity,
            abs(result.balance.soil_root_hto_identity_residual_bq_m2),
        )
        max_plant_residual = max(
            max_plant_residual,
            abs(result.balance.plant_residual_bq_m2),
        )
        max_coupled_residual = max(
            max_coupled_residual,
            abs(result.balance.coupled_residual_bq_m2),
        )
        max_soil_residual = max(
            max_soil_residual,
            abs(result.soil_result.global_balance.hto_residual_bq_m2),
        )
        state = result.state

    return {
        "profile": profile.identifier,
        "dt_s": dt_s,
        "steps": steps,
        "soil_hto_bq_m2": state.soil_state.total_hto_inventory_bq_m2,
        "tfwt_bq_m2": state.tfwt_state.inventory(),
        "obt_bq_m2": state.obt_state.inventory(),
        "plant_total_bq_m2": (
            state.tfwt_state.inventory() + state.obt_state.inventory()
        ),
        "max_abs_root_identity_residual_bq_m2": max_root_identity,
        "max_abs_plant_residual_bq_m2": max_plant_residual,
        "max_abs_coupled_residual_bq_m2": max_coupled_residual,
        "max_abs_soil_residual_bq_m2": max_soil_residual,
        "final_state": state.to_mapping(),
    }


def state_error(case: dict[str, Any], reference: dict[str, Any]) -> float:
    return sum(
        abs(float(case[key]) - float(reference[key]))
        for key in ("soil_hto_bq_m2", "tfwt_bq_m2", "obt_bq_m2")
    )


def profile_chain_qualification(profile: QualificationProfile) -> dict[str, Any]:
    reference = run_chain_case(profile, REF_DT_S)
    runs = {
        str(int(dt)): run_chain_case(profile, dt)
        for dt in REFINEMENT_DTS_S
    }
    errors = {
        key: state_error(case, reference) for key, case in runs.items()
    }
    ordered_errors = [errors[str(int(dt))] for dt in REFINEMENT_DTS_S]
    refinement_pass = all(
        later < earlier
        for earlier, later in zip(ordered_errors, ordered_errors[1:])
    )

    direct = runs[str(int(QUALIFICATION_DT_S))]
    repeat = run_chain_case(profile, QUALIFICATION_DT_S)
    restarted = run_chain_case(
        profile, QUALIFICATION_DT_S, restart_at_half=True
    )

    cases = [reference, *runs.values()]
    balance_pass = all(
        float(case[key]) <= BALANCE_TOL
        for case in cases
        for key in (
            "max_abs_root_identity_residual_bq_m2",
            "max_abs_plant_residual_bq_m2",
            "max_abs_coupled_residual_bq_m2",
            "max_abs_soil_residual_bq_m2",
        )
    )
    return {
        "profile": profile.identifier,
        "source_context": profile.source_context,
        "parameters": {
            "kf_s": profile.parameters.kf_s,
            "kr_s": profile.parameters.kr_s,
            "daylight_multiplier": profile.parameters.daylight_multiplier,
            "nighttime_multiplier": profile.parameters.nighttime_multiplier,
        },
        "reference_dt_s": REF_DT_S,
        "reference": reference,
        "runs": runs,
        "refinement_errors": errors,
        "gates": {
            "conservation_closed": balance_pass,
            "deterministic_repeat": repeat == direct,
            "restart_equivalence": restarted == direct,
            "timestep_refinement": refinement_pass,
            "obt_formation_nonzero": all(
                float(case["obt_bq_m2"]) > 0.0 for case in runs.values()
            ),
        },
    }


def _analytic_next_obt(
    *,
    tfwt_inventory_bq_m2: float,
    initial_obt_bq_m2: float,
    kf_s: float,
    kr_s: float,
    interval_s: float,
) -> float:
    source_rate = kf_s * tfwt_inventory_bq_m2
    if kr_s == 0.0:
        return initial_obt_bq_m2 + source_rate * interval_s
    equilibrium = source_rate / kr_s
    return equilibrium + (
        initial_obt_bq_m2 - equilibrium
    ) * math.exp(-kr_s * interval_s)


def analytic_probe(profile: QualificationProfile) -> dict[str, Any]:
    timestamp = datetime(2026, 2, 1, tzinfo=UTC)
    provenance = plant_provenance(DURATION_S, profile.identifier)
    tfwt_inventory = 2.0
    initial_obt = 0.0
    tfwt = TFWTState.from_inventory(
        plant_identifier="analytic-plant",
        crop="analytic-crop",
        growth_stage="analytic-stage",
        tfwt_inventory_bq_m2=tfwt_inventory,
        water_content_kg_m2=0.4,
        time=timestamp,
        provenance=provenance,
        area_basis="plant_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier="analytic-plant",
        crop="analytic-crop",
        growth_stage="analytic-stage",
        obt_inventory_bq_m2=initial_obt,
        plant_mass_kg_m2=0.1,
        timestamp=timestamp,
        provenance=provenance,
        area_basis="plant_area",
    )
    solver = OBTSolver(parameters=profile.parameters)
    result = solver.advance(
        tfwt,
        obt,
        DURATION_S,
        PlantBiologicalForcing(is_daylight=True),
    )
    expected = _analytic_next_obt(
        tfwt_inventory_bq_m2=tfwt_inventory,
        initial_obt_bq_m2=initial_obt,
        kf_s=profile.parameters.kf_s,
        kr_s=profile.parameters.kr_s,
        interval_s=DURATION_S,
    )
    residual = result.state.inventory() - expected
    formation_expected = (
        profile.parameters.kf_s * tfwt_inventory * DURATION_S
    )
    return {
        "profile": profile.identifier,
        "expected_obt_bq_m2": expected,
        "solver_obt_bq_m2": result.state.inventory(),
        "residual_bq_m2": residual,
        "formation_expected_bq_m2": formation_expected,
        "formation_reported_bq_m2": result.balance.obt_formation_bq_m2,
        "other_loss_bq_m2": result.balance.other_loss_bq_m2,
        "balance_residual_bq_m2": result.balance.residual_bq_m2,
        "pass": (
            abs(residual) <= ANALYTIC_TOL
            and math.isclose(
                result.balance.obt_formation_bq_m2,
                formation_expected,
                rel_tol=0.0,
                abs_tol=ANALYTIC_TOL,
            )
            and abs(result.balance.residual_bq_m2) <= ANALYTIC_TOL
        ),
    }


def zero_tfwt_decay_probe(profile: QualificationProfile) -> dict[str, Any]:
    timestamp = datetime(2026, 2, 2, tzinfo=UTC)
    provenance = plant_provenance(DURATION_S, profile.identifier)
    tfwt = TFWTState.from_inventory(
        plant_identifier="decay-plant",
        crop="analytic-crop",
        growth_stage="analytic-stage",
        tfwt_inventory_bq_m2=0.0,
        water_content_kg_m2=0.4,
        time=timestamp,
        provenance=provenance,
        area_basis="plant_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier="decay-plant",
        crop="analytic-crop",
        growth_stage="analytic-stage",
        obt_inventory_bq_m2=1.0,
        plant_mass_kg_m2=0.1,
        timestamp=timestamp,
        provenance=provenance,
        area_basis="plant_area",
    )
    result = OBTSolver(parameters=profile.parameters).advance(
        tfwt,
        obt,
        DURATION_S,
        PlantBiologicalForcing(is_daylight=True),
    )
    expected = math.exp(-profile.parameters.kr_s * DURATION_S)
    return {
        "profile": profile.identifier,
        "expected_obt_bq_m2": expected,
        "solver_obt_bq_m2": result.state.inventory(),
        "formation_bq_m2": result.balance.obt_formation_bq_m2,
        "pass": (
            math.isclose(
                result.state.inventory(),
                expected,
                rel_tol=0.0,
                abs_tol=ANALYTIC_TOL,
            )
            and result.balance.obt_formation_bq_m2 == 0.0
            and abs(result.balance.residual_bq_m2) <= ANALYTIC_TOL
        ),
    }


def legacy_baseline_identity() -> dict[str, Any]:
    profile = section_2_2_6_profile()
    frozen = current_short_term_inventory_baseline()
    profile_case = run_chain_case(profile, QUALIFICATION_DT_S)
    frozen_profile = QualificationProfile(
        identifier="FROZEN_REDUCED_RC1_REFERENCE",
        parameters=frozen,
        source_context="FROZEN_OBT_V3_CONTROLLED_BASELINE",
        interpretation="REFERENCE_ONLY",
    )
    frozen_case = run_chain_case(frozen_profile, QUALIFICATION_DT_S)
    comparable_keys = (
        "soil_hto_bq_m2",
        "tfwt_bq_m2",
        "obt_bq_m2",
        "plant_total_bq_m2",
        "max_abs_root_identity_residual_bq_m2",
        "max_abs_plant_residual_bq_m2",
        "max_abs_coupled_residual_bq_m2",
        "max_abs_soil_residual_bq_m2",
    )
    deltas = {
        key: float(profile_case[key]) - float(frozen_case[key])
        for key in comparable_keys
    }
    return {
        "parameters_identical": profile.parameters == frozen,
        "state_deltas": deltas,
        "pass": (
            profile.parameters == frozen
            and all(value == 0.0 for value in deltas.values())
        ),
    }


def build_result() -> dict[str, Any]:
    short_profile, eq_profile = qualification_profiles()
    qualifications = {
        profile.identifier: profile_chain_qualification(profile)
        for profile in (short_profile, eq_profile)
    }
    analytic = {
        profile.identifier: analytic_probe(profile)
        for profile in (short_profile, eq_profile)
    }
    decay = {
        profile.identifier: zero_tfwt_decay_probe(profile)
        for profile in (short_profile, eq_profile)
    }
    legacy = legacy_baseline_identity()
    short_final = qualifications[SECTION_2_2_6_PROFILE]["runs"]["1800"]
    eq_final = qualifications[EQ65_66_PROFILE]["runs"]["1800"]
    profile_delta = {
        key: float(short_final[key]) - float(eq_final[key])
        for key in ("tfwt_bq_m2", "obt_bq_m2", "plant_total_bq_m2")
    }
    rate_reconciliation = ufotri_obt_rate_reconciliation()
    role_map = ufotri_obt_role_map()

    profile_gates = all(
        all(bool(value) for value in item["gates"].values())
        for item in qualifications.values()
    )
    gates = {
        "both_profiles_chain_qualified": profile_gates,
        "both_profiles_match_independent_analytic_solution": all(
            bool(item["pass"]) for item in analytic.values()
        ),
        "both_profiles_close_zero_tfwt_decay": all(
            bool(item["pass"]) for item in decay.values()
        ),
        "section_2_2_6_matches_frozen_reduced_rc1": bool(legacy["pass"]),
        "profile_consequence_is_nonzero": abs(profile_delta["obt_bq_m2"]) > 0.0,
        "manual_rate_forms_remain_nonidentical": not rate_reconciliation.numerically_identical,
        "selected_operator_split_preserved": (
            SELECTED_OPERATOR_SPLIT == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
        ),
        "no_separate_exchangeable_pool": (
            NO_SEPARATE_EXCHANGEABLE_POOL
            and not role_map.separate_exchangeable_obt_pool
            and not role_map.exchangeable_obt_extra_inventory_added
        ),
    }

    result: dict[str, Any] = {
        "schema_version": "v1",
        "stage": STAGE,
        "status": PASS_STATUS if all(gates.values()) else "HOLD_NUMERICAL_GATE_FAILED",
        "source_kind": "UFOTRI_MANUAL_RATE_PROFILE_COMPARISON_PLUS_SYNTHETIC_FORCING",
        "selected_operator_split": SELECTED_OPERATOR_SPLIT,
        "duration_s": DURATION_S,
        "profiles": {
            profile.identifier: {
                "source_context": profile.source_context,
                "interpretation": profile.interpretation,
                "kf_s": profile.parameters.kf_s,
                "kr_s": profile.parameters.kr_s,
                "daylight_multiplier": profile.parameters.daylight_multiplier,
                "nighttime_multiplier": profile.parameters.nighttime_multiplier,
                "recovered_original_executable_truth": profile.recovered_original_executable_truth,
                "production_parameter_profile": profile.production_parameter_profile,
            }
            for profile in (short_profile, eq_profile)
        },
        "chain_qualification": qualifications,
        "analytic_probes": analytic,
        "zero_tfwt_decay_probes": decay,
        "legacy_reduced_rc1_identity": legacy,
        "profile_state_delta_at_1800s": profile_delta,
        "manual_rate_reconciliation": {
            "section_2_2_6_forward_h_1": rate_reconciliation.section_2_2_6_forward_h_1,
            "eq66_forward_h_1": rate_reconciliation.eq66_forward_h_1,
            "section_2_2_6_loss_h_1": rate_reconciliation.section_2_2_6_loss_h_1,
            "eq65_loss_h_1": rate_reconciliation.eq65_loss_h_1,
            "numerically_identical": rate_reconciliation.numerically_identical,
        },
        "gates": gates,
        "hard_boundaries": {
            "calibration": False,
            "empirical_validation": False,
            "physical_accuracy_claim": False,
            "production_parameter_activation": False,
            "real_cteas_atmos_binding": False,
            "generic_multi_pool_obt": False,
            "original_executable_parameter_selection_recovered": False,
            "normalized_day_night_multiplier_recovered": False,
            "frozen_v3_rc1_default_changed": False,
        },
    }
    if result["status"] != PASS_STATUS:
        raise RuntimeError(json.dumps(gates, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    print(f"UFOTRI_OBT_B2_STATUS={result['status']}")
    print(f"UFOTRI_OBT_B2_RESULT_JSON={encoded}")
    if args.output is not None:
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
