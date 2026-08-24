# V3-P7.6C-1 evidence reconciliation report

## Source records

| Evidence ID | Authority | Reported value | Normalized value | Lineage disposition | Independent stream count |
| --- | --- | ---: | ---: | --- | ---: |
| `evidence.nist.tritium_half_life.2000` | NIST, Lucas & Unterweger (2000) | `4500 +/- 8 d` | `388800000 +/- 691200 s` | `INDEPENDENT_EVALUATION` | 1 |
| `evidence.ddep.tritium_half_life.2006` | DDEP/LNE-LNHB/BIPM-5 (2006) | `4497 +/- 9 d` | `388540800 +/- 777600 s` | `DERIVED_FROM_EXISTING_EVALUATION` | 0 |

NIST source: [NIST publication record](https://www.nist.gov/publications/comprehensive-review-and-critical-evaluation-half-life-tritium)
and [official NIST PDF](https://nvlpubs.nist.gov/nistpubs/jres/105/4/j54luc2.pdf).
DDEP source: [BIPM/DDEP comments on evaluations, Volumes 1-3](https://www.bipm.org/utils/common/pdf/monographieRI/Monographie_BIPM-5_Comments_Vol1-3.pdf).

## Independence audit

The DDEP comments explicitly state that the 3H experimental-data table was
taken from Lucas and Unterweger (2000), then report the adopted value
`12.312(25) years`, or `4497(9) days`. It is therefore a separate evaluated
recommendation with explicit derived lineage, not an independent measurement
stream. The registry counts one independent stream and retains both source
records. A duplicate representation would likewise remain visible but would
contribute zero independent streams.

## Reconciliation rule and result

The rule is pairwise comparison after explicit conversion to seconds. No
arithmetic average, inverse-variance weighting, or newest-source-only shortcut
was used. The absolute difference is `259200 s`; the ratio to the combined
standard uncertainty is `0.24913644`, below the configured threshold of `2.0`.
The values are therefore consistent. Because DDEP is the later recognized
evaluated recommendation and supplies explicit lineage, its reported value is
selected unchanged.

```text
source_agreement_status = CONSISTENT_DERIVED_EVALUATIONS
reconciliation_method = LATEST_RECOGNIZED_EVALUATED_RECOMMENDATION_WITH_EXPLICIT_LINEAGE
selected_source = evidence.ddep.tritium_half_life.2006
blind_averaging = FALSE
```

If lineage becomes unknown or a future source conflicts beyond the rule,
P7.6C-1 must produce `HOLD_EVIDENCE_RECONCILIATION_REQUIRED` and retain
`VALIDATION_CANDIDATE`.
