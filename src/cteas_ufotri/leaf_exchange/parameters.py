"""Parameter access for the V3-P1 Leaf Exchange framework."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping

from ..parameters import ParameterDatabase, ParameterUnavailableError
from ..parameters.provenance import ParameterProvenance


DEFAULT_PARAMETER_NAMES: Mapping[str, str] = MappingProxyType(
    {
        "tfwt_exchange_rate_s": "leaf_exchange.tfwt_exchange_rate",
        "obt_formation_rate_s": "leaf_exchange.obt_formation_rate",
        "obt_decay_rate_s": "leaf_exchange.obt_decay_rate",
        "air_to_tfwt_partition_m3_per_kg": "leaf_exchange.air_to_tfwt_partition",
    }
)

EXPECTED_PARAMETER_UNITS: Mapping[str, str] = MappingProxyType(
    {
        "tfwt_exchange_rate_s": "s-1",
        "obt_formation_rate_s": "s-1",
        "obt_decay_rate_s": "s-1",
        "air_to_tfwt_partition_m3_per_kg": "m3 kg-1",
    }
)


class LeafExchangeParameterError(ValueError):
    """Raised when the Leaf Exchange parameter bundle is unusable."""


def _finite_nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise LeafExchangeParameterError(f"{name} must be finite and non-negative")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0.0:
        raise LeafExchangeParameterError(f"{name} must be finite and non-negative")
    return numeric


@dataclass(frozen=True, slots=True)
class LeafExchangeParameters:
    """Typed values resolved exclusively through :class:`ParameterDatabase`.

    This bundle is deliberately marked ``TEST_ONLY`` in P1.  It is suitable
    for deterministic framework tests only; it is not a UFOTRI parameter set.
    """

    tfwt_exchange_rate_s: float
    obt_formation_rate_s: float
    obt_decay_rate_s: float
    air_to_tfwt_partition_m3_per_kg: float
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
    ) -> "LeafExchangeParameters":
        """Resolve all required values with ``get_entry`` and fail closed.

        The default names are intentionally not added to the existing P0
        placeholder file.  A caller must provide an explicit synthetic test
        database until the UFOTRI parameter mapping is reviewed.
        """

        required = tuple(DEFAULT_PARAMETER_NAMES)
        missing_roles = [role for role in required if role not in parameter_names]
        if missing_roles:
            raise LeafExchangeParameterError(
                f"Missing Leaf Exchange parameter roles: {missing_roles}"
            )

        resolved_values: dict[str, float] = {}
        resolved_provenance: dict[str, ParameterProvenance] = {}
        resolved_names: dict[str, str] = {}
        for role in required:
            name = parameter_names[role]
            if not isinstance(name, str) or not name.startswith("leaf_exchange."):
                raise LeafExchangeParameterError(
                    f"Leaf Exchange parameter {role!r} must use the leaf_exchange namespace"
                )
            entry = parameter_db.get_entry(name)
            if entry.value is None:
                raise ParameterUnavailableError(
                    f"Parameter {name!r} is a placeholder and cannot drive P1 arithmetic"
                )
            expected_unit = EXPECTED_PARAMETER_UNITS[role]
            if entry.unit != expected_unit:
                raise LeafExchangeParameterError(
                    f"Parameter {name!r} has unit {entry.unit!r}; "
                    f"expected {expected_unit!r}"
                )
            resolved_values[role] = _finite_nonnegative(entry.value, name)
            resolved_provenance[role] = parameter_db.get_provenance(name)
            resolved_names[role] = name

        return cls(
            tfwt_exchange_rate_s=resolved_values["tfwt_exchange_rate_s"],
            obt_formation_rate_s=resolved_values["obt_formation_rate_s"],
            obt_decay_rate_s=resolved_values["obt_decay_rate_s"],
            air_to_tfwt_partition_m3_per_kg=resolved_values[
                "air_to_tfwt_partition_m3_per_kg"
            ],
            parameter_names=MappingProxyType(resolved_names),
            provenance=MappingProxyType(resolved_provenance),
            database_hash=parameter_db.hash(),
        )

    def provenance_mapping(self) -> dict[str, object]:
        """Return a serializable parameter/provenance record."""

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
