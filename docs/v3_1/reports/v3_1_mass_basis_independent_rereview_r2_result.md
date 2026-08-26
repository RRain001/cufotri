# V3.1 Mass-Basis Contract — Independent Rereview R2 Result

## Verdict

```ini
STATUS = PASS_INDEPENDENT_REREVIEW
REVIEWED_SHA = 95f78801d0fa3b507e6bd76249b192adf8b107cb
REVIEWER = codex-local-gpt-5.6-luna
REVIEW_ID = LOCAL_CODEX_GPT56LUNA_V3_1_REREVIEW_R2
REVIEW_DATE = 2026-08-26
BLOCKING_FINDINGS = 0
PRIOR_R1_VERDICT = HOLD_REMEDIATION_REQUIRED
```

The reviewer worked from a fresh detached worktree at the exact frozen target
and did not participate in the R1 remediation implementation. Existing tests
were not treated as the sole evidence; reviewer-owned adversarial probes were
also used.

## Blocking gates

| Gate | Result |
| --- | --- |
| PRIOR_BLOCKER_WHITESPACE_SCHEMA_PARITY | PASS |
| NO_NUMERICAL_BASIS_CONVERSION | CONFIRMED_ABSENT |
| EXPLICIT_SOURCE_TARGET_PAIRING | PASS |
| PAIR_REUSE_FAIL_CLOSED | PASS |
| EVIDENCE_TISSUE_SCOPE_BINDING | PASS |
| EVIDENCE_AREA_BASIS_BINDING | PASS |
| CROSS_BASIS_EVIDENCE_ID_BINDING | PASS |
| SAME_BASIS_EVIDENCE_STATE_BYPASS | PASS_R1_BLOCKER_REMEDIATED |
| PYTHON_SCHEMA_BOUNDARY | PASS |
| FROZEN_RUNTIME_ISOLATION | PASS |
| P7_8B2_SCOPE_COMPLIANCE | PASS |

### Key findings

- Python and JSON Schema reject whitespace-only values consistently for all
  serialized text fields governed by `_require_text()`.
- V3.1 contains no numerical fresh/dry/water/hydrogen conversion factor and no
  arithmetic conversion path.
- `PairedMeasurement` explicitly binds source and target measurement records;
  self-pairs, duplicate pair IDs, and measurement reuse across pair roles fail
  closed.
- `BasisConversionEvidence` is bound to exact mass-basis direction, tissue
  scope, area basis, provenance, and declared evidence ID.
- The Luna R1 bypass is closed: clean same-basis proposals alone may return
  `IDENTITY_ONLY`; same-basis proposals carrying `EVIDENCE_DECLARED` or a
  supplied cross-basis evidence object fail closed.
- `require_direct_comparison()` remains the direct same-basis comparison API.
- The persisted schema covers `MassBasisContract`; `PairedMeasurement` and
  `BasisConversionEvidence` remain in-memory governance objects in V3.1.
- Independent Git blob comparison confirmed the existing leaf, TFWT, OBT,
  soil, root, food, exposure, pipeline, and P7.5/P7.5B runtime semantics are
  unchanged.
- No V4 physics, calibration, parameter activation, or physical-validation
  declaration was introduced.

## Local verification

```text
Python = 3.14.6
Platform = macOS arm64
focused tests = 26 passed
portable suite = 1000 passed, 1 skipped, 57 deselected, 1 warning
explicit invariants = 79 passed
compileall = PASS
import smoke = PASS
git diff --check = PASS
frozen runtime isolation = PASS
reviewer adversarial probe groups = 8/8 PASS
```

After the verdict artifacts were committed to the R2 review branch, the review
branch suite reported `1008 passed, 1 skipped`; GitHub Actions on final R2 head
`7a06733f3201cc60c4c6599799892899cdb61d7f` also passed both V3 Remediation CI
and V3 Protected Integration Gate.

## Nonblocking notes

1. The prior R1 macOS P7.7B synthetic registry mismatch did not reproduce in
   R2. It remains cross-platform software reproducibility debt only and is not
   evidence for or against physical validation.
2. The pre-existing NumPy/netCDF binary-compatibility RuntimeWarning remains
   nonblocking and unrelated to V3.1.
3. Local Python 3.14/macOS and CI Python 3.12/Ubuntu both passed, with no V3.1
   version-specific behavior observed.

## Exit policy at review time

```ini
IMPLEMENTATION_PR_MERGE_READY = TRUE
MAIN_MERGE_AUTHORIZED_BY_THIS_REVIEW = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

The later main merge was separately authorized by the repository owner and is
recorded by the V3.1 post-merge closure; it does not alter this reviewer verdict.
