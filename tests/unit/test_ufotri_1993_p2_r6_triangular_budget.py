"""Independent closed-form and invariant tests for conditional P2 R6 audit."""
from dataclasses import replace
import math
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_photo_obt_rates import (
    KFK5194CropOrgan as Crop, KFK5194PhotoOBTError,
    KFK5194SolarPeriod as Period,
)
from cteas_ufotri.plant.kfk5194_1993_p2_r4_diurnal_budget import (
    KFK5194R4DayPart as Part,
)
from cteas_ufotri.plant.kfk5194_1993_p2_r6_triangular_budget import (
    KFK5194R6Hypothesis as Hypothesis,
    audit_kfk5194_1993_r6_triangular_budget as audit,
    _retained_formation,
)

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "docs/v4/1993_upgrade/primary_source_transfer_tables_r3.yaml"
HYPOTHESIS = Hypothesis.ISOLATED_TRIANGULAR_NO_SINK_FEEDBACK
RATES = {
    Crop.GRASS_WHOLE: (.0081, .0464, {
        "grass HTO": .024, "cow HTO": .018,
        "cow OBT": .0029, "milk OBT": .0015,
    }),
    Crop.LEAFY_VEGETABLE_WHOLE: (.0025, .032, {
        "plant HTO": .032,
    }),
}


def _profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _run(crop=Crop.GRASS_WHOLE, **overrides):
    params = dict(
        profile=_profile(), crop_organ=crop, pinned_table_source=TABLES,
        segments=(Part(Period.DAY, 12.), Part(Period.NIGHT, 12.)),
        externally_supplied_fig11_factor=1.0,
        initial_hto_bq_m2_ground=1000.,
        initial_parent_obt_bq_m2_ground=200.,
        hypothesis=HYPOTHESIS,
    )
    return audit(**(params | overrides))


def _reference_step(h, b, sink, a, k, hours):
    """Independent direct matrix-exponential solution (moderate test rates)."""
    h_next = h * math.exp(-a * hours)
    b_next = b * math.exp(-k * hours)
    if a == k:
        b_next += a * h * hours * math.exp(-k * hours)
    else:
        b_next += a * h * (
            math.exp(-a * hours) - math.exp(-k * hours)
        ) / (k - a)
    return h_next, b_next, sink + h + b - h_next - b_next


@pytest.mark.parametrize("crop", list(RATES))
def test_r6_independent_analytic_two_pool_day_night_and_branches(crop):
    formation_daily, outflow_daily, branches = RATES[crop]
    result = _run(crop)
    h, b, sink = 1000., 200., 0.
    for factor in (1.75, 0.25):
        h, b, sink = _reference_step(
            h, b, sink, formation_daily * factor / 24.,
            outflow_daily / 24., 12.,
        )
    assert result.final_hto_bq_m2 == pytest.approx(h, rel=1e-12)
    assert result.final_parent_obt_bq_m2 == pytest.approx(b, rel=1e-12)
    actual = {x.destination_as_printed: x.activity_bq_m2
              for x in result.sink_totals}
    assert set(actual) == set(branches)
    for dest, rate in branches.items():
        assert actual[dest] == pytest.approx(
            sink * rate / outflow_daily, rel=1e-11, abs=1e-10
        )
    assert result.initial_total_bq_m2 == 1200.
    assert result.final_total_bq_m2 == pytest.approx(1200., abs=1e-10)
    assert abs(result.closure_residual_bq_m2) < 1e-10
    assert all(abs(x.closure_residual_bq_m2) < 1e-10
               for x in result.steps)
    p = result.provenance()
    assert p["production_runtime_activated"] is False
    assert p["physical_receiving_states"] is False
    assert p["original_executable_equivalence"] == "NOT_ESTABLISHED"


@pytest.mark.parametrize("crop", list(RATES))
@pytest.mark.parametrize("step_hours", [12., 6., 3., 1., 0.5])
def test_r6_refinement_invariant_without_operator_splitting(crop, step_hours):
    base = _run(crop)
    n = int(12 / step_hours)
    segments = (
        (Part(Period.DAY, step_hours),) * n
        + (Part(Period.NIGHT, step_hours),) * n
    )
    refined = _run(crop, segments=segments)
    assert refined.final_hto_bq_m2 == pytest.approx(
        base.final_hto_bq_m2, rel=2e-12, abs=1e-10
    )
    assert refined.final_parent_obt_bq_m2 == pytest.approx(
        base.final_parent_obt_bq_m2, rel=2e-12, abs=1e-10
    )
    assert [x.activity_bq_m2 for x in refined.sink_totals] == pytest.approx(
        [x.activity_bq_m2 for x in base.sink_totals],
        rel=2e-12, abs=1e-10,
    )
    assert abs(refined.closure_residual_bq_m2) < 1e-10


def test_r6_time_order_affects_obt_and_sinks_but_not_hto():
    day_night = _run()
    night_day = _run(segments=(
        Part(Period.NIGHT, 12.), Part(Period.DAY, 12.),
    ))
    assert day_night.final_hto_bq_m2 == pytest.approx(
        night_day.final_hto_bq_m2, rel=1e-13
    )
    # Formation earlier in the day permits more OBT outgoing loss.
    assert day_night.final_parent_obt_bq_m2 < night_day.final_parent_obt_bq_m2
    assert sum(s.activity_bq_m2 for s in day_night.sink_totals) > sum(
        s.activity_bq_m2 for s in night_day.sink_totals
    )


def test_r6_zero_hto_leaves_exact_parent_survival_and_source_sinks():
    r = _run(initial_hto_bq_m2_ground=0.)
    expected = 200. * math.exp(-.0464)
    assert r.final_hto_bq_m2 == 0.
    assert r.final_parent_obt_bq_m2 == pytest.approx(expected)
    assert sum(s.activity_bq_m2 for s in r.sink_totals) == pytest.approx(
        200. - expected
    )


def test_r6_zero_obt_retains_some_formed_obt_and_positive_outflows():
    r = _run(initial_parent_obt_bq_m2_ground=0.)
    assert 0. < r.final_parent_obt_bq_m2 < 1000.
    assert 0. < sum(s.activity_bq_m2 for s in r.sink_totals) < 1000.
    assert r.final_total_bq_m2 == pytest.approx(1000.)


def test_r6_zero_fig11_disables_formation_but_not_parent_loss():
    r = _run(externally_supplied_fig11_factor=0.)
    assert r.final_hto_bq_m2 == 1000.
    assert r.final_parent_obt_bq_m2 == pytest.approx(200*math.exp(-.0464))
    assert all(s.formation_bq_m2 == 0 for s in r.steps)


def test_r6_zero_pools_have_no_creation():
    r = _run(initial_hto_bq_m2_ground=0.,
             initial_parent_obt_bq_m2_ground=0.)
    assert r.final_hto_bq_m2 == r.final_parent_obt_bq_m2 == 0.
    assert all(x.activity_bq_m2 == 0 for x in r.sink_totals)
    assert r.closure_residual_bq_m2 == 0.

@pytest.mark.parametrize("a,b", [
    (0.02, 0.02), (0.02, 0.02 + 1e-13),
    (0.02 + 1e-13, 0.02),
])
def test_r6_near_degenerate_convolution_stays_finite_and_stable(a, b):
    h, dt = 1000., 12.
    exact_limit = h * 0.02 * dt * math.exp(-0.02 * dt)
    assert _retained_formation(h, a, b, dt) == pytest.approx(
        exact_limit, rel=2e-11
    )


def test_r6_large_hazard_convolution_no_positive_exponent_overflow():
    # Direct positive exponent formulas can overflow; this form cannot.
    result = _retained_formation(1000., 100., 1., 12.)
    expected = 1000. * 100. * math.exp(-12.) / 99.
    assert math.isfinite(result)
    assert result == pytest.approx(expected, rel=1e-13)


@pytest.mark.parametrize("crop", [
    Crop.POTATO_TUBER, Crop.WHEAT_SEEDLINGS_PRINTED,
])
def test_r6_rejects_edible_vs_parent_compartment_conflation(crop):
    with pytest.raises(KFK5194PhotoOBTError, match="edible OBT is distinct"):
        _run(crop)


@pytest.mark.parametrize("bad", [
    (Part(Period.DAY, 24.),),
    (Part(Period.DAY, 8.), Part(Period.NIGHT, 16.)),
    (Part(Period.DAY, 12.), Part(Period.NIGHT, 11.)),
    (Part(Period.DAY, 12.), Part(Period.NIGHT, float("nan"))),
])
def test_r6_bad_or_unqualified_photoperiod_fails_closed(bad):
    with pytest.raises(KFK5194PhotoOBTError):
        _run(segments=bad)


@pytest.mark.parametrize("field,value", [
    ("initial_hto_bq_m2_ground", -1.),
    ("initial_parent_obt_bq_m2_ground", float("nan")),
    ("initial_parent_obt_bq_m2_ground", float("inf")),
    ("initial_hto_bq_m2_ground", True),
    ("externally_supplied_fig11_factor", -1.),
    ("hypothesis", None),
    ("hypothesis", "ISOLATED_TRIANGULAR_NO_SINK_FEEDBACK"),
    ("crop_organ", "GRASS_WHOLE"),
])
def test_r6_bad_inputs_fail_closed(field, value):
    with pytest.raises(KFK5194PhotoOBTError):
        _run(**{field: value})


def test_r6_wrong_edition_and_modified_primary_table_rejected(tmp_path):
    with pytest.raises(KFK5194PhotoOBTError):
        _run(profile=replace(_profile(), profile_id="KFK4605_1990"))
    tampered = tmp_path / TABLES.name
    tampered.write_bytes(TABLES.read_bytes().replace(
        b"rate_per_day: 0.024", b"rate_per_day: 0.025"
    ))
    with pytest.raises(KFK5194PhotoOBTError, match="pinned"):
        _run(pinned_table_source=tampered)


def test_r6_not_imported_by_default_1990_or_production_path():
    for rel in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/obt_ufotri_v4/model.py",
        "src/cteas_ufotri/plant/obt_v3/obt_solver.py",
        "src/cteas_ufotri/v4_integration/soil_root_tfwt_obt.py",
    ):
        assert "kfk5194_1993_p2_r6_triangular_budget" not in (
            ROOT / rel
        ).read_text(encoding="utf-8")
