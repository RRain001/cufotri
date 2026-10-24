"""R13: independent Eq.(28) math discriminants, NOT original executable physics."""

import math
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/v4/1993_upgrade"


def gross(pm, eps, incident, k, lai):
    bottom_abs = k * incident * math.exp(-k * lai)
    top = pm + eps * k * incident
    printed = pm / k * math.log(top / (pm + eps * k * bottom_abs))
    integrated = pm / k * math.log(top / (pm + eps * bottom_abs))
    return printed, integrated, bottom_abs


def difference_independent(pm, eps, bottom_abs, k):
    x = eps * bottom_abs
    return pm / k * math.log((pm + x) / (pm + k * x))


def quadrature(pm, eps, incident, k, lai, n=15000):
    if lai == 0:
        return 0.0
    dl = lai / n
    return math.fsum(
        pm * (eps * k * incident * math.exp(-k * (j + 0.5) * dl)) /
        (pm + eps * k * incident * math.exp(-k * (j + 0.5) * dl)) * dl
        for j in range(n)
    )


@pytest.mark.parametrize("lai,incident", [
    (0.0, 500.0), (0.2, 35.0), (0.7, 400.0), (1.0, 220.0), (3.0, 1200.0),
])
def test_independent_leaf_midpoint_quadrature_and_exact_bias(lai, incident):
    pm, eps, k = 5.0, 0.012, 0.6
    printed, integral, bottom = gross(pm, eps, incident, k, lai)
    numeric = quadrature(pm, eps, incident, k, lai)
    assert integral == pytest.approx(numeric, rel=1e-8, abs=1e-10)
    assert printed - integral == pytest.approx(
        difference_independent(pm, eps, bottom, k), rel=2e-13, abs=1e-13)
    assert printed > integral if lai > 0 else printed > 0 and integral == 0
    assert 0 < printed - integral < pm / k * math.log(1.0 / k)


def test_zero_lai_and_k_equal_one_are_discriminating_limits():
    pm, eps, incident = 5.0, 0.012, 300.0
    printed, integrated, _ = gross(pm, eps, incident, 0.6, 0.0)
    assert printed > 0
    assert integrated == 0.0
    for lai in (0.0, 0.3, 1.0, 3.0):
        p, i, _ = gross(pm, eps, incident, 1.0, lai)
        assert p == pytest.approx(i, abs=1e-13)


@pytest.mark.parametrize("lai", [0.0, 0.4, 1.0, 3.0])
def test_low_light_slopes_track_extra_k_factor(lai):
    pm, eps, k, incident = 5.0, 0.012, 0.6, 1e-5
    printed, integrated, _ = gross(pm, eps, incident, k, lai)
    expected_integrated = eps * (1 - math.exp(-k * lai))
    expected_printed = eps * (1 - k * math.exp(-k * lai))
    assert integrated / incident == pytest.approx(expected_integrated, rel=1e-5, abs=1e-9)
    assert printed / incident == pytest.approx(expected_printed, rel=1e-5, abs=1e-9)
    assert (printed-integrated)/incident == pytest.approx(
        eps*(1-k)*math.exp(-k*lai), rel=1e-5, abs=1e-9)


def test_high_light_bound_and_canopy_monotonicity():
    pm, eps, k = 5.0, 0.012, 0.6
    limit = pm/k * math.log(1/k)
    for lai in (0.0, 0.8, 3.0):
        p, i, _ = gross(pm, eps, 1e11, k, lai)
        assert p-i == pytest.approx(limit, rel=4e-7)
        assert i == pytest.approx(pm*lai, rel=3e-7, abs=1e-8)
    diffs = []
    for lai in (0.0, 0.5, 1.0, 2.0, 4.0):
        p, i, _ = gross(pm, eps, 500.0, k, lai)
        diffs.append(p-i)
    assert diffs == sorted(diffs, reverse=True)


def test_net_sign_can_reverse_below_one_lai_without_selecting_a_physics_branch():
    pm, eps, k, lai, incident = 5.0, 0.012, 0.6, 0.4, 500.0
    printed, integrated, _ = gross(pm, eps, incident, k, lai)
    d = printed-integrated
    threshold = d/(1-lai)
    for rd, expected_positive in ((0.0, True), (0.5*threshold, True), (1.5*threshold, False)):
        diff = (printed-rd) - (integrated-lai*rd)
        assert diff == pytest.approx(d+(lai-1)*rd, abs=1e-12)
        assert (diff > 0) is expected_positive
    for lai in (1.0, 3.0):
        p, i, _ = gross(pm, eps, incident, k, lai)
        for rd in (0.0, 0.2, 3.0):
            assert (p-rd)-(i-lai*rd)>0


def test_bias_derivative_and_strict_bounds():
    pm, eps, k = 5.0, 0.012, 0.6
    x, h = 2.0, 1e-4
    f = lambda q: pm/k * math.log((pm+q)/(pm+k*q))
    centered = (f(x+h)-f(x-h))/(2*h)
    analytic = pm/k * pm*(1-k)/((pm+x)*(pm+k*x))
    assert centered == pytest.approx(analytic, rel=1e-8)
    assert 0 < f(x) < pm/k * math.log(1/k)


def test_source_gates_and_1990_baseline_remain_fail_closed():
    registry = yaml.safe_load((DOC/"physics_delta_matrix.yaml").read_text(encoding="utf-8"))
    row = next(row for row in registry["rows"] if row["id"] == "UF93-13")
    r = row["p2_r13_eq28_bias_sign_limit_audit"]
    assert registry["baseline_version"] == "KFK4605_1990"
    assert registry["runtime_1993_profile_activated"] is False
    assert r["source_pdf_sha256"] == row["p2_r9_source_gate"]["source_pdf_sha256"]
    assert r["source_printed_pages"] == [19, 20]
    assert r["source_pdf_page_indices_zero_based"] == [28, 29]
    assert r["evidence_level"] == "PRINTED_FORMULA_AND_INDEPENDENT_MATH_ONLY"
    assert r["sign_light_difference_if_0_lt_k_lt_1"] == "STRICTLY_POSITIVE_FOR_POSITIVE_PAR"
    assert r["conditional_net_sign_for_lai_lt_1"] == "UNDETERMINED_CAN_REVERSE"
    assert r["eq28_printed_vs_eq26_27_integral"] == "INCONSISTENT_TWO_TERMS"
    for key in ("respiration_area_basis", "eq29_mass_unit_bridge", "eq30_biomass_area_bridge"):
        assert r[key] == "NOT_ESTABLISHED"
    assert r["original_executable_parity"] == "NOT_RUN"
    assert r["independent_scientific_review"] == "NOT_RUN"
    assert r["production_coupling_allowed"] is False
    assert row["p2_r9_source_gate"]["production_coupling_allowed"] is False
    packet = ROOT/r["audit_packet"]
    assert packet.is_file()
    text = packet.read_text(encoding="utf-8")
    assert "PRODUCTION_COUPLING_BLOCKED" in text and "NOT_ESTABLISHED" in text
    assert packet.name in (DOC/"PHYSICS_DELTA_MATRIX.md").read_text(encoding="utf-8")
