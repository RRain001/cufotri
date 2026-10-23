"""P3 R2 checks: opt-in 1993 nighttime and daytime rain leaf branches."""
from dataclasses import replace
import math
from pathlib import Path

import pytest

from cteas_ufotri.plant.kfk5194_1993_canopy_et import KFK5194P3InputError
from cteas_ufotri.plant.kfk5194_1993_canopy_regimes import (
    KFK5194LeafRegime as R,
    kfk5194_1993_rain_night_canopy,
)
from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, load_1993_source_profile,
)

ROOT = Path(__file__).resolve().parents[2]


def _args(**changes):
    p = load_1993_source_profile(
        ROOT / "configs" / "ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )
    data = dict(
        profile=p, regime=R.NIGHT_DRY_EPIDERMAL,
        reference_dry_day_stomatal_resistance_s_m=150.0,
        leaf_area_index=3.0, wind_speed_at_reference_m_s=4.0,
        friction_velocity_m_s=0.4, stanton_number=0.2,
        night_epidermal_resistance_s_m=1800.0,
    )
    data.update(changes)
    return data


def test_night_epidermis_correct_leaf_canopy_aerodynamic_resistances():
    s = kfk5194_1993_rain_night_canopy(**_args())
    assert s.leaf_or_epidermal_resistance_s_m == 1800.0
    assert s.aerodynamic_resistance_s_m == pytest.approx(25.0)
    assert s.boundary_layer_resistance_s_m == pytest.approx(12.5)
    assert s.canopy_resistance_s_m == pytest.approx(600.0)
    assert s.leaf_total_resistance_s_m == pytest.approx(1837.5)
    assert s.canopy_total_resistance_s_m == pytest.approx(637.5)
    assert s.exchange_velocity_m_s == pytest.approx(1.0 / 637.5)
    assert s.provenance()["whole_1993_runtime_activated"] is False


@pytest.mark.parametrize("reference,epidermis", [(150, 1500), (150, 1800), (200, 3000)])
def test_night_resistance_minimum_ratio_with_user_values(reference, epidermis):
    s = kfk5194_1993_rain_night_canopy(**_args(
        reference_dry_day_stomatal_resistance_s_m=reference,
        night_epidermal_resistance_s_m=epidermis,
    ))
    assert s.leaf_or_epidermal_resistance_s_m / reference >= 10


def test_night_rain_does_not_lower_epidermal_resistance():
    dry = kfk5194_1993_rain_night_canopy(**_args())
    rain = kfk5194_1993_rain_night_canopy(**_args(
        regime=R.NIGHT_RAIN_EPIDERMAL
    ))
    assert dry.canopy_total_resistance_s_m == rain.canopy_total_resistance_s_m
    assert dry.exchange_velocity_m_s == rain.exchange_velocity_m_s
    assert rain.provenance()["original_executable_equivalence"] == "NOT_ESTABLISHED"


def test_day_rain_wet_finite_and_atmosphere_only_limit_are_explicitly_distinct():
    finite_kwargs = _args(
        regime=R.DAY_RAIN_EXPLICIT_FINITE,
        night_epidermal_resistance_s_m=None,
        wet_day_leaf_resistance_s_m=2.5,
    )
    finite = kfk5194_1993_rain_night_canopy(**finite_kwargs)
    limit = kfk5194_1993_rain_night_canopy(**_args(
        regime=R.DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT,
        night_epidermal_resistance_s_m=None,
    ))
    assert finite.canopy_resistance_s_m == pytest.approx(2.5 / 3.0)
    assert limit.canopy_resistance_s_m == 0.0
    assert limit.exchange_velocity_m_s > finite.exchange_velocity_m_s
    assert "SOURCE_LIMITED" in limit.source_status
    assert "ASYMPTOTIC_APPROXIMATION" in limit.provenance()["rain_zero_limit"]
    assert all(math.isfinite(x) and x >= 0 for x in (
        finite.canopy_total_resistance_s_m, limit.canopy_total_resistance_s_m,
        finite.exchange_velocity_m_s, limit.exchange_velocity_m_s,
    ))


@pytest.mark.parametrize("changes", [
    {"regime": "NIGHT_RAIN_EPIDERMAL"},
    {"profile": None},
    {"leaf_area_index": 0},
    {"wind_speed_at_reference_m_s": -1},
    {"friction_velocity_m_s": 0},
    {"stanton_number": float("nan")},
    {"night_epidermal_resistance_s_m": 1499.0},
    {"reference_dry_day_stomatal_resistance_s_m": 0},
    {"wet_day_leaf_resistance_s_m": 0.5},  # night cannot silently become day wet
])
def test_night_invalid_or_misapplied_inputs_fail_closed(changes):
    with pytest.raises(KFK5194P3InputError):
        kfk5194_1993_rain_night_canopy(**_args(**changes))


@pytest.mark.parametrize("regime,wet_value,night_value", [
    (R.DAY_RAIN_EXPLICIT_FINITE, None, None),
    (R.DAY_RAIN_EXPLICIT_FINITE, 150.0, None),
    (R.DAY_RAIN_EXPLICIT_FINITE, 0.0, None),
    (R.DAY_RAIN_EXPLICIT_FINITE, 3.0, 1800.0),
    (R.DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT, 1.0, None),
    (R.DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT, None, 1800.0),
    (R.NIGHT_RAIN_EPIDERMAL, None, None),
    (R.NIGHT_RAIN_EPIDERMAL, 1.0, 1800.0),
])
def test_regime_requires_matching_explicit_resistance(regime, wet_value, night_value):
    with pytest.raises(KFK5194P3InputError):
        kfk5194_1993_rain_night_canopy(**_args(
            regime=regime,
            wet_day_leaf_resistance_s_m=wet_value,
            night_epidermal_resistance_s_m=night_value,
        ))


def test_profile_identity_is_explicit_not_default_runtime():
    profile = _args()["profile"]
    for changed in (
        replace(profile, profile_id="KFK4605_1990"),
        replace(profile, flag_defaults=tuple(
            (k, 0 if k == "IMODEL" else v)
            for k, v in profile.flag_defaults)),
    ):
        with pytest.raises(KFK5194P3InputError):
            kfk5194_1993_rain_night_canopy(**_args(profile=changed))
    for path in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/leaf_ufotri_v4/model.py",
        "src/cteas_ufotri/plant/kfk5194_1993_canopy_et.py",
    ):
        assert "kfk5194_1993_canopy_regimes" not in (ROOT / path).read_text(encoding="utf-8")
