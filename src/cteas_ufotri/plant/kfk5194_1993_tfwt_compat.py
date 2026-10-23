"""Opt-in 1993 canopy-resistance to TFWT *compatibility* coupling (P3 R3).

KfK5194 (1993) Eq.(4)-(10) resistance is passed into the existing
KfK4605-compatible analytic leaf-exchange operator and V3 TFWT ledger.
The old leaf-exchange operator is NOT certified as 1993 original FORTRAN.
No default model, CLI, soil, root, OBT, or ET-water-loss activation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Sequence

from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, Historical1993SourceProfile,
)
from .kfk5194_1993_canopy_et import (
    KFK5194P3Canopy, KFK5194_SOURCE_URL,
)
from .kfk5194_1993_canopy_regimes import KFK5194P3RegimeResistance
from .leaf_ufotri_v4 import (
    UFOTRIAnalyticLeafTransfer, advance_tfwt_with_ufotri_analytic_leaf_exchange,
)
from .tfwt_v3 import TFWTState, TFWTStepResult


class KFK5194CouplingError(ValueError):
    """Fail closed on incompatible area basis, model or assumptions."""


class KFK5194LeafExchangeKernel(str, Enum):
    KFK4605_EQ27_30_COMPATIBILITY = "KFK4605_EQ27_30_COMPATIBILITY"


CanopyState = KFK5194P3Canopy | KFK5194P3RegimeResistance


@dataclass(frozen=True, slots=True)
class KFK5194TFWTExposure:
    """One interval with constant HTO air concentration and leaf conditions."""

    canopy: CanopyState
    air_hto_concentration_bq_m3: float
    temperature_k: float
    isotope_fractionation_liquid_to_vapour: float
    interval_seconds: float


@dataclass(frozen=True, slots=True)
class KFK5194TFWTCompatibilityResult:
    """Dynamic state and signed leaf-exchange activity balance, per ground area."""

    profile_id: str
    branch: str
    canopy_total_resistance_s_m: float
    analytic_leaf_transfer: UFOTRIAnalyticLeafTransfer
    tfwt_step: TFWTStepResult

    @property
    def state(self) -> TFWTState:
        return self.tfwt_step.state

    @property
    def leaf_activity_transfer_bq_m2(self) -> float:
        return self.analytic_leaf_transfer.leaf_transfer_bq_m2

    @property
    def residual_bq_m2(self) -> float:
        return self.tfwt_step.balance.residual_bq_m2

    def provenance(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "source_resistance": "KFK5194_1993_EQ4_TO10",
            "resistance_branch": self.branch,
            "leaf_exchange_kernel": KFK5194LeafExchangeKernel.KFK4605_EQ27_30_COMPATIBILITY.value,
            "tfwt_storage": "V3_FROZEN_FIXED_WATER_CONTENT_LEDGER",
            "area_basis": "ground_area",
            "exact_original_1993_leaf_exchange": "NOT_ESTABLISHED",
            "mixed_edition_compatibility_not_1993_numerical_parity": True,
            "root_obt_et_water_loss_coupled": False,
            "whole_1993_runtime_activated": False,
        }


def _require_profile(profile: Historical1993SourceProfile) -> None:
    if not isinstance(profile, Historical1993SourceProfile):
        raise KFK5194CouplingError("explicit loaded 1993 P1 profile required")
    if (profile.profile_id != PROFILE_ID or profile.source_url != KFK5194_SOURCE_URL
            or dict(profile.flag_defaults).get("IMODEL") != 1
            or dict(profile.flag_printed_pages).get("IMODEL") != 54):
        raise KFK5194CouplingError("1993 model identity/IMODEL mismatch")


def _require_resistance(canopy: CanopyState) -> tuple[str, float]:
    if isinstance(canopy, KFK5194P3Canopy):
        branch = "DAYLIGHT_DRY"
        ra, rb, rc = (canopy.aerodynamic_resistance_s_m,
                      canopy.boundary_resistance_s_m,
                      canopy.canopy_resistance_s_m)
    elif isinstance(canopy, KFK5194P3RegimeResistance):
        branch = canopy.regime.value
        ra, rb, rc = (canopy.aerodynamic_resistance_s_m,
                      canopy.boundary_layer_resistance_s_m,
                      canopy.canopy_resistance_s_m)
    else:
        raise KFK5194CouplingError("validated P3 R1/R2 canopy state required")
    total = canopy.canopy_total_resistance_s_m
    if canopy.profile_id != PROFILE_ID or not all(
        isinstance(x, (float, int)) and math.isfinite(x) and x >= 0
        for x in (ra, rb, rc, total)
    ) or ra <= 0 or rb <= 0 or total <= 0:
        raise KFK5194CouplingError("invalid 1993 canopy resistance provenance/units")
    if not math.isclose(total, ra + rb + rc, rel_tol=1e-12, abs_tol=1e-12):
        raise KFK5194CouplingError("canopy resistance components do not close")
    if isinstance(canopy, KFK5194P3RegimeResistance):
        if not math.isclose(canopy.exchange_velocity_m_s, 1.0 / total,
                            rel_tol=1e-12, abs_tol=1e-15):
            raise KFK5194CouplingError("1993 branch exchange velocity is inconsistent")
    return branch, total


def _positive(value: float, field: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise KFK5194CouplingError(f"{field} must be finite SI quantity")
    if value <= 0.0:
        raise KFK5194CouplingError(f"{field} must be positive")
    return float(value)


def advance_kfk5194_tfwt_compatibility(
    *,
    profile: Historical1993SourceProfile,
    state: TFWTState,
    exposure: KFK5194TFWTExposure,
    kernel: KFK5194LeafExchangeKernel,
) -> KFK5194TFWTCompatibilityResult:
    """Apply 1993 resistance to existing analytic leaf operator and V3 storage.

    This is a *mixed-edition* explicit compatibility experiment, NOT recovered
    KfK5194-original TFWT dynamics. Area basis must be per m² GROUND, since
    Eq.(10) canopy resistance r_st/LAI is already on that basis.
    """
    _require_profile(profile)
    if kernel is not KFK5194LeafExchangeKernel.KFK4605_EQ27_30_COMPATIBILITY:
        raise KFK5194CouplingError("explicit KFK4605 compatibility kernel required")
    if not isinstance(state, TFWTState) or state.area_basis != "ground_area":
        raise KFK5194CouplingError("TFWT state must use explicit ground_area inventory")
    if not isinstance(exposure, KFK5194TFWTExposure):
        raise KFK5194CouplingError("explicit typed interval exposure required")
    branch, total = _require_resistance(exposure.canopy)
    air = exposure.air_hto_concentration_bq_m3
    if type(air) not in (int, float) or not math.isfinite(float(air)) or air < 0:
        raise KFK5194CouplingError("air_hto_concentration_bq_m3 must be nonnegative")
    temp = _positive(exposure.temperature_k, "temperature_k")
    alpha = _positive(
        exposure.isotope_fractionation_liquid_to_vapour, "isotope_fractionation"
    )
    dt = _positive(exposure.interval_seconds, "interval_seconds")
    step = advance_tfwt_with_ufotri_analytic_leaf_exchange(
        state,
        air_concentration_bq_m3=float(air),
        temperature_k=temp,
        total_resistance_s_m=total,
        isotope_fractionation_liquid_to_vapour=alpha,
        interval_seconds=dt,
    )
    leaf_transfer = step.analytic_leaf_transfer.leaf_transfer_bq_m2
    actual_delta = step.state.tfwt_inventory_bq_m2 - state.tfwt_inventory_bq_m2
    scale = max(1.0, abs(leaf_transfer), abs(state.tfwt_inventory_bq_m2))
    if (not math.isclose(actual_delta, leaf_transfer, rel_tol=1e-11,
                         abs_tol=1e-11 * scale)
            or not math.isclose(step.tfwt_step.balance.leaf_exchange_input_bq_m2,
                                leaf_transfer, rel_tol=1e-11, abs_tol=1e-11 * scale)):
        raise KFK5194CouplingError("signed TFWT mass/activity exchange failed closure")
    return KFK5194TFWTCompatibilityResult(
        profile_id=PROFILE_ID, branch=branch,
        canopy_total_resistance_s_m=total,
        analytic_leaf_transfer=step.analytic_leaf_transfer,
        tfwt_step=step.tfwt_step,
    )


def advance_kfk5194_tfwt_intervals(
    *,
    profile: Historical1993SourceProfile,
    initial_state: TFWTState,
    exposures: Sequence[KFK5194TFWTExposure],
    kernel: KFK5194LeafExchangeKernel,
) -> tuple[KFK5194TFWTCompatibilityResult, ...]:
    """Propagate hour-by-hour with validated explicit P3 regime switches."""
    if not isinstance(exposures, (list, tuple)) or not exposures:
        raise KFK5194CouplingError("at least one explicit interval required")
    state = initial_state
    results: list[KFK5194TFWTCompatibilityResult] = []
    for exposure in exposures:
        result = advance_kfk5194_tfwt_compatibility(
            profile=profile, state=state, exposure=exposure, kernel=kernel,
        )
        results.append(result)
        state = result.state
    return tuple(results)
