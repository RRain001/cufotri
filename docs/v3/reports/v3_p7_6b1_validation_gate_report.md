# V3-P7.6B-1 validation-candidate gate report

Status: `PASS_PARAMETER_APPLICABILITY_REVIEW`

## Gate contract

`src/cteas_ufotri/parameters_v3/validation_gate.py` exposes a pure,
fail-closed candidate-identification function. It does not look up a runtime
parameter and does not mutate an evidence or applicability record.

A record is eligible only when all of the following hold:

1. P7.6A evidence status is `EVIDENCE_FOUND` but not `VALIDATED` or `ACTIVE`;
2. the source is not `TEST_ONLY` and the class is not
   `TEST_ONLY_PARAMETER`;
3. the applicability is `DIRECT_MATCH` with direct equation and unit matches,
   or is `PARTIAL_MATCH` with a compatible equation match, direct unit match,
   and `uncertainty_available: true`.

`UNKNOWN`, `TRANSFER_REQUIRED`, and `NOT_APPLICABLE` are blocked. A direct
match does not bypass the evidence-status and test-only restrictions.

## Executed result

```text
reviewed_records = 76
validation_candidates_identified = TRUE
candidate_count = 0
blocked_records = 76
calibration_started = FALSE
active_database = FALSE
```

The 56 provisional records are blocked because their evidence status is not
`EVIDENCE_FOUND`. The 20 `EVIDENCE_FOUND` records are blocked because they
are synthetic P7.5/P7.5B test fixtures, not physical evidence. No row has a
direct/partial/transfer applicability disposition in the current matrix.

The empty candidate set is an identified, auditable result—not a missing
review. P7.6B-2 can proceed to protocol design, but it must first acquire
actual source packages if it is to admit a physical validation candidate.

## Prohibited effects verified

- no parameter value was imported or replaced;
- no numerical calibration or observation fitting was run;
- no active database or runtime lookup was created;
- no solver equation, P6 module, P7.5 pipeline, or P7.5B coupling was changed.
