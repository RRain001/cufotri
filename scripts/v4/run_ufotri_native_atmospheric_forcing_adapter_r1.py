#!/usr/bin/env python3
"""Machine-readable qualification for UFOTRI H3 native forcing adapters."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from cteas_ufotri.atmosphere.ufotri_native_v4 import (
    NativeSpeciesPolicy,
    TritiumAtmosphericForm,
    kfk4605_iter_benchmark_policy,
    transport_straight_segment,
)
from cteas_ufotri.coupling.ht_v4 import GaseousTritiumSpecies, HTForcingSourceKind
from cteas_ufotri.coupling.ufotri_native_atmos_forcing_v4 import (
    NativeForcingContext,
    adapt_native_ht_forcing,
    adapt_native_hto_forcing,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _context() -> NativeForcingContext:
    return NativeForcingContext(
        start_utc=T0,
        end_utc=T0 + timedelta(hours=1),
        source_id="H3_NATIVE_MACHINE_GATE",
        provenance_id="H3_NATIVE_MACHINE_GATE_PROVENANCE",
        source_version="h3-r1",
        artifact_sha256="a" * 64,
        spatial_support="source-relative-receptor-1000m-centreline",
        concentration_sampling_height_m=1.0,
        air_temperature_k=283.15,
        relative_humidity=0.7,
        wind_speed_m_s=5.0,
        precipitation_m_s=0.0,
        creation_time_utc=T0,
    )


def _transport(policy: NativeSpeciesPolicy):
    return transport_straight_segment(
        source_bq_s=1.0e8,
        downwind_m=1000.0,
        crosswind_m=0.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        receptor_height_m=1.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=policy,
    )


def build_result() -> dict[str, object]:
    context = _context()
    ht_native = _transport(kfk4605_iter_benchmark_policy(TritiumAtmosphericForm.HT))
    ht = adapt_native_ht_forcing(
        result=ht_native,
        context=context,
        gaseous_species=GaseousTritiumSpecies.HT,
    )

    hto_dry_native = _transport(
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HTO,
            dry_deposition_velocity_m_s=1.8e-2,
        )
    )
    hto_dry = adapt_native_hto_forcing(result=hto_dry_native, context=context)

    hto_wet_native = _transport(
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HTO,
            dry_deposition_velocity_m_s=1.8e-2,
            hto_washout_coefficient_s_1=1.0e-4,
        )
    )
    explicit_wet_flux = 2.5e-4
    hto_wet = adapt_native_hto_forcing(
        result=hto_wet_native,
        context=context,
        wet_surface_deposition_flux_bq_m2_s=explicit_wet_flux,
    )

    checks = {
        "ht_source_kind_is_ufotri_native": (
            ht.forcing.source_kind is HTForcingSourceKind.UFOTRI_NATIVE
        ),
        "ht_concentration_identity": (
            ht.forcing.air_ht_concentration_bq_m3 == ht_native.air_concentration_bq_m3
        ),
        "ht_surface_flux_identity": (
            ht.forcing.surface_ht_deposition_flux_bq_m2_s
            == ht_native.dry_surface_flux_bq_m2_s
        ),
        "ht_e1_to_e2_activity_closes": (
            ht.soil_boundary.deposited_ht_bq_m2
            == ht.soil_conversion.generated_hto_bq_m2
            and ht.soil_conversion.ledger.activity_residual_bq_m2 == 0.0
        ),
        "hto_concentration_identity": (
            hto_dry.forcing.air_hto_concentration
            == hto_dry_native.air_concentration_bq_m3
        ),
        "hto_dry_flux_identity": (
            hto_dry.forcing.deposition_flux
            == hto_dry_native.dry_surface_flux_bq_m2_s
        ),
        "hto_explicit_wet_flux_is_added_once": (
            hto_wet.forcing.deposition_flux
            == hto_wet_native.dry_surface_flux_bq_m2_s + explicit_wet_flux
        ),
        "hto_wet_source_loss_not_claimed_as_local_flux": (
            hto_wet.native_wet_source_loss_bq_s > 0.0
            and not hto_wet.wet_source_to_surface_spatial_closure_claimed
        ),
        "no_atmospheric_ht_to_hto_aliasing": (
            ht_native.atmospheric_ht_to_hto_generated_bq_s == 0.0
            and hto_dry_native.atmospheric_ht_to_hto_generated_bq_s == 0.0
        ),
        "interval_and_spatial_provenance_preserved": (
            ht.forcing.start_utc == context.start_utc
            and ht.forcing.end_utc == context.end_utc
            and ht.forcing.spatial_support == context.spatial_support
            and hto_dry.forcing.timestamp == context.start_utc
            and hto_dry.forcing.provenance.spatial_reference == context.spatial_support
            and hto_dry.forcing.provenance.temporal_resolution_s
            == context.interval_seconds
        ),
        "adapter_ledgers_close": (
            ht.ledger.mapped_air_concentration_bq_m3
            == ht.ledger.native_air_concentration_bq_m3
            and hto_wet.ledger.mapped_total_surface_flux_bq_m2_s
            == hto_wet.ledger.native_dry_surface_flux_bq_m2_s
            + hto_wet.ledger.explicit_wet_surface_flux_bq_m2_s
        ),
    }
    forbidden_claims = {
        "cteas_atmos_binding": False,
        "h4_washout_parameter_recovery": False,
        "building_wake_reconciliation": False,
        "thermal_lift_reconciliation": False,
        "production_parameter_activation": False,
        "original_musemet_numerical_equivalence": False,
        "wet_source_loss_relabelled_as_surface_flux": False,
    }
    status = (
        "PASS_UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER"
        if all(checks.values()) and not any(forbidden_claims.values())
        else "FAIL_UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER"
    )
    return {
        "stage": "UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1",
        "status": status,
        "checks": checks,
        "forbidden_claims": forbidden_claims,
        "ht": {
            "air_concentration_bq_m3": ht.forcing.air_ht_concentration_bq_m3,
            "surface_flux_bq_m2_s": ht.forcing.surface_ht_deposition_flux_bq_m2_s,
            "deposited_ht_bq_m2": ht.soil_boundary.deposited_ht_bq_m2,
            "generated_soil_hto_bq_m2": ht.soil_conversion.generated_hto_bq_m2,
        },
        "hto": {
            "dry_only_surface_flux_bq_m2_s": hto_dry.forcing.deposition_flux,
            "wet_case_native_source_loss_bq_s": hto_wet.native_wet_source_loss_bq_s,
            "wet_case_explicit_surface_flux_bq_m2_s": explicit_wet_flux,
            "wet_case_total_surface_flux_bq_m2_s": hto_wet.forcing.deposition_flux,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(text + "\n", encoding="utf-8")
    print("H3_NATIVE_FORCING_ADAPTER_STATUS=" + str(result["status"]))
    print(text)
    return 0 if str(result["status"]).startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
