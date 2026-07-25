# V3 external-evidence gate remediation report

Date: 2026-07-25

## Verdict

```text
P1_01_STATUS = FIXED_PENDING_INDEPENDENT_REVIEW
P1_02_STATUS = FIXED_PENDING_INDEPENDENT_REVIEW

REMEDIATION_STATUS =
READY_FOR_INDEPENDENT_ADVERSARIAL_REVIEW

MERGE_RECOMMENDATION =
HOLD_PENDING_INDEPENDENT_REVIEW
```

No real external dataset was acquired or inspected. No calibration or holdout
was executed. This branch must not be merged until independent adversarial
review confirms the artifact and Git-history contracts.

## Original P1 reproduction and attacks

```text
NONEXISTENT_MANIFEST_ATTACK = BLOCKED_AFTER_REPRODUCED_OLD_BYPASS
NONNUMERIC_AIR_HTO_ATTACK = BLOCKED_AFTER_REPRODUCED_OLD_BYPASS
EMPTY_DETECTION_LIMIT_ATTACK = BLOCKED_AFTER_REPRODUCED_OLD_BYPASS
CHECKSUM_TAMPER_ATTACK = BLOCKED
BOOLEAN_BYPASS_ATTACK = BLOCKED
PREREGISTRATION_ORDER_ATTACK = BLOCKED
SYNTHETIC_EVIDENCE_ATTACK = BLOCKED_FOR_PHYSICS
INTERNAL_REFERENCE_ATTACK = BLOCKED_FOR_PHYSICS
```

The old gate returned `READY_FOR_BOUNDED_V3_PHYSICS` for two nonexistent
manifest strings after booleans and labels were edited. The old intake
returned `PASS_SYNTHETIC_CONTRACT_ONLY` for nonnumeric air HTO and an empty
detection-limit row. All three cases were captured as failing tests before the
implementation changed.

## Evidence verification implementation

```text
SCHEMA_RUNTIME_VALIDATION_STATUS = PASS_EXECUTED_JSONSCHEMA_4_26_0
RAW_CHECKSUM_RECOMPUTE_STATUS = PASS_TESTED
GIT_PREREGISTRATION_ORDER_STATUS = PASS_TEST_ONLY_COMPLETE_CHAIN
HOLDOUT_ARTIFACT_VALIDATION_STATUS = PASS_TEST_ONLY_COMPLETE_CHAIN
```

The production gate configuration is now an evidence entry point. It contains
an optional evidence-bundle path and allowed roots, not readiness booleans.
When a bundle is present, the gate:

1. requires nonempty regular files inside allowed roots;
2. executes Draft 2020-12 JSON Schema validation for every artifact;
3. recomputes raw and holdout-result SHA-256 values;
4. cross-checks dataset IDs, raw/intake/preregistration hashes, config hash,
   model commit, parameter hash, and frozen sample IDs;
5. verifies finite calibration, identifiability, and holdout metrics;
6. verifies the preregistration file at its declared Git commit;
7. finds the first commit adding the holdout result and proves strict
   preregistration ancestry;
8. rejects uncommitted preregistration or holdout changes;
9. accepts only controlled experiment, matched field observation, or licensed
   external holdout evidence types;
10. requires V1, V2, and validation-readiness result artifacts associated with
    the same model commit.

The soybean adapter now validates actual numeric content, finite/range
constraints, detection-limit and uncertainty applicability/units, forcing
continuity and exposure coverage, split disjointness, raw file sizes, and
expected versus calculated checksums. Its generated intake manifest is
immediately revalidated against the executable intake schema.

## Regression results

```text
TEST_STATUS = PASS_234_ONE_KNOWN_NUMPY_NETCDF_WARNING
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY
V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_EXTERNAL_EVIDENCE_UNBLOCKING_STATUS =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
COMPILE_STATUS = PASS
DIFF_CHECK_STATUS = PASS
```

The warning is the pre-existing NumPy/NetCDF binary-size runtime warning in
`tests/unit/test_era5_reader.py::test_netcdf_mapping`.

## Scope and branch

```text
FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0
MAIN_HEAD = f618515caef22a19867d75d59b1d4c78f1cb212f
V1_TAG = 6918440faa3455b848f43589784672f3bfabfe3d
V2_CANDIDATE_TAG = f097115cbfc052baa18f1e49a1207fa6b3523cff
BRANCH = codex/v3-external-evidence-gate-remediation
BRANCH_HEAD = VERIFY_WITH_GIT_REV_PARSE_AFTER_REPORT_COMMIT
WORKTREE_STATUS = CLEAN_REQUIRED_BEFORE_PUSH
```

No `src/` or `configs/` file changed. The production gate remains blocked
because `evidence_bundle_path` and the three regression-report paths are null;
no test fixture is referenced by production configuration.

## Commits before final documentation

```text
7e5b65b Add executable external evidence schemas and checksum validation
9fffca0 Harden soybean intake numeric and time-series validation
6b9f2d1 Replace declarative V3 physics gate with artifact verification
7354c07 Add adversarial fail-closed evidence tests
```

## Key executed commands

```bash
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_validation_readiness.py
.venv/bin/python scripts/verify_v3_compatibility.py
.venv/bin/python scripts/verify_v3_architecture_readiness.py
.venv/bin/python scripts/verify_v3_external_evidence_unblocking.py
.venv/bin/python scripts/verify_v3_physics_start_gate.py
.venv/bin/python -m compileall -q src tests era5 scripts validation
git diff --check
git diff main...HEAD -- src configs
```
