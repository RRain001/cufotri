# V3 external-evidence gate remediation 3 report

Date: 2026-07-26

## Status

```text
F_04_STATUS = FIXED_PENDING_THIRD_INDEPENDENT_REVIEW

REMEDIATION_3_STATUS =
READY_FOR_THIRD_INDEPENDENT_ADVERSARIAL_REVIEW

MERGE_RECOMMENDATION =
HOLD_PENDING_THIRD_INDEPENDENT_REVIEW
```

The second independent attack was imported without changing its blocked
expectation. Before repair, its independent positive baseline returned ready
and its consistently rehashed unregistered parameter chain also returned
ready. After repair, the same attack is blocked.

## Frozen parameter contract

```text
FROZEN_PARAMETER_CONTRACT_STATUS = PASS_TARGETED
CALIBRATION_PARAMETER_SET_STATUS = PASS_TARGETED
CALIBRATION_PARAMETER_BOUNDS_STATUS = PASS_TARGETED
CALIBRATION_PARAMETER_UNIT_STATUS = PASS_TARGETED
CALIBRATION_PARAMETER_TRANSFORM_STATUS = PASS_TARGETED
PARAMETER_CONTRACT_HASH_STATUS = PASS_TARGETED
PARAMETER_RESULT_HASH_STATUS = PASS_TARGETED
IDENTIFIABILITY_PARAMETER_COVERAGE_STATUS = PASS_TARGETED
HOLDOUT_PARAMETER_CONTRACT_STATUS = PASS_TARGETED
```

Production accepts only `parameter_contract`, with ASCII lowercase names,
explicit units, finite inclusive/exclusive bounds, and one of `IDENTITY`,
`LOG`, `LOG10`, or `LOGIT`. Contract order is ignored after canonical sorting.
Calibration and holdout values use `{value, unit, transform}` objects.

```text
parameter_contract_hash =
SHA256(canonical contract sorted by name)

parameter_result_hash =
SHA256(canonical calibrated parameters in frozen-name order)
```

Both hashes are additional consistency proofs. The gate first compares names,
units, transforms, finite values, and bounds item by item. Identifiability
must cover the complete frozen name set, and holdout carries and revalidates
the complete calibrated parameter mapping.

## Tests before full regression

```text
PREVIOUS_TARGETED_ATTACK_COUNT = 78
THIRD_REMEDIATION_ATTACK_COUNT = 37
TOTAL_TARGETED_TEST_STATUS = PASS_115
TOTAL_PYTEST_STATUS = PASS_317

V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS =
PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY
V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_EXTERNAL_EVIDENCE_TOOLING_STATUS =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
COMPILE_STATUS = PASS
DIFF_CHECK_STATUS = PASS

FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0

BRANCH =
codex/v3-external-evidence-gate-remediation-3

BRANCH_HEAD =
RECORDED_AFTER_FINAL_REMEDIATION_COMMIT

WORKTREE_STATUS =
PENDING_FINAL_COMMITS
```

No external data was searched, acquired, or inspected. No real calibration,
holdout, identifiability run, V3 physics implementation, or tag operation was
performed.
