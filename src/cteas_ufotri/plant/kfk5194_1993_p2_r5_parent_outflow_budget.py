"""P2 R5: source-pinned, isolated competing-outflow OBT activity audit.

KfK 5194 (1993), printed pp.22-23 and COMA Tables 9-12 (pp.86-89).
The table's daily parent-OBT outgoing edges are mapped and hash-checked
by P2 R3. This test-only first-order *research operator* allocates
loss from an isolated parent OBT pool into separate bookkeeping sinks.

A sink label is NOT a cow, milk, plant HTO, harvest or food-chain state.
There is no feedback, OBT formation, dilution, decay, source replenishment,
environmental exchange, or production solver integration. Potato tuber
and wheat seedling edible OBT are distinct, non-losing source compartments
under the explicit printed p.23 rule; they must not be equated with the
parent potato/wheat OBT pool. All supplied inventories share Bq/m2 ground.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from pathlib import Path

from cteas_ufotri.versioned_inputs_1993 import Historical1993SourceProfile
from .kfk5194_1993_photo_obt_rates import KFK5194CropOrgan, KFK5194PhotoOBTError
from .kfk5194_1993_p2_crop_rate_source import (
    KFK5194P2CropSourceRate, audit_kfk5194_1993_p2_crop_source_rate,
)


class KFK5194R5Hypothesis(str, Enum):
    ISOLATED_PARENT_COMPETING_HAZARDS_NO_FEEDBACK = (
        "ISOLATED_PARENT_COMPETING_HAZARDS_NO_FEEDBACK"
    )


@dataclass(frozen=True, slots=True)
class KFK5194R5SinkTransfer:
    symbol_as_printed: str
    destination_as_printed: str
    daily_rate: float
    transferred_bq_m2: float


@dataclass(frozen=True, slots=True)
class KFK5194R5Step:
    duration_hours: float
    start_parent_obt_bq_m2: float
    end_parent_obt_bq_m2: float
    outgoing_bq_m2: float
    sink_transfers: tuple[KFK5194R5SinkTransfer, ...]
    closure_residual_bq_m2: float


@dataclass(frozen=True, slots=True)
class KFK5194R5Budget:
    source: KFK5194P2CropSourceRate
    steps: tuple[KFK5194R5Step, ...]
    elapsed_hours: float
    initial_parent_obt_bq_m2: float
    final_parent_obt_bq_m2: float
    initial_edible_obt_bq_m2: float | None
    final_edible_obt_bq_m2: float | None
    sink_totals: tuple[KFK5194R5SinkTransfer, ...]
    initial_total_bq_m2: float
    final_total_bq_m2: float
    full_budget_residual_bq_m2: float

    def provenance(self) -> dict[str, object]:
        return {
            "authority": "KFK5194_1993_PRINTED_P23_TABLES9_12",
            "source_table_sha256": self.source.provenance()["source_table_sha256"],
            "rate_context": "COMA_LONG_TERM_INGESTION_DAILY_EDGES",
            "operator": "CONDITIONAL_ISOLATED_PARENT_COMPETING_HAZARDS",
            "activity_basis": "Bq_per_m2_ground_for_all_declared_pools",
            "sinks_are_physical_cow_milk_plant_states": False,
            "outgoing_feedback_to_hto": "NOT_IMPLEMENTED",
            "edible_parent_pool_separation": (
                "EXPLICIT_ZERO_EDIBLE_LOSS_PRINTED_P23"
                if self.initial_edible_obt_bq_m2 is not None
                else "PARENT_IS_FORMATION_TARGET"
            ),
            "eq33_advanced_night": "NOT_EXECUTED",
            "coupled_historical_solver": "NOT_ESTABLISHED",
            "original_fortran_parity": "NOT_ESTABLISHED",
            "independent_science_review": "NOT_RUN",
            "production_runtime_activated": False,
        }


def _nonnegative_finite(name: str, value: float, *, positive: bool = False) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise KFK5194PhotoOBTError(f"{name} must be finite numeric")
    v = float(value)
    if v < 0.0 or (positive and v == 0.0):
        raise KFK5194PhotoOBTError(f"{name} must be nonnegative/positive")
    return v


def audit_kfk5194_1993_r5_parent_obt_outflow_budget(
    *,
    profile: Historical1993SourceProfile,
    crop_organ: KFK5194CropOrgan,
    pinned_table_source: Path,
    duration_hours_segments: tuple[float, ...],
    initial_parent_obt_bq_m2_ground: float,
    initial_edible_obt_bq_m2_ground: float | None,
    hypothesis: KFK5194R5Hypothesis,
) -> KFK5194R5Budget:
    """Exact isolated competing-hazard ledger; NOT a 1993 COMA solver.

    For total daily hazard K=sum_i(k_i), each segment of dt hours has
    F=B*(-expm1(-K*dt/24)); B'=B-F; F_i=F*k_i/K. The four grass
    branches remain separate. All F_i are receiving *audit buckets*.
    """
    if hypothesis is not KFK5194R5Hypothesis.ISOLATED_PARENT_COMPETING_HAZARDS_NO_FEEDBACK:
        raise KFK5194PhotoOBTError("explicit R5 research hypothesis required")
    if not isinstance(duration_hours_segments, tuple) or not (
        0 < len(duration_hours_segments) <= 10000
    ):
        raise KFK5194PhotoOBTError("nonempty bounded duration tuple required")
    durations = tuple(
        _nonnegative_finite("duration hours", x, positive=True)
        for x in duration_hours_segments
    )
    elapsed = math.fsum(durations)
    if not math.isfinite(elapsed):
        raise KFK5194PhotoOBTError("nonfinite elapsed duration")
    parent = _nonnegative_finite(
        "initial parent OBT Bq/m2", initial_parent_obt_bq_m2_ground
    )
    src = audit_kfk5194_1993_p2_crop_source_rate(
        profile=profile, crop_organ=crop_organ,
        pinned_table_source=pinned_table_source,
    )
    distinct_edible = crop_organ in (
        KFK5194CropOrgan.POTATO_TUBER, KFK5194CropOrgan.WHEAT_SEEDLINGS_PRINTED
    )
    if distinct_edible:
        if initial_edible_obt_bq_m2_ground is None:
            raise KFK5194PhotoOBTError("explicit separate edible OBT pool required")
        if src.edible_obt_loss_per_day_as_printed != 0.0:
            raise KFK5194PhotoOBTError("printed edible OBT zero-loss contract violated")
        edible = _nonnegative_finite(
            "initial edible OBT Bq/m2", initial_edible_obt_bq_m2_ground
        )
        if src.formation_to_as_printed == src.parent_obt_compartment:
            raise KFK5194PhotoOBTError("edible and parent OBT compartments conflated")
    else:
        if initial_edible_obt_bq_m2_ground is not None:
            raise KFK5194PhotoOBTError("separate edible OBT not applicable to this crop")
        if src.formation_to_as_printed != src.parent_obt_compartment:
            raise KFK5194PhotoOBTError("parent formation target contract violated")
        edible = None
    initial_total = math.fsum((parent, edible or 0.0))
    if not math.isfinite(initial_total):
        raise KFK5194PhotoOBTError("nonfinite initial total activity")
    total_rate = src.parent_obt_total_outflow_d_1
    if not math.isfinite(total_rate) or total_rate <= 0.0:
        raise KFK5194PhotoOBTError("positive parent outflow hazard required")
    rates = src.parent_obt_outflows
    if not rates or not math.isclose(
        math.fsum(x.rate_d_1 for x in rates), total_rate,
        rel_tol=1e-14, abs_tol=0.0,
    ):
        raise KFK5194PhotoOBTError("source parent outflow hazard mismatch")
    totals = [0.0 for _ in rates]
    steps: list[KFK5194R5Step] = []
    for duration in durations:
        exponent = total_rate * (duration / 24.0)
        if not math.isfinite(exponent):
            raise KFK5194PhotoOBTError("nonfinite outgoing hazard exponent")
        outgoing = parent * (-math.expm1(-exponent))
        remaining = parent - outgoing
        transfers = tuple(
            KFK5194R5SinkTransfer(
                symbol_as_printed=edge.symbol_as_printed,
                destination_as_printed=edge.to_as_printed,
                daily_rate=edge.rate_d_1,
                transferred_bq_m2=outgoing * (edge.rate_d_1 / total_rate),
            ) for edge in rates
        )
        residual = math.fsum(
            (remaining, *(x.transferred_bq_m2 for x in transfers), -parent)
        )
        scale = max(1.0, parent, remaining)
        if (not all(math.isfinite(x) for x in (outgoing, remaining, residual))
                or remaining < 0.0 or outgoing < 0.0
                or any(not math.isfinite(x.transferred_bq_m2)
                       or x.transferred_bq_m2 < 0.0 for x in transfers)
                or abs(residual) > 5e-13 * scale):
            raise KFK5194PhotoOBTError("R5 competing-outflow activity violation")
        for i, transfer in enumerate(transfers):
            totals[i] += transfer.transferred_bq_m2
        steps.append(KFK5194R5Step(
            duration_hours=duration, start_parent_obt_bq_m2=parent,
            end_parent_obt_bq_m2=remaining, outgoing_bq_m2=outgoing,
            sink_transfers=transfers, closure_residual_bq_m2=residual,
        ))
        parent = remaining
    sink_totals = tuple(
        KFK5194R5SinkTransfer(
            symbol_as_printed=edge.symbol_as_printed,
            destination_as_printed=edge.to_as_printed,
            daily_rate=edge.rate_d_1,
            transferred_bq_m2=totals[i],
        ) for i, edge in enumerate(rates)
    )
    final_total = math.fsum(
        (parent, edible or 0.0, *(x.transferred_bq_m2 for x in sink_totals))
    )
    residual = math.fsum(
        (parent, edible or 0.0, *(x.transferred_bq_m2 for x in sink_totals),
         -initial_total)
    )
    if (not math.isfinite(final_total) or not math.isfinite(residual)
            or abs(residual) > 5e-13 * max(1.0, initial_total)):
        raise KFK5194PhotoOBTError("R5 full-budget activity violation")
    return KFK5194R5Budget(
        source=src, steps=tuple(steps), elapsed_hours=elapsed,
        initial_parent_obt_bq_m2=initial_parent_obt_bq_m2_ground,
        final_parent_obt_bq_m2=parent,
        initial_edible_obt_bq_m2=edible, final_edible_obt_bq_m2=edible,
        sink_totals=sink_totals, initial_total_bq_m2=initial_total,
        final_total_bq_m2=final_total,
        full_budget_residual_bq_m2=residual,
    )
