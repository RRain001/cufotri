# D3 prospective synthetic experiment dry-run report

## Executive decision

The acquisition research was independently reproduced and merged locally by
fast-forward. The prospective assumptions, forcing, blinded data, classifier,
unblinding and intake workflow are reproducible. The fail-closed classifier
correctly returned `DATA_INCONCLUSIVE` for the out-of-model challenge, but it
also returned `DATA_INCONCLUSIVE` for both H2 and H3 positive controls.

```text
EVIDENCE_CLASS =
SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN

REAL_EXTERNAL_EVIDENCE = FALSE
EMPIRICAL_VALIDATION_CLAIM = FALSE
TRUSTED_REGISTRY_ELIGIBLE = FALSE
PRODUCTION_ELIGIBLE = FALSE

H2_TRUTH_CLASSIFICATION = FAIL_DATA_INCONCLUSIVE
H3_TRUTH_CLASSIFICATION = FAIL_DATA_INCONCLUSIVE
OUT_OF_MODEL_CHALLENGE = PASS_DATA_INCONCLUSIVE

H2_H3_FORMAL_SELECTION = NOT_AUTHORIZED
FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

The result is a successful end-to-end process rehearsal but a failed
positive-control discrimination result. It must not be rewritten as a
successful H2/H3 classifier validation.

## Milestone status

| milestone | status |
|---|---|
| external acquisition package independently reviewed and merged | PASS, local fast-forward merge |
| D3 prospective experiment assumptions frozen | PASS |
| blinded synthetic experiment datasets generated | PASS, bytewise reproducible |
| intake and H2/H3 classification dry run completed | COMPLETE_WITH_POSITIVE_CONTROL_FAILURE |
| real experiment execution package finalized | READY_FOR_LAB_FEASIBILITY_REVIEW; COMMISSIONING_HOLD |

The local acquisition merge and dry-run branch have not been merged or pushed
to remote `main`.

## Frozen assumptions and forcing

`D3_PROSPECTIVE_ASSUMPTIONS_V1` marks every planning number as
`PROJECT_ASSUMPTION_NOT_LITERATURE_FACT`. The frozen H2/H3 parameters remain
bound to source commit
`4b79f62741db4d4b51f4d608df33d2e13c499636` and parameter-result hash
`f95f27fe6ce601af688c1a40d3b23619d11374e0c4151d8c1a702d0c6a2160a9`.
No parameter was fitted.

The 5-minute forcing contains 288 exposure intervals and a 120 h
post-exposure record. The exposure mean is exactly 5270 Bq/mL water with CV
5%. The primary synthetic background is positive, with mean 0.5% and maximum
0.628% of the setpoint. A separate strict-zero background scenario is
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
| A | H2 frozen | DATA_INCONCLUSIVE | 0.147996 dex |
| B | H3 frozen | DATA_INCONCLUSIVE | 0.141807 dex |
| C | synthetic out-of-model challenge | DATA_INCONCLUSIVE | 0.104248 dex |

The classification result was committed before the local truth key was read.
The truth-key SHA-256 matched the committed record. Thresholds, seeds, data and
aggregation were not changed after unblinding.

## Replicate and noise sensitivity

Each of 60 truth/replicate/CV cells used 1,000 Monte Carlo experiments.

| replicates | H2 correct at CV20 | H3 correct at CV20 | challenge false confident |
|---:|---:|---:|---:|
| 3 | 0.239 | 0.183 | 0.019 |
| 4 | 0.250 | 0.229 | 0.011 |
| 5 | 0.285 | 0.257 | 0.007 |
| 6 | 0.307 | 0.268 | 0.010 |

No replicate count from 3 to 6 meets the required 90% accuracy for both truth
models at CV20. All counts meet the challenge false-confident maximum of 10%.
Five remains the operational planning default for sample-loss and anomaly
resistance, but it is not a power proof.

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

The package is ready for laboratory feasibility discussion, but commissioning
as a decisive H2/H3 experiment is on hold. A new preregistered design or power
analysis must resolve the positive-control failure without tuning against real
observations.
