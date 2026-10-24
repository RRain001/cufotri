"""P2 R5 independent analytical oracles for conditional COMA outflow audit."""
from dataclasses import replace
import math
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_photo_obt_rates import (
    KFK5194CropOrgan as Crop, KFK5194PhotoOBTError,
)
from cteas_ufotri.plant.kfk5194_1993_p2_r5_parent_outflow_budget import (
    KFK5194R5Hypothesis as Hypothesis,
    audit_kfk5194_1993_r5_parent_obt_outflow_budget,
)

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "docs/v4/1993_upgrade/primary_source_transfer_tables_r3.yaml"
P = Hypothesis.ISOLATED_PARENT_COMPETING_HAZARDS_NO_FEEDBACK
EDIBLE = (Crop.POTATO_TUBER, Crop.WHEAT_SEEDLINGS_PRINTED)


def _profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _audit(crop=Crop.GRASS_WHOLE, **overrides):
    params = dict(
        profile=_profile(), crop_organ=crop, pinned_table_source=CORPUS,
        duration_hours_segments=(12.0, 12.0),
        initial_parent_obt_bq_m2_ground=1000.0,
        initial_edible_obt_bq_m2_ground=25.0 if crop in EDIBLE else None,
        hypothesis=P,
    )
    return audit_kfk5194_1993_r5_parent_obt_outflow_budget(
        **(params | overrides)
    )


@pytest.mark.parametrize("crop,total_rate,branches", [
    (Crop.GRASS_WHOLE, .0464, {
        "grass HTO": .024, "cow HTO": .018,
        "cow OBT": .0029, "milk OBT": .0015,
    }),
    (Crop.LEAFY_VEGETABLE_WHOLE, .032, {"plant HTO": .032}),
    (Crop.POTATO_TUBER, .069, {"potato HTO": .069}),
    (Crop.WHEAT_SEEDLINGS_PRINTED, .069, {"wheat HTO": .069}),
])
def test_r5_independent_exact_competing_hazard_branch_oracles(
    crop, total_rate, branches
):
    r = _audit(crop)
    expected_out = 1000.0 * (-math.expm1(-total_rate))
    assert r.elapsed_hours == 24.0
    assert r.final_parent_obt_bq_m2 == pytest.approx(
        1000.0 * math.exp(-total_rate), rel=1e-13
    )
    actual = {x.destination_as_printed: x.transferred_bq_m2
              for x in r.sink_totals}
    assert set(actual) == set(branches)
    for destination, rate in branches.items():
        assert actual[destination] == pytest.approx(
            expected_out * rate / total_rate, rel=2e-13, abs=1e-12
        )
    assert math.fsum(actual.values()) == pytest.approx(expected_out)
    assert r.initial_total_bq_m2 == 1000.0 + (25.0 if crop in EDIBLE else 0.0)
    assert r.final_total_bq_m2 == pytest.approx(r.initial_total_bq_m2)
    assert abs(r.full_budget_residual_bq_m2) < 1e-9
    assert all(abs(s.closure_residual_bq_m2) < 1e-9 for s in r.steps)
    assert r.provenance()["production_runtime_activated"] is False
    assert r.provenance()["original_fortran_parity"] == "NOT_ESTABLISHED"
    assert r.provenance()["sinks_are_physical_cow_milk_plant_states"] is False


@pytest.mark.parametrize("crop", list(Crop))
@pytest.mark.parametrize("elapsed", [24.0, 168.0])
def test_r5_timestep_refinement_and_analytic_survival(crop, elapsed):
    baseline = _audit(crop, duration_hours_segments=(elapsed,))
    for step in (0.5, 1.0, 6.0, 12.0):
        n = int(elapsed / step)
        result = _audit(crop, duration_hours_segments=(step,) * n)
        assert result.final_parent_obt_bq_m2 == pytest.approx(
            baseline.final_parent_obt_bq_m2, rel=5e-13, abs=1e-9
        )
        assert [x.transferred_bq_m2 for x in result.sink_totals] == pytest.approx(
            [x.transferred_bq_m2 for x in baseline.sink_totals],
            rel=5e-13, abs=1e-9,
        )
        assert abs(result.full_budget_residual_bq_m2) < 1e-9
    rate = {Crop.GRASS_WHOLE:.0464, Crop.LEAFY_VEGETABLE_WHOLE:.032,
            Crop.POTATO_TUBER:.069, Crop.WHEAT_SEEDLINGS_PRINTED:.069}[crop]
    assert baseline.final_parent_obt_bq_m2 == pytest.approx(
        1000 * math.exp(-rate * elapsed / 24.0)
    )


@pytest.mark.parametrize("crop", list(Crop))
def test_r5_zero_parent_no_outflow_and_edible_pool_separation(crop):
    result = _audit(crop, initial_parent_obt_bq_m2_ground=0.0)
    assert result.final_parent_obt_bq_m2 == 0.0
    assert all(x.transferred_bq_m2 == 0.0 for x in result.sink_totals)
    if crop in EDIBLE:
        assert result.initial_edible_obt_bq_m2 == 25.0
        assert result.final_edible_obt_bq_m2 == 25.0
        assert result.initial_total_bq_m2 == result.final_total_bq_m2 == 25.0
        assert result.source.parent_obt_compartment != result.source.formation_to_as_printed
    else:
        assert result.initial_edible_obt_bq_m2 is None
        assert result.final_edible_obt_bq_m2 is None
        assert result.source.parent_obt_compartment == result.source.formation_to_as_printed


def test_r5_grass_all_four_sinks_and_no_hidden_return_to_hto():
    result = _audit()
    assert len(result.sink_totals) == 4
    assert sum(x.transferred_bq_m2 for x in result.sink_totals) > 0
    assert result.provenance()["outgoing_feedback_to_hto"] == "NOT_IMPLEMENTED"
    assert result.final_parent_obt_bq_m2 < 1000
    # The grass HTO-labelled receiving bucket is *not* reused as an
    # HTO source pool or an additional Eq32 formation transfer.
    assert result.provenance()["operator"] == (
        "CONDITIONAL_ISOLATED_PARENT_COMPETING_HAZARDS"
    )


@pytest.mark.parametrize("crop", EDIBLE)
def test_r5_edible_parent_separation_is_required(crop):
    with pytest.raises(KFK5194PhotoOBTError, match="separate edible"):
        _audit(crop, initial_edible_obt_bq_m2_ground=None)
    r = _audit(crop, initial_parent_obt_bq_m2_ground=100.0,
               initial_edible_obt_bq_m2_ground=10000.0)
    assert r.final_edible_obt_bq_m2 == 10000.0
    assert r.final_parent_obt_bq_m2 < 100.0
    assert r.source.edible_obt_loss_per_day_as_printed == 0.0


@pytest.mark.parametrize("bad", [
    (), [], (0.0,), (-1.0,), (float("nan"),),
    (float("inf"),), (True,), ("12",), (12.0, -2.0),
])
def test_r5_bad_duration_partitions_fail_closed(bad):
    with pytest.raises(KFK5194PhotoOBTError):
        _audit(duration_hours_segments=bad)


@pytest.mark.parametrize("key,bad", [
    ("initial_parent_obt_bq_m2_ground", -1.0),
    ("initial_parent_obt_bq_m2_ground", float("inf")),
    ("initial_parent_obt_bq_m2_ground", float("nan")),
    ("initial_parent_obt_bq_m2_ground", True),
    ("hypothesis", None),
    ("hypothesis", "ISOLATED_PARENT_COMPETING_HAZARDS_NO_FEEDBACK"),
    ("crop_organ", "GRASS_WHOLE"),
    ("initial_edible_obt_bq_m2_ground", 5.0),
])
def test_r5_bad_inputs_fail_closed(key, bad):
    with pytest.raises(KFK5194PhotoOBTError):
        _audit(**{key:bad})


@pytest.mark.parametrize("bad", [-1., float("nan"), float("inf"), True])
def test_r5_invalid_edible_inventory_rejected(bad):
    with pytest.raises(KFK5194PhotoOBTError):
        _audit(Crop.POTATO_TUBER, initial_edible_obt_bq_m2_ground=bad)


def test_r5_1990_profile_and_tampered_source_rejected(tmp_path):
    with pytest.raises(KFK5194PhotoOBTError):
        _audit(profile=replace(_profile(), profile_id="KFK4605_1990"))
    bad = tmp_path / CORPUS.name
    bad.write_bytes(CORPUS.read_bytes().replace(
        b"rate_per_day: 0.024", b"rate_per_day: 0.025"
    ))
    with pytest.raises(KFK5194PhotoOBTError, match="pinned"):
        _audit(pinned_table_source=bad)


def test_r5_no_default_or_production_solver_activation():
    for relpath in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/obt_ufotri_v4/model.py",
        "src/cteas_ufotri/plant/obt_v3/obt_solver.py",
        "src/cteas_ufotri/v4_integration/soil_root_tfwt_obt.py",
    ):
        assert "kfk5194_1993_p2_r5_parent_outflow_budget" not in (
            ROOT / relpath
        ).read_text(encoding="utf-8")
