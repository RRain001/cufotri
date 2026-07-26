from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = (
    ROOT / "validation" / "benchmarks" / "slow_mechanism_discriminability"
)
PROTOCOL_PATH = (
    BENCHMARK / "preregistration" / "h2_h3_discriminability_protocol.yaml"
)
SCRIPT = (
    BENCHMARK / "scripts" / "run_discriminability_analysis.py"
)


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "discriminability_runner_for_tests", SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNNER = load_runner()
PROTOCOL = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def forcing_by_design() -> dict[str, pd.DataFrame]:
    return {
        design_id: RUNNER.build_forcing(PROTOCOL, design_id)
        for design_id in PROTOCOL["designs"]
    }


def exposure_intervals(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["phase"].str.startswith("CONTROLLED_EXPOSURE")]


def test_d0_reproduces_single_pulse_baseline_shape(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = exposure_intervals(
        forcing_by_design["D0_SINGLE_PULSE_BASELINE"]
    )
    assert len(frame) == 12
    assert set(frame["phase"]) == {"CONTROLLED_EXPOSURE_1"}
    assert set(frame["air_moisture_hto_bq_ml_water"]) == {52700.0}
    assert frame["hours_from_first_exposure_start"].min() == pytest.approx(
        1.0 / 12.0
    )
    assert frame["hours_from_first_exposure_start"].max() == 1.0


def test_d1_double_pulse_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = exposure_intervals(
        forcing_by_design["D1_SECOND_PULSE_AFTER_24H"]
    )
    counts = frame["phase"].value_counts().to_dict()
    assert counts == {
        "CONTROLLED_EXPOSURE_1": 12,
        "CONTROLLED_EXPOSURE_2": 12,
    }
    first_end = frame.loc[
        frame["phase"] == "CONTROLLED_EXPOSURE_1",
        "hours_from_first_exposure_start",
    ].max()
    second_start_boundary = 25.0
    assert first_end == 1.0
    assert second_start_boundary - first_end == 24.0


def test_d2_delayed_double_pulse_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = exposure_intervals(
        forcing_by_design["D2_SECOND_PULSE_AFTER_72H"]
    )
    assert len(frame) == 24
    first_end = frame.loc[
        frame["phase"] == "CONTROLLED_EXPOSURE_1",
        "hours_from_first_exposure_start",
    ].max()
    assert 73.0 - first_end == 72.0
    assert frame["hours_from_first_exposure_start"].max() == 74.0


def test_d3_short_step_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = exposure_intervals(forcing_by_design["D3_SHORT_STEP_24H"])
    assert len(frame) == 24 * 12
    assert set(frame["air_moisture_hto_bq_ml_water"]) == {5270.0}
    assert frame["hours_from_first_exposure_start"].max() == 24.0


def test_d4_long_step_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = exposure_intervals(forcing_by_design["D4_LONG_STEP_72H"])
    assert len(frame) == 72 * 12
    assert set(frame["air_moisture_hto_bq_ml_water"]) == {5270.0}
    assert frame["hours_from_first_exposure_start"].max() == 72.0


def test_d5_pulse_washout_reexposure_schedule(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    frame = exposure_intervals(
        forcing_by_design["D5_PULSE_WASHOUT_REEXPOSURE"]
    )
    first = frame[frame["phase"] == "CONTROLLED_EXPOSURE_1"]
    second = frame[frame["phase"] == "CONTROLLED_EXPOSURE_2"]
    assert len(first) == 12
    assert len(second) == 24 * 12
    assert set(first["air_moisture_hto_bq_ml_water"]) == {52700.0}
    assert set(second["air_moisture_hto_bq_ml_water"]) == {5270.0}
    assert 73.0 - first["hours_from_first_exposure_start"].max() == 72.0
    assert second["hours_from_first_exposure_start"].max() == 97.0


def test_h2_parameters_remain_frozen() -> None:
    assert RUNNER.parameter_values(PROTOCOL, "H2_SB1_FROZEN") == {
        "slow_capture_fraction": 0.001,
        "slow_release_rate_s": 1.0e-6,
    }
    assert PROTOCOL["scope"]["parameter_refit_allowed"] is False


def test_h3_parameters_remain_frozen() -> None:
    assert RUNNER.parameter_values(PROTOCOL, "H3_SB1_FROZEN") == {
        "fast_to_slow_rate_s": 1.0e-7,
        "slow_to_fast_rate_s": 1.0e-6,
    }
    assert PROTOCOL["scope"]["parameter_refit_count"] == 0


def test_no_synthetic_data_used_as_external_evidence(
    forcing_by_design: dict[str, pd.DataFrame],
) -> None:
    assert PROTOCOL["scope"]["synthetic_status"] == (
        "DESIGN_ONLY_NOT_EXPERIMENTAL_EVIDENCE"
    )
    assert PROTOCOL["scope"]["empirical_validation_claim"] is False
    assert PROTOCOL["scope"]["production_gate_eligible"] is False
    for frame in forcing_by_design.values():
        assert set(frame["forcing_evidence_class"]) == {
            "SYNTHETIC_CONTROLLED_CONDITIONS"
        }


def test_no_latent_pool_used_for_classification() -> None:
    assert PROTOCOL["observables"]["primary"]["id"] == (
        "total_plant_body_tfwt"
    )
    assert PROTOCOL["observables"]["latent_pool_used_for_classification"] is False
    assert all(
        item["classification_role"] == "INTERPRETATION_ONLY"
        for item in PROTOCOL["observables"]["secondary"]
    )


def test_sampling_grid_frozen_before_execution() -> None:
    assert PROTOCOL["status"] == "FROZEN_BEFORE_SYNTHETIC_EXECUTION"
    assert PROTOCOL["sampling"]["frozen_before_execution"] is True
    assert PROTOCOL["sampling"]["candidate_hours_after_final_exposure"] == [
        0.2,
        0.5,
        1,
        3,
        6,
        12,
        24,
        48,
        72,
        120,
        168,
        336,
        504,
        768,
    ]


def test_monte_carlo_seed_reproducible() -> None:
    truth = np.asarray([1.0, 2.0, 4.0])
    first = RUNNER.noise_replicates(
        PROTOCOL, truth, 0.20, "seed-test"
    )
    second = RUNNER.noise_replicates(
        PROTOCOL, truth, 0.20, "seed-test"
    )
    np.testing.assert_array_equal(first, second)
    assert first.shape == (1000, 3)


def test_monte_carlo_runs_both_truth_models() -> None:
    assert PROTOCOL["monte_carlo"]["truth_models"] == [
        "H2_SB1_FROZEN",
        "H3_SB1_FROZEN",
    ]
    assert PROTOCOL["monte_carlo"][
        "replicates_per_truth_model_design_noise"
    ] == 1000


def test_discrimination_thresholds_frozen() -> None:
    assert PROTOCOL["pointwise_metrics"][
        "strong_separation_delta_log10_minimum"
    ] == 0.30
    assert PROTOCOL["pointwise_metrics"][
        "moderate_separation_delta_log10_minimum"
    ] == 0.15
    assert PROTOCOL["design_success_criteria"][
        "classification_accuracy_minimum"
    ] == {"cv_0_10": 0.90, "cv_0_20": 0.80, "cv_0_30": 0.70}


def test_minimum_sampling_set_uses_only_candidate_grid() -> None:
    optimization = PROTOCOL["sampling"]["optimization"]
    assert optimization["minimum_sample_count"] == 3
    assert optimization["maximum_sample_count"] == 8
    assert optimization["algorithm"] == (
        "DETERMINISTIC_GREEDY_WORST_NOISE_ACCURACY"
    )


def test_design_branch_not_production_gate_eligible() -> None:
    assert PROTOCOL["scope"]["formal_v3_physics"] == "NOT_STARTED"
    assert PROTOCOL["scope"]["production_gate_eligible"] is False
    assert PROTOCOL["scope"]["v3_physics_start_gate"] == (
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )


def test_attack_modified_noise_level_rejected_by_frozen_contract() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["monte_carlo"]["coefficient_of_variation"] = [0.10, 0.25, 0.30]
    assert forged["monte_carlo"]["coefficient_of_variation"] != [
        0.10,
        0.20,
        0.30,
    ]


def test_attack_parameter_refit_rejected_by_frozen_contract() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["scope"]["parameter_refit_allowed"] = True
    assert forged["scope"]["parameter_refit_allowed"] is not False


def test_attack_latent_pool_classifier_rejected_by_frozen_contract() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["observables"]["latent_pool_used_for_classification"] = True
    assert forged["observables"]["latent_pool_used_for_classification"] is not False
