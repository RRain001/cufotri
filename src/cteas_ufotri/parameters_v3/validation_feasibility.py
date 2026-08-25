"""P7.6C-3 UFOTRI validation-feasibility control plane.

This module classifies the feasibility of validating the quantities already
recorded by the P7.6C-2 semantic mapping.  It contains no parameter values,
does not resolve a runtime parameter, and cannot activate a solver.  A
``PHYSICS_REDESIGN_REQUIRED`` record is a model-design gate, not a deferred
numeric candidate.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .validation import (
    ParameterEvidenceError,
    ParameterLifecycleError,
    ParameterRegistryError,
    ParameterSchemaError,
    ValidationProvenance,
    coerce_enum,
    require_identifier,
    require_mapping,
    require_text,
)


class ValidationFeasibility(str, Enum):
    """Frozen decision states for a mapped UFOTRI-related quantity."""

    VALIDATION_FEASIBLE = "VALIDATION_FEASIBLE"
    VALIDATION_FEASIBLE_WITH_LIMITATIONS = "VALIDATION_FEASIBLE_WITH_LIMITATIONS"
    PHYSICS_REDESIGN_REQUIRED = "PHYSICS_REDESIGN_REQUIRED"
    NOT_IMPORTABLE = "NOT_IMPORTABLE"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


_VALIDATION_ALLOWED = frozenset(
    {
        ValidationFeasibility.VALIDATION_FEASIBLE,
        ValidationFeasibility.VALIDATION_FEASIBLE_WITH_LIMITATIONS,
    }
)
_KNOWN_V3_STATUS = frozenset(
    {"PROVISIONAL", "EVIDENCE_FOUND", "VALIDATED", "ACTIVE", "REJECTED"}
)


@dataclass(frozen=True)
class ParameterValidationFeasibilityRecord:
    """Immutable feasibility decision for one mapping or derived quantity."""

    mapping_id: str
    parameter_id: str
    subsystem: str
    current_v3_equation: str
    ufotri_mapping_status: str
    validation_feasibility: ValidationFeasibility | str
    physics_alignment: str
    required_action: str
    validation_data_requirement: str
    uncertainty_source: str
    blocking_reason: str
    review_notes: str
    provenance: ValidationProvenance | Mapping[str, Any]
    current_v3_status: str = "PROVISIONAL"
    derived_quantity: bool = False

    def __post_init__(self) -> None:
        for field in (
            "mapping_id",
            "parameter_id",
        ):
            require_identifier(getattr(self, field), field=field)
        for field in (
            "subsystem",
            "current_v3_equation",
            "ufotri_mapping_status",
            "physics_alignment",
            "required_action",
            "validation_data_requirement",
            "uncertainty_source",
            "blocking_reason",
            "review_notes",
        ):
            require_text(getattr(self, field), field=field)
        status = coerce_enum(
            self.validation_feasibility,
            ValidationFeasibility,
            field="validation_feasibility",
        )
        object.__setattr__(self, "validation_feasibility", status)
        current_status = require_text(
            self.current_v3_status,
            field="current_v3_status",
        ).upper()
        if current_status not in _KNOWN_V3_STATUS:
            raise ParameterSchemaError(
                "current_v3_status must be a known V3 evidence status"
            )
        object.__setattr__(self, "current_v3_status", current_status)
        if not isinstance(self.derived_quantity, bool):
            raise ParameterSchemaError("derived_quantity must be a boolean")
        provenance = self.provenance
        if not isinstance(provenance, ValidationProvenance):
            provenance = ValidationProvenance.from_mapping(provenance)
        object.__setattr__(self, "provenance", provenance)

        if status in _VALIDATION_ALLOWED and not self.blocking_reason.strip() in {
            "NONE",
            "LIMITATION_ONLY",
        }:
            raise ParameterSchemaError(
                "validation-feasible records must use blocking_reason NONE "
                "or LIMITATION_ONLY"
            )
        if status in {
            ValidationFeasibility.PHYSICS_REDESIGN_REQUIRED,
            ValidationFeasibility.NOT_IMPORTABLE,
            ValidationFeasibility.INSUFFICIENT_INFORMATION,
        } and self.blocking_reason.strip() in {"", "NONE"}:
            raise ParameterSchemaError(
                f"{status.value} requires a non-empty blocking_reason"
            )
        if status is ValidationFeasibility.NOT_IMPORTABLE and self.derived_quantity:
            raise ParameterSchemaError("a derived quantity cannot be NOT_IMPORTABLE")

    @property
    def can_enter_validation(self) -> bool:
        """Whether this decision permits a future validation workflow."""

        return self.validation_feasibility in _VALIDATION_ALLOWED

    @property
    def can_activate(self) -> bool:
        """P7.6C-3 never permits runtime activation."""

        return False

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "ParameterValidationFeasibilityRecord":
        payload = dict(require_mapping(value, field="validation_feasibility_record"))
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ParameterSchemaError(
                f"invalid validation-feasibility record: {exc}"
            ) from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "parameter_id": self.parameter_id,
            "subsystem": self.subsystem,
            "current_v3_equation": self.current_v3_equation,
            "ufotri_mapping_status": self.ufotri_mapping_status,
            "validation_feasibility": self.validation_feasibility.value,
            "physics_alignment": self.physics_alignment,
            "required_action": self.required_action,
            "validation_data_requirement": self.validation_data_requirement,
            "uncertainty_source": self.uncertainty_source,
            "blocking_reason": self.blocking_reason,
            "review_notes": self.review_notes,
            "current_v3_status": self.current_v3_status,
            "derived_quantity": self.derived_quantity,
            "provenance": self.provenance.to_mapping(),
        }


@dataclass(frozen=True)
class ParameterValidationFeasibilityRegistry:
    """Complete P7.6C-3 decision matrix with fail-closed lifecycle flags."""

    records: tuple[ParameterValidationFeasibilityRecord, ...]
    required_v3_parameter_ids: tuple[str, ...]
    stage: str = "P7.6C-3"
    schema_version: str = "v1"
    status: str = "PASS_VALIDATION_FEASIBILITY_ASSESSMENT"
    all_parameters_assessed: bool = True
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
        if self.stage != "P7.6C-3":
            raise ParameterRegistryError("feasibility registry stage must be P7.6C-3")
        require_text(self.schema_version, field="schema_version")
        require_text(self.status, field="status")
        records = tuple(self.records)
        if any(
            not isinstance(record, ParameterValidationFeasibilityRecord)
            for record in records
        ):
            raise ParameterRegistryError(
                "records must contain ParameterValidationFeasibilityRecord values"
            )
        records = tuple(sorted(records, key=lambda record: record.mapping_id))
        mapping_ids = [record.mapping_id for record in records]
        parameter_ids = [record.parameter_id for record in records]
        if len(mapping_ids) != len(set(mapping_ids)):
            raise ParameterRegistryError("duplicate feasibility mapping_id values")
        if len(parameter_ids) != len(set(parameter_ids)):
            raise ParameterRegistryError("duplicate feasibility parameter_id values")
        required = tuple(sorted(self.required_v3_parameter_ids))
        if len(required) != len(set(required)):
            raise ParameterRegistryError(
                "required_v3_parameter_ids must be unique"
            )
        for index, parameter_id in enumerate(required):
            require_identifier(parameter_id, field=f"required_v3_parameter_ids[{index}]")
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "required_v3_parameter_ids", required)
        if not isinstance(self.all_parameters_assessed, bool):
            raise ParameterSchemaError("all_parameters_assessed must be a boolean")
        for field in (
            "new_validation_candidates",
            "validated_parameters",
            "active_parameters",
        ):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ParameterRegistryError(f"{field} must be a non-negative integer")
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
                    f"{field} must remain false during P7.6C-3"
                )
        self.validate_completeness()
        if self.status != "PASS_VALIDATION_FEASIBILITY_ASSESSMENT":
            raise ParameterRegistryError(
                "P7.6C-3 status must be PASS_VALIDATION_FEASIBILITY_ASSESSMENT"
            )
        if self.new_validation_candidates != 0 or self.active_parameters != 0:
            raise ParameterRegistryError(
                "P7.6C-3 cannot create candidates or activate parameters"
            )
        if self.validated_parameters != 1:
            raise ParameterRegistryError(
                "P7.6C-3 must preserve the P7.6C-1 validated=1 snapshot"
            )

    @classmethod
    def from_records(
        cls,
        records: Iterable[ParameterValidationFeasibilityRecord],
        *,
        required_v3_parameter_ids: Iterable[str],
    ) -> "ParameterValidationFeasibilityRegistry":
        return cls(
            records=tuple(records),
            required_v3_parameter_ids=tuple(required_v3_parameter_ids),
        )

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "ParameterValidationFeasibilityRegistry":
        payload = dict(require_mapping(value, field="validation_feasibility_registry"))
        if payload.get("feasibility_registry") is not True:
            raise ParameterSchemaError(
                "validation_feasibility_registry.feasibility_registry must be true"
            )
        raw_records = payload.get("parameters")
        if not isinstance(raw_records, list):
            raise ParameterSchemaError(
                "validation_feasibility_registry.parameters must be a list"
            )
        required = payload.get("required_v3_parameter_ids")
        if not isinstance(required, list):
            raise ParameterSchemaError(
                "required_v3_parameter_ids must be a list"
            )
        supported = {
            "stage",
            "schema_version",
            "status",
            "all_parameters_assessed",
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
        registry = cls(
            records=tuple(
                ParameterValidationFeasibilityRecord.from_mapping(item)
                for item in raw_records
            ),
            required_v3_parameter_ids=tuple(required),
            **kwargs,
        )
        counts = registry.counts_by_feasibility()
        declared = {
            "mapped_parameter_count": registry.mapped_parameter_count,
            "assessment_record_count": len(registry.records),
            "derived_quantity_count": registry.derived_quantity_count,
            "validation_feasible": counts[ValidationFeasibility.VALIDATION_FEASIBLE.value],
            "validation_feasible_with_limitations": counts[
                ValidationFeasibility.VALIDATION_FEASIBLE_WITH_LIMITATIONS.value
            ],
            "physics_redesign_required": counts[
                ValidationFeasibility.PHYSICS_REDESIGN_REQUIRED.value
            ],
            "not_importable": counts[ValidationFeasibility.NOT_IMPORTABLE.value],
            "insufficient_information": counts[
                ValidationFeasibility.INSUFFICIENT_INFORMATION.value
            ],
        }
        for field, actual in declared.items():
            if field in payload and payload[field] != actual:
                raise ParameterRegistryError(
                    f"{field} disagrees with feasibility records"
                )
        return registry

    @classmethod
    def from_yaml_file(
        cls,
        path: str | Path,
    ) -> "ParameterValidationFeasibilityRegistry":
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            raise ParameterRegistryError("PyYAML is required to load feasibility manifests") from exc
        manifest_path = Path(path)
        try:
            payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ParameterRegistryError(
                f"cannot read feasibility manifest {manifest_path}"
            ) from exc
        return cls.from_mapping(payload)

    def validate_completeness(self) -> None:
        """Require one non-derived assessment for every mapped V3 parameter."""

        required = set(self.required_v3_parameter_ids)
        mapped = {
            record.parameter_id
            for record in self.records
            if not record.derived_quantity
        }
        if mapped != required:
            missing = sorted(required - mapped)
            extra = sorted(mapped - required)
            raise ParameterRegistryError(
                "feasibility records must exactly cover mapping parameters; "
                f"missing={missing}, extra={extra}"
            )
        derived = [record for record in self.records if record.derived_quantity]
        if any(record.parameter_id in required for record in derived):
            raise ParameterRegistryError(
                "derived assessments cannot duplicate mapped parameter IDs"
            )
        if not self.all_parameters_assessed:
            raise ParameterRegistryError(
                "all_parameters_assessed must be true for a complete matrix"
            )

    def validate_against_mapping(self, mapping_registry: Any) -> None:
        """Cross-check every assessment against the P7.6C-2 mapping registry."""

        mapping_records = tuple(mapping_registry.records)
        by_parameter = {record.v3_parameter_id: record for record in mapping_records}
        required = set(self.required_v3_parameter_ids)
        if set(by_parameter) != required:
            raise ParameterRegistryError(
                "P7.6C-2 mapping parameter IDs disagree with the feasibility matrix"
            )
        for record in self.records:
            if record.derived_quantity:
                continue
            mapping = by_parameter[record.parameter_id]
            if record.mapping_id != mapping.mapping_id:
                raise ParameterRegistryError(
                    f"{record.parameter_id}: mapping_id reference mismatch"
                )
            if record.ufotri_mapping_status != mapping.mapping_status.value:
                raise ParameterRegistryError(
                    f"{record.parameter_id}: mapping status reference mismatch"
                )
            if record.subsystem != mapping.v3_subsystem:
                raise ParameterRegistryError(
                    f"{record.parameter_id}: subsystem reference mismatch"
                )
            if record.current_v3_equation != mapping.v3_equation:
                raise ParameterRegistryError(
                    f"{record.parameter_id}: equation reference mismatch"
                )
            if record.current_v3_status != mapping.current_status:
                raise ParameterRegistryError(
                    f"{record.parameter_id}: current status reference mismatch"
                )

    def get(self, parameter_id: str) -> ParameterValidationFeasibilityRecord:
        """Return one mapped or derived assessment by parameter ID."""

        for record in self.records:
            if record.parameter_id == parameter_id:
                return record
        raise KeyError(parameter_id)

    def counts_by_feasibility(self, *, include_derived: bool = False) -> dict[str, int]:
        records = self.records if include_derived else tuple(
            record for record in self.records if not record.derived_quantity
        )
        counts = Counter(record.validation_feasibility.value for record in records)
        return {
            state.value: counts.get(state.value, 0)
            for state in ValidationFeasibility
        }

    @property
    def mapped_parameter_count(self) -> int:
        return sum(not record.derived_quantity for record in self.records)

    @property
    def derived_quantity_count(self) -> int:
        return sum(record.derived_quantity for record in self.records)

    def assert_safe(self) -> None:
        self.validate_completeness()
        if self.active_parameters:
            raise ParameterRegistryError("P7.6C-3 cannot activate parameters")
        for field in (
            "calibration_started",
            "ufotri_parameter_imported",
            "ufotri_active_database",
            "physics_changed",
            "numerical_coupling_changed",
            "v3_physics_ready",
        ):
            if getattr(self, field):
                raise ParameterRegistryError(f"unsafe P7.6C-3 state: {field}")

    def to_mapping(self) -> dict[str, Any]:
        self.assert_safe()
        counts = self.counts_by_feasibility()
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "status": self.status,
            "feasibility_registry": True,
            "all_parameters_assessed": self.all_parameters_assessed,
            "mapped_parameter_count": self.mapped_parameter_count,
            "assessment_record_count": len(self.records),
            "derived_quantity_count": self.derived_quantity_count,
            "validation_feasible": counts[ValidationFeasibility.VALIDATION_FEASIBLE.value],
            "validation_feasible_with_limitations": counts[
                ValidationFeasibility.VALIDATION_FEASIBLE_WITH_LIMITATIONS.value
            ],
            "physics_redesign_required": counts[
                ValidationFeasibility.PHYSICS_REDESIGN_REQUIRED.value
            ],
            "not_importable": counts[ValidationFeasibility.NOT_IMPORTABLE.value],
            "insufficient_information": counts[
                ValidationFeasibility.INSUFFICIENT_INFORMATION.value
            ],
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
            "parameters": [record.to_mapping() for record in self.records],
        }


def can_enter_validation(record: ParameterValidationFeasibilityRecord) -> bool:
    """Return whether a future validation workflow may consider the record."""

    return (
        isinstance(record, ParameterValidationFeasibilityRecord)
        and record.can_enter_validation
    )


def admit_for_validation(
    record: ParameterValidationFeasibilityRecord,
) -> ParameterValidationFeasibilityRecord:
    """Fail closed when a blocked feasibility state is admitted by mistake."""

    if not can_enter_validation(record):
        raise ParameterEvidenceError(
            f"{record.parameter_id}: feasibility state "
            f"{record.validation_feasibility.value} blocks validation entry"
        )
    return record


def can_activate(record: ParameterValidationFeasibilityRecord) -> bool:
    """P7.6C-3 never permits a feasibility record to become ACTIVE."""

    return False


def reject_activation(record: ParameterValidationFeasibilityRecord) -> None:
    """Raise the explicit lifecycle error used by negative activation tests."""

    if not isinstance(record, ParameterValidationFeasibilityRecord):
        raise ParameterSchemaError("record must be a feasibility record")
    raise ParameterLifecycleError(
        f"{record.parameter_id}: P7.6C-3 cannot transition a feasibility decision to ACTIVE"
    )


__all__ = [
    "ParameterValidationFeasibilityRecord",
    "ParameterValidationFeasibilityRegistry",
    "ValidationFeasibility",
    "admit_for_validation",
    "can_activate",
    "can_enter_validation",
    "reject_activation",
]
