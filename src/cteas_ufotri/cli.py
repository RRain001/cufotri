from __future__ import annotations

import argparse
from pathlib import Path

from .case import run_short_case
from .config import load_configuration, load_yaml
from .meteorology.era5_reader import prepare_hourly_forcing, read_era5
from .outputs.diagnostics import (
    create_validation_figures,
    write_atmosphere_spatial_outputs,
    write_validation_report,
)
from .outputs.writer import write_results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parameters", default="configs/default_parameters.yaml")
    parser.add_argument("--case", default="configs/test_case.yaml")
    parser.add_argument("--era5", help="Optional mapped ERA5 CSV/NetCDF forcing")
    parser.add_argument("--output-directory", help="Override case output directory")
    args = parser.parse_args()
    config = load_configuration(args.parameters, args.case)
    forcing = None
    forcing_description = "deterministic synthetic hourly forcing"
    if args.era5:
        mapping = load_yaml("configs/era5_mapping.yaml")
        raw = read_era5(args.era5, mapping)
        forcing = prepare_hourly_forcing(
            raw,
            config["physics"]["fallback_shortwave_absorptivity"],
            config["physics"]["fallback_net_longwave_loss_w_m2"],
            accumulation_semantics=mapping.get("accumulation_semantics", "interval"),
        )
        forcing_description = (
            f"ERA5 hourly point series ({forcing['radiation_method'].iloc[0]})"
        )
    frame = run_short_case(config, forcing)
    if args.output_directory:
        config["output_directory"] = args.output_directory
    output = Path(config["output_directory"])
    result = write_results(frame, output)
    create_validation_figures(frame, output)
    write_atmosphere_spatial_outputs(config, output)
    report = write_validation_report(
        frame, output, config["name"], forcing_description, config
    )
    print(f"Results: {result}")
    print(f"Report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
