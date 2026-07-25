# V3 external-evidence adversarial test report

Date: 2026-07-25

## Scope and threat model

This report tests whether malformed data, missing artifacts, mutable
declarations, ineligible evidence, or invalid Git chronology can incorrectly
produce `READY_FOR_BOUNDED_V3_PHYSICS`. It does not validate any real
experiment and does not authorize V3 physics implementation.

The old implementation was tested before remediation. The three initial tests
all failed:

```text
test_physics_gate_rejects_nonexistent_manifest_paths = FAILED_OLD_IMPLEMENTATION
test_intake_rejects_non_numeric_air_hto = FAILED_OLD_IMPLEMENTATION
test_intake_rejects_empty_detection_limit_values = FAILED_OLD_IMPLEMENTATION
```

The reproduced old outputs were:

```text
nonexistent manifest paths -> READY_FOR_BOUNDED_V3_PHYSICS
non-numeric air HTO -> PASS_SYNTHETIC_CONTRACT_ONLY
empty detection-limit row -> PASS_SYNTHETIC_CONTRACT_ONLY
```

## Adversarial matrix after remediation

| Attack | Expected | Observed |
| --- | --- | --- |
| Nonexistent manifest path | blocked | blocked |
| Manifest path is a directory | blocked | blocked |
| Empty manifest | blocked | blocked |
| Manifest violates JSON Schema | blocked | blocked |
| Required raw file missing | blocked | blocked |
| Expected or calculated checksum mismatch | blocked | blocked |
| Air HTO is text | blocked | blocked |
| Air HTO is NaN, +Inf, or -Inf | blocked | blocked |
| Detection-limit value is empty | blocked | blocked |
| Detection-limit value is negative | blocked | blocked |
| Chamber volume is zero | blocked | blocked |
| Mixing/ventilation rate is negative | blocked | blocked |
| Timestamp is duplicate or nonmonotonic | blocked | blocked |
| Time series is discontinuous | blocked | blocked |
| Meteorology/air HTO does not cover exposure | blocked | blocked |
| Calibration and holdout IDs overlap | blocked | blocked |
| Preregistration has uncommitted changes | blocked | blocked |
| Preregistration commit is not before holdout | blocked | blocked |
| Holdout result is missing | blocked | blocked |
| Holdout metric is nonnumeric | blocked | blocked |
| Evidence type is synthetic | blocked for physics | blocked |
| Evidence type is internal reference | blocked for physics | blocked |
| Legacy diagnostic booleans are all true | blocked | blocked |
| Complete synthetic intake contract | contract-only pass | contract-only pass |
| Complete test-only artifact chain | gate logic ready | ready in isolated test Git repository |

The complete artifact-chain fixture is generated inside a temporary Git
repository. It is labelled test-only, is never used by the production gate,
and cannot contribute an empirical case. It exists solely to prove that the
positive path is executable after all artifact, hash, schema, chronology, and
regression checks pass.

## Independent mutation operations

The tests define expected blocked outcomes directly. They do not call
production code to generate expected metrics or verdicts. Mutation-style
checks independently:

- change the evidence type to `SYNTHETIC_CONTRACT_TEST` or
  `INTERNAL_REFERENCE`;
- change a raw file byte without updating the manifest;
- replace an expected SHA-256;
- remove or empty the detection-limit data;
- overlap calibration and holdout identifiers;
- replace the preregistration commit with a non-preceding commit;
- remove the holdout result;
- inject legacy diagnostic booleans with value `true`.

## Executed commands

```bash
.venv/bin/python -m pytest -q \
  tests/unit/test_v3_external_evidence_adversarial.py

.venv/bin/python scripts/verify_v3_external_evidence_unblocking.py

.venv/bin/python scripts/verify_v3_physics_start_gate.py
```

Result:

```text
ADVERSARIAL_TEST_COUNT = 29
ADVERSARIAL_TEST_STATUS = PASS
SCHEMA_RUNTIME_VALIDATION_STATUS = PASS_EXECUTED
PRODUCTION_GATE_STATUS = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```
