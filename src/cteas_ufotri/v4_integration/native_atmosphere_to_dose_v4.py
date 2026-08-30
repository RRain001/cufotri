"""H5 composition boundary from reconciled UFOTRI-native atmosphere to V4 replay.

This module does not add a second environmental solver.  It composes the
already-qualified H3 native forcing adapters, E2 HT->HTO soil conversion and
V4 replay-input orchestrator contract.

The HTO air concentration remains the native HTO concentration (plus an
explicitly routed secondary-air contribution when supplied).  The soil surface
HTO input is the sum of primary HTO deposition and HT-derived HTO produced by
the already-qualified E2 1:1 activity conversion.  The two deposition origins
remain visible in the returned sidecar ledger even though the existing soil
state stores one aggregate HTO inventory.

No atmospheric HT->HTO conversion, source-loss-to-local-wet-flux inference,
production parameter activation, calibration, or CTEAS-Atmos binding occurs
here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math

from cteas_ufotri.atmosphere.ufotri_native_v4 import (
    NativePrimaryTransportResult,
    TritiumAtmosphericForm,
)
from cteas_ufotri.coupling.ht_v4 import GaseousTritiumSpecies
from cteas_ufotri.coupling.ufotri_native_atmos_forcing_v4 import (
    NativeForcingContext,
    NativeHTForcingAdaptation,
    NativeHTOForcingAdaptation,
    adapt_native_ht_forcing,
    adapt_native_hto_forcing,
)

from .replay_input_orchestration import V4ReplayIntervalInput


class NativeAtmosphereToDoseQualificationError(ValueError):
    """Fail-closed H5 composition error."""


def _finite(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NativeAtmosphereToDoseQualificationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise NativeAtmosphereToDoseQualificationError(f"{field} must be finite")
    return result


def _nonnegative(value: float, *, field: str) -> float:
    result = _finite(value, field=field)
    if result < 0.0:
        raise NativeAtmosphereToDoseQualificationError(f"{field} must be non-negative")
    return result


def _closed(value: float, *, field: str, scale: float) -> None:
    tolerance = 1.0e-12 * max(1.0, abs(scale))
    if abs(value) > tolerance:
        raise NativeAtmosphereToDoseQualificationError(
            f"{field} failed closure: residual={value}"
        )


@dataclass(frozen=True)
class NativeAtmosphereReplayLedger:
    """Origin-preserving H5 sidecar for the aggregate replay forcing."""

    primary_hto_surface_flux_bq_m2_s: float
    ht_derived_hto_surface_flux_bq_m2_s: float
    combined_hto_surface_flux_bq_m2_s: float
    primary_hto_air_bq_m3: float
    secondary_hto_air_bq_m3: float
    combined_hto_air_bq_m3: float
    hto_source_depletion_residual_bq_s: float
    ht_source_depletion_residual_bq_s: float
    e2_activity_residual_bq_m2: float
    atmospheric_ht_to_hto_generated_bq_s: float
    wet_source_to_local_surface_spatial_closure_claimed: bool = False

    def __post_init__(self) -> None:
        primary_flux = _nonnegative(
            self.primary_hto_surface_flux_bq_m2_s,
            field="primary_hto_surface_flux_bq_m2_s",
        )
        derived_flux = _nonnegative(
            self.ht_derived_hto_surface_flux_bq_m2_s,
            field="ht_derived_hto_surface_flux_bq_m2_s",
        )
        combined_flux = _nonnegative(
            self.combined_hto_surface_flux_bq_m2_s,
            field="combined_hto_surface_flux_bq_m2_s",
        )
        primary_air = _nonnegative(
            self.primary_hto_air_bq_m3,
            field="primary_hto_air_bq_m3",
        )
        secondary_air = _nonnegative(
            self.secondary_hto_air_bq_m3,
            field="secondary_hto_air_bq_m3",
        )
        combined_air = _nonnegative(
            self.combined_hto_air_bq_m3,
            field="combined_hto_air_bq_m3",
        )
        _closed(
            combined_flux - primary_flux - derived_flux,
            field="combined HTO surface flux",
            scale=combined_flux,
        )
        _closed(
            combined_air - primary_air - secondary_air,
            field="combined HTO air concentration",
            scale=combined_air,
        )
        _closed(
            _finite(
                self.hto_source_depletion_residual_bq_s,
                field="hto_source_depletion_residual_bq_s",
            ),
            field="HTO source depletion",
            scale=1.0,
        )
        _closed(
            _finite(
                self.ht_source_depletion_residual_bq_s,
                field="ht_source_depletion_residual_bq_s",
            ),
            field="HT source depletion",
            scale=1.0,
        )
        _closed(
            _finite(
                self.e2_activity_residual_bq_m2,
                field="e2_activity_residual_bq_m2",
            ),
            field="E2 activity",
            scale=1.0,
        )
        generated = _nonnegative(
            self.atmospheric_ht_to_hto_generated_bq_s,
            field="atmospheric_ht_to_hto_generated_bq_s",
        )
        if generated != 0.0:
            raise NativeAtmosphereToDoseQualificationError(
                "KfK 4605 fidelity route must keep atmospheric HT->HTO disabled"
            )
        if self.wet_source_to_local_surface_spatial_closure_claimed:
            raise NativeAtmosphereToDoseQualificationError(
                "H5 must not claim plume wet-source loss equals one local surface flux"
            )


@dataclass(frozen=True)
class NativeAtmosphereReplayComposition:
    """H5 native-atmosphere composition ready for the existing replay orchestrator."""

    replay_input: V4ReplayIntervalInput
    hto_adaptation: NativeHTOForcingAdaptation
    ht_adaptation: NativeHTForcingAdaptation | None
    ledger: NativeAtmosphereReplayLedger

    def __post_init__(self) -> None:
        if not isinstance(self.replay_input, V4ReplayIntervalInput):
            raise NativeAtmosphereToDoseQualificationError(
                "replay_input must be V4ReplayIntervalInput"
            )
        if not isinstance(self.hto_adaptation, NativeHTOForcingAdaptation):
            raise NativeAtmosphereToDoseQualificationError(
                "hto_adaptation must be NativeHTOForcingAdaptation"
            )
        if self.ht_adaptation is not None and not isinstance(
            self.ht_adaptation, NativeHTForcingAdaptation
        ):
            raise NativeAtmosphereToDoseQualificationError(
                "ht_adaptation must be NativeHTForcingAdaptation or None"
            )


def compose_native_atmosphere_replay_input(
    *,
    template: V4ReplayIntervalInput,
    native_hto_result: NativePrimaryTransportResult,
    context: NativeForcingContext,
    native_ht_result: NativePrimaryTransportResult | None = None,
    gaseous_ht_species: GaseousTritiumSpecies = GaseousTritiumSpecies.HT,
    wet_surface_deposition_flux_bq_m2_s: float | None = None,
    secondary_hto_air_bq_m3: float = 0.0,
) -> NativeAtmosphereReplayComposition:
    """Compose native HT/HTO into the existing V4 replay-input contract.

    ``template`` supplies only the already-reviewed non-atmospheric ownership:
    soil external transport/re-emission, explicit root water uptake,
    biological forcing, resistance and their independent provenance.

    Native HTO owns atmospheric concentration and primary HTO deposition.
    Native HT, when present, is converted through H3->E2 and contributes only
    its generated soil-HTO surface flux.  It never contributes to atmospheric
    HTO concentration.

    ``secondary_hto_air_bq_m3`` is an already-routed F1 secondary atmospheric
    concentration.  Supplying it adds concentration only; it creates no new
    environmental inventory term and no implicit deposition flux.
    """

    if not isinstance(template, V4ReplayIntervalInput):
        raise NativeAtmosphereToDoseQualificationError(
            "template must be V4ReplayIntervalInput"
        )
    if not isinstance(context, NativeForcingContext):
        raise NativeAtmosphereToDoseQualificationError(
            "context must be NativeForcingContext"
        )
    if native_hto_result.species is not TritiumAtmosphericForm.HTO:
        raise NativeAtmosphereToDoseQualificationError(
            "native_hto_result must be chemically HTO"
        )
    if template.interval_start != context.start_utc or template.interval_end != context.end_utc:
        raise NativeAtmosphereToDoseQualificationError(
            "template interval must exactly match NativeForcingContext"
        )
    if template.spatial_reference != context.spatial_support:
        raise NativeAtmosphereToDoseQualificationError(
            "template spatial support must match NativeForcingContext"
        )

    secondary_air = _nonnegative(
        secondary_hto_air_bq_m3,
        field="secondary_hto_air_bq_m3",
    )
    hto = adapt_native_hto_forcing(
        result=native_hto_result,
        context=context,
        wet_surface_deposition_flux_bq_m2_s=wet_surface_deposition_flux_bq_m2_s,
    )

    ht: NativeHTForcingAdaptation | None = None
    derived_flux = 0.0
    ht_residual = 0.0
    e2_residual = 0.0
    generated_atmospheric_hto = native_hto_result.atmospheric_ht_to_hto_generated_bq_s
    if native_ht_result is not None:
        if native_ht_result.species is not TritiumAtmosphericForm.HT:
            raise NativeAtmosphereToDoseQualificationError(
                "native_ht_result must be chemically HT"
            )
        ht = adapt_native_ht_forcing(
            result=native_ht_result,
            context=context,
            gaseous_species=gaseous_ht_species,
        )
        derived_flux = ht.soil_conversion.generated_hto_flux_bq_m2_s
        ht_residual = native_ht_result.source_depletion_residual_bq_s
        e2_residual = ht.soil_conversion.ledger.activity_residual_bq_m2
        generated_atmospheric_hto += (
            native_ht_result.atmospheric_ht_to_hto_generated_bq_s
        )

    primary_flux = hto.forcing.deposition_flux
    combined_flux = primary_flux + derived_flux
    primary_air = hto.forcing.air_hto_concentration
    combined_air = primary_air + secondary_air
    combined_forcing = replace(
        hto.forcing,
        air_hto_concentration=combined_air,
        air_ht0_concentration=combined_air,
        deposition_flux=combined_flux,
    )
    replay_input = replace(template, atmospheric_forcing=combined_forcing)
    ledger = NativeAtmosphereReplayLedger(
        primary_hto_surface_flux_bq_m2_s=primary_flux,
        ht_derived_hto_surface_flux_bq_m2_s=derived_flux,
        combined_hto_surface_flux_bq_m2_s=combined_flux,
        primary_hto_air_bq_m3=primary_air,
        secondary_hto_air_bq_m3=secondary_air,
        combined_hto_air_bq_m3=combined_air,
        hto_source_depletion_residual_bq_s=(
            native_hto_result.source_depletion_residual_bq_s
        ),
        ht_source_depletion_residual_bq_s=ht_residual,
        e2_activity_residual_bq_m2=e2_residual,
        atmospheric_ht_to_hto_generated_bq_s=generated_atmospheric_hto,
        wet_source_to_local_surface_spatial_closure_claimed=False,
    )
    return NativeAtmosphereReplayComposition(
        replay_input=replay_input,
        hto_adaptation=hto,
        ht_adaptation=ht,
        ledger=ledger,
    )


__all__ = [
    "NativeAtmosphereReplayComposition",
    "NativeAtmosphereReplayLedger",
    "NativeAtmosphereToDoseQualificationError",
    "compose_native_atmosphere_replay_input",
]
