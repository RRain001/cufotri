"""Typed provenance metadata for the V3 P7 atmospheric forcing boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .validation import TIME_RESOLUTION_UNIT, validate_metadata


@dataclass(frozen=True)
class AtmosphericForcingMetadata:
    """Immutable metadata shared by future atmospheric forcing producers."""

    model_name: str
    version: str
    grid_definition: str
    time_resolution: float
    source_dataset: str
    creation_time: datetime
    quality_flag: str
    time_resolution_unit: str = TIME_RESOLUTION_UNIT

    def __post_init__(self) -> None:
        validate_metadata(self)


__all__ = ["AtmosphericForcingMetadata"]
