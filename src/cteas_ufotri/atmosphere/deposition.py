from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SurfaceDepositionLedger:
    """Allocate one authoritative plume loss to a modelled surface footprint."""

    plume_loss_bq_s: float
    footprint_area_m2: float
    allocation: str = "uniform"

    def __post_init__(self) -> None:
        if self.plume_loss_bq_s < 0:
            raise ValueError("Plume deposition loss must be non-negative")
        if self.footprint_area_m2 <= 0:
            raise ValueError("Deposition footprint area must be positive")
        if self.allocation != "uniform":
            raise ValueError(
                f"Unsupported deposition-footprint allocation: {self.allocation}"
            )

    @property
    def surface_flux_bq_m2_s(self) -> float:
        return self.plume_loss_bq_s / self.footprint_area_m2

    @property
    def surface_input_bq_s(self) -> float:
        # The plume loss is the authoritative activity ledger.  The local
        # flux is only its spatial representation and must not be multiplied
        # back to create a second, round-trip-rounded source value.
        return self.plume_loss_bq_s

    @property
    def interface_residual_bq_s(self) -> float:
        return self.plume_loss_bq_s - self.surface_input_bq_s


def surface_deposition_ledger(
    plume_loss_bq_s: float,
    footprint: dict,
) -> SurfaceDepositionLedger:
    """Build the dry or wet surface allocation from a plume-side loss."""

    return SurfaceDepositionLedger(
        plume_loss_bq_s=max(float(plume_loss_bq_s), 0.0),
        footprint_area_m2=float(footprint["area_m2"]),
        allocation=str(footprint["allocation"]),
    )


@dataclass(frozen=True)
class DepositionActivityComponents:
    """Keep dry and wet footprint activities distinct before ecological coupling.

    The pathway footprints define local deposition fluxes.  The downstream
    ecological box has its own explicit reference area, so each authoritative
    activity is divided by that reference area only after the two component
    activities have been recorded.  No equality between dry and wet footprint
    areas is assumed.
    """

    dry: SurfaceDepositionLedger
    wet: SurfaceDepositionLedger
    ecological_reference_area_m2: float

    def __post_init__(self) -> None:
        if self.ecological_reference_area_m2 <= 0:
            raise ValueError("Ecological reference area must be positive")

    @property
    def dry_activity_bq_s(self) -> float:
        return self.dry.surface_input_bq_s

    @property
    def wet_activity_bq_s(self) -> float:
        return self.wet.surface_input_bq_s

    @property
    def total_activity_bq_s(self) -> float:
        return self.dry_activity_bq_s + self.wet_activity_bq_s

    @property
    def dry_ecological_flux_bq_m2_s(self) -> float:
        return self.dry_activity_bq_s / self.ecological_reference_area_m2

    @property
    def wet_ecological_flux_bq_m2_s(self) -> float:
        return self.wet_activity_bq_s / self.ecological_reference_area_m2


def deposition_activity_components(
    dry: SurfaceDepositionLedger,
    wet: SurfaceDepositionLedger,
    ecological_reference_area_m2: float,
) -> DepositionActivityComponents:
    """Build the explicit dry/wet activity contract for ecological coupling."""

    return DepositionActivityComponents(
        dry=dry,
        wet=wet,
        ecological_reference_area_m2=float(ecological_reference_area_m2),
    )
