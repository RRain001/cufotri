"""V3.1 typed mass-basis and tissue-scope contract.

This module is intentionally orthogonal to the frozen V3 solvers.  It provides
metadata and fail-closed comparison gates only; it does not perform numerical
fresh/dry/water/hydrogen conversion and is not imported by the V3 pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BasisContractError(ValueError):
    """Raised when a V3.1 basis contract is incomplete or inconsistent."""


class BasisCompatibilityError(BasisContractError):
    """Raised when two records cannot be compared under the declared basis."""


class MassBasis(str, Enum):
    """Declared denominator basis for plant/product activity concentration."""

    FRESH_MASS = "fresh_mass"
    DRY_MASS = "dry_mass"
    WATER_MASS = "water_mass"
    HYDROGEN_MASS = "hydrogen_mass"


class TissueScopeKind(str, Enum):
    """Typed biological/product scope associated with a mass basis."""

    WHOLE_PLANT = "whole_plant"
    EDIBLE_TISSUE = "edible_tissue"
    LEAF = "leaf"
    ROOT = "root"
    STEM = "stem"
    GRAIN = "grain"
    FRUIT = "fruit"
    HARVEST_PRODUCT = "harvest_product"
    CUSTOM = "custom"


class AreaBasisKind(str, Enum):
    """Declared area normalization used when an inventory is area based."""

    GROUND_AREA = "ground_area"
    LEAF_AREA = "leaf_area"
    HARVEST_AREA = "harvest_area"
    NOT_APPLICABLE = "not_applicable"
    CUSTOM = "custom"


class ConversionStatus(str, Enum):
    """Lifecycle state for a possible cross-mass-basis relation."""

    NOT_REQUESTED = "not_requested"
    IDENTITY_ONLY = "identity_only"
    EVIDENCE_DECLARED = "evidence_declared"
    BLOCKED_MISSING_EVIDENCE = "blocked_missing_evidence"


def _require_text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BasisContractError(f"{field} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class BasisProvenance:
    """Provenance for the declared basis metadata, not a physics parameter."""

    source_id: str
    source_locator: str
    revision: str
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _require_text(self.source_id, field="source_id"))
        object.__setattr__(
            self,
            "source_locator",
            _require_text(self.source_locator, field="source_locator"),
        )
        object.__setattr__(self, "revision", _require_text(self.revision, field="revision"))
        if self.note is not None:
            object.__setattr__(self, "note", _require_text(self.note, field="note"))


@dataclass(frozen=True)
class TissueScope:
    """Typed tissue/product scope with an optional declared identifier."""

    kind: TissueScopeKind
    identifier: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TissueScopeKind):
            raise BasisContractError("kind must be a TissueScopeKind")
        if self.kind is TissueScopeKind.CUSTOM:
            if self.identifier is None:
                raise BasisContractError("custom tissue scope requires identifier")
            object.__setattr__(
                self,
                "identifier",
                _require_text(self.identifier, field="tissue_scope.identifier"),
            )
        elif self.identifier is not None:
            object.__setattr__(
                self,
                "identifier",
                _require_text(self.identifier, field="tissue_scope.identifier"),
            )


@dataclass(frozen=True)
class AreaBasis:
    """Typed area basis with an optional declared identifier."""

    kind: AreaBasisKind
    identifier: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AreaBasisKind):
            raise BasisContractError("kind must be an AreaBasisKind")
        if self.kind is AreaBasisKind.CUSTOM:
            if self.identifier is None:
                raise BasisContractError("custom area basis requires identifier")
            object.__setattr__(
                self,
                "identifier",
                _require_text(self.identifier, field="area_basis.identifier"),
            )
        elif self.identifier is not None:
            object.__setattr__(
                self,
                "identifier",
                _require_text(self.identifier, field="area_basis.identifier"),
            )


@dataclass(frozen=True)
class MassBasisContract:
    """Immutable V3.1 declaration attached to a plant/product observation."""

    subject_id: str
    mass_basis: MassBasis
    tissue_scope: TissueScope
    area_basis: AreaBasis
    provenance: BasisProvenance
    conversion_status: ConversionStatus = ConversionStatus.NOT_REQUESTED
    conversion_evidence_id: str | None = None
    version: str = "v3.1-mass-basis-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_id", _require_text(self.subject_id, field="subject_id"))
        if not isinstance(self.mass_basis, MassBasis):
            raise BasisContractError("mass_basis must be a MassBasis")
        if not isinstance(self.tissue_scope, TissueScope):
            raise BasisContractError("tissue_scope must be a TissueScope")
        if not isinstance(self.area_basis, AreaBasis):
            raise BasisContractError("area_basis must be an AreaBasis")
        if not isinstance(self.provenance, BasisProvenance):
            raise BasisContractError("provenance must be BasisProvenance")
        if not isinstance(self.conversion_status, ConversionStatus):
            raise BasisContractError("conversion_status must be a ConversionStatus")
        if self.conversion_status is ConversionStatus.EVIDENCE_DECLARED:
            if self.conversion_evidence_id is None:
                raise BasisContractError(
                    "evidence_declared conversion status requires conversion_evidence_id"
                )
            object.__setattr__(
                self,
                "conversion_evidence_id",
                _require_text(
                    self.conversion_evidence_id,
                    field="conversion_evidence_id",
                ),
            )
        elif self.conversion_evidence_id is not None:
            raise BasisContractError(
                "conversion_evidence_id is only valid when conversion_status is evidence_declared"
            )
        object.__setattr__(self, "version", _require_text(self.version, field="version"))


@dataclass(frozen=True)
class BasisConversionEvidence:
    """Evidence declaration for a proposed cross-basis relation.

    No conversion factor is stored here.  V3.1 validates only that a proposed
    relation is explicitly sourced and based on paired measurements.  A future
    numerical conversion requires a separately reviewed scientific relation.
    """

    evidence_id: str
    source_basis: MassBasis
    target_basis: MassBasis
    paired_measurement_ids: tuple[str, ...]
    provenance: BasisProvenance

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", _require_text(self.evidence_id, field="evidence_id"))
        if not isinstance(self.source_basis, MassBasis) or not isinstance(
            self.target_basis, MassBasis
        ):
            raise BasisContractError("source_basis and target_basis must be MassBasis values")
        if self.source_basis is self.target_basis:
            raise BasisContractError("conversion evidence must connect different mass bases")
        if len(self.paired_measurement_ids) < 2:
            raise BasisContractError(
                "cross-basis evidence requires at least two declared paired measurement ids"
            )
        cleaned = tuple(
            _require_text(value, field="paired_measurement_ids")
            for value in self.paired_measurement_ids
        )
        if len(set(cleaned)) != len(cleaned):
            raise BasisContractError("paired_measurement_ids must be unique")
        object.__setattr__(self, "paired_measurement_ids", cleaned)
        if not isinstance(self.provenance, BasisProvenance):
            raise BasisContractError("provenance must be BasisProvenance")


def _require_same_scope(left: MassBasisContract, right: MassBasisContract) -> None:
    if left.tissue_scope != right.tissue_scope:
        raise BasisCompatibilityError(
            "tissue scope mismatch; cross-tissue comparison is not authorized"
        )
    if left.area_basis != right.area_basis:
        raise BasisCompatibilityError(
            "area basis mismatch; an area conversion contract is not defined in V3.1"
        )


def require_direct_comparison(
    left: MassBasisContract,
    right: MassBasisContract,
) -> None:
    """Allow direct comparison only for identical mass/tissue/area bases."""

    _require_same_scope(left, right)
    if left.mass_basis is not right.mass_basis:
        raise BasisCompatibilityError(
            "mass basis mismatch; direct comparison is blocked and no numerical "
            "fresh/dry/water/hydrogen conversion is implemented in V3.1"
        )


def validate_conversion_proposal(
    source: MassBasisContract,
    target: MassBasisContract,
    evidence: BasisConversionEvidence | None,
) -> ConversionStatus:
    """Validate evidence metadata for a proposed cross-basis conversion.

    This function never converts a value.  It returns only the governance state
    of the proposal and fails closed on scope or evidence mismatch.
    """

    _require_same_scope(source, target)
    if source.mass_basis is target.mass_basis:
        return ConversionStatus.IDENTITY_ONLY
    if evidence is None:
        raise BasisCompatibilityError(
            "cross-basis conversion blocked: paired evidence and provenance are required"
        )
    if evidence.source_basis is not source.mass_basis:
        raise BasisCompatibilityError("conversion evidence source basis does not match")
    if evidence.target_basis is not target.mass_basis:
        raise BasisCompatibilityError("conversion evidence target basis does not match")
    return ConversionStatus.EVIDENCE_DECLARED


__all__ = [
    "AreaBasis",
    "AreaBasisKind",
    "BasisCompatibilityError",
    "BasisContractError",
    "BasisConversionEvidence",
    "BasisProvenance",
    "ConversionStatus",
    "MassBasis",
    "MassBasisContract",
    "TissueScope",
    "TissueScopeKind",
    "require_direct_comparison",
    "validate_conversion_proposal",
]
