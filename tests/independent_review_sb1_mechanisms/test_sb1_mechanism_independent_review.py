from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]
MECHANISM_ROOT = (
    ROOT / "validation" / "benchmarks" / "emras_soybean_sb1_mechanisms"
)
REPORTS = MECHANISM_ROOT / "reports"
SB1_REPORTS = (
    ROOT / "validation" / "benchmarks" / "emras_soybean_sb1" / "reports"
)
PROTOCOL = yaml.safe_load(
    (
        MECHANISM_ROOT
        / "preregistration"
        / "sb1_mechanism_discrimination_protocol.yaml"
    ).read_text(encoding="utf-8")
)
CANDIDATES = (
    "H0_CURRENT_SINGLE_POOL",
    "H1_DYNAMIC_WATER_STORAGE",
    "H2_PARALLEL_FAST_SLOW_RESIDUAL",
    "H3_REVERSIBLE_FAST_SLOW_EXCHANGE",
    "H4_OBT_MEDIATED_RECYCLE",
)
PROTOCOL_COMMIT = "104b1b5264c60b4035f489ad1804f870f94be6c4"
CANDIDATE_COMMIT = "868680f"
PARAMETER_COMMIT = "4b79f62741db4d4b51f4d608df33d2e13c499636"
LATE_COMMIT = "83980e5"
TESTED_EVIDENCE_PARENT = "744db57e87f8f7e3c202cda070c4ce95fd5c109b"
REVIEW_TARGET = "5c1d4bf39415be9b6e7960efeda23af50570f518"


def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def load_selection() -> dict:
    return json.loads(
        (REPORTS / "mechanism_selection.json").read_text(encoding="utf-8")
    )


def independent_log_metrics(frame: pd.DataFrame) -> dict[str, float]:
    observed = frame["observed_bq_l_water"].to_numpy(float)
    predicted = frame["predicted_bq_l_water"].to_numpy(float)
    assert np.all(observed > 0)
    assert np.all(predicted > 0)
    residual = np.log10(predicted) - np.log10(observed)
    ratio = predicted / observed
    absolute = np.abs(residual)
    return {
        "log10_rmse": float(np.sqrt(np.mean(residual**2))),
        "log10_mean_bias": float(np.mean(residual)),
        "median_predicted_to_observed_ratio": float(np.median(ratio)),
        "factor_2_coverage": float(np.mean(absolute <= math.log10(2.0))),
        "factor_10_coverage": float(np.mean(absolute <= 1.0)),
    }


def independently_recomputed_forcing_passes() -> dict[str, list[str]]:
    predictions = pd.read_csv(REPORTS / "mechanism_late_predictions.csv")
    body = predictions[predictions["compartment"] == "plant_body"]
    result: dict[str, list[str]] = {}
    h0 = body[body["mechanism_id"] == "H0_CURRENT_SINGLE_POOL"]
    h0_by_run = {
        run_id: independent_log_metrics(group)
        for run_id, group in h0.groupby("run_id")
    }
    for mechanism_id in CANDIDATES[1:]:
        passed: list[str] = []
        candidate = body[body["mechanism_id"] == mechanism_id]
        for run_id, group in candidate.groupby("run_id"):
            reference = h0_by_run[run_id]
            metrics = independent_log_metrics(group)
            rmse_improvement = (
                reference["log10_rmse"] - metrics["log10_rmse"]
            )
            ratio_improvement = abs(
                math.log10(
                    reference["median_predicted_to_observed_ratio"]
                )
            ) - abs(
                math.log10(metrics["median_predicted_to_observed_ratio"])
            )
            if (
                rmse_improvement
                >= PROTOCOL["success_criteria"][
                    "late_log10_rmse_improvement_minimum_dex"
                ]
                and ratio_improvement
                >= PROTOCOL["success_criteria"][
                    "late_median_ratio_closeness_improvement_minimum_dex"
                ]
            ):
                passed.append(run_id)
        result[mechanism_id] = passed
    return result


def independently_selected_grid_row(mechanism_id: str) -> pd.Series:
    search = pd.read_csv(REPORTS / "mechanism_parameter_search.csv")
    subset = search[search["mechanism_id"] == mechanism_id].copy()
    return subset.sort_values(
        ["log10_rmse", "parameter_1_value", "parameter_2_value"],
        na_position="last",
    ).iloc[0]


def test_review_h0_reproduces_sb1_baseline() -> None:
    calibration = pd.read_csv(
        REPORTS / "mechanism_calibration_predictions.csv"
    )
    h0_calibration = calibration[
        calibration["mechanism_id"] == "H0_CURRENT_SINGLE_POOL"
    ].reset_index(drop=True)
    sb1_calibration = pd.read_csv(
        SB1_REPORTS / "calibration_predictions_frozen.csv"
    )
    sb1_calibration = sb1_calibration[
        sb1_calibration["run_id"] == "RUN_01"
    ].reset_index(drop=True)
    np.testing.assert_array_equal(
        h0_calibration["predicted_bq_l_water"].to_numpy(),
        sb1_calibration["predicted_bq_l_water"].to_numpy(),
    )

    late = pd.read_csv(REPORTS / "mechanism_late_predictions.csv")
    h0_late = late[
        late["mechanism_id"] == "H0_CURRENT_SINGLE_POOL"
    ].reset_index(drop=True)
    sb1_late = pd.read_csv(
        SB1_REPORTS / "pseudo_holdout_predictions.csv"
    ).reset_index(drop=True)
    np.testing.assert_array_equal(
        h0_late["predicted_bq_l_water"].to_numpy(),
        sb1_late["predicted_bq_l_water"].to_numpy(),
    )


def test_review_protocol_precedes_execution() -> None:
    assert git(
        "merge-base", "--is-ancestor", PROTOCOL_COMMIT, CANDIDATE_COMMIT
    ).returncode == 0


def test_review_parameters_precede_late_check() -> None:
    assert git(
        "merge-base", "--is-ancestor", PARAMETER_COMMIT, LATE_COMMIT
    ).returncode == 0
    assert git(
        "merge-base",
        "--is-ancestor",
        LATE_COMMIT,
        TESTED_EVIDENCE_PARENT,
    ).returncode == 0


def test_review_late_data_not_used_for_search() -> None:
    assert (
        PROTOCOL["parameter_search"]["late_observations_available_to_search"]
        is False
    )
    calibration = pd.read_csv(
        REPORTS / "mechanism_calibration_predictions.csv"
    )
    assert set(calibration["hours_after_exposure"]) == {
        0.2,
        1.0,
        24.0,
        120.0,
        336.0,
    }
    assert {936.0, 1608.0, 2280.0}.isdisjoint(
        set(calibration["hours_after_exposure"])
    )


def test_review_h2_grid_optimum_recomputed() -> None:
    best = independently_selected_grid_row(
        "H2_PARALLEL_FAST_SLOW_RESIDUAL"
    )
    assert best["parameter_1_value"] == 0.001
    assert best["parameter_2_value"] == 1.0e-6
    assert math.isclose(best["log10_rmse"], 0.5996877479119134)


def test_review_h3_grid_optimum_recomputed() -> None:
    best = independently_selected_grid_row(
        "H3_REVERSIBLE_FAST_SLOW_EXCHANGE"
    )
    assert best["parameter_1_value"] == 1.0e-7
    assert best["parameter_2_value"] == 1.0e-6
    assert math.isclose(best["log10_rmse"], 0.2758599654751513)


def test_review_h4_grid_optimum_recomputed() -> None:
    best = independently_selected_grid_row("H4_OBT_MEDIATED_RECYCLE")
    assert best["parameter_1_value"] == 2.0
    assert best["parameter_2_value"] == 2.52
    assert math.isclose(best["log10_rmse"], 1.1505051341726669)


def test_review_h2_boundary_hit_detected() -> None:
    search = pd.read_csv(REPORTS / "mechanism_parameter_search.csv")
    subset = search[
        search["mechanism_id"] == "H2_PARALLEL_FAST_SLOW_RESIDUAL"
    ]
    best = independently_selected_grid_row(
        "H2_PARALLEL_FAST_SLOW_RESIDUAL"
    )
    assert best["parameter_1_value"] == subset["parameter_1_value"].min()


def test_review_h3_forcing_pass_count_is_four() -> None:
    passes = independently_recomputed_forcing_passes()
    assert len(passes["H3_REVERSIBLE_FAST_SLOW_EXCHANGE"]) == 4


def test_review_h3_background_scenarios_fail() -> None:
    passes = independently_recomputed_forcing_passes()
    failures = {
        f"RUN_{index:02d}"
        for index in range(1, 8)
    } - set(passes["H3_REVERSIBLE_FAST_SLOW_EXCHANGE"])
    assert failures == {"RUN_05", "RUN_06", "RUN_07"}


def test_review_h2_internal_transfer_conservation() -> None:
    mass = pd.read_csv(REPORTS / "mechanism_mass_balance.csv")
    h2 = mass[
        mass["mechanism_id"] == "H2_PARALLEL_FAST_SLOW_RESIDUAL"
    ]
    assert (
        h2["maximum_internal_transfer_residual_abs_bq_m2"].max()
        <= 1.0e-9
    )


def test_review_h3_internal_transfer_conservation() -> None:
    mass = pd.read_csv(REPORTS / "mechanism_mass_balance.csv")
    h3 = mass[
        mass["mechanism_id"] == "H3_REVERSIBLE_FAST_SLOW_EXCHANGE"
    ]
    assert (
        h3["maximum_internal_transfer_residual_abs_bq_m2"].max()
        <= 1.0e-9
    )


def test_review_mass_balance_all_35_runs() -> None:
    mass = pd.read_csv(REPORTS / "mechanism_mass_balance.csv")
    assert len(mass) == 35
    assert mass["mass_balance_pass"].all()
    assert (mass["nan_count"] == 0).all()
    assert (mass["inf_count"] == 0).all()
    assert (mass["negative_inventory_count"] == 0).all()
    assert (mass["negative_concentration_count"] == 0).all()


def test_review_metrics_independently_recomputed() -> None:
    predictions = pd.read_csv(REPORTS / "mechanism_late_predictions.csv")
    reported = pd.read_csv(REPORTS / "mechanism_late_metrics.csv")
    for mechanism_id in CANDIDATES:
        frame = predictions[
            (predictions["mechanism_id"] == mechanism_id)
            & (predictions["run_id"] == "RUN_01")
            & (predictions["compartment"] == "plant_body")
        ]
        independent = independent_log_metrics(frame)
        row = reported[
            (reported["mechanism_id"] == mechanism_id)
            & (reported["run_id"] == "RUN_01")
            & (reported["partition"] == "pseudo_holdout_a")
        ].iloc[0]
        for name, value in independent.items():
            assert math.isclose(value, float(row[name]), rel_tol=1.0e-12)


def test_review_selection_fail_closed() -> None:
    passes = independently_recomputed_forcing_passes()
    h2_boundary = True
    h3_robust = (
        len(passes["H3_REVERSIBLE_FAST_SLOW_EXCHANGE"])
        >= PROTOCOL["success_criteria"]["forcing_scenarios_required_to_persist"]
    )
    h1_primary = len(passes["H1_DYNAMIC_WATER_STORAGE"]) > 0
    h4_primary = len(passes["H4_OBT_MEDIATED_RECYCLE"]) > 0
    supported = h1_primary or (not h2_boundary) or h3_robust or h4_primary
    assert supported is False
    result = load_selection()
    assert (
        result["mechanism_discrimination_status"]
        == "NO_MINIMAL_MECHANISM_SUPPORTED"
    )
    assert result["best_supported_mechanism"] is None


def test_review_no_formal_src_changes() -> None:
    assert git("diff", "--quiet", "main...HEAD", "--", "src").returncode == 0


def test_review_no_formal_config_changes() -> None:
    assert (
        git("diff", "--quiet", "main...HEAD", "--", "configs").returncode
        == 0
    )


def test_review_production_gate_stays_blocked() -> None:
    result = load_selection()
    assert result["production_gate_eligible"] is False
    assert result["empirical_validation_claim"] is False
    assert result["v3_physics_implementation_status"] == "NOT_STARTED"
    assert (
        result["v3_physics_start_gate"]
        == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )


def test_review_attack_forged_h3_forcing_count_rejected() -> None:
    forged = load_selection()
    forged["candidate_results"]["H3_REVERSIBLE_FAST_SLOW_EXCHANGE"][
        "forcing_pass_count"
    ] = 5
    independent = independently_recomputed_forcing_passes()
    assert forged["candidate_results"][
        "H3_REVERSIBLE_FAST_SLOW_EXCHANGE"
    ]["forcing_pass_count"] == 5
    assert len(independent["H3_REVERSIBLE_FAST_SLOW_EXCHANGE"]) == 4


def test_review_attack_forged_h2_boundary_summary_rejected() -> None:
    forged = load_selection()
    forged["candidate_results"]["H2_PARALLEL_FAST_SLOW_RESIDUAL"][
        "boundary_hit"
    ] = False
    search = pd.read_csv(REPORTS / "mechanism_parameter_search.csv")
    subset = search[
        search["mechanism_id"] == "H2_PARALLEL_FAST_SLOW_RESIDUAL"
    ]
    best = independently_selected_grid_row(
        "H2_PARALLEL_FAST_SLOW_RESIDUAL"
    )
    independent_boundary = (
        best["parameter_1_value"] == subset["parameter_1_value"].min()
        or best["parameter_1_value"] == subset["parameter_1_value"].max()
        or best["parameter_2_value"] == subset["parameter_2_value"].min()
        or best["parameter_2_value"] == subset["parameter_2_value"].max()
    )
    assert forged["candidate_results"][
        "H2_PARALLEL_FAST_SLOW_RESIDUAL"
    ]["boundary_hit"] is False
    assert independent_boundary


def test_review_h1_changes_mapping_not_inventory_contract() -> None:
    source = (
        MECHANISM_ROOT / "models" / "dynamic_water_storage.py"
    ).read_text(encoding="utf-8")
    assert "inventory_bq_m2" in source
    assert "return max(float(inventory_bq_m2), 0.0) / storage / 1000.0" in source
    assert PROTOCOL["candidates"]["H1_DYNAMIC_WATER_STORAGE"][
        "new_fitted_parameter_count"
    ] == 0


def test_review_h4_obt_consistency_failure_recomputed() -> None:
    structural = pd.read_csv(
        REPORTS / "mechanism_structural_diagnostics.csv"
    )
    primary = structural[structural["run_id"] == "RUN_01"].set_index(
        "mechanism_id"
    )
    observed = 16000.0
    h0_error = abs(
        math.log10(
            primary.loc[
                "H0_CURRENT_SINGLE_POOL",
                "plant_body_obt_bq_l_combustion_water",
            ]
            / observed
        )
    )
    h4_error = abs(
        math.log10(
            primary.loc[
                "H4_OBT_MEDIATED_RECYCLE",
                "plant_body_obt_bq_l_combustion_water",
            ]
            / observed
        )
    )
    assert h4_error > h0_error


def test_review_report_finalization_is_docs_only() -> None:
    changed = git(
        "diff",
        "--name-only",
        TESTED_EVIDENCE_PARENT,
        REVIEW_TARGET,
    ).stdout.splitlines()
    assert changed
    assert all(path.startswith("docs/") for path in changed)


def test_review_trusted_registry_unchanged() -> None:
    path = "validation/v3/policy/trusted_external_evidence_registry.yaml"
    assert git("diff", "--quiet", "main...HEAD", "--", path).returncode == 0
