#!/usr/bin/env python3
"""Machine gate for UFOTRI F1 re-emission/area-source reconciliation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cteas_ufotri.coupling.reemission_area_source_v4 import (
    AREA_SOURCE_SIGMA_WIDTH_FACTOR,
    EQ6_NORMALIZATION_CONVENTION,
    SOURCE_HOUR_SECONDS,
    AccountedReemissionLoss,
    HourlyReemissionHandoffBuffer,
    HT_DERIVED_HTO,
    MIXED_HTO_ORIGIN,
    PLANT,
    PRIMARY_HTO,
    SOIL,
    ManualAreaSourceGeometry,
    eq5_effective_sigma_y_m,
    eq6_equivalent_area_source_concentration_bq_m3,
    superpose_secondary_sources,
)


ROOT = Path(__file__).resolve().parents[2]
STAGE = "UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION_R1"


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _hourly_probe(dt_s: int) -> dict[str, Any]:
    geometry = ManualAreaSourceGeometry.from_canopy_height(
        length_m=20.0,
        width_m=20.0,
        canopy_height_m=2.0,
    )
    buffer = HourlyReemissionHandoffBuffer(
        time_step_seconds=dt_s,
        geometry=geometry,
    )
    first_hour_zero = True
    for index in range(SOURCE_HOUR_SECONDS // dt_s):
        soil, plant = buffer.step(
            (
                AccountedReemissionLoss(
                    compartment=SOIL,
                    flux_bq_m2_s=0.25,
                    origin=PRIMARY_HTO,
                    transfer_id=f"S-{dt_s}-{index}",
                ),
                AccountedReemissionLoss(
                    compartment=PLANT,
                    flux_bq_m2_s=0.10,
                    origin=PRIMARY_HTO,
                    transfer_id=f"P-{dt_s}-{index}",
                ),
            )
        )
        first_hour_zero = first_hour_zero and (
            soil.flux_bq_m2_s == 0.0 and plant.flux_bq_m2_s == 0.0
        )
    soil, plant = buffer.active_sources()
    return {
        "first_hour_secondary_zero": first_hour_zero,
        "soil_flux_bq_m2_s": soil.flux_bq_m2_s,
        "plant_flux_bq_m2_s": plant.flux_bq_m2_s,
        "soil_activity_bq": soil.routed_activity_bq,
        "plant_activity_bq": plant.routed_activity_bq,
        "soil_ledger_closed": soil.environmental_loss_activity_bq
        == soil.routed_activity_bq + soil.unrouted_activity_bq,
        "plant_ledger_closed": plant.environmental_loss_activity_bq
        == plant.routed_activity_bq + plant.unrouted_activity_bq,
    }


def _mixed_origin_probe() -> dict[str, bool | str]:
    geometry = ManualAreaSourceGeometry(
        length_m=10.0,
        width_m=10.0,
        effective_height_m=1.0,
    )
    buffer = HourlyReemissionHandoffBuffer(
        time_step_seconds=1800,
        geometry=geometry,
    )
    for index in range(2):
        buffer.step(
            (
                AccountedReemissionLoss(
                    compartment=SOIL,
                    flux_bq_m2_s=0.1,
                    origin=PRIMARY_HTO,
                    transfer_id=f"PRIMARY-{index}",
                ),
                AccountedReemissionLoss(
                    compartment=SOIL,
                    flux_bq_m2_s=0.1,
                    origin=HT_DERIVED_HTO,
                    transfer_id=f"DERIVED-{index}",
                    origin_proof_id="E2-PROOF",
                ),
            )
        )
    soil, _ = buffer.active_sources()
    missing_proof_rejected = False
    try:
        AccountedReemissionLoss(
            compartment=SOIL,
            flux_bq_m2_s=0.1,
            origin=HT_DERIVED_HTO,
            transfer_id="NO-PROOF",
        )
    except ValueError:
        missing_proof_rejected = True
    return {
        "origin": soil.origin,
        "mixed_origin_preserved": soil.origin == MIXED_HTO_ORIGIN,
        "missing_ht_derived_proof_rejected": missing_proof_rejected,
    }


def build_result() -> dict[str, Any]:
    manual = _text("ufotri_manual.md")
    e3 = _text(
        "docs/v4/adr/ADR-073-ufotri-ht-derived-hto-reemission-secondary-feedback-reconciliation-r1.md"
    )
    historical_case = _text("src/cteas_ufotri/case.py")
    historical_gaussian = _text("src/cteas_ufotri/atmosphere/gaussian.py")
    defaults = _text("configs/default_parameters.yaml")
    adapter = _text("src/cteas_ufotri/coupling/reemission_area_source_v4.py")

    manual_gates = {
        "hour_n_to_n_plus_one": (
            "concentrations of hour N" in manual
            and "modified in hour N + 1" in manual
        ),
        "rectangular_sources": "If possible, the area sources should be rectangular" in manual,
        "center_point_method_selected": (
            'Method "2." presents the least difficulties in programming' in manual
            and "source point in the center of the area source" in manual
        ),
        "eq5_width_over_4_3": "width of the area source divided by 4.3" in manual,
        "eq6_separate_soil_plant": (
            'Equation 6 is applied separately for the two compartments "soil" and "plants"'
            in manual
        ),
        "linear_superposition": (
            "resulting plumes are calculated assuming linear dispersion and superposition"
            in manual
        ),
        "common_source_height": "identical   source   heights" in manual,
    }

    e3_gates = {
        "same_loss_handoff": (
            "environmental inventory loss = secondary-source activity handed to atmosphere"
            in e3
        ),
        "mixed_origin_fail_closed": (
            "MIXED_HTO_ORIGIN" in e3
            and "no proportional source split may be invented silently" in e3
        ),
        "eq44_still_unresolved": (
            "numerical generation of a manual-fidelity Eq. (44) soil re-emission rate remains unresolved"
            in e3
        ),
        "phase_f_owns_numerics": (
            "source geometry, emission height, delay semantics and source integration are Phase-F responsibilities"
            in e3
        ),
    }

    historical_gates = {
        "legacy_delay_present": (
            "reemission_feedback_delay_s" in historical_case
            and "feedback_history.append(diag.total_reemission_bq_m2_s)" in historical_case
        ),
        "legacy_rectangle_quadrature_present": (
            "rectangular_area_source_concentration(" in historical_case
            and "Midpoint integration of a uniform rectangular ground-level area source"
            in historical_gaussian
        ),
        "legacy_primary_plus_secondary_present": "air = primary + secondary" in historical_case,
        "default_area_source_unchanged": "reemission_feedback_mode: area_source" in defaults,
        "default_3600_delay_unchanged": "reemission_feedback_delay_s: 3600" in defaults,
    }

    geometry = ManualAreaSourceGeometry.from_canopy_height(
        length_m=100.0,
        width_m=50.0,
        canopy_height_m=2.0,
    )
    sigma_eff = eq5_effective_sigma_y_m(30.0, 50.0)
    sigma_expected = (30.0**2 + (50.0 / 4.3) ** 2) ** 0.5
    eq6_value = eq6_equivalent_area_source_concentration_bq_m3(
        surface_flux_bq_m2_s=2.0e-4,
        geometry=geometry,
        receptor_downwind_m=800.0,
        receptor_crosswind_m=0.0,
        wind_speed_m_s=3.0,
        stability_class="D",
        fallout_factor=1.0,
        washout_factor=1.0,
    )
    probe_600 = _hourly_probe(600)
    probe_300 = _hourly_probe(300)
    mixed = _mixed_origin_probe()

    buffer = HourlyReemissionHandoffBuffer(
        time_step_seconds=3600,
        geometry=geometry,
    )
    buffer.step(
        (
            AccountedReemissionLoss(
                compartment=SOIL,
                flux_bq_m2_s=0.2,
                origin=PRIMARY_HTO,
                transfer_id="S",
            ),
            AccountedReemissionLoss(
                compartment=PLANT,
                flux_bq_m2_s=0.1,
                origin=PRIMARY_HTO,
                transfer_id="P",
            ),
        )
    )
    soil_source, plant_source = buffer.active_sources()
    concentrations = superpose_secondary_sources(
        primary_air_bq_m3=1.0,
        soil_source=soil_source,
        plant_source=plant_source,
        geometry=geometry,
        receptor_downwind_m=800.0,
        receptor_crosswind_m=0.0,
        wind_speed_m_s=3.0,
        stability_class="D",
        soil_fallout_factor=1.0,
        soil_washout_factor=1.0,
        plant_fallout_factor=1.0,
        plant_washout_factor=1.0,
    )

    superposition_residual = abs(
        concentrations.secondary_air_bq_m3
        - concentrations.soil_secondary_bq_m3
        - concentrations.plant_secondary_bq_m3
    )
    superposition_scale = max(
        concentrations.secondary_air_bq_m3,
        concentrations.soil_secondary_bq_m3,
        concentrations.plant_secondary_bq_m3,
        1.0e-30,
    )

    numerical_gates = {
        "phase_a_flqh_reused": geometry.effective_height_m == 1.6,
        "eq5_width_factor_exact": abs(sigma_eff - sigma_expected) < 1.0e-14,
        "printed_eq6_convention_explicit": EQ6_NORMALIZATION_CONVENTION
        == "PRINTED_SIGMA_Y_DENOMINATOR_SIGMA_YG_LATERAL_EXPONENT",
        "eq6_positive_controlled_replay": eq6_value > 0.0,
        "first_hour_zero_dt600": bool(probe_600["first_hour_secondary_zero"]),
        "first_hour_zero_dt300": bool(probe_300["first_hour_secondary_zero"]),
        "dt_invariant_soil_flux": abs(
            float(probe_600["soil_flux_bq_m2_s"])
            - float(probe_300["soil_flux_bq_m2_s"])
        ) < 1.0e-15,
        "dt_invariant_plant_flux": abs(
            float(probe_600["plant_flux_bq_m2_s"])
            - float(probe_300["plant_flux_bq_m2_s"])
        ) < 1.0e-15,
        "dt_invariant_soil_activity": abs(
            float(probe_600["soil_activity_bq"])
            - float(probe_300["soil_activity_bq"])
        ) < 1.0e-9,
        "dt_invariant_plant_activity": abs(
            float(probe_600["plant_activity_bq"])
            - float(probe_300["plant_activity_bq"])
        ) < 1.0e-9,
        "soil_ledger_closed": bool(probe_600["soil_ledger_closed"]),
        "plant_ledger_closed": bool(probe_600["plant_ledger_closed"]),
        "mixed_origin_preserved": bool(mixed["mixed_origin_preserved"]),
        "missing_ht_derived_proof_rejected": bool(
            mixed["missing_ht_derived_proof_rejected"]
        ),
        "soil_plant_superposition": superposition_residual
        <= max(1.0e-15, 1.0e-12 * superposition_scale),
    }

    implementation_gates = {
        "stage_module_present": STAGE in adapter,
        "source_hour_frozen": SOURCE_HOUR_SECONDS == 3600,
        "width_factor_frozen": AREA_SOURCE_SIGMA_WIDTH_FACTOR == 4.3,
        "eq44_solver_not_imported": "ufotri_empirical_soil_reemission" not in adapter,
        "depletion_factors_explicit": "fallout_factor" in adapter and "washout_factor" in adapter,
        "ground_level_fidelity_source_forbidden": "effective_height_m must be at least 1 m" in adapter,
    }

    contract_gates = {
        "manual": all(manual_gates.values()),
        "e3": all(e3_gates.values()),
        "historical": all(historical_gates.values()),
        "numerical": all(numerical_gates.values()),
        "implementation": all(implementation_gates.values()),
    }
    status = (
        "PASS_UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION"
        if all(contract_gates.values())
        else "FAIL_UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION"
    )
    return {
        "stage": STAGE,
        "status": status,
        "manual_gates": manual_gates,
        "e3_gates": e3_gates,
        "historical_gates": historical_gates,
        "numerical_gates": numerical_gates,
        "implementation_gates": implementation_gates,
        "contract_gates": contract_gates,
        "hourly_probe_dt600": probe_600,
        "hourly_probe_dt300": probe_300,
        "mixed_origin_probe": mixed,
        "decision": {
            "existing_default_source_changed": False,
            "opt_in_f1_adapter_added": True,
            "printed_manual_eq5_eq6_compatibility_added": True,
            "legacy_rectangular_quadrature_promoted_to_original_ufotri": False,
            "eq44_rate_generation_recovered": False,
            "real_cteas_atmos_bound": False,
            "benchmark_started": False,
        },
        "scope_claim": "OPT_IN_PRINTED_MANUAL_COMPATIBILITY_ADAPTER_ONLY",
        "empirical_validation": False,
        "physical_accuracy_claim": False,
        "production_readiness_claim": False,
        "original_executable_equivalence": False,
    }


def main() -> int:
    result = build_result()
    print(f"F1_RECONCILIATION_STATUS={result['status']}")
    print("F1_RECONCILIATION_RESULT_JSON=" + json.dumps(result, sort_keys=True))
    return 0 if result["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())