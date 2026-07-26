#!/usr/bin/env python3
"""Run the frozen SB1 H0/H2/H3 parameters across the SB4 forcing matrix."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import jsonschema
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb4"
REPORTS = BENCHMARK / "reports"
LOCAL = ROOT / "validation" / "external_local" / "emras_soybean_sb4"
GENERATED = LOCAL / "generated_forcing"
OUTPUTS = LOCAL / "outputs"
PROTOCOL_PATH = BENCHMARK / "preregistration" / "sb4_transfer_protocol.yaml"
SB1_MECHANISM_ROOT = (
    ROOT / "validation" / "benchmarks" / "emras_soybean_sb1_mechanisms"
)
SB1_FROZEN = SB1_MECHANISM_ROOT / "reports" / "frozen_mechanism_parameters.yaml"
OBSERVATIONS = BENCHMARK / "published_tables" / "sb4_tfwt_observations.csv"
OBT_OBSERVATIONS = BENCHMARK / "published_tables" / "sb4_obt_harvest.csv"
FORCING_MANIFEST = GENERATED / "sb4_forcing_manifest.json"
PROFILE_IDS = ("CONSTANT_REPORTED_MEAN", "SCALED_SB1_OBSERVED_SHAPE")
RUN_IDS = tuple(f"RUN_{index:02d}" for index in range(1, 8))
MECHANISMS = (
    "H0_CURRENT_SINGLE_POOL",
    "H2_SB1_FROZEN",
    "H3_SB1_FROZEN",
)
SOURCE_MECHANISM_IDS = {
    "H0_CURRENT_SINGLE_POOL": "H0_CURRENT_SINGLE_POOL",
    "H2_SB1_FROZEN": "H2_PARALLEL_FAST_SLOW_RESIDUAL",
    "H3_SB1_FROZEN": "H3_REVERSIBLE_FAST_SLOW_EXCHANGE",
}
EXPOSURE_START = pd.Timestamp("2001-08-09T09:30:00+09:00")
EXPOSURE_END = pd.Timestamp("2001-08-09T10:30:00+09:00")
HARVEST = pd.Timestamp("2001-10-05T10:30:00+09:00")
POD_START = pd.Timestamp("2001-07-10T00:00:00+09:00")
EXPOSURE_BODY_WATER_M = 0.0009826
EXPOSURE_BODY_DRY_G_M2 = 477.8
HARVEST_BODY_DRY_G_M2 = 946.3
HARVEST_POD_FRESH_G_M2 = 1069.9
HARVEST_POD_DRY_G_M2 = 340.6
MAXIMUM_HOURS_AFTER_EXPOSURE = 1368.0


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_mechanism_runner() -> Any:
    scripts = SB1_MECHANISM_ROOT / "scripts"
    sys.path.insert(0, str(scripts))
    sys.path.insert(0, str(SB1_MECHANISM_ROOT))
    runner = load_module(
        scripts / "run_mechanism_discrimination.py",
        "sb1_mechanism_runner_for_sb4",
    )
    sb1 = runner.sb1
    sb1.EXPOSURE_START = EXPOSURE_START
    sb1.EXPOSURE_END = EXPOSURE_END
    sb1.HARVEST = HARVEST
    sb1.POD_START = POD_START
    sb1.EXPOSURE_BODY_WATER_M = EXPOSURE_BODY_WATER_M
    sb1.EXPOSURE_BODY_DRY_G_M2 = EXPOSURE_BODY_DRY_G_M2
    sb1.HARVEST_BODY_DRY_G_M2 = HARVEST_BODY_DRY_G_M2
    sb1.HARVEST_POD_FRESH_G_M2 = HARVEST_POD_FRESH_G_M2
    sb1.HARVEST_POD_DRY_G_M2 = HARVEST_POD_DRY_G_M2
    sb1.HARVEST_POD_WATER_M = (
        (HARVEST_POD_FRESH_G_M2 - HARVEST_POD_DRY_G_M2)
        / 1000.0
        / 1000.0
    )
    return runner


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def load_protocol() -> dict[str, Any]:
    protocol = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if not isinstance(protocol, dict):
        raise ValueError("SB4 protocol is not a mapping")
    if not protocol["no_sb4_parameter_refit"]:
        raise ValueError("SB4 parameter refit must be disabled")
    if protocol["sb4_parameter_refit_count"] != 0:
        raise ValueError("SB4 parameter refit count must be zero")
    relative = str(PROTOCOL_PATH.relative_to(ROOT))
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", relative],
        cwd=ROOT,
        check=False,
    ).returncode != 0:
        raise ValueError("SB4 protocol differs from committed HEAD")
    return protocol


def validate_parameter_contract(protocol: dict[str, Any]) -> None:
    source = protocol["sb1_parameter_source"]
    if sha256(SB1_FROZEN) != source["frozen_parameter_file_sha256"]:
        raise ValueError("SB1 frozen parameter file checksum mismatch")
    frozen = yaml.safe_load(SB1_FROZEN.read_text(encoding="utf-8"))
    if (
        frozen["mechanism_parameter_result_hash"]
        != source["mechanism_parameter_result_hash"]
    ):
        raise ValueError("SB1 mechanism parameter-result hash mismatch")
    expected = {
        "H2_SB1_FROZEN": (
            "H2_PARALLEL_FAST_SLOW_RESIDUAL",
            {"slow_capture_fraction": 0.001, "slow_release_rate_s": 1.0e-6},
        ),
        "H3_SB1_FROZEN": (
            "H3_REVERSIBLE_FAST_SLOW_EXCHANGE",
            {"fast_to_slow_rate_s": 1.0e-7, "slow_to_fast_rate_s": 1.0e-6},
        ),
    }
    for target, (source_id, parameters) in expected.items():
        declared = protocol["mechanisms"][target]
        if declared["selected_from_sb4"]:
            raise ValueError(f"{target} was selected from SB4")
        if declared["parameters"] != parameters:
            raise ValueError(f"{target} parameters differ from frozen values")
        if frozen["candidates"][source_id]["parameters"] != parameters:
            raise ValueError(f"{target} does not match SB1 frozen file")
    commit = source["frozen_parameter_commit"]
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT,
        check=True,
    )


def load_forcing_manifest() -> dict[str, Any]:
    manifest = json.loads(FORCING_MANIFEST.read_text(encoding="utf-8"))
    if manifest["total_forcing_files"] != 14:
        raise ValueError("SB4 forcing manifest must contain 14 files")
    if len(manifest["scenarios"]) != 14:
        raise ValueError("SB4 forcing scenario count mismatch")
    for item in manifest["scenarios"].values():
        path = ROOT / item["path"]
        if sha256(path) != item["sha256"]:
            raise ValueError(f"SB4 forcing checksum mismatch: {path}")
        if item["chamber_profile_evidence_class"] != "RECONSTRUCTED":
            raise ValueError("SB4 chamber profile is not marked reconstructed")
    return manifest


def load_forcing(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True)
    frame["time_local"] = frame["time_utc"].dt.tz_convert("Asia/Seoul")
    frame = frame[
        frame["time_local"].between(EXPOSURE_START, HARVEST)
    ].copy()
    frame = frame.sort_values("time_utc").reset_index(drop=True)
    differences = frame["time_utc"].diff().dropna().dt.total_seconds()
    if frame["time_utc"].duplicated().any() or not (differences == 300).all():
        raise ValueError(f"Non-continuous forcing: {path}")
    if set(
        frame.loc[
            frame["phase"] == "CHAMBER_EXPOSURE",
            "chamber_profile_evidence_class",
        ]
    ) != {"RECONSTRUCTED"}:
        raise ValueError(f"Observed-profile spoof detected: {path}")
    return frame


def observations() -> pd.DataFrame:
    frame = pd.read_csv(OBSERVATIONS)
    frame["sample_datetime_utc"] = pd.to_datetime(
        frame["sample_datetime_utc"], utc=True
    )
    return frame


def log_metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    observed = frame["observed_bq_l_water"].to_numpy(float)
    predicted = frame["predicted_bq_l_water"].to_numpy(float)
    if (
        not np.isfinite(observed).all()
        or not np.isfinite(predicted).all()
        or (observed <= 0).any()
        or (predicted <= 0).any()
    ):
        raise ValueError("Metrics require finite positive values")
    residual = np.log10(predicted) - np.log10(observed)
    ratio = predicted / observed
    absolute = np.abs(residual)
    return {
        "log10_rmse": float(np.sqrt(np.mean(residual**2))),
        "log10_mean_bias": float(np.mean(residual)),
        "median_predicted_to_observed_ratio": float(np.median(ratio)),
        "factor_2_coverage": float(np.mean(absolute <= math.log10(2.0))),
        "factor_10_coverage": float(np.mean(absolute <= 1.0)),
        "n": int(len(frame)),
    }


def partitions(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    hours = frame["hours_after_exposure"]
    return {
        "overall": frame,
        "early": frame[hours.isin([0.2, 1.0])],
        "mid": frame[hours.isin([24.0, 120.0, 336.0])],
        "late": frame[hours.isin([768.0, 1368.0])],
    }


def summarize_mass(model: pd.DataFrame, protocol: dict[str, Any]) -> dict[str, Any]:
    numeric = model.select_dtypes(include=[np.number])
    inventory = numeric.filter(regex="_inventory_bq_m2$")
    concentration = numeric.filter(regex="_bq_l_")
    formal = float(model["formal_mass_closure_abs_bq_m2"].max())
    internal_state_sum = float(
        model["internal_transfer_residual_abs_bq_m2"].max()
    )
    internal_ledger = float(
        model.attrs.get("maximum_internal_transfer_ledger_residual_abs_bq_m2", 0.0)
    )
    result = {
        "nan_count": int(numeric.isna().sum().sum()),
        "inf_count": int(np.isinf(numeric.to_numpy()).sum()),
        "negative_inventory_count": int(
            (inventory.to_numpy() < -1.0e-12).sum()
        ),
        "negative_concentration_count": int(
            (concentration.to_numpy() < -1.0e-12).sum()
        ),
        "maximum_formal_mass_closure_abs_bq_m2": formal,
        "maximum_internal_transfer_residual_abs_bq_m2": internal_ledger,
        "maximum_internal_state_sum_roundoff_abs_bq_m2": internal_state_sum,
    }
    criteria = protocol["support_criteria"]
    result["mass_balance_pass"] = bool(
        formal <= criteria["mass_closure_absolute_tolerance_bq_m2"]
        and internal_ledger
        <= criteria["internal_transfer_absolute_tolerance_bq_m2"]
        and result["nan_count"] == 0
        and result["inf_count"] == 0
        and result["negative_inventory_count"] == 0
        and result["negative_concentration_count"] == 0
    )
    return result


def simulate_with_transfer_audit(
    runner: Any,
    forcing: pd.DataFrame,
    source_id: str,
    parameters: dict[str, float],
) -> pd.DataFrame:
    """Audit paired internal fluxes without changing candidate state updates."""
    ledger_residuals = [0.0]
    if source_id == "H2_PARALLEL_FAST_SLOW_RESIDUAL":
        module = runner.parallel_fast_slow
        original = module.transfer

        def audited_transfer(*args: Any, **kwargs: Any) -> Any:
            result = original(*args, **kwargs)
            ledger_residuals.append(
                abs(
                    math.fsum(
                        [
                            -result.capture_bq_m2,
                            result.release_bq_m2,
                            result.capture_bq_m2,
                            -result.release_bq_m2,
                        ]
                    )
                )
            )
            return result

    elif source_id == "H3_REVERSIBLE_FAST_SLOW_EXCHANGE":
        module = runner.reversible_fast_slow
        original = module.transfer

        def audited_transfer(*args: Any, **kwargs: Any) -> Any:
            result = original(*args, **kwargs)
            ledger_residuals.append(
                abs(
                    math.fsum(
                        [
                            -result.fast_to_slow_bq_m2,
                            result.slow_to_fast_bq_m2,
                            result.fast_to_slow_bq_m2,
                            -result.slow_to_fast_bq_m2,
                        ]
                    )
                )
            )
            return result

    else:
        model = runner.simulate(
            forcing,
            source_id,
            parameters,
            MAXIMUM_HOURS_AFTER_EXPOSURE,
        )
        model.attrs[
            "maximum_internal_transfer_ledger_residual_abs_bq_m2"
        ] = 0.0
        return model

    module.transfer = audited_transfer
    try:
        model = runner.simulate(
            forcing,
            source_id,
            parameters,
            MAXIMUM_HOURS_AFTER_EXPOSURE,
        )
    finally:
        module.transfer = original
    model.attrs[
        "maximum_internal_transfer_ledger_residual_abs_bq_m2"
    ] = max(ledger_residuals)
    return model


def early_check(
    reference: pd.DataFrame,
    candidate: pd.DataFrame,
    criteria: dict[str, Any],
) -> tuple[bool, float, float]:
    candidate_ratio = (
        candidate["predicted_bq_l_water"].to_numpy(float)
        / candidate["observed_bq_l_water"].to_numpy(float)
    )
    factor_pass = bool(
        np.all(
            (candidate_ratio >= 1.0 / criteria["early_prediction_factor_limit"])
            & (candidate_ratio <= criteria["early_prediction_factor_limit"])
        )
    )
    candidate_error = np.abs(
        np.log10(candidate["predicted_bq_l_water"].to_numpy(float))
        - np.log10(candidate["observed_bq_l_water"].to_numpy(float))
    )
    reference_error = np.abs(
        np.log10(reference["predicted_bq_l_water"].to_numpy(float))
        - np.log10(reference["observed_bq_l_water"].to_numpy(float))
    )
    worsening = float(np.max(candidate_error - reference_error))
    return (
        bool(
            factor_pass
            or worsening
            <= criteria["early_log10_error_worsening_maximum_dex"]
        ),
        float(candidate_ratio.min()),
        float(candidate_ratio.max()),
    )


def main() -> int:
    protocol = load_protocol()
    validate_parameter_contract(protocol)
    forcing_manifest = load_forcing_manifest()
    runner = load_mechanism_runner()
    observed = observations()
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    prediction_rows: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    mass_rows: list[dict[str, Any]] = []
    obt_rows: list[dict[str, Any]] = []
    sampled_lookup: dict[tuple[str, str, str], pd.DataFrame] = {}
    metric_lookup: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    mass_lookup: dict[tuple[str, str, str], dict[str, Any]] = {}

    for profile_id in PROFILE_IDS:
        for run_id in RUN_IDS:
            forcing_item = forcing_manifest["scenarios"][
                f"{profile_id}:{run_id}"
            ]
            forcing = load_forcing(ROOT / forcing_item["path"])
            for mechanism_id in MECHANISMS:
                source_id = SOURCE_MECHANISM_IDS[mechanism_id]
                parameters = protocol["mechanisms"][mechanism_id]["parameters"]
                model = simulate_with_transfer_audit(
                    runner,
                    forcing,
                    source_id,
                    parameters,
                )
                sampled = runner.sample_predictions(model, observed)
                sampled.insert(0, "run_id", run_id)
                sampled.insert(0, "profile_id", profile_id)
                sampled.insert(0, "mechanism_id", mechanism_id)
                sampled["selected_from_sb4"] = False
                sampled["sb4_parameter_refit_count"] = 0
                prediction_rows.append(sampled)
                sampled_lookup[(mechanism_id, profile_id, run_id)] = sampled
                for compartment in ("plant_body", "pods"):
                    compartment_frame = sampled[
                        sampled["compartment"] == compartment
                    ]
                    for partition_id, partition in partitions(
                        compartment_frame
                    ).items():
                        values = log_metrics(partition)
                        metric_lookup[
                            (
                                mechanism_id,
                                profile_id,
                                run_id,
                                compartment,
                                partition_id,
                            )
                        ] = values
                        metric_rows.append(
                            {
                                "mechanism_id": mechanism_id,
                                "profile_id": profile_id,
                                "run_id": run_id,
                                "compartment": compartment,
                                "partition": partition_id,
                                **values,
                            }
                        )
                mass = summarize_mass(model, protocol)
                mass_lookup[(mechanism_id, profile_id, run_id)] = mass
                mass_rows.append(
                    {
                        "mechanism_id": mechanism_id,
                        "profile_id": profile_id,
                        "run_id": run_id,
                        **mass,
                    }
                )
                final = model.iloc[-1]
                obt_rows.append(
                    {
                        "mechanism_id": mechanism_id,
                        "profile_id": profile_id,
                        "run_id": run_id,
                        "plant_body_obt_bq_l_combustion_water": float(
                            final[
                                "plant_body_obt_bq_l_combustion_water"
                            ]
                        ),
                        "pods_obt_bq_l_combustion_water": float(
                            final["pods_obt_bq_l_combustion_water"]
                        ),
                        "obt_role": "CONSISTENCY_CHECK_ONLY",
                    }
                )

    predictions = pd.concat(prediction_rows, ignore_index=True)
    metrics = pd.DataFrame(metric_rows)
    mass = pd.DataFrame(mass_rows)
    obt = pd.DataFrame(obt_rows)
    predictions.to_csv(REPORTS / "sb4_transfer_predictions.csv", index=False)
    metrics.to_csv(REPORTS / "sb4_transfer_metrics.csv", index=False)
    mass.to_csv(REPORTS / "sb4_transfer_mass_balance.csv", index=False)
    obt.to_csv(REPORTS / "sb4_transfer_obt_consistency.csv", index=False)

    criteria = protocol["support_criteria"]
    robustness_rows: list[dict[str, Any]] = []
    candidate_results: dict[str, Any] = {}
    obt_observed = pd.read_csv(OBT_OBSERVATIONS).set_index("compartment")
    observed_body_obt = float(
        obt_observed.loc[
            "plant_body_average", "obt_bq_l_combustion_water"
        ]
    )
    observed_pods_obt = float(
        obt_observed.loc["pods_average", "obt_bq_l_combustion_water"]
    )

    for mechanism_id in MECHANISMS[1:]:
        profile_results: dict[str, Any] = {}
        all_mass_pass = True
        for profile_id in PROFILE_IDS:
            forcing_passes = 0
            scenario_results: dict[str, Any] = {}
            for run_id in RUN_IDS:
                reference_overall = metric_lookup[
                    (
                        "H0_CURRENT_SINGLE_POOL",
                        profile_id,
                        run_id,
                        "plant_body",
                        "overall",
                    )
                ]
                candidate_overall = metric_lookup[
                    (
                        mechanism_id,
                        profile_id,
                        run_id,
                        "plant_body",
                        "overall",
                    )
                ]
                reference_late = metric_lookup[
                    (
                        "H0_CURRENT_SINGLE_POOL",
                        profile_id,
                        run_id,
                        "plant_body",
                        "late",
                    )
                ]
                candidate_late = metric_lookup[
                    (
                        mechanism_id,
                        profile_id,
                        run_id,
                        "plant_body",
                        "late",
                    )
                ]
                reference_early = sampled_lookup[
                    ("H0_CURRENT_SINGLE_POOL", profile_id, run_id)
                ]
                reference_early = reference_early[
                    (reference_early["compartment"] == "plant_body")
                    & reference_early["hours_after_exposure"].isin([0.2, 1.0])
                ]
                candidate_early = sampled_lookup[
                    (mechanism_id, profile_id, run_id)
                ]
                candidate_early = candidate_early[
                    (candidate_early["compartment"] == "plant_body")
                    & candidate_early["hours_after_exposure"].isin([0.2, 1.0])
                ]
                early_pass, early_min, early_max = early_check(
                    reference_early, candidate_early, criteria
                )
                overall_improvement = (
                    reference_overall["log10_rmse"]
                    - candidate_overall["log10_rmse"]
                )
                late_improvement = (
                    reference_late["log10_rmse"]
                    - candidate_late["log10_rmse"]
                )
                scenario_mass = mass_lookup[
                    (mechanism_id, profile_id, run_id)
                ]
                scenario_pass = bool(
                    overall_improvement
                    >= criteria[
                        "overall_log10_rmse_improvement_minimum_dex"
                    ]
                    and late_improvement
                    >= criteria["late_log10_rmse_improvement_minimum_dex"]
                    and early_pass
                    and scenario_mass["mass_balance_pass"]
                )
                forcing_passes += int(scenario_pass)
                all_mass_pass &= bool(scenario_mass["mass_balance_pass"])
                scenario_results[run_id] = {
                    "overall_log10_rmse_improvement_dex": overall_improvement,
                    "late_log10_rmse_improvement_dex": late_improvement,
                    "early_pass": early_pass,
                    "early_min_predicted_to_observed_ratio": early_min,
                    "early_max_predicted_to_observed_ratio": early_max,
                    "mass_balance_pass": scenario_mass["mass_balance_pass"],
                    "frozen_transfer_thresholds_pass": scenario_pass,
                }
                robustness_rows.append(
                    {
                        "mechanism_id": mechanism_id,
                        "profile_id": profile_id,
                        "run_id": run_id,
                        **scenario_results[run_id],
                    }
                )

            primary = scenario_results["RUN_01"]
            reference_pods = metric_lookup[
                (
                    "H0_CURRENT_SINGLE_POOL",
                    profile_id,
                    "RUN_01",
                    "pods",
                    "overall",
                )
            ]
            candidate_pods = metric_lookup[
                (
                    mechanism_id,
                    profile_id,
                    "RUN_01",
                    "pods",
                    "overall",
                )
            ]
            pods_worsening = (
                candidate_pods["log10_rmse"]
                - reference_pods["log10_rmse"]
            )
            primary_obt = obt[
                (obt["profile_id"] == profile_id)
                & (obt["run_id"] == "RUN_01")
            ].set_index("mechanism_id")
            h0_body_error = abs(
                math.log10(
                    primary_obt.loc[
                        "H0_CURRENT_SINGLE_POOL",
                        "plant_body_obt_bq_l_combustion_water",
                    ]
                    / observed_body_obt
                )
            )
            candidate_body_error = abs(
                math.log10(
                    primary_obt.loc[
                        mechanism_id,
                        "plant_body_obt_bq_l_combustion_water",
                    ]
                    / observed_body_obt
                )
            )
            h0_pods_error = abs(
                math.log10(
                    primary_obt.loc[
                        "H0_CURRENT_SINGLE_POOL",
                        "pods_obt_bq_l_combustion_water",
                    ]
                    / observed_pods_obt
                )
            )
            candidate_pods_error = abs(
                math.log10(
                    primary_obt.loc[
                        mechanism_id,
                        "pods_obt_bq_l_combustion_water",
                    ]
                    / observed_pods_obt
                )
            )
            obt_worsening = max(
                candidate_body_error - h0_body_error,
                candidate_pods_error - h0_pods_error,
            )
            profile_supported = bool(
                primary["overall_log10_rmse_improvement_dex"]
                >= criteria["overall_log10_rmse_improvement_minimum_dex"]
                and primary["late_log10_rmse_improvement_dex"]
                >= criteria["late_log10_rmse_improvement_minimum_dex"]
                and primary["early_pass"]
                and forcing_passes
                >= criteria["forcing_scenarios_required_per_profile"]
                and pods_worsening
                <= criteria["pods_log10_rmse_worsening_maximum_dex"]
                and obt_worsening
                <= criteria[
                    "obt_absolute_log10_error_worsening_maximum_dex"
                ]
            )
            profile_results[profile_id] = {
                "primary_overall_log10_rmse_improvement_dex": primary[
                    "overall_log10_rmse_improvement_dex"
                ],
                "primary_late_log10_rmse_improvement_dex": primary[
                    "late_log10_rmse_improvement_dex"
                ],
                "primary_early_pass": primary["early_pass"],
                "forcing_pass_count": forcing_passes,
                "pods_log10_rmse_worsening_dex": pods_worsening,
                "obt_absolute_log10_error_worsening_dex": obt_worsening,
                "profile_supported": profile_supported,
            }
        supported = bool(
            all(
                result["profile_supported"]
                for result in profile_results.values()
            )
            and all_mass_pass
        )
        candidate_results[mechanism_id] = {
            "parameters": protocol["mechanisms"][mechanism_id]["parameters"],
            "parameter_source_commit": protocol["sb1_parameter_source"][
                "frozen_parameter_commit"
            ],
            "selected_from_sb4": False,
            "sb4_parameter_refit_count": 0,
            "profiles": profile_results,
            "all_mass_balance_pass": all_mass_pass,
            "supported": supported,
            "status": (
                "SUPPORTED_FOR_BOUNDED_CROSS_EXPERIMENT_DESIGN"
                if supported
                else "NOT_SUPPORTED_BY_FROZEN_TRANSFER_CRITERIA"
            ),
        }

    h2_supported = candidate_results["H2_SB1_FROZEN"]["supported"]
    h3_supported = candidate_results["H3_SB1_FROZEN"]["supported"]
    if h2_supported and h3_supported:
        transfer_status = "MULTIPLE_SLOW_MECHANISMS_TRANSFER_SUPPORTED"
        design_recommendation = "BOUNDED_COMPARATIVE_DESIGN_REVIEW_ONLY"
    elif h2_supported:
        transfer_status = "H2_PARALLEL_RESIDUAL_TRANSFER_SUPPORTED"
        design_recommendation = "ADDITIONAL_SLOW_CAPTURE_CONSTRAINT_REQUIRED"
    elif h3_supported:
        transfer_status = "H3_REVERSIBLE_EXCHANGE_TRANSFER_SUPPORTED"
        design_recommendation = "LIMITED_V3_DESIGN_REVIEW_NOT_IMPLEMENTATION"
    else:
        transfer_status = "H2_H3_NOT_TRANSFERABLE"
        design_recommendation = "NOT_READY"

    robustness = pd.DataFrame(robustness_rows)
    robustness.to_csv(
        REPORTS / "sb4_transfer_forcing_robustness.csv", index=False
    )
    protocol_commit = git_output(
        "log", "-1", "--format=%H", "--", str(PROTOCOL_PATH.relative_to(ROOT))
    )
    result = {
        "protocol_id": protocol["protocol_id"],
        "protocol_commit": protocol_commit,
        "parameter_source_commit": protocol["sb1_parameter_source"][
            "frozen_parameter_commit"
        ],
        "mechanism_parameter_result_hash": protocol[
            "sb1_parameter_source"
        ]["mechanism_parameter_result_hash"],
        "sb4_parameter_refit_count": 0,
        "selected_from_sb4": False,
        "run_count": 42,
        "candidate_results": candidate_results,
        "sb4_transfer_status": transfer_status,
        "formal_v3_design_recommendation": design_recommendation,
        "formal_v3_physics": "NOT_STARTED",
        "empirical_validation_claim": False,
        "production_gate_eligible": False,
        "v3_physics_start_gate": (
            "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        ),
    }
    schema = json.loads(
        (
            BENCHMARK / "schemas" / "sb4_transfer_result.schema.json"
        ).read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(schema).validate(result)
    (REPORTS / "sb4_transfer_selection.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print("SB4_TRANSFER_RUN_COUNT = 42")
    print("SB4_PARAMETER_REFIT_COUNT = 0")
    print(f"SB4_TRANSFER_STATUS = {transfer_status}")
    print(f"FORMAL_V3_DESIGN_RECOMMENDATION = {design_recommendation}")
    print("V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"SB4 transfer test failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
