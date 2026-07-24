from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import os
import tempfile

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "cteas_ufotri_matplotlib")
)
os.environ.setdefault(
    "XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "cteas_ufotri_cache")
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from cteas_ufotri.analysis.uncertainty import (
    one_at_a_time_sensitivity,
    run_uncertainty,
)
from cteas_ufotri.case import _forcing, run_short_case
from cteas_ufotri.config import load_configuration, load_yaml
from cteas_ufotri.meteorology.era5_reader import (
    prepare_hourly_forcing,
    read_era5,
)


ROOT = Path(__file__).resolve().parents[1]
CASE_FILES = (
    "v2_era5_72h_wet_deposition.yaml",
    "v2_accident_plant_obt_14d.yaml",
    "v2_crop_ingestion_season.yaml",
    "v2_pasture_milk_pathway.yaml",
    "v2_full_adult_dose.yaml",
    "v2_leaf_exchange_food_dose_72h.yaml",
)


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


def hybrid_era5_forcing(config: dict, era5_path: Path) -> pd.DataFrame:
    mapping = load_yaml(ROOT / "configs/era5_mapping.yaml")
    raw = read_era5(era5_path, mapping)
    forcing = prepare_hourly_forcing(
        raw,
        config["physics"]["fallback_shortwave_absorptivity"],
        config["physics"]["fallback_net_longwave_loss_w_m2"],
        accumulation_semantics=mapping.get("accumulation_semantics", "interval"),
    )
    required = int(config["duration_hours"])
    rows = [forcing.iloc[index].to_dict() for index in range(min(len(forcing), required))]
    start = datetime.fromisoformat(config["start"].replace("Z", "+00:00"))
    for index in range(len(rows), required):
        row = _forcing(index * 3600.0, config)
        row["time"] = start + timedelta(hours=index)
        row["radiation_method"] = "documented deterministic extension after available ERA5"
        rows.append(row)
    result = pd.DataFrame(rows)
    result["time"] = pd.to_datetime(result["time"], utc=True)
    return result


def plot_columns(
    frame: pd.DataFrame,
    directory: Path,
    filename: str,
    columns: list[str],
    ylabel: str,
) -> None:
    fig, axis = plt.subplots(figsize=(8, 4.5))
    time = pd.to_datetime(frame["time"])
    for column in columns:
        axis.plot(time, frame[column], label=column)
    axis.set_xlabel("UTC")
    axis.set_ylabel(ylabel)
    if len(columns) > 1:
        axis.legend(fontsize=7)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(directory / filename, dpi=140)
    plt.close(fig)


def write_figures(frame: pd.DataFrame, directory: Path) -> None:
    definitions = (
        ("atmospheric_hto.png", ["air_hto_concentration"], "Bq m-3"),
        (
            "dry_wet_deposition.png",
            ["dry_depletion_bq_s", "wet_depletion_bq_s"],
            "Bq s-1",
        ),
        ("soil_hto.png", ["soil_hto_inventory"], "Bq m-2"),
        (
            "tfwt.png",
            ["plant_tfwt_inventory", "edible_tfwt_inventory_bq_m2"],
            "Bq m-2",
        ),
        (
            "obt.png",
            ["plant_obt_inventory", "edible_obt_inventory_bq_m2"],
            "Bq m-2",
        ),
        (
            "food_concentration.png",
            [
                "leafy_tfwt_bq_kg_fresh",
                "pasture_tfwt_bq_kg_fresh",
                "milk_hto_bq_l",
            ],
            "food concentration",
        ),
        (
            "dose_pathways.png",
            [
                "inhalation_dose_sv",
                "skin_absorption_dose_sv",
                "plant_ingestion_dose_sv",
                "milk_dose_sv",
                "meat_dose_sv",
            ],
            "Sv",
        ),
        (
            "conservation.png",
            [
                "surface_box_relative_residual",
                "ecological_box_relative_residual",
            ],
            "relative residual",
        ),
    )
    for filename, columns, ylabel in definitions:
        plot_columns(frame, directory, filename, columns, ylabel)


def uncertainty_artifacts(config: dict, output_root: Path) -> dict:
    model_config = json.loads(json.dumps(config))
    model_config["duration_hours"] = 24.0
    model_config["time_step_seconds"] = 3600
    specifications = [
        {
            "name": "deposition_velocity",
            "path": "atmosphere.deposition_velocity_m_s",
            "distribution": "uniform",
            "low": 0.0025,
            "high": 0.0075,
        },
        {
            "name": "pasture_lai",
            "path": "crops.parameters.pasture.max_lai",
            "distribution": "uniform",
            "low": 2.0,
            "high": 5.0,
        },
        {
            "name": "feed_intake",
            "path": "foodchain.feed_intake_kg_fresh_day",
            "distribution": "uniform",
            "low": 30.0,
            "high": 70.0,
        },
        {
            "name": "adult_hto_coefficient",
            "path": "dose.age_groups.adult.hto_dose_coefficient_sv_bq",
            "distribution": "uniform",
            "low": 1.6e-11,
            "high": 2.0e-11,
        },
    ]

    def model(sample_config: dict) -> dict[str, float]:
        final = run_short_case(sample_config).iloc[-1]
        return {
            name: float(final[name])
            for name in (
                "inhalation_dose_sv",
                "skin_absorption_dose_sv",
                "plant_ingestion_dose_sv",
                "milk_dose_sv",
                "meat_dose_sv",
                "total_effective_dose_sv",
            )
        }

    result = run_uncertainty(
        model,
        model_config,
        specifications,
        12,
        "latin_hypercube",
        20260724,
        pathway_output_names=[
            "inhalation_dose_sv",
            "skin_absorption_dose_sv",
            "plant_ingestion_dose_sv",
            "milk_dose_sv",
            "meat_dose_sv",
        ],
    )
    oat = one_at_a_time_sensitivity(
        model,
        model_config,
        specifications,
        "total_effective_dose_sv",
    )
    summary = {
        "seed": result.seed,
        "method": result.method,
        "sample_count": 12,
        "statistics": result.statistics,
        "rank_correlations": result.rank_correlations,
        "pathway_contributions": result.pathway_contributions,
        "oat_sensitivity": oat,
    }
    (output_root / "uncertainty_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dose_stats = result.statistics["total_effective_dose_sv"]
    fig, axis = plt.subplots(figsize=(5, 4))
    axis.errorbar(
        ["total dose"],
        [dose_stats["median"]],
        yerr=[
            [dose_stats["median"] - dose_stats["p05"]],
            [dose_stats["p95"] - dose_stats["median"]],
        ],
        fmt="o",
    )
    axis.set_ylabel("Sv")
    axis.set_title("LHS 5-95% interval")
    fig.tight_layout()
    fig.savefig(output_root / "uncertainty_interval.png", dpi=140)
    plt.close(fig)
    fig, axis = plt.subplots(figsize=(7, 4))
    axis.bar(list(oat), list(oat.values()))
    axis.tick_params(axis="x", rotation=25)
    axis.set_ylabel("d dose / d parameter")
    fig.tight_layout()
    fig.savefig(output_root / "parameter_sensitivity.png", dpi=140)
    plt.close(fig)
    return summary


def run(output_root: Path, era5_path: Path) -> dict:
    started = datetime.now(timezone.utc)
    output_root.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for filename in CASE_FILES:
        case_path = ROOT / "configs/v2" / filename
        config = load_configuration(ROOT / "configs/default_parameters.yaml", case_path)
        case_directory = output_root / config["name"]
        case_directory.mkdir(parents=True, exist_ok=True)
        forcing = (
            hybrid_era5_forcing(config, era5_path)
            if config["name"] == "v2_era5_72h_wet_deposition"
            else None
        )
        frame = run_short_case(config, forcing)
        results_path = case_directory / "results.csv"
        frame.to_csv(results_path, index=False)
        write_figures(frame, case_directory)
        config_hash = hashlib.sha256(
            json.dumps(config, sort_keys=True).encode("utf-8")
        ).hexdigest()
        files = sorted(
            path for path in case_directory.iterdir() if path.name != "provenance.json"
        )
        provenance = {
            "case": config["name"],
            "git_head": git_value("rev-parse", "HEAD"),
            "worktree_status": git_value("status", "--short"),
            "python": platform.python_version(),
            "dependencies": dependency_versions(),
            "config_file": str(case_path),
            "config_file_sha256": sha256(case_path),
            "merged_config_sha256": config_hash,
            "input_hashes": (
                {"era5": sha256(era5_path)}
                if forcing is not None
                else {"synthetic_forcing": config_hash}
            ),
            "forcing_source": (
                "48 h existing ERA5 plus explicit 24 h deterministic extension"
                if forcing is not None
                else "deterministic configured forcing"
            ),
            "model_modes": {
                "wet_scavenging": config["atmosphere"]["depletion"][
                    "wet_scavenging_mode"
                ],
                "leaf_exchange": config["plant"]["leaf_exchange_mode"],
                "reemission": config["reemission"]["mode"],
                "crop": config["crops"]["active_crop"],
                "foodchain": config["foodchain"]["animal_mode"],
                "beef_product": config["foodchain"]["animal_products"]["beef"][
                    "mode"
                ],
                "dose_age_group": config["dose"]["active_age_group"],
            },
            "runtime_started_utc": started.isoformat(),
            "runtime_finished_utc": datetime.now(timezone.utc).isoformat(),
            "output_hashes": {path.name: sha256(path) for path in files},
        }
        (case_directory / "provenance.json").write_text(
            json.dumps(provenance, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        summaries[config["name"]] = {
            "steps": len(frame),
            "max_surface_relative_residual": float(
                frame["surface_box_relative_residual"].max()
            ),
            "final_total_dose_sv": float(frame["total_effective_dose_sv"].iloc[-1]),
            "output_directory": str(case_directory),
        }
    full_config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/v2/v2_full_adult_dose.yaml",
    )
    uncertainty = uncertainty_artifacts(full_config, output_root)
    suite = {
        "started_utc": started.isoformat(),
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "cases": summaries,
        "uncertainty": uncertainty,
    }
    (output_root / "suite_summary.json").write_text(
        json.dumps(suite, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return suite


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--era5",
        type=Path,
        default=ROOT / "data/era5/era5_surface_2025-06-01_2025-06-02.csv",
    )
    args = parser.parse_args()
    suite = run(args.output, args.era5)
    print(json.dumps(suite["cases"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
