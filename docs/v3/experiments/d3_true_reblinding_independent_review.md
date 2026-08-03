# D3 V3 true-reblinding independent review

```text
REMEDIATION_REVIEW_TARGET =
9bcb7d986148a299384291e1ae0e610e437e057b

INDEPENDENT_REVIEW_WORKTREE =
/Users/rain/Documents/Doctor/Topic/CETAS_ufotri_d3_v3_true_reblinding_independent_review

INDEPENDENT_REVIEW_BRANCH =
codex/v3-d3-prospective-true-reblinding-independent-review

D3_PROSPECTIVE_INDEPENDENT_REVIEW =
PASS_REPRODUCIBLE_TRUE_REBLINDING

V1_STATUS =
FAILED_ARCHIVED

V2_STATUS =
NUMERICALLY_USEFUL_BUT_BLINDING_INVALID

V3_REBLINDING =
PASS

REAL_EXTERNAL_EVIDENCE =
FALSE

TRUSTED_REGISTRY_ELIGIBILITY =
FALSE

PRODUCTION_ELIGIBILITY =
FALSE

FORMAL_V3_PHYSICS =
NOT_STARTED

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Independent review scope

The review started from the final remediation target in a new worktree. It
did not reuse the failed A/B/C review environment. Git-ignored local forcing
and sealed-secret evidence were copied read-only only after V3 unblinding, so
the reviewer could run the full repository regression and independently
verify the secret commitment.

The review independently checked:

1. preservation of the V1 and V2 failure histories;
2. explicit invalidation of V2 blind-validation status;
3. absence of the new opaque IDs before the V3 preclassification commit;
4. non-reuse of V1/V2 dataset hashes;
5. Git ignore and SHA-256 commitment of the private generation secret;
6. absence of the secret and truth key from the classifier worktree;
7. absence of a new truth mapping in the preclassification and classification
   commit trees;
8. strict preclassification → classification → unblinding ancestry;
9. exactly one V3 dataset realization and one classification attempt;
10. no result-dependent regeneration or retry.

## Preserved failure record

```text
V1_ARCHIVE_CONTENT_INTEGRITY =
PASS

V1_ARCHIVE_COMMIT_CHRONOLOGY =
NONCOMPLIANT_WITH_PLANNED_ORDER

V1_SCIENTIFIC_USE =
FAILURE_RECORD_ONLY

V2_BLINDING_STATUS =
INVALID_TRUTH_MAPPING_PREEXPOSED
```

No historical commit was rewritten or deleted. The V1 archive contents remain
valid failure evidence even though the physical archive-copy commit occurred
after the background-amendment commit. V2 remains a numerical diagnostic only.

## True-reblinding chronology

```text
TRUE_REBLINDING_PRECLASSIFICATION_COMMIT =
b616d934fb0ae9d4abc90543d598de7c3754af23

TRUE_BLIND_CLASSIFICATION_COMMIT =
d8ae38373d63f2d4faa9ec0dede3f032077c98d3

TRUE_REBLINDING_UNBLINDING_COMMIT =
48b779980644a86471a049a8b5d3272f5ae9ec7a

STRICT_GIT_ANCESTRY =
PASS

GENERATION_ATTEMPTS =
1

CLASSIFICATION_ATTEMPTS =
1
```

The opaque IDs were `2L9ET5`, `4SUJBR` and `VYBVXE`. They were absent from
the parent of the preclassification commit and appeared preclassification
only in their blinded CSV, generation manifest and contamination scan. No
preclassification line associated an ID with H2, H3, challenge, truth class,
expected result or truth mapping.

The three new dataset hashes were:

| opaque ID | SHA-256 |
|---|---|
| `2L9ET5` | `e1ac2774f08e8fec1d100efef61b6850af9c77f80da06759ee56730cd7007f43` |
| `4SUJBR` | `6e4b145b08ffde7871163c5881e31513ced97fdc149e47c6197e48af6ea3c037` |
| `VYBVXE` | `fd1d0c4e16876347042d71635ee137779cb240597926c78bcd189ffaf3392158` |

All differed from the three V1 and three V2 hashes. The private sealed secret
was not tracked, remained covered by `validation/external_local/.gitignore`,
and independently matched the tracked commitment
`00cef70341c21220e0e3913ff93e59315e5a5a16c313bd5e62a8058323ccefef`.

The actual classifier worktree contained only the tracked
`validation/external_local/.gitignore` and `README.md`; it did not contain the
V3 private directory. Static source review also confirmed that the classifier
does not reference the secret path, truth-key path, secret-to-mapping function
or truth class.

## Independent classification and unblinding

The reviewer independently computed arithmetic mean total plant-body TFWT at
0.2, 48 and 120 h, then applied the frozen 0.15/0.50 dex log10-RMSE rules.

| opaque ID | H2 RMSE | H3 RMSE | independent blind result |
|---|---:|---:|---|
| `2L9ET5` | 0.153031 | 0.090442 | `DATA_INCONCLUSIVE` |
| `4SUJBR` | 0.231402 | 0.029816 | `H3_SUPPORTED_OVER_H2` |
| `VYBVXE` | 0.045379 | 0.252258 | `H2_SUPPORTED_OVER_H3` |

Only after matching the committed blind-classification result was the tracked
unblinding comparison checked:

```text
H2_TRUTH =
PASS_H2_SUPPORTED_OVER_H3

H3_TRUTH =
PASS_H3_SUPPORTED_OVER_H2

OUT_OF_MODEL_CHALLENGE =
PASS_DATA_INCONCLUSIVE

UNBLINDING_EXPECTATION_STATUS =
PASS_3_OF_3
```

## Independent Monte Carlo

The review did not read the existing Monte Carlo result CSVs. It independently
recomputed all 60 cells:

```text
4 replicate counts
× 5 total-CV levels
× 3 truth classes
× 1000 trials per cell
```

At total CV 20%:

| replicates | H2 correct | H3 correct | challenge false confident |
|---:|---:|---:|---:|
| 3 | 0.869 | 0.846 | 0.067 |
| 4 | 0.914 | 0.877 | 0.047 |
| 5 | 0.937 | 0.927 | 0.035 |
| 6 | 0.955 | 0.955 | 0.027 |

Only five and six replicates met the frozen bidirectional 90% target while
remaining below 10% challenge false confidence. Five remains the default
because it is the smallest frozen planning count that passes; no parameter,
threshold, sampling time, forcing value or challenge definition was changed.

## Attack tests and verdict

The independent review added 26 tests. They include injected
`<opaque-ID>,H2` contamination, replacement by a prior V2 hash, source-level
secret/truth access, commit-tree mapping leakage, duplicate generation or
classification, chronology, independent sample-level classification and the
60-cell Monte Carlo.

```text
INDEPENDENT_REVIEW_TESTS =
PASS_26_OF_26

MODEL_PARAMETERS_CHANGED =
FALSE

FORCING_CHANGED =
FALSE

CLASSIFICATION_RULE_CHANGED =
FALSE

PRIMARY_TIMES_CHANGED =
FALSE

LAB_HANDOFF_STATUS =
READY_FOR_LAB_FEASIBILITY_CONFIRMATION
```

## Full regression and formal-scope audit

The first repository-wide run in this fresh worktree correctly failed because
Git-ignored SB1/SB4 and ERA5 evidence had not yet been copied. After the
existing local evidence was copied from the source worktree, raw evidence was
kept read-only and only the derived SB1/SB4 `generated_forcing` directories
were made writable for their existing regeneration tests.

```text
FULL_REPOSITORY_PYTEST =
PASS_671_OF_671

V1_RECOMPUTE_ACCEPTANCE =
PASS

V2_RECOMPUTE_ACCEPTANCE =
PASS

V2_VALIDATION_READINESS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY

V3_COMPATIBILITY =
PASS_BITWISE_WHERE_DETERMINISTIC

V3_ARCHITECTURE =
READY_ARCHITECTURE_ONLY

V3_EXTERNAL_EVIDENCE_UNBLOCKING =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

COMPILEALL =
PASS

FORMAL_SRC_DIFF =
0

FORMAL_CONFIG_DIFF =
0

TRUSTED_REGISTRY_DIFF =
0
```

The only warning was the pre-existing NumPy/NetCDF binary-compatibility
runtime warning in the independent SB1 ERA5 semantics test.

The review therefore recommends the synthetic true-reblinding dry-run
infrastructure for fast-forward integration while retaining the fail-closed
external-evidence and V3-physics boundaries.
