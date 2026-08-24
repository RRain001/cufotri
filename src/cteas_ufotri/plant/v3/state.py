"""Public V3 plant pathway state facade."""

from __future__ import annotations

from dataclasses import dataclass

from ..tfwt_v3 import TFWTState


@dataclass(frozen=True)
class V3PlantState:
    """Current V3 state with an explicit, unimplemented OBT reservation."""

    tfwt: TFWTState
    obt: None = None

    @property
    def plant_identifier(self) -> str:
        return self.tfwt.plant_identifier

    def inventory(self) -> float:
        """Expose the public TFWT inventory without leaking internals."""

        return self.tfwt.inventory()

    def activity_concentration(self) -> float:
        """Expose the public TFWT activity concentration."""

        return self.tfwt.activity_concentration()


__all__ = ["V3PlantState"]
