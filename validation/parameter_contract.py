"""Canonical frozen parameter contracts for the external-evidence gate."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence

from validation.evidence_validation import EvidenceValidationError


PARAMETER_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$", flags=re.ASCII)
ALLOWED_TRANSFORMS = {"IDENTITY", "LOG", "LOG10", "LOGIT"}
CONTRACT_FIELDS = {
    "name",
    "unit",
    "lower_bound",
    "upper_bound",
    "lower_inclusive",
    "upper_inclusive",
    "transform",
}
CALIBRATED_PARAMETER_FIELDS = {"value", "unit", "transform"}


class ParameterContractError(EvidenceValidationError):
    """A frozen parameter-contract violation with a stable gate reason."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _finite_real(value: object, *, label: str, code: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise ParameterContractError(code, f"{label} must be a finite real number")
    return float(value)


def _valid_name(value: object, *, label: str, code: str) -> str:
    if not isinstance(value, str) or PARAMETER_NAME_PATTERN.fullmatch(value) is None:
        raise ParameterContractError(
            code,
            f"{label} must match ^[a-z][a-z0-9_]*$",
        )
    return value


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def canonicalize_parameter_contract(
    parameter_contract: object,
) -> list[dict[str, Any]]:
    """Validate and sort a frozen parameter contract by ASCII parameter name."""

    if not isinstance(parameter_contract, list) or not parameter_contract:
        raise ParameterContractError(
            "FROZEN_PARAMETER_CONTRACT_INVALID",
            "frozen parameter_contract must be a non-empty list",
        )
    canonical: list[dict[str, Any]] = []
    names: list[str] = []
    for index, item in enumerate(parameter_contract):
        if not isinstance(item, Mapping) or set(item) != CONTRACT_FIELDS:
            raise ParameterContractError(
                "FROZEN_PARAMETER_CONTRACT_INVALID",
                f"parameter_contract[{index}] has missing or unknown fields",
            )
        name = _valid_name(
            item.get("name"),
            label=f"parameter_contract[{index}].name",
            code="FROZEN_PARAMETER_CONTRACT_INVALID",
        )
        names.append(name)
        unit = item.get("unit")
        if not isinstance(unit, str) or not unit.strip():
            raise ParameterContractError(
                "FROZEN_PARAMETER_CONTRACT_INVALID",
                f"parameter {name} must declare a non-empty unit",
            )
        transform = item.get("transform")
        if transform not in ALLOWED_TRANSFORMS:
            raise ParameterContractError(
                "FROZEN_PARAMETER_CONTRACT_INVALID",
                f"parameter {name} has unknown transform: {transform}",
            )
        lower = _finite_real(
            item.get("lower_bound"),
            label=f"parameter {name} lower_bound",
            code="FROZEN_PARAMETER_CONTRACT_INVALID",
        )
        upper = _finite_real(
            item.get("upper_bound"),
            label=f"parameter {name} upper_bound",
            code="FROZEN_PARAMETER_CONTRACT_INVALID",
        )
        lower_inclusive = item.get("lower_inclusive")
        upper_inclusive = item.get("upper_inclusive")
        if not isinstance(lower_inclusive, bool) or not isinstance(
            upper_inclusive, bool
        ):
            raise ParameterContractError(
                "FROZEN_PARAMETER_CONTRACT_INVALID",
                f"parameter {name} bound inclusivity must be boolean",
            )
        if lower > upper or (
            lower == upper and not (lower_inclusive and upper_inclusive)
        ):
            raise ParameterContractError(
                "FROZEN_PARAMETER_CONTRACT_INVALID",
                f"parameter {name} has an empty or reversed frozen interval",
            )
        canonical.append(
            {
                "name": name,
                "unit": unit,
                "lower_bound": lower,
                "upper_bound": upper,
                "lower_inclusive": lower_inclusive,
                "upper_inclusive": upper_inclusive,
                "transform": transform,
            }
        )
    if len(names) != len(set(names)):
        raise ParameterContractError(
            "FROZEN_PARAMETER_CONTRACT_INVALID",
            "duplicate parameter names in frozen preregistration",
        )
    return sorted(canonical, key=lambda item: item["name"])


def parameter_contract_hash(
    canonical_contract: Sequence[Mapping[str, Any]],
) -> str:
    return canonical_sha256(list(canonical_contract))


def validate_calibrated_parameters(
    canonical_contract: Sequence[Mapping[str, Any]],
    parameters: object,
    *,
    artifact_label: str,
) -> list[dict[str, Any]]:
    """Validate names, units, transforms, values, and bounds against the freeze."""

    if not isinstance(parameters, Mapping) or not parameters:
        raise ParameterContractError(
            "CALIBRATION_PARAMETER_SET_NOT_FROZEN",
            f"{artifact_label} parameters must be a non-empty mapping",
        )
    frozen_by_name = {str(item["name"]): item for item in canonical_contract}
    calibrated_names: set[str] = set()
    for raw_name in parameters:
        calibrated_names.add(
            _valid_name(
                raw_name,
                label=f"{artifact_label} parameter name",
                code="CALIBRATION_PARAMETER_SET_NOT_FROZEN",
            )
        )
    frozen_names = set(frozen_by_name)
    if calibrated_names != frozen_names:
        missing = sorted(frozen_names - calibrated_names)
        unexpected = sorted(calibrated_names - frozen_names)
        raise ParameterContractError(
            "CALIBRATION_PARAMETER_SET_NOT_FROZEN",
            "calibration parameter set differs from frozen preregistration: "
            f"missing={missing}, unexpected={unexpected}",
        )

    canonical_parameters: list[dict[str, Any]] = []
    for name in sorted(frozen_names):
        frozen = frozen_by_name[name]
        supplied = parameters[name]
        if (
            not isinstance(supplied, Mapping)
            or set(supplied) != CALIBRATED_PARAMETER_FIELDS
        ):
            raise ParameterContractError(
                "CALIBRATION_PARAMETER_CONTRACT_MISMATCH",
                f"parameter {name} must contain value, unit, and transform only",
            )
        value = _finite_real(
            supplied.get("value"),
            label=f"parameter {name} value",
            code="CALIBRATION_PARAMETER_VALUE_INVALID",
        )
        if supplied.get("unit") != frozen["unit"]:
            raise ParameterContractError(
                "CALIBRATION_PARAMETER_CONTRACT_MISMATCH",
                f"parameter {name} unit differs from frozen preregistration",
            )
        if supplied.get("transform") != frozen["transform"]:
            raise ParameterContractError(
                "CALIBRATION_PARAMETER_CONTRACT_MISMATCH",
                f"parameter {name} transform differs from frozen preregistration",
            )
        lower_pass = (
            value >= float(frozen["lower_bound"])
            if frozen["lower_inclusive"]
            else value > float(frozen["lower_bound"])
        )
        upper_pass = (
            value <= float(frozen["upper_bound"])
            if frozen["upper_inclusive"]
            else value < float(frozen["upper_bound"])
        )
        if not lower_pass or not upper_pass:
            raise ParameterContractError(
                "CALIBRATION_PARAMETER_OUT_OF_FROZEN_BOUNDS",
                f"parameter {name} is outside its frozen interval",
            )
        canonical_parameters.append(
            {
                "name": name,
                "value": value,
                "unit": frozen["unit"],
                "transform": frozen["transform"],
            }
        )
    return canonical_parameters


def parameter_result_hash(
    canonical_parameters: Sequence[Mapping[str, Any]],
) -> str:
    return canonical_sha256(list(canonical_parameters))
