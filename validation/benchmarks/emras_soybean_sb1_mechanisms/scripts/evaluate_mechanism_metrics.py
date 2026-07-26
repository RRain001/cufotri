from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def log_metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    observed = frame["observed_bq_l_water"].to_numpy(float)
    predicted = frame["predicted_bq_l_water"].to_numpy(float)
    if (
        len(frame) == 0
        or not np.isfinite(observed).all()
        or not np.isfinite(predicted).all()
        or np.any(observed <= 0)
        or np.any(predicted <= 0)
    ):
        raise ValueError("Log metrics require finite positive observations and predictions")
    residual = np.log10(predicted) - np.log10(observed)
    ratio = predicted / observed
    return {
        "log10_rmse": float(np.sqrt(np.mean(residual**2))),
        "log10_mean_bias": float(np.mean(residual)),
        "median_predicted_to_observed_ratio": float(np.median(ratio)),
        "factor_2_coverage": float(np.mean((ratio >= 0.5) & (ratio <= 2.0))),
        "factor_10_coverage": float(np.mean((ratio >= 0.1) & (ratio <= 10.0))),
        "n": int(len(frame)),
    }


def median_ratio_closeness_dex(ratio: float) -> float:
    if ratio <= 0 or not math.isfinite(ratio):
        return math.inf
    return abs(math.log10(ratio))


def late_improvement(
    reference: dict[str, float | int],
    candidate: dict[str, float | int],
) -> dict[str, float]:
    reference_ratio = float(reference["median_predicted_to_observed_ratio"])
    candidate_ratio = float(candidate["median_predicted_to_observed_ratio"])
    return {
        "late_rmse_improvement_dex": (
            float(reference["log10_rmse"]) - float(candidate["log10_rmse"])
        ),
        "late_median_ratio_closeness_improvement_dex": (
            median_ratio_closeness_dex(reference_ratio)
            - median_ratio_closeness_dex(candidate_ratio)
        ),
        "late_median_ratio_improvement_factor_toward_unity": 10.0
        ** (
            median_ratio_closeness_dex(reference_ratio)
            - median_ratio_closeness_dex(candidate_ratio)
        ),
    }


def evaluate_primary_success(
    *,
    protocol: dict[str, Any],
    reference_calibration: dict[str, float | int],
    reference_late: dict[str, float | int],
    candidate_calibration: dict[str, float | int],
    candidate_late: dict[str, float | int],
    early_predictions: pd.DataFrame,
    finite_nonnegative: bool,
    mass_balance_pass: bool,
    boundary_hit: bool,
    identifiability_pass: bool,
    forcing_pass_count: int,
    obt_consistency_pass: bool,
) -> dict[str, Any]:
    criteria = protocol["success_criteria"]
    improvement = late_improvement(reference_late, candidate_late)
    ratios = (
        early_predictions["predicted_bq_l_water"].to_numpy(float)
        / early_predictions["observed_bq_l_water"].to_numpy(float)
    )
    factor_limit = float(criteria["early_prediction_factor_limit"])
    checks = {
        "late_rmse": (
            improvement["late_rmse_improvement_dex"]
            >= float(criteria["late_log10_rmse_improvement_minimum_dex"])
        ),
        "late_median_ratio": (
            improvement["late_median_ratio_closeness_improvement_dex"]
            >= float(
                criteria[
                    "late_median_ratio_closeness_improvement_minimum_dex"
                ]
            )
        ),
        "calibration_not_worse": (
            float(candidate_calibration["log10_rmse"])
            - float(reference_calibration["log10_rmse"])
            <= float(criteria["calibration_log10_rmse_worsening_maximum_dex"])
        ),
        "early_within_factor": bool(
            np.all((ratios >= 1.0 / factor_limit) & (ratios <= factor_limit))
        ),
        "finite_nonnegative": bool(finite_nonnegative),
        "mass_balance": bool(mass_balance_pass),
        "no_parameter_boundary_hit": not bool(boundary_hit),
        "identifiability": bool(identifiability_pass),
        "forcing_robustness": (
            int(forcing_pass_count)
            >= int(criteria["forcing_scenarios_required_to_persist"])
        ),
        "obt_consistency": bool(obt_consistency_pass),
    }
    return {
        **improvement,
        "calibration_rmse_change_dex": (
            float(candidate_calibration["log10_rmse"])
            - float(reference_calibration["log10_rmse"])
        ),
        "early_min_ratio": float(np.min(ratios)),
        "early_max_ratio": float(np.max(ratios)),
        "forcing_pass_count": int(forcing_pass_count),
        "checks": checks,
        "supported": all(checks.values()),
    }
