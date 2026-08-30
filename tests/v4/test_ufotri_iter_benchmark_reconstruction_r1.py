from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/check_ufotri_iter_benchmark_reconstruction_r1.py"


def _load_gate_module():
    spec = importlib.util.spec_from_file_location("iter_benchmark_gate", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = _load_gate_module()


def test_table8_emission_meteorology_and_building_contract_is_frozen() -> None:
    result = GATE.build_result()
    inputs = result["benchmark_inputs"]

    assert inputs["emission"]["release_quantity_g"] == pytest.approx(100.0)
    assert inputs["emission"]["chemical_forms"] == ["HT", "HTO"]
    assert inputs["emission"]["duration_s"] == pytest.approx(120.0)
    assert inputs["emission"]["table8_release_heights_m"] == [0.0, 20.0, 60.0]
    assert inputs["emission"]["result_release_heights_m"] == [10.0, 20.0, 60.0]
    assert inputs["meteorology"]["D"] == {
        "wind_speed_at_60m_m_s": 5.0,
        "mixing_lid_m": 560.0,
        "wind_profile_exponent": 0.34,
    }
    assert inputs["meteorology"]["F"] == {
        "wind_speed_at_60m_m_s": 3.0,
        "mixing_lid_m": 200.0,
        "wind_profile_exponent": 0.44,
    }
    assert inputs["meteorology"]["rain"] == "NONE"
    assert inputs["meteorology"]["plume_rise"] == "NONE"
    assert inputs["building"]["wake_case_release_height_m"] == pytest.approx(20.0)
    assert inputs["building"]["width_m"] == pytest.approx(100.0)
    assert inputs["building"]["height_m"] == pytest.approx(70.0)


def test_code_soil_site_diet_and_mol_parameters_match_manual_contract() -> None:
    inputs = GATE.build_result()["benchmark_inputs"]
    coeff = inputs["coefficients"]

    assert coeff["dry_deposition_velocity_hto_cm_s"] == pytest.approx(1.8)
    assert coeff["dry_deposition_velocity_ht_cm_s"] == pytest.approx(0.05)
    assert coeff["soil_diffusion_hto_cm2_s"] == pytest.approx(2.0e-5)
    assert coeff["soil_diffusion_ht_cm2_s"] == pytest.approx(5.0e-2)
    assert coeff["soil_hto_reemission_percent_per_h"] == pytest.approx(5.0)
    assert coeff["air_oxidation_percent_per_d"] == pytest.approx(0.5)
    assert coeff["breathing_rate_m3_s"] == pytest.approx(2.66e-4)
    assert coeff["dose_conversion_7d_inhalation_sv_bq"] == pytest.approx(6.3e-12)
    assert coeff["dose_conversion_50a_inhalation_ingestion_sv_bq"] == pytest.approx(1.7e-11)

    assert inputs["soil_vegetation"]["soil_type"] == "SANDY_LOAM"
    assert inputs["soil_vegetation"]["pore_volume_fraction"] == pytest.approx(0.50)
    assert inputs["soil_vegetation"]["pore_water_fraction"] == pytest.approx(0.40)
    assert inputs["soil_vegetation"]["pore_air_fraction"] == pytest.approx(0.60)
    assert inputs["site_population"]["exclusion_radius_km"] == pytest.approx(1.0)
    assert inputs["site_population"]["outer_radius_km"] == pytest.approx(80.0)
    assert inputs["human_diet_kg_s"]["milk"] == pytest.approx(3.5e-6)
    assert inputs["human_diet_kg_s"]["water"] == pytest.approx(1.7e-5)
    assert inputs["mol_diffusion"]["D"] == {
        "p_y": 0.418,
        "q_y": 0.796,
        "p_z": 0.520,
        "q_z": 0.711,
    }
    assert inputs["mol_diffusion"]["F"] == {
        "p_y": 0.235,
        "q_y": 0.796,
        "p_z": 0.311,
        "q_z": 0.711,
    }


def test_tables_10_to_13_are_four_complete_authoritative_1km_reference_tables() -> None:
    result = GATE.build_result()
    tables = result["reference_1km_tables"]

    assert list(tables) == ["table10_hto_D", "table11_hto_F", "table12_ht_D", "table13_ht_F"]
    assert all(list(table) == GATE.CASES for table in tables.values())
    assert all(len(row) == 7 for table in tables.values() for row in table.values())

    assert tables["table10_hto_D"]["10_m"] == pytest.approx(
        [1.2e-3, 2.3e-3, 6.2e-3, 6.5e-3, 4.1e-2, 8.8e-3, 4.7e-2]
    )
    assert tables["table11_hto_F"]["20_m_with_building_wake"] == pytest.approx(
        [4.8e-3, 8.6e-3, 2.3e-2, 1.3e-2, 2.2e-1, 2.2e-2, 2.4e-1]
    )
    assert tables["table12_ht_D"]["60_m"] == pytest.approx(
        [2.2e-8, 4.7e-6, 1.2e-5, 1.5e-5, 1.3e-4, 2.0e-5, 1.4e-4]
    )
    assert tables["table13_ht_F"]["10_m"] == pytest.approx(
        [3.1e-7, 1.8e-4, 4.9e-4, 3.6e-4, 7.8e-3, 5.4e-4, 8.3e-3]
    )


def test_printed_table_sum_identities_close_with_rounding_only() -> None:
    result = GATE.build_result()
    checks = result["sum_identity_checks"]
    assert all(value for table in checks.values() for value in table.values())


def test_robust_1km_release_height_wake_and_stability_ordering_is_preserved() -> None:
    result = GATE.build_result()
    assert all(result["ordering_checks"].values())
    assert all(result["source_trend_checks"].values())


def test_zero_vs_ten_metre_source_conflict_is_explicit_and_fails_closed() -> None:
    result = GATE.build_result()
    ambiguity = result["benchmark_inputs"]["release_height_ambiguity"]

    assert ambiguity == {
        "id": "ITER_RELEASE_HEIGHT_0_VS_10_M",
        "table8_value_m": 0.0,
        "section53_result_value_m": 10.0,
        "resolution": "PRESERVE_AMBIGUITY",
    }
    assert result["source_boundary"]["release_height_conflict_preserved"] is True
    assert result["decision"]["table8_zero_m_silently_replaced_by_10m"] is False
    assert result["source_boundary"]["full_atmospheric_numeric_replay_complete"] is False
    assert result["source_boundary"]["real_cteas_atmos_binding"] is False


def test_chart_helpers_are_not_promoted_and_g2_does_not_change_production_scope() -> None:
    result = GATE.build_result()
    assert result["source_boundary"]["figure_helper_tables_exact_oracle"] is False
    assert result["decision"]["figure_chart_values_promoted_to_exact_oracle"] is False
    assert result["decision"]["production_source_changed"] is False
    assert result["decision"]["default_parameters_changed"] is False
    assert result["decision"]["workflow_changed"] is False
    assert result["decision"]["roadmap_changed_in_stage_pr"] is False
    assert result["non_claims"]["iter_empirical_validation"] is False
    assert result["non_claims"]["original_ufotri_executable_equivalence"] is False


def test_g2_machine_gate_passes_as_tabulated_benchmark_reconstruction_only() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "G2_ITER_STATUS=PASS_MANUAL_TABULATED_ITER_BENCHMARK_RECONSTRUCTION" in completed.stdout

    json_line = next(
        line for line in completed.stdout.splitlines() if line.startswith("G2_ITER_RESULT_JSON=")
    )
    payload = json.loads(json_line.split("=", 1)[1])
    assert all(payload["contract_gates"].values())
    assert payload["non_claims"]["iter_full_atmospheric_numeric_replay"] is False
