"""P7.6D V3 physics-adoption and redesign control plane.

This module records model decisions made after the P7.6C-3 feasibility
assessment.  It is deliberately separate from production plant, soil,
exposure, coupling, and pipeline code.  A decision is not a parameter value,
validation approval, calibration result, or runtime lookup.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .validation import (
    ParameterLifecycleError,
    ParameterRegistryError,
    ParameterSchemaError,
    coerce_enum,
    require_identifier,
    require_mapping,
    require_text,
)
from .validation_feasibility import (
    ParameterValidationFeasibilityRegistry,
    ValidationFeasibility,
)


class PhysicsAdoptionDecision(str, Enum):
    """Frozen P7.6D decisions for the current V3 model boundary."""

    KEEP_CURRENT_V3 = "KEEP_CURRENT_V3"
    VALIDATE_CURRENT_MODEL = "VALIDATE_CURRENT_MODEL"
    EXTEND_V3_PHYSICS = "EXTEND_V3_PHYSICS"
    REDESIGN_REQUIRED = "REDESIGN_REQUIRED"
    DO_NOT_IMPORT = "DO_NOT_IMPORT"
    WAIT_FOR_EVIDENCE = "WAIT_FOR_EVIDENCE"


class CouplingImpact(str, Enum):
    """Whether a future redesign changes a numerical boundary."""

    NO_IMPACT = "NO_IMPACT"
    INTERFACE_ONLY = "INTERFACE_ONLY"
    NUMERICAL_COUPLING_CHANGE_REQUIRED = "NUMERICAL_COUPLING_CHANGE_REQUIRED"


class DecisionPriority(str, Enum):
    """Priority tier for a future decision or redesign action."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


_FEASIBILITY_TO_DECISIONS = {
    ValidationFeasibility.VALIDATION_FEASIBLE: frozenset(
        {
            PhysicsAdoptionDecision.KEEP_CURRENT_V3,
            PhysicsAdoptionDecision.VALIDATE_CURRENT_MODEL,
            PhysicsAdoptionDecision.EXTEND_V3_PHYSICS,
        }
    ),
    ValidationFeasibility.VALIDATION_FEASIBLE_WITH_LIMITATIONS: frozenset(
        {
            PhysicsAdoptionDecision.KEEP_CURRENT_V3,
            PhysicsAdoptionDecision.VALIDATE_CURRENT_MODEL,
            PhysicsAdoptionDecision.EXTEND_V3_PHYSICS,
        }
    ),
    ValidationFeasibility.PHYSICS_REDESIGN_REQUIRED: frozenset(
        {PhysicsAdoptionDecision.REDESIGN_REQUIRED}
    ),
    ValidationFeasibility.NOT_IMPORTABLE: frozenset(
        {PhysicsAdoptionDecision.DO_NOT_IMPORT}
    ),
    ValidationFeasibility.INSUFFICIENT_INFORMATION: frozenset(
        {PhysicsAdoptionDecision.WAIT_FOR_EVIDENCE}
    ),
}


@dataclass(frozen=True)
class PhysicsDecisionRecord:
    """One immutable adoption decision for a P7.6C-3 feasibility item."""

    parameter_id: str
    subsystem: str
    current_v3_model: str
    ufotri_reference: str
    feasibility_class: ValidationFeasibility | str
    adoption_decision: PhysicsAdoptionDecision | str
    decision_reason: str
    physics_gap: str
    required_redesign: bool
    priority: DecisionPriority | str
    impact_level: DecisionPriority | str
    coupling_impact: CouplingImpact | str
    validation_requirement: str
    future_stage: str
    provenance: Mapping[str, Any]
    feasibility_mapping_id: str
    derived_quantity: bool = False

    def __post_init__(self) -> None:
        require_identifier(self.parameter_id, field="parameter_id")
        require_identifier(
            self.feasibility_mapping_id,
            field="feasibility_mapping_id",
        )
        for field in (
            "subsystem",
            "current_v3_model",
            "ufotri_reference",
            "decision_reason",
            "physics_gap",
            "validation_requirement",
            "future_stage",
        ):
            require_text(getattr(self, field), field=field)
        feasibility = coerce_enum(
            self.feasibility_class,
            ValidationFeasibility,
            field="feasibility_class",
        )
        adoption = coerce_enum(
            self.adoption_decision,
            PhysicsAdoptionDecision,
            field="adoption_decision",
        )
        priority = coerce_enum(
            self.priority,
            DecisionPriority,
            field="priority",
        )
        impact = coerce_enum(
            self.impact_level,
            DecisionPriority,
            field="impact_level",
        )
        coupling = coerce_enum(
            self.coupling_impact,
            CouplingImpact,
            field="coupling_impact",
        )
        object.__setattr__(self, "feasibility_class", feasibility)
        object.__setattr__(self, "adoption_decision", adoption)
        object.__setattr__(self, "priority", priority)
        object.__setattr__(self, "impact_level", impact)
        object.__setattr__(self, "coupling_impact", coupling)
        if not isinstance(self.required_redesign, bool):
            raise ParameterSchemaError("required_redesign must be a boolean")
        if not isinstance(self.derived_quantity, bool):
            raise ParameterSchemaError("derived_quantity must be a boolean")
        require_mapping(self.provenance, field="provenance")

        allowed = _FEASIBILITY_TO_DECISIONS[feasibility]
        if adoption not in allowed:
            raise ParameterSchemaError(
                f"{self.parameter_id}: adoption decision {adoption.value} "
                f"is incompatible with feasibility {feasibility.value}"
            )
        is_blocking_redesign = (
            feasibility is ValidationFeasibility.PHYSICS_REDESIGN_REQUIRED
        )
        if self.required_redesign != is_blocking_redesign:
            raise ParameterSchemaError(
                f"{self.parameter_id}: required_redesign must match the "
                "P7.6C-3 PHYSICS_REDESIGN_REQUIRED state"
            )

    @property
    def can_enter_validation(self) -> bool:
        """Return the P7.6D gate result for the current frozen registry."""

        if self.required_redesign:
            return False
        if self.adoption_decision is PhysicsAdoptionDecision.DO_NOT_IMPORT:
            return False
        if self.adoption_decision is PhysicsAdoptionDecision.WAIT_FOR_EVIDENCE:
            return False
        return self.feasibility_class in {
            ValidationFeasibility.VALIDATION_FEASIBLE,
            ValidationFeasibility.VALIDATION_FEASIBLE_WITH_LIMITATIONS,
        }

    @property
    def can_activate(self) -> bool:
        """P7.6D never authorizes runtime activation."""

        return False

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PhysicsDecisionRecord":
        payload = dict(require_mapping(value, field="physics_decision_record"))
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ParameterSchemaError(
                f"invalid P7.6D physics decision record: {exc}"
            ) from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "parameter_id": self.parameter_id,
            "subsystem": self.subsystem,
            "current_v3_model": self.current_v3_model,
            "ufotri_reference": self.ufotri_reference,
            "feasibility_class": self.feasibility_class.value,
            "adoption_decision": self.adoption_decision.value,
            "decision_reason": self.decision_reason,
            "physics_gap": self.physics_gap,
            "required_redesign": self.required_redesign,
            "priority": self.priority.value,
            "impact_level": self.impact_level.value,
            "coupling_impact": self.coupling_impact.value,
            "validation_requirement": self.validation_requirement,
            "future_stage": self.future_stage,
            "provenance": dict(self.provenance),
            "feasibility_mapping_id": self.feasibility_mapping_id,
            "derived_quantity": self.derived_quantity,
        }


@dataclass(frozen=True)
class PhysicsAdoptionRegistry:
    """Complete P7.6D decision registry with fail-closed stage flags."""

    records: tuple[PhysicsDecisionRecord, ...]
    stage: str = "P7.6D"
    schema_version: str = "v1"
    status: str = "PASS_PHYSICS_ADOPTION_DECISION"
    current_v3_model: str = "FROZEN"
    all_feasibility_items_reviewed: bool = True
    redesign_items_identified: bool = True
    implementation_started: bool = False
    new_validation_candidates: int = 0
    validated_parameters: int = 1
    active_parameters: int = 0
    calibration_started: bool = False
    ufotri_active_database: bool = False
    v3_physics_ready: bool = False
    physics_changed: bool = False
    numerical_coupling_changed: bool = False

    def __post_init__(self) -> None:
        require_text(self.stage, field="stage")
        if self.stage != "P7.6D":
            raise ParameterRegistryError("P7.6D registry stage is required")
        require_text(self.schema_version, field="schema_version")
        require_text(self.status, field="status")
        if self.status != "PASS_PHYSICS_ADOPTION_DECISION":
            raise ParameterRegistryError(
                "P7.6D registry status must be PASS_PHYSICS_ADOPTION_DECISION"
            )
        if self.current_v3_model != "FROZEN":
            raise ParameterRegistryError("current_v3_model must remain FROZEN")
        records = tuple(self.records)
        if any(not isinstance(item, PhysicsDecisionRecord) for item in records):
            raise ParameterRegistryError(
                "records must contain PhysicsDecisionRecord values"
            )
        records = tuple(sorted(records, key=lambda item: item.parameter_id))
        ids = [item.parameter_id for item in records]
        if len(ids) != len(set(ids)):
            raise ParameterRegistryError("duplicate P7.6D parameter_id values")
        object.__setattr__(self, "records", records)
        if (
            not isinstance(self.all_feasibility_items_reviewed, bool)
            or not self.all_feasibility_items_reviewed
        ):
            raise ParameterRegistryError(
                "all_feasibility_items_reviewed must remain true"
            )
        if (
            not isinstance(self.redesign_items_identified, bool)
            or not self.redesign_items_identified
        ):
            raise ParameterRegistryError("redesign_items_identified must remain true")
        if (
            not isinstance(self.implementation_started, bool)
            or self.implementation_started
        ):
            raise ParameterRegistryError("implementation_started must remain false")
        if (
            not isinstance(self.new_validation_candidates, int)
            or isinstance(self.new_validation_candidates, bool)
            or self.new_validation_candidates != 0
        ):
            raise ParameterRegistryError(
                "new_validation_candidates must remain zero"
            )
        if (
            not isinstance(self.validated_parameters, int)
            or isinstance(self.validated_parameters, bool)
            or self.validated_parameters != 1
        ):
            raise ParameterRegistryError(
                "validated_parameters must preserve the P7.6C-1 count of one"
            )
        if (
            not isinstance(self.active_parameters, int)
            or isinstance(self.active_parameters, bool)
            or self.active_parameters != 0
        ):
            raise ParameterRegistryError("active_parameters must remain zero")
        for field in (
            "calibration_started",
            "ufotri_active_database",
            "v3_physics_ready",
            "physics_changed",
            "numerical_coupling_changed",
        ):
            if not isinstance(getattr(self, field), bool) or getattr(self, field):
                raise ParameterRegistryError(f"{field} must remain false during P7.6D")
        if not any(item.required_redesign for item in records):
            raise ParameterRegistryError("P7.6D must identify redesign items")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PhysicsAdoptionRegistry":
        payload = dict(require_mapping(value, field="physics_adoption_registry"))
        if payload.get("decision_registry") is not True:
            raise ParameterSchemaError(
                "physics_adoption_registry.decision_registry must be true"
            )
        raw_records = payload.get("decision_records")
        if not isinstance(raw_records, list):
            raise ParameterSchemaError(
                "physics_adoption_registry.decision_records must be a list"
            )
        supported = {
            "stage",
            "schema_version",
            "status",
            "current_v3_model",
            "all_feasibility_items_reviewed",
            "redesign_items_identified",
            "implementation_started",
            "new_validation_candidates",
            "validated_parameters",
            "active_parameters",
            "calibration_started",
            "ufotri_active_database",
            "v3_physics_ready",
            "physics_changed",
            "numerical_coupling_changed",
        }
        kwargs = {key: payload[key] for key in supported if key in payload}
        return cls(
            records=tuple(
                PhysicsDecisionRecord.from_mapping(item) for item in raw_records
            ),
            **kwargs,
        )

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "PhysicsAdoptionRegistry":
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            raise ParameterRegistryError(
                "PyYAML is required to load the P7.6D decision registry"
            ) from exc
        manifest_path = Path(path)
        try:
            payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ParameterRegistryError(
                f"cannot read P7.6D decision registry {manifest_path}"
            ) from exc
        return cls.from_mapping(payload)

    def validate_against_feasibility(
        self,
        feasibility_registry: ParameterValidationFeasibilityRegistry,
    ) -> None:
        """Require one decision for every P7.6C-3 mapped or derived item."""

        if not isinstance(
            feasibility_registry,
            ParameterValidationFeasibilityRegistry,
        ):
            raise ParameterRegistryError(
                "feasibility_registry must be a P7.6C-3 feasibility registry"
            )
        source_by_id = {
            item.parameter_id: item for item in feasibility_registry.records
        }
        decision_by_id = {item.parameter_id: item for item in self.records}
        if set(source_by_id) != set(decision_by_id):
            raise ParameterRegistryError(
                "P7.6D decisions must exactly cover P7.6C-3 assessment records"
            )
        for parameter_id, decision in decision_by_id.items():
            source = source_by_id[parameter_id]
            if decision.feasibility_mapping_id != source.mapping_id:
                raise ParameterRegistryError(
                    f"{parameter_id}: feasibility mapping reference mismatch"
                )
            if decision.feasibility_class is not source.validation_feasibility:
                raise ParameterRegistryError(
                    f"{parameter_id}: feasibility class reference mismatch"
                )
            if decision.derived_quantity != source.derived_quantity:
                raise ParameterRegistryError(
                    f"{parameter_id}: derived-quantity reference mismatch"
                )

    def get(self, parameter_id: str) -> PhysicsDecisionRecord:
        for record in self.records:
            if record.parameter_id == parameter_id:
                return record
        raise KeyError(parameter_id)

    def counts_by_decision(self) -> dict[str, int]:
        counts = Counter(item.adoption_decision.value for item in self.records)
        return {
            state.value: counts.get(state.value, 0)
            for state in PhysicsAdoptionDecision
        }

    @property
    def redesign_parameter_ids(self) -> tuple[str, ...]:
        return tuple(
            item.parameter_id for item in self.records if item.required_redesign
        )

    def assert_safe(self) -> None:
        if self.implementation_started or self.active_parameters:
            raise ParameterRegistryError("P7.6D cannot implement or activate physics")
        for field in (
            "calibration_started",
            "ufotri_active_database",
            "v3_physics_ready",
            "physics_changed",
            "numerical_coupling_changed",
        ):
            if getattr(self, field):
                raise ParameterRegistryError(f"unsafe P7.6D state: {field}")
        if any(item.can_activate for item in self.records):
            raise ParameterRegistryError("P7.6D records cannot activate")


def can_enter_validation(record: PhysicsDecisionRecord) -> bool:
    """Apply both the P7.6C-3 feasibility and P7.6D adoption gates."""

    return isinstance(record, PhysicsDecisionRecord) and record.can_enter_validation


def admit_for_validation(record: PhysicsDecisionRecord) -> PhysicsDecisionRecord:
    """Fail closed when a redesign or non-physical item reaches a gate."""

    if not can_enter_validation(record):
        raise ParameterLifecycleError(
            f"{record.parameter_id}: P7.6D decision "
            f"{record.adoption_decision.value} blocks validation entry"
        )
    return record


def can_activate(record: PhysicsDecisionRecord) -> bool:
    """P7.6D decisions never authorize runtime activation."""

    return False


__all__ = [
    "CouplingImpact",
    "DecisionPriority",
    "PhysicsAdoptionDecision",
    "PhysicsAdoptionRegistry",
    "PhysicsDecisionRecord",
    "admit_for_validation",
    "can_activate",
    "can_enter_validation",
]
