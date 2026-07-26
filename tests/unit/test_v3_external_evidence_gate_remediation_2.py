from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import pytest
import yaml

import scripts.verify_v3_physics_start_gate as gate
from tests.helpers.v3_gate_fixture import (
    build_gate_repository,
    git,
    write_yaml,
)
from validation.evidence_validation import calculate_sha256
from validation.holdout_verdict import derive_holdout_verdict


BLOCKED = "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def _evaluate(root: Path, config: Path, *, hooks=None) -> dict:
    return gate.evaluate_gate_for_test(
        config,
        repository_root=root,
        hooks=hooks,
    )


def _assert_blocked(result: dict) -> None:
    assert result["status"] == BLOCKED
    assert result["final_gate"] != "READY_FOR_BOUNDED_V3_PHYSICS"


def _mutate_trusted_registry(
    root: Path,
    transform: Callable[[dict], None],
    *,
    align_remote: bool = True,
) -> None:
    current = git(root, "branch", "--show-current")
    git(root, "switch", "-q", "main")
    path = root / gate.TRUSTED_POLICY_PATH
    registry = yaml.safe_load(path.read_text(encoding="utf-8"))
    transform(registry)
    write_yaml(path, registry)
    git(root, "add", path.relative_to(root).as_posix())
    git(root, "commit", "-q", "-m", "Mutate trusted policy for attack")
    if align_remote:
        git(
            root,
            "update-ref",
            gate.TRUSTED_REMOTE_REF,
            git(root, "rev-parse", "HEAD"),
        )
    git(root, "switch", "-q", current)


def _set_protected_refs_to_approval_commit(root: Path, paths: dict[str, Path]) -> None:
    approval_commit = git(
        root,
        "log",
        "-1",
        "--format=%H",
        "--",
        paths["approval_record"].relative_to(root).as_posix(),
    )
    git(root, "update-ref", gate.TRUSTED_LOCAL_REF, approval_commit)
    git(root, "update-ref", gate.TRUSTED_REMOTE_REF, approval_commit)


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_rejects_no_trusted_registry_entry(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    _set_protected_refs_to_approval_commit(tmp_path, paths)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_bundle_self_declared_empirical_origin(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    _set_protected_refs_to_approval_commit(tmp_path, paths)
    bundle = _load(paths["bundle"])
    bundle["test_only"] = False
    bundle["artifact_purpose"] = "EMPIRICAL_VALIDATION"
    bundle["origin_class"] = "CONTROLLED_EXPERIMENT"
    write_yaml(paths["bundle"], bundle)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_registry_entry_only_in_working_tree(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    _set_protected_refs_to_approval_commit(tmp_path, paths)
    paths["registry"].write_text(
        paths["registry"].read_text(encoding="utf-8") + "# uncommitted\n",
        encoding="utf-8",
    )
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_registry_entry_only_on_feature_branch(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    _set_protected_refs_to_approval_commit(tmp_path, paths)
    assert git(tmp_path, "branch", "--show-current") == "evidence-chain"
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_uncommitted_registry_change(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    _set_protected_refs_to_approval_commit(tmp_path, paths)
    registry = _load(paths["registry"])
    registry["entries"][0]["test_only"] = False
    write_yaml(paths["registry"], registry)
    assert git(tmp_path, "status", "--porcelain", "--", paths["registry"].relative_to(tmp_path).as_posix())
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_registry_raw_manifest_hash_mismatch(tmp_path: Path) -> None:
    config, _ = build_gate_repository(tmp_path)
    _mutate_trusted_registry(
        tmp_path,
        lambda registry: registry["entries"][0].update(
            raw_manifest_sha256="0" * 64
        ),
    )
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_registry_evidence_type_mismatch(tmp_path: Path) -> None:
    config, _ = build_gate_repository(tmp_path)
    _mutate_trusted_registry(
        tmp_path,
        lambda registry: registry["entries"][0].update(
            evidence_type="MATCHED_FIELD_OBSERVATION"
        ),
    )
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_registry_test_only_entry_in_production(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config, _ = build_gate_repository(tmp_path)
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    _assert_blocked(gate.evaluate_gate(config))


def test_rejects_registry_pending_entry(tmp_path: Path) -> None:
    config, _ = build_gate_repository(tmp_path)
    _mutate_trusted_registry(
        tmp_path,
        lambda registry: registry["entries"][0].update(
            empirical_eligibility="PENDING"
        ),
    )
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_registry_rejected_entry(tmp_path: Path) -> None:
    config, _ = build_gate_repository(tmp_path)
    _mutate_trusted_registry(
        tmp_path,
        lambda registry: registry["entries"][0].update(
            empirical_eligibility="REJECTED"
        ),
    )
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_registry_approval_commit_not_in_trusted_main(tmp_path: Path) -> None:
    config, _ = build_gate_repository(tmp_path)
    feature_head = git(tmp_path, "rev-parse", "HEAD")
    _mutate_trusted_registry(
        tmp_path,
        lambda registry: registry["entries"][0]["approval"].update(
            approval_commit=feature_head
        ),
    )
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_registry_approval_after_preregistration(tmp_path: Path) -> None:
    config, _ = build_gate_repository(tmp_path)
    preregistration_commit = git(
        tmp_path,
        "log",
        "--format=%H",
        "--reverse",
        "--",
        "validation/preregistration/gate_fixture.yaml",
    ).splitlines()[0]
    _mutate_trusted_registry(
        tmp_path,
        lambda registry: registry["entries"][0]["approval"].update(
            approval_commit=preregistration_commit
        ),
    )
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_local_main_remote_main_mismatch(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    approval_commit = git(
        tmp_path,
        "log",
        "-1",
        "--format=%H",
        "--",
        paths["approval_record"].relative_to(tmp_path).as_posix(),
    )
    git(tmp_path, "update-ref", gate.TRUSTED_REMOTE_REF, approval_commit)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_attempted_policy_path_override(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    value = _load(config)
    value["trusted_registry_path"] = paths["registry"].relative_to(tmp_path).as_posix()
    write_yaml(config, value)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_same_size_raw_replacement(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)

    def attack(_: dict) -> None:
        original = paths["raw_file"].read_text(encoding="utf-8")
        replacement = original.replace("CAL_001,1", "CAL_001,9")
        assert len(replacement) == len(original)
        paths["raw_file"].write_text(replacement, encoding="utf-8")

    result = _evaluate(
        tmp_path,
        config,
        hooks={"before_final_source_recheck": attack},
    )
    _assert_blocked(result)
    assert result["final_gate"] == "BLOCKED_EVIDENCE_CHANGED_AFTER_SNAPSHOT"


def test_rejects_raw_rename_replacement(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)

    def attack(_: dict) -> None:
        replacement = paths["raw_file"].with_suffix(".replacement")
        replacement.write_bytes(paths["raw_file"].read_bytes())
        os.replace(replacement, paths["raw_file"])

    result = _evaluate(
        tmp_path,
        config,
        hooks={"before_final_source_recheck": attack},
    )
    _assert_blocked(result)


def test_rejects_raw_in_place_mutation(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)

    def attack(_: dict) -> None:
        with paths["raw_file"].open("r+b") as stream:
            stream.seek(0)
            stream.write(b"X")
            stream.flush()
            os.fsync(stream.fileno())

    _assert_blocked(
        _evaluate(
            tmp_path,
            config,
            hooks={"before_final_source_recheck": attack},
        )
    )


def test_rejects_symlink_target_switch(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)

    def attack(_: dict) -> None:
        target = paths["raw_file"].with_suffix(".target")
        target.write_bytes(paths["raw_file"].read_bytes())
        paths["raw_file"].unlink()
        paths["raw_file"].symlink_to(target)

    _assert_blocked(
        _evaluate(
            tmp_path,
            config,
            hooks={"before_final_source_recheck": attack},
        )
    )


def test_rejects_holdout_result_replacement(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)

    def attack(_: dict) -> None:
        original = paths["holdout"].read_text(encoding="utf-8")
        paths["holdout"].write_text(
            original.replace("declared_verdict: PASS", "declared_verdict: FAIL"),
            encoding="utf-8",
        )

    _assert_blocked(
        _evaluate(
            tmp_path,
            config,
            hooks={"before_final_source_recheck": attack},
        )
    )


def test_rejects_result_file_replacement(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)

    def attack(_: dict) -> None:
        paths["model_output"].write_text(
            "sample_id,prediction\nHOLD_001,9\n",
            encoding="utf-8",
        )

    _assert_blocked(
        _evaluate(
            tmp_path,
            config,
            hooks={"before_final_source_recheck": attack},
        )
    )


def test_rejects_evidence_change_during_snapshot_copy(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    attacked = False

    def attack(context: dict) -> None:
        nonlocal attacked
        if context["label"] == "raw_observations" and not attacked:
            attacked = True
            paths["raw_file"].write_text(
                paths["raw_file"].read_text(encoding="utf-8").replace(
                    "CAL_001,1",
                    "CAL_001,9",
                ),
                encoding="utf-8",
            )

    result = _evaluate(
        tmp_path,
        config,
        hooks={"during_snapshot_copy": attack},
    )
    assert attacked
    _assert_blocked(result)
    assert result["final_gate"] == "BLOCKED_EVIDENCE_CHANGED_DURING_SNAPSHOT"


def test_rejects_evidence_change_after_snapshot(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)

    def attack(_: dict) -> None:
        paths["raw_file"].write_bytes(paths["raw_file"].read_bytes() + b"\n")

    _assert_blocked(
        _evaluate(
            tmp_path,
            config,
            hooks={"after_snapshot_validation": attack},
        )
    )


def test_rejects_non_regular_source_file(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    paths["raw_file"].unlink()
    os.mkfifo(paths["raw_file"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_snapshot_validation_uses_snapshot_not_live_path(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    observed_snapshot_hash: str | None = None

    def attack(context: dict) -> None:
        nonlocal observed_snapshot_hash
        observed_snapshot_hash = calculate_sha256(
            context["raw_files"]["observations"]
        )
        paths["raw_file"].write_text(
            paths["raw_file"].read_text(encoding="utf-8").replace(
                "HOLD_001,2",
                "HOLD_001,8",
            ),
            encoding="utf-8",
        )
        assert calculate_sha256(
            context["raw_files"]["observations"]
        ) == observed_snapshot_hash

    result = _evaluate(
        tmp_path,
        config,
        hooks={"after_snapshot_validation": attack},
    )
    assert observed_snapshot_hash is not None
    _assert_blocked(result)


def test_rejects_holdout_declared_fail(tmp_path: Path) -> None:
    config, _ = build_gate_repository(tmp_path, declared_verdict="FAIL")
    result = _evaluate(tmp_path, config)
    _assert_blocked(result)
    assert result["final_gate"] == "BLOCKED_EXTERNAL_HOLDOUT_FAILED"


def test_rejects_holdout_declared_inconclusive(tmp_path: Path) -> None:
    config, _ = build_gate_repository(
        tmp_path,
        declared_verdict="INCONCLUSIVE",
    )
    result = _evaluate(tmp_path, config)
    _assert_blocked(result)
    assert result["final_gate"] == "BLOCKED_EXTERNAL_HOLDOUT_INCONCLUSIVE"


def test_rejects_declared_pass_with_metric_failure(tmp_path: Path) -> None:
    config, _ = build_gate_repository(tmp_path, metric_value=0.5)
    result = _evaluate(tmp_path, config)
    _assert_blocked(result)
    assert result["final_gate"] == "BLOCKED_HOLDOUT_VERDICT_MISMATCH"


def test_rejects_declared_pass_with_missing_primary_metric(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    holdout = _load(paths["holdout"])
    holdout["metrics"] = [
        {"metric_id": "secondary", "value": 0.0, "value_unit": "1"}
    ]
    write_yaml(paths["holdout"], holdout)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_declared_pass_with_nonnumeric_metric(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    holdout = _load(paths["holdout"])
    holdout["metrics"][0]["value"] = "not-a-number"
    write_yaml(paths["holdout"], holdout)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_declared_pass_with_wrong_metric_unit(tmp_path: Path) -> None:
    config, _ = build_gate_repository(tmp_path, metric_unit="percent")
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_declared_pass_with_wrong_parameter_hash(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    holdout = _load(paths["holdout"])
    holdout["parameter_result_hash"] = "0" * 64
    write_yaml(paths["holdout"], holdout)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_declared_pass_with_wrong_config_hash(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    holdout = _load(paths["holdout"])
    holdout["config_hash"] = "0" * 64
    write_yaml(paths["holdout"], holdout)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_declared_pass_with_calibration_id_reuse(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    holdout = _load(paths["holdout"])
    holdout["holdout_ids"] = ["CAL_001"]
    write_yaml(paths["holdout"], holdout)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_metric_value_not_matching_result_file(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    paths["model_output"].write_text(
        "sample_id,prediction\nHOLD_001,3\n",
        encoding="utf-8",
    )
    holdout = _load(paths["holdout"])
    holdout["result_file_checksums"][
        paths["model_output"].relative_to(tmp_path).as_posix()
    ] = calculate_sha256(paths["model_output"])
    write_yaml(paths["holdout"], holdout)
    git(
        tmp_path,
        "add",
        paths["model_output"].relative_to(tmp_path).as_posix(),
        paths["holdout"].relative_to(tmp_path).as_posix(),
    )
    git(tmp_path, "commit", "-q", "-m", "Forge inconsistent holdout metric")
    result = _evaluate(tmp_path, config)
    _assert_blocked(result)
    assert (
        result["final_gate"]
        == "BLOCKED_HOLDOUT_METRIC_RECOMPUTE_MISMATCH"
    )


def test_rejects_modified_preregistered_threshold(tmp_path: Path) -> None:
    config, paths = build_gate_repository(tmp_path)
    record = _load(paths["preregistration_record"])
    record["primary_metrics"][0]["threshold"] = 0.9
    write_yaml(paths["preregistration_record"], record)
    git(
        tmp_path,
        "add",
        paths["preregistration_record"].relative_to(tmp_path).as_posix(),
    )
    git(tmp_path, "commit", "-q", "-m", "Modify threshold after holdout")
    _assert_blocked(_evaluate(tmp_path, config))


def test_accepts_test_only_positive_chain_only_when_metrics_recompute_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, _ = build_gate_repository(tmp_path)
    isolated = _evaluate(tmp_path, config)
    assert isolated["status"] == "READY_FOR_BOUNDED_V3_PHYSICS"
    assert isolated["holdout_evaluation"]["derived_verdict"] == "PASS"
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    _assert_blocked(gate.evaluate_gate(config))


@pytest.mark.parametrize(
    ("comparator", "threshold", "value", "expected"),
    [
        ("LT", 1.0, 1.0, "FAIL"),
        ("LE", 1.0, 1.0, "PASS"),
        ("GT", 1.0, 1.0, "FAIL"),
        ("GE", 1.0, 1.0, "PASS"),
        ("BETWEEN_CLOSED", [1.0, 2.0], 2.0, "PASS"),
        ("ABS_LE", 1.0, -1.0, "PASS"),
    ],
)
def test_holdout_comparator_boundaries(
    comparator: str,
    threshold: float | list[float],
    value: float,
    expected: str,
) -> None:
    evaluation = derive_holdout_verdict(
        {
            "primary_metrics": [
                {
                    "metric_id": "m",
                    "required": True,
                    "comparator": comparator,
                    "threshold": threshold,
                    "value_unit": "1",
                    "missing_policy": "FAIL",
                }
            ]
        },
        [{"metric_id": "m", "value": value, "value_unit": "1"}],
    )
    assert evaluation.derived_verdict == expected
