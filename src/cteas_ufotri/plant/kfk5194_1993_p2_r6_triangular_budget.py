"""P2 R6: isolated triangular HTO->OBT->audit-sinks mathematical experiment.

Source rates: KfK 5194 (1993), printed Eq.(32), pp.22-23, COMA Tables
9-12 pp.86-89; source-checked by P2 R3. The Eq.(32) day/night factors
and Figure 11 external factor are validated by the P2 R4 audit.
Parent OBT outflow edges are the P2 R5 source-pinned table edges.

This is NOT the original UFOTRI 4.0 plant/COMA integrator. Grass/leafy
only: potato/wheat Eq.(32) formation goes to edible OBT, while the
documented parent-OBT outflow leaves a different compartment. No
feedback from any sink (including a sink named grass HTO), no exchange,
growth, radioactive decay, respiration, animals, dose, or soil.
Every pool is an independently declared Bq/m2-ground synthetic input.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from pathlib import Path

from cteas_ufotri.versioned_inputs_1993 import Historical1993SourceProfile
from .kfk5194_1993_photo_obt_rates import (
    KFK5194CropOrgan, KFK5194PhotoOBTError, KFK5194SolarPeriod,
)
from .kfk5194_1993_p2_r4_diurnal_budget import (
    KFK5194R4DayPart, KFK5194R4Hypothesis,
    audit_kfk5194_1993_r4_eq32_diurnal_budget,
)


class KFK5194R6Hypothesis(str, Enum):
    ISOLATED_TRIANGULAR_NO_SINK_FEEDBACK = "ISOLATED_TRIANGULAR_NO_SINK_FEEDBACK"


@dataclass(frozen=True, slots=True)
class KFK5194R6Sink:
    symbol_as_printed: str
    destination_as_printed: str
    rate_d_1: float
    activity_bq_m2: float


@dataclass(frozen=True, slots=True)
class KFK5194R6Step:
    period: KFK5194SolarPeriod
    duration_hours: float
    formation_rate_h_1: float
    total_parent_outflow_rate_h_1: float
    initial_hto_bq_m2: float
    final_hto_bq_m2: float
    initial_parent_obt_bq_m2: float
    final_parent_obt_bq_m2: float
    formation_bq_m2: float
    sink_transfers: tuple[KFK5194R6Sink, ...]
    closure_residual_bq_m2: float


@dataclass(frozen=True, slots=True)
class KFK5194R6Budget:
    crop_organ: KFK5194CropOrgan
    steps: tuple[KFK5194R6Step, ...]
    final_hto_bq_m2: float
    final_parent_obt_bq_m2: float
    sink_totals: tuple[KFK5194R6Sink, ...]
    initial_total_bq_m2: float
    final_total_bq_m2: float
    closure_residual_bq_m2: float
    source_table_sha256: str

    def provenance(self) -> dict[str, object]:
        return {
            "authority": "KFK5194_1993_EQ32_TABLES9_12_CONDITIONAL",
            "source_table_sha256": self.source_table_sha256,
            "hypothesis": KFK5194R6Hypothesis.ISOLATED_TRIANGULAR_NO_SINK_FEEDBACK.value,
            "crop_scope": "GRASS_AND_LEAFY_ONLY_PARENT_EQUALS_FORMATION_TARGET",
            "p2_r4_diurnal_reference": "12H_DAY_12H_NIGHT",
            "p2_r5_outflows": "COMA_DAILY_TABLE_EDGES_AS_AUDIT_SINKS",
            "feedback_from_sinks": False,
            "physical_receiving_states": False,
            "eq33_advanced_night": "NOT_EXECUTED",
            "1990_default_modified": False,
            "production_runtime_activated": False,
            "original_executable_equivalence": "NOT_ESTABLISHED",
            "independent_science_review": "NOT_RUN",
        }


def _retained_formation(
    h: float, a: float, b: float, dt: float
) -> float:
    """Exact convolution integral a*H0*int(exp(-a*s-b*(dt-s))) ds.

    Evaluate using the smaller of a,b as the outer exponential, and
    -expm1(-abs(a-b)*dt)/abs(a-b), avoiding near-equal cancellation
    and exp(positive large) overflow. a,b are nonnegative h^-1.
    """
    delta = abs(a - b)
    if delta == 0.0:
        return h * a * dt * math.exp(-a * dt)
    return (
        h * a * math.exp(-min(a, b) * dt)
        * (-math.expm1(-delta * dt) / delta)
    )


def audit_kfk5194_1993_r6_triangular_budget(
    *,
    profile: Historical1993SourceProfile,
    crop_organ: KFK5194CropOrgan,
    pinned_table_source: Path,
    segments: tuple[KFK5194R4DayPart, ...],
    externally_supplied_fig11_factor: float,
    initial_hto_bq_m2_ground: float,
    initial_parent_obt_bq_m2_ground: float,
    hypothesis: KFK5194R6Hypothesis,
) -> KFK5194R6Budget:
    """Exact piecewise-constant two-pool + sink ledger, research-only.

    dH/dt=-a*H, dB/dt=a*H-b*B, dS_i/dt=(k_i/24)*B,
    with a from the R4 Eq.(32) day/night conditional diagnostic and
    b=sum_i(k_i)/24 from R3/R5 source-pinned parent OBT edges.
    """
    if hypothesis is not KFK5194R6Hypothesis.ISOLATED_TRIANGULAR_NO_SINK_FEEDBACK:
        raise KFK5194PhotoOBTError("explicit R6 research hypothesis required")
    if crop_organ not in (
        KFK5194CropOrgan.GRASS_WHOLE,
        KFK5194CropOrgan.LEAFY_VEGETABLE_WHOLE,
    ) or not isinstance(crop_organ, KFK5194CropOrgan):
        raise KFK5194PhotoOBTError(
            "R6 requires same HTO->parent OBT compartment; "
            "potato/wheat edible OBT is distinct from parent OBT"
        )
    # R4 validates the exact source hash, 1993 profile, 24h/12+12h
    # partition, Figure 11 factor, input types and Eq.(32) rates.
    r4 = audit_kfk5194_1993_r4_eq32_diurnal_budget(
        profile=profile, crop_organ=crop_organ,
        pinned_table_source=pinned_table_source,
        segments=segments,
        externally_supplied_fig11_factor=externally_supplied_fig11_factor,
        initial_hto_bq_m2_ground=initial_hto_bq_m2_ground,
        initial_obt_bq_m2_ground=initial_parent_obt_bq_m2_ground,
        hypothesis=KFK5194R4Hypothesis.ISOLATED_ONE_WAY_FIXED_AREAL_POOLS,
    )
    src = r4.source
    if src.formation_to_as_printed != src.parent_obt_compartment:
        raise KFK5194PhotoOBTError("formation target/parent OBT mismatch")
    edges = src.parent_obt_outflows
    total_rate = src.parent_obt_total_outflow_d_1
    if not edges or total_rate <= 0 or not math.isfinite(total_rate):
        raise KFK5194PhotoOBTError("positive source-checked parent outflows required")
    if not math.isclose(
        math.fsum(edge.rate_d_1 for edge in edges),
        total_rate, rel_tol=1e-14, abs_tol=0.0,
    ):
        raise KFK5194PhotoOBTError("parent outgoing source mismatch")
    h = float(initial_hto_bq_m2_ground)
    b_pool = float(initial_parent_obt_bq_m2_ground)
    origin = math.fsum((h, b_pool))
    if not math.isfinite(origin):
        raise KFK5194PhotoOBTError("nonfinite initial activity total")
    b_rate = total_rate / 24.0
    sink_totals = [0.0] * len(edges)
    steps: list[KFK5194R6Step] = []
    for r4_step in r4.segments:
        a = r4_step.effective_rate_per_h
        dt = r4_step.duration_hours
        formed = h * (-math.expm1(-a * dt))
        h_new = h - formed
        b_survival = b_pool * math.exp(-b_rate * dt)
        retained_formed = _retained_formation(h, a, b_rate, dt)
        b_new = math.fsum((b_survival, retained_formed))
        # All H loss is either in B or in the audit sinks. The
        # old B loss also goes to sinks. Never return sink-labelled HTO.
        sink_total = math.fsum((
            b_pool * (-math.expm1(-b_rate * dt)),
            formed, -retained_formed,
        ))
        scale = max(1.0, origin, h, b_pool, h_new, b_new)
        if (not all(math.isfinite(x) for x in (
                formed, h_new, b_new, retained_formed, sink_total))
                or h_new < 0 or b_new < 0
                or sink_total < -5e-13 * scale):
            raise KFK5194PhotoOBTError("R6 invalid triangular activity state")
        # Below machine resolution, a tiny negative sink is roundoff,
        # not a physical negative transfer; preserve closure tolerance.
        sink_total = max(0.0, sink_total)
        sinks = tuple(
            KFK5194R6Sink(
                symbol_as_printed=edge.symbol_as_printed,
                destination_as_printed=edge.to_as_printed,
                rate_d_1=edge.rate_d_1,
                activity_bq_m2=sink_total * edge.rate_d_1 / total_rate,
            )
            for edge in edges
        )
        residual = math.fsum((
            h_new, b_new, *(s.activity_bq_m2 for s in sinks),
            -h, -b_pool,
        ))
        if abs(residual) > 5e-13 * scale:
            raise KFK5194PhotoOBTError("R6 segment activity closure failed")
        for i, s in enumerate(sinks):
            sink_totals[i] = math.fsum((sink_totals[i], s.activity_bq_m2))
        steps.append(KFK5194R6Step(
            period=r4_step.period, duration_hours=dt,
            formation_rate_h_1=a, total_parent_outflow_rate_h_1=b_rate,
            initial_hto_bq_m2=h, final_hto_bq_m2=h_new,
            initial_parent_obt_bq_m2=b_pool, final_parent_obt_bq_m2=b_new,
            formation_bq_m2=formed, sink_transfers=sinks,
            closure_residual_bq_m2=residual,
        ))
        h, b_pool = h_new, b_new
    sinks_final = tuple(
        KFK5194R6Sink(
            symbol_as_printed=edge.symbol_as_printed,
            destination_as_printed=edge.to_as_printed,
            rate_d_1=edge.rate_d_1,
            activity_bq_m2=sink_totals[i],
        )
        for i, edge in enumerate(edges)
    )
    final = math.fsum((h, b_pool, *(s.activity_bq_m2 for s in sinks_final)))
    residual = math.fsum((
        h, b_pool, *(s.activity_bq_m2 for s in sinks_final), -origin,
    ))
    if not math.isfinite(final) or abs(residual) > 5e-13 * max(1., origin):
        raise KFK5194PhotoOBTError("R6 full-day activity closure failed")
    return KFK5194R6Budget(
        crop_organ=crop_organ, steps=tuple(steps),
        final_hto_bq_m2=h, final_parent_obt_bq_m2=b_pool,
        sink_totals=sinks_final, initial_total_bq_m2=origin,
        final_total_bq_m2=final, closure_residual_bq_m2=residual,
        source_table_sha256=src.provenance()["source_table_sha256"],
    )
