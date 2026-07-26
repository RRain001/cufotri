# V3 external-evidence gate independent review 3 report

Date: 2026-07-26

## Verdict

```text
REVIEWED_REMEDIATION_3_HEAD =
54d1e8112e0e64c5835c709f28a88ac68d6292d2

INDEPENDENT_REVIEW_3_BRANCH =
codex/v3-external-evidence-gate-independent-review-3

INDEPENDENT_REVIEW_3_TEST_COMMIT =
32a302c18c15c71851f160f31e83b3cfd07bddb0

INDEPENDENT_REVIEW_3_HEAD =
RECORDED_BY_GIT_AFTER_THIS_REPORT_COMMIT

THIRD_INDEPENDENT_REVIEW_STATUS =
PASS_ADVERSARIAL_REVIEW

MERGE_RECOMMENDATION =
READY_TO_MERGE_REMEDIATION_3
```

No production implementation, schema, `src/`, or formal `configs/` file was
modified on the review branch. The review added only an independent test file
and this report.

## Independent construction

The review test builds a new temporary Git repository without importing the
remediation fixture builder. It independently creates:

* a protected test `main` and aligned simulated `origin/main`;
* a trusted test-only registry approval committed before preregistration;
* a two-parameter frozen contract;
* calibration and holdout mappings in an order different from the frozen list;
* complete identifiability results;
* a recomputable PASS holdout metric;
* regression artifacts, a stable snapshot, and a final source recheck.

The isolated evaluator returns `READY_FOR_BOUNDED_V3_PHYSICS` only for this
complete test-only chain. The production evaluator rejects the same test-only
source, and the checked-in production null-bundle configuration remains
blocked.

```text
TEST_ONLY_PARAMETER_CONTRACT_PATH =
PASS_GATE_LOGIC_ONLY

EMPIRICAL_VALIDATION =
FALSE
```

## Manual review

```text
PARAMETER_CONTRACT_SOURCE_STATUS =
PASS_FROZEN_PREREGISTRATION_ONLY

PARAMETER_SET_STATUS =
PASS_EXACT_ASCII_CASE_SENSITIVE_SET

PARAMETER_ORDER_STATUS =
PASS_CANONICAL_ORDER_INDEPENDENT

PARAMETER_BOUNDS_STATUS =
PASS_RUNTIME_INCLUSIVE_EXCLUSIVE_CHECKS

PARAMETER_UNIT_STATUS =
PASS_ITEM_BY_ITEM

PARAMETER_TRANSFORM_STATUS =
PASS_ITEM_BY_ITEM_STRICT_ENUM

PARAMETER_CONTRACT_HASH_STATUS =
PASS_RECOMPUTED_FROM_CANONICAL_FROZEN_CONTRACT

PARAMETER_RESULT_HASH_STATUS =
PASS_RECOMPUTED_IN_FROZEN_NAME_ORDER

IDENTIFIABILITY_COVERAGE_STATUS =
PASS_EXACT_COMPLETE_PARAMETER_SET

HOLDOUT_PARAMETER_STATUS =
PASS_SAME_CONTRACT_AND_CANONICAL_RESULT

TRUSTED_REGISTRY_REVIEW =
PASS_NO_REGRESSION

SNAPSHOT_REVIEW =
PASS_NO_REGRESSION

HOLDOUT_VERDICT_REVIEW =
PASS_FAIL_AND_INCONCLUSIVE_REMAIN_BLOCKED

PRODUCTION_NULL_BUNDLE_STATUS =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

The semantic name/value/unit/transform/bounds checks execute before accepting
artifact hashes. Replacing, adding, or deleting parameter names while
consistently updating calibration, identifiability, holdout, and all
parameter-result hashes therefore remains blocked.

## Independent attack matrix

New test file:

```text
tests/independent_review_3/
  test_v3_external_evidence_parameter_contract_review.py
```

The 34 independently collected cases comprise 31 blocked attacks and three
required positive boundary/order cases:

```text
O1_PARAMETER_SET_AND_ORDER_CASES = 6
O2_RANGE_AND_NUMERIC_CASES = 10
O3_UNIT_TRANSFORM_CHRONOLOGY_CASES = 5
O4_IDENTIFIABILITY_CASES = 6
O5_ADJACENT_OLD_MECHANISM_CASES = 7

NEW_INDEPENDENT_ATTACK_COUNT = 34
NEW_INDEPENDENT_ATTACK_STATUS = PASS_34

PREVIOUS_ATTACK_COUNT = 115
TOTAL_TARGETED_REVIEW_TEST_STATUS = PASS_149
```

O5 independently rechecked production test-only isolation, same-size raw
replacement after snapshot, declared holdout `FAIL`, production policy-path
override rejection, an untrusted feature-branch registry, preregistration
chronology, and the production null bundle.

## Full regression in review worktree

```text
COLLECTED_TEST_COUNT = 351
PYTEST_STATUS =
PASS_350_WITH_1_EXISTING_ENVIRONMENTAL_SKIP

EXISTING_SKIP =
LOCAL_READ_ONLY_ERA5_AUDIT_FORCING_NOT_AVAILABLE

FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0
```

The skip is the pre-existing conditional skip in
`tests/integration/test_deposition_activity_ledger.py`; it is unrelated to the
external-evidence gate.

## Final finding status

```text
F_01_STATUS = CONFIRMED_FIXED
F_02_STATUS = CONFIRMED_FIXED
F_03_STATUS = CONFIRMED_FIXED
F_04_STATUS = CONFIRMED_FIXED

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

THIRD_INDEPENDENT_REVIEW_STATUS =
PASS_ADVERSARIAL_REVIEW

MERGE_RECOMMENDATION =
READY_TO_MERGE_REMEDIATION_3
```

No external data was searched, acquired, or inspected. No real intake,
calibration, identifiability, holdout, V3 physics implementation, or tag
operation was performed.
