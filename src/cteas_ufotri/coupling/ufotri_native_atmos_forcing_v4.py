"""UFOTRI-native atmosphere -> environmental forcing adapters (H3).

This module is an opt-in coupling boundary between the reconstructed native
MUSEMET/Gaussian atmosphere and the already-reviewed environmental contracts.
It does not implement atmospheric dispersion, washout physics, building wake,
plume rise, soil chemistry, or CTEAS-Atmos binding.

The adapter keeps HT and HTO chemically distinct:

* native HT -> E1 ``AtmosphericHTForcing`` with ``UFOTRI_NATIVE`` provenance;
* native HT dry deposition -> E1 soil boundary -> existing E2 HT->HTO
  conversion;
* native HTO -> existing P7 ``AtmosphericHTOForcing``;
* native HTO wet source loss is never relabelled as a surface flux.  If the
  native transport reports wet source loss, an independently resolved local
  wet-deposition surface flux must be supplied explicitly or the adapter fails
  closed.

All conversions here are identity mappings of already-computed physical
quantities.  No production parameter is selected or activated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math

from cteas_ufotri.atmosphere.ufotri_native_v4 import (
    NativePrimaryTransportResult,
    TritiumAtmosphericForm,
)
from cteas_ufotri.coupling.atmos_v3.forcing import AtmosphericHTOForcing
from cteas_ufotri.coupling.atmos_v3.metadata import AtmosphericForcingMetadata
from cteas_ufotri.coupling.ht_to_hto_soil_v4 import (
    HTToHTOSoilConversionResult,
    convert_deposited_ht_to_soil_hto,
)
from cteas_ufotri.coupling.ht_v4 import (
    AtmosphericHTForcing,
    GaseousTritiumSpecies,
    HTForcingSourceKind,
    HTSoilDepositionBoundary,
)
from cteas_ufotri.plant.leaf_exchange_resistance.types import ForcingProvenance

UFOTRI_NATIVE_SOURCE_KIND = "UFOTRI_NATIVE"
UFOTRI_NATIVE_MODEL_NAME = "UFOTRI_NATIVE_MUSEMET_GAUSSIAN"
UFOTRI_NATIVE_ADAPTER_VERSION = "h3-r1"


class UFOTRINativeForcingAdapterError(ValueError):
    """Fail-closed error for H3 native atmospheric forcing adaptation."""


def _finite(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UFOTRINativeForcingAdapterError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise UFOTRINativeForcingAdapterError(f"{field} must be finite")
    return result


def _nonnegative(value: float, *, field: str) -> float:
    result = _finite(value, field=field)
    if result < 0.0:
        raise UFOTRINativeForcingAdapterError(f"{field} must be non-negative")
    return result


def _required_text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UFOTRINativeForcingAdapterError(f"{field} is required")
    return value.strip()


def _utc(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise UFOTRINativeForcingAdapterError(f"{field} must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise UFOTRINativeForcingAdapterError(f"{field} must use UTC")
    return value.astimezone(timezone.utc)


def _closed(value: float, *, field: str, scale: float) -> None:
    tolerance = 1.0e-12 * max(1.0, abs(scale))
    if abs(value) > tolerance:
        raise UFOTRINativeForcingAdapterError(f"{field} must close; residual={value}")


@dataclass(frozen=True)
class NativeForcingContext:
    """Explicit interval, meteorology and provenance required by H3.

    H1/H2 do not own all fields required by the legacy HTO coupling contract
    (for example air temperature and relative humidity), so H3 requires those
    ancillary values explicitly instead of inventing them.
    """

    start_utc: datetime
    end_utc: datetime
    source_id: str
    provenance_id: str
    source_version: str
    artifact_sha256: str
    spatial_support: str
    concentration_sampling_height_m: float
    air_temperature_k: float
    relative_humidity: float
    wind_speed_m_s: float
    precipitation_m_s: float
    creation_time_utc: datetime
    quality_flag: str = "H3_NATIVE_ADAPTER"

    def __post_init__(self) -> None:
        start = _utc(self.start_utc, field="start_utc")
        end = _utc(self.end_utc, field="end_utc")
        creation = _utc(self.creation_time_utc, field="creation_time_utc")
        if end <= start:
            raise UFOTRINativeForcingAdapterError("end_utc must be later than start_utc")
        for field in (
            "source_id",
            "provenance_id",
            "source_version",
            "spatial_support",
            "quality_flag",
        ):
            _required_text(getattr(self, field), field=field)
        digest = _required_text(self.artifact_sha256, field="artifact_sha256")
        if len(digest) != 64 or any(c not in "0123456789abcdefABCDEF" for c in digest):
            raise UFOTRINativeForcingAdapterError("artifact_sha256 must be SHA-256 hex")
        _nonnegative(
            self.concentration_sampling_height_m,
            field="concentration_sampling_height_m",
        )
        if _finite(self.air_temperature_k, field="air_temperature_k") <= 0.0:
            raise UFOTRINativeForcingAdapterError("air_temperature_k must be positive")
        humidity = _finite(self.relative_humidity, field="relative_humidity")
        if not 0.0 <= humidity <= 1.0:
            raise UFOTRINativeForcingAdapterError("relative_humidity must be in [0, 1]")
        _nonnegative(self.wind_speed_m_s, field="wind_speed_m_s")
        _nonnegative(self.precipitation_m_s, field="precipitation_m_s")
        object.__setattr__(self, "start_utc", start)
        object.__setattr__(self, "end_utc", end)
        object.__setattr__(self, "creation_time_utc", creation)

    @property
    def interval_seconds(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds()

    @property
    def hto_provenance(self) -> ForcingProvenance:
        return ForcingProvenance(
            source_id=self.source_id,
            source_version=self.source_version,
            artifact_sha256=self.artifact_sha256,
            spatial_reference=self.spatial_support,
            temporal_resolution_s=self.interval_seconds,
        )

    @property
    def hto_metadata(self) -> AtmosphericForcingMetadata:
        return AtmosphericForcingMetadata(
            model_name=UFOTRI_NATIVE_MODEL_NAME,
            version=UFOTRI_NATIVE_ADAPTER_VERSION,
            grid_definition=self.spatial_support,
            time_resolution=self.interval_seconds,
            source_dataset=self.source_id,
            creation_time=self.creation_time_utc,
            quality_flag=self.quality_flag,
        )


@dataclass(frozen=True)
class NativeForcingAdapterLedger:
    """Identity-mapping and source-depletion ledger across the H3 boundary."""

    native_air_concentration_bq_m3: float
    mapped_air_concentration_bq_m3: float
    native_dry_surface_flux_bq_m2_s: float
    explicit_wet_surface_flux_bq_m2_s: float
    mapped_total_surface_flux_bq_m2_s: float
    native_source_depletion_residual_bq_s: float
    e2_activity_residual_bq_m2: float = 0.0

    def __post_init__(self) -> None:
        native_c = _nonnegative(
            self.native_air_concentration_bq_m3,
            field="native_air_concentration_bq_m3",
        )
        mapped_c = _nonnegative(
            self.mapped_air_concentration_bq_m3,
            field="mapped_air_concentration_bq_m3",
        )
        dry = _nonnegative(
            self.native_dry_surface_flux_bq_m2_s,
            field="native_dry_surface_flux_bq_m2_s",
        )
        wet = _nonnegative(
            self.explicit_wet_surface_flux_bq_m2_s,
            field="explicit_wet_surface_flux_bq_m2_s",
        )
        mapped = _nonnegative(
            self.mapped_total_surface_flux_bq_m2_s,
            field="mapped_total_surface_flux_bq_m2_s",
        )
        source_residual = _finite(
            self.native_source_depletion_residual_bq_s,
            field="native_source_depletion_residual_bq_s",
        )
        e2_residual = _finite(
            self.e2_activity_residual_bq_m2,
            field="e2_activity_residual_bq_m2",
        )
        scale_c = max(native_c, mapped_c, 1.0)
        scale_flux = max(dry, wet, mapped, 1.0)
        _closed(mapped_c - native_c, field="air concentration mapping", scale=scale_c)
        _closed(mapped - dry - wet, field="surface deposition mapping", scale=scale_flux)
        _closed(source_residual, field="native source depletion", scale=1.0)
        _closed(e2_residual, field="E2 activity ledger", scale=1.0)


@dataclass(frozen=True)
class NativeHTForcingAdaptation:
    forcing: AtmosphericHTForcing
    soil_boundary: HTSoilDepositionBoundary
    soil_conversion: HTToHTOSoilConversionResult
    ledger: NativeForcingAdapterLedger

    def __post_init__(self) -> None:
        if self.forcing.source_kind is not HTForcingSourceKind.UFOTRI_NATIVE:
            raise UFOTRINativeForcingAdapterError("HT forcing must retain UFOTRI_NATIVE source kind")
        if self.soil_boundary.source_kind is not HTForcingSourceKind.UFOTRI_NATIVE:
            raise UFOTRINativeForcingAdapterError("HT soil boundary lost UFOTRI_NATIVE provenance")
        if self.soil_conversion.source_kind is not HTForcingSourceKind.UFOTRI_NATIVE:
            raise UFOTRINativeForcingAdapterError("E2 conversion lost UFOTRI_NATIVE provenance")


@dataclass(frozen=True)
class NativeHTOForcingAdaptation:
    forcing: AtmosphericHTOForcing
    native_wet_source_loss_bq_s: float
    explicit_wet_surface_flux_bq_m2_s: float
    wet_source_to_surface_spatial_closure_claimed: bool
    ledger: NativeForcingAdapterLedger

    def __post_init__(self) -> None:
        wet_loss = _nonnegative(
            self.native_wet_source_loss_bq_s,
            field="native_wet_source_loss_bq_s",
        )
        wet_flux = _nonnegative(
            self.explicit_wet_surface_flux_bq_m2_s,
            field="explicit_wet_surface_flux_bq_m2_s",
        )
        if wet_loss == 0.0 and wet_flux != 0.0:
            raise UFOTRINativeForcingAdapterError(
                "wet surface flux cannot be nonzero when native wet source loss is zero"
            )
        if self.wet_source_to_surface_spatial_closure_claimed:
            raise UFOTRINativeForcingAdapterError(
                "H3 cannot claim plume-source-loss to local-surface-flux spatial closure"
            )


def _validate_native_result(result: NativePrimaryTransportResult) -> None:
    if not isinstance(result, NativePrimaryTransportResult):
        raise UFOTRINativeForcingAdapterError(
            "result must be NativePrimaryTransportResult from the UFOTRI-native atmosphere"
        )
    _nonnegative(result.air_concentration_bq_m3, field="air_concentration_bq_m3")
    _nonnegative(result.dry_surface_flux_bq_m2_s, field="dry_surface_flux_bq_m2_s")
    _nonnegative(result.effective_source_bq_s, field="effective_source_bq_s")
    _nonnegative(result.dry_source_loss_bq_s, field="dry_source_loss_bq_s")
    _nonnegative(result.wet_source_loss_bq_s, field="wet_source_loss_bq_s")
    generated = _nonnegative(
        result.atmospheric_ht_to_hto_generated_bq_s,
        field="atmospheric_ht_to_hto_generated_bq_s",
    )
    if generated != 0.0:
        raise UFOTRINativeForcingAdapterError(
            "KfK 4605 native path must not create atmospheric HTO from HT"
        )
    _closed(
        result.source_depletion_residual_bq_s,
        field="native source depletion",
        scale=max(1.0, result.effective_source_bq_s),
    )


def adapt_native_ht_forcing(
    *,
    result: NativePrimaryTransportResult,
    context: NativeForcingContext,
    gaseous_species: GaseousTritiumSpecies,
) -> NativeHTForcingAdaptation:
    """Map native HT concentration/deposition through the existing E1/E2 path."""

    _validate_native_result(result)
    if result.species is not TritiumAtmosphericForm.HT:
        raise UFOTRINativeForcingAdapterError("HT adapter requires native HT result")
    if not isinstance(gaseous_species, GaseousTritiumSpecies):
        raise UFOTRINativeForcingAdapterError("gaseous_species must be explicit HT or T2")
    if result.wet_source_loss_bq_s != 0.0:
        raise UFOTRINativeForcingAdapterError("native HT wet deposition must remain zero")

    forcing = AtmosphericHTForcing(
        start_utc=context.start_utc,
        end_utc=context.end_utc,
        species=gaseous_species,
        air_ht_concentration_bq_m3=result.air_concentration_bq_m3,
        surface_ht_deposition_flux_bq_m2_s=result.dry_surface_flux_bq_m2_s,
        source_kind=HTForcingSourceKind.UFOTRI_NATIVE,
        source_id=context.source_id,
        provenance_id=context.provenance_id,
        spatial_support=context.spatial_support,
        concentration_sampling_height_m=context.concentration_sampling_height_m,
    )
    boundary = forcing.to_soil_deposition_boundary()
    conversion = convert_deposited_ht_to_soil_hto(boundary)
    ledger = NativeForcingAdapterLedger(
        native_air_concentration_bq_m3=result.air_concentration_bq_m3,
        mapped_air_concentration_bq_m3=forcing.air_ht_concentration_bq_m3,
        native_dry_surface_flux_bq_m2_s=result.dry_surface_flux_bq_m2_s,
        explicit_wet_surface_flux_bq_m2_s=0.0,
        mapped_total_surface_flux_bq_m2_s=forcing.surface_ht_deposition_flux_bq_m2_s,
        native_source_depletion_residual_bq_s=result.source_depletion_residual_bq_s,
        e2_activity_residual_bq_m2=conversion.ledger.activity_residual_bq_m2,
    )
    return NativeHTForcingAdaptation(
        forcing=forcing,
        soil_boundary=boundary,
        soil_conversion=conversion,
        ledger=ledger,
    )


def adapt_native_hto_forcing(
    *,
    result: NativePrimaryTransportResult,
    context: NativeForcingContext,
    wet_surface_deposition_flux_bq_m2_s: float | None = None,
) -> NativeHTOForcingAdaptation:
    """Map native HTO concentration and resolved local deposition to P7 forcing.

    ``NativePrimaryTransportResult.wet_source_loss_bq_s`` is a plume/source
    ledger term and has dimensions Bq/s.  It is not a local ground flux.  H3
    therefore requires an explicit local wet flux whenever wet source loss is
    nonzero, and deliberately makes no global source-loss-to-ground-area
    closure claim.
    """

    _validate_native_result(result)
    if result.species is not TritiumAtmosphericForm.HTO:
        raise UFOTRINativeForcingAdapterError("HTO adapter requires native HTO result")

    if wet_surface_deposition_flux_bq_m2_s is None:
        if result.wet_source_loss_bq_s > 0.0:
            raise UFOTRINativeForcingAdapterError(
                "native HTO wet source loss requires explicit local wet surface deposition flux"
            )
        wet_flux = 0.0
    else:
        wet_flux = _nonnegative(
            wet_surface_deposition_flux_bq_m2_s,
            field="wet_surface_deposition_flux_bq_m2_s",
        )
        if result.wet_source_loss_bq_s == 0.0 and wet_flux != 0.0:
            raise UFOTRINativeForcingAdapterError(
                "wet surface flux cannot be supplied when native wet source loss is zero"
            )

    total_flux = result.dry_surface_flux_bq_m2_s + wet_flux
    forcing = AtmosphericHTOForcing(
        timestamp=context.start_utc,
        location=context.spatial_support,
        air_hto_concentration=result.air_concentration_bq_m3,
        deposition_flux=total_flux,
        temperature=context.air_temperature_k,
        humidity=context.relative_humidity,
        wind_speed=context.wind_speed_m_s,
        precipitation=context.precipitation_m_s,
        source=UFOTRI_NATIVE_SOURCE_KIND,
        provenance=context.hto_provenance,
        metadata=context.hto_metadata,
    )
    ledger = NativeForcingAdapterLedger(
        native_air_concentration_bq_m3=result.air_concentration_bq_m3,
        mapped_air_concentration_bq_m3=forcing.air_hto_concentration,
        native_dry_surface_flux_bq_m2_s=result.dry_surface_flux_bq_m2_s,
        explicit_wet_surface_flux_bq_m2_s=wet_flux,
        mapped_total_surface_flux_bq_m2_s=forcing.deposition_flux,
        native_source_depletion_residual_bq_s=result.source_depletion_residual_bq_s,
        e2_activity_residual_bq_m2=0.0,
    )
    return NativeHTOForcingAdaptation(
        forcing=forcing,
        native_wet_source_loss_bq_s=result.wet_source_loss_bq_s,
        explicit_wet_surface_flux_bq_m2_s=wet_flux,
        wet_source_to_surface_spatial_closure_claimed=False,
        ledger=ledger,
    )


__all__ = [
    "UFOTRI_NATIVE_ADAPTER_VERSION",
    "UFOTRI_NATIVE_MODEL_NAME",
    "UFOTRI_NATIVE_SOURCE_KIND",
    "NativeForcingAdapterLedger",
    "NativeForcingContext",
    "NativeHTForcingAdaptation",
    "NativeHTOForcingAdaptation",
    "UFOTRINativeForcingAdapterError",
    "adapt_native_ht_forcing",
    "adapt_native_hto_forcing",
]
