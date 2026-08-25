"""Fail-closed entry gates for the P7.7A baseline validation framework."""

from __future__ import annotations

from dataclasses import dataclass

from .validation_case import ParameterStatus, ScenarioType, ValidationCase


class ValidationGateError(ValueError):
    """A gate invocation contains an invalid stage-control flag."""


@dataclass(frozen=True)
class ValidationGateResult:
    """Auditable decision; an allowed result still means synthetic-only scope."""

    case_id: str
    allowed: bool
    reasons: tuple[str, ...]
    stage: str = "P7.7A"
    baseline_synthetic_only: bool = True

    def assert_allowed(self) -> None:
        if not self.allowed:
            raise ValidationGateError(
                f"validation case {self.case_id!r} is blocked: "
                + "; ".join(self.reasons)
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "case_id": self.case_id,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "baseline_synthetic_only": self.baseline_synthetic_only,
        }


_BASELINE_SCENARIOS = frozenset(
    {
        ScenarioType.SYNTHETIC_BENCHMARK,
        ScenarioType.SOFTWARE_REGRESSION,
        ScenarioType.ANALYTICAL_SEMANTIC,
    }
)


def evaluate_validation_gate(
    case: ValidationCase,
    *,
    active_parameters: int = 0,
    calibration_started: bool = False,
    ufotri_active_database: bool = False,
    ufotri_parameter_imported: bool = False,
    v3_physics_ready: bool = False,
) -> ValidationGateResult:
    """Evaluate whether a case may enter P7.7A baseline validation.

    The gate admits only software/analytical/synthetic cases using explicit
    test-only parameters.  It intentionally does not open a path for
    evaluated physical constants, empirical observations, calibration,
    parameter activation, or V3 physics readiness.
    """

    if not isinstance(case, ValidationCase):
        raise ValidationGateError("case must be a ValidationCase")
    if (
        not isinstance(active_parameters, int)
        or isinstance(active_parameters, bool)
        or active_parameters < 0
    ):
        raise ValidationGateError("active_parameters must be a non-negative integer")
    for field, value in (
        ("calibration_started", calibration_started),
        ("ufotri_active_database", ufotri_active_database),
        ("ufotri_parameter_imported", ufotri_parameter_imported),
        ("v3_physics_ready", v3_physics_ready),
    ):
        if not isinstance(value, bool):
            raise ValidationGateError(f"{field} must be a boolean")

    reasons: list[str] = []
    if case.scenario_type not in _BASELINE_SCENARIOS:
        reasons.append(
            f"scenario_type={case.scenario_type.value} is outside baseline synthetic scope"
        )
    if active_parameters != 0:
        reasons.append("active_parameters must remain zero")
    if calibration_started:
        reasons.append("calibration_started must remain false")
    if ufotri_active_database:
        reasons.append("ufotri_active_database must remain false")
    if ufotri_parameter_imported:
        reasons.append("ufotri_parameter_imported must remain false")
    if v3_physics_ready:
        reasons.append("v3_physics_ready must remain false during P7.7A")

    for parameter in case.parameter_context:
        if parameter.status is ParameterStatus.ACTIVE:
            reasons.append(
                f"parameter {parameter.parameter_id} has ACTIVE status"
            )
        elif parameter.status is not ParameterStatus.TEST_ONLY:
            reasons.append(
                f"parameter {parameter.parameter_id} is not TEST_ONLY"
            )

    return ValidationGateResult(
        case_id=case.case_id,
        allowed=not reasons,
        reasons=tuple(reasons),
    )


def can_enter_validation(
    case: ValidationCase,
    *,
    active_parameters: int = 0,
    calibration_started: bool = False,
    ufotri_active_database: bool = False,
    ufotri_parameter_imported: bool = False,
    v3_physics_ready: bool = False,
) -> bool:
    """Return whether the case is eligible for baseline synthetic validation."""

    return evaluate_validation_gate(
        case,
        active_parameters=active_parameters,
        calibration_started=calibration_started,
        ufotri_active_database=ufotri_active_database,
        ufotri_parameter_imported=ufotri_parameter_imported,
        v3_physics_ready=v3_physics_ready,
    ).allowed


__all__ = [
    "ValidationGateError",
    "ValidationGateResult",
    "can_enter_validation",
    "evaluate_validation_gate",
]
