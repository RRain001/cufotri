from __future__ import annotations

import math

import pytest

from cteas_ufotri.atmosphere.depletion import segment_exponential_depletion
from cteas_ufotri.atmosphere.wet_deposition import (
    scavenging_coefficient_s,
    wet_deposition_ledger,
)


def test_no_rain_or_off_mode_gives_zero_scavenging():
    assert (
        scavenging_coefficient_s(
            0.0,
            "constant_scavenging_coefficient",
            constant_coefficient_s=2.0e-5,
        )
        == 0.0
    )
    assert (
        scavenging_coefficient_s(
            1.0e-6,
            "off",
            constant_coefficient_s=2.0e-5,
        )
        == 0.0
    )


def test_power_law_is_monotone_with_rain():
    low = scavenging_coefficient_s(
        1.0e-7, "precipitation_power_law", power_law_a_s=1.0e-5, power_law_b=0.8
    )
    high = scavenging_coefficient_s(
        1.0e-5, "precipitation_power_law", power_law_a_s=1.0e-5, power_law_b=0.8
    )
    assert 0.0 < low < high


def test_combined_dry_wet_depletion_is_partitioned_once_and_grid_stable():
    kwargs = dict(
        source_bq_s=1.0e9,
        downwind_m=1000.0,
        effective_wind_m_s=3.0,
        deposition_velocity_m_s=0.005,
        mixing_height_m=1000.0,
        dry_enabled=True,
        wet_enabled=True,
        wet_scavenging_rate_s=2.0e-5,
    )
    coarse = segment_exponential_depletion(**kwargs, segments=1)
    fine = segment_exponential_depletion(**kwargs, segments=100)
    for budget in (coarse, fine):
        assert budget.source_before_bq_s == pytest.approx(
            budget.source_after_bq_s
            + budget.dry_depletion_bq_s
            + budget.wet_depletion_bq_s
        )
        assert min(
            budget.source_after_bq_s,
            budget.dry_depletion_bq_s,
            budget.wet_depletion_bq_s,
        ) >= 0.0
        assert all(
            math.isfinite(value)
            for value in (
                budget.source_after_bq_s,
                budget.dry_depletion_bq_s,
                budget.wet_depletion_bq_s,
            )
        )
    assert fine.source_after_bq_s == pytest.approx(
        coarse.source_after_bq_s, rel=1.0e-12
    )
    assert fine.wet_depletion_bq_s == pytest.approx(
        coarse.wet_depletion_bq_s, rel=1.0e-12
    )


def test_wet_surface_ledger_matches_source_loss():
    ledger = wet_deposition_ledger(2500.0, 2.0e-5, 500.0)
    assert ledger.surface_flux_bq_m2_s == pytest.approx(5.0)
    assert (
        ledger.surface_flux_bq_m2_s * ledger.footprint_area_m2
        == pytest.approx(ledger.depleted_source_bq_s)
    )

