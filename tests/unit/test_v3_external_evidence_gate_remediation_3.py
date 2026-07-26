from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

import scripts.verify_v3_physics_start_gate as gate
from tests.helpers.v3_gate_fixture import build_gate_repository, git, write_yaml
from validation.parameter_contract import (
    ParameterContractError,
    canonical_sha256,
    canonicalize_parameter_contract,
    parameter_result_hash,
    validate_calibrated_parameters,
)


BLOCKED = "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _commit(root: Path, message: str, *paths: Path) -> None:
    git(
        root,
        "add",
        *(path.relative_to(root).as_posix() for path in paths),
    )
    git(root, "commit", "-q", "-m", message)


def _evaluate(root: Path, config: Path) -> dict:
    return gate.evaluate_gate_for_test(config, repository_root=root)


def _assert_blocked(result: dict) -> None:
    assert result["status"] == BLOCKED
    assert result["final_gate"] != "READY_FOR_BOUNDED_V3_PHYSICS"


def _parameter_hash_without_contract(parameters: dict) -> str:
    canonical = [
        {
            "name": name,
            "value": float(value["value"]),
            "unit": value["unit"],
            "transform": value["transform"],
        }
        for name, value in sorted(parameters.items())
    ]
    return canonical_sha256(canonical)


def _consistent_rehash(
    root: Path,
    paths: dict[str, Path],
    parameters: dict,
) -> None:
    result_hash = _parameter_hash_without_contract(parameters)
    calibration = _load(paths["calibration"])
    calibration["parameters"] = parameters
    calibration["parameter_result_hash"] = result_hash
    write_yaml(paths["calibration"], calibration)

    identifiability = _load(paths["identifiability"])
    identifiability["parameter_result_hash"] = result_hash
    identifiability["parameter_results"] = {
        name: {
            "status": "IDENTIFIABLE",
            "lower_interval": max(float(value["value"]) - 0.01, 0.0),
            "upper_interval": float(value["value"]) + 0.01,
            "boundary_hit": False,
        }
        for name, value in parameters.items()
    }
    identifiability["boundary_hits"] = []
    write_yaml(paths["identifiability"], identifiability)

    holdout = _load(paths["holdout"])
    holdout["parameters"] = parameters
    holdout["parameter_result_hash"] = result_hash
    write_yaml(paths["holdout"], holdout)
    _commit(
        root,
        "Apply consistently rehashed parameter attack",
        paths["calibration"],
        paths["identifiability"],
        paths["holdout"],
    )


def _valid_contract(
    *,
    lower: float = 0.0,
    upper: float = 1.0,
    lower_inclusive: bool = True,
    upper_inclusive: bool = True,
) -> list[dict]:
    return [
        {
            "name": "rate",
            "unit": "s-1",
            "lower_bound": lower,
            "upper_bound": upper,
            "lower_inclusive": lower_inclusive,
            "upper_inclusive": upper_inclusive,
            "transform": "IDENTITY",
        }
    ]


def _valid_parameter(value: object = 0.5) -> dict:
    return {
        "rate": {
            "value": value,
            "unit": "s-1",
            "transform": "IDENTITY",
        }
    }


def _mutate_calibration_parameter(
    tmp_path: Path,
    *,
    name: str = "exchange_rate",
    field: str = "value",
    value: object,
) -> dict:
    config, paths = build_gate_repository(tmp_path)
    calibration = _load(paths["calibration"])
    calibration["parameters"][name][field] = value
    write_yaml(paths["calibration"], calibration)
    _commit(tmp_path, "Mutate calibration parameter", paths["calibration"])
    return _evaluate(tmp_path, config)


def test_rejects_extra_unregistered_parameter(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    parameters = deepcopy(_load(paths["calibration"])["parameters"])
    parameters["unregistered_rate"] = {
        "value": 0.3,
        "unit": "s-1",
        "transform": "IDENTITY",
    }
    _consistent_rehash(tmp_path, paths, parameters)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_missing_preregistered_parameter(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    parameters = deepcopy(_load(paths["calibration"])["parameters"])
    parameters.pop("turnover_rate")
    _consistent_rehash(tmp_path, paths, parameters)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_renamed_parameter(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    parameters = deepcopy(_load(paths["calibration"])["parameters"])
    parameters["renamed_rate"] = parameters.pop("turnover_rate")
    _consistent_rehash(tmp_path, paths, parameters)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_case_variant_parameter_name(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    parameters = deepcopy(_load(paths["calibration"])["parameters"])
    parameters["Turnover_rate"] = parameters.pop("turnover_rate")
    _consistent_rehash(tmp_path, paths, parameters)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_unicode_parameter_name(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    parameters = deepcopy(_load(paths["calibration"])["parameters"])
    parameters["turnover_ｒate"] = parameters.pop("turnover_rate")
    _consistent_rehash(tmp_path, paths, parameters)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_whitespace_parameter_name(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    parameters = deepcopy(_load(paths["calibration"])["parameters"])
    parameters["turnover rate"] = parameters.pop("turnover_rate")
    _consistent_rehash(tmp_path, paths, parameters)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_duplicate_parameter_contract_name() -> None:
    contract = _valid_contract() * 2
    with pytest.raises(ParameterContractError, match="duplicate"):
        canonicalize_parameter_contract(contract)


def test_accepts_same_parameter_names_in_different_order(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    preregistration = _load(paths["preregistration_file"])
    calibration = _load(paths["calibration"])
    assert [item["name"] for item in preregistration["parameter_contract"]] != list(
        calibration["parameters"]
    )
    assert _evaluate(tmp_path, config)["status"] == "READY_FOR_BOUNDED_V3_PHYSICS"


def test_rejects_boolean_parameter_value(tmp_path: Path) -> None:
    _assert_blocked(
        _mutate_calibration_parameter(tmp_path, value=True)
    )


def test_rejects_string_parameter_value(tmp_path: Path) -> None:
    _assert_blocked(
        _mutate_calibration_parameter(tmp_path, value="0.2")
    )


def test_rejects_null_parameter_value(tmp_path: Path) -> None:
    _assert_blocked(_mutate_calibration_parameter(tmp_path, value=None))


def test_rejects_nan_parameter_value(tmp_path: Path) -> None:
    _assert_blocked(_mutate_calibration_parameter(tmp_path, value=float("nan")))


def test_rejects_positive_infinity_parameter_value(tmp_path: Path) -> None:
    _assert_blocked(_mutate_calibration_parameter(tmp_path, value=float("inf")))


def test_rejects_negative_infinity_parameter_value(tmp_path: Path) -> None:
    _assert_blocked(_mutate_calibration_parameter(tmp_path, value=float("-inf")))


def test_rejects_parameter_below_frozen_bound(tmp_path: Path) -> None:
    _assert_blocked(_mutate_calibration_parameter(tmp_path, value=-0.1))


def test_rejects_parameter_above_frozen_bound(tmp_path: Path) -> None:
    _assert_blocked(_mutate_calibration_parameter(tmp_path, value=1.1))


def test_accepts_inclusive_lower_bound() -> None:
    contract = canonicalize_parameter_contract(_valid_contract())
    result = validate_calibrated_parameters(
        contract,
        _valid_parameter(0.0),
        artifact_label="test",
    )
    assert result[0]["value"] == 0.0


def test_accepts_inclusive_upper_bound() -> None:
    contract = canonicalize_parameter_contract(_valid_contract())
    result = validate_calibrated_parameters(
        contract,
        _valid_parameter(1.0),
        artifact_label="test",
    )
    assert result[0]["value"] == 1.0


def test_rejects_exclusive_lower_boundary() -> None:
    contract = canonicalize_parameter_contract(
        _valid_contract(lower_inclusive=False)
    )
    with pytest.raises(ParameterContractError, match="outside"):
        validate_calibrated_parameters(
            contract,
            _valid_parameter(0.0),
            artifact_label="test",
        )


def test_rejects_exclusive_upper_boundary() -> None:
    contract = canonicalize_parameter_contract(
        _valid_contract(upper_inclusive=False)
    )
    with pytest.raises(ParameterContractError, match="outside"):
        validate_calibrated_parameters(
            contract,
            _valid_parameter(1.0),
            artifact_label="test",
        )


def test_rejects_parameter_unit_mismatch(tmp_path: Path) -> None:
    _assert_blocked(
        _mutate_calibration_parameter(
            tmp_path,
            field="unit",
            value="h-1",
        )
    )


def test_rejects_missing_parameter_unit(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    calibration = _load(paths["calibration"])
    calibration["parameters"]["exchange_rate"].pop("unit")
    write_yaml(paths["calibration"], calibration)
    _commit(tmp_path, "Remove calibration unit", paths["calibration"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_parameter_transform_mismatch(tmp_path: Path) -> None:
    _assert_blocked(
        _mutate_calibration_parameter(
            tmp_path,
            field="transform",
            value="LOG",
        )
    )


def test_rejects_unknown_parameter_transform(tmp_path: Path) -> None:
    _assert_blocked(
        _mutate_calibration_parameter(
            tmp_path,
            field="transform",
            value="CUSTOM_EVAL",
        )
    )


def test_rejects_calibration_contract_hash_mismatch(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    calibration = _load(paths["calibration"])
    calibration["parameter_contract_hash"] = "0" * 64
    write_yaml(paths["calibration"], calibration)
    _commit(tmp_path, "Corrupt calibration contract hash", paths["calibration"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_identifiability_missing_parameter(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    artifact = _load(paths["identifiability"])
    artifact["parameter_results"].pop("turnover_rate")
    write_yaml(paths["identifiability"], artifact)
    _commit(tmp_path, "Omit identifiability parameter", paths["identifiability"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_identifiability_extra_parameter(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    artifact = _load(paths["identifiability"])
    artifact["parameter_results"]["extra_rate"] = {
        "status": "IDENTIFIABLE",
        "lower_interval": 0.0,
        "upper_interval": 1.0,
        "boundary_hit": False,
    }
    write_yaml(paths["identifiability"], artifact)
    _commit(tmp_path, "Add identifiability parameter", paths["identifiability"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_identifiability_renamed_parameter(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    artifact = _load(paths["identifiability"])
    artifact["parameter_results"]["renamed_rate"] = artifact[
        "parameter_results"
    ].pop("turnover_rate")
    write_yaml(paths["identifiability"], artifact)
    _commit(tmp_path, "Rename identifiability parameter", paths["identifiability"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_identifiability_parameter_hash_mismatch(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    artifact = _load(paths["identifiability"])
    artifact["parameter_result_hash"] = "0" * 64
    write_yaml(paths["identifiability"], artifact)
    _commit(tmp_path, "Corrupt identifiability result hash", paths["identifiability"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_identifiability_contract_hash_mismatch(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    artifact = _load(paths["identifiability"])
    artifact["parameter_contract_hash"] = "0" * 64
    write_yaml(paths["identifiability"], artifact)
    _commit(tmp_path, "Corrupt identifiability contract hash", paths["identifiability"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_missing_parameter_identifiability_status(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    artifact = _load(paths["identifiability"])
    artifact["parameter_results"]["exchange_rate"].pop("status")
    write_yaml(paths["identifiability"], artifact)
    _commit(tmp_path, "Remove identifiability status", paths["identifiability"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_holdout_parameter_contract_hash_mismatch(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    artifact = _load(paths["holdout"])
    artifact["parameter_contract_hash"] = "0" * 64
    write_yaml(paths["holdout"], artifact)
    _commit(tmp_path, "Corrupt holdout contract hash", paths["holdout"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_holdout_parameter_result_hash_mismatch(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    artifact = _load(paths["holdout"])
    artifact["parameter_result_hash"] = "0" * 64
    write_yaml(paths["holdout"], artifact)
    _commit(tmp_path, "Corrupt holdout result hash", paths["holdout"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_holdout_using_altered_parameter_set(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    artifact = _load(paths["holdout"])
    artifact["parameters"]["extra_rate"] = {
        "value": 0.1,
        "unit": "s-1",
        "transform": "IDENTITY",
    }
    write_yaml(paths["holdout"], artifact)
    _commit(tmp_path, "Alter holdout parameter set", paths["holdout"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_holdout_using_same_values_under_new_names(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    artifact = _load(paths["holdout"])
    artifact["parameters"]["new_exchange_rate"] = artifact["parameters"].pop(
        "exchange_rate"
    )
    write_yaml(paths["holdout"], artifact)
    _commit(tmp_path, "Rename holdout parameter", paths["holdout"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_consistently_rehashed_unregistered_parameter_chain(
    tmp_path: Path,
) -> None:
    config, paths = build_gate_repository(tmp_path)
    parameters = {
        "unregistered_rate": {
            "value": 0.2,
            "unit": "s-1",
            "transform": "IDENTITY",
        }
    }
    _consistent_rehash(tmp_path, paths, parameters)
    result = _evaluate(tmp_path, config)
    _assert_blocked(result)
    assert (
        result["final_gate"]
        == "BLOCKED_CALIBRATION_PARAMETER_SET_NOT_FROZEN"
    )


def test_test_only_parameter_contract_positive_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, paths = build_gate_repository(tmp_path)
    isolated = _evaluate(tmp_path, config)
    assert isolated["status"] == "READY_FOR_BOUNDED_V3_PHYSICS"
    assert isolated["diagnostics"]["PARAMETER_CONTRACT_HASH_STATUS"] == "PASS"
    assert isolated["diagnostics"]["HOLDOUT_PARAMETER_CONTRACT_STATUS"] == "PASS"
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    _assert_blocked(gate.evaluate_gate(config))
