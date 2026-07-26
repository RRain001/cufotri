# V3 external-evidence gate independent adversarial review

Date: 2026-07-26

## Review identity and scope

```text
REVIEWED_BRANCH =
codex/v3-external-evidence-gate-remediation

REVIEWED_HEAD =
e348be45c9188eeac0cf6264514728004077071d

INDEPENDENT_REVIEW_BRANCH =
codex/v3-external-evidence-gate-independent-review

INDEPENDENT_REVIEW_TEST_HEAD =
4949f3e51ea255a37a9deb09d5250ee3815938dd

INDEPENDENT_REVIEW_HEAD =
VERIFY_WITH_GIT_REV_PARSE_AFTER_REPORT_COMMIT
```

The review used a separate worktree and branch. It did not modify remediation
production code. The only review-branch changes are independent attack tests
and this report.

## Verdict

```text
INDEPENDENT_REVIEW_STATUS =
FAIL_ADDITIONAL_GATE_WEAKNESS

P1_01_STATUS =
NOT_CONFIRMED_FIXED_ADDITIONAL_PHYSICS_READY_BYPASSES

P1_02_STATUS =
NOT_CONFIRMED_FIXED_RAW_CHECKSUM_TOCTOU_REMAINS

MERGE_RECOMMENDATION =
HOLD_FOR_FURTHER_REMEDIATION

REMEDIATION_MERGE_STATUS =
NOT_MERGED

MAIN_STATUS =
UNCHANGED
```

Three independently constructed attacks expected a blocked verdict. All three
instead returned `READY_FOR_BOUNDED_V3_PHYSICS`. This triggers the Phase E1
stop condition. No full Phase F regression, review-to-remediation merge,
`main` merge, or push of `main` was attempted.

## Findings

### F-01: Test-only evidence can masquerade as an eligible empirical chain

Severity: HIGH — merge blocker.

The raw-manifest schema has no explicit immutable `test_only` or empirical
eligibility field. Its `source` object accepts arbitrary nonempty title,
authority, and reference strings
(`schemas/v3/external_raw_data_manifest.schema.json:43-51`). The gate checks
only the evidence-type allowlist and licence/local-use labels
(`scripts/verify_v3_physics_start_gate.py:331-349`).

The independent fixture explicitly declares:

```text
title = TEST-ONLY independent adversarial fixture
authority = pytest independent review
reference = NOT EMPIRICAL; MUST NOT UNBLOCK PRODUCTION
```

but uses `evidence_type: CONTROLLED_EXPERIMENT`. A production-shaped gate
configuration referencing the chain returns physics-ready. Reproduction:
`tests/independent_review/test_v3_external_evidence_gate_independent_attacks.py:348-357`.

Required remediation: add a schema-enforced evidence-origin/test-only contract
and make production gate evaluation reject every test-only fixture regardless
of its path or claimed eligible type. The production gate entry configuration
must also be anchored to trusted tracked policy rather than accepting a
fixture-authored eligibility claim.

### F-02: Raw-data replacement after initial checksum is not detected

Severity: HIGH — merge blocker.

Raw files are hashed once near the beginning of the gate
(`scripts/verify_v3_physics_start_gate.py:279-284`). The returned checksum
mapping is compared with intake declarations, but raw files are not rehashed
immediately before the final ready verdict
(`scripts/verify_v3_physics_start_gate.py:481-498`).

The independent attack wraps the initial verifier, replaces a raw file with a
different same-size payload immediately after that verification, and then
allows the normal gate flow to continue. The gate returns physics-ready.
Reproduction:
`tests/independent_review/test_v3_external_evidence_gate_independent_attacks.py:360-384`.

Required remediation: use a frozen/read-only evidence snapshot or stable open
file descriptors, and revalidate every decisive raw/result byte identity at
the final decision boundary. Document the unavoidable concurrent-filesystem
boundary and require an immutable evidence directory for formal runs.

### F-03: A failed external holdout still produces physics-ready

Severity: HIGH — merge blocker.

The holdout schema permits `PASS`, `FAIL`, and `INCONCLUSIVE`
(`schemas/v3/external_holdout_result.schema.json:62-68`). The gate validates
finite metrics and result-file checksums but never inspects
`holdout["verdict"]` (`scripts/verify_v3_physics_start_gate.py:454-467`) before
returning ready (`scripts/verify_v3_physics_start_gate.py:492-498`).

A fully schema-valid, clean, chronologically valid chain with
`verdict: FAIL` returns physics-ready. Reproduction:
`tests/independent_review/test_v3_external_evidence_gate_independent_attacks.py:387-399`.

Required remediation: derive readiness from an explicitly acceptable holdout
verdict and blocker policy. `FAIL` and `INCONCLUSIVE` must be blocked unless a
separately reviewed policy explicitly defines a weaker architecture-only
outcome; neither may authorize bounded physics implementation.

## Review status matrix

```text
PATH_CONTAINMENT_STATUS =
PASS_STATIC_CANONICAL_CONTAINMENT_FOR_FIXED_ROOTS
INDEPENDENT_PATH_MATRIX_NOT_COMPLETED_AFTER_EARLY_STOP

SCHEMA_RUNTIME_STATUS =
PASS_EXISTING_RUNTIME_VALIDATION

CHECKSUM_RECOMPUTE_STATUS =
FAIL_NO_FINAL_RAW_RECHECK_TOCTOU_BYPASS

INTAKE_NUMERIC_STATUS =
PASS_EXISTING_32_ATTACKS_AND_MANUAL_REVIEW

DETECTION_LIMIT_STATUS =
PASS_EXISTING_32_ATTACKS_AND_MANUAL_REVIEW

TIME_COVERAGE_STATUS =
PASS_EXISTING_32_ATTACKS_AND_MANUAL_REVIEW

GIT_CHRONOLOGY_STATUS =
PASS_STATIC_REVIEW_FOR_FIRST_ADD_AND_STRICT_ANCESTRY
INDEPENDENT_GIT_MATRIX_NOT_COMPLETED_AFTER_EARLY_STOP

HOLDOUT_ARTIFACT_STATUS =
FAIL_HOLDOUT_FAIL_VERDICT_AUTHORIZES_READY

EVIDENCE_ALLOWLIST_STATUS =
PASS_STRICT_STRING_ENUM
FAIL_TEST_ONLY_ORIGIN_CAN_MASQUERADE_AS_ELIGIBLE

LEGACY_BOOLEAN_BYPASS_STATUS =
PASS_EXISTING_ATTACK

TEST_FIXTURE_ISOLATION_STATUS =
FAIL_PRODUCTION_SHAPED_CONFIG_ACCEPTS_TEST_ONLY_CHAIN

TOCTOU_REVIEW_STATUS =
FAIL_RAW_FILE_REPLACEMENT_AFTER_INITIAL_HASH_NOT_DETECTED
```

## Test evidence

Existing remediation attacks:

```text
EXISTING_ADVERSARIAL_TEST_COUNT = 32
EXISTING_ADVERSARIAL_TEST_STATUS = PASS
```

Independent review attacks:

```text
INDEPENDENT_ADVERSARIAL_TEST_COUNT = 3
INDEPENDENT_ADVERSARIAL_TEST_STATUS =
FAIL_3_OF_3_RETURNED_READY_FOR_BOUNDED_V3_PHYSICS

TOTAL_TEST_STATUS =
NOT_RUN_PHASE_F_STOPPED_ON_REVIEW_FAILURE
```

The new test fixture was written independently in a fresh temporary Git
repository and does not import or call the remediation fixture builder.
Expected verdicts are literal `BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA`
strings.

## Regression and repository status

Phase E1 requires immediate stop after any independent bypass. Therefore the
full Phase F and post-merge suites were intentionally not executed.

```text
V1_RECOMPUTE_STATUS = NOT_RUN_STOPPED_ON_REVIEW_FAILURE
V2_RECOMPUTE_STATUS = NOT_RUN_STOPPED_ON_REVIEW_FAILURE
V3_COMPATIBILITY_STATUS = NOT_RUN_STOPPED_ON_REVIEW_FAILURE
V3_ARCHITECTURE_STATUS = NOT_RUN_STOPPED_ON_REVIEW_FAILURE
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA_FOR_PRODUCTION_NULL_BUNDLE

FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0
WORKTREE_STATUS = CLEAN_REQUIRED_AFTER_REPORT_COMMIT
```

The formal production configuration still reports blocked only because its
bundle path is null. The independent findings show that a supplied,
schema-valid artifact chain can still produce an unsafe ready verdict.

## Commands executed

```bash
git fetch --all --prune
git worktree add --detach \
  ../CETAS_ufotri_v3_gate_independent_review \
  e348be45c9188eeac0cf6264514728004077071d
git switch -c codex/v3-external-evidence-gate-independent-review

git diff main...HEAD --stat
git diff main...HEAD --name-status
git diff main...HEAD -- src configs
git diff main...HEAD -- pyproject.toml

/Users/rain/Documents/Doctor/Topic/CETAS_ufotri/.venv/bin/python \
  -m pytest -q tests/unit/test_v3_external_evidence_adversarial.py

/Users/rain/Documents/Doctor/Topic/CETAS_ufotri/.venv/bin/python \
  scripts/verify_v3_external_evidence_unblocking.py

/Users/rain/Documents/Doctor/Topic/CETAS_ufotri/.venv/bin/python \
  scripts/verify_v3_physics_start_gate.py

/Users/rain/Documents/Doctor/Topic/CETAS_ufotri/.venv/bin/python \
  -m pytest -q -p no:cacheprovider \
  tests/independent_review/test_v3_external_evidence_gate_independent_attacks.py
```
