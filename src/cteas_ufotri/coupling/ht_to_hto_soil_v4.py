"""Opt-in UFOTRI E2 HT->HTO soil conversion compatibility path.

KfK 4605 Eq. (1)-(2) represents the soil state as HTO and adds the HT
contribution directly through ``v_d,HT * X_HT``. Section 2.2.3 explains why:
HT deposition depends on soil/moisture/microorganism conditions, deposited HT
is transformed rapidly to HTO, and only the transformed part remains in soil.
The recoverable model therefore uses an effective deposition/conversion
boundary rather than a separately parameterised soil-HT kinetic pool.

This module consumes the chemically-HT E1 ``HTSoilDepositionBoundary`` and
closes that boundary as an activity-conserving HTO input to the existing V4
three-layer soil forcing. It does not implement E3 re-emission, atmospheric
HT oxidation, real CTEAS-Atmos binding, or production parameter selection.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
import math

from cteas_ufotri.coupling.ht_v4 import (
    GaseousTritiumSpecies,
    HTForcingSourceKind,
    HTSoilDepositionBoundary,
)
from cteas_ufotri.plant.soil_v4.soil_solver import ThreeLayerSoilForcing

HT_TO_HTO_SOIL_CONVERSION_SEMANTICS = "KFK4605_EQ1_EQ2_DIRECT_SOIL_CONVERSION_R1"
HT_TO_HTO_ACTIVITY_AMOUNT_UNIT = "Bq m-2"
HT_DERIVED_HTO_FLUX_UNIT = "Bq m-2 s-1"


class HTToHTOSoilConversionError(ValueError):
    """Fail-closed error for the isolated E2 conversion/projection path."""


def _finite(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HTToHTOSoilConversionError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise HTToHTOSoilConversionError(f"{field} must be finite")
    return result


def _finite_nonnegative(value: float, *, field: str) -> float:
    result = _finite(value, field=field)
    if result < 0.0:
        raise HTToHTOSoilConversionError(f"{field} must be non-negative")
    return result


def _required_text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HTToHTOSoilConversionError(f"{field} is required")
    return value.strip()


@dataclass(frozen=True)
class HTToHTOSoilConversionLedger:
    """Activity ledger at the E1->E2 chemical-form boundary."""

    input_ht_bq_m2: float
    generated_hto_bq_m2: float
    residual_ht_bq_m2: float
    activity_residual_bq_m2: float
    amount_unit: str = HT_TO_HTO_ACTIVITY_AMOUNT_UNIT

    def __post_init__(self) -> None:
        input_ht = _finite_nonnegative(self.input_ht_bq_m2, field="input_ht_bq_m2")
        generated = _finite_nonnegative(
            self.generated_hto_bq_m2,
            field="generated_hto_bq_m2",
        )
        residual_ht = _finite_nonnegative(
            self.residual_ht_bq_m2,
            field="residual_ht_bq_m2",
        )
        activity_residual = _finite(
            self.activity_residual_bq_m2,
            field="activity_residual_bq_m2",
        )
        if self.amount_unit != HT_TO_HTO_ACTIVITY_AMOUNT_UNIT:
            raise HTToHTOSoilConversionError(
                f"amount_unit must be {HT_TO_HTO_ACTIVITY_AMOUNT_UNIT!r}"
            )
        expected_residual = input_ht - generated - residual_ht
        scale = max(1.0, input_ht, generated, residual_ht)
        tolerance = 1.0e-12 * scale
        if abs(activity_residual - expected_residual) > tolerance:
            raise HTToHTOSoilConversionError(
                "activity_residual_bq_m2 must close input_ht-generated_hto-residual_ht"
            )
        if abs(activity_residual) > tolerance:
            raise HTToHTOSoilConversionError("HT->HTO activity ledger must close")
        if residual_ht != 0.0:
            raise HTToHTOSoilConversionError(
                "recoverable Eq. (1)-(2) path has no retained independent soil-HT pool"
            )
        if abs(input_ht - generated) > tolerance:
            raise HTToHTOSoilConversionError(
                "recoverable Eq. (1)-(2) path requires 1:1 HT activity to HTO activity"
            )


@dataclass(frozen=True)
class HTToHTOSoilConversionResult:
    """Manual-fidelity E2 result before projection into the soil solver."""

    start_utc: datetime
    end_utc: datetime
    species: GaseousTritiumSpecies
    source_kind: HTForcingSourceKind
    provenance_id: str
    spatial_support: str
    input_ht_bq_m2: float
    generated_hto_bq_m2: float
    residual_ht_bq_m2: float
    generated_hto_flux_bq_m2_s: float
    conversion_semantics: str = HT_TO_HTO_SOIL_CONVERSION_SEMANTICS
    amount_unit: str = HT_TO_HTO_ACTIVITY_AMOUNT_UNIT
    flux_unit: str = HT_DERIVED_HTO_FLUX_UNIT
    conversion_fraction: float = 1.0
    atmospheric_ht_oxidation_applied: bool = False
    secondary_hto_reemission_generated: bool = False
    production_parameter_activation: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.start_utc, datetime) or not isinstance(self.end_utc, datetime):
            raise HTToHTOSoilConversionError("start_utc/end_utc must be datetimes")
        if self.start_utc.tzinfo is None or self.end_utc.tzinfo is None:
            raise HTToHTOSoilConversionError("start_utc/end_utc must be timezone-aware UTC")
        if self.start_utc.utcoffset() != timedelta(0) or self.end_utc.utcoffset() != timedelta(0):
            raise HTToHTOSoilConversionError("start_utc/end_utc must use UTC")
        duration = (self.end_utc - self.start_utc).total_seconds()
        if duration <= 0.0:
            raise HTToHTOSoilConversionError("conversion interval must be positive")
        if not isinstance(self.species, GaseousTritiumSpecies):
            raise HTToHTOSoilConversionError("species must remain explicit HT or T2")
        if not isinstance(self.source_kind, HTForcingSourceKind):
            raise HTToHTOSoilConversionError("source_kind must be HTForcingSourceKind")
        if self.source_kind is HTForcingSourceKind.REAL_CTEAS_ATMOS:
            raise HTToHTOSoilConversionError(
                "real CTEAS-Atmos HT binding remains deferred to E4"
            )
        _required_text(self.provenance_id, field="provenance_id")
        _required_text(self.spatial_support, field="spatial_support")
        input_ht = _finite_nonnegative(self.input_ht_bq_m2, field="input_ht_bq_m2")
        generated = _finite_nonnegative(
            self.generated_hto_bq_m2,
            field="generated_hto_bq_m2",
        )
        residual_ht = _finite_nonnegative(
            self.residual_ht_bq_m2,
            field="residual_ht_bq_m2",
        )
        flux = _finite_nonnegative(
            self.generated_hto_flux_bq_m2_s,
            field="generated_hto_flux_bq_m2_s",
        )
        if self.conversion_semantics != HT_TO_HTO_SOIL_CONVERSION_SEMANTICS:
            raise HTToHTOSoilConversionError("unexpected HT->HTO conversion semantics")
        if self.amount_unit != HT_TO_HTO_ACTIVITY_AMOUNT_UNIT:
            raise HTToHTOSoilConversionError("unexpected activity amount unit")
        if self.flux_unit != HT_DERIVED_HTO_FLUX_UNIT:
            raise HTToHTOSoilConversionError("unexpected HT-derived HTO flux unit")
        if self.conversion_fraction != 1.0:
            raise HTToHTOSoilConversionError(
                "manual Eq. (1)-(2) effective deposition/conversion fraction is fixed to 1"
            )
        if self.atmospheric_ht_oxidation_applied:
            raise HTToHTOSoilConversionError("atmospheric HT oxidation is not E2 scope")
        if self.secondary_hto_reemission_generated:
            raise HTToHTOSoilConversionError("secondary HTO re-emission is E3 scope")
        if self.production_parameter_activation:
            raise HTToHTOSoilConversionError("E2 does not activate production parameters")
        scale = max(1.0, input_ht, generated)
        tolerance = 1.0e-12 * scale
        if residual_ht != 0.0 or abs(generated - input_ht) > tolerance:
            raise HTToHTOSoilConversionError(
                "recoverable Eq. (1)-(2) path requires complete retained-HT -> HTO mapping"
            )
        if abs(flux * duration - generated) > tolerance:
            raise HTToHTOSoilConversionError(
                "generated HTO flux must integrate to generated HTO amount"
            )

    @property
    def duration_s(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds()

    @property
    def ledger(self) -> HTToHTOSoilConversionLedger:
        return HTToHTOSoilConversionLedger(
            input_ht_bq_m2=self.input_ht_bq_m2,
            generated_hto_bq_m2=self.generated_hto_bq_m2,
            residual_ht_bq_m2=self.residual_ht_bq_m2,
            activity_residual_bq_m2=(
                self.input_ht_bq_m2
                - self.generated_hto_bq_m2
                - self.residual_ht_bq_m2
            ),
        )


@dataclass(frozen=True)
class HTToHTOSoilProjection:
    """Provenance-preserving projection into the existing soil forcing type."""

    forcing: ThreeLayerSoilForcing
    primary_hto_surface_flux_bq_m2_s: float
    ht_derived_hto_surface_flux_bq_m2_s: float
    combined_hto_surface_flux_bq_m2_s: float
    ht_source_kind: HTForcingSourceKind
    ht_species: GaseousTritiumSpecies
    ht_provenance_id: str
    ht_spatial_support: str

    def __post_init__(self) -> None:
        if not isinstance(self.forcing, ThreeLayerSoilForcing):
            raise HTToHTOSoilConversionError("forcing must be ThreeLayerSoilForcing")
        primary = _finite_nonnegative(
            self.primary_hto_surface_flux_bq_m2_s,
            field="primary_hto_surface_flux_bq_m2_s",
        )
        derived = _finite_nonnegative(
            self.ht_derived_hto_surface_flux_bq_m2_s,
            field="ht_derived_hto_surface_flux_bq_m2_s",
        )
        combined = _finite_nonnegative(
            self.combined_hto_surface_flux_bq_m2_s,
            field="combined_hto_surface_flux_bq_m2_s",
        )
        tolerance = 1.0e-12 * max(1.0, primary, derived, combined)
        if abs(combined - primary - derived) > tolerance:
            raise HTToHTOSoilConversionError("primary + HT-derived HTO flux must close")
        if abs(self.forcing.surface_deposition_flux_bq_m2_s - combined) > tolerance:
            raise HTToHTOSoilConversionError(
                "projected soil forcing must carry the combined HTO surface flux"
            )
        if not isinstance(self.ht_source_kind, HTForcingSourceKind):
            raise HTToHTOSoilConversionError("ht_source_kind must be HTForcingSourceKind")
        if not isinstance(self.ht_species, GaseousTritiumSpecies):
            raise HTToHTOSoilConversionError("ht_species must remain explicit HT or T2")
        _required_text(self.ht_provenance_id, field="ht_provenance_id")
        _required_text(self.ht_spatial_support, field="ht_spatial_support")


def convert_deposited_ht_to_soil_hto(
    boundary: HTSoilDepositionBoundary,
) -> HTToHTOSoilConversionResult:
    """Map the E1 effective deposited-HT boundary directly into HTO activity.

    No extra kinetic constant is introduced: in the recoverable UFOTRI
    Eq. (1)-(2) semantics, ``v_d,HT * X_HT`` is already the effective soil-HTO
    source term after rapid microorganism-mediated conversion.
    """

    if not isinstance(boundary, HTSoilDepositionBoundary):
        raise HTToHTOSoilConversionError(
            "boundary must be the reviewed E1 HTSoilDepositionBoundary"
        )
    if boundary.converted_to_hto_bq_m2 != 0.0:
        raise HTToHTOSoilConversionError(
            "E2 requires an unconverted E1 HT boundary to prevent double conversion"
        )
    duration = (boundary.end_utc - boundary.start_utc).total_seconds()
    if duration <= 0.0:
        raise HTToHTOSoilConversionError("boundary interval must be positive")
    amount = _finite_nonnegative(
        boundary.deposited_ht_bq_m2,
        field="deposited_ht_bq_m2",
    )
    return HTToHTOSoilConversionResult(
        start_utc=boundary.start_utc,
        end_utc=boundary.end_utc,
        species=boundary.species,
        source_kind=boundary.source_kind,
        provenance_id=boundary.provenance_id,
        spatial_support=boundary.spatial_support,
        input_ht_bq_m2=amount,
        generated_hto_bq_m2=amount,
        residual_ht_bq_m2=0.0,
        generated_hto_flux_bq_m2_s=amount / duration,
    )


def project_ht_derived_hto_into_soil_forcing(
    *,
    base_forcing: ThreeLayerSoilForcing,
    conversion: HTToHTOSoilConversionResult,
    interval_seconds: float,
) -> HTToHTOSoilProjection:
    """Add HT-derived HTO to, rather than overwrite, primary HTO soil input."""

    if not isinstance(base_forcing, ThreeLayerSoilForcing):
        raise HTToHTOSoilConversionError("base_forcing must be ThreeLayerSoilForcing")
    if not isinstance(conversion, HTToHTOSoilConversionResult):
        raise HTToHTOSoilConversionError(
            "conversion must be HTToHTOSoilConversionResult"
        )
    interval = _finite_nonnegative(interval_seconds, field="interval_seconds")
    if interval <= 0.0:
        raise HTToHTOSoilConversionError("interval_seconds must be positive")
    tolerance_s = 1.0e-12 * max(1.0, interval, conversion.duration_s)
    if abs(interval - conversion.duration_s) > tolerance_s:
        raise HTToHTOSoilConversionError(
            "soil interval_seconds must equal the HT conversion interval"
        )
    if base_forcing.timestamp != conversion.start_utc:
        raise HTToHTOSoilConversionError(
            "base_forcing.timestamp must equal conversion.start_utc"
        )
    primary = base_forcing.surface_deposition_flux_bq_m2_s
    derived = conversion.generated_hto_flux_bq_m2_s
    combined = primary + derived
    forcing = replace(
        base_forcing,
        surface_deposition_flux_bq_m2_s=combined,
    )
    return HTToHTOSoilProjection(
        forcing=forcing,
        primary_hto_surface_flux_bq_m2_s=primary,
        ht_derived_hto_surface_flux_bq_m2_s=derived,
        combined_hto_surface_flux_bq_m2_s=combined,
        ht_source_kind=conversion.source_kind,
        ht_species=conversion.species,
        ht_provenance_id=conversion.provenance_id,
        ht_spatial_support=conversion.spatial_support,
    )


__all__ = [
    "HT_DERIVED_HTO_FLUX_UNIT",
    "HT_TO_HTO_ACTIVITY_AMOUNT_UNIT",
    "HT_TO_HTO_SOIL_CONVERSION_SEMANTICS",
    "HTToHTOSoilConversionError",
    "HTToHTOSoilConversionLedger",
    "HTToHTOSoilConversionResult",
    "HTToHTOSoilProjection",
    "convert_deposited_ht_to_soil_hto",
    "project_ht_derived_hto_into_soil_forcing",
]
