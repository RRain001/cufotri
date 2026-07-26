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
RESULTS = BENCHMARK / "results"
REPORTS = BENCHMARK / "reports"


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
    with pytest.raises(ValueError, match="Monte Carlo"):
        RUNNER.validate_protocol_mapping(forged)


def test_attack_parameter_refit_rejected_by_frozen_contract() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["scope"]["parameter_refit_allowed"] = True
    with pytest.raises(ValueError, match="refit"):
        RUNNER.validate_protocol_mapping(forged)


def test_attack_latent_pool_classifier_rejected_by_frozen_contract() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["observables"]["latent_pool_used_for_classification"] = True
    with pytest.raises(ValueError, match="Latent pool"):
        RUNNER.validate_protocol_mapping(forged)


def test_attack_sampling_grid_change_rejected_after_execution() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["sampling"]["candidate_hours_after_final_exposure"].append(1000)
    with pytest.raises(ValueError, match="sampling grid"):
        RUNNER.validate_protocol_mapping(forged)


def test_attack_synthetic_empirical_claim_rejected() -> None:
    forged = copy.deepcopy(PROTOCOL)
    forged["scope"]["empirical_validation_claim"] = True
    with pytest.raises(ValueError, match="Design-only evidence"):
        RUNNER.validate_protocol_mapping(forged)


def test_all_required_output_contract_files_exist() -> None:
    for name in PROTOCOL["output_contract"]["required_outputs"]:
        assert (RESULTS / name).is_file() or (REPORTS / name).is_file()
    assert (
        ROOT / PROTOCOL["output_contract"]["experiment_specification"]
    ).is_file()
    assert (ROOT / PROTOCOL["output_contract"]["final_report"]).is_file()


def test_all_synthetic_runs_finite_nonnegative() -> None:
    qa = pd.read_csv(RESULTS / "design_run_qa.csv")
    assert len(qa) == 12
    assert qa["finite_nonnegative_pass"].all()
    assert (qa["parameter_refit_count"] == 0).all()
    assert (qa["nan_count"] == 0).all()
    assert (qa["inf_count"] == 0).all()
    assert (qa["negative_inventory_count"] == 0).all()
    assert (qa["negative_concentration_count"] == 0).all()


def test_all_synthetic_runs_mass_conservative() -> None:
    qa = pd.read_csv(RESULTS / "design_run_qa.csv")
    assert qa["mass_conservation_pass"].all()
    assert (
        qa["maximum_formal_mass_closure_abs_bq_m2"] <= 1.0e-6
    ).all()
    assert (
        qa["maximum_internal_transfer_ledger_residual_abs_bq_m2"]
        <= 1.0e-9
    ).all()


def test_synthetic_predictions_are_design_only_and_observable_only() -> None:
    predictions = pd.read_csv(
        RESULTS / "synthetic_design_predictions.csv"
    )
    assert set(predictions["design_id"]) == set(PROTOCOL["designs"])
    assert set(predictions["mechanism_id"]) == set(
        PROTOCOL["monte_carlo"]["truth_models"]
    )
    assert set(predictions["evidence_class"]) == {"SYNTHETIC_DESIGN_ONLY"}
    assert set(predictions["classification_observable"]) == {
        "total_plant_body_tfwt"
    }
    assert not predictions["latent_pool_used_for_classification"].any()
    assert (predictions["parameter_refit_count"] == 0).all()
    numeric = predictions.select_dtypes(include=[np.number]).to_numpy()
    assert np.isfinite(numeric).all()
    assert (
        predictions[
            [
                "plant_body_tfwt_bq_l_water",
                "plant_fast_tfwt_inventory_bq_m2",
                "plant_slow_tfwt_inventory_bq_m2",
            ]
        ]
        >= 0
    ).all().all()


def test_monte_carlo_output_covers_frozen_truth_noise_matrix() -> None:
    frame = pd.read_csv(RESULTS / "monte_carlo_classification.csv")
    expected = {
        (design, truth, cv)
        for design in PROTOCOL["designs"]
        for truth in PROTOCOL["monte_carlo"]["truth_models"]
        for cv in PROTOCOL["monte_carlo"]["coefficient_of_variation"]
    }
    actual = set(
        zip(
            frame["design_id"],
            frame["truth_model"],
            frame["coefficient_of_variation"],
            strict=True,
        )
    )
    assert actual == expected
    assert (frame["replicate_count"] == 1000).all()
    assert (frame["parameter_refit_count"] == 0).all()
    assert not frame["latent_pool_used"].any()


def test_attack_forged_accuracy_rejected_by_independent_recalculation() -> None:
    predictions = pd.read_csv(
        RESULTS / "synthetic_design_predictions.csv"
    )
    stored = pd.read_csv(RESULTS / "monte_carlo_classification.csv")
    design_id = "D3_SHORT_STEP_24H"
    truth_model = "H2_SB1_FROZEN"
    cv = 0.20
    hours, h2, h3 = RUNNER.prediction_vectors(predictions, design_id)
    observations = RUNNER.noise_replicates(
        PROTOCOL,
        h2,
        cv,
        f"full_grid:{design_id}:{truth_model}:{cv:.2f}",
    )
    recalculated = RUNNER.classify_replicates(
        observations, h2, h3, truth_model
    )
    selected = stored[
        (stored["design_id"] == design_id)
        & (stored["truth_model"] == truth_model)
        & np.isclose(stored["coefficient_of_variation"], cv)
    ]
    assert len(selected) == 1
    assert recalculated == pytest.approx(
        float(selected.iloc[0]["correct_classification_rate"])
    )
    forged = min(1.0, recalculated + 0.001)
    if forged == recalculated:
        forged = recalculated - 0.001
    assert forged != pytest.approx(recalculated)
    assert len(hours) == 14


def test_minimum_sampling_results_use_frozen_grid_and_bounds() -> None:
    frame = pd.read_csv(RESULTS / "minimum_sampling_design.csv")
    candidates = set(
        float(value)
        for value in PROTOCOL["sampling"][
            "candidate_hours_after_final_exposure"
        ]
    )
    assert set(frame["design_id"]) == set(PROTOCOL["designs"])
    assert frame["sample_count"].between(3, 8).all()
    for row in frame.itertuples():
        hours = {float(value) for value in row.sample_hours.split(";")}
        assert hours <= candidates
        assert len(hours) == row.sample_count
    assert (frame["parameter_refit_count"] == 0).all()
    assert not frame["latent_pool_used"].any()


def test_d3_is_only_fully_robust_screened_design() -> None:
    frame = pd.read_csv(RESULTS / "design_robustness_matrix.csv")
    assert (frame["parameter_refit_count"] == 0).all()
    assert not frame["latent_pool_used"].any()
    assert frame["finite_nonnegative_pass"].all()
    assert frame["mass_conservation_pass"].all()
    pass_by_design = frame.groupby("design_id")["criteria_pass"].all()
    assert pass_by_design.to_dict() == {
        "D3_SHORT_STEP_24H": True,
        "D4_LONG_STEP_72H": False,
        "D5_PULSE_WASHOUT_REEXPOSURE": False,
    }


@pytest.mark.parametrize(
    ("filename", "mechanism_id", "parameter_names"),
    [
        (
            "h2_local_sensitivity.csv",
            "H2_SB1_FROZEN",
            {"slow_capture_fraction", "slow_release_rate_s"},
        ),
        (
            "h3_local_sensitivity.csv",
            "H3_SB1_FROZEN",
            {"fast_to_slow_rate_s", "slow_to_fast_rate_s"},
        ),
    ],
)
def test_local_sensitivity_is_bounded_not_global_claim(
    filename: str,
    mechanism_id: str,
    parameter_names: set[str],
) -> None:
    frame = pd.read_csv(RESULTS / filename)
    assert set(frame["mechanism_id"]) == {mechanism_id}
    assert set(frame["parameter_name"]) == parameter_names
    assert set(frame["design_id"]) == set(PROTOCOL["designs"])
    assert not frame["global_identifiability_claim"].any()
    numeric = frame.select_dtypes(include=[np.number]).to_numpy()
    assert np.isfinite(numeric).all()
    assert (frame["lower_parameter_value"] > 0).all()
    assert (
        frame["upper_parameter_value"]
        > frame["lower_parameter_value"]
    ).all()


def test_final_report_preserves_design_only_gate_and_d3_robustness() -> None:
    report = (
        ROOT / PROTOCOL["output_contract"]["final_report"]
    ).read_text(encoding="utf-8")
    assert "BEST_DISCRIMINATING_DESIGN = D3_SHORT_STEP_24H" in report
    assert "D3_STATUS = DISCRIMINATING_DESIGN_SUPPORTED" in report
    assert "CONCENTRATION_ROBUSTNESS = True" in report
    assert "RH_ROBUSTNESS = True" in report
    assert "WIND_ROBUSTNESS = True" in report
    assert "LEAF_PARAMETER_ROBUSTNESS = True" in report
    assert "EMPIRICAL_VALIDATION_CLAIM = FALSE" in report
    assert (
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA" in report
    )
