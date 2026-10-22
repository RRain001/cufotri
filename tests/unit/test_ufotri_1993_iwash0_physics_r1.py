"""Independent IWASH=0 physics checks for KfK5194 P1 opt-in profile."""
from dataclasses import replace
import math
from pathlib import Path

import pytest

from cteas_ufotri.atmosphere.kfk5194_1993_washout import (
    KFK5194DurationTreatment as T,
    kfk5194_iwash0_profiled_source_budget,
)
from cteas_ufotri.atmosphere.ufotri_native_process_v4 import (
    KFK5194HTOWashoutMode, kfk5194_species_policy,
    source_depletion_kfk4332,
)
from cteas_ufotri.atmosphere.ufotri_native_v4 import (
    TritiumAtmosphericForm as Form,
    UFOTRINativeAtmosphereError,
)
from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, load_1993_source_profile,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILE = ROOT / "configs" / "ufotri_1993_manual_source_profile.yaml"


def _args(**extra):
    profile = load_1993_source_profile(SOURCE_FILE, selected_profile=PROFILE_ID)
    data = dict(
        profile=profile,
        species=Form.HTO,
        precipitation_mm_h=2.0,
        source_bq_s=1.0e8,
        downwind_m=3000.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=15.0,
        stability_class="D",
        mixing_lid_m=560.0,
        duration_treatment=T.MEAN_FRACTION_OF_TRAVEL,
    )
    data.update(extra)
    return data


@pytest.mark.parametrize("rain,klass,coeff,frac", [
    (0.0, None, 0.0, 0.5),
    (0.1, 1, 6.0e-5, 0.5),
    (0.99999999, 1, 6.0e-5, 0.5),
    (1.0, 2, 1.0e-4, 0.75),
    (2.99999999, 2, 1.0e-4, 0.75),
    (3.0, 3, 4.0e-4, 0.72),
    (8.0, 3, 4.0e-4, 0.72),
])
def test_source_1993_rain_class_limits_and_regtim(
    rain: float, klass: int | None, coeff: float, frac: float
) -> None:
    result = kfk5194_iwash0_profiled_source_budget(
        **_args(precipitation_mm_h=rain)
    )
    assert result.rain_class == klass
    assert result.documented_coefficient_s_1 == coeff
    assert result.documented_relative_rain_duration == frac
    assert result.effective_wet_removal_rate_s_1 == pytest.approx(
        coeff * (frac if rain > 0 else 0.0)
    )
    assert result.depletion.wet_loss_bq_s >= 0.0
    assert result.residual_bq_s == pytest.approx(0.0, abs=1.0e-8)


@pytest.mark.parametrize("treatment", list(T))
def test_wet_factor_matches_exponential_and_activity_closes(treatment: T) -> None:
    wet = kfk5194_iwash0_profiled_source_budget(
        **_args(duration_treatment=treatment)
    )
    dry = kfk5194_iwash0_profiled_source_budget(
        **_args(precipitation_mm_h=0.0, duration_treatment=treatment)
    )
    exponent = -wet.effective_wet_removal_rate_s_1 * wet.depletion.travel_time_s
    assert wet.depletion.source_after_bq_s / dry.depletion.source_after_bq_s == (
        pytest.approx(math.exp(exponent), rel=1e-12)
    )
    assert wet.depletion.source_before_bq_s == pytest.approx(
        wet.depletion.source_after_bq_s
        + wet.depletion.dry_loss_bq_s
        + wet.depletion.wet_loss_bq_s,
        abs=1e-7,
    )
    assert wet.residual_bq_s == pytest.approx(0.0, abs=1e-8)
    assert all(math.isfinite(q) and q >= 0.0 for q in (
        wet.depletion.source_after_bq_s,
        wet.depletion.dry_loss_bq_s,
        wet.depletion.wet_loss_bq_s,
    ))


def test_duration_assumption_brackets_wet_loss_without_claiming_fortran_parity() -> None:
    fraction = kfk5194_iwash0_profiled_source_budget(**_args())
    upper = kfk5194_iwash0_profiled_source_budget(
        **_args(duration_treatment=T.FULL_RAIN_TRAVEL_UPPER_BOUND)
    )
    assert upper.depletion.wet_loss_bq_s > fraction.depletion.wet_loss_bq_s > 0.0
    assert upper.depletion.source_after_bq_s < fraction.depletion.source_after_bq_s
    assert upper.documented_coefficient_s_1 == fraction.documented_coefficient_s_1
    assert fraction.applied_travel_rain_fraction == 0.75
    assert upper.applied_travel_rain_fraction == 1.0
    assert fraction.provenance()["original_regtim_application"] == (
        "SOURCE_LIMITED_NOT_ESTABLISHED"
    )
    assert fraction.provenance()["original_executable_numeric_equivalence"] == (
        "NOT_ESTABLISHED"
    )


@pytest.mark.parametrize("rain", [0.0, 0.5, 1.0, 3.0, 100.0])
def test_ht_has_no_wet_loss_under_1993_default(rain: float) -> None:
    result = kfk5194_iwash0_profiled_source_budget(
        **_args(species=Form.HT, precipitation_mm_h=rain)
    )
    assert result.documented_coefficient_s_1 == 0.0
    assert result.applied_travel_rain_fraction == 0.0
    assert result.depletion.wet_loss_bq_s == 0.0


@pytest.mark.parametrize("overrides", [
    {"source_bq_s": -1.0},
    {"source_bq_s": float("nan")},
    {"precipitation_mm_h": -0.1},
    {"precipitation_mm_h": float("inf")},
    {"wind_speed_m_s": 0.0},
    {"downwind_m": -1.0},
    {"species": "HTO"},
    {"duration_treatment": "MEAN_FRACTION_OF_TRAVEL"},
    {"profile": None},
])
def test_invalid_inputs_fail_closed(overrides: dict) -> None:
    with pytest.raises(UFOTRINativeAtmosphereError):
        kfk5194_iwash0_profiled_source_budget(**_args(**overrides))


def test_1993_profile_mismatch_fails_closed() -> None:
    profile = _args()["profile"]
    for changed in (
        replace(profile, profile_id="KFK4605_1990"),
        replace(profile, washout_mode=1),
        replace(profile, washout_class_boundaries_mm_h=(100.0, 300.0)),
        replace(profile, washout_hto_rates_per_s=(6e-5, 9e-5, 4e-4)),
        replace(profile, washout_hto_duration_fraction=(0.5, 1.0, 0.72)),
    ):
        with pytest.raises(UFOTRINativeAtmosphereError, match="1993 source profile"):
            kfk5194_iwash0_profiled_source_budget(**_args(profile=changed))


def test_existing_h4_policy_and_legacy_cli_not_modified() -> None:
    existing = kfk5194_species_policy(
        species=Form.HTO, dry_deposition_velocity_m_s=0.005,
        precipitation_mm_h=2.0,
        mode=KFK5194HTOWashoutMode.PRECALCULATED_CLASSES,
    )
    assert existing.wet_scavenging_rate_s_1 == 1e-4
    legacy = source_depletion_kfk4332(
        source_bq_s=1e8, downwind_m=3000, wind_speed_m_s=5,
        effective_release_height_m=15, stability_class="D",
        mixing_lid_m=560, policy=existing,
    )
    assert legacy.source_after_bq_s > 0.0
    for file in ("src/cteas_ufotri/config.py", "src/cteas_ufotri/cli.py"):
        assert "kfk5194_1993_washout" not in (ROOT / file).read_text(encoding="utf-8")


def test_zero_distance_budget_conserves_activity() -> None:
    result = kfk5194_iwash0_profiled_source_budget(**_args(downwind_m=0.0))
    assert result.depletion.source_after_bq_s == result.depletion.source_before_bq_s
    assert result.depletion.dry_loss_bq_s == 0.0
    assert result.depletion.wet_loss_bq_s == 0.0
