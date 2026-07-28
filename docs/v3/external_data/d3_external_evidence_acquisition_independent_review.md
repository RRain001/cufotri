# D3 external-evidence acquisition independent review

## Decision

```text
ACQUISITION_INDEPENDENT_REVIEW =
PASS_REPRODUCIBLE_NO_EXECUTABLE_PUBLIC_DATA

MERGE_RECOMMENDATION =
READY_TO_MERGE_ACQUISITION_RESEARCH

REAL_EXTERNAL_VALIDATION =
NOT_STARTED

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

This review authorizes integration of the acquisition research package only.
It does not authorize calibration, H2/H3 parameter refitting, H2/H3 formal
selection, trusted-registry modification, production physics, or an empirical
validation claim.

## Reviewed baseline and independence boundary

- Requested acquisition target:
  `2979e47153a8d162ed03d41997cd576d1d4cc059`.
- Main baseline:
  `1f44f8f847e8869e09b6f87262b81cafc2f2828e`.
- Final reviewed acquisition descendant:
  `a686be3d01058ca558a80cd11e0bf99338777ebe`.
- Independent worktree:
  `CETAS_ufotri_d3_acquisition_independent_review`.
- Review branch:
  `codex/v3-d3-external-acquisition-independent-review`.

The final reviewed descendant differs from the requested target only by removal
of four Markdown trailing-whitespace instances found by the independent review.
The formatting cleanup changes no candidate, tier, evidence, request, registry,
or gate semantics.

Git-ignored SB1/SB4 evidence and the two frozen ERA5 verifier inputs were copied
from the main checkout into the fresh worktree only to execute the existing
full regression and verifier set. Source and copied content were compared
before use. The PDF and raw ERA5 inputs were kept read-only. These local files
remain outside Git and are not D3 candidate raw data.

## Independent acquisition findings

The YAML and CSV inventories were parsed independently rather than trusting the
acquisition test assertions.

```text
CANDIDATE_COUNT = 8
UNIQUE_CANDIDATE_ID_COUNT = 8
YAML_CSV_ID_SEQUENCE_MATCH = TRUE

TIER_A = 0
TIER_B = 0
TIER_C = 3
NON_EXECUTABLE = 5

PUBLIC_RAW_DATA_FOUND = FALSE
RAW_FILE_DOWNLOAD_COUNT = 0
REGISTRY_ELIGIBLE_CANDIDATE_COUNT = 0
SYNTHETIC_CANDIDATE_COUNT = 0
```

The three Tier C candidates contain numeric TFWT information that can support
bounded mechanism discussion, but none can execute the frozen D3 comparison.
Their decisive gaps include nonmatching exposure schedules, missing primary
sampling times, incomplete air/background forcing, absent sample-level raw
data, and unknown redistribution terms. The five remaining records have no
reusable numeric experiment table or are figure/abstract-only and are correctly
retained as non-executable.

The referenced EMRAS support workbooks were not silently reclassified as
absent:

```text
sbTbox.xls = REFERENCED_NOT_ACCESSIBLE
sbTHS.xls = REFERENCED_NOT_ACCESSIBLE
sbWR.xls = REFERENCED_NOT_ACCESSIBLE
```

The request contract and email draft agree:

```text
REQUEST_STATUS = DRAFT_READY_NOT_SENT
REQUEST_SENT = FALSE
AUTOMATIC_CONTACT_AUTHORIZED = FALSE
```

No D3 raw file is tracked. `validation/external_local` has only its tracked
`.gitignore` and `README.md`, and the inventory declares zero downloaded raw
files.

## Scope audit

Relative to the main baseline:

```text
FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0
TRUSTED_REGISTRY_CHANGE_COUNT = 0
```

The acquisition package changes only documentation, tests, and validation
artifacts. `git diff --check` is clean on the final reviewed descendant.

## Verification evidence

### Acquisition gate tests

```text
20 passed
```

The tests cover the inventory schema and score aggregation, tier counts,
unknown-value handling, raw-file tracking, SHA-256 manifest contract, licence
boundary, unsent request state, six-day minimum schedule, optional 120-day
follow-up, registry/production prohibitions, and eight fail-closed attacks.

### Full repository regression

```text
COLLECTED_TESTS = 586
FULL_REPOSITORY_REGRESSION = PASS
```

The first fresh-worktree run correctly failed because Git-ignored SB1/SB4
evidence was absent. After copying the existing evidence into the isolated
worktree, the full suite passed. A further sandboxed run exposed only the
expected inability to rewrite ignored generated forcing outside the writable
root; the effective run outside that sandbox restriction passed. No tracked
file was changed by the regression.

### Acceptance and V3 verifier set

```text
V1_ACCEPTANCE_RECOMPUTE = PASS
V2_ACCEPTANCE_RECOMPUTE = PASS
V2_VALIDATION_READINESS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY

V2_TO_V3_COMPATIBILITY_STATUS =
PASS_BITWISE_WHERE_DETERMINISTIC

V3_ARCHITECTURE_STATUS =
READY_ARCHITECTURE_ONLY

V3_EXTERNAL_EVIDENCE_UNBLOCKING_STATUS =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

V3_PHYSICS_IMPLEMENTATION_STATUS =
NOT_STARTED
```

The physics-start verifier reported no trusted empirical approval entry and
retained `EXTERNAL_EXPERIMENT_OR_FIELD_DATA` as the blocking reason.

## Limitations and allowed next action

This result demonstrates that the acquisition package is reproducible and
fail-closed; it does not add external evidence. The public search still has no
executable Tier A or Tier B dataset, the three EMRAS workbooks remain
inaccessible, no request has been sent, and no real experiment has begun.

The acquisition research and this report may be integrated with
`git merge --ff-only`. The next branch may perform a clearly labelled synthetic
prospective experiment dry run, but its data must remain ineligible for the
trusted registry and production physics.
