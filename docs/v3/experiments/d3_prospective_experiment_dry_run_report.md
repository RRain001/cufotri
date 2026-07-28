# D3 prospective synthetic experiment dry-run report

## Executive decision

The acquisition research was independently reproduced and merged locally by
fast-forward. V1 was reproducible but exposed a background-bound encoding
defect. The corrected V2 rerun preserved that failure, froze its amendment
before new data generation, selected the matching model for both positive
controls and returned `DATA_INCONCLUSIVE` for the out-of-model challenge.

```text
EVIDENCE_CLASS =
SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN

REAL_EXTERNAL_EVIDENCE = FALSE
EMPIRICAL_VALIDATION_CLAIM = FALSE
TRUSTED_REGISTRY_ELIGIBLE = FALSE
PRODUCTION_ELIGIBLE = FALSE

H2_TRUTH_CLASSIFICATION = PASS
H3_TRUTH_CLASSIFICATION = PASS
OUT_OF_MODEL_CHALLENGE = PASS_DATA_INCONCLUSIVE

H2_H3_FORMAL_SELECTION = NOT_AUTHORIZED
FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

The result is a successful synthetic process rehearsal, not empirical
classifier validation and not authorization to select formal V3 physics.

## Milestone status

| milestone | status |
|---|---|
| external acquisition package independently reviewed and merged | PASS, local fast-forward merge |
| D3 prospective experiment assumptions frozen | PASS |
| blinded synthetic experiment datasets generated | PASS, bytewise reproducible |
| intake and H2/H3 classification dry run completed | PASS_ALL_3_EXPECTATIONS |
| real experiment execution package finalized | READY_FOR_LAB_FEASIBILITY_AND_COMMISSIONING |

The local acquisition merge and dry-run branch have not been merged or pushed
to remote `main`.

## Frozen assumptions and forcing

V1 encoded an upper-bound background target as an exact 0.5% mean; its failed
classification and sensitivity results remain under `reports/archive/` and
`results/archive/`. The V2 amendment was committed before rerun and marks every
planning number as `PROJECT_ASSUMPTION_NOT_LITERATURE_FACT`. The frozen H2/H3
parameters remain bound to source commit
`4b79f62741db4d4b51f4d608df33d2e13c499636` and parameter-result hash
`f95f27fe6ce601af688c1a40d3b23619d11374e0c4151d8c1a702d0c6a2160a9`.
No parameter was fitted.

The 5-minute forcing contains 288 exposure intervals and a 120 h
post-exposure record. The exposure mean is exactly 5270 Bq/mL water with CV
5%. The primary V2 synthetic background is positive, with mean 0.25% and
maximum 0.2821% of the setpoint, below the 0.5% target maximum. A separate
strict-zero background scenario is
sensitivity-only. Both files regenerate byte-for-byte.

## Blinded datasets and boundary

Each tracked A/B/C file contains seven time points and five biological
replicates per time. The files expose only total combined-stem-and-leaf TFWT,
sample masses, uncertainty, detection-limit flags and synthetic status.

```text
SYNTHETIC_STATUS = SYNTHETIC_NOT_EXTERNAL_EVIDENCE
TRUTH_KEY_GIT_TRACKED = FALSE
TRACKED_TRUTH_ARTIFACT = SHA256_ONLY
TRUTH_MAPPING_DISCLOSED_BEFORE_CLASSIFICATION_COMMIT = FALSE
```

CV20, one-missing-replicate, flagged-outlier and detection-limit variants are
local ignored dry-run files. Below-detection simulated values are retained
with explicit flags and are not silently replaced.

## Blind classification and unblinding

The classifier used only the arithmetic mean total plant-body TFWT at 0.2,
48 and 120 h. It did not use diagnostic times, pods, roots or latent pools.
The decision thresholds were frozen at 0.15 dex for inconclusive and 0.50 dex
for both inadequate.

| blind ID | truth after unblinding | result | absolute RMSE difference |
|---|---|---|---:|
| A | H2 frozen | H2_SUPPORTED_OVER_H3 | 0.212114 dex |
| B | H3 frozen | H3_SUPPORTED_OVER_H2 | 0.205910 dex |
| C | synthetic out-of-model challenge | DATA_INCONCLUSIVE | 0.105341 dex |

The V2 classification result was committed at
`f69dee0fb9a7e88e6c3ceebbde6bdd73adc9bdf2` before the local truth key was
read. The truth-key SHA-256 matched the committed record. Thresholds, seeds and
H2/H3 parameters were unchanged from V1.

## Replicate and noise sensitivity

Each of 60 truth/replicate/CV cells used 1,000 Monte Carlo experiments.

| replicates | H2 correct at CV20 | H3 correct at CV20 | challenge false confident |
|---:|---:|---:|---:|
| 3 | 0.869 | 0.846 | 0.067 |
| 4 | 0.914 | 0.877 | 0.047 |
| 5 | 0.937 | 0.927 | 0.035 |
| 6 | 0.955 | 0.955 | 0.027 |

Five and six replicates meet the required 90% accuracy for both truth models at
CV20. All four counts meet the challenge false-confident maximum of 10%.
Five remains the minimum operational planning default that meets the synthetic
target, but it is not empirical power proof.

## Intake dry run

The intake workflow copied each blinded file to a local ignored read-only
snapshot, generated SHA-256 entries and independently checked schema, units,
missing values, numeric finiteness, fresh/dry/tissue-water consistency,
detection-limit flags and synthetic status.

```text
INTAKE_STATUS = PASS_SYNTHETIC_INTAKE_WORKFLOW
LICENCE = SYNTHETIC_INTERNAL_TEST_DATA
REGISTRY_ELIGIBILITY = FALSE
PRODUCTION_ELIGIBILITY = FALSE
REAL_EXTERNAL_VALIDATION = NOT_STARTED
```

No trusted-registry entry was created or modified.

## Real experiment package decision

The logistics package now separates:

- minimum formal sampling: 0.2, 48 and 120 h, five biological replicates,
  project planning total 30 plants including controls and reserve;
- recommended diagnostic sampling: 0.2, 1, 6, 24, 48, 72 and 120 h, project
  planning total 57 plants including controls and reserve.

The plant counts, 250 Bq/L detection limit, mass resolution and chamber control
bands are project assumptions requiring laboratory confirmation. Operation at
5270 Bq/mL water requires facility-specific radiation-safety review.

The package is ready for laboratory feasibility and commissioning review,
subject to facility-specific radiation safety, achievable background,
detection limit, uncertainty and sample-capacity confirmation.

## Repository verification

The D3 prospective and acquisition targeted set passes 53/53. The V3
external-evidence unblocking verifier now passes fail-closed because tracked
synthetic artifacts reside under the benchmark `blinded/` directory and
`validation/external_local` contains no tracked data. The post-amendment full
suite passes 619/619 with one pre-existing NumPy binary-compatibility warning.
V1/V2 recomputation and readiness, V3 compatibility and architecture,
compile-all and both V3 gate verifiers pass. The physics gate remains
`BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA`.

No `src/`, formal `configs/` or trusted-registry file changed, and no V3 tag
was created.
