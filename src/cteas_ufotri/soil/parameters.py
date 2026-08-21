"""ParameterDatabase access for the V3-P2 soil framework."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping

from ..parameters import ParameterDatabase, ParameterUnavailableError
from ..parameters.provenance import ParameterProvenance


DEFAULT_PARAMETER_NAMES: Mapping[str, str] = MappingProxyType(
    {
        "interlayer_transport_rate_s": "soil.interlayer_transport_rate",
        "decay_rate_s": "soil.decay_rate",
    }
)

EXPECTED_PARAMETER_UNITS: Mapping[str, str] = MappingProxyType(
    {
        "interlayer_transport_rate_s": "s-1",
        "decay_rate_s": "s-1",
    }
)


class SoilParameterError(ValueError):
    """Raised when the soil parameter bundle is unusable."""


def _finite_nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise SoilParameterError(f"{name} must be finite and non-negative")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise SoilParameterError(f"{name} must be finite and non-negative") from exc
    if not math.isfinite(numeric) or numeric < 0.0:
        raise SoilParameterError(f"{name} must be finite and non-negative")
    return numeric


@dataclass(frozen=True, slots=True)
class SoilParameters:
    """Typed test-only values resolved only through ``get_entry``."""

    interlayer_transport_rate_s: float
    decay_rate_s: float
    parameter_names: Mapping[str, str]
    provenance: Mapping[str, ParameterProvenance]
    database_hash: str
    status: str = "TEST_ONLY"

    @classmethod
    def from_database(
        cls,
        parameter_db: ParameterDatabase,
        *,
        parameter_names: Mapping[str, str] = DEFAULT_PARAMETER_NAMES,
    ) -> "SoilParameters":
        required = tuple(DEFAULT_PARAMETER_NAMES)
        missing = [role for role in required if role not in parameter_names]
        if missing:
            raise SoilParameterError(f"Missing soil parameter roles: {missing}")

        values: dict[str, float] = {}
        provenance: dict[str, ParameterProvenance] = {}
        names: dict[str, str] = {}
        for role in required:
            name = parameter_names[role]
            if not isinstance(name, str) or not name.startswith("soil."):
                raise SoilParameterError(
                    f"Soil parameter {role!r} must use the soil namespace"
                )
            entry = parameter_db.get_entry(name)
            if entry.value is None:
                raise ParameterUnavailableError(
                    f"Parameter {name!r} is a placeholder and cannot drive P2 arithmetic"
                )
            expected_unit = EXPECTED_PARAMETER_UNITS[role]
            if entry.unit != expected_unit:
                raise SoilParameterError(
                    f"Parameter {name!r} has unit {entry.unit!r}; "
                    f"expected {expected_unit!r}"
                )
            values[role] = _finite_nonnegative(entry.value, name)
            provenance[role] = parameter_db.get_provenance(name)
            names[role] = name

        return cls(
            interlayer_transport_rate_s=values["interlayer_transport_rate_s"],
            decay_rate_s=values["decay_rate_s"],
            parameter_names=MappingProxyType(names),
            provenance=MappingProxyType(provenance),
            database_hash=parameter_db.hash(),
        )

    def provenance_mapping(self) -> dict[str, object]:
        """Return serializable parameter provenance for result metadata."""

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
