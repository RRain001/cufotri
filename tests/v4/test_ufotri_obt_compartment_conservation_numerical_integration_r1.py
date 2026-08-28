"""UFOTRI B2 OBT compartment numerical qualification tests."""

from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys

from cteas_ufotri.plant.obt_ufotri_v4 import (
    NO_SEPARATE_EXCHANGEABLE_POOL,
    current_short_term_inventory_baseline,
    ufotri_long_term_ingestion_obt_profile,
    ufotri_obt_rate_reconciliation,
    ufotri_obt_role_map,
)
from cteas_ufotri.plant.obt_v3 import ufotri_obt_baseline_parameters
from cteas_ufotri.v4_integration import SELECTED_OPERATOR_SPLIT


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/run_ufotri_obt_compartment_conservation_numerical_integration_r1.py"
PASS_STATUS = "PASS_OBT_COMPARTMENT_CONSERVATION_NUMERICAL_INTEGRATION"
SHORT_ID = "SECTION_2_2_6_DAILY_AVERAGE_CONTROLLED_BASELINE"
EQ_ID = "EQ65_66_DERIVED_HOURLY_COMPARISON"


def _run_machine_result() -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    line = next(
        item
        for item in completed.stdout.splitlines()
        if item.startswith("UFOTRI_OBT_B2_RESULT_JSON=")
    )
    return json.loads(line.split("=", 1)[1])


def test_b1_state_role_boundary_is_preserved_in_b2() -> None:
    role_map = ufotri_obt_role_map()
    assert NO_SEPARATE_EXCHANGEABLE_POOL is True
    assert role_map.exchangeable_obt_representation == "TFWTState"
    assert role_map.nonexchangeable_obt_representation == "OBTState"
    assert role_map.separate_exchangeable_obt_pool is False
    assert role_map.exchangeable_obt_extra_inventory_added is False
    assert SELECTED_OPERATOR_SPLIT == "PRESERVE_V3_POST_OBT_ROOT_GAIN"


def test_section_2_2_6_profile_remains_exactly_the_frozen_controlled_baseline() -> None:
    assert current_short_term_inventory_baseline() == ufotri_obt_baseline_parameters()


def test_eq65_66_hourly_profile_is_derived_without_selecting_it_as_default() -> None:
    long_term = ufotri_long_term_ingestion_obt_profile()
    rates = ufotri_obt_rate_reconciliation()

    expected_kf_h = (
        (math.log(2.0) / 10.0) * 0.1 * 9.0 / (0.4 * 13.0) / 24.0
    )
    expected_kr_h = (math.log(2.0) / 10.0) / 24.0
    assert math.isclose(
        long_term.hto_to_obt_h_1_exact_from_stated_masses,
        expected_kf_h,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )
    assert math.isclose(
        long_term.obt_to_hto_h_1,
        expected_kr_h,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )
    assert rates.numerically_identical is False
    assert current_short_term_inventory_baseline() == ufotri_obt_baseline_parameters()


def test_independent_constant_tfwt_analytic_values_for_both_profiles() -> None:
    duration_s = 24.0 * 3600.0
    tfwt_inventory = 2.0

    profiles = {
        SHORT_ID: (
            0.0006 / 3600.0,
            0.003 / 3600.0,
            0.027787641675517703,
            0.0288,
        ),
        EQ_ID: (
            ((math.log(2.0) / 10.0) * 0.1 * 9.0 / (0.4 * 13.0)) / 24.0 / 3600.0,
            ((math.log(2.0) / 10.0) / 24.0) / 3600.0,
            0.023180887544951283,
            0.023993556250151954,
        ),
    }

    for _, (kf_s, kr_s, expected_obt, expected_formation) in profiles.items():
        source = kf_s * tfwt_inventory
        equilibrium = source / kr_s
        manual = equilibrium * (1.0 - math.exp(-kr_s * duration_s))
        formation = source * duration_s
        assert math.isclose(manual, expected_obt, rel_tol=0.0, abs_tol=1.0e-15)
        assert math.isclose(
            formation,
            expected_formation,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        )


def test_machine_runner_closes_all_b2_gates() -> None:
    result = _run_machine_result()

    assert result["stage"] == "UFOTRI_OBT_COMPARTMENT_CONSERVATION_NUMERICAL_INTEGRATION_R1"
    assert result["status"] == PASS_STATUS
    assert all(result["gates"].values())

    chain = result["chain_qualification"]
    assert set(chain) == {SHORT_ID, EQ_ID}
    for profile_id in (SHORT_ID, EQ_ID):
        assert all(chain[profile_id]["gates"].values())
        assert result["analytic_probes"][profile_id]["pass"] is True
        assert result["zero_tfwt_decay_probes"][profile_id]["pass"] is True

    assert result["legacy_reduced_rc1_identity"]["pass"] is True
    assert result["manual_rate_reconciliation"]["numerically_identical"] is False
    assert result["profile_state_delta_at_1800s"]["obt_bq_m2"] != 0.0


def test_machine_runner_preserves_all_claim_boundaries() -> None:
    result = _run_machine_result()
    boundaries = result["hard_boundaries"]

    assert boundaries == {
        "calibration": False,
        "empirical_validation": False,
        "frozen_v3_rc1_default_changed": False,
        "generic_multi_pool_obt": False,
        "normalized_day_night_multiplier_recovered": False,
        "original_executable_parameter_selection_recovered": False,
        "physical_accuracy_claim": False,
        "production_parameter_activation": False,
        "real_cteas_atmos_binding": False,
    }
