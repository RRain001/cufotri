from __future__ import annotations

import copy
import csv
import importlib
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = (
    ROOT
    / "validation"
    / "benchmarks"
    / "d3_prospective_experiment"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

core = importlib.import_module("d3_prospective_core")
forcing = importlib.import_module("generate_d3_prospective_forcing")
generator = importlib.import_module("generate_d3_blinded_datasets")
classifier = importlib.import_module("run_d3_blinded_classification")
sensitivity = importlib.import_module("run_d3_replicate_sensitivity")

BENCHMARK = (
    ROOT / "validation" / "benchmarks" / "d3_prospective_experiment"
)
LOCAL = (
    ROOT / "validation" / "external_local" / "d3_prospective_experiment"
)
TRACKED = (
    ROOT
    / "validation"
    / "benchmarks"
    / "d3_prospective_experiment"
    / "blinded"
)
ASSUMPTIONS = yaml.safe_load(
    forcing.ASSUMPTIONS_PATH.read_text(encoding="utf-8")
)
PROTOCOL = yaml.safe_load(
    core.CLASSIFICATION_PROTOCOL_PATH.read_text(encoding="utf-8")
)
GENERATION = yaml.safe_load(
    (TRACKED / "generation_manifest.yaml").read_text(encoding="utf-8")
)
INTAKE = yaml.safe_load(
    (BENCHMARK / "results" / "data_intake_manifest.yaml").read_text(
        encoding="utf-8"
    )
)


def classification_results() -> dict[str, str]:
    path = (
        BENCHMARK / "results" / "d3_blinded_classification_results.csv"
    )
    with path.open(encoding="utf-8", newline="") as stream:
        return {
            row["dataset_blind_id"]: row["classification_result"]
            for row in csv.DictReader(stream)
        }


def baseline_rows(blind_id: str) -> list[dict[str, object]]:
    with (TRACKED / f"dataset_{blind_id}.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        return [dict(row) for row in csv.DictReader(stream)]


def frame_for_aggregation(rows: list[dict[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame["hours_after_exposure"] = frame[
        "hours_after_exposure"
    ].astype(float)
    frame["tfwt_bq_l_water"] = frame["tfwt_bq_l_water"].astype(float)
    frame["below_detection_limit"] = frame[
        "below_detection_limit"
    ].map(classifier.parse_bool)
    return frame


def write_protocol(path: Path, protocol: dict[str, object]) -> None:
    path.write_text(
        yaml.safe_dump(protocol, sort_keys=False), encoding="utf-8"
    )


def test_assumptions_marked_project_only() -> None:
    loaded = forcing.load_assumptions(require_committed=True)
    assert loaded["assumption_set"] == "D3_PROSPECTIVE_ASSUMPTIONS_V2"
    assert loaded["amendment"]["post_unblinding_design_amendment"] is True
    assert (
        loaded["numeric_assumption_status"]
        == "PROJECT_ASSUMPTION_NOT_LITERATURE_FACT"
    )
    assert not loaded["measurement_assumptions"][
        "instrument_capability_claim"
    ]


def test_synthetic_forcing_mean_within_one_percent() -> None:
    rows = forcing.generate_forcing(
        ASSUMPTIONS, strict_zero_background=False
    )
    values = np.asarray(
        [
            row["air_hto_bq_ml_water"]
            for row in rows
            if row["phase"] == "CONTROLLED_EXPOSURE"
        ],
        dtype=float,
    )
    assert abs(values.mean() - 5270.0) / 5270.0 <= 0.01
    assert values.std(ddof=0) / values.mean() == pytest.approx(0.05)


def test_synthetic_forcing_five_minute_complete() -> None:
    rows = forcing.generate_forcing(
        ASSUMPTIONS, strict_zero_background=False
    )
    minutes = np.asarray(
        [row["minutes_from_exposure_start"] for row in rows], dtype=int
    )
    assert len(rows) == 1729
    assert minutes[0] == 0
    assert minutes[-1] == 8640
    assert np.all(np.diff(minutes) == 5)


def test_background_hto_measured_not_silent_zero() -> None:
    measured = forcing.generate_forcing(
        ASSUMPTIONS, strict_zero_background=False
    )
    strict_zero = forcing.generate_forcing(
        ASSUMPTIONS, strict_zero_background=True
    )
    measured_background = [
        row["air_hto_bq_ml_water"]
        for row in measured
        if row["phase"] == "POST_EXPOSURE_BACKGROUND"
    ]
    zero_background = [
        row["air_hto_bq_ml_water"]
        for row in strict_zero
        if row["phase"] == "POST_EXPOSURE_BACKGROUND"
    ]
    measured_fraction = np.asarray(measured_background) / 5270.0
    assert min(measured_background) > 0
    assert measured_fraction.mean() == pytest.approx(0.0025)
    assert measured_fraction.max() <= 0.005
    assert set(zero_background) == {0.0}


def test_h2_truth_uses_frozen_parameters() -> None:
    assert PROTOCOL["model_contract"]["H2_SB1_FROZEN"]["parameters"] == {
        "slow_capture_fraction": 0.001,
        "slow_release_rate_s": 1.0e-6,
    }
    assert (
        PROTOCOL["source_contract"]["parameter_source_commit"]
        == "4b79f62741db4d4b51f4d608df33d2e13c499636"
    )


def test_h3_truth_uses_frozen_parameters() -> None:
    assert PROTOCOL["model_contract"]["H3_SB1_FROZEN"]["parameters"] == {
        "fast_to_slow_rate_s": 1.0e-7,
        "slow_to_fast_rate_s": 1.0e-6,
    }
    assert PROTOCOL["model_contract"]["parameter_refit_count"] == 0


def test_truth_key_not_git_tracked() -> None:
    tracked = subprocess.run(
        [
            "git",
            "ls-files",
            "validation/external_local/d3_prospective_experiment/truth",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert tracked == ""
    assert (TRACKED / "truth_key_sha256").read_text(
        encoding="utf-8"
    ).strip()


def test_tracked_blind_artifacts_are_outside_external_local() -> None:
    tracked_local = subprocess.run(
        ["git", "ls-files", "validation/external_local"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert set(tracked_local) <= {
        "validation/external_local/.gitignore",
        "validation/external_local/README.md",
    }
    assert {
        path.name
        for path in TRACKED.iterdir()
        if path.is_file()
    } == {
        "dataset_A.csv",
        "dataset_B.csv",
        "dataset_C.csv",
        "generation_manifest.yaml",
        "truth_key_sha256",
    }


def test_blinded_files_do_not_reveal_truth() -> None:
    forbidden = (
        "H2_SB1_FROZEN",
        "H3_SB1_FROZEN",
        "SYNTHETIC_OUT_OF_MODEL_CHALLENGE",
        "truth_kind",
    )
    for name in (
        "dataset_A.csv",
        "dataset_B.csv",
        "dataset_C.csv",
        "generation_manifest.yaml",
    ):
        text = (TRACKED / name).read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden)
    assert GENERATION["truth_mapping_disclosed"] is False


def test_classifier_uses_only_total_tfwt() -> None:
    observable = PROTOCOL["observable_contract"]
    assert observable["classifier_observable"] == "total plant-body TFWT"
    assert not observable["latent_state_allowed"]
    assert not observable["pods_allowed"]
    assert not observable["roots_allowed"]


def test_classifier_uses_only_primary_times() -> None:
    assert PROTOCOL["sampling_contract"]["classification_times_h"] == [
        0.2,
        48,
        120,
    ]
    assert not PROTOCOL["sampling_contract"][
        "diagnostic_times_allowed_for_classification"
    ]


def test_no_parameter_refit() -> None:
    assert PROTOCOL["model_contract"]["parameter_refit"] is False
    assert PROTOCOL["model_contract"]["parameter_refit_count"] == 0
    with (
        BENCHMARK / "results" / "d3_blinded_classification_results.csv"
    ).open(encoding="utf-8", newline="") as stream:
        assert {
            int(row["parameter_refit_count"]) for row in csv.DictReader(stream)
        } == {0}


def test_dataset_a_classifies_h2() -> None:
    assert classification_results()["A"] == "H2_SUPPORTED_OVER_H3"


def test_dataset_b_classifies_h3() -> None:
    assert classification_results()["B"] == "H3_SUPPORTED_OVER_H2"


def test_dataset_c_returns_inconclusive() -> None:
    assert classification_results()["C"] == "DATA_INCONCLUSIVE"


def test_detection_limit_flags_preserved() -> None:
    rows = generator.detection_limit_rows(baseline_rows("A"), 250.0)
    flagged = [row for row in rows if row["below_detection_limit"] is True]
    assert len(flagged) == 1
    assert flagged[0]["tfwt_bq_l_water"] == 200.0
    assert flagged[0]["tfwt_bq_l_water"] != 125.0


def test_missing_replicate_challenge() -> None:
    rows = generator.missing_replicate_rows(baseline_rows("A"))
    means, summary = classifier.aggregate_primary_times(
        frame_for_aggregation(rows), "A", PROTOCOL
    )
    assert means is not None
    at_48 = next(row for row in summary if row["hours_after_exposure"] == 48)
    assert at_48["uncensored_replicate_count"] == 4


def test_outlier_challenge() -> None:
    rows = generator.outlier_rows(baseline_rows("A"))
    means, summary = classifier.aggregate_primary_times(
        frame_for_aggregation(rows), "A", PROTOCOL
    )
    assert means is not None
    at_48 = next(row for row in summary if row["hours_after_exposure"] == 48)
    assert at_48["non_ok_quality_excluded_count"] == 1
    assert at_48["uncensored_replicate_count"] == 4


def test_replicate_noise_monte_carlo_reproducible() -> None:
    truth = np.asarray([2.0e6, 2.0e4, 2.4e4])
    first = sensitivity.simulated_means(
        truth, cv=0.20, replicates=5, experiments=1000, seed=2026072705
    )
    second = sensitivity.simulated_means(
        truth, cv=0.20, replicates=5, experiments=1000, seed=2026072705
    )
    np.testing.assert_array_equal(first, second)


def test_synthetic_data_not_registry_eligible() -> None:
    assert GENERATION["trusted_registry_eligible"] is False
    assert INTAKE["registry_eligible"] is False
    assert INTAKE["licence"] == "SYNTHETIC_INTERNAL_TEST_DATA"


def test_synthetic_data_not_production_eligible() -> None:
    assert GENERATION["production_eligible"] is False
    assert INTAKE["production_eligible"] is False


def test_v3_gate_remains_blocked() -> None:
    assert (
        PROTOCOL["evidence_boundary"]["v3_physics_start_gate"]
        == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )
    assert (
        INTAKE["v3_physics_start_gate"]
        == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )


def test_v2_amendment_preserves_parameters_thresholds_and_seeds() -> None:
    preregistration = BENCHMARK / "preregistration"
    v1_assumptions = yaml.safe_load(
        (
            preregistration / "d3_prospective_experiment_assumptions.yaml"
        ).read_text(encoding="utf-8")
    )
    v1_protocol = yaml.safe_load(
        (
            preregistration / "d3_blinded_classification_protocol.yaml"
        ).read_text(encoding="utf-8")
    )
    assert ASSUMPTIONS["amendment"]["original_v1_result_preserved"] is True
    assert ASSUMPTIONS["random_seeds"] == v1_assumptions["random_seeds"]
    assert PROTOCOL["model_contract"] == v1_protocol["model_contract"]
    assert PROTOCOL["classifier"] == v1_protocol["classifier"]
    archived = yaml.safe_load(
        (
            BENCHMARK
            / "results"
            / "archive"
            / "v1_unblinding_manifest.yaml"
        ).read_text(encoding="utf-8")
    )
    current = yaml.safe_load(
        (BENCHMARK / "results" / "unblinding_manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert archived["status"] == "FAIL_POSITIVE_CONTROL_CLASSIFICATION"
    assert current["status"] == "PASS_ALL_EXPECTATIONS"


def test_attack_synthetic_status_changed_to_real_fails(
    tmp_path: Path,
) -> None:
    rows = baseline_rows("A")
    rows[0]["synthetic_status"] = "REAL_EXPERIMENT"
    path = tmp_path / "dataset_A.csv"
    generator.write_rows(path, rows)
    with pytest.raises(ValueError, match="synthetic status"):
        classifier.load_blinded_dataset(path, "A")


def test_attack_truth_key_added_to_git_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    truth = tmp_path / "truth_key.yaml"
    truth.write_text("tracked: true\n", encoding="utf-8")
    truth_hash = tmp_path / "truth_key_sha256"
    truth_hash.write_text("0" * 64 + "\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "truth_key.yaml", "truth_key_sha256"],
        cwd=tmp_path,
        check=True,
    )
    monkeypatch.setattr(classifier, "ROOT", tmp_path)
    monkeypatch.setattr(classifier, "TRUTH_KEY_PATH", truth)
    monkeypatch.setattr(classifier, "TRUTH_KEY_HASH_PATH", truth_hash)
    with pytest.raises(ValueError, match="tracked"):
        classifier.assert_truth_key_not_tracked()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda protocol: protocol["observable_contract"].__setitem__(
                "latent_state_allowed", True
            ),
            "observable",
        ),
        (
            lambda protocol: protocol["model_contract"][
                "H2_SB1_FROZEN"
            ]["parameters"].__setitem__("slow_capture_fraction", 0.002),
            "parameters",
        ),
        (
            lambda protocol: protocol["sampling_contract"].__setitem__(
                "diagnostic_times_allowed_for_classification", True
            ),
            "Diagnostic",
        ),
        (
            lambda protocol: protocol["classifier"][
                "absolute_rmse_difference_inconclusive_dex"
            ].__setitem__("value", 0.0),
            "thresholds",
        ),
        (
            lambda protocol: protocol["evidence_boundary"].__setitem__(
                "trusted_registry_eligible", True
            ),
            "boundary",
        ),
        (
            lambda protocol: protocol["challenge_contract"].__setitem__(
                "expected_result", "H2_SUPPORTED_OVER_H3"
            ),
            "challenge",
        ),
    ],
)
def test_attack_protocol_mutations_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: object,
    message: str,
) -> None:
    attacked = copy.deepcopy(PROTOCOL)
    mutation(attacked)  # type: ignore[operator]
    path = tmp_path / "protocol.yaml"
    write_protocol(path, attacked)
    monkeypatch.setattr(core, "CLASSIFICATION_PROTOCOL_PATH", path)
    with pytest.raises(ValueError, match=message):
        core.load_classification_protocol()


def test_attack_detection_limit_written_as_instrument_fact_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attacked = copy.deepcopy(ASSUMPTIONS)
    attacked["measurement_assumptions"]["instrument_capability_claim"] = True
    path = tmp_path / "assumptions.yaml"
    path.write_text(
        yaml.safe_dump(attacked, sort_keys=False), encoding="utf-8"
    )
    monkeypatch.setattr(forcing, "ASSUMPTIONS_PATH", path)
    with pytest.raises(ValueError, match="instrument fact"):
        forcing.load_assumptions(require_committed=False)


def test_intake_snapshot_contract_is_read_only_and_ineligible() -> None:
    assert INTAKE["raw_snapshot_read_only"] is True
    assert all(item["read_only"] for item in INTAKE["files"])
    assert INTAKE["registry_eligible"] is False
    assert INTAKE["production_eligible"] is False
