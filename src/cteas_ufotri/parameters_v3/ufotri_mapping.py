"""Read-only UFOTRI-to-V3 semantic mapping control plane.

P7.6C-2 records equation and quantity semantics recovered from UFOTRI
material.  The module deliberately has no runtime parameter lookup and is
not imported by plant, soil, exposure, or pipeline code.  A mapping record is
not a selected value, a validation result, or an activation instruction.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .validation import (
    ParameterRegistryError,
    ParameterSchemaError,
    ValidationProvenance,
    coerce_enum,
    require_identifier,
    require_mapping,
    require_text,
)


class MappingStatus(str, Enum):
    """Frozen semantic disposition for one UFOTRI/V3 comparison."""

    DIRECT_MAPPING = "DIRECT_MAPPING"
    TRANSFORMABLE_MAPPING = "TRANSFORMABLE_MAPPING"
    CONCEPTUAL_ANALOGUE = "CONCEPTUAL_ANALOGUE"
    NO_MAPPING = "NO_MAPPING"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class MappingReviewStatus(str, Enum):
    """Review state of a mapping record, separate from evidence status."""

    PENDING_REVIEW = "PENDING_REVIEW"
    INTERNAL_REVIEWED = "INTERNAL_REVIEWED"
    INDEPENDENT_REVIEWED = "INDEPENDENT_REVIEWED"
    REJECTED = "REJECTED"


_RELATIONSHIPS = frozenset(
    {
        "EXACT",
        "EXACT_ROLE",
        "EXACT_UNIT",
        "UNIT_SCALE_ONLY",
        "COMPATIBLE",
        "COMPATIBLE_ROLE",
        "COMPATIBLE_COMPARTMENT",
        "INCOMPATIBLE",
        "TRANSFER_REQUIRED",
        "UNKNOWN",
        "NOT_APPLICABLE",
    }
)


@dataclass(frozen=True)
class UFOTRIParameterMappingRecord:
    """Immutable one-parameter semantic mapping record.

    The fields intentionally describe both sides of the comparison.  No
    numerical value is present: a record can only say whether a later evidence
    recovery step may be considered.
    """

    mapping_id: str
    v3_parameter_id: str
    v3_subsystem: str
    v3_symbol: str
    v3_equation: str
    v3_quantity_definition: str
    v3_canonical_unit: str
    v3_state_basis: str
    ufotri_source_id: str
    ufotri_symbol: str
    ufotri_equation: str
    ufotri_quantity_definition: str
    ufotri_reported_unit: str
    ufotri_compartment: str
    ufotri_time_basis: str
    mapping_status: MappingStatus | str
    unit_relationship: str
    equation_relationship: str
    compartment_relationship: str
    state_basis_relationship: str
    required_transformation: str
    transformation_derivation: str
    mapping_notes: str
    review_status: MappingReviewStatus | str
    provenance: ValidationProvenance | Mapping[str, Any]
    current_status: str = "PROVISIONAL"
    transformation_possible: bool = False
    future_evidence_recovery_allowed: bool = False

    def __post_init__(self) -> None:
        for field in (
            "mapping_id",
            "v3_parameter_id",
            "ufotri_source_id",
        ):
            require_identifier(getattr(self, field), field=field)
        for field in (
            "v3_subsystem",
            "v3_symbol",
            "v3_equation",
            "v3_quantity_definition",
            "v3_state_basis",
            "ufotri_symbol",
            "ufotri_equation",
            "ufotri_quantity_definition",
            "ufotri_compartment",
            "ufotri_time_basis",
            "unit_relationship",
            "equation_relationship",
            "compartment_relationship",
            "state_basis_relationship",
            "required_transformation",
            "transformation_derivation",
            "mapping_notes",
            "current_status",
        ):
            require_text(getattr(self, field), field=field)
        require_text(self.v3_canonical_unit, field="v3_canonical_unit")
        require_text(self.ufotri_reported_unit, field="ufotri_reported_unit")
        if not isinstance(self.transformation_possible, bool):
            raise ParameterSchemaError("transformation_possible must be a boolean")
        if not isinstance(self.future_evidence_recovery_allowed, bool):
            raise ParameterSchemaError(
                "future_evidence_recovery_allowed must be a boolean"
            )

        status = coerce_enum(
            self.mapping_status,
            MappingStatus,
            field="mapping_status",
        )
        review = coerce_enum(
            self.review_status,
            MappingReviewStatus,
            field="review_status",
        )
        object.__setattr__(self, "mapping_status", status)
        object.__setattr__(self, "review_status", review)

        current_status = self.current_status.upper()
        if current_status not in {"PROVISIONAL", "EVIDENCE_FOUND", "VALIDATED", "ACTIVE", "REJECTED"}:
            raise ParameterSchemaError(
                "current_status must be a known V3 evidence status"
            )
        object.__setattr__(self, "current_status", current_status)

        for field in (
            "unit_relationship",
            "equation_relationship",
            "compartment_relationship",
            "state_basis_relationship",
        ):
            relationship = getattr(self, field).upper()
            if relationship not in _RELATIONSHIPS:
                raise ParameterSchemaError(
                    f"{field} has unsupported relationship {relationship!r}"
                )
            object.__setattr__(self, field, relationship)

        provenance = self.provenance
        if not isinstance(provenance, ValidationProvenance):
            provenance = ValidationProvenance.from_mapping(provenance)
        object.__setattr__(self, "provenance", provenance)
        self._validate_status_contract()

    def _validate_status_contract(self) -> None:
        status = self.mapping_status
        if status is MappingStatus.DIRECT_MAPPING:
            if self.transformation_possible:
                raise ParameterSchemaError(
                    "DIRECT_MAPPING cannot advertise a model transformation"
                )
            if self.equation_relationship not in {"EXACT", "EXACT_ROLE", "COMPATIBLE_ROLE"}:
                raise ParameterSchemaError(
                    "DIRECT_MAPPING requires an exact or compatible equation role"
                )
            if self.unit_relationship not in {"EXACT", "EXACT_UNIT", "UNIT_SCALE_ONLY"}:
                raise ParameterSchemaError(
                    "DIRECT_MAPPING requires exact units or unit scaling only"
                )
            if self.compartment_relationship not in {
                "EXACT",
                "COMPATIBLE",
                "COMPATIBLE_COMPARTMENT",
            }:
                raise ParameterSchemaError(
                    "DIRECT_MAPPING requires compatible compartments"
                )
            if self.state_basis_relationship not in {
                "EXACT",
                "COMPATIBLE",
            }:
                raise ParameterSchemaError(
                    "DIRECT_MAPPING requires a compatible state basis"
                )
        elif status is MappingStatus.TRANSFORMABLE_MAPPING:
            if not self.transformation_possible:
                raise ParameterSchemaError(
                    "TRANSFORMABLE_MAPPING requires transformation_possible=true"
                )
            if self.equation_relationship in {"INCOMPATIBLE", "UNKNOWN"}:
                raise ParameterSchemaError(
                    "TRANSFORMABLE_MAPPING requires a compatible equation role"
                )
            if self.compartment_relationship in {"INCOMPATIBLE", "UNKNOWN"}:
                raise ParameterSchemaError(
                    "TRANSFORMABLE_MAPPING requires a compatible compartment"
                )
            if self.state_basis_relationship in {"INCOMPATIBLE", "UNKNOWN"}:
                raise ParameterSchemaError(
                    "TRANSFORMABLE_MAPPING requires a compatible state basis"
                )
            if self.required_transformation.upper() in {"NONE", "BLOCKED", "NOT_APPLICABLE"}:
                raise ParameterSchemaError(
                    "TRANSFORMABLE_MAPPING requires an explicit transformation"
                )
            if self.transformation_derivation.upper() in {
                "NONE",
                "NOT_AVAILABLE",
                "TO_BE_DERIVED",
            }:
                raise ParameterSchemaError(
                    "TRANSFORMABLE_MAPPING requires a derivation"
                )
        else:
            if self.transformation_possible:
                raise ParameterSchemaError(
                    f"{status.value} cannot advertise a permitted transformation"
                )
            if self.required_transformation.upper() not in {
                "BLOCKED",
                "NOT_APPLICABLE",
                "NONE",
            }:
                raise ParameterSchemaError(
                    f"{status.value} must keep transformation blocked"
                )
        if status in {
            MappingStatus.CONCEPTUAL_ANALOGUE,
            MappingStatus.NO_MAPPING,
            MappingStatus.SOURCE_UNAVAILABLE,
        } and self.can_enter_validation:
            raise ParameterSchemaError(
                f"{status.value} cannot enter validation"
            )

    @property
    def can_enter_validation(self) -> bool:
        """Whether this semantic record is eligible for later evidence recovery."""

        return (
            self.mapping_status
            in {MappingStatus.DIRECT_MAPPING, MappingStatus.TRANSFORMABLE_MAPPING}
            and self.review_status is MappingReviewStatus.INDEPENDENT_REVIEWED
            and self.current_status not in {"ACTIVE", "REJECTED"}
            and self.future_evidence_recovery_allowed
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "UFOTRIParameterMappingRecord":
        payload = dict(require_mapping(value, field="ufotri_mapping_record"))
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ParameterSchemaError(
                f"invalid UFOTRI mapping record: {exc}"
            ) from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "v3_parameter_id": self.v3_parameter_id,
            "v3_subsystem": self.v3_subsystem,
            "v3_symbol": self.v3_symbol,
            "v3_equation": self.v3_equation,
            "v3_quantity_definition": self.v3_quantity_definition,
            "v3_canonical_unit": self.v3_canonical_unit,
            "v3_state_basis": self.v3_state_basis,
            "ufotri_source_id": self.ufotri_source_id,
            "ufotri_symbol": self.ufotri_symbol,
            "ufotri_equation": self.ufotri_equation,
            "ufotri_quantity_definition": self.ufotri_quantity_definition,
            "ufotri_reported_unit": self.ufotri_reported_unit,
            "ufotri_compartment": self.ufotri_compartment,
            "ufotri_time_basis": self.ufotri_time_basis,
            "mapping_status": self.mapping_status.value,
            "unit_relationship": self.unit_relationship,
            "equation_relationship": self.equation_relationship,
            "compartment_relationship": self.compartment_relationship,
            "state_basis_relationship": self.state_basis_relationship,
            "required_transformation": self.required_transformation,
            "transformation_possible": self.transformation_possible,
            "future_evidence_recovery_allowed": self.future_evidence_recovery_allowed,
            "transformation_derivation": self.transformation_derivation,
            "mapping_notes": self.mapping_notes,
            "review_status": self.review_status.value,
            "current_status": self.current_status,
            "provenance": self.provenance.to_mapping(),
        }


@dataclass(frozen=True)
class UFOTRIMappingRegistry:
    """Sorted mapping manifest with a P7.6C-2 fail-closed gate."""

    records: tuple[UFOTRIParameterMappingRecord, ...]
    required_v3_parameter_ids: tuple[str, ...]
    stage: str = "P7.6C-2"
    schema_version: str = "v1"
    ufotri_mapping_complete: bool = True
    source_inventory_complete: bool = True
    new_validation_candidates: int = 0
    validated_parameters: int = 1
    active_parameters: int = 0
    calibration_started: bool = False
    ufotri_parameter_imported: bool = False
    ufotri_active_database: bool = False
    physics_changed: bool = False
    numerical_coupling_changed: bool = False
    v3_physics_ready: bool = False

    def __post_init__(self) -> None:
        require_text(self.stage, field="stage")
        require_text(self.schema_version, field="schema_version")
        records = tuple(self.records)
        if any(not isinstance(item, UFOTRIParameterMappingRecord) for item in records):
            raise ParameterRegistryError(
                "records must contain UFOTRIParameterMappingRecord values"
            )
        ordered = tuple(sorted(records, key=lambda item: item.mapping_id))
        mapping_ids = [item.mapping_id for item in ordered]
        parameter_ids = [item.v3_parameter_id for item in ordered]
        if len(mapping_ids) != len(set(mapping_ids)):
            raise ParameterRegistryError("duplicate mapping_id values")
        if len(parameter_ids) != len(set(parameter_ids)):
            raise ParameterRegistryError("duplicate v3_parameter_id values")
        required = tuple(sorted(self.required_v3_parameter_ids))
        if len(required) != len(set(required)):
            raise ParameterRegistryError(
                "required_v3_parameter_ids must be unique"
            )
        for index, parameter_id in enumerate(required):
            require_identifier(parameter_id, field=f"required_v3_parameter_ids[{index}]")
        object.__setattr__(self, "records", ordered)
        object.__setattr__(self, "required_v3_parameter_ids", required)
        self.validate_manifest()

    @classmethod
    def from_records(
        cls,
        records: Iterable[UFOTRIParameterMappingRecord],
        *,
        required_v3_parameter_ids: Iterable[str],
        **kwargs: Any,
    ) -> "UFOTRIMappingRegistry":
        return cls(
            records=tuple(records),
            required_v3_parameter_ids=tuple(required_v3_parameter_ids),
            **kwargs,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "UFOTRIMappingRegistry":
        payload = dict(require_mapping(value, field="ufotri_mapping_manifest"))
        raw_records = payload.get("parameters")
        if not isinstance(raw_records, list):
            raise ParameterSchemaError(
                "ufotri_mapping_manifest.parameters must be a list"
            )
        records = [UFOTRIParameterMappingRecord.from_mapping(item) for item in raw_records]
        required = payload.get("required_v3_parameter_ids")
        if not isinstance(required, list):
            raise ParameterSchemaError(
                "required_v3_parameter_ids must be a list"
            )
        supported = {
            "stage",
            "schema_version",
            "ufotri_mapping_complete",
            "source_inventory_complete",
            "new_validation_candidates",
            "validated_parameters",
            "active_parameters",
            "calibration_started",
            "ufotri_parameter_imported",
            "ufotri_active_database",
            "physics_changed",
            "numerical_coupling_changed",
            "v3_physics_ready",
        }
        kwargs = {key: payload[key] for key in supported if key in payload}
        return cls(
            records=tuple(records),
            required_v3_parameter_ids=tuple(required),
            **kwargs,
        )

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "UFOTRIMappingRegistry":
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            raise ParameterRegistryError("PyYAML is required to load a manifest") from exc
        manifest_path = Path(path)
        try:
            payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ParameterRegistryError(f"cannot read manifest {manifest_path}") from exc
        return cls.from_mapping(payload)

    def validate_manifest(self) -> None:
        actual = {item.v3_parameter_id for item in self.records}
        required = set(self.required_v3_parameter_ids)
        if actual != required:
            missing = sorted(required - actual)
            extra = sorted(actual - required)
            raise ParameterRegistryError(
                f"mapping records must exactly cover required V3 parameters; "
                f"missing={missing}, extra={extra}"
            )
        if not self.ufotri_mapping_complete or not self.source_inventory_complete:
            raise ParameterRegistryError(
                "P7.6C-2 manifest cannot be complete while a completion flag is false"
            )
        for field in (
            "new_validation_candidates",
            "validated_parameters",
            "active_parameters",
        ):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ParameterRegistryError(f"{field} must be a non-negative integer")
        if self.new_validation_candidates != 0:
            raise ParameterRegistryError(
                "P7.6C-2 cannot create validation candidates"
            )
        if self.validated_parameters != 1 or self.active_parameters != 0:
            raise ParameterRegistryError(
                "P7.6C-2 must preserve the P7.6C-1 validated=1 active=0 snapshot"
            )
        active_ids = [
            item.v3_parameter_id
            for item in self.records
            if item.current_status == "ACTIVE"
        ]
        if active_ids:
            raise ParameterRegistryError(
                "P7.6C-2 cannot contain ACTIVE mapping records: "
                + ", ".join(active_ids)
            )
        validated_ids = [
            item.v3_parameter_id
            for item in self.records
            if item.current_status == "VALIDATED"
        ]
        if validated_ids != ["soil.tritium_half_life"]:
            raise ParameterRegistryError(
                "P7.6C-2 may preserve only the P7.6C-1 soil half-life validation"
            )
        for field in (
            "calibration_started",
            "ufotri_parameter_imported",
            "ufotri_active_database",
            "physics_changed",
            "numerical_coupling_changed",
            "v3_physics_ready",
        ):
            if not isinstance(getattr(self, field), bool) or getattr(self, field):
                raise ParameterRegistryError(
                    f"{field} must remain false in P7.6C-2"
                )

    def get(self, parameter_id: str) -> UFOTRIParameterMappingRecord:
        for record in self.records:
            if record.v3_parameter_id == parameter_id:
                return record
        raise KeyError(parameter_id)

    def counts_by_status(self) -> dict[str, int]:
        counts = Counter(record.mapping_status.value for record in self.records)
        return {
            status.value: counts.get(status.value, 0)
            for status in MappingStatus
        }

    def to_mapping(self) -> dict[str, Any]:
        self.validate_manifest()
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "ufotri_mapping_complete": self.ufotri_mapping_complete,
            "source_inventory_complete": self.source_inventory_complete,
            "new_validation_candidates": self.new_validation_candidates,
            "validated_parameters": self.validated_parameters,
            "active_parameters": self.active_parameters,
            "calibration_started": self.calibration_started,
            "ufotri_parameter_imported": self.ufotri_parameter_imported,
            "ufotri_active_database": self.ufotri_active_database,
            "physics_changed": self.physics_changed,
            "numerical_coupling_changed": self.numerical_coupling_changed,
            "v3_physics_ready": self.v3_physics_ready,
            "required_v3_parameter_ids": list(self.required_v3_parameter_ids),
            "parameters": [item.to_mapping() for item in self.records],
        }


def can_enter_validation(record: UFOTRIParameterMappingRecord) -> bool:
    """Expose the later-evidence gate without creating any candidate."""

    return isinstance(record, UFOTRIParameterMappingRecord) and record.can_enter_validation


__all__ = [
    "MappingReviewStatus",
    "MappingStatus",
    "UFOTRIParameterMappingRecord",
    "UFOTRIMappingRegistry",
    "can_enter_validation",
]
