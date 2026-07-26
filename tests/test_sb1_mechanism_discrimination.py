from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
MECHANISM_ROOT = (
    ROOT / "validation" / "benchmarks" / "emras_soybean_sb1_mechanisms"
)
REPORTS = MECHANISM_ROOT / "reports"
SB1_REPORTS = (
    ROOT / "validation" / "benchmarks" / "emras_soybean_sb1" / "reports"
)
sys.path.insert(0, str(MECHANISM_ROOT))

from models import (  # noqa: E402
    current_single_pool,
    dynamic_water_storage,
    obt_recycle,
    parallel_fast_slow,
    reversible_fast_slow,
)


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def protocol() -> dict:
    return load_yaml(
        MECHANISM_ROOT
        / "preregistration"
        / "sb1_mechanism_discrimination_protocol.yaml"
    )


def selection() -> dict:
    return load_json(REPORTS / "mechanism_selection.json")


def test_h0_reproduces_merged_sb1_baseline() -> None:
    mechanism_calibration = pd.read_csv(
        REPORTS / "mechanism_calibration_predictions.csv"
    )
    mechanism_calibration = mechanism_calibration[
        mechanism_calibration["mechanism_id"] == "H0_CURRENT_SINGLE_POOL"
    ].reset_index(drop=True)
    baseline_calibration = pd.read_csv(
        SB1_REPORTS / "calibration_predictions_frozen.csv"
    )
    baseline_calibration = baseline_calibration[
        baseline_calibration["run_id"] == "RUN_01"
    ].reset_index(drop=True)
    np.testing.assert_allclose(
        mechanism_calibration["predicted_bq_l_water"],
        baseline_calibration["predicted_bq_l_water"],
        rtol=0.0,
        atol=0.0,
    )

    mechanism_late = pd.read_csv(REPORTS / "mechanism_late_predictions.csv")
    mechanism_late = mechanism_late[
        mechanism_late["mechanism_id"] == "H0_CURRENT_SINGLE_POOL"
    ].reset_index(drop=True)
    baseline_late = pd.read_csv(
        SB1_REPORTS / "pseudo_holdout_predictions.csv"
    ).reset_index(drop=True)
    np.testing.assert_allclose(
        mechanism_late["predicted_bq_l_water"],
        baseline_late["predicted_bq_l_water"],
        rtol=0.0,
        atol=0.0,
    )


def test_h1_inventory_unchanged_by_storage_mapping() -> None:
    inventory = 42.5
    assert current_single_pool.observed_inventory_bq_m2(inventory) == inventory
    first = dynamic_water_storage.concentration_bq_l(
        inventory, 0.0, 100.0
    )
    second = dynamic_water_storage.concentration_bq_l(
        inventory, 100.0, 100.0
    )
    assert first != second
    assert inventory == 42.5


def test_h2_fast_slow_transfer_conserves_activity() -> None:
    result = parallel_fast_slow.transfer(
        fast_inventory_bq_m2=100.0,
        slow_inventory_bq_m2=20.0,
        positive_leaf_uptake_bq_m2_s=0.2,
        slow_capture_fraction=0.1,
        slow_release_rate_s=1.0e-5,
        decay_constant_s=0.0,
        dt_s=600.0,
    )
    assert abs(result.internal_transfer_residual_bq_m2) <= 1.0e-12
    assert result.fast_inventory_bq_m2 + result.slow_inventory_bq_m2 == 120.0


def test_h3_reversible_transfer_conserves_activity() -> None:
    result = reversible_fast_slow.transfer(
        fast_inventory_bq_m2=100.0,
        slow_inventory_bq_m2=20.0,
        fast_to_slow_rate_s=1.0e-5,
        slow_to_fast_rate_s=2.0e-5,
        decay_constant_s=0.0,
        dt_s=600.0,
    )
    assert abs(result.internal_transfer_residual_bq_m2) <= 1.0e-12
    assert result.fast_inventory_bq_m2 + result.slow_inventory_bq_m2 == 120.0


def test_h4_reuses_existing_obt_flux_contract() -> None:
    original = {
        "plant": {
            "obt_formation_rate_s": 2.0,
            "obt_turnover_rate_s": 3.0,
            "unrelated": 4.0,
        },
        "physics": {"unchanged": True},
    }
    candidate = obt_recycle.apply_multipliers(original, 0.5, 4.0)
    assert candidate["plant"]["obt_formation_rate_s"] == 1.0
    assert candidate["plant"]["obt_turnover_rate_s"] == 12.0
    assert candidate["plant"]["unrelated"] == 4.0
    assert candidate["physics"] == original["physics"]
    assert original["plant"]["obt_formation_rate_s"] == 2.0
    assert obt_recycle.NEW_FITTED_PARAMETER_COUNT == 2


def test_no_candidate_uses_late_observations_for_fit() -> None:
    frozen_protocol = protocol()
    frozen = load_yaml(REPORTS / "frozen_mechanism_parameters.yaml")
    result = selection()
    assert frozen_protocol["parameter_search"][
        "late_observations_available_to_search"
    ] is False
    assert frozen["late_check_executed"] is False
    assert result["late_data_used_for_fit"] is False
    assert result["late_check_hours"] == [936, 1608, 2280]


def test_candidate_parameter_count_limit() -> None:
    frozen_protocol = protocol()
    limit = frozen_protocol["parameter_search"][
        "maximum_new_parameters_per_candidate"
    ]
    counts = [
        candidate["new_fitted_parameter_count"]
        for candidate in frozen_protocol["candidates"].values()
    ]
    assert counts == [0, 0, 2, 2, 2]
    assert max(counts) <= limit == 2


def test_candidate_parameters_frozen_before_late_check() -> None:
    frozen_path = REPORTS / "frozen_mechanism_parameters.yaml"
    late_path = REPORTS / "mechanism_selection.json"
    frozen_commit = subprocess.run(
        [
            "git",
            "log",
            "-1",
            "--format=%H",
            "--",
            str(frozen_path.relative_to(ROOT)),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    late_commit = subprocess.run(
        [
            "git",
            "log",
            "-1",
            "--format=%H",
            "--",
            str(late_path.relative_to(ROOT)),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert frozen_commit
    assert late_commit
    assert frozen_commit != late_commit
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", frozen_commit, late_commit],
        cwd=ROOT,
        check=True,
    )


def test_all_mechanisms_finite_nonnegative() -> None:
    mass = pd.read_csv(REPORTS / "mechanism_mass_balance.csv")
    assert mass["mechanism_id"].nunique() == 5
    assert len(mass) == 35
    assert not mass.select_dtypes(include=[np.number]).isna().any().any()
    assert (mass["inf_count"] == 0).all()
    assert (mass["negative_inventory_count"] == 0).all()
    assert (mass["negative_concentration_count"] == 0).all()


def test_all_mechanisms_reproducible() -> None:
    predictions = pd.read_csv(REPORTS / "mechanism_late_predictions.csv")
    frozen = load_yaml(REPORTS / "frozen_mechanism_parameters.yaml")
    assert predictions["mechanism_id"].nunique() == 5
    assert predictions["run_id"].nunique() == 7
    assert predictions["mechanism_parameter_result_hash"].nunique() == 1
    assert (
        predictions["mechanism_parameter_result_hash"].iloc[0]
        == frozen["mechanism_parameter_result_hash"]
    )
    first = reversible_fast_slow.transfer(
        10.0, 5.0, 1.0e-7, 1.0e-6, 1.0e-9, 600.0
    )
    second = reversible_fast_slow.transfer(
        10.0, 5.0, 1.0e-7, 1.0e-6, 1.0e-9, 600.0
    )
    assert first == second


def test_mechanism_selection_uses_frozen_thresholds() -> None:
    result = selection()["candidate_results"]
    for mechanism_id in (
        "H1_DYNAMIC_WATER_STORAGE",
        "H2_PARALLEL_FAST_SLOW_RESIDUAL",
        "H3_REVERSIBLE_FAST_SLOW_EXCHANGE",
        "H4_OBT_MEDIATED_RECYCLE",
    ):
        candidate = result[mechanism_id]
        assert candidate["supported"] == all(candidate["checks"].values())
    assert result["H2_PARALLEL_FAST_SLOW_RESIDUAL"]["checks"][
        "late_rmse"
    ]
    assert result["H2_PARALLEL_FAST_SLOW_RESIDUAL"]["checks"][
        "late_median_ratio"
    ]
    assert not result["H2_PARALLEL_FAST_SLOW_RESIDUAL"]["checks"][
        "no_parameter_boundary_hit"
    ]


def test_pods_not_used_for_model_selection() -> None:
    frozen_protocol = protocol()
    assert (
        frozen_protocol["observations"]["pods_status"]
        == "STRUCTURAL_DIAGNOSTIC_ONLY_NOT_USED_FOR_SELECTION"
    )
    late_metrics = pd.read_csv(REPORTS / "mechanism_late_metrics.csv")
    assert set(late_metrics["partition"]) == {
        "calibration",
        "pseudo_holdout_a",
        "pseudo_holdout_b",
    }
    structural = pd.read_csv(
        REPORTS / "mechanism_structural_diagnostics.csv"
    )
    assert (structural["pods_status"] == "NOT_USED_FOR_SELECTION").all()


def test_mechanism_branch_not_production_gate_eligible() -> None:
    frozen_protocol = protocol()
    result = selection()
    assert frozen_protocol["production_gate_eligible"] is False
    assert frozen_protocol["formal_model_change"] is False
    assert result["production_gate_eligible"] is False
    assert result["empirical_validation_claim"] is False
    assert result["v3_physics_implementation_status"] == "NOT_STARTED"
    assert (
        result["v3_physics_start_gate"]
        == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )


def test_all_mechanism_mass_balance_checks_pass() -> None:
    frozen_protocol = protocol()
    mass = pd.read_csv(REPORTS / "mechanism_mass_balance.csv")
    assert mass["mass_balance_pass"].all()
    assert (
        mass["maximum_formal_mass_closure_abs_bq_m2"].max()
        <= frozen_protocol["success_criteria"][
            "mass_closure_absolute_tolerance_bq_m2"
        ]
    )
    assert (
        mass["maximum_internal_transfer_residual_abs_bq_m2"].max()
        <= frozen_protocol["success_criteria"][
            "internal_transfer_absolute_tolerance_bq_m2"
        ]
    )


def test_h3_fails_only_frozen_forcing_robustness_requirement() -> None:
    candidate = selection()["candidate_results"][
        "H3_REVERSIBLE_FAST_SLOW_EXCHANGE"
    ]
    assert candidate["forcing_pass_count"] == 4
    assert not candidate["checks"]["forcing_robustness"]
    other_checks = {
        name: passed
        for name, passed in candidate["checks"].items()
        if name != "forcing_robustness"
    }
    assert all(other_checks.values())
    assert candidate["supported"] is False


def test_observation_partition_is_frozen_and_disjoint() -> None:
    frozen_protocol = protocol()
    calibration = set(frozen_protocol["observations"]["calibration_hours"])
    late = set(frozen_protocol["observations"]["late_check_hours"])
    assert calibration == {0.2, 1, 24, 120, 336}
    assert late == {936, 1608, 2280}
    assert calibration.isdisjoint(late)


def test_descriptive_fit_is_not_a_selection_input() -> None:
    frozen_protocol = protocol()
    result = load_json(REPORTS / "descriptive_timescale_results.json")
    assert frozen_protocol["descriptive_timescale_analysis"][
        "descriptive_only"
    ]
    assert result["descriptive_only"]
    assert result["used_for_candidate_calibration"] is False
    assert result["used_for_model_selection"] is False
    assert result["double_exponential"]["log_sse"] < result[
        "single_exponential"
    ]["log_sse"]
