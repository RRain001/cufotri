"""UFOTRI root evidence retained as non-active reference fixtures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UFOTRIRootReferenceEvidenceV4:
    layer_ids: tuple[str, str, str] = ("L1", "L2", "L3")
    layer_depth_m: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] = (
        (0.00, 0.05),
        (0.05, 0.15),
        (0.15, 0.30),
    )
    long_term_layer_water_uptake_fraction: tuple[float, float, float] = (0.20, 0.40, 0.40)
    long_term_transfer_rate_d_minus_1: tuple[float, float, float] = (0.026, 0.026, 0.017)
    short_term_transpiration_to_root_delay_h: float = 3.0
    source_id: str = "KfK_4605_manual"
    long_term_status: str = "REFERENCE_EVIDENCE_NOT_ACTIVE_PARAMETERIZATION"
    short_term_status: str = "REFERENCE_EVIDENCE_NOT_RUNTIME_ACTIVATION"
    runtime_activation: bool = False


UFOTRI_ROOT_REFERENCE_EVIDENCE_V4 = UFOTRIRootReferenceEvidenceV4()


__all__ = ["UFOTRIRootReferenceEvidenceV4", "UFOTRI_ROOT_REFERENCE_EVIDENCE_V4"]
