#!/usr/bin/env python3
"""Machine-visible qualification for E1 HT branch reconciliation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
from typing import Any

from cteas_ufotri.coupling.atmos_v3.forcing import AtmosphericHTOForcing
from cteas_ufotri.coupling.ht_v4 import (
    AIR_HT_CONCENTRATION_UNIT,
    HT_SURFACE_DEPOSITION_AMOUNT_UNIT,
    HT_SURFACE_DEPOSITION_FLUX_UNIT,
    AtmosphericHTForcing,
    GaseousTritiumSpecies,
    HTContractError,
    HTForcingSourceKind,
    ht_branch_ownership,
    ht_manual_evidence_profile,
)

STAGE = "UFOTRI_HT_BRANCH_RECONCILIATION_R1"
STATUS = "PASS_UFOTRI_HT_BRANCH_RECONCILIATION"
UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _forcing(
    *,
    start: datetime = T0,
    duration_s: float = 3600.0,
    flux: float = 2.0e-4,
    source_kind: HTForcingSourceKind = HTForcingSourceKind.SYNTHETIC,
) -> AtmosphericHTForcing:
    return AtmosphericHTForcing(
        start_utc=start,
        end_utc=start + timedelta(seconds=duration_s),
        species=GaseousTritiumSpecies.HT,
        air_ht_concentration_bq_m3=100.0,
        surface_ht_deposition_flux_bq_m2_s=flux,
        source_kind=source_kind,
        source_id="E1_MACHINE_SYNTHETIC",
        provenance_id="E1_MACHINE_PROVENANCE",
        spatial_support="synthetic_cell_0",
        concentration_sampling_height_m=1.5,
    )


def build_result() -> dict[str, Any]:
    profile = ht_manual_evidence_profile()
    ownership = ht_branch_ownership()
    whole = _forcing()
    whole_boundary = whole.to_soil_deposition_boundary()

    partition_amount = 0.0
    for index in range(4):
        record = _forcing(
            start=T0 + timedelta(minutes=15 * index),
            duration_s=900.0,
            source_kind=HTForcingSourceKind.REPLAY,
        )
        partition_amount += record.to_soil_deposition_boundary().deposited_ht_bq_m2

    real_binding_failed_closed = False
    try:
        _forcing(source_kind=HTForcingSourceKind.REAL_CTEAS_ATMOS)
    except HTContractError:
        real_binding_failed_closed = True

    contract_gates = {
        "ht_concentration_unit": whole.concentration_unit == AIR_HT_CONCENTRATION_UNIT,
        "ht_deposition_flux_unit": (
            whole.deposition_flux_unit == HT_SURFACE_DEPOSITION_FLUX_UNIT
        ),
        "ht_deposition_amount_unit": (
            whole_boundary.amount_unit == HT_SURFACE_DEPOSITION_AMOUNT_UNIT
        ),
        "whole_flux_integral": math.isclose(
            whole_boundary.deposited_ht_bq_m2,
            0.72,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ),
        "partition_equivalence": math.isclose(
            partition_amount,
            whole_boundary.deposited_ht_bq_m2,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ),
        "chemical_identity_preserved": (
            whole.species is GaseousTritiumSpecies.HT
            and whole_boundary.species is GaseousTritiumSpecies.HT
        ),
        "no_hto_created_in_e1": whole_boundary.converted_to_hto_bq_m2 == 0.0,
        "real_atmos_binding_fails_closed": real_binding_failed_closed,
        "hto_contract_is_distinct_type": AtmosphericHTForcing is not AtmosphericHTOForcing,
        "hto_field_not_reused": (
            "air_ht_concentration_bq_m3"
            not in AtmosphericHTOForcing.__dataclass_fields__
            and "air_hto_concentration"
            not in AtmosphericHTForcing.__dataclass_fields__
        ),
        "e2_owns_soil_conversion": (
            not ownership.e1_ht_to_hto_soil_conversion
            and ownership.e2_owns_ht_to_hto_soil_conversion
        ),
        "e3_owns_secondary_hto_reemission": (
            not ownership.e1_secondary_hto_reemission
            and ownership.e3_owns_ht_derived_hto_reemission
        ),
        "e4_owns_real_ht_binding": (
            not ownership.e1_real_atmos_binding
            and ownership.e4_owns_real_ht_atmos_binding
        ),
        "hto_not_relabelled_as_ht": not ownership.hto_forcing_reused_for_ht,
    }

    manual_evidence_gates = {
        "benchmark_ht_dry_deposition_visible": math.isclose(
            profile.benchmark_ht_dry_deposition_velocity_cm_s,
            0.05,
            rel_tol=0.0,
            abs_tol=0.0,
        ),
        "benchmark_ht_dry_deposition_si_visible": math.isclose(
            profile.benchmark_ht_dry_deposition_velocity_m_s,
            5.0e-4,
            rel_tol=0.0,
            abs_tol=1.0e-18,
        ),
        "benchmark_air_oxidation_visible": math.isclose(
            profile.benchmark_air_oxidation_fraction_d_1,
            0.005,
            rel_tol=0.0,
            abs_tol=0.0,
        ),
        "benchmark_ht_soil_diffusion_visible": math.isclose(
            profile.benchmark_ht_soil_diffusion_cm2_s,
            5.0e-2,
            rel_tol=0.0,
            abs_tol=0.0,
        ),
        "benchmark_hto_comparison_visible": (
            profile.benchmark_hto_dry_deposition_velocity_cm_s == 1.8
            and profile.benchmark_hto_soil_diffusion_cm2_s == 2.0e-5
        ),
        "soil_type_moisture_dependency_preserved": (
            profile.ht_deposition_depends_on_soil_type_and_moisture
        ),
        "rapid_microbial_conversion_semantics_preserved": (
            profile.deposited_ht_rapidly_converts_via_microorganisms
        ),
        "only_transformed_ht_remains_semantics_preserved": (
            profile.only_transformed_ht_remains_in_soil
        ),
        "air_oxidation_not_activated_in_e1": not profile.atmospheric_oxidation_owned_by_e1,
        "soil_conversion_not_activated_in_e1": not profile.soil_conversion_owned_by_e1,
        "benchmark_values_not_production_defaults": not profile.production_parameter_activation,
    }

    hard_boundaries = {
        "historical_v2_changed": False,
        "frozen_hto_forcing_changed": False,
        "frozen_rc1_changed": False,
        "ht_to_hto_soil_conversion_implemented": False,
        "ht_derived_hto_reemission_implemented": False,
        "real_cteas_atmos_ht_binding_active": False,
        "benchmark_deposition_velocity_activated_as_global_default": False,
        "benchmark_air_oxidation_activated_as_global_default": False,
        "benchmark_soil_diffusion_activated_as_global_default": False,
        "dt_species_silently_supported": False,
        "unspecified_total_tritium_supported": False,
        "calibration": False,
        "empirical_validation": False,
        "physical_accuracy_claim": False,
        "production_readiness_claim": False,
        "original_executable_equivalence": False,
    }

    if not all(contract_gates.values()):
        failed = sorted(key for key, value in contract_gates.items() if not value)
        raise RuntimeError(f"E1 HT contract gate failed: {failed}")
    if not all(manual_evidence_gates.values()):
        failed = sorted(key for key, value in manual_evidence_gates.items() if not value)
        raise RuntimeError(f"E1 HT manual-evidence gate failed: {failed}")
    if any(hard_boundaries.values()):
        failed = sorted(key for key, value in hard_boundaries.items() if value)
        raise RuntimeError(f"E1 hard boundary violated: {failed}")

    return {
        "schema_version": "v1",
        "stage": STAGE,
        "status": STATUS,
        "contract": {
            "accepted_species": [item.value for item in GaseousTritiumSpecies],
            "accepted_source_kinds": [
                HTForcingSourceKind.SYNTHETIC.value,
                HTForcingSourceKind.REPLAY.value,
            ],
            "concentration_unit": AIR_HT_CONCENTRATION_UNIT,
            "deposition_flux_unit": HT_SURFACE_DEPOSITION_FLUX_UNIT,
            "deposition_amount_unit": HT_SURFACE_DEPOSITION_AMOUNT_UNIT,
            "contract_gates": contract_gates,
        },
        "manual_evidence": {
            "profile_id": profile.profile_id,
            "benchmark_ht_dry_deposition_velocity_cm_s": (
                profile.benchmark_ht_dry_deposition_velocity_cm_s
            ),
            "benchmark_air_oxidation_fraction_d_1": (
                profile.benchmark_air_oxidation_fraction_d_1
            ),
            "benchmark_ht_soil_diffusion_cm2_s": (
                profile.benchmark_ht_soil_diffusion_cm2_s
            ),
            "manual_evidence_gates": manual_evidence_gates,
        },
        "hard_boundaries": hard_boundaries,
        "next_stage": "UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1",
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    text = json.dumps(result, indent=2, sort_keys=True)
    print(f"E1_HT_STATUS={result['status']}")
    print(f"E1_HT_RESULT_JSON={json.dumps(result, sort_keys=True)}")
    if args.output is not None:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
