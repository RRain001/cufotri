"""R4 numerical and negative controls on the source-limited Eq.(32) day."""
from dataclasses import replace
import math
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, load_1993_source_profile,
)
from cteas_ufotri.plant.kfk5194_1993_photo_obt_rates import (
    KFK5194CropOrgan as Crop, KFK5194SolarPeriod as Period,
    KFK5194PhotoOBTError,
)
from cteas_ufotri.plant.kfk5194_1993_p2_r4_diurnal_budget import (
    KFK5194R4Hypothesis as Hypothesis,
    KFK5194R4DayPart as Part,
    audit_kfk5194_1993_r4_eq32_diurnal_budget,
)

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "docs/v4/1993_upgrade/primary_source_transfer_tables_r3.yaml"
P = Hypothesis.ISOLATED_ONE_WAY_FIXED_AREAL_POOLS


def _profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _audit(**kwargs):
    args = dict(
        profile=_profile(), crop_organ=Crop.GRASS_WHOLE,
        pinned_table_source=CORPUS,
        segments=(Part(Period.DAY, 12.), Part(Period.NIGHT, 12.)),
        externally_supplied_fig11_factor=1.,
        initial_hto_bq_m2_ground=1000.,
        initial_obt_bq_m2_ground=40.,
        hypothesis=P,
    )
    return audit_kfk5194_1993_r4_eq32_diurnal_budget(**(args | kwargs))


@pytest.mark.parametrize("crop,mean_rate", [
    (Crop.GRASS_WHOLE, .0081),
    (Crop.LEAFY_VEGETABLE_WHOLE, .0025),
    (Crop.POTATO_TUBER, .0026),
    (Crop.WHEAT_SEEDLINGS_PRINTED, .0041),
])
def test_r4_all_four_crops_independent_exact_12_12_day_oracle(crop, mean_rate):
    r = _audit(crop_organ=crop)
    assert r.daytime_hours == 12.
    assert r.nighttime_hours == 12.
    assert r.historical_12_12_reference_matched
    assert r.weighted_daily_factor == pytest.approx(
        (1.75*12 + .25*12)/24
    )
    assert r.mean_coefficient_integral == pytest.approx(mean_rate)
    assert r.segments[0].effective_rate_per_h == pytest.approx(mean_rate/24*1.75)
    assert r.segments[1].effective_rate_per_h == pytest.approx(mean_rate/24*.25)
    assert r.final_hto_bq_m2 == pytest.approx(1000*math.exp(-mean_rate), rel=2e-13)
    assert r.final_obt_bq_m2 == pytest.approx(
        40 + 1000*(-math.expm1(-mean_rate)), rel=2e-13
    )
    assert r.cumulative_transfer_bq_m2 == pytest.approx(
        1000*(-math.expm1(-mean_rate)), rel=2e-13
    )
    assert r.initial_total_bq_m2 == 1040.
    assert math.fsum((r.final_hto_bq_m2,r.final_obt_bq_m2)) == pytest.approx(1040.)
    assert abs(r.full_day_activity_closure_residual_bq_m2) < 1e-10
    assert abs(r.segments[0].activity_closure_residual_bq_m2) < 1e-10
    assert abs(r.segments[1].activity_closure_residual_bq_m2) < 1e-10
    assert r.provenance()["advanced_eq33_night_branch"] == "NOT_ESTABLISHED_NOT_EXECUTED"
    assert r.provenance()["production_runtime_activated"] is False


@pytest.mark.parametrize("crop", list(Crop))
def test_r4_refinement_invariance_24_hour_hourly_and_half_hourly(crop):
    reference = _audit(crop_organ=crop)
    for chunk in (.5, 1., 2., 3., 4., 6.):
        parts = tuple(
            [Part(Period.DAY, chunk)]*int(12/chunk)
            + [Part(Period.NIGHT, chunk)]*int(12/chunk)
        )
        out = _audit(crop_organ=crop, segments=parts)
        assert out.final_hto_bq_m2 == pytest.approx(reference.final_hto_bq_m2,
                                                      rel=4e-14, abs=1e-10)
        assert out.final_obt_bq_m2 == pytest.approx(reference.final_obt_bq_m2,
                                                      rel=4e-14, abs=1e-10)
        assert out.mean_coefficient_integral == pytest.approx(
            reference.mean_coefficient_integral, rel=1e-14
        )
        assert len(out.segments) == 24/chunk
        assert abs(out.full_day_activity_closure_residual_bq_m2) < 1e-9


def test_r4_interleaved_day_night_does_not_change_isolated_final_ledger():
    a = _audit()
    b = _audit(segments=tuple(
        [Part(Period.DAY, 3.), Part(Period.NIGHT, 3.)]*4
    ))
    assert b.daytime_hours == 12.
    assert b.nighttime_hours == 12.
    assert b.final_hto_bq_m2 == pytest.approx(a.final_hto_bq_m2)
    assert b.final_obt_bq_m2 == pytest.approx(a.final_obt_bq_m2)
    assert b.cumulative_transfer_bq_m2 == pytest.approx(a.cumulative_transfer_bq_m2)


@pytest.mark.parametrize("factor,initial_hto,initial_obt", [
    (0., 1000., 40.),
    (1., 0., 50.),
    (0., 0., 0.),
    (2., 200., 0.),
])
def test_r4_zero_and_positive_hypothesis_inputs_do_not_create_activity(
    factor,initial_hto,initial_obt
):
    r = _audit(externally_supplied_fig11_factor=factor,
               initial_hto_bq_m2_ground=initial_hto,
               initial_obt_bq_m2_ground=initial_obt)
    assert r.final_hto_bq_m2 >= 0.
    assert r.final_obt_bq_m2 >= 0.
    assert r.cumulative_transfer_bq_m2 >= 0.
    assert r.final_obt_bq_m2 == pytest.approx(
        initial_obt + r.cumulative_transfer_bq_m2
    )
    assert r.final_hto_bq_m2 == pytest.approx(
        initial_hto - r.cumulative_transfer_bq_m2
    )
    if factor == 0 or initial_hto == 0:
        assert r.cumulative_transfer_bq_m2 == 0.


def test_r4_non_12_12_photoperiod_detected_not_silently_normalized():
    bad_day = (Part(Period.DAY, 8.), Part(Period.NIGHT, 16.))
    with pytest.raises(KFK5194PhotoOBTError, match="12/12"):
        _audit(segments=bad_day)
    research = _audit(segments=bad_day, require_historical_12_12_reference=False)
    assert research.daytime_hours == 8.
    assert research.nighttime_hours == 16.
    assert research.weighted_daily_factor == pytest.approx(.75)
    assert research.mean_coefficient_integral == pytest.approx(.0081*.75)
    assert research.final_hto_bq_m2 == pytest.approx(1000*math.exp(-.0081*.75))
    assert research.provenance()["historical_reference_matched"] is False
    # The user-supplied 8/16 diagnostic does not renormalise 1.75/.25 to unity.
    assert research.mean_coefficient_integral != pytest.approx(.0081)


@pytest.mark.parametrize("durations", [
    (Part(Period.DAY, 12.),),
    (Part(Period.DAY, 12.), Part(Period.NIGHT, 13.)),
    (Part(Period.DAY, 24.1),),
    (Part(Period.DAY, 0.), Part(Period.NIGHT, 24.)),
    (Part(Period.DAY, -1.), Part(Period.NIGHT, 25.)),
    (Part(Period.DAY, float("nan")), Part(Period.NIGHT, 12.)),
    (Part(Period.DAY, True), Part(Period.NIGHT, 12.)),
    (Part("DAY", 12.), Part(Period.NIGHT, 12.)),
])
def test_r4_invalid_day_partition_fails_closed(durations):
    with pytest.raises(KFK5194PhotoOBTError):
        _audit(segments=durations)


@pytest.mark.parametrize("key,bad", [
    ("initial_hto_bq_m2_ground", -1.),
    ("initial_hto_bq_m2_ground", float("inf")),
    ("initial_obt_bq_m2_ground", float("nan")),
    ("initial_obt_bq_m2_ground", True),
    ("externally_supplied_fig11_factor", -1.),
    ("externally_supplied_fig11_factor", None),
    ("externally_supplied_fig11_factor", float("nan")),
    ("hypothesis", None),
    ("hypothesis", "ISOLATED_ONE_WAY_FIXED_AREAL_POOLS"),
    ("require_historical_12_12_reference", 1),
    ("crop_organ", "GRASS_WHOLE"),
    ("segments", []),
    ("segments", ()),
])
def test_r4_invalid_isolated_model_input_fails_closed(key,bad):
    with pytest.raises(KFK5194PhotoOBTError):
        _audit(**{key:bad})


def test_r4_1990_wrong_version_is_not_fallback():
    with pytest.raises(KFK5194PhotoOBTError):
        _audit(profile=replace(_profile(), profile_id="KFK4605_1990"))


def test_r4_no_1993_runtime_activation_and_no_advanced_night_selection():
    assert _audit().provenance()["night_branch"] == "SIMPLE_EQ32_EMPIRICAL_0_25_NOT_EQ33"
    for name in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/obt_ufotri_v4/model.py",
        "src/cteas_ufotri/plant/obt_v3/obt_solver.py",
        "src/cteas_ufotri/v4_integration/soil_root_tfwt_obt.py",
    ):
        assert "kfk5194_1993_p2_r4_diurnal_budget" not in (
            ROOT/name
        ).read_text(encoding="utf-8")
