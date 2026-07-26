# V3 external-evidence gate independent review 2 report

Date: 2026-07-26

## Verdict

```text
REVIEWED_REMEDIATION_2_HEAD =
e9a0f6b64d9f57d69b6f3b6a48d93196370b5efb

INDEPENDENT_REVIEW_2_BRANCH =
codex/v3-external-evidence-gate-independent-review-2

INDEPENDENT_REVIEW_2_HEAD =
RECORDED_BY_GIT_AFTER_THIS_REPORT_COMMIT

SECOND_INDEPENDENT_REVIEW_STATUS =
FAIL_ADDITIONAL_GATE_WEAKNESS

MERGE_RECOMMENDATION =
HOLD_FOR_THIRD_REMEDIATION

REMEDIATION_2_MERGE_STATUS =
NOT_MERGED

MAIN_STATUS =
UNCHANGED
```

The stopping condition was reached by the first new independent attack.
Production code was not modified. No subsequent full regression, merge,
`main` push, external-data work, calibration, holdout execution, or V3 physics
work was performed.

## New independent finding

```text
F_04 =
PREREGISTERED_PARAMETER_SET_NOT_ENFORCED

SEVERITY =
HIGH

INDEPENDENT_BASELINE_CHAIN =
READY_FOR_BOUNDED_V3_PHYSICS

PARAMETER_SET_REPLACEMENT_ATTACK =
READY_FOR_BOUNDED_V3_PHYSICS

EXPECTED_ATTACK_RESULT =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

The frozen preregistration file and record both declare:

```yaml
parameter_set:
  - approved_decay_rate
```

After preregistration and holdout, the independent attack replaces the
calibration parameter mapping with:

```yaml
parameters:
  unregistered_rate: 0.2
```

It recomputes `parameter_result_hash` and consistently updates calibration,
identifiability, and holdout artifacts, then commits the changes. All
registry, snapshot, result-file, primary-metric, verdict, chronology, and
clean-worktree checks remain satisfied. The gate incorrectly returns
`READY_FOR_BOUNDED_V3_PHYSICS`.

## Root cause

`scripts/verify_v3_physics_start_gate.py` verifies that the preregistration
file and record agree on `parameter_set`. It then verifies that calibration
parameters are finite and that calibration, identifiability, and holdout
share the same recomputed parameter hash. It never compares the keys of
`calibration["parameters"]` with the frozen preregistered `parameter_set`.

The missing invariant is equivalent to:

```text
set(calibration.parameters.keys())
==
set(frozen_preregistration.parameter_set)
```

The third remediation must define whether ordering is significant and enforce
the corresponding exact contract before accepting the calibration hash. This
report does not implement that fix.

## Independent test evidence

New test file:

```text
tests/independent_review_2/
  test_v3_external_evidence_gate_second_review.py
```

Test:

```text
test_rejects_calibration_parameter_set_not_frozen_by_preregistration
```

Actual result:

```text
NEW_INDEPENDENT_ATTACK_COUNT = 1
NEW_INDEPENDENT_ATTACK_PASS_COUNT = 0
NEW_INDEPENDENT_ATTACK_FAIL_COUNT = 1

BASELINE_POSITIVE_CHAIN_STATUS =
READY_FOR_BOUNDED_V3_PHYSICS

ATTACKED_CHAIN_STATUS =
READY_FOR_BOUNDED_V3_PHYSICS

TOTAL_REVIEW_TEST_STATUS =
FAIL_1_SECURITY_ASSERTION
```

The test builds a new protected-ref, approval, registry, preregistration,
snapshot, metric-recompute, and holdout chain without importing the remediation
fixture builder. The baseline positive chain first proves the independent
fixture is executable; only then is the frozen parameter-set attack applied.

Executed command:

```bash
/Users/rain/Documents/Doctor/Topic/CETAS_ufotri/.venv/bin/python \
  -m pytest -q -p no:cacheprovider \
  tests/independent_review_2/\
test_v3_external_evidence_gate_second_review.py
```

Pytest failed at the security assertion because:

```text
assert attacked["status"] ==
  "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"

actual =
  "READY_FOR_BOUNDED_V3_PHYSICS"
```

## Review matrix at stop

```text
PREVIOUS_ATTACK_COUNT = 77
NEW_INDEPENDENT_ATTACK_COUNT = 1

TRUSTED_REGISTRY_STATUS =
NO_NEW_BYPASS_OBSERVED_BEFORE_STOP

TEST_ONLY_ISOLATION_STATUS =
NO_NEW_BYPASS_OBSERVED_BEFORE_STOP

SNAPSHOT_STATUS =
NO_NEW_BYPASS_OBSERVED_BEFORE_STOP

TOCTOU_STATUS =
NO_NEW_BYPASS_OBSERVED_BEFORE_STOP

HOLDOUT_VERDICT_STATUS =
PASS_IN_INDEPENDENT_BASELINE_CHAIN

HOLDOUT_METRIC_RECOMPUTE_STATUS =
PASS_IN_INDEPENDENT_BASELINE_CHAIN

GIT_CHRONOLOGY_STATUS =
PASS_IN_INDEPENDENT_BASELINE_CHAIN

PREREGISTERED_PARAMETER_SET_STATUS =
FAIL_NOT_ENFORCED
```

Because the mandatory stop fired on a new HIGH weakness, the remaining O1-O4
attack matrix was not represented as completed.

## Original three findings

```text
F_01_STATUS =
TARGETED_REMEDIATION_TESTS_PASS_BUT_SECOND_REVIEW_NOT_COMPLETED

F_02_STATUS =
TARGETED_REMEDIATION_TESTS_PASS_BUT_SECOND_REVIEW_NOT_COMPLETED

F_03_STATUS =
TARGETED_REMEDIATION_TESTS_PASS_BUT_SECOND_REVIEW_NOT_COMPLETED
```

They cannot be promoted to `CONFIRMED_FIXED` because the second independent
review did not satisfy its complete pass condition.

## Scope and stopping state

```text
FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0
PRODUCTION_IMPLEMENTATION_CHANGE_COUNT_ON_REVIEW_BRANCH = 0

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

SECOND_INDEPENDENT_REVIEW_STATUS =
FAIL_ADDITIONAL_GATE_WEAKNESS

MERGE_RECOMMENDATION =
HOLD_FOR_THIRD_REMEDIATION

REMEDIATION_2_MERGE_STATUS =
NOT_MERGED
```
