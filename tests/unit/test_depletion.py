import pytest

from cteas_ufotri.atmosphere.calm_wind import resolve_calm_wind
from cteas_ufotri.atmosphere.depletion import segment_exponential_depletion


def calm(mode="minimum_effective_wind"):
    return {
        "mode": mode,
        "threshold_m_s": 0.5,
        "effective_wind_m_s": 0.5,
        "record_substitution": True,
    }


@pytest.mark.parametrize("wind", [0.0, 1e-12, 0.1])
def test_minimum_effective_wind_is_explicit_and_finite(wind):
    result = resolve_calm_wind(wind, calm())
    assert result.applied
    assert result.effective_wind_speed_m_s == 0.5


def test_calm_threshold_modes():
    assert not resolve_calm_wind(0.5, calm()).applied
    assert not resolve_calm_wind(1.0, calm()).applied
    assert resolve_calm_wind(0.1, calm("skip_gaussian")).skip_gaussian
    with pytest.raises(ValueError, match="Calm wind"):
        resolve_calm_wind(0.1, calm("error"))


def test_dry_depletion_is_monotone_and_segment_stable():
    base = dict(
        source_bq_s=1e9,
        downwind_m=1000.0,
        effective_wind_m_s=1.0,
        mixing_height_m=1000.0,
        segments=10,
    )
    zero = segment_exponential_depletion(**base, deposition_velocity_m_s=0.0)
    low = segment_exponential_depletion(**base, deposition_velocity_m_s=0.001)
    high = segment_exponential_depletion(**base, deposition_velocity_m_s=0.01)
    fine = segment_exponential_depletion(
        **{**base, "segments": 100}, deposition_velocity_m_s=0.01
    )
    assert zero.source_after_bq_s == zero.source_before_bq_s
    assert high.source_after_bq_s < low.source_after_bq_s < zero.source_after_bq_s
    assert high.source_after_bq_s == pytest.approx(fine.source_after_bq_s)
    assert high.source_before_bq_s - high.source_after_bq_s == pytest.approx(
        high.dry_depletion_bq_s
    )
