from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/check_ufotri_canada_1987_benchmark_reconstruction_r1.py"


def _load_gate_module():
    spec = importlib.util.spec_from_file_location("canada_1987_gate", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = _load_gate_module()


def test_recovered_release_and_deposition_inputs_are_frozen_with_exact_unit_conversions() -> None:
    result = GATE.build_result()
    recovered = result["recovered_static_inputs"]

    assert recovered["release"]["chemical_form"] == "HT"
    assert recovered["release"]["rate_bq_s"] == pytest.approx(1.9e9)
    assert recovered["release"]["duration_s"] == pytest.approx(1800.0)
    assert recovered["release"]["integrated_activity_bq"] == pytest.approx(3.42e12)
    assert recovered["release"]["height_m"] == pytest.approx(1.0)
    assert recovered["dispersion"]["pasquill_gifford_class"] == "B"
    assert recovered["dispersion"]["met_instrument_height_m"] == pytest.approx(2.75)
    assert recovered["deposition"]["ht_cm_s"] == pytest.approx(0.055)
    assert recovered["deposition"]["ht_m_s"] == pytest.approx(5.5e-4)
    assert recovered["deposition"]["reemitted_hto_cm_s"] == pytest.approx(0.5)
    assert recovered["deposition"]["reemitted_hto_m_s"] == pytest.approx(5.0e-3)
    assert all(result["conversion_gates"].values())


def test_recovered_soil_plant_and_reemission_inputs_preserve_manual_values() -> None:
    result = GATE.build_result()
    soil_plant = result["recovered_static_inputs"]["soil_plant"]
    reemission = result["recovered_static_inputs"]["reemission"]

    assert soil_plant["initial_soil_water_fraction"] == pytest.approx(0.20)
    assert soil_plant["plant_inorganic_water_g"] == pytest.approx(200.0)
    assert soil_plant["plant_organic_matter_g"] == pytest.approx(100.0)
    assert soil_plant["leaf_area_index_m2_m2"] == pytest.approx(3.0)
    assert soil_plant["day_leaf_diffusion_resistance_s_cm"] == pytest.approx(4.0)
    assert soil_plant["night_leaf_diffusion_resistance_s_cm"] == pytest.approx(60.0)
    assert soil_plant["day_leaf_diffusion_resistance_s_m"] == pytest.approx(400.0)
    assert soil_plant["night_leaf_diffusion_resistance_s_m"] == pytest.approx(6000.0)
    assert reemission["soil_day"] == "CALCULATED_EACH_HOUR_EXCEPT_RAIN"
    assert reemission["soil_night_start_percent"] == pytest.approx(1.0)
    assert reemission["soil_rain_start_percent"] == pytest.approx(3.0)
    assert reemission["night_and_rain_rates_decrease_with_time"] is True


def test_all_manual_observable_families_are_reconstructed_without_resolving_figure_28_ambiguity() -> None:
    result = GATE.build_result()
    observables = result["observable_contract"]

    assert [item["figure"] for item in observables] == list(range(21, 29))
    assert all(item.get("manual_caption_present") for item in observables)

    fig28 = observables[-1]
    assert fig28["distance_m"] is None
    assert fig28["distance_ambiguity_m"] == [175, 180]
    assert fig28["manual_text_175_m_present"] is True
    assert fig28["manual_caption_180_m_present"] is True
    assert result["figure_gates"]["figure_28_distance_ambiguity_preserved"] is True


def test_full_numeric_replay_fails_closed_on_explicit_missing_evidence() -> None:
    result = GATE.build_result()
    blocker_ids = {item["id"] for item in result["unresolved_blockers"]}

    assert {
        "CAN1987_REFERENCE_44_RAW_REPORT_AND_DATA",
        "CAN1987_RAW_HOURLY_MET_SERIES",
        "CAN1987_RELEASE_CLOCK_ALIGNMENT",
        "CAN1987_PRECIPITATION_EVENT_TIMING",
        "CAN1987_RAW_MEASURED_AND_CALCULATED_SERIES",
        "CAN1987_SIGMA_PARAMETER_NUMERIC_PROVENANCE",
        "CAN1987_COMPLETE_EQ44_REEMISSION_RATE_RECOVERY",
        "CAN1987_PRIMARY_ATMOS_NUMERICAL_EQUIVALENCE",
    } <= blocker_ids
    assert all(item["required_for_full_numeric_replay"] for item in result["unresolved_blockers"])

    policy = result["acceptance_policy"]
    assert policy["full_numeric_replay_ready"] is False
    assert policy["empirical_reproduction_executed"] is False
    assert policy["empirical_validation_complete"] is False
    assert policy["authoritative_pointwise_rmse_allowed"] is False
    assert policy["chart_transcription_as_ground_truth_allowed"] is False
    assert policy["silent_fill_of_missing_inputs_allowed"] is False


def test_current_repository_has_the_manual_compatible_ht_conversion_and_reemission_seams() -> None:
    result = GATE.build_result()
    assert all(result["repository_mapping"].values())
    assert result["decision"]["production_source_changed"] is False
    assert result["decision"]["default_parameters_changed"] is False
    assert result["decision"]["roadmap_changed_in_stage_pr"] is False
    assert result["decision"]["reference_44_values_invented"] is False
    assert result["decision"]["figure_28_distance_silently_resolved"] is False


def test_g1_machine_gate_passes_as_source_limited_reconstruction_not_empirical_validation() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (
        "G1_CANADA_1987_STATUS=PASS_SOURCE_LIMITED_CANADA_1987_BENCHMARK_RECONSTRUCTION"
        in completed.stdout
    )

    json_line = next(
        line for line in completed.stdout.splitlines() if line.startswith("G1_CANADA_1987_RESULT_JSON=")
    )
    payload = json.loads(json_line.split("=", 1)[1])
    assert payload["contract_gates"]
    assert all(payload["contract_gates"].values())
    assert payload["non_claims"]["canada_1987_empirical_reproduction"] is False
