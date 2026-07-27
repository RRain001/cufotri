from __future__ import annotations

import copy
import hashlib
import importlib.util
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = (
    ROOT / "validation" / "benchmarks" / "slow_mechanism_discriminability"
)
PROTOCOL_PATH = (
    BENCHMARK / "preregistration" / "h2_h3_discriminability_protocol.yaml"
)
RUNNER_PATH = BENCHMARK / "scripts" / "run_discriminability_analysis.py"
RESULTS = BENCHMARK / "results"
MECHANISMS = ("H2_SB1_FROZEN", "H3_SB1_FROZEN")
GRID = [0.2, 0.5, 1, 3, 6, 12, 24, 48, 72, 120, 168, 336, 504, 768]


def load_module(path: Path, name: str) -> Any:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


RUNNER = load_module(RUNNER_PATH, "independent_review_discriminability_runner")
PROTOCOL = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def forcing_by_design() -> dict[str, pd.DataFrame]:
    return {
        design_id: RUNNER.build_forcing(PROTOCOL, design_id)
        for design_id in PROTOCOL["designs"]
    }


@pytest.fixture(scope="module")
def independent_base() -> tuple[pd.DataFrame, pd.DataFrame]:
    mechanism_runner = RUNNER.load_mechanism_runner()
    predictions: list[pd.DataFrame] = []
    qa_rows: list[pd.DataFrame] = []
    for design_id in PROTOCOL["designs"]:
        current_predictions, current_qa = RUNNER.run_design(
            mechanism_runner, PROTOCOL, design_id
        )
        predictions.append(current_predictions)
        qa_rows.append(current_qa)
    return (
        pd.concat(predictions, ignore_index=True),
        pd.concat(qa_rows, ignore_index=True),
    )


def exposure(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["phase"].str.startswith("CONTROLLED_EXPOSURE")]


def assert_zero_background_after_final(
    frame: pd.DataFrame, final_exposure_end_h: float
) -> None:
    selected = frame[
        frame["hours_from_first_exposure_start"] > final_exposure_end_h
    ]
    assert len(selected) > 0
    assert (selected["air_moisture_hto_bq_ml_water"] == 0.0).all()
    assert set(selected["phase"]) == {"STRICT_ZERO_BACKGROUND"}


def test_review_d0_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = forcing_by_design["D0_SINGLE_PULSE_BASELINE"]
    exposed = exposure(frame)
    assert len(exposed) == 12
    assert set(exposed["phase"]) == {"CONTROLLED_EXPOSURE_1"}
    assert set(exposed["air_moisture_hto_bq_ml_water"]) == {52700.0}
    assert_zero_background_after_final(frame, 1.0)


def test_review_d1_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = forcing_by_design["D1_SECOND_PULSE_AFTER_24H"]
    exposed = exposure(frame)
    first = exposed[exposed["phase"] == "CONTROLLED_EXPOSURE_1"]
    second = exposed[exposed["phase"] == "CONTROLLED_EXPOSURE_2"]
    assert (len(first), len(second)) == (12, 12)
    assert second["hours_from_first_exposure_start"].min() == pytest.approx(
        25.0 + 1.0 / 12.0
    )
    assert_zero_background_after_final(frame, 26.0)


def test_review_d2_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = forcing_by_design["D2_SECOND_PULSE_AFTER_72H"]
    exposed = exposure(frame)
    first = exposed[exposed["phase"] == "CONTROLLED_EXPOSURE_1"]
    second = exposed[exposed["phase"] == "CONTROLLED_EXPOSURE_2"]
    assert (len(first), len(second)) == (12, 12)
    assert second["hours_from_first_exposure_start"].min() == pytest.approx(
        73.0 + 1.0 / 12.0
    )
    assert_zero_background_after_final(frame, 74.0)


def test_review_d3_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = forcing_by_design["D3_SHORT_STEP_24H"]
    exposed = exposure(frame)
    assert len(exposed) == 24 * 12
    assert set(exposed["air_moisture_hto_bq_ml_water"]) == {5270.0}
    assert exposed["hours_from_first_exposure_start"].max() == 24.0
    assert_zero_background_after_final(frame, 24.0)


def test_review_d4_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = forcing_by_design["D4_LONG_STEP_72H"]
    exposed = exposure(frame)
    assert len(exposed) == 72 * 12
    assert set(exposed["air_moisture_hto_bq_ml_water"]) == {5270.0}
    assert exposed["hours_from_first_exposure_start"].max() == 72.0
    assert_zero_background_after_final(frame, 72.0)


def test_review_d5_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = forcing_by_design["D5_PULSE_WASHOUT_REEXPOSURE"]
    exposed = exposure(frame)
    first = exposed[exposed["phase"] == "CONTROLLED_EXPOSURE_1"]
    second = exposed[exposed["phase"] == "CONTROLLED_EXPOSURE_2"]
    assert (len(first), len(second)) == (12, 24 * 12)
    assert set(first["air_moisture_hto_bq_ml_water"]) == {52700.0}
    assert set(second["air_moisture_hto_bq_ml_water"]) == {5270.0}
    assert_zero_background_after_final(frame, 97.0)


def test_review_d3_minimum_followup_is_120h() -> None:
    duration = PROTOCOL["experiment_duration_contract"]
    minimum = duration["minimum_discriminating_experiment"]
    extended = duration["extended_diagnostic_experiment"]
    assert minimum == {
        "design_id": "D3_SHORT_STEP_24H",
        "exposure_duration_h": 24,
        "post_exposure_observation_h": 120,
        "total_elapsed_duration_h": 144,
        "approximate_total_duration_days": 6,
        "required_sampling_hours_after_final_exposure": [0.2, 48, 120],
    }
    assert extended["required"] is False
    assert extended["maximum_followup_days_after_final_exposure"] == 120


def test_review_h2_parameters_frozen() -> None:
    parameters = PROTOCOL["target_models"]["H2_SB1_FROZEN"]["parameters"]
    assert {name: float(item["value"]) for name, item in parameters.items()} == {
        "slow_capture_fraction": 0.001,
        "slow_release_rate_s": 1.0e-6,
    }


def test_review_h3_parameters_frozen() -> None:
    parameters = PROTOCOL["target_models"]["H3_SB1_FROZEN"]["parameters"]
    assert {name: float(item["value"]) for name, item in parameters.items()} == {
        "fast_to_slow_rate_s": 1.0e-7,
        "slow_to_fast_rate_s": 1.0e-6,
    }


def test_review_no_parameter_refit() -> None:
    assert PROTOCOL["scope"]["parameter_refit_allowed"] is False
    assert PROTOCOL["scope"]["parameter_refit_count"] == 0
    assert PROTOCOL["monte_carlo"]["parameter_refit"] is False
    assert PROTOCOL["robustness"]["slow_process_parameter_refit"] is False


def test_review_classifier_uses_total_tfwt_only() -> None:
    primary = PROTOCOL["observables"]["primary"]
    assert primary["id"] == "total_plant_body_tfwt"
    assert primary["model_field"] == "plant_body_tfwt_bq_l_water"
    assert primary["classification_role"] == "PRIMARY_ONLY"


def test_review_latent_pool_not_used() -> None:
    assert PROTOCOL["observables"]["latent_pool_used_for_classification"] is False
    assert PROTOCOL["monte_carlo"]["latent_pool_input_allowed"] is False
    assert PROTOCOL["design_success_criteria"][
        "latent_pool_observation_allowed"
    ] is False


def prediction_vectors(
    predictions: pd.DataFrame, design_id: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    selected = predictions[
        (predictions["design_id"] == design_id)
        & (predictions["sample_context"] == "POST_FINAL_EXPOSURE")
    ]
    pivot = selected.pivot(
        index="sample_hour",
        columns="mechanism_id",
        values="plant_body_tfwt_bq_l_water",
    ).sort_index()
    return (
        pivot.index.to_numpy(float),
        pivot["H2_SB1_FROZEN"].to_numpy(float),
        pivot["H3_SB1_FROZEN"].to_numpy(float),
    )


def test_review_pointwise_separation_recomputed(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    predictions, _ = independent_base
    expected = {
        "D0_SINGLE_PULSE_BASELINE": 0.24162527879806772,
        "D1_SECOND_PULSE_AFTER_24H": 0.24227310466213803,
        "D2_SECOND_PULSE_AFTER_72H": 0.3816106861748447,
        "D3_SHORT_STEP_24H": 0.4644692161799018,
        "D4_LONG_STEP_72H": 0.6747577773160778,
        "D5_PULSE_WASHOUT_REEXPOSURE": 0.6829246580200246,
    }
    for design_id, maximum in expected.items():
        _, h2, h3 = prediction_vectors(predictions, design_id)
        delta = np.abs(np.log10(h2) - np.log10(h3))
        assert float(delta.max()) == pytest.approx(maximum, abs=1.0e-12)


def stable_seed(key: str) -> int:
    base = int(PROTOCOL["monte_carlo"]["random_seed"])
    digest = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
    return (base + digest) % (2**32 - 1)


def independent_noise(
    truth: np.ndarray, cv: float, key: str
) -> np.ndarray:
    count = int(
        PROTOCOL["monte_carlo"][
            "replicates_per_truth_model_design_noise"
        ]
    )
    sigma = math.sqrt(math.log1p(cv**2))
    mean = -0.5 * sigma**2
    generator = np.random.default_rng(stable_seed(key))
    return truth[None, :] * generator.lognormal(
        mean, sigma, size=(count, len(truth))
    )


def independent_accuracy(
    observations: np.ndarray,
    h2: np.ndarray,
    h3: np.ndarray,
    truth_model: str,
) -> float:
    observed = np.log10(np.clip(observations, np.finfo(float).tiny, None))
    h2_log = np.log10(np.clip(h2, np.finfo(float).tiny, None))
    h3_log = np.log10(np.clip(h3, np.finfo(float).tiny, None))
    h2_rmse = np.sqrt(np.mean((observed - h2_log) ** 2, axis=1))
    h3_rmse = np.sqrt(np.mean((observed - h3_log) ** 2, axis=1))
    selected = np.where(
        h2_rmse < h3_rmse,
        "H2_SB1_FROZEN",
        np.where(h3_rmse < h2_rmse, "H3_SB1_FROZEN", "INCONCLUSIVE"),
    )
    return float(np.mean(selected == truth_model))


def independent_accuracy_matrix(
    predictions: pd.DataFrame,
    design_id: str,
    prefix: str,
    selected_hours: list[float] | None = None,
) -> dict[tuple[str, float], float]:
    hours, h2, h3 = prediction_vectors(predictions, design_id)
    if selected_hours is None:
        indices = np.arange(len(hours))
    else:
        indices = np.asarray(
            [
                int(np.flatnonzero(np.isclose(hours, sample_hour))[0])
                for sample_hour in selected_hours
            ]
        )
    output: dict[tuple[str, float], float] = {}
    for cv in (0.10, 0.20, 0.30):
        for truth_model, truth in zip(MECHANISMS, (h2, h3), strict=True):
            observations = independent_noise(
                truth,
                cv,
                f"{prefix}:{design_id}:{truth_model}:{cv:.2f}",
            )
            output[(truth_model, cv)] = independent_accuracy(
                observations[:, indices], h2[indices], h3[indices], truth_model
            )
    return output


def test_review_d3_full_grid_bidirectional_accuracy(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    predictions, _ = independent_base
    accuracy = independent_accuracy_matrix(
        predictions, "D3_SHORT_STEP_24H", "full_grid"
    )
    assert set(accuracy.values()) == {1.0}


def test_review_d3_minimum_grid_bidirectional_accuracy(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    predictions, _ = independent_base
    accuracy = independent_accuracy_matrix(
        predictions,
        "D3_SHORT_STEP_24H",
        "sampling",
        [0.2, 48, 120],
    )
    assert accuracy == {
        ("H2_SB1_FROZEN", 0.10): 1.000,
        ("H3_SB1_FROZEN", 0.10): 1.000,
        ("H2_SB1_FROZEN", 0.20): 1.000,
        ("H3_SB1_FROZEN", 0.20): 1.000,
        ("H2_SB1_FROZEN", 0.30): 0.998,
        ("H3_SB1_FROZEN", 0.30): 0.991,
    }
    for value in accuracy.values():
        standard_error = math.sqrt(value * (1.0 - value) / 1000)
        assert standard_error <= 0.003


def independent_greedy_d3(predictions: pd.DataFrame) -> list[float]:
    design_id = "D3_SHORT_STEP_24H"
    hours, h2, h3 = prediction_vectors(predictions, design_id)
    delta = np.abs(np.log10(h2) - np.log10(h3))
    selected = [int(np.argmax(delta))]
    cached: dict[tuple[str, float], np.ndarray] = {}
    for cv in (0.10, 0.20, 0.30):
        for truth_model, truth in zip(MECHANISMS, (h2, h3), strict=True):
            cached[(truth_model, cv)] = independent_noise(
                truth,
                cv,
                f"sampling:{design_id}:{truth_model}:{cv:.2f}",
            )

    def evaluate(indices: list[int]) -> dict[tuple[str, float], float]:
        ordered = np.asarray(sorted(indices), dtype=int)
        return {
            (truth_model, cv): independent_accuracy(
                cached[(truth_model, cv)][:, ordered],
                h2[ordered],
                h3[ordered],
                truth_model,
            )
            for cv in (0.10, 0.20, 0.30)
            for truth_model in MECHANISMS
        }

    thresholds = {0.10: 0.90, 0.20: 0.80, 0.30: 0.70}
    while len(selected) <= 8:
        values = evaluate(selected)
        strong_count = int(np.sum(delta[sorted(selected)] >= 0.30))
        if (
            len(selected) >= 3
            and strong_count >= 2
            and all(
                min(values[(model, cv)] for model in MECHANISMS)
                >= thresholds[cv]
                for cv in thresholds
            )
        ):
            return [float(hours[index]) for index in sorted(selected)]
        candidates = [
            index for index in range(len(hours)) if index not in selected
        ]
        scores: list[tuple[tuple[float, float, float], int]] = []
        for candidate in candidates:
            trial = evaluate(selected + [candidate])
            cv20 = min(trial[(model, 0.20)] for model in MECHANISMS)
            normalized = min(
                trial[(model, cv)] / thresholds[cv]
                for model in MECHANISMS
                for cv in thresholds
            )
            scores.append(
                ((cv20, normalized, -float(hours[candidate])), candidate)
            )
        selected.append(max(scores, key=lambda item: item[0])[1])
    raise AssertionError("No D3 sampling set met the frozen criteria")


def test_review_minimum_sampling_from_frozen_grid(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    predictions, _ = independent_base
    selected = independent_greedy_d3(predictions)
    assert selected == [0.2, 48.0, 120.0]
    assert set(selected) <= set(GRID)


def test_review_minimum_sampling_bidirectional(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    predictions, _ = independent_base
    accuracy = independent_accuracy_matrix(
        predictions,
        "D3_SHORT_STEP_24H",
        "sampling",
        [0.2, 48, 120],
    )
    assert min(accuracy[(model, 0.30)] for model in MECHANISMS) == 0.991


def test_review_minimum_sampling_reproducible(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    predictions, _ = independent_base
    assert independent_greedy_d3(predictions) == independent_greedy_d3(
        predictions
    )


def test_review_recomputed_base_matches_frozen_snapshots(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    predictions, qa = independent_base
    stored_predictions = pd.read_csv(
        RESULTS / "synthetic_design_predictions.csv"
    )
    stored_qa = pd.read_csv(RESULTS / "design_run_qa.csv")
    pd.testing.assert_frame_equal(
        predictions.reset_index(drop=True),
        stored_predictions.reset_index(drop=True),
        check_exact=False,
        rtol=1.0e-13,
        atol=1.0e-13,
    )
    pd.testing.assert_frame_equal(
        qa.reset_index(drop=True),
        stored_qa[qa.columns].reset_index(drop=True),
        check_exact=False,
        rtol=1.0e-13,
        atol=1.0e-13,
    )
    assert set(stored_qa["run_class"]) == {"BASE_DESIGN"}


def test_review_d3_all_robustness_factors_pass() -> None:
    robustness = pd.read_csv(RESULTS / "design_robustness_matrix.csv")
    d3 = robustness[robustness["design_id"] == "D3_SHORT_STEP_24H"]
    assert set(d3["factor"]) == {
        "exposure_concentration_multiplier",
        "relative_humidity_percent",
        "wind_speed_m_s",
        "stomatal_resistance_multiplier",
    }
    assert d3.groupby("factor").size().eq(3).all()
    assert d3["criteria_pass"].all()


def test_review_d2_robustness_not_evaluated() -> None:
    robustness = pd.read_csv(RESULTS / "design_robustness_matrix.csv")
    assert not (
        robustness["design_id"] == "D2_SECOND_PULSE_AFTER_72H"
    ).any()


def test_review_d4_fails_at_low_wind() -> None:
    robustness = pd.read_csv(RESULTS / "design_robustness_matrix.csv")
    failure = robustness[
        (robustness["design_id"] == "D4_LONG_STEP_72H")
        & (robustness["factor"] == "wind_speed_m_s")
        & np.isclose(robustness["level"], 0.2)
    ]
    assert len(failure) == 1
    assert bool(failure.iloc[0]["criteria_pass"]) is False
    assert int(failure.iloc[0]["strong_separation_point_count"]) == 1


def test_review_d5_fails_minimum_set_and_robustness() -> None:
    minimum = pd.read_csv(RESULTS / "minimum_sampling_design.csv")
    d5_minimum = minimum[
        minimum["design_id"] == "D5_PULSE_WASHOUT_REEXPOSURE"
    ].iloc[0]
    assert d5_minimum["status"] == (
        "NO_3_TO_8_POINT_SET_MEETS_FROZEN_CRITERIA"
    )
    robustness = pd.read_csv(RESULTS / "design_robustness_matrix.csv")
    d5 = robustness[
        robustness["design_id"] == "D5_PULSE_WASHOUT_REEXPOSURE"
    ]
    assert not d5["criteria_pass"].any()


def test_review_all_designs_finite_nonnegative(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    predictions, qa = independent_base
    numeric = predictions.select_dtypes(include=[np.number]).to_numpy()
    assert np.isfinite(numeric).all()
    assert qa["finite_nonnegative_pass"].all()
    assert (qa[["nan_count", "inf_count"]] == 0).all().all()
    assert (
        qa[["negative_inventory_count", "negative_concentration_count"]] == 0
    ).all().all()


def test_review_all_designs_mass_conservative(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    _, qa = independent_base
    assert qa["mass_conservation_pass"].all()
    assert (
        qa["maximum_formal_mass_closure_abs_bq_m2"] <= 1.0e-6
    ).all()


def test_review_internal_transfer_ledger(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    _, qa = independent_base
    assert (
        qa["maximum_internal_transfer_ledger_residual_abs_bq_m2"] <= 1.0e-9
    ).all()
    assert (
        qa["maximum_internal_state_sum_roundoff_abs_bq_m2"] >= 0.0
    ).all()
    assert not np.array_equal(
        qa["maximum_internal_transfer_ledger_residual_abs_bq_m2"].to_numpy(),
        qa["maximum_internal_state_sum_roundoff_abs_bq_m2"].to_numpy(),
    )


def test_review_no_tolerance_relaxation() -> None:
    assert RUNNER.FORMAL_MASS_TOLERANCE_BQ_M2 == 1.0e-6
    assert RUNNER.INTERNAL_LEDGER_TOLERANCE_BQ_M2 == 1.0e-9


def review_contract_errors(protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if protocol["sampling"]["candidate_hours_after_final_exposure"] != GRID:
        errors.append("sampling_grid")
    if protocol["monte_carlo"]["coefficient_of_variation"] != [
        0.10,
        0.20,
        0.30,
    ]:
        errors.append("noise_levels")
    if protocol["scope"]["parameter_refit_allowed"]:
        errors.append("parameter_refit")
    if protocol["observables"]["latent_pool_used_for_classification"]:
        errors.append("latent_pool")
    if protocol["scope"]["empirical_validation_claim"]:
        errors.append("empirical_claim")
    duration = protocol["experiment_duration_contract"]
    if (
        duration["minimum_discriminating_experiment"][
            "post_exposure_observation_h"
        ]
        != 120
        or duration["extended_diagnostic_experiment"]["required"]
    ):
        errors.append("duration_conflation")
    return errors


def test_review_attack_modified_noise_rejected() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["monte_carlo"]["coefficient_of_variation"] = [0.10, 0.25, 0.30]
    assert "noise_levels" in review_contract_errors(forged)


def test_review_attack_modified_sampling_rejected(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["sampling"]["candidate_hours_after_final_exposure"] = [
        value for value in GRID if value != 48
    ]
    forged["sampling"]["candidate_hours_after_final_exposure"].append(72)
    assert "sampling_grid" in review_contract_errors(forged)
    predictions, _ = independent_base
    assert independent_greedy_d3(predictions) != [0.2, 72.0, 120.0]


def test_review_attack_parameter_refit_rejected() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["scope"]["parameter_refit_allowed"] = True
    assert "parameter_refit" in review_contract_errors(forged)


def test_review_attack_latent_pool_rejected() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["observables"]["latent_pool_used_for_classification"] = True
    assert "latent_pool" in review_contract_errors(forged)


def test_review_attack_empirical_claim_rejected() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["scope"]["empirical_validation_claim"] = True
    assert "empirical_claim" in review_contract_errors(forged)


def test_review_attack_duration_conflation_rejected() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["experiment_duration_contract"][
        "minimum_discriminating_experiment"
    ]["post_exposure_observation_h"] = 120 * 24
    forged["experiment_duration_contract"]["extended_diagnostic_experiment"][
        "required"
    ] = True
    assert "duration_conflation" in review_contract_errors(forged)


def test_review_attack_forged_minimum_accuracy_rejected(
    independent_base: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    predictions, _ = independent_base
    independent = independent_accuracy_matrix(
        predictions,
        "D3_SHORT_STEP_24H",
        "sampling",
        [0.2, 48, 120],
    )
    forged = dict(independent)
    forged[("H3_SB1_FROZEN", 0.30)] = 1.0
    assert forged != independent
    assert independent[("H3_SB1_FROZEN", 0.30)] == 0.991


def test_review_design_only_gate_preserved() -> None:
    scope = PROTOCOL["scope"]
    assert scope["synthetic_status"] == (
        "DESIGN_ONLY_NOT_EXPERIMENTAL_EVIDENCE"
    )
    assert scope["formal_v3_physics"] == "NOT_STARTED"
    assert scope["production_gate_eligible"] is False
    assert scope["trusted_registry_eligible"] is False
    assert scope["v3_physics_start_gate"] == (
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )
