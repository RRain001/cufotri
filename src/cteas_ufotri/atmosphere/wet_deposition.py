from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WetDepositionLedger:
    scavenging_coefficient_s: float
    depleted_source_bq_s: float
    footprint_area_m2: float

    @property
    def surface_flux_bq_m2_s(self) -> float:
        if self.footprint_area_m2 <= 0:
            raise ValueError("Wet-deposition footprint area must be positive")
        return self.depleted_source_bq_s / self.footprint_area_m2


def scavenging_coefficient_s(
    precipitation_m_s: float,
    mode: str,
    *,
    constant_coefficient_s: float = 0.0,
    power_law_a_s: float = 0.0,
    power_law_b: float = 1.0,
) -> float:
    """Return Lambda_w in s-1.

    The precipitation power law uses P in mm h-1:
    ``Lambda_w = a * P**b``.  The units and provenance of ``a`` therefore
    depend on ``b`` and must be recorded with the configured parameter set.
    """
    rain_mm_h = max(float(precipitation_m_s), 0.0) * 1000.0 * 3600.0
    if mode == "off" or rain_mm_h == 0.0:
        return 0.0
    if mode == "constant_scavenging_coefficient":
        if constant_coefficient_s < 0:
            raise ValueError("Constant scavenging coefficient must be non-negative")
        return float(constant_coefficient_s)
    if mode == "precipitation_power_law":
        if power_law_a_s < 0 or power_law_b < 0:
            raise ValueError("Wet-scavenging power-law parameters must be non-negative")
        return float(power_law_a_s) * rain_mm_h ** float(power_law_b)
    raise ValueError(f"Unsupported wet-scavenging mode: {mode}")


def wet_deposition_ledger(
    depleted_source_bq_s: float,
    scavenging_rate_s: float,
    footprint_area_m2: float,
) -> WetDepositionLedger:
    return WetDepositionLedger(
        max(float(scavenging_rate_s), 0.0),
        max(float(depleted_source_bq_s), 0.0),
        float(footprint_area_m2),
    )

