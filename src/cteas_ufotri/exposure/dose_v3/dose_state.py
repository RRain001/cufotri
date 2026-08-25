"""Immutable V3 P6.6B intake-to-dose result state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .validation import (
    ANNUAL_TIME_PERIOD,
    COMMITTED_DOSE_UNIT,
    DOSE_COEFFICIENT_UNIT,
    INTAKE_INVENTORY_UNIT,
    require_finite,
    validate_dose_state,
)


@dataclass(frozen=True)
class DoseState:
    """Annual intake activity and its committed dose result."""

    consumer_identifier: str
    age_group_identifier: str
    pathway_identifier: str
    intake_inventory_bq: float
    dose_coefficient: float
    dose_coefficient_unit: str
    committed_dose_sv: float
    time_period: str
    timestamp: datetime
    provenance: Any
    intake_inventory_unit: str = INTAKE_INVENTORY_UNIT
    committed_dose_unit: str = COMMITTED_DOSE_UNIT
    version: str = "v3-p6-6b"

    def __post_init__(self) -> None:
        validate_dose_state(self)

    @classmethod
    def from_calculation(
        cls,
        *,
        consumer_identifier: str,
        age_group_identifier: str,
        pathway_identifier: str,
        intake_inventory_bq: float,
        dose_coefficient: float,
        committed_dose_sv: float,
        timestamp: datetime,
        provenance: Any,
        time_period: str = ANNUAL_TIME_PERIOD,
    ) -> "DoseState":
        """Construct a checked immutable dose result."""

        return cls(
            consumer_identifier=consumer_identifier,
            age_group_identifier=age_group_identifier,
            pathway_identifier=pathway_identifier,
            intake_inventory_bq=require_finite(
                intake_inventory_bq,
                field="intake_inventory_bq",
            ),
            dose_coefficient=require_finite(
                dose_coefficient,
                field="dose_coefficient",
            ),
            dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
            committed_dose_sv=require_finite(
                committed_dose_sv,
                field="committed_dose_sv",
            ),
            time_period=time_period,
            timestamp=timestamp,
            provenance=provenance,
        )

    def inventory(self) -> float:
        """Return the intake inventory used by the dose calculation in Bq."""

        return self.intake_inventory_bq

    def dose(self) -> float:
        """Return the committed dose result in Sv."""

        return self.committed_dose_sv

    def consumer(self) -> str:
        """Return the stable consumer identifier."""

        return self.consumer_identifier


__all__ = ["DoseState"]
