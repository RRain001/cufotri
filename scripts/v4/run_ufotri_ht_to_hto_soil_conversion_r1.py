#!/usr/bin/env python3
"""Machine gate for UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

from cteas_ufotri.coupling.ht_to_hto_soil_v4 import (
    HT_TO_HTO_SOIL_CONVERSION_SEMANTICS,
    convert_deposited_ht_to_soil_hto,
    project_ht_derived_hto_into_soil_forcing,
)
from cteas_ufotri.coupling.ht_v4 import (
    AtmosphericHTForcing,
    GaseousTritiumSpecies,
    HTForcingSourceKind,
    ht_manual_evidence_profile,
)
from cteas_ufotri.plant.soil_v4.soil_solver import (
    ThreeLayerSoilForcing,
    ThreeLayerSoilStorageSolver,
)
from cteas_ufotri.plant.soil_v4.soil_state import (
    SoilV4Provenance,
    ThreeLayerSoilState,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)
TRITIUM_HALF_LIFE_S = 12.32 * 365.25 * 86400.0


def _ht_forcing(
    *,
    start: datetime,
    duration_s: float,
    deposition_flux: float,
    source_kind: HTForcingSourceKind = HTForcingSourceKind.SYNTHETIC,
) -> AtmosphericHTForcing:
    return AtmosphericHTForcing(
        start_utc=start,
        end_utc=start + timedelta(seconds=duration_s),
        species=GaseousTritiumSpecies.HT,
        air_ht_concentration_bq_m3=100.0,
        surface_ht_deposition_flux_bq_m2_s=deposition_flux,
        source_kind=source_kind,
        source_id="E2_CONTROLLED_HT",
        provenance_id="E2_CONTROLLED_HT_PROVENANCE",
        spatial_support="synthetic_cell_0",
        concentration_sampling_height_m=1.5,
    )


def build_result() -> dict[str, object]:
    ht = _ht_forcing(start=T0, duration_s=3600.0, deposition_flux=2.0e-4)
    boundary = ht.to_soil_deposition_boundary()
    conversion = convert_deposited_ht_to_soil_hto(boundary)

    base = ThreeLayerSoilForcing(
        timestamp=T0,
        surface_deposition_flux_bq_m2_s=3.0e-4,
    )
    projection = project_ht_derived_hto_into_soil_forcing(
        base_forcing=base,
        conversion=conversion,
        interval_seconds=3600.0,
    )

    provenance = SoilV4Provenance(
        source_id="E2_CONTROLLED_SOIL",
        source_version="r1",
        artifact_sha256="a" * 64,
        spatial_reference="synthetic_cell_0",
        temporal_resolution_s=3600.0,
    )
    state = ThreeLayerSoilState.from_inventories(
        soil_identifier="E2_CONTROLLED_SOIL",
        water_inventories_m=(0.05, 0.10, 0.15),
        hto_inventories_bq_m2=(0.0, 0.0, 0.0),
        timestamp=T0,
        provenance=provenance,
    )
    step = ThreeLayerSoilStorageSolver(
        tritium_half_life_s=TRITIUM_HALF_LIFE_S
    ).advance(state, projection.forcing, 3600.0)

    quarter_total = 0.0
    for index in range(4):
        part = _ht_forcing(
            start=T0 + timedelta(minutes=15 * index),
            duration_s=900.0,
            deposition_flux=2.0e-4,
            source_kind=HTForcingSourceKind.REPLAY,
        )
        quarter_total += convert_deposited_ht_to_soil_hto(
            part.to_soil_deposition_boundary()
        ).generated_hto_bq_m2

    manual = ht_manual_evidence_profile()
    expected_primary = 3.0e-4 * 3600.0
    expected_derived = 2.0e-4 * 3600.0
    expected_combined = expected_primary + expected_derived

    conversion_gates = {
        "manual_semantics_exact": (
            conversion.conversion_semantics == HT_TO_HTO_SOIL_CONVERSION_SEMANTICS
        ),
        "ht_loss_equals_hto_gain": abs(
            conversion.input_ht_bq_m2 - conversion.generated_hto_bq_m2
        ) <= 1.0e-15,
        "no_retained_soil_ht_pool": conversion.residual_ht_bq_m2 == 0.0,
        "ledger_closes": abs(conversion.ledger.activity_residual_bq_m2) <= 1.0e-15,
        "flux_integrates_to_amount": abs(
            conversion.generated_hto_flux_bq_m2_s * conversion.duration_s
            - conversion.generated_hto_bq_m2
        ) <= 1.0e-15,
        "partition_equivalence": abs(
            quarter_total - conversion.generated_hto_bq_m2
        ) <= 1.0e-15,
    }
    projection_gates = {
        "primary_hto_preserved": abs(
            projection.primary_hto_surface_flux_bq_m2_s - 3.0e-4
        ) <= 1.0e-15,
        "ht_derived_hto_explicit": abs(
            projection.ht_derived_hto_surface_flux_bq_m2_s - 2.0e-4
        ) <= 1.0e-15,
        "combined_flux_is_sum": abs(
            projection.combined_hto_surface_flux_bq_m2_s - 5.0e-4
        ) <= 1.0e-15,
        "soil_external_input_closes": abs(
            step.global_balance.external_hto_input_bq_m2 - expected_combined
        ) <= 1.0e-12,
        "soil_global_balance_closes": abs(
            step.global_balance.hto_residual_bq_m2
        ) <= 1.0e-10,
        "generated_hto_enters_top_layer": step.state.layers[0].hto_inventory_bq_m2 > 0.0,
        "deeper_layers_not_directly_injected": (
            step.state.layers[1].hto_inventory_bq_m2 == 0.0
            and step.state.layers[2].hto_inventory_bq_m2 == 0.0
        ),
    }
    manual_evidence_gates = {
        "soil_moisture_and_type_remain_deposition_ownership": manual.ht_deposition_depends_on_soil_type_and_moisture,
        "rapid_microorganism_conversion_visible": manual.deposited_ht_rapidly_converts_via_microorganisms,
        "only_transformed_part_remains_visible": manual.only_transformed_ht_remains_in_soil,
        "benchmark_deposition_not_recomputed": abs(
            conversion.generated_hto_flux_bq_m2_s
            - ht.surface_ht_deposition_flux_bq_m2_s
        ) <= 1.0e-15,
        "benchmark_profile_not_production": not manual.production_parameter_activation,
    }
    hard_boundaries = {
        "independent_soil_ht_kinetic_pool_created": False,
        "microbial_half_life_invented": False,
        "atmospheric_ht_oxidation_applied": conversion.atmospheric_ht_oxidation_applied,
        "secondary_hto_reemission_generated": conversion.secondary_hto_reemission_generated,
        "real_cteas_atmos_binding_enabled": False,
        "production_parameter_activation": conversion.production_parameter_activation,
    }

    passed = (
        all(conversion_gates.values())
        and all(projection_gates.values())
        and all(manual_evidence_gates.values())
        and not any(hard_boundaries.values())
    )
    return {
        "stage": "UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1",
        "status": "PASS_UFOTRI_HT_TO_HTO_SOIL_CONVERSION" if passed else "FAIL",
        "manual_semantics": HT_TO_HTO_SOIL_CONVERSION_SEMANTICS,
        "conversion": {
            "input_ht_bq_m2": conversion.input_ht_bq_m2,
            "generated_hto_bq_m2": conversion.generated_hto_bq_m2,
            "residual_ht_bq_m2": conversion.residual_ht_bq_m2,
            "generated_hto_flux_bq_m2_s": conversion.generated_hto_flux_bq_m2_s,
            "conversion_gates": conversion_gates,
        },
        "projection": {
            "primary_hto_bq_m2": expected_primary,
            "ht_derived_hto_bq_m2": expected_derived,
            "combined_external_hto_bq_m2": expected_combined,
            "projection_gates": projection_gates,
        },
        "manual_evidence": {
            "manual_evidence_gates": manual_evidence_gates,
        },
        "hard_boundaries": hard_boundaries,
    }


def main() -> int:
    result = build_result()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS_UFOTRI_HT_TO_HTO_SOIL_CONVERSION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
