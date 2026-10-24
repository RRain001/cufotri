"""Independent RK4 ODE oracle for the *conditional* P2 R6 audit.

This checks a numerical consequence of the documented synthetic
H -> parent OBT -> audit-sink hypothesis. It does not validate the
historical UFOTRI 4.0 executable, plant physiology or field evidence.
Rates are separately transcribed from KfK 5194 (1993) Tables 9-12.
"""
import math
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_photo_obt_rates import (
    KFK5194CropOrgan as Crop, KFK5194SolarPeriod as Solar,
)
from cteas_ufotri.plant.kfk5194_1993_p2_r4_diurnal_budget import KFK5194R4DayPart
from cteas_ufotri.plant.kfk5194_1993_p2_r6_triangular_budget import (
    KFK5194R6Hypothesis, audit_kfk5194_1993_r6_triangular_budget,
)

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "docs/v4/1993_upgrade/primary_source_transfer_tables_r3.yaml"

# Independent documentary constants (d^-1), not obtained from the R6 result.
CROPS = {
    Crop.GRASS_WHOLE: (0.0081, (0.024, 0.018, 0.0029, 0.0015)),
    Crop.LEAFY_VEGETABLE_WHOLE: (0.0025, (0.032,)),
}


def _rhs(y: tuple[float, ...], a: float, edges_h: tuple[float, ...]):
    h, b = y[:2]
    return (-a * h, a * h - math.fsum(edges_h) * b,
            *(rate * b for rate in edges_h))


def _rk4(y: tuple[float, ...], a: float, edges_h: tuple[float, ...],
         dt: float) -> tuple[float, ...]:
    k1 = _rhs(y, a, edges_h)
    k2 = _rhs(tuple(x + dt * k / 2 for x, k in zip(y, k1)), a, edges_h)
    k3 = _rhs(tuple(x + dt * k / 2 for x, k in zip(y, k2)), a, edges_h)
    k4 = _rhs(tuple(x + dt * k for x, k in zip(y, k3)), a, edges_h)
    return tuple(x + dt * (u + 2*v + 2*w + z) / 6
                 for x, u, v, w, z in zip(y, k1, k2, k3, k4))


def _independent_ode(formation_d: float, edges_d: tuple[float, ...],
                     factors: tuple[float, float], fig11: float,
                     h0: float, b0: float):
    """Solve all sink ODEs explicitly, without a matrix exponential.

    RK4 time increment 0.025 h; day and night each 480 steps.
    The 1/24 conversion is applied independently to all daily rates.
    """
    y = (h0, b0, *(0.0 for _ in edges_d))
    snapshots = []
    edges_h = tuple(k / 24 for k in edges_d)
    for day_factor in factors:
        a = formation_d * fig11 * day_factor / 24
        for _ in range(480):
            y = _rk4(y, a, edges_h, 0.025)
        snapshots.append(y)
    return snapshots


@pytest.mark.parametrize("crop", list(CROPS))
@pytest.mark.parametrize("order", [(Solar.DAY, Solar.NIGHT),
                                   (Solar.NIGHT, Solar.DAY)])
@pytest.mark.parametrize("fig11", [0.0, 0.7, 2.0])
@pytest.mark.parametrize("initial", [(1000.0, 200.0), (1000.0, 0.0)])
def test_r6_against_independent_multisink_rk4(crop, order, fig11, initial):
    formation_d, edges_d = CROPS[crop]
    profile = load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )
    result = audit_kfk5194_1993_r6_triangular_budget(
        profile=profile, crop_organ=crop, pinned_table_source=TABLES,
        segments=tuple(KFK5194R4DayPart(period, 12.0) for period in order),
        externally_supplied_fig11_factor=fig11,
        initial_hto_bq_m2_ground=initial[0],
        initial_parent_obt_bq_m2_ground=initial[1],
        hypothesis=KFK5194R6Hypothesis.ISOLATED_TRIANGULAR_NO_SINK_FEEDBACK,
    )
    factors = tuple(1.75 if p is Solar.DAY else 0.25 for p in order)
    snapshots = _independent_ode(
        formation_d, edges_d, factors, fig11, *initial,
    )
    assert len(result.steps) == len(snapshots) == 2
    previous_sinks = (0.0,) * len(edges_d)
    for step, state in zip(result.steps, snapshots):
        assert len(step.sink_transfers) == len(edges_d)
        assert step.final_hto_bq_m2 == pytest.approx(state[0], rel=2e-10, abs=2e-9)
        assert step.final_parent_obt_bq_m2 == pytest.approx(
            state[1], rel=2e-10, abs=2e-9
        )
        transfers = tuple(s.activity_bq_m2 for s in step.sink_transfers)
        assert transfers == pytest.approx(
            tuple(total - previous for total, previous
                  in zip(state[2:], previous_sinks)),
            rel=2e-9, abs=2e-9,
        )
        previous_sinks = state[2:]
        assert abs(step.closure_residual_bq_m2) < 1e-9

    last = snapshots[-1]
    assert tuple(s.activity_bq_m2 for s in result.sink_totals) == pytest.approx(
        last[2:], rel=2e-9, abs=2e-9
    )
    assert result.final_total_bq_m2 == pytest.approx(
        math.fsum(initial), rel=1e-12, abs=1e-9
    )
    assert math.fsum(last) == pytest.approx(
        math.fsum(initial), rel=2e-10, abs=2e-9
    )
    assert result.provenance()["original_executable_equivalence"] == "NOT_ESTABLISHED"
