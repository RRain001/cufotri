# V3 Protected Integration Review

Date: 2026-08-25

Repository: `RRain001/CTEAS_ufotri`

Review branch: `codex/v3-protected-integration-review`

Draft PR: #1, `V3 protected integration review`

## Decision

```text
PROTECTED_INTEGRATION_REVIEW = PASS
MAIN_MERGE_RECOMMENDED = TRUE
MAIN_MERGE_AUTHORIZED = FALSE
MAIN_MERGE_PERFORMED = FALSE

CORE_RUNTIME_CHANGED_AFTER_VERIFIED_CANDIDATE = FALSE
PHYSICS_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

This review establishes technical readiness for a separate, explicitly
authorized integration of the current V3 candidate line into `main`. It does
not claim physical validation, UFOTRI database activation, calibration, or
production physics readiness.

## Frozen lineage

At review entry:

- `main` = `6671f5793d04842bf2ceae4904f3c0cf30a0d7e0`
- verified remediation/runtime candidate =
  `8d5bff32a6fd43b3109f59f086170d89a0e9a8cd`
- merge base = `main`
- candidate ahead of `main` = 44 commits
- candidate behind `main` = 0 commits

Therefore the candidate line had no divergent-main replay problem. The review
branch was created directly from the verified remediation candidate.

## Runtime freeze during review

All commits added after the verified candidate were restricted to review
infrastructure, governance documents, CI, and test-governance remediation.
No files under the following protected runtime/data surfaces were changed:

- `src/`
- `configs/`
- `parameters/`
- `validation/results/`
- `schemas/`

The only non-architecture-test test changes were explicit test-governance
changes in `tests/conftest.py` and the D3 historical mapping scope test. They do
not alter model runtime behavior.

## Integration gate

The decisive pull-request run was:

```text
WORKFLOW = V3 Protected Integration Gate
JOB = integration-gate
RUN_ID = 32804857229
VERIFIED_HEAD = 432533b8bb4f449661a3099bbe13aa55c9fbf0e3
RESULT = SUCCESS
RUNNER = ubuntu-24.04
PYTHON = 3.12.14
```

The gate passed:

1. full-history checkout;
2. `origin/main` ancestor check;
3. `git diff --check origin/main...HEAD`;
4. `python -m compileall -q src`;
5. V3 package/import smoke;
6. portable current pytest suite;
7. current and frozen-boundary integration invariants.

The portable current suite result was:

```text
974 passed
1 skipped
57 deselected
1 warning
```

The explicit integration/frozen-boundary invariant suite result was:

```text
53 passed
```

The warning was a NumPy binary-compatibility runtime warning raised while the
ERA5 NetCDF mapping test itself passed. It is recorded as a packaging/runtime
environment technical debt, not as a physics or numerical validation failure.

## Historical-review test portability remediation

An initial full non-external run exposed eight failures. Independent inspection
showed that they were not current V3 runtime regressions. They belonged to
historical review assertions that depended on one of the following:

- a local `main` branch existing in the worktree;
- `HEAD` still being the historical stage tip;
- a dedicated sibling blind-classifier worktree being provisioned.

Those assumptions are valid only in their original audit context and are not
evergreen properties of later V3 descendants.

Seven exact test node IDs are now classified as
`historical_review_context`. They are excluded from the portable current CI
suite by name and are not silently weakened. Their core immutable protection
claims are reproduced by a new SHA-frozen boundary suite covering:

- D3 manual mapping: `f5d18886... -> 0164a99c...`;
- external-evidence unblocking: `f618515c... -> 2a3bbd1f...`;
- SB1 independent review: `744db57e... -> 5c1d4bf3...`;
- SB4 independent review: `d08d9d81... -> b5403870...`.

The D3 manual mapping test itself was minimally changed so its protected-path
assertion compares the actual frozen historical interval rather than a mutable
`main...HEAD` expression.

## Pull request state

PR #1 is open, draft, unmerged, and GitHub reports it as mergeable. Technical
mergeability is evidence that there is no Git conflict; it is not merge
authorization.

## Merge-method decision

The current V3 history contains documents and provenance records that refer to
frozen commit SHAs. Therefore:

```text
PREFERRED = MERGE_COMMIT_PRESERVE_EXISTING_STAGE_SHAS
ALTERNATIVE = EXACT_FAST_FORWARD_REF_UPDATE_IF_EXPLICITLY_AUTHORIZED
FORBIDDEN = REBASE
FORBIDDEN = SQUASH
```

A normal merge commit preserves all existing stage commit identities while
recording the integration event. Rebase would rewrite frozen stage SHAs;
squash would destroy the stage-by-stage audit history.

## Main protection recommendation

`main` currently has no branch protection and no required status checks. After
an explicitly authorized integration, the recommended minimum protection is:

- require `V3 Protected Integration Gate / integration-gate` for future V3
  integration PRs;
- prohibit force pushes and branch deletion;
- do not require linear history if merge commits remain the provenance-safe
  integration method;
- avoid imposing an approval rule that would deadlock a single-maintainer
  workflow unless an independent reviewer is actually available.

Branch-protection configuration is intentionally not changed by this review.

## Remaining non-blocking limitations

The following remain open and must not be confused with this software
integration decision:

1. Historical P7.7 synthetic SHA-256 sentinel values are not provenance-grade
   content digests.
2. The integrated pipeline does not wire a non-zero signed soil transport
   forcing into the current P7.5B pipeline path.
3. `PlantBiologicalForcing` remains runner-static rather than time-varying over
   a multi-step simulation.
4. Physical/empirical validation is incomplete.
5. The ERA5 NetCDF test emitted a NumPy binary-compatibility warning in the
   GitHub-hosted Python 3.12 environment and should be addressed by future
   dependency/packaging hardening.

None of these limitations changes `ACTIVE_PARAMETERS`, enables the UFOTRI
parameter database, or makes `V3_PHYSICS_READY` true.

## Final recommendation

The current V3 candidate line is technically suitable for protected main
integration, provided the actual merge remains a separate explicit action and
preserves existing commit identities.

```text
MAIN_MERGE_RECOMMENDED = TRUE
MAIN_MERGE_AUTHORIZED = FALSE
MAIN_MERGE_PERFORMED = FALSE
```
