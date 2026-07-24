from __future__ import annotations

from copy import deepcopy
from itertools import combinations

import numpy as np
from scipy.stats import spearmanr

from ..case import run_short_case
from .uncertainty import (
    UncertaintyResult,
    partition_parameters_by_mode,
    run_uncertainty,
)


DOSE_OUTPUTS = (
    "inhalation_dose_sv",
    "skin_absorption_dose_sv",
    "plant_ingestion_dose_sv",
    "milk_dose_sv",
    "meat_dose_sv",
    "total_effective_dose_sv",
)
PATHWAY_OUTPUTS = list(DOSE_OUTPUTS[:-1])


def _serializable_run(result: UncertaintyResult) -> dict:
    return {
        "seed": result.seed,
        "sample_count": len(next(iter(result.outcomes.values()))),
        "statistics": result.statistics,
        "rank_correlations": result.rank_correlations,
        "rank_order": sorted(
            result.parameter_samples,
            key=lambda name: abs(
                result.rank_correlations[name]["total_effective_dose_sv"]
            ),
            reverse=True,
        )[:10],
        "pathway_contributions": result.pathway_contributions,
    }


def _rank_stability(
    results: list[UncertaintyResult],
) -> dict[str, float | bool]:
    names = sorted(results[0].parameter_samples)
    coefficients = [
        np.asarray(
            [
                abs(result.rank_correlations[name]["total_effective_dose_sv"])
                for name in names
            ]
        )
        for result in results
    ]
    pairwise = []
    orders = [
        sorted(
            names,
            key=lambda name: abs(
                result.rank_correlations[name]["total_effective_dose_sv"]
            ),
            reverse=True,
        )
        for result in results
    ]
    top_three_overlap = []
    for first, second in combinations(coefficients, 2):
        coefficient = spearmanr(first, second).statistic
        pairwise.append(float(coefficient) if np.isfinite(coefficient) else 0.0)
    for first, second in combinations(orders, 2):
        first_set = set(first[:3])
        second_set = set(second[:3])
        top_three_overlap.append(
            len(first_set & second_set) / len(first_set | second_set)
        )
    return {
        "minimum_pairwise_spearman": min(pairwise) if pairwise else 1.0,
        "mean_pairwise_spearman": float(np.mean(pairwise)) if pairwise else 1.0,
        "minimum_top3_jaccard": min(top_three_overlap) if top_three_overlap else 1.0,
        "dominant_parameter_consistent": len({order[0] for order in orders}) == 1,
    }


def _quantile_stability(
    coarse: UncertaintyResult,
    fine: UncertaintyResult,
) -> dict[str, float]:
    coarse_stats = coarse.statistics["total_effective_dose_sv"]
    fine_stats = fine.statistics["total_effective_dose_sv"]
    result = {}
    for name in ("median", "p05", "p95", "mean", "std"):
        denominator = max(abs(fine_stats[name]), 1.0e-30)
        result[name] = abs(coarse_stats[name] - fine_stats[name]) / denominator
    result["maximum_relative_change"] = max(result.values())
    return result


def run_full_model_lhs_convergence(
    base_config: dict,
    specifications: list[dict],
    *,
    sample_sizes: tuple[int, ...] = (64, 128, 256),
    primary_seed: int = 20260724,
    additional_seeds: tuple[int, ...] = (20260725, 20260726, 20260727),
    audit_duration_hours: float = 24.0,
) -> dict:
    """Run mode-aware LHS convergence on a real full-dose model configuration."""

    if tuple(sorted(sample_sizes)) != sample_sizes or len(sample_sizes) < 3:
        raise ValueError("Use at least three increasing uncertainty sample sizes")
    if len(set(additional_seeds)) < 3 or primary_seed in additional_seeds:
        raise ValueError("Use at least three distinct additional seeds")
    config = deepcopy(base_config)
    config["duration_hours"] = audit_duration_hours
    config["time_step_seconds"] = 3600
    active, inactive = partition_parameters_by_mode(config, specifications)
    run_count = 0

    def model(sample_config: dict) -> dict[str, float]:
        nonlocal run_count
        run_count += 1
        final = run_short_case(sample_config).iloc[-1]
        return {name: float(final[name]) for name in DOSE_OUTPUTS}

    size_results = {
        count: run_uncertainty(
            model,
            config,
            active,
            count,
            "latin_hypercube",
            primary_seed,
            pathway_output_names=PATHWAY_OUTPUTS,
        )
        for count in sample_sizes
    }
    reproducibility_check = run_uncertainty(
        model,
        config,
        active,
        sample_sizes[0],
        "latin_hypercube",
        primary_seed,
        pathway_output_names=PATHWAY_OUTPUTS,
    )
    same_seed_reproducible = all(
        np.array_equal(
            size_results[sample_sizes[0]].outcomes[name],
            reproducibility_check.outcomes[name],
        )
        for name in DOSE_OUTPUTS
    )
    final_count = sample_sizes[-1]
    seed_results = [size_results[final_count]]
    for seed in additional_seeds:
        seed_results.append(
            run_uncertainty(
                model,
                config,
                active,
                final_count,
                "latin_hypercube",
                seed,
                pathway_output_names=PATHWAY_OUTPUTS,
            )
        )
    quantile = _quantile_stability(
        size_results[sample_sizes[-2]],
        size_results[sample_sizes[-1]],
    )
    rank = _rank_stability(seed_results)
    different_seed_statistics_reasonable = all(
        (
            result.statistics["total_effective_dose_sv"]["p05"]
            <= result.statistics["total_effective_dose_sv"]["median"]
            <= result.statistics["total_effective_dose_sv"]["p95"]
            and result.statistics["total_effective_dose_sv"]["mean"] > 0.0
            and result.statistics["total_effective_dose_sv"]["std"] > 0.0
        )
        for result in seed_results
    )
    expected_run_count = (
        sum(sample_sizes)
        + sample_sizes[0]
        + len(additional_seeds) * final_count
    )
    parameter_write_status = all(
        np.ptp(size_results[final_count].parameter_samples[name]) > 0.0
        for name in (specification["name"] for specification in active)
    )
    rank_status = (
        "PASS"
        if rank["minimum_pairwise_spearman"] >= 0.70
        else "LIMITED_WITH_EVIDENCE"
    )
    quantile_status = (
        "PASS"
        if quantile["maximum_relative_change"] <= 0.10
        else "FAIL"
    )
    pass_status = bool(
        same_seed_reproducible
        and different_seed_statistics_reasonable
        and parameter_write_status
        and run_count == expected_run_count
        and quantile_status == "PASS"
        and rank_status in {"PASS", "LIMITED_WITH_EVIDENCE"}
    )
    return {
        "status": "PASS" if pass_status else "FAIL",
        "case": base_config["name"],
        "audit_duration_hours": audit_duration_hours,
        "active_parameters": [specification["name"] for specification in active],
        "inactive_parameters": inactive,
        "sample_count": final_count,
        "sample_sizes": list(sample_sizes),
        "seed": primary_seed,
        "additional_seeds": list(additional_seeds),
        "model_run_count": run_count,
        "expected_model_run_count": expected_run_count,
        "parameter_write_status": (
            "PASS" if parameter_write_status else "FAIL"
        ),
        "same_seed_reproducible": same_seed_reproducible,
        "different_seed_statistics_reasonable": different_seed_statistics_reasonable,
        "sample_size_runs": {
            str(count): _serializable_run(result)
            for count, result in size_results.items()
        },
        "seed_runs": [_serializable_run(result) for result in seed_results],
        "quantile_stability": {
            **quantile,
            "status": quantile_status,
        },
        "rank_stability": {
            **rank,
            "status": rank_status,
        },
    }
