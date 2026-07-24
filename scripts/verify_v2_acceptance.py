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

from cteas_ufotri.analysis.uncertainty import run_uncertainty
from cteas_ufotri.benchmarks.v2_cases import (
    benchmark_suite_passes,
    run_v2_benchmark_suite,
)
from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration


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

    return {
        "wet_scavenging": {
            "steps": len(wet_frame),
            "max_wet_depletion_bq_s": float(wet_frame["wet_depletion_bq_s"].max()),
            "max_ledger_mismatch_bq_s": wet_mismatch,
        },
        "leaf_exchange": {
            "steps": len(leaf_frame),
            "max_leaf_uptake_bq_m2_s": float(leaf_frame["leaf_uptake_flux"].max()),
            "max_surface_residual": float(
                leaf_frame["surface_box_relative_residual"].max()
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
        uncertainty = _uncertainty_check()
        benchmarks = run_v2_benchmark_suite(_base())
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
                "dose": "research screening dose",
            },
            "runtime_started_utc": started.isoformat(),
            "runtime_finished_utc": datetime.now(timezone.utc).isoformat(),
            "temporary_output_directory": str(output_root),
            "v1_acceptance_output": v1.stdout.splitlines(),
            "case_checks": case_checks,
            "uncertainty": uncertainty,
            "benchmark_case_count": len(benchmarks),
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
            "PASS: fixed-seed LHS uncertainty sample",
            f"PASS: {len(benchmarks)} V2 benchmark cases",
            "PASS: five end-to-end cases and required artifacts recomputed",
            "PASS: V2 provenance and hashes recorded in temporary output",
        ]


def main() -> int:
    for line in recompute():
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
