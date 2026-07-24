from __future__ import annotations

from pathlib import Path
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
import numpy as np

from ..atmosphere.gaussian import concentration_grid
from ..atmosphere.plume_rise import effective_stack_height_m


def create_validation_figures(frame: pd.DataFrame, output_directory: str | Path) -> list[Path]:
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    definitions = [
        ("air_concentration.png", ["air_hto_concentration"], "Bq m$^{-3}$"),
        ("soil_hto.png", ["soil_hto_inventory"], "Bq m$^{-2}$"),
        ("plant_hto.png", ["plant_tfwt_inventory", "plant_obt_inventory"], "Bq m$^{-2}$"),
        ("reemission.png", ["soil_reemission_flux", "plant_reemission_flux"], "Bq m$^{-2}$ s$^{-1}$"),
        ("mass_balance.png", ["mass_balance_error"], "Bq m$^{-2}$"),
    ]
    paths: list[Path] = []
    time = pd.to_datetime(frame["time"])
    for filename, columns, ylabel in definitions:
        fig, axis = plt.subplots(figsize=(7, 4))
        for column in columns:
            axis.plot(time, frame[column], label=column)
        axis.set_ylabel(ylabel)
        axis.set_xlabel("UTC")
        if len(columns) > 1:
            axis.legend()
        fig.autofmt_xdate()
        fig.tight_layout()
        path = directory / filename
        fig.savefig(path, dpi=150)
        plt.close(fig)
        paths.append(path)
    return paths


def write_validation_report(
    frame: pd.DataFrame,
    output_directory: str | Path,
    case_name: str,
    forcing_description: str = "deterministic synthetic hourly forcing",
    config: dict | None = None,
) -> Path:
    target = Path(output_directory) / "validation_report.md"
    max_abs = float(frame["mass_balance_error"].abs().max())
    max_rel = float(frame["mass_balance_relative_error"].max())
    case_lines = ""
    if config is not None:
        case_lines = f"""
## Declared case parameters

- Source coordinate: {config['site']['longitude_deg']} E, {config['site']['latitude_deg']} N
- Pollutant and release: {config['source']['pollutant']}, {config['source']['emission_rate_bq_s']:.6e} Bq s^-1
- Stack height/diameter: {config['source']['stack_height_m']} m / {config['source']['stack_diameter_m']} m
- Stack temperature/exit velocity: {config['source']['stack_temperature_k']} K / {config['source']['exit_velocity_m_s']} m s^-1
- Plume rise/stability: {config['atmosphere']['plume_rise_mode']} / {config['atmosphere']['stability_mode']}
- Re-emission mode: {config['reemission']['mode']}
- Duration/internal step/forcing step: {config['duration_hours']} h / {config['time_step_seconds']} s / {config['meteorology_step_seconds']} s
- Soil depth and LAI: {config['soil']['depth_m']} m / {config['plant']['lai']}
"""
    text = f"""# {case_name} validation report

- Steps: {len(frame)}
- Maximum absolute HTO mass-balance residual: {max_abs:.6e} Bq m^-2
- Maximum relative HTO mass-balance error: {max_rel:.6e}
- Air concentration finite/non-negative: {bool(frame['air_hto_concentration'].ge(0).all())}
- Final soil HTO inventory: {frame['soil_hto_inventory'].iloc[-1]:.6e} Bq m^-2
- Final plant TFWT inventory: {frame['plant_tfwt_inventory'].iloc[-1]:.6e} Bq m^-2
- Final plant OBT inventory: {frame['plant_obt_inventory'].iloc[-1]:.6e} Bq m^-2
- Meteorological forcing: {forcing_description}
{case_lines}

The same calculation kernel accepts mapped ERA5 CSV/NetCDF or deterministic
synthetic forcing through the meteorological provider boundary.
"""
    target.write_text(text, encoding="utf-8")
    return target


def write_atmosphere_spatial_outputs(config: dict, output_directory: str | Path) -> list[Path]:
    """Write a representative grid and centreline plot for the configured source."""
    directory = Path(output_directory)
    output = config["outputs"]
    x = np.linspace(
        output["grid_downwind_min_m"],
        output["grid_downwind_max_m"],
        output["grid_downwind_count"],
    )
    y = np.linspace(
        output["grid_crosswind_min_m"],
        output["grid_crosswind_max_m"],
        output["grid_crosswind_count"],
    )
    height = effective_stack_height_m(
        config["source"]["stack_height_m"],
        config["atmosphere"]["plume_rise_mode"],
        config["atmosphere"]["fixed_plume_rise_m"],
        stack_diameter_m=config["source"]["stack_diameter_m"],
        exit_velocity_m_s=config["source"]["exit_velocity_m_s"],
        stack_temperature_k=config["source"]["stack_temperature_k"],
        ambient_temperature_k=output["representative_ambient_temperature_k"],
        wind_speed_m_s=output["representative_wind_m_s"],
        downwind_distance_m=output["representative_plume_rise_distance_m"],
    )
    values = concentration_grid(
        config["source"]["emission_rate_bq_s"],
        x,
        y,
        output["representative_wind_m_s"],
        height,
        config["atmosphere"]["stability_class"],
        config["atmosphere"].get("mixing_height_m"),
        config["atmosphere"].get("mixing_layer_image_terms", 4),
    )
    grid = pd.DataFrame(
        [(xx, yy, values[ix, iy]) for ix, xx in enumerate(x) for iy, yy in enumerate(y)],
        columns=["downwind_m", "crosswind_m", "air_hto_concentration_bq_m3"],
    )
    csv_path = directory / "atmosphere_grid.csv"
    grid.to_csv(csv_path, index=False)
    fig, axis = plt.subplots(figsize=(7, 4))
    centre = values[:, int(np.argmin(np.abs(y)))]
    axis.plot(x, centre)
    axis.set_xlabel("Downwind distance (m)")
    axis.set_ylabel("HTO concentration (Bq m$^{-3}$)")
    axis.set_title("Representative plume centreline")
    fig.tight_layout()
    plot_path = directory / "centreline_air_concentration.png"
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)
    return [csv_path, plot_path]
