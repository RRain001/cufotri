from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

from cteas_ufotri.analysis.uncertainty import run_uncertainty
from cteas_ufotri.analysis.wet_sensitivity import wet_parameter_sensitivity
from cteas_ufotri.benchmarks.v2_cases import (
    benchmark_suite_passes,
    run_v2_benchmark_suite,
)
from cteas_ufotri.benchmarks.independent import benchmark_category_counts
from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration
from cteas_ufotri.coupling.integrator import advance
from cteas_ufotri.coupling.state import State


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def dependency_versions() -> dict[str, str]:
    result = {}
    for name in ("numpy", "pandas", "scipy", "matplotlib", "PyYAML"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = "not-installed"
    return result


def _base() -> dict:
    return load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/test_case.yaml",
    )


def _case_checks() -> dict[str, dict]:
    wet = _base()
    wet["duration_hours"] = 2.0
    wet["synthetic_forcing"].update(
        rain_start_hour=0.0, rain_end_hour=2.0, rain_rate_m_s=1.0e-5
    )
    wet["atmosphere"]["depletion"]["wet_scavenging_mode"] = (
        "precipitation_power_law"
    )
    wet_frame = run_short_case(wet)
    wet_mismatch = float(wet_frame["depletion_deposition_mismatch_bq_s"].abs().max())
    if wet_frame["wet_depletion_bq_s"].max() <= 0 or wet_mismatch > 1.0e-5:
        raise ValueError("Wet-scavenging acceptance failed")

    leaf = _base()
    leaf["duration_hours"] = 2.0
    leaf["plant"]["leaf_exchange_mode"] = "bidirectional_resistance"
    leaf_frame = run_short_case(leaf)
    if leaf_frame["leaf_uptake_flux"].max() <= 0:
        raise ValueError("Leaf-exchange acceptance failed")
    formal_leaf = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/v2/v2_leaf_exchange_food_dose_72h.yaml",
    )
    formal_leaf_frame = run_short_case(formal_leaf)
    formal_leaf_off = deepcopy(formal_leaf)
    formal_leaf_off["plant"]["leaf_exchange_mode"] = "off"
    formal_leaf_off_frame = run_short_case(formal_leaf_off)
    if (
        formal_leaf_frame["plant_ingestion_dose_sv"].iloc[-1] <= 0.0
        or formal_leaf_frame["plant_obt_inventory"].iloc[-1] <= 0.0
        or formal_leaf_off_frame["plant_ingestion_dose_sv"].iloc[-1] != 0.0
    ):
        raise ValueError("Formal leaf-to-food/dose acceptance failed")

    food = _base()
    food["duration_hours"] = 8.0
    food["crops"]["active_crop"] = "pasture"
    food["crops"]["edible_compartments_enabled"] = True
    food["foodchain"]["enabled"] = True
    food["foodchain"]["animal_mode"] = "minimal_cow"
    food_frame = run_short_case(food)
    if (
        food_frame["milk_hto_bq_l"].iloc[-1] <= 0
        or food_frame["ecological_box_relative_residual"].abs().max() > 1.0e-12
    ):
        raise ValueError("Food-chain acceptance failed")

    dose = deepcopy(food)
    dose["dose"]["enabled"] = True
    dose_frame = run_short_case(dose)
    if dose_frame["total_effective_dose_sv"].iloc[-1] <= 0:
        raise ValueError("Dose acceptance failed")
    beef = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/v2/v2_full_adult_dose.yaml",
    )
    beef_frame = run_short_case(beef)
    if (
        beef_frame["beef_produced_hto_bq_m2"].iloc[-1] <= 0.0
        or beef_frame["beef_consumed_hto_bq_m2"].iloc[-1] <= 0.0
        or beef_frame["meat_dose_sv"].iloc[-1] <= 0.0
        or beef_frame["animal_product_activity_residual_bq_m2"].abs().max()
        > 1.0e-12
    ):
        raise ValueError("Conservative beef-production acceptance failed")

    return {
        "wet_scavenging": {
            "steps": len(wet_frame),
            "max_wet_depletion_bq_s": float(wet_frame["wet_depletion_bq_s"].max()),
            "max_ledger_mismatch_bq_s": wet_mismatch,
        },
        "leaf_exchange": {
            "steps": len(formal_leaf_frame),
            "max_leaf_uptake_bq_m2_s": float(leaf_frame["leaf_uptake_flux"].max()),
            "max_surface_residual": float(
                formal_leaf_frame["surface_box_relative_residual"].max()
            ),
            "final_plant_ingestion_dose_sv": float(
                formal_leaf_frame["plant_ingestion_dose_sv"].iloc[-1]
            ),
            "off_control_plant_ingestion_dose_sv": float(
                formal_leaf_off_frame["plant_ingestion_dose_sv"].iloc[-1]
            ),
        },
        "food_chain": {
            "steps": len(food_frame),
            "final_milk_hto_bq_l": float(food_frame["milk_hto_bq_l"].iloc[-1]),
            "max_ecological_residual": float(
                food_frame["ecological_box_relative_residual"].abs().max()
            ),
        },
        "dose": {
            "steps": len(dose_frame),
            "final_total_effective_dose_sv": float(
                dose_frame["total_effective_dose_sv"].iloc[-1]
            ),
        },
        "beef_boundary": {
            "steps": len(beef_frame),
            "produced_hto_bq_m2": float(
                beef_frame["beef_produced_hto_bq_m2"].iloc[-1]
            ),
            "consumed_hto_bq_m2": float(
                beef_frame["beef_consumed_hto_bq_m2"].iloc[-1]
            ),
            "final_meat_dose_sv": float(beef_frame["meat_dose_sv"].iloc[-1]),
            "max_combined_residual_bq_m2": float(
                beef_frame["animal_product_activity_residual_bq_m2"].abs().max()
            ),
        },
    }


def _uncertainty_check() -> dict:
    base = {"parameters": {"x": 1.0, "y": 2.0}}
    specifications = [
        {
            "name": "x",
            "path": "parameters.x",
            "distribution": "uniform",
            "low": 0.5,
            "high": 1.5,
        },
        {
            "name": "y",
            "path": "parameters.y",
            "distribution": "uniform",
            "low": 1.0,
            "high": 3.0,
        },
    ]

    def model(config):
        return {
            "total": config["parameters"]["x"] + 2.0 * config["parameters"]["y"]
        }

    first = run_uncertainty(
        model, base, specifications, 8, "latin_hypercube", 20260724
    )
    second = run_uncertainty(
        model, base, specifications, 8, "latin_hypercube", 20260724
    )
    if not np.array_equal(first.outcomes["total"], second.outcomes["total"]):
        raise ValueError("Uncertainty acceptance is not reproducible")
    return {
        "seed": first.seed,
        "method": first.method,
        "sample_count": len(first.outcomes["total"]),
        "statistics": first.statistics["total"],
    }


def _expanded_rc1_checks(end_to_end_root: Path) -> dict:
    required_activity_fields = {
        "external_stack_input_bq",
        "dry_plume_loss_bq",
        "wet_plume_loss_bq",
        "dry_surface_input_bq",
        "wet_surface_input_bq",
        "environmental_inventory_bq",
        "harvested_activity_bq",
        "milk_activity_bq",
        "beef_activity_bq",
        "excreted_activity_bq",
        "deep_loss_bq",
        "runoff_bypass_bq",
        "decay_loss_bq",
        "activity_residual_bq",
    }
    case_frames = {}
    for case_name in (
        "v2_era5_72h_wet_deposition",
        "v2_accident_plant_obt_14d",
        "v2_crop_ingestion_season",
        "v2_pasture_milk_pathway",
        "v2_full_adult_dose",
        "v2_leaf_exchange_food_dose_72h",
    ):
        frame = pd.read_csv(end_to_end_root / case_name / "results.csv")
        missing = required_activity_fields - set(frame)
        if missing:
            raise ValueError(
                f"{case_name} lacks activity-protocol fields: {sorted(missing)}"
            )
        final = frame.iloc[-1]
        if (
            final["dry_plume_loss_bq"] != final["dry_surface_input_bq"]
            or final["wet_plume_loss_bq"] != final["wet_surface_input_bq"]
            or final["activity_relative_residual"] > 1.0e-12
            or final["accounted_environmental_activity_bq"]
            > final["external_stack_input_bq"] * (1.0 + 1.0e-12) + 1.0e-6
        ):
            raise ValueError(f"{case_name} activity propagation failed")
        case_frames[case_name] = frame

    dry_final = case_frames["v2_era5_72h_wet_deposition"].iloc[-1]
    dry_ratio = dry_final["dry_surface_input_bq"] / dry_final["dry_plume_loss_bq"]
    wet_ratio = wet_final = (
        dry_final["wet_surface_input_bq"] / dry_final["wet_plume_loss_bq"]
    )
    if dry_ratio != 1.0 or wet_ratio != 1.0:
        raise ValueError("Dry/wet 72 h interface ledger failed")

    leaf_config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/v2/v2_leaf_exchange_food_dose_72h.yaml",
    )
    timestep_results = {}
    endpoints = (
        "plant_tfwt_inventory",
        "plant_obt_inventory",
        "edible_tfwt_inventory_bq_m2",
        "edible_obt_inventory_bq_m2",
        "plant_ingestion_dose_sv",
    )
    for dt_s in (600, 300, 120, 60):
        candidate = deepcopy(leaf_config)
        candidate["time_step_seconds"] = dt_s
        final = run_short_case(candidate).iloc[-1]
        timestep_results[str(dt_s)] = {
            name: float(final[name]) for name in endpoints
        }
    reference = timestep_results["60"]
    maximum_timestep_change = max(
        abs(values[name] - reference[name]) / max(abs(reference[name]), 1.0e-30)
        for values in timestep_results.values()
        for name in endpoints
    )
    if maximum_timestep_change >= 0.01:
        raise ValueError("Leaf formal-case time-step convergence failed")

    footprint_results = {}
    for area in (1.0e5, 1.0e6, 1.0e7):
        config = _base()
        config["duration_hours"] = 1.0
        config["deposition"]["dry_footprint"]["area_m2"] = area
        final = run_short_case(config).iloc[-1]
        footprint_results[str(area)] = {
            "plume_loss_bq": float(final["dry_plume_loss_bq"]),
            "plume_loss_bq_s": float(final["dry_depletion_bq_s"]),
            "surface_flux_bq_m2_s": float(
                final["dry_deposition_flux_bq_m2_s"]
            ),
        }
    plume_losses = {
        values["plume_loss_bq"] for values in footprint_results.values()
    }
    if len(plume_losses) != 1 or any(
        abs(
            values["surface_flux_bq_m2_s"] * float(area)
            - values["plume_loss_bq_s"]
        )
        > 1.0e-6
        for area, values in footprint_results.items()
    ):
        raise ValueError("Footprint scaling failed")

    zero = _base()
    zero["duration_hours"] = 2.0
    zero["source"]["emission_rate_bq_s"] = 0.0
    zero_final = run_short_case(zero).iloc[-1]
    if (
        zero_final["external_stack_input_bq"] != 0.0
        or zero_final["accounted_environmental_activity_bq"] != 0.0
    ):
        raise ValueError("Zero-source activity protocol failed")

    internal = _base()
    internal["plant"]["leaf_exchange_mode"] = "off"
    internal["physics"]["tritium_decay_constant_s"] = 0.0
    initial = State(
        soil_water_m=0.01,
        plant_tfwt_bq_m2=100.0,
        plant_obt_bq_m2=50.0,
    )
    internal_final, internal_diag = advance(
        initial,
        60.0,
        0.0,
        0.0,
        0.0,
        0.0,
        internal,
        edible_allocation_rate_s=1.0e-5,
    )
    if (
        internal_diag.surface_box_mass_closure.external_input_bq_m2 != 0.0
        or internal_final.total_hto_bq_m2 != initial.total_hto_bq_m2
        or internal_diag.surface_box_mass_closure.relative_error > 1.0e-12
    ):
        raise ValueError("Closed internal-transfer activity check failed")

    pasture_config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/v2/v2_pasture_multiyear_2y.yaml",
    )
    pasture = run_short_case(pasture_config)
    pasture_final = pasture.iloc[-1]
    if (
        int(pasture["harvest_event"].sum()) != 6
        or pasture["surface_box_relative_residual"].max() > 1.0e-12
        or pasture_final["activity_relative_residual"] > 1.0e-12
    ):
        raise ValueError("Two-year pasture acceptance failed")

    return {
        "activity_protocol_case_count": len(case_frames) + 1,
        "dry_72h": {
            "pre_fix_plume_loss_bq": 3.246027849313e9,
            "pre_fix_surface_input_bq": 2.901284607250e10,
            "pre_fix_ratio": 8.937953529463,
            "post_fix_plume_loss_bq": float(dry_final["dry_plume_loss_bq"]),
            "post_fix_surface_input_bq": float(dry_final["dry_surface_input_bq"]),
            "post_fix_ratio": float(dry_ratio),
        },
        "wet_72h_ratio": float(wet_final),
        "maximum_activity_relative_residual": max(
            float(frame["activity_relative_residual"].max())
            for frame in case_frames.values()
        ),
        "maximum_timestep_endpoint_change": maximum_timestep_change,
        "footprint_scaling": footprint_results,
        "zero_source_status": "PASS",
        "closed_internal_transfer_status": "PASS",
        "pasture_two_year": {
            "steps": len(pasture),
            "cut_events": int(pasture["harvest_event"].sum()),
            "final_harvested_activity_bq": float(
                pasture_final["harvested_activity_bq"]
            ),
            "maximum_activity_relative_residual": float(
                pasture["activity_relative_residual"].max()
            ),
        },
    }


def recompute() -> list[str]:
    started = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory(prefix="cteas_ufotri_v2_acceptance_") as tmp:
        output_root = Path(tmp)
        v1 = subprocess.run(
            [sys.executable, "scripts/verify_acceptance.py", "--recompute"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        case_checks = _case_checks()
        wet_sensitivity = wet_parameter_sensitivity(_base())
        if len(wet_sensitivity) != 12 or any(
            record["wet_plume_loss_bq"] != record["wet_surface_input_bq"]
            for record in wet_sensitivity
        ):
            raise ValueError("Wet-parameter uncertainty grid failed")
        uncertainty = _uncertainty_check()
        benchmarks = run_v2_benchmark_suite(_base())
        benchmark_counts = benchmark_category_counts(benchmarks)
        if not benchmark_suite_passes(benchmarks):
            raise ValueError("V2 benchmark acceptance failed")

        end_to_end_root = output_root / "end_to_end"
        subprocess.run(
            [
                sys.executable,
                "scripts/run_v2_end_to_end.py",
                "--output",
                str(end_to_end_root),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        required = [
            end_to_end_root / "suite_summary.json",
            end_to_end_root / "uncertainty_summary.json",
            end_to_end_root / "uncertainty_interval.png",
            end_to_end_root / "parameter_sensitivity.png",
        ]
        for case_name in (
            "v2_era5_72h_wet_deposition",
            "v2_accident_plant_obt_14d",
            "v2_crop_ingestion_season",
            "v2_pasture_milk_pathway",
            "v2_full_adult_dose",
            "v2_leaf_exchange_food_dose_72h",
        ):
            required.extend(
                [
                    end_to_end_root / case_name / "results.csv",
                    end_to_end_root / case_name / "provenance.json",
                    end_to_end_root / case_name / "conservation.png",
                ]
            )
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise ValueError(f"Missing V2 recompute artifacts: {missing}")
        full_model_uncertainty = json.loads(
            (end_to_end_root / "uncertainty_summary.json").read_text(
                encoding="utf-8"
            )
        )
        if (
            full_model_uncertainty["status"] != "PASS"
            or full_model_uncertainty["sample_sizes"] != [64, 128, 256]
            or len(full_model_uncertainty["additional_seeds"]) < 3
            or not full_model_uncertainty["inactive_parameters"]
            or not full_model_uncertainty["same_seed_reproducible"]
            or full_model_uncertainty["model_run_count"]
            != full_model_uncertainty["expected_model_run_count"]
        ):
            raise ValueError("Full-model mode-aware LHS acceptance failed")
        expanded_rc1 = _expanded_rc1_checks(end_to_end_root)

        config_paths = [
            ROOT / "configs/default_parameters.yaml",
            ROOT / "configs/test_case.yaml",
            *sorted((ROOT / "configs/v2").glob("*.yaml")),
        ]
        provenance = {
            "git_head": git_value("rev-parse", "HEAD"),
            "worktree_status": git_value("status", "--short"),
            "python": platform.python_version(),
            "dependencies": dependency_versions(),
            "config_hashes": {path.name: sha256(path) for path in config_paths},
            "input_hashes": {
                "era5": sha256(
                    ROOT / "data/era5/era5_surface_2025-06-01_2025-06-02.csv"
                )
            },
            "random_seed": 20260724,
            "model_modes": {
                "chemical": "HTO-only",
                "soil_formal": "single_top_5cm",
                "soil_experimental": "surface_root_deep_3box standalone",
                "wet_scavenging": "precipitation_power_law",
                "leaf_exchange": "bidirectional_resistance",
                "foodchain": "minimal_cow",
                "beef_product": "continuous_herd_turnover",
                "dose": "research screening dose",
            },
            "runtime_started_utc": started.isoformat(),
            "runtime_finished_utc": datetime.now(timezone.utc).isoformat(),
            "temporary_output_directory": str(output_root),
            "v1_acceptance_output": v1.stdout.splitlines(),
            "case_checks": case_checks,
            "wet_parameter_sensitivity": wet_sensitivity,
            "uncertainty_algorithm": uncertainty,
            "full_model_uncertainty": full_model_uncertainty,
            "expanded_rc1_checks": expanded_rc1,
            "benchmark_record_count": len(benchmarks),
            "benchmark_category_counts": benchmark_counts,
            "end_to_end_summary_sha256": sha256(
                end_to_end_root / "suite_summary.json"
            ),
        }
        provenance_path = output_root / "v2_acceptance_provenance.json"
        provenance_path.write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if not provenance_path.is_file():
            raise ValueError("V2 acceptance provenance was not written")
        return [
            "PASS: V1 recompute acceptance",
            (
                "PASS: wet/leaf/food/dose cases: "
                + ", ".join(f"{name}={values['steps']} steps" for name, values in case_checks.items())
            ),
            (
                "PASS: analytic LHS algorithm and full-model convergence "
                "at n=64/128/256 with four seeds"
            ),
            "PASS: 12-case wet-scavenging parameter grid",
            (
                "PASS: expanded RC1 activity protocol, footprint, time-step, "
                "zero-source, internal-transfer, and two-year pasture checks"
            ),
            (
                "PASS: categorized V2 evidence "
                f"({benchmark_counts['analytic_benchmark']} analytic, "
                f"{benchmark_counts['manual_anchor']} manual, "
                f"{benchmark_counts['literature_comparison']} literature)"
            ),
            "PASS: six end-to-end cases and required artifacts recomputed",
            "PASS: V2 provenance and hashes recorded in temporary output",
        ]


def main() -> int:
    for line in recompute():
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
