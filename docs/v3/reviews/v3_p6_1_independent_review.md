# V3-P6.1 independent review

## Review identity

```text
REVIEW_BRANCH = codex/v3-p6-1-independent-review
BASE_COMMIT = 40c403d17689c1e00ce1af4d2543ed08fbc08f77
REVIEW_SCOPE = UFOTRI_PARAMETER_DATABASE_SCHEMA_ONLY
```

The review is performed against the actual working-tree diff from the P5.6
independent-review baseline. It does not delegate acceptance to the presence
of a table schema or to a passing synthetic fixture.

## Required adversarial checks

| Check | Evidence | Verdict |
|---|---|---|
| UFOTRI parameters added secretly | No numerical UFOTRI table file was added. The existing `parameters/databases/ufotri_leaf_exchange.yaml` still resolves only placeholders with `value: null`. The new test table is generated in memory and marked `TEST_ONLY`. | PASS |
| Default configuration changed | `git diff --name-only BASE_COMMIT -- configs` is empty; no default case or V2 configuration is changed. | PASS |
| Model output path changed | `git diff --name-only BASE_COMMIT` is empty under `src/cteas_ufotri/atmosphere`, `leaf_exchange`, `soil`, and `dose`. The current V1/V2 case/CLI path does not import `ParameterDatabase` as a runtime source. | PASS_WITH_STATIC_BOUNDARY |
| Manual values called validated | The source audit separates explicit, derived, assumption, and missing records. It states that manual values are not validated by P6.1. The reserved source id `UFOTRI_VALIDATED` remains `external_reference_required` and `production_allowed: false`. | PASS |
| Unvalidated table enters runtime | `ParameterDatabase.get()` rejects table values; `lookup(..., production=True)` requires validated source/metadata and an `ACTIVE` migration record. A `REVIEWED` table therefore fails closed for production. | PASS |
| Lifecycle bypass | Existing sequential migration rules remain in force. P6.1 adds no `VALIDATED` or `ACTIVE` UFOTRI database entry or activation record. | PASS |

## Verification record

The focused P6.1 schema/provenance/lifecycle/boundary tests pass. The P5.1
parameter database and migration regressions pass. The complete `tests/unit`
suite passes with the repository's known NumPy/NetCDF binary-compatibility
warning in the ERA5 reader test.

The historical `tests/architecture/test_v3_p5_6_phase_boundary.py` contains a
deliberate P5.6 assertion that no `src` or `schemas` path may change relative
to the P5.6 audit target. It fails when run against P6.1 because P6.1 is the
explicit, authorized schema-layer change. This review does not weaken or
rewrite that historical test; it records the incompatibility as a stale
previous-phase gate.

```ini
P6_1_STATUS = PASS_DATABASE_READY
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
LEAF_EXCHANGE_IMPLEMENTATION = FALSE
NEXT_PHASE = P6_2_LEAF_EXCHANGE_PHYSICS
INDEPENDENT_REVIEW = PASS_WITH_DECLARED_STALE_P5_6_GATE
```

No commit, merge, or push is performed by this review.
