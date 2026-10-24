"""P2 R8: independent, conditional algebraic diagnostics for KfK5194 Eq.(28)/(30).

Neither closure is a historical UFOTRI implementation. In particular the
Eq.(28) respiration area basis and the Eq.(30) CO2-equivalent biomass bridge
are not independently qualified. No production code imports these tests.
"""

import math
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_photo_r2_audit import (
    audit_kfk5194_1993_eq28_canopy,
    audit_kfk5194_1993_eq30_respiration,
)

ROOT = Path(__file__).resolve().parents[2]


def _profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _gross_terms(lai: float, incident_par: float):
    result = audit_kfk5194_1993_eq28_canopy(
        profile=_profile(), incident_par_w_m2_ground=incident_par,
        lai_m2_leaf_per_m2_ground=lai,
        maximum_co2_g_m2_leaf_h=5.0,
        initial_light_efficiency_g_co2_per_w_h=0.012,
        respiration_g_co2_m2_leaf_h=0.0,
    )
    assert result.provenance()["disposition"] == (
        "FORMULAE_NOT_EQUIVALENT_DO_NOT_AUTO_SELECT"
    )
    return (
        result.printed_eq28_pc_g_co2_m2_ground_h,
        result.integrated_eq26_27_pc_g_co2_m2_ground_h,
    )


def _independent_bisection(gross: float, scale: float, biomass: float):
    """Solve P = gross - scale*(0.36*P + 0.000167*W) without closed form."""
    def residual(p):
        return p - gross + scale*(0.36*p + 1.67e-4*biomass)

    left, right = -1e6, 1e6
    assert residual(left) < 0 < residual(right)
    for _ in range(100):
        mid = (left + right)/2
        if residual(mid) > 0:
            right = mid
        else:
            left = mid
    return (left + right)/2


@pytest.mark.parametrize("lai,par,biomass", [
    (0.5, 500.0, 100.0),
    (1.0, 500.0, 1200.0),
    (3.0, 500.0, 1200.0),
    (4.0, 150.0, 100.0),
])
def test_r8_two_hypothetical_implicit_closures_have_distinct_fixed_points(lai, par, biomass):
    printed_gross, integrated_gross = _gross_terms(lai, par)
    for gross, scale in ((printed_gross, 1.0), (integrated_gross, lai)):
        # Conditional on equating the Eq.(28) and Eq.(30) Rd area bases,
        # which is NOT established by the historical source.
        closed = (gross - scale*1.67e-4*biomass)/(1.0 + scale*0.36)
        independent = _independent_bisection(gross, scale, biomass)
        assert closed == pytest.approx(independent, abs=1e-9)
        if closed >= 0:
            rd = audit_kfk5194_1993_eq30_respiration(
                profile=_profile(), canopy_pc_g_co2_m2_ground_h=closed,
                accumulated_biomass_g_co2_equiv_m2_ground=biomass,
            ).total_respiration_g_co2_m2_ground_h
            assert closed == pytest.approx(gross-scale*rd, abs=1e-11)
    printed = (printed_gross-1.67e-4*biomass)/1.36
    integrated = (integrated_gross-lai*1.67e-4*biomass)/(1+lai*0.36)
    assert not math.isclose(printed, integrated, rel_tol=1e-5, abs_tol=1e-5)


def test_r8_zero_lai_exposes_nonzero_literal_canopy_even_after_implicit_closure():
    printed_gross, integrated_gross = _gross_terms(0.0, 500.0)
    assert printed_gross > 0.0
    assert integrated_gross == pytest.approx(0.0, abs=1e-12)
    assert printed_gross/1.36 > 0.0  # W=0, literal printed branch
    assert integrated_gross == pytest.approx(0.0, abs=1e-12)


def test_r8_zero_light_can_produce_negative_net_pc_and_must_not_be_clamped():
    printed_gross, integrated_gross = _gross_terms(3.0, 0.0)
    assert printed_gross == integrated_gross == 0.0
    biomass = 1200.0
    printed_pc = -1.67e-4*biomass/1.36
    integrated_pc = -3.0*1.67e-4*biomass/(1+3.0*0.36)
    assert printed_pc < 0.0 and integrated_pc < 0.0
    assert printed_pc != pytest.approx(integrated_pc)
    # Existing Eq.(30) API rejects negative Pc; no invented nighttime
    # positive assimilation or implicit clamp is permitted.
    from cteas_ufotri.plant.kfk5194_1993_photo_r2_audit import KFK5194PhotoOBTError
    with pytest.raises(KFK5194PhotoOBTError):
        audit_kfk5194_1993_eq30_respiration(
            profile=_profile(), canopy_pc_g_co2_m2_ground_h=printed_pc,
            accumulated_biomass_g_co2_equiv_m2_ground=biomass,
        )


def test_r8_eq29_unqualified_pm_and_1990_default_are_not_wired():
    for relative_path in (
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/plant/obt_ufotri_v4/model.py",
        "src/cteas_ufotri/plant/kfk5194_1993_p2_r6_triangular_budget.py",
    ):
        content = (ROOT/relative_path).read_text(encoding="utf-8")
        assert "kfk5194_1993_photo_r2_audit" not in content
    assert _profile().profile_id == "KFK5194_1993_V4"
