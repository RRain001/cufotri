# D3 V2 blinding failure and true-reblinding boundary

```text
REVIEW_TARGET =
a5af7e862b2860e4f3e441d7f3582eb0ffce01d4

V1_STATUS =
FAILED_BACKGROUND_ENCODING

V2_NUMERICAL_STATUS =
SUCCESSFUL_DIAGNOSTIC_ONLY

V2_BLINDING_STATUS =
INVALID_TRUTH_MAPPING_PREEXPOSED

V2_EMPIRICAL_OR_BLIND_VALIDATION_CLAIM =
FALSE

REAL_EXTERNAL_EVIDENCE =
FALSE

FORMAL_V3_PHYSICS =
NOT_STARTED

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Failure finding

The V2 pre-unblinding classification commit
`f69dee0fb9a7e88e6c3ceebbde6bdd73adc9bdf2` inherited the V1
`unblinding_comparison.csv` and unblinded report. Those tracked files already
mapped A to frozen H2, B to frozen H3 and C to the synthetic out-of-model
challenge. V2 reused the same A/B/C identifiers and mapping. Consequently,
the V2 manifest statement `truth_mapping_disclosed: false` did not describe
the complete commit tree, and V2 was not a valid blinded realization.

Deleting those files now, renaming A/B/C, or rewriting the historical commits
would not restore blinding because the mapping is already public in Git
history. V2 remains useful only as a numerical diagnostic rehearsal. It is
not blind validation, empirical validation, trusted-registry evidence, or
authorization to select H2/H3.

## Preserved audit history

The following artifacts and commits remain immutable:

- the V1 exact-0.5-percent-background forcing and failed classification;
- the V1 classification and unblinding commits;
- the V1 archive copies;
- the V2 background-bound amendment;
- the V2 datasets, classification and unblinding results;
- the independent review finding that invalidated V2 blinding.

```text
V1_ARCHIVE_CONTENT_INTEGRITY =
PASS

V1_ARCHIVE_COMMIT_CHRONOLOGY =
NONCOMPLIANT_WITH_PLANNED_ORDER

V1_SCIENTIFIC_USE =
FAILURE_RECORD_ONLY
```

The V1 failure was committed before the background amendment, and its archive
contents reproduce byte-for-byte. The physical archive-copy commit occurred
after the background amendment commit, however. This chronology is recorded
as noncompliant and must not be rewritten.

## True-reblinding remediation boundary

A valid replacement must retain the frozen H2/H3 parameters, V2 forcing,
primary observable, sampling times, challenge definition and classification
thresholds while generating exactly one new private realization with:

- new non-A/B/C opaque identifiers;
- new biological-observation noise;
- a private CSPRNG-generated permutation and observation secret;
- a tracked commitment to the secret, but no tracked secret or truth mapping;
- a preclassification contamination scan;
- classification in a clean worktree that never contains the secret or truth
  key;
- a committed classification result before the first unblinding access.

The first generated realization is final. It must not be regenerated or
retried after classification, even if its result is failed or inconclusive.
