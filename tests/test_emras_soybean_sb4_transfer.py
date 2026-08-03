from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
import yaml

from validation.external_input_requirements import dataset_root


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = (
    ROOT / "validation" / "benchmarks" / "emras_soybean_sb4"
)
TABLES = BENCHMARK / "published_tables"
REPORTS = BENCHMARK / "reports"
LOCAL = dataset_root(ROOT, "SB4")
GENERATED = LOCAL / "generated_forcing"
PROTOCOL = yaml.safe_load(
    (
        BENCHMARK
        / "preregistration"
        / "sb4_transfer_protocol.yaml"
    ).read_text(encoding="utf-8")
)
SELECTION = json.loads(
    (REPORTS / "sb4_transfer_selection.json").read_text(encoding="utf-8")
)
PROFILE_IDS = {
    "CONSTANT_REPORTED_MEAN",
    "SCALED_SB1_OBSERVED_SHAPE",
}
MECHANISM_IDS = {
    "H0_CURRENT_SINGLE_POOL",
    "H2_SB1_FROZEN",
    "H3_SB1_FROZEN",
}


def load_transfer_runner():
    path = BENCHMARK / "scripts" / "run_sb4_transfer_test.py"
    spec = importlib.util.spec_from_file_location(
        "sb4_transfer_runner_for_tests", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def independent_log_metrics(frame: pd.DataFrame) -> dict[str, float]:
    observed = frame["observed_bq_l_water"].to_numpy(float)
    predicted = frame["predicted_bq_l_water"].to_numpy(float)
    assert np.isfinite(observed).all()
    assert np.isfinite(predicted).all()
    assert (observed > 0).all()
    assert (predicted > 0).all()
    residual = np.log10(predicted) - np.log10(observed)
    ratio = predicted / observed
    absolute = np.abs(residual)
    return {
        "log10_rmse": float(np.sqrt(np.mean(residual**2))),
        "log10_mean_bias": float(np.mean(residual)),
        "median_predicted_to_observed_ratio": float(np.median(ratio)),
        "factor_2_coverage": float(
            np.mean(absolute <= math.log10(2.0))
        ),
        "factor_10_coverage": float(np.mean(absolute <= 1.0)),
    }


def independent_forcing_pass_count(
    mechanism_id: str, profile_id: str
) -> int:
    predictions = pd.read_csv(REPORTS / "sb4_transfer_predictions.csv")
    mass = pd.read_csv(REPORTS / "sb4_transfer_mass_balance.csv")
    criteria = PROTOCOL["support_criteria"]
    count = 0
    for run_id in sorted(predictions["run_id"].unique()):
        subset = predictions[
            (predictions["profile_id"] == profile_id)
            & (predictions["run_id"] == run_id)
            & (predictions["compartment"] == "plant_body")
        ]
        reference = subset[
            subset["mechanism_id"] == "H0_CURRENT_SINGLE_POOL"
        ]
        candidate = subset[subset["mechanism_id"] == mechanism_id]
        reference_overall = independent_log_metrics(reference)
        candidate_overall = independent_log_metrics(candidate)
        reference_late = independent_log_metrics(
            reference[
                reference["hours_after_exposure"].isin([768.0, 1368.0])
            ]
        )
        candidate_late = independent_log_metrics(
            candidate[
                candidate["hours_after_exposure"].isin([768.0, 1368.0])
            ]
        )
        reference_early = reference[
            reference["hours_after_exposure"].isin([0.2, 1.0])
        ]
        candidate_early = candidate[
            candidate["hours_after_exposure"].isin([0.2, 1.0])
        ]
        ratio = (
            candidate_early["predicted_bq_l_water"].to_numpy(float)
            / candidate_early["observed_bq_l_water"].to_numpy(float)
        )
        factor_pass = bool(
            (
                (ratio >= 1.0 / criteria["early_prediction_factor_limit"])
                & (ratio <= criteria["early_prediction_factor_limit"])
            ).all()
        )
        candidate_error = np.abs(
            np.log10(
                candidate_early["predicted_bq_l_water"].to_numpy(float)
            )
            - np.log10(
                candidate_early["observed_bq_l_water"].to_numpy(float)
            )
        )
        reference_error = np.abs(
            np.log10(
                reference_early["predicted_bq_l_water"].to_numpy(float)
            )
            - np.log10(
                reference_early["observed_bq_l_water"].to_numpy(float)
            )
        )
        early_pass = bool(
            factor_pass
            or np.max(candidate_error - reference_error)
            <= criteria["early_log10_error_worsening_maximum_dex"]
        )
        mass_pass = bool(
            mass[
                (mass["mechanism_id"] == mechanism_id)
                & (mass["profile_id"] == profile_id)
                & (mass["run_id"] == run_id)
            ]["mass_balance_pass"].iloc[0]
        )
        count += int(
            reference_overall["log10_rmse"]
            - candidate_overall["log10_rmse"]
            >= criteria["overall_log10_rmse_improvement_minimum_dex"]
            and reference_late["log10_rmse"]
            - candidate_late["log10_rmse"]
            >= criteria["late_log10_rmse_improvement_minimum_dex"]
            and early_pass
            and mass_pass
        )
    return count


def test_sb4_pdf_tfwt_values() -> None:
    tfwt = pd.read_csv(TABLES / "sb4_tfwt_observations.csv")
    body = tfwt[tfwt["compartment"] == "plant_body"]
    pods = tfwt[tfwt["compartment"] == "pods"]
    np.testing.assert_array_equal(
        body["tfwt_bq_ml_water"],
        [7000, 3200, 25.9, 2.1, 0.8, 0.27, 0.14],
    )
    np.testing.assert_array_equal(
        pods["tfwt_bq_ml_water"],
        [10500, 8000, 2700, 63.5, 1.49, 0.84, 0.26],
    )
    inventory = yaml.safe_load(
        (BENCHMARK / "source_inventory.yaml").read_text(encoding="utf-8")
    )
    assert inventory["tables"]["tfwt"] == "Table 5.2"
    assert inventory["source_document"]["reviewed_pdf_pages"] == [
        105,
        287,
        290,
    ]


def test_sb4_pdf_obt_values() -> None:
    obt = pd.read_csv(TABLES / "sb4_obt_harvest.csv").set_index(
        "compartment"
    )
    expected = {
        "stem": 19.8,
        "leaves": 8.8,
        "plant_body_average": 14.3,
        "shell": 74.7,
        "seeds": 200.0,
        "pods_average": 137.4,
    }
    assert obt["obt_bq_ml_combustion_water"].to_dict() == expected


def test_sb4_sampling_schedule() -> None:
    schedule = pd.read_csv(TABLES / "sb4_sampling_schedule.csv")
    assert len(schedule) == 14
    for _, group in schedule.groupby("compartment"):
        np.testing.assert_array_equal(
            group["hours_after_exposure"],
            [0.2, 1, 24, 120, 336, 768, 1368],
        )


@pytest.mark.external_sb4_data
def test_sb4_constant_profile_mean() -> None:
    profiles = pd.read_csv(GENERATED / "sb4_chamber_profiles.csv")
    constant = profiles[
        profiles["profile_id"] == "CONSTANT_REPORTED_MEAN"
    ]
    mean = np.trapezoid(
        constant["air_moisture_hto_bq_ml_water"],
        constant["minutes_from_exposure_start"],
    ) / 60.0
    assert math.isclose(mean, 52700.0, abs_tol=1.0e-9)


@pytest.mark.external_sb4_data
def test_sb4_scaled_sb1_profile_mean() -> None:
    profiles = pd.read_csv(GENERATED / "sb4_chamber_profiles.csv")
    scaled = profiles[
        profiles["profile_id"] == "SCALED_SB1_OBSERVED_SHAPE"
    ]
    mean = np.trapezoid(
        scaled["air_moisture_hto_bq_ml_water"],
        scaled["minutes_from_exposure_start"],
    ) / 60.0
    assert math.isclose(mean, 52700.0, abs_tol=1.0e-9)
    assert scaled.iloc[0]["air_moisture_hto_bq_ml_water"] == 0.0


@pytest.mark.external_sb4_data
def test_sb4_profile_marked_reconstructed() -> None:
    profiles = pd.read_csv(GENERATED / "sb4_chamber_profiles.csv")
    assert set(profiles["profile_evidence_class"]) == {"RECONSTRUCTED"}
    assert not profiles["sb4_observed_curve_claim"].astype(bool).any()


@pytest.mark.external_sb4_data
def test_sb4_era5_time_coverage() -> None:
    manifest = json.loads(
        (GENERATED / "sb4_forcing_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["era5_raw_reuse_case"] == (
        "EMRAS_SOYBEAN_SB1_PDF_ERA5_V1"
    )
    assert len(manifest["era5_raw_checksums"]) == 5
    for item in manifest["scenarios"].values():
        frame = pd.read_csv(GENERATED / Path(item["path"]).name, usecols=["time_utc"])
        time = pd.to_datetime(frame["time_utc"], utc=True)
        assert time.iloc[0] == pd.Timestamp("2001-08-09T00:25:00Z")
        assert time.iloc[-1] == pd.Timestamp("2001-10-05T14:00:00Z")
        assert len(frame) == 16580


def test_sb4_uses_sb1_frozen_h2_parameters() -> None:
    declared = PROTOCOL["mechanisms"]["H2_SB1_FROZEN"]
    assert declared["parameters"] == {
        "slow_capture_fraction": 0.001,
        "slow_release_rate_s": 1.0e-6,
    }
    assert declared["selected_from_sb4"] is False


def test_sb4_uses_sb1_frozen_h3_parameters() -> None:
    declared = PROTOCOL["mechanisms"]["H3_SB1_FROZEN"]
    assert declared["parameters"] == {
        "fast_to_slow_rate_s": 1.0e-7,
        "slow_to_fast_rate_s": 1.0e-6,
    }
    assert declared["selected_from_sb4"] is False


def test_sb4_no_parameter_refit() -> None:
    predictions = pd.read_csv(REPORTS / "sb4_transfer_predictions.csv")
    assert PROTOCOL["no_sb4_parameter_refit"] is True
    assert PROTOCOL["sb4_parameter_refit_count"] == 0
    assert set(predictions["sb4_parameter_refit_count"]) == {0}
    assert not predictions["selected_from_sb4"].astype(bool).any()


def test_sb4_runs_42_scenarios() -> None:
    mass = pd.read_csv(REPORTS / "sb4_transfer_mass_balance.csv")
    assert len(mass) == 42
    assert set(mass["mechanism_id"]) == MECHANISM_IDS
    assert set(mass["profile_id"]) == PROFILE_IDS
    assert mass[["mechanism_id", "profile_id", "run_id"]].duplicated().sum() == 0


def test_sb4_plant_body_metrics() -> None:
    predictions = pd.read_csv(REPORTS / "sb4_transfer_predictions.csv")
    metrics = pd.read_csv(REPORTS / "sb4_transfer_metrics.csv")
    for keys, frame in predictions[
        predictions["compartment"] == "plant_body"
    ].groupby(["mechanism_id", "profile_id", "run_id"]):
        independently_recomputed = independent_log_metrics(frame)
        stored = metrics[
            (metrics["mechanism_id"] == keys[0])
            & (metrics["profile_id"] == keys[1])
            & (metrics["run_id"] == keys[2])
            & (metrics["compartment"] == "plant_body")
            & (metrics["partition"] == "overall")
        ].iloc[0]
        for metric, value in independently_recomputed.items():
            assert math.isclose(stored[metric], value, abs_tol=1.0e-12)


def test_sb4_pods_not_used_for_selection() -> None:
    pods = PROTOCOL["observations"]["pods"]
    assert pods["used_for_parameter_selection"] is False
    assert pods["positive_selection_evidence"] is False
    assert pods["provisional_mapping"] is True


def test_sb4_obt_not_used_for_selection() -> None:
    obt = PROTOCOL["observations"]["obt"]
    assert obt["role"] == "CONSISTENCY_CHECK_ONLY"
    assert obt["used_for_parameter_selection"] is False
    assert obt["positive_selection_evidence"] is False


def test_sb4_transfer_thresholds_frozen() -> None:
    criteria = PROTOCOL["support_criteria"]
    assert criteria == {
        "overall_log10_rmse_improvement_minimum_dex": 0.50,
        "late_log10_rmse_improvement_minimum_dex": 0.50,
        "early_prediction_factor_limit": 3.0,
        "early_log10_error_worsening_maximum_dex": 0.25,
        "both_chamber_profiles_required": True,
        "forcing_scenarios_required_per_profile": 5,
        "require_finite_nonnegative": True,
        "mass_closure_absolute_tolerance_bq_m2": 1.0e-6,
        "internal_transfer_absolute_tolerance_bq_m2": 1.0e-9,
        "pods_log10_rmse_worsening_maximum_dex": 0.50,
        "obt_absolute_log10_error_worsening_maximum_dex": 0.50,
    }


def test_sb4_mass_balance() -> None:
    mass = pd.read_csv(REPORTS / "sb4_transfer_mass_balance.csv")
    assert mass["mass_balance_pass"].astype(bool).all()
    assert mass["maximum_formal_mass_closure_abs_bq_m2"].max() <= 1.0e-6
    assert (
        mass["maximum_internal_transfer_residual_abs_bq_m2"].max()
        <= 1.0e-9
    )


def test_sb4_finite_nonnegative() -> None:
    predictions = pd.read_csv(REPORTS / "sb4_transfer_predictions.csv")
    mass = pd.read_csv(REPORTS / "sb4_transfer_mass_balance.csv")
    numeric = predictions.select_dtypes(include=[np.number]).to_numpy()
    assert np.isfinite(numeric).all()
    assert (predictions["predicted_bq_l_water"] >= 0).all()
    assert mass["nan_count"].sum() == 0
    assert mass["inf_count"].sum() == 0
    assert mass["negative_inventory_count"].sum() == 0
    assert mass["negative_concentration_count"].sum() == 0


def test_sb4_not_production_gate_eligible() -> None:
    manifest = json.loads(
        (BENCHMARK / "sb4_case_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["production_gate_eligible"] is False
    assert SELECTION["production_gate_eligible"] is False
    assert SELECTION["empirical_validation_claim"] is False
    assert SELECTION["formal_v3_physics"] == "NOT_STARTED"
    assert SELECTION["v3_physics_start_gate"] == (
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )


def test_sb4_independent_selection_recomputed() -> None:
    for mechanism_id in ("H2_SB1_FROZEN", "H3_SB1_FROZEN"):
        for profile_id in PROFILE_IDS:
            count = independent_forcing_pass_count(
                mechanism_id, profile_id
            )
            assert count == 7
            stored = SELECTION["candidate_results"][mechanism_id][
                "profiles"
            ][profile_id]
            assert stored["forcing_pass_count"] == count
            assert stored["profile_supported"] is True
        assert SELECTION["candidate_results"][mechanism_id]["supported"] is True
    assert SELECTION["sb4_transfer_status"] == (
        "MULTIPLE_SLOW_MECHANISMS_TRANSFER_SUPPORTED"
    )


def test_sb4_internal_roundoff_is_disclosed_separately() -> None:
    mass = pd.read_csv(REPORTS / "sb4_transfer_mass_balance.csv")
    assert (
        mass["maximum_internal_state_sum_roundoff_abs_bq_m2"].max()
        > 1.0e-9
    )
    assert (
        mass["maximum_internal_transfer_residual_abs_bq_m2"].max()
        == 0.0
    )


def test_sb4_attack_modified_h2_parameter_fails() -> None:
    runner = load_transfer_runner()
    forged = copy.deepcopy(PROTOCOL)
    forged["mechanisms"]["H2_SB1_FROZEN"]["parameters"][
        "slow_capture_fraction"
    ] = 0.002
    with pytest.raises(
        ValueError, match="parameters differ from frozen values"
    ):
        runner.validate_parameter_contract(forged)


def test_sb4_attack_selected_from_sb4_fails() -> None:
    runner = load_transfer_runner()
    forged = copy.deepcopy(PROTOCOL)
    forged["mechanisms"]["H3_SB1_FROZEN"]["selected_from_sb4"] = True
    with pytest.raises(ValueError, match="selected from SB4"):
        runner.validate_parameter_contract(forged)


@pytest.mark.external_sb4_data
def test_sb4_attack_observed_profile_spoof_fails(
    tmp_path: Path,
) -> None:
    runner = load_transfer_runner()
    source = (
        GENERATED / "sb4_constant_reported_mean_run_01.csv"
    )
    forged = pd.read_csv(source)
    forged.loc[
        forged["phase"] == "CHAMBER_EXPOSURE",
        "chamber_profile_evidence_class",
    ] = "PUBLISHED_OBSERVATION"
    target = tmp_path / "forged_observed_profile.csv"
    forged.to_csv(target, index=False)
    with pytest.raises(ValueError, match="Observed-profile spoof"):
        runner.load_forcing(target)
