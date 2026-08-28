"""Opt-in typed HT forcing contract for UFOTRI Phase E1.

E1 freezes the chemical identity, units, provenance, interval semantics and
soil-boundary handoff for gaseous tritium without implementing HT->HTO
conversion.  It intentionally remains separate from the frozen HTO forcing
contract.

Only synthetic/replay HT forcing is authorized in E1.  Real CTEAS-Atmos HT
binding remains Phase E4.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
import math

AIR_HT_CONCENTRATION_UNIT = "Bq m-3"
HT_SURFACE_DEPOSITION_FLUX_UNIT = "Bq m-2 s-1"
HT_SURFACE_DEPOSITION_AMOUNT_UNIT = "Bq m-2"
MANUAL_HT_REFERENCE_PROFILE_ID = "KFK4605_HT_EVIDENCE_R1"


class HTContractError(ValueError):
    """Fail-closed error for the isolated E1 HT contract."""


class GaseousTritiumSpecies(str, Enum):
    """Manual-supported gaseous tritium identities.

    KfK 4605 explicitly describes gaseous tritium as HT/T2.  Other mixtures
    are not silently normalized into this manual-replication contract.
    """

    HT = "HT"
    T2 = "T2"


class HTForcingSourceKind(str, Enum):
    SYNTHETIC = "synthetic"
    REPLAY = "replay"
    REAL_CTEAS_ATMOS = "real_cteas_atmos"


def _finite_nonnegative(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HTContractError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise HTContractError(f"{field} must be finite")
    if result < 0.0:
        raise HTContractError(f"{field} must be non-negative")
    return result


def _required_text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HTContractError(f"{field} is required")
    return value.strip()


def _utc(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise HTContractError(f"{field} must be timezone-aware UTC")
    offset = value.utcoffset()
    if offset != timedelta(0):
        raise HTContractError(f"{field} must be UTC with zero offset")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class HTManualEvidenceProfile:
    """Manual/benchmark evidence exposed without activating production defaults."""

    profile_id: str = MANUAL_HT_REFERENCE_PROFILE_ID

    benchmark_ht_dry_deposition_velocity_cm_s: float = 0.05
    benchmark_air_oxidation_fraction_d_1: float = 0.005
    benchmark_ht_soil_diffusion_cm2_s: float = 5.0e-2
    benchmark_hto_dry_deposition_velocity_cm_s: float = 1.8
    benchmark_hto_soil_diffusion_cm2_s: float = 2.0e-5

    ht_deposition_depends_on_soil_type_and_moisture: bool = True
    deposited_ht_rapidly_converts_via_microorganisms: bool = True
    only_transformed_ht_remains_in_soil: bool = True
    atmospheric_oxidation_owned_by_e1: bool = False
    soil_conversion_owned_by_e1: bool = False
    production_parameter_activation: bool = False

    def __post_init__(self) -> None:
        if self.profile_id != MANUAL_HT_REFERENCE_PROFILE_ID:
            raise HTContractError("unexpected HT evidence profile")
        for field in (
            "benchmark_ht_dry_deposition_velocity_cm_s",
            "benchmark_air_oxidation_fraction_d_1",
            "benchmark_ht_soil_diffusion_cm2_s",
            "benchmark_hto_dry_deposition_velocity_cm_s",
            "benchmark_hto_soil_diffusion_cm2_s",
        ):
            if _finite_nonnegative(getattr(self, field), field=field) <= 0.0:
                raise HTContractError(f"{field} must be positive")
        required_true = (
            self.ht_deposition_depends_on_soil_type_and_moisture,
            self.deposited_ht_rapidly_converts_via_microorganisms,
            self.only_transformed_ht_remains_in_soil,
        )
        if not all(required_true):
            raise HTContractError("manual HT process semantics must remain explicit")
        if self.atmospheric_oxidation_owned_by_e1:
            raise HTContractError("E1 does not own atmospheric HT oxidation")
        if self.soil_conversion_owned_by_e1:
            raise HTContractError("E1 does not implement HT->HTO soil conversion")
        if self.production_parameter_activation:
            raise HTContractError("E1 benchmark evidence is not a production parameter set")

    @property
    def benchmark_ht_dry_deposition_velocity_m_s(self) -> float:
        return self.benchmark_ht_dry_deposition_velocity_cm_s * 1.0e-2

    @property
    def benchmark_air_oxidation_rate_s_1(self) -> float:
        return self.benchmark_air_oxidation_fraction_d_1 / 86400.0

    @property
    def benchmark_ht_soil_diffusion_m2_s(self) -> float:
        return self.benchmark_ht_soil_diffusion_cm2_s * 1.0e-4


@dataclass(frozen=True)
class AtmosphericHTForcing:
    """Typed E1 HT forcing record.

    This is not interchangeable with AtmosphericHTOForcing.  The surface
    deposition value is still HT at the soil boundary; no HTO is created here.
    """

    start_utc: datetime
    end_utc: datetime
    species: GaseousTritiumSpecies
    air_ht_concentration_bq_m3: float
    surface_ht_deposition_flux_bq_m2_s: float
    source_kind: HTForcingSourceKind
    source_id: str
    provenance_id: str
    spatial_support: str
    concentration_sampling_height_m: float
    concentration_unit: str = AIR_HT_CONCENTRATION_UNIT
    deposition_flux_unit: str = HT_SURFACE_DEPOSITION_FLUX_UNIT

    def __post_init__(self) -> None:
        start = _utc(self.start_utc, field="start_utc")
        end = _utc(self.end_utc, field="end_utc")
        if end <= start:
            raise HTContractError("end_utc must be later than start_utc")
        if not isinstance(self.species, GaseousTritiumSpecies):
            raise HTContractError("species must be explicit HT or T2")
        if not isinstance(self.source_kind, HTForcingSourceKind):
            raise HTContractError("source_kind must be HTForcingSourceKind")
        if self.source_kind is HTForcingSourceKind.REAL_CTEAS_ATMOS:
            raise HTContractError(
                "real CTEAS-Atmos HT binding is deferred to E4 and fails closed in E1"
            )
        _finite_nonnegative(
            self.air_ht_concentration_bq_m3,
            field="air_ht_concentration_bq_m3",
        )
        _finite_nonnegative(
            self.surface_ht_deposition_flux_bq_m2_s,
            field="surface_ht_deposition_flux_bq_m2_s",
        )
        height = _finite_nonnegative(
            self.concentration_sampling_height_m,
            field="concentration_sampling_height_m",
        )
        _required_text(self.source_id, field="source_id")
        _required_text(self.provenance_id, field="provenance_id")
        _required_text(self.spatial_support, field="spatial_support")
        if self.concentration_unit != AIR_HT_CONCENTRATION_UNIT:
            raise HTContractError(
                f"concentration_unit must be {AIR_HT_CONCENTRATION_UNIT!r}"
            )
        if self.deposition_flux_unit != HT_SURFACE_DEPOSITION_FLUX_UNIT:
            raise HTContractError(
                f"deposition_flux_unit must be {HT_SURFACE_DEPOSITION_FLUX_UNIT!r}"
            )
        object.__setattr__(self, "start_utc", start)
        object.__setattr__(self, "end_utc", end)
        object.__setattr__(self, "concentration_sampling_height_m", height)

    @property
    def duration_s(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds()

    def to_soil_deposition_boundary(self) -> "HTSoilDepositionBoundary":
        """Integrate HT surface flux over the interval without chemistry conversion."""

        amount = self.surface_ht_deposition_flux_bq_m2_s * self.duration_s
        return HTSoilDepositionBoundary(
            start_utc=self.start_utc,
            end_utc=self.end_utc,
            species=self.species,
            deposited_ht_bq_m2=amount,
            source_kind=self.source_kind,
            provenance_id=self.provenance_id,
            spatial_support=self.spatial_support,
        )


@dataclass(frozen=True)
class HTSoilDepositionBoundary:
    """E1 output handed to E2.

    The inventory remains chemically HT.  E2 must own any conversion to HTO.
    """

    start_utc: datetime
    end_utc: datetime
    species: GaseousTritiumSpecies
    deposited_ht_bq_m2: float
    source_kind: HTForcingSourceKind
    provenance_id: str
    spatial_support: str
    amount_unit: str = HT_SURFACE_DEPOSITION_AMOUNT_UNIT
    converted_to_hto_bq_m2: float = 0.0

    def __post_init__(self) -> None:
        start = _utc(self.start_utc, field="start_utc")
        end = _utc(self.end_utc, field="end_utc")
        if end <= start:
            raise HTContractError("end_utc must be later than start_utc")
        if not isinstance(self.species, GaseousTritiumSpecies):
            raise HTContractError("species must remain explicit HT or T2")
        if not isinstance(self.source_kind, HTForcingSourceKind):
            raise HTContractError("source_kind must be HTForcingSourceKind")
        _finite_nonnegative(self.deposited_ht_bq_m2, field="deposited_ht_bq_m2")
        converted = _finite_nonnegative(
            self.converted_to_hto_bq_m2,
            field="converted_to_hto_bq_m2",
        )
        if converted != 0.0:
            raise HTContractError("E1 must not create HTO from deposited HT")
        _required_text(self.provenance_id, field="provenance_id")
        _required_text(self.spatial_support, field="spatial_support")
        if self.amount_unit != HT_SURFACE_DEPOSITION_AMOUNT_UNIT:
            raise HTContractError(
                f"amount_unit must be {HT_SURFACE_DEPOSITION_AMOUNT_UNIT!r}"
            )
        object.__setattr__(self, "start_utc", start)
        object.__setattr__(self, "end_utc", end)


@dataclass(frozen=True)
class HTBranchOwnership:
    """Machine-readable stage ownership boundary."""

    e1_contract_and_mapping: bool = True
    e1_ht_to_hto_soil_conversion: bool = False
    e1_secondary_hto_reemission: bool = False
    e1_real_atmos_binding: bool = False
    e2_owns_ht_to_hto_soil_conversion: bool = True
    e3_owns_ht_derived_hto_reemission: bool = True
    e4_owns_real_ht_atmos_binding: bool = True
    hto_forcing_reused_for_ht: bool = False

    def __post_init__(self) -> None:
        if not self.e1_contract_and_mapping:
            raise HTContractError("E1 must own HT contract/mapping")
        forbidden = (
            self.e1_ht_to_hto_soil_conversion,
            self.e1_secondary_hto_reemission,
            self.e1_real_atmos_binding,
            self.hto_forcing_reused_for_ht,
        )
        if any(forbidden):
            raise HTContractError("E1 ownership boundary violated")
        required = (
            self.e2_owns_ht_to_hto_soil_conversion,
            self.e3_owns_ht_derived_hto_reemission,
            self.e4_owns_real_ht_atmos_binding,
        )
        if not all(required):
            raise HTContractError("downstream HT stage ownership must stay explicit")


def ht_manual_evidence_profile() -> HTManualEvidenceProfile:
    return HTManualEvidenceProfile()


def ht_branch_ownership() -> HTBranchOwnership:
    return HTBranchOwnership()


__all__ = [
    "AIR_HT_CONCENTRATION_UNIT",
    "HT_SURFACE_DEPOSITION_AMOUNT_UNIT",
    "HT_SURFACE_DEPOSITION_FLUX_UNIT",
    "MANUAL_HT_REFERENCE_PROFILE_ID",
    "AtmosphericHTForcing",
    "GaseousTritiumSpecies",
    "HTBranchOwnership",
    "HTContractError",
    "HTForcingSourceKind",
    "HTManualEvidenceProfile",
    "HTSoilDepositionBoundary",
    "ht_branch_ownership",
    "ht_manual_evidence_profile",
]
