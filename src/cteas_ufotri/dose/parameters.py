"""ParameterDatabase integration for the V3-P4 dose interface."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping

from ..parameters import ParameterDatabase, ParameterUnavailableError
from ..parameters.provenance import ParameterProvenance


DEFAULT_PARAMETER_NAMES: Mapping[str, str] = MappingProxyType(
    {"dose_coefficient": "dose.coefficient"}
)

EXPECTED_PARAMETER_UNITS: Mapping[str, str] = MappingProxyType(
    {"dose_coefficient": "Sv Bq-1"}
)


class DoseParameterError(ValueError):
    """Raised when the P4 parameter bundle is unusable."""


def _finite_nonnegative(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise DoseParameterError(f"{name} must be finite and non-negative")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DoseParameterError(
            f"{name} must be finite and non-negative"
        ) from exc
    if not math.isfinite(numeric) or numeric < 0.0:
        raise DoseParameterError(f"{name} must be finite and non-negative")
    return numeric


@dataclass(frozen=True, slots=True)
class DoseParameters:
    """Placeholder-status values resolved from an explicit parameter DB."""

    coefficient: float
    coefficient_unit: str
    parameter_names: Mapping[str, str]
    provenance: Mapping[str, ParameterProvenance]
    database_hash: str
    status: str = "PLACEHOLDER"

    @classmethod
    def from_database(
        cls,
        parameter_db: ParameterDatabase,
        *,
        parameter_names: Mapping[str, str] = DEFAULT_PARAMETER_NAMES,
    ) -> "DoseParameters":
        required = tuple(DEFAULT_PARAMETER_NAMES)
        missing = [role for role in required if role not in parameter_names]
        if missing:
            raise DoseParameterError(f"Missing dose parameter roles: {missing}")

        values: dict[str, float] = {}
        units: dict[str, str] = {}
        names: dict[str, str] = {}
        provenance: dict[str, ParameterProvenance] = {}
        for role in required:
            name = parameter_names[role]
            if not isinstance(name, str) or not name.startswith("dose."):
                raise DoseParameterError(
                    f"Dose parameter {role!r} must use the dose namespace"
                )
            entry = parameter_db.get_entry(name)
            if entry.value is None:
                raise ParameterUnavailableError(
                    f"Parameter {name!r} is a placeholder and cannot drive P4 arithmetic"
                )
            expected_unit = EXPECTED_PARAMETER_UNITS[role]
            if entry.unit != expected_unit:
                raise DoseParameterError(
                    f"Parameter {name!r} has unit {entry.unit!r}; "
                    f"expected {expected_unit!r}"
                )
            values[role] = _finite_nonnegative(entry.value, name)
            units[role] = entry.unit
            names[role] = name
            provenance[role] = parameter_db.get_provenance(name)

        return cls(
            coefficient=values["dose_coefficient"],
            coefficient_unit=units["dose_coefficient"],
            parameter_names=MappingProxyType(names),
            provenance=MappingProxyType(provenance),
            database_hash=parameter_db.hash(),
        )

    def provenance_mapping(self) -> dict[str, object]:
        """Return serializable dose-parameter provenance."""

        return {
            "status": self.status,
            "database_sha256": self.database_hash,
            "parameters": {
                role: {
                    "name": self.parameter_names[role],
                    **self.provenance[role].to_mapping(),
                }
                for role in sorted(self.parameter_names)
            },
        }


ParameterError = DoseParameterError
