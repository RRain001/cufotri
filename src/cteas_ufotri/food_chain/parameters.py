"""ParameterDatabase access for the V3-P3 food-chain framework."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping

from ..parameters import ParameterDatabase, ParameterUnavailableError
from ..parameters.provenance import ParameterProvenance


DEFAULT_PARAMETER_NAMES: Mapping[str, str] = MappingProxyType(
    {
        "transfer_rate_s": "food_chain.transfer_rate",
        "decay_rate_s": "food_chain.decay_rate",
    }
)

EXPECTED_PARAMETER_UNITS: Mapping[str, str] = MappingProxyType(
    {
        "transfer_rate_s": "s-1",
        "decay_rate_s": "s-1",
    }
)


class FoodChainParameterError(ValueError):
    """Raised when the food-chain parameter bundle is unusable."""


def _finite_nonnegative(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise FoodChainParameterError(f"{name} must be finite and non-negative")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise FoodChainParameterError(
            f"{name} must be finite and non-negative"
        ) from exc
    if not math.isfinite(numeric) or numeric < 0.0:
        raise FoodChainParameterError(f"{name} must be finite and non-negative")
    return numeric


@dataclass(frozen=True, slots=True)
class FoodChainParameters:
    """Typed framework/test values resolved only through ``ParameterDatabase``.

    The status remains ``PLACEHOLDER`` because no validated UFOTRI food-chain
    parameter set is imported.  Numeric values used by deterministic tests
    must come from an explicitly synthetic database.
    """

    transfer_rate_s: float
    decay_rate_s: float
    parameter_names: Mapping[str, str]
    provenance: Mapping[str, ParameterProvenance]
    database_hash: str
    status: str = "PLACEHOLDER"

    @property
    def internal_transfer_rate_s(self) -> float:
        """Descriptive alias for the synthetic internal-transfer rate."""

        return float(self.transfer_rate_s)

    @classmethod
    def from_database(
        cls,
        parameter_db: ParameterDatabase,
        *,
        parameter_names: Mapping[str, str] = DEFAULT_PARAMETER_NAMES,
    ) -> "FoodChainParameters":
        """Resolve all executable values with strict namespace/unit checks."""

        required = tuple(DEFAULT_PARAMETER_NAMES)
        missing = [role for role in required if role not in parameter_names]
        if missing:
            raise FoodChainParameterError(
                f"Missing food-chain parameter roles: {missing}"
            )

        values: dict[str, float] = {}
        provenance: dict[str, ParameterProvenance] = {}
        names: dict[str, str] = {}
        for role in required:
            name = parameter_names[role]
            if not isinstance(name, str) or not name.startswith("food_chain."):
                raise FoodChainParameterError(
                    f"Food-chain parameter {role!r} must use the food_chain namespace"
                )
            entry = parameter_db.get_entry(name)
            if entry.value is None:
                raise ParameterUnavailableError(
                    f"Parameter {name!r} is a placeholder and cannot drive P3 arithmetic"
                )
            expected_unit = EXPECTED_PARAMETER_UNITS[role]
            if entry.unit != expected_unit:
                raise FoodChainParameterError(
                    f"Parameter {name!r} has unit {entry.unit!r}; "
                    f"expected {expected_unit!r}"
                )
            values[role] = _finite_nonnegative(entry.value, name)
            provenance[role] = parameter_db.get_provenance(name)
            names[role] = name

        return cls(
            transfer_rate_s=values["transfer_rate_s"],
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


PlantParameters = FoodChainParameters
