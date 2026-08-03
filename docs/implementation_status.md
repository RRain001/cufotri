# Implementation status

Updated: 2026-08-03

## D3 UFOTRI manual data mapping and laboratory handoff

The working branch `codex/v3-d3-ufotri-manual-data-mapping` was created from
the clean laboratory-handoff branch `codex/v3-d3-lab-feasibility-handoff` at
`72c757159807c692c4a4c792db41302356dbcd7e`. The read-only `ufotri_manual.md`
source was checked at SHA-256
`82c7c7f07975553a51e7ba1666a912f80096e5af4fc138aba6f45a120e6d3562`.
The manual-to-D3 matrix contains 100 fields and keeps manual case values
separate from D3 design values and modern QA fields. The D3 primary endpoint
is explicitly combined stem-and-leaf TFWT; roots, pods and seeds remain outside
the primary endpoint. The D3 planning LOD of 250 Bq/L is not a laboratory
capability claim.

```text
D3_UFOTRI_MANUAL_MAPPING_ID = D3_UFOTRI_MANUAL_DATA_FIELD_MAPPING_V1
D3_UFOTRI_MANUAL_MAPPING_STATUS = FROZEN_PRE_LAB
D3_UFOTRI_MANUAL_MAPPING_FIELDS = 100
D3_UFOTRI_MANUAL_EXPLICIT_FIELDS = 36
D3_UFOTRI_MANUAL_DERIVED_FIELDS = 10
D3_UFOTRI_D3_DESIGN_SPECIFIC_FIELDS = 34
D3_UFOTRI_MODERN_QA_FIELDS = 17
D3_UFOTRI_CONTROLLED_CHAMBER_NA_FIELDS = 7
D3_UFOTRI_UNRESOLVED_FIELDS = 3
D3_UFOTRI_MAPPING_TESTS = PASS_22_OF_22
D3_UFOTRI_MANUAL_MAPPING_REMEDIATION_R1 = HOLD_UNRESOLVED_EXTERNAL_INPUT
D3_UFOTRI_MANUAL_DATA_MAPPING_REMEDIATION_R1 = READY_FOR_INDEPENDENT_REREVIEW
D3_SCOPED_REMEDIATION_SELF_CHECK = PASS_SELF_CHECK
D3_TARGETED_MAPPING_RELATED_TESTS = PASS_107_OF_107_WITH_1_PRIVATE_SKIP
D3_CLEAN_WORKTREE_FULL_PYTEST = PASS_107_OF_108_WITH_1_EXPLICIT_PRIVATE_SKIP
D3_REPOSITORY_FULL_PYTEST_BASELINE = BLOCKED_24_FAILED_6_ERRORS_MISSING_IGNORED_EXTERNAL_INPUTS
D3_PORTABLE_CLEAN_WORKTREE_TESTS = PASS_WITH_DOCUMENTED_EXTERNAL_INPUT_SKIPS
D3_PORTABLE_FULL_PYTEST = PASS_660_WITH_51_DOCUMENTED_EXTERNAL_INPUT_SKIPS
D3_STRICT_EXTERNAL_INPUT_TESTS = BLOCKED_MISSING_SB1_SB4_INPUTS
D3_PRIVATE_SECRET_AUDIT = SKIP_PRIVATE_SECRET_NOT_AVAILABLE
D3_LOCAL_FULL_RECOMPUTE_WITH_EXTERNAL_INPUTS = HISTORICAL_PASS_NOT_REPRODUCED_IN_THIS_WORKTREE
D3_PORTABLE_ERA5_RECOMPUTE = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT
D3_ACCEPTANCE_AND_VERIFIERS = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT_WITH_EXIT_2_STATUS
D3_SRC_DIFF_FROM_MAIN = 0
D3_FORMAL_CONFIGS_DIFF_FROM_MAIN = 0
D3_TRUSTED_REGISTRY_DIFF_FROM_MAIN = 0
D3_REAL_EXPERIMENT = NOT_EXECUTED
D3_REAL_EXTERNAL_EVIDENCE = FALSE
D3_H2_H3_FORMAL_SELECTION = NOT_AUTHORIZED
D3_FORMAL_V3_PHYSICS = NOT_STARTED
D3_LAB_FEASIBILITY_STATUS = AWAITING_LAB_CONFIRMATION
D3_V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
D3_MAPPING_COMMIT_STATUS = R1_PUSHED_NOT_MERGED
```

The external-input portability remediation is isolated on branch
`codex/v3-external-input-test-portability-r1`, based on R1 snapshot
`29f59c83cb2ed6b8c4111799a3e3878c8b568b72`. Portable pytest runs preserve all
original numerical assertions and skip only tests marked as direct readers of
missing SB1, SB4, ERA5, or private-secret inputs. `--require-external-inputs`
converts missing required inputs into explicit failures with a complete missing
file list. Malformed or incomplete inputs are failures in both modes. No raw
data, placeholder, synthetic input, key, threshold, model source, or physics
gate was changed; the R1 snapshot was pushed, while this portability branch has
not yet been independently reviewed or merged.

## D3 discriminability review and external-evidence acquisition

The frozen H2/H3 D3 discriminability design was independently reproduced and
reviewed, then fast-forwarded through the design branch into `main` at
`1f44f8f847e8869e09b6f87262b81cafc2f2828e`. The independent review added 35
tests and returned `PASS`; it did not fit either candidate, use a latent pool,
or authorize formal V3 physics.

The acquisition branch froze its search protocol before searching. It found no
executable public Tier A or Tier B dataset. Three sources contain Tier C public
numeric evidence and five primary records are non-executable. The best request
target is the IAEA/KAERI EMRAS soybean package, whose three named forcing
workbooks are `REFERENCED_NOT_ACCESSIBLE`. A fresh worktree independently
reproduced the inventory and gate boundary, passed all 586 repository tests,
and fast-forwarded the reviewed acquisition research into local `main` at
`e0d6f89a34e75b939ec9fe64411d18f23866d76e`; that reviewed baseline was later
included in the D3 true-reblinding integration and pushed with the current
`main`.

```text
MERGED_D3_DESIGN_HEAD =
1f44f8f847e8869e09b6f87262b81cafc2f2828e
D3_MINIMUM_EXPERIMENT =
24H_EXPOSURE_PLUS_120H_FOLLOWUP_EQUALS_144H
D3_EXTENDED_120_DAY_FOLLOWUP = OPTIONAL
D3_INDEPENDENT_REVIEW_TEST_STATUS = PASS_35_OF_35
D3_RESEARCH_MERGE_STATUS = MERGED_AND_PUSHED

D3_ACQUISITION_BRANCH =
codex/v3-d3-external-evidence-acquisition
D3_ACQUISITION_INDEPENDENT_REVIEW =
PASS_REPRODUCIBLE_NO_EXECUTABLE_PUBLIC_DATA
D3_ACQUISITION_REVIEW_HEAD =
e0d6f89a34e75b939ec9fe64411d18f23866d76e
D3_ACQUISITION_BRANCH_MERGE = MERGED_AND_PUSHED_VIA_MAIN
D3_EXTERNAL_SEARCH_STATUS =
COMPLETE_NO_EXECUTABLE_PUBLIC_DATA
D3_TIER_COUNTS = A_0_B_0_C_3_NON_EXECUTABLE_5
D3_PUBLIC_RAW_DATA_FOUND = FALSE
D3_PUBLIC_NUMERIC_DATA_FOUND = TRUE
D3_RAW_FILE_DOWNLOAD_COUNT = 0
D3_EMRAS_ATTACHMENT_STATUS =
REFERENCED_NOT_ACCESSIBLE_ALL_3
D3_DATA_REQUEST_STATUS = DRAFT_READY_NOT_SENT
D3_EXPERIMENT_COMMISSION_PACKAGE_STATUS = READY
D3_ACQUISITION_TEST_STATUS = PASS_20_OF_20
D3_FULL_REPOSITORY_TEST_STATUS = PASS_586

D3_REAL_EXTERNAL_VALIDATION_RUN = NOT_STARTED
D3_TRUSTED_REGISTRY_CHANGE_COUNT = 0
D3_H2_H3_FORMAL_SELECTION = NOT_AUTHORIZED
D3_FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## D3 prospective synthetic experiment dry run

The branch `codex/v3-d3-prospective-experiment-dry-run` was created from the
locally merged acquisition review. V1 exposed a specification defect: the
post-exposure target of at most 0.5% of setpoint had been encoded as an exact
0.5% mean. Its positive-control failure remains archived. The prospectively
committed `D3_PROSPECTIVE_ASSUMPTIONS_V2` amendment separates a 0.25%
operational synthetic mean from the 0.5% target upper bound. It marks every
planning number as `PROJECT_ASSUMPTION_NOT_LITERATURE_FACT` and does not change
the frozen H2/H3 parameters, seeds or classifier thresholds.

The first executable stage generates 5-minute synthetic chamber forcing for a
24 h exposure and 120 h follow-up. The exposure time-weighted mean is exactly
5270 Bq/mL water with CV 5%. The default background remains positive and
measured in the synthetic record; a separate strict-zero background file is a
sensitivity scenario. Both files regenerate byte-for-byte from the frozen
seed and remain Git-ignored local dry-run data.

Terminology note for this historical dry-run paragraph: its unqualified
`5270 Bq/mL water` is shorthand for `5270 Bq/mL air-moisture water` in the
`HTO_IN_CHAMBER_AIR_MOISTURE` medium. It is not a liquid culture, irrigation
or reservoir-water concentration. This note clarifies the historical wording
without changing the synthetic result.

V2 tracked three sample-level datasets under A/B/C. Its classification commit
`f69dee0fb9a7e88e6c3ceebbde6bdd73adc9bdf2` preceded the V2 unblinding
commit, but the commit tree still contained the V1 A/B/C truth mapping. Because
V2 reused that mapping, it is numerically useful only and is not a valid blind
test. This failure is preserved without rewriting V1/V2 history.

V3 true reblinding froze the failure record and protocol before generating
exactly one new private realization. A system-CSPRNG secret produced three new
opaque IDs, a new biological-noise realization and a new private permutation.
The secret and truth key remain Git-ignored; only the secret SHA-256 commitment
is tracked. The preclassification commit contains no new ID-to-truth mapping,
and classification ran in a separate clean worktree with no V3 private files.
The classification commit was created before the first secret/truth-key read.
The single realization passed H2, H3 and out-of-model expectations 3/3. A new
independent review recomputed the sample-level classification and all 60 Monte
Carlo cells without reading the prior result CSVs.

```text
D3_PROSPECTIVE_ASSUMPTIONS = V2_FORCING_FROZEN_AND_TRACEABLE
D3_DRY_RUN_BLINDING_V1 = FAILED_ARCHIVED
D3_V1_ARCHIVE_CONTENT_INTEGRITY = PASS
D3_V1_ARCHIVE_COMMIT_CHRONOLOGY =
NONCOMPLIANT_WITH_PLANNED_ORDER
D3_DRY_RUN_BLINDING_V2 =
INVALID_TRUTH_MAPPING_PREEXPOSED
D3_V2_NUMERICAL_STATUS = SUCCESSFUL_DIAGNOSTIC_ONLY
D3_V2_EMPIRICAL_OR_BLIND_VALIDATION_CLAIM = FALSE
D3_BACKGROUND_OPERATIONAL_MEAN_FRACTION = 0.0025
D3_BACKGROUND_TARGET_MAXIMUM_FRACTION = 0.005
D3_PROSPECTIVE_EVIDENCE_CLASS =
SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN
D3_FORCING_STATUS = PASS_SYNTHETIC_CONTROLLED_FORCING
D3_FORCING_INTERVAL = COMPLETE_5_MINUTE_AXIS
D3_FORCING_REGENERATION = PASS_BYTEWISE
D3_DRY_RUN_BLINDING_V3 = PASS_TRUE_REBLINDING
D3_V3_OPAQUE_IDS = 2L9ET5_4SUJBR_VYBVXE
D3_V3_OBSERVATION_REALIZATION_REUSED = FALSE
D3_V3_GENERATION_ATTEMPTS = 1
D3_V3_CLASSIFICATION_ATTEMPTS = 1
D3_V3_REGENERATION_OR_RETRY = PROHIBITED
D3_V3_SECRET_GIT_TRACKED = FALSE
D3_V3_TRUTH_KEY_GIT_TRACKED = FALSE
D3_V3_TRACKED_SECRET_ARTIFACT = SHA256_ONLY
D3_V3_PRECLASSIFICATION_CONTAMINATION_SCAN = PASS
D3_V3_PRECLASSIFICATION_COMMIT =
b616d934fb0ae9d4abc90543d598de7c3754af23
D3_V3_CLASSIFICATION_COMMIT =
d8ae38373d63f2d4faa9ec0dede3f032077c98d3
D3_V3_UNBLINDING_COMMIT =
48b779980644a86471a049a8b5d3272f5ae9ec7a
D3_V3_CLASSIFIER_WORKTREE_SECRET_STATUS = ABSENT
D3_CLASSIFICATION_PARAMETER_REFIT_COUNT = 0
D3_V3_UNBLINDING_STATUS = PASS_TRUE_REBLINDING
D3_V3_EXPECTATION_PASS_COUNT = 3_OF_3
D3_H2_TRUTH_CLASSIFICATION = PASS
D3_H3_TRUTH_CLASSIFICATION = PASS
D3_OUT_OF_MODEL_CHALLENGE = PASS_DATA_INCONCLUSIVE
D3_CV20_PASSING_REPLICATE_COUNTS_3_TO_6 = 5_AND_6
D3_CV20_H2_CORRECT_RANGE = 0.869_TO_0.955
D3_CV20_H3_CORRECT_RANGE = 0.846_TO_0.955
D3_CV20_CHALLENGE_FALSE_CONFIDENT_RANGE = 0.027_TO_0.067
D3_DEFAULT_PLANNING_REPLICATES = 5_SYNTHETIC_TARGET_PASS
D3_DATA_INTAKE_DRY_RUN = PASS_SYNTHETIC_INTAKE_WORKFLOW
D3_INTAKE_RAW_SNAPSHOT = READ_ONLY_GIT_IGNORED
D3_INTAKE_REGISTRY_ELIGIBLE = FALSE
D3_V3_REMEDIATION_TESTS = PASS_26_OF_26
D3_V3_INDEPENDENT_REVIEW_TESTS = PASS_26_OF_26
D3_V3_INDEPENDENT_REVIEW =
PASS_REPRODUCIBLE_TRUE_REBLINDING
D3_FULL_PYTEST = PASS_671_OF_671_ONE_KNOWN_NUMPY_ABI_WARNING
D3_V1_V2_AND_V3_COMPATIBILITY_ARCHITECTURE = PASS
D3_V3_EXTERNAL_UNBLOCKING_VERIFIER = PASS_FAIL_CLOSED
D3_TRUE_REBLINDING_BRANCH_MERGE = MERGED_AND_PUSHED_TO_MAIN
D3_TRUE_REBLINDING_MAIN_HEAD = 569f6bc9b1e86b15056a0b5f178a656c27c5e6b1
D3_TRUE_REBLINDING_REMOTE_ALIGNMENT = PASS_MAIN_EQUALS_ORIGIN_MAIN
D3_EXPERIMENT_PACKAGE =
READY_FOR_LAB_FEASIBILITY_CONFIRMATION
D3_EXPERIMENT_COMMISSIONING =
READY_SUBJECT_TO_LAB_SAFETY_AND_CAPABILITY_CONFIRMATION
D3_NEXT_STEP = LAB_FEASIBILITY_CONFIRMATION
D3_REAL_EXTERNAL_EVIDENCE = FALSE
D3_TRUSTED_REGISTRY_ELIGIBLE = FALSE
D3_EMPIRICAL_VALIDATION_CLAIM = FALSE
D3_FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## EMRAS soybean SB1 research benchmark branch

This section records the non-production benchmark executed on
`codex/v3-emras-soybean-sb1-pdf-era5` from main baseline
`ae23ac037781caa5d69e2b69adb7de7214549c85`. It does not supersede the
released V2 candidate, register trusted external evidence, or authorize V3
physics.

```text
SB1_CASE_ID = EMRAS_SOYBEAN_SB1_PDF_ERA5_V1
SB1_DATASET_STATUS = READY_PUBLISHED_TABLES_PLUS_ERA5
SB1_SITE_STATUS = PROVISIONAL_WITH_SPATIAL_SENSITIVITY
SB1_CHAMBER_FORCING_STATUS = PUBLISHED_RAW_AND_MEAN_CONSTRAINED
SB1_OUTDOOR_FORCING_STATUS = ERA5_COMPLETE_FIVE_POINTS
SB1_MODEL_INTERFACE_STATUS = RUNNABLE_WITH_VALIDATION_ADAPTER_ONLY
SB1_BASELINE_RUN_STATUS = PASS_7_OF_7
SB1_CALIBRATION_STATUS =
CALIBRATED_MODEL_DEVELOPMENT_ONLY_BOUNDARY_HIT
SB1_PSEUDO_HOLDOUT_STATUS = EXECUTED_7_OF_7_NO_PARAMETER_RECALL
SB1_IDENTIFIABILITY_STATUS = LIMITED_BOUNDARY_OR_CORRELATION
SB1_BENCHMARK_STATUS = EXECUTED_AND_REPRODUCIBLE
SB1_EMPIRICAL_VALIDATION = NOT_CLAIMED
SB1_PRODUCTION_GATE_ELIGIBLE = FALSE
SB1_TARGETED_TEST_STATUS = PASS_16
SB1_FULL_REGRESSION_STATUS = PASS_367_ONE_KNOWN_NUMPY_NETCDF_WARNING
SB1_V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
SB1_V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
SB1_V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
SB1_V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
SB1_FORMAL_PHYSICS_CHANGE_COUNT = 0
SB1_FORMAL_CONFIG_CHANGE_COUNT = 0
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
SB1_MERGE_RECOMMENDATION = READY_FOR_INDEPENDENT_BENCHMARK_REVIEW
```

The public IAEA tables were checked against rendered PDF pages. ERA5 is a
substitution for the unavailable organizer tower data, and the coordinate is
an institutional-area proxy rather than a confirmed plot. The primary model
reproduces only the first-hour scale and substantially underpredicts
plant-body TFWT after 24 h and the late residual platform. These limitations
are retained as scientific findings rather than removed by parameter
expansion.

## Independent SB1 review, merge and validation-only mechanism screen

The independent review branch rebuilt the benchmark from the source PDF and
five read-only raw ERA5 responses at exact benchmark head
`178fb0a3ebae53b20b101000cdbb2b39406088c0`. It added 27 independent tests,
confirmed the 24-2280 h structural underprediction, and returned
`PASS_REPRODUCIBLE_STRUCTURAL_DEFICIT`. The review was fast-forwarded through
the benchmark branch into `main`; merged `main` and `origin/main` are
`2a56c56d6de3ee79c1069b799a5dab90e10a0097`.

The subsequent branch
`codex/v3-sb1-plant-water-mechanism-discrimination` is validation-only. Its
protocol and all candidate ranges were committed before execution, and its
calibration parameters were committed before the late check. H1-H4 do not
modify `src/`, formal `configs/`, the trusted registry or a production gate.

```text
INDEPENDENT_SB1_BENCHMARK_REVIEW =
PASS_REPRODUCIBLE_STRUCTURAL_DEFICIT

SB1_BENCHMARK_MERGE_STATUS = MERGED_AND_PUSHED
MERGED_SB1_BASELINE_HEAD =
2a56c56d6de3ee79c1069b799a5dab90e10a0097

MECHANISM_PROTOCOL_STATUS = FROZEN_BEFORE_CANDIDATE_EXECUTION
MECHANISM_PARAMETER_STATUS = FROZEN_BEFORE_LATE_CHECK
MECHANISM_TARGETED_TEST_STATUS = PASS_17
MECHANISM_FULL_REGRESSION_STATUS =
PASS_411_ONE_KNOWN_NUMPY_NETCDF_WARNING
MECHANISM_V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
MECHANISM_V2_RECOMPUTE_STATUS =
PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
MECHANISM_V2_VALIDATION_READINESS_STATUS = PASS
MECHANISM_V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
MECHANISM_V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
MECHANISM_V3_EXTERNAL_EVIDENCE_STATUS =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA
MECHANISM_MASS_BALANCE_STATUS = PASS_35_OF_35
MECHANISM_FORCING_STATUS =
H1_0_OF_7_H2_7_OF_7_H3_4_OF_7_H4_0_OF_7
MECHANISM_DISCRIMINATION_STATUS =
NO_MINIMAL_MECHANISM_SUPPORTED
BEST_SUPPORTED_MECHANISM = NONE
FORMAL_V3_DESIGN_RECOMMENDATION = NOT_READY
MECHANISM_BRANCH_MERGE = NOT_REQUESTED
FORMAL_V3_PHYSICS_CHANGE = NOT_STARTED
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## EMRAS soybean SB4 frozen cross-experiment transfer

The SB1 mechanism result was independently reviewed at
`5c1d4bf39415be9b6e7960efeda23af50570f518`, fast-forwarded to `main` at
`d08d9d81f3ef10b11c2431e7bebe2f802c56cd18`, and pushed. The SB4 benchmark
branch starts from that exact merged main. It transcribes the SB4 publication
tables, reuses checksum-bound SB1 ERA5 raw inputs, and constructs two
explicitly reconstructed chamber profiles constrained to the reported SB4
mean.

The transfer protocol was committed before predictions. H2 and H3 parameters
come unchanged from SB1 frozen commit
`4b79f62741db4d4b51f4d608df33d2e13c499636`; no SB4 refit or selection
occurred. Both candidates pass all seven forcing scenarios under both profiles,
so the result supports only a bounded comparative design review, not a unique
mechanism or formal V3 implementation.

```text
SB1_MECHANISM_SCREEN = INDEPENDENTLY_REVIEWED_AND_MERGED
MERGED_MAIN_HEAD = d08d9d81f3ef10b11c2431e7bebe2f802c56cd18
SB4_CASE_ID = EMRAS_SOYBEAN_SB4_PDF_ERA5_V1
SB4_BRANCH = codex/v3-emras-soybean-sb4-transfer-benchmark
SB4_TESTED_EVIDENCE_PARENT = 8353611
SB4_DATA_STATUS = PASS_TRACEABLE_PUBLISHED_TABLE_TRANSCRIPTION
SB4_CHAMBER_PROFILE_STATUS = PASS_2_RECONSTRUCTED
SB4_ERA5_STATUS = PASS_REUSED_5_SB1_RAW_FILES_BY_CHECKSUM
SB4_PARAMETER_REFIT_COUNT = 0
SB4_RUN_STATUS = PASS_42_OF_42
SB4_H2_FORCING_STATUS = PASS_7_OF_7_BOTH_PROFILES
SB4_H3_FORCING_STATUS = PASS_7_OF_7_BOTH_PROFILES
SB4_MASS_BALANCE_STATUS = PASS_42_OF_42
SB4_TARGETED_TEST_STATUS = PASS_23
SB4_FULL_REGRESSION_STATUS =
PASS_458_ONE_KNOWN_NUMPY_NETCDF_WARNING
SB4_TRANSFER_STATUS = MULTIPLE_SLOW_MECHANISMS_TRANSFER_SUPPORTED
FORMAL_V3_DESIGN_RECOMMENDATION =
BOUNDED_COMPARATIVE_DESIGN_REVIEW_ONLY
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Current repository and release status

```text
CURRENT_RELEASED_MODEL =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE

CURRENT_MAIN_BASELINE_HEAD =
d08d9d81f3ef10b11c2431e7bebe2f802c56cd18

CURRENT_MAIN_HEAD =
d08d9d81f3ef10b11c2431e7bebe2f802c56cd18

CURRENT_DEVELOPMENT_BRANCH =
codex/v3-emras-soybean-sb4-transfer-benchmark

CURRENT_DEVELOPMENT_BASELINE_HEAD =
d08d9d81f3ef10b11c2431e7bebe2f802c56cd18

CURRENT_DEVELOPMENT_HEAD =
FINALIZED_ON_TOP_OF_TESTED_EVIDENCE_PARENT_8353611

CURRENT_DEVELOPMENT_STATUS =
SB4_TRANSFER_BENCHMARK_EXECUTED_AND_REPRODUCIBLE

CURRENT_TEST_STATUS =
PASS_458_ONE_KNOWN_NUMPY_NETCDF_WARNING

CURRENT_SB1_BENCHMARK_STATUS =
INDEPENDENTLY_REVIEWED_AND_MERGED

CURRENT_MECHANISM_BRANCH =
codex/v3-sb1-plant-water-mechanism-discrimination

CURRENT_MECHANISM_STATUS =
NO_MINIMAL_MECHANISM_SUPPORTED

CURRENT_MECHANISM_TEST_STATUS =
PASS_435_ONE_KNOWN_NUMPY_NETCDF_WARNING

CURRENT_V1_RECOMPUTE_STATUS =
PASS_5_FROZEN_CASES

CURRENT_V2_RECOMPUTE_STATUS =
PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE

CURRENT_V3_ARCHITECTURE_STATUS =
READY_ARCHITECTURE_ONLY

CURRENT_V3_PHYSICS_STATUS =
NOT_STARTED

FORMAL_V3_PHYSICS_STATUS =
NOT_STARTED

CURRENT_V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

CURRENT_EXTERNAL_EVIDENCE_PACKAGE_STATUS =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA

CURRENT_EXTERNAL_EVIDENCE_GATE_REMEDIATION_STATUS =
PASS_ADVERSARIAL_REVIEW_MERGED

CURRENT_SOYBEAN_DATA_STATUS =
BLOCKED_EXTERNAL_DATA

CURRENT_PREREGISTRATION_STATUS =
DRAFT_NOT_PREREGISTERED

CURRENT_CALIBRATION_STATUS =
NOT_RUN_BLOCKED_EXTERNAL_DATA

CURRENT_PARAMETER_IDENTIFIABILITY_STATUS =
NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE
```

The current released model is the immutable V2 candidate. The current `main`
publishes V3 architecture and the fail-closed external-evidence gate only.
The merged remediation replaces declaration
booleans with a runtime-validated artifact chain, strengthens numeric/checksum
intake validation, and passed the third independent adversarial review. It is
not a V3 physics release and contains no empirical data, calibration result,
or accepted holdout. The second remediation added a protected-ref approval
registry, stable-FD snapshots with final identity/hash rechecks, and
preregistered holdout-verdict recomputation. The third remediation binds
calibration, identifiability, and holdout to a canonical frozen parameter
contract.

## V3 external-evidence gate third remediation before independent review

The second independent review exposed an unbound preregistered parameter set.
The third remediation replaces the list with a canonical semantic contract
and binds calibration, identifiability, and holdout to the same names, units,
transforms, bounds, contract hash, and canonical result hash.

```text
F_04_STATUS = FIXED_PENDING_THIRD_INDEPENDENT_REVIEW
PREVIOUS_TARGETED_ATTACK_COUNT = 78
THIRD_REMEDIATION_ATTACK_COUNT = 37
TARGETED_ATTACK_STATUS = PASS_115
FULL_REGRESSION_STATUS = PASS_317
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY
V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
MERGE_RECOMMENDATION = HOLD_PENDING_THIRD_INDEPENDENT_REVIEW
```

### Third independent review and merge

The third independent worktree added 34 new cases without importing the
remediation fixture builder. All 149 targeted gate cases and all 351
repository tests passed on the merged main worktree.

```text
THIRD_INDEPENDENT_REVIEW_STATUS = PASS_ADVERSARIAL_REVIEW
F_01_STATUS = CONFIRMED_FIXED
F_02_STATUS = CONFIRMED_FIXED
F_03_STATUS = CONFIRMED_FIXED
F_04_STATUS = CONFIRMED_FIXED
THIRD_INDEPENDENT_ATTACK_COUNT = 34
TOTAL_TARGETED_GATE_STATUS = PASS_149
POST_MERGE_FULL_REGRESSION_STATUS = PASS_351
REMEDIATION_3_MERGE_STATUS = MERGED_BY_STRICT_FAST_FORWARD
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## V3 external-evidence gate second remediation

The three independent-review weaknesses were reproduced as three failing
attacks before repair. The imported attacks now pass together with the
original 32 attacks and 40 second-remediation tests.

```text
F_01_STATUS = FIXED_PENDING_SECOND_INDEPENDENT_REVIEW
F_02_STATUS = FIXED_PENDING_SECOND_INDEPENDENT_REVIEW
F_03_STATUS = FIXED_PENDING_SECOND_INDEPENDENT_REVIEW
TRUSTED_POLICY_PATH =
validation/v3/policy/trusted_external_evidence_registry.yaml
PRODUCTION_REGISTRY_ENTRY_COUNT = 0
TARGETED_ATTACK_STATUS = PASS_77
FULL_REGRESSION_STATUS = PASS_279
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY
V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
MERGE_RECOMMENDATION = HOLD_PENDING_SECOND_INDEPENDENT_REVIEW
```

## V3 external-evidence gate directed remediation

The two reproduced P1 issues were fixed without changing `src/` or `configs/`.
The physics gate now opens and validates raw, intake, preregistration,
calibration, identifiability, holdout, and regression artifacts; recomputes
raw/result checksums; verifies cross-artifact identifiers and hashes; and uses
Git object/history checks to prove that the frozen preregistration predates the
tracked holdout result. Synthetic/internal evidence types are explicitly
ineligible.

The soybean intake now parses required numeric columns, rejects empty,
non-numeric, NaN/Inf, invalid ranges, nonpositive chamber/mixing values,
invalid detection-limit/uncertainty mappings, duplicate or discontinuous
forcing timestamps, incomplete exposure coverage, split overlap, and checksum
tampering. Generated intake manifests are validated at runtime with
`jsonschema`.

```text
P1_01_STATUS = FIXED_PENDING_INDEPENDENT_REVIEW
P1_02_STATUS = FIXED_PENDING_INDEPENDENT_REVIEW
TEST_STATUS = PASS_234_ONE_KNOWN_NUMPY_NETCDF_WARNING
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
REMEDIATION_STATUS = READY_FOR_INDEPENDENT_ADVERSARIAL_REVIEW
MERGE_RECOMMENDATION = HOLD_PENDING_INDEPENDENT_REVIEW
```

## V3 architecture-only baseline

```text
MILESTONE_1 = V2_EXTERNAL_VALIDATION_PHASE1_MERGED
MILESTONE_2 = V3_ARCHITECTURE_BASELINE_READY
MILESTONE_3 = V3_EXTERNAL_EVIDENCE_INTAKE_READY
MILESTONE_4 = V3_PHYSICS_IMPLEMENTATION_GATE_REEVALUATED

V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_PHYSICS_IMPLEMENTATION_STATUS = NOT_STARTED
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

V2_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V1_GOLDEN_CASES = PASS_5_OF_5
V2_GOLDEN_CASES = PASS_6_OF_6
FORCING_72H_GOLDEN_STATUS = PASS_BITWISE
INDEPENDENT_REFERENCE_GOLDEN_STATUS = PASS_BITWISE

STATE_SCHEMA_STATUS = PASS
FLUX_SCHEMA_STATUS = PASS
LEDGER_CONTRACT_STATUS = PASS
CONFIG_RESULT_PROVENANCE_SCHEMA_STATUS = PASS
MODULE_REGISTRY_STATUS = PASS_8_UNIQUE
ADR_STATUS = PASS_8_COMPLETE
MIGRATION_MATRIX_STATUS = PASS_32_ROWS_COMPLETE
EXTERNAL_DATA_INTAKE_STATUS = PASS_FAIL_CLOSED

SOYBEAN_DATA_STATUS = BLOCKED_EXTERNAL_DATA
FIELD_DATA_STATUS = BLOCKED_EXTERNAL_DATA
PREREGISTRATION_STATUS = DRAFT_NOT_PREREGISTERED
CALIBRATION_STATUS = NOT_RUN_BLOCKED_EXTERNAL_DATA
PARAMETER_IDENTIFIABILITY_STATUS =
NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE

TEST_STATUS = PASS_191_ONE_KNOWN_NUMPY_NETCDF_WARNING
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY
COMPILE_STATUS = PASS
DIFF_CHECK_STATUS = PASS
```

The V3 branch changes no `src/` file and no V2 configuration. It contains
architecture, ADRs, fail-closed schemas, a lossless `v2_frozen` migration
envelope, deterministic golden compatibility checks, evidence-intake
scaffolding, and architecture/physics gates. It implements no advanced
re-emission equation, formal three-box coupling, dynamic-air solver, HT
chemistry, or broader food/dose physics.

The next stronger gate remains unavailable until a complete legally usable
experiment or field case is acquired, preregistered before holdout inspection,
calibrated with a separate holdout, assessed for parameter identifiability, and
executed against that holdout.

## Historical released-model and validation-readiness milestones

```text
HISTORICAL_RELEASE_MILESTONE =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE

HISTORICAL_RELEASE_BASIS =
RC2_INDEPENDENT_REAUDIT_ACCEPTED_WITH_MINOR_CORRECTIONS

HISTORICAL_RELEASE_BRANCH =
codex/v2-physics-remediation-rc2

HISTORICAL_RELEASE_SOURCE_HEAD =
CANDIDATE_FINALIZATION_COMMIT_RECORDED_IN_RELEASE_REPORT_AND_TAG

V1_BASELINE =
6918440faa3455b848f43589784672f3bfabfe3d

V1_TAG =
formal-minimal-baseline-v1

HISTORICAL_RELEASE_TEST_STATUS =
PASS_167_ONE_KNOWN_WARNING

FORMAL_SCOPE =
HTO_ONLY_RESEARCH_CANDIDATE

SITE_CALIBRATED =
NO

REGULATORY_VALIDATED =
NO

COMPLETE_UFOTRI_EQUIVALENCE =
NO

ANIMAL_STATE_NAMING_STATUS =
DOCUMENTED_COMPATIBILITY_LIMITATION_WITH_BQ_M2_ALIASES

VALIDATION_INFRASTRUCTURE_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY

HISTORICAL_VALIDATION_READINESS_BRANCH =
codex/v2-validation-readiness

EMPIRICAL_VALIDATION_STATUS =
BLOCKED_EXTERNAL_DATA

HISTORICAL_VALIDATION_READINESS_TEST_STATUS =
PASS_178_ONE_KNOWN_NUMPY_NETCDF_WARNING
```

The current physics acceptance basis is
`docs/v2/v2_rc2_independent_reaudit.md`, whose verdict is
`ACCEPT_RC2_WITH_MINOR_CORRECTIONS`. Release finalization resolves the named
provenance and current-status LOW findings without changing model results.
The five retained MEDIUM research limitations are frozen in
`docs/v2/v2_candidate_limitations.yaml`.

The post-candidate validation branch adds a 42-entry evidence registry,
external-data schemas, general metrics, an isolated validation runner,
forcing-completeness checks, parameter priorities, and closure plans for all
five MEDIUM limitations. `VALIDATION_READY` describes infrastructure, not
empirical validation: experiment, field, reference-model, complete observed
forcing, and site-case evidence remain absent and correctly blocked.

## Historical milestones

- V1 formal minimal baseline:
  `formal-minimal-baseline-v1` at `6918440faa3455b848f43589784672f3bfabfe3d`.
- Initial V2 self-assessment: historical candidate recommendation.
- Initial V2 independent audit: rejected for cross-module conservation and
  other evidence gaps.
- RC1 self-assessment: ready for independent re-audit.
- RC1 independent re-audit: `REJECT_RC1_REMEDIATION`.
- RC2 remediation status: candidate ready, held for independent review.
- RC2 independent re-audit:
  `ACCEPT_RC2_WITH_MINOR_CORRECTIONS`, with no BLOCKER or HIGH.

The complete immutable evidence chain is indexed in
`docs/v2/v2_audit_history.md`.

## Previous assessment: V2 physics remediation RC1 progress

Development branch: `codex/v2-physics-remediation-rc1`

```text
V2_STATUS = PHYSICS_REMEDIATION_RC1_CANDIDATE
FORMAL_ACCEPTANCE = PENDING_INDEPENDENT_REAUDIT
RC1_STAGE_1 = PASS
RC1_STAGE_2 = PASS
RC1_STAGE_3 = PASS
RC1_STAGE_4 = PASS
RC1_STAGE_5 = PASS
RC1_STAGE_6 = PASS
RC1_STAGE_7 = PASS
RC1_STAGE_8 = PASS
RC1_STAGE_9 = PASS
RC1_STAGE_10 = PASS
RC1_STAGE_11 = PASS
RC1_STAGE_12 = PASS_PREPARED_FOR_INDEPENDENT_REAUDIT
DRY_INTERFACE_CONSERVATION_STATUS = PASS
WET_INTERFACE_CONSERVATION_STATUS = PASS
DRY_WET_COMPETITION_STATUS = PASS
ACTIVITY_PROPAGATION_STATUS = PASS_STAGE_1_SCOPE
LEAF_RESISTANCE_METEOROLOGY_STATUS = PASS
LAI_APPLICATION_STATUS = PASS_NO_DOUBLE_COUNT
LEAF_END_TO_END_STATUS = PASS
BEEF_PRODUCTION_BOUNDARY_STATUS = PASS
MEAT_DOSE_CONSERVATION_STATUS = PASS
WET_PARAMETER_SOURCE_STATUS = PASS_DOCUMENTED_LITERATURE_COMPARISON
WET_PARAMETER_UNCERTAINTY_STATUS = PASS
ANALYTIC_BENCHMARK_COUNT = 10
MANUAL_OR_LITERATURE_NUMERIC_COUNT = 7
EXECUTION_ONLY_CASES_NOT_LABELLED_REFERENCE = PASS
FULL_MODEL_LHS_STATUS = PASS
SAMPLE_SIZE_CONVERGENCE_STATUS = PASS
MODE_AWARE_PARAMETER_STATUS = PASS
RANK_STABILITY_STATUS = LIMITED_WITH_EVIDENCE
PERENNIAL_PHENOLOGY_STATUS = PASS
MULTIYEAR_PASTURE_STATUS = PASS
MULTIBOX_SCOPE_STATUS = CLEAR_EXPERIMENTAL_STANDALONE
BLOCKER_REMAINING = 0
HIGH_REMAINING = 1_PARTIAL_H06_RANK_STABILITY
RC1_VERDICT = READY_FOR_INDEPENDENT_REAUDIT
INDEPENDENT_REAUDIT_RECOMMENDATION = PROCEED_BEFORE_FORMAL_ACCEPTANCE
RC1_TEST_STATUS = PASS_158
RC1_V1_RECOMPUTE_STATUS = PASS
RC1_V2_RECOMPUTE_STATUS = PASS
```

Stage 1 replaced the independent `v_d C_air` surface inventory input with
explicit dry and wet allocations of the plume-side loss. The two deposition
footprints are independent configuration objects and are not inferred from the
re-emission feedback area. The former `v_d C_air` value remains diagnostic
only. Tests cover the audited 72 h case, all five V2 configurations, footprint
scaling, dry/wet switches and zero limits, segment counts, the stack-input
upper bound, and surface inventory plus boundary-output closure.

Stage 2 replaced the fixed 50 s m-1 aerodynamic and boundary resistances with
the manual wind-profile equations plus a documented Golder
Pasquill-to-Monin-Obukhov mapping and a laminar flat-plate water-vapour
boundary correlation. The implementation is explicitly labelled
`LITERATURE_PARAMETERIZATION`, not validated UFOTRI equivalence. A new 72 h
formal case disables deposition and root uptake and independently propagates
air-leaf exchange through TFWT, OBT, edible leafy crop, and ingestion dose.
The mode-off control is zero, and the 600/300/120/60 s endpoints converge
within 1%.

Stage 3 adds a continuous representative-herd turnover boundary. Slaughter
HTO/OBT is removed from the animal once, becomes produced beef activity,
decays or remains in explicit product storage, and can be consumed only up to
the available product mass. The dose module uses actual consumed activity.
Mode `off`, zero turnover, product exhaustion, stopped production, product
closure, and combined animal/product closure are independently tested.

Stage 4 replaces the unsourced wet coefficient default with a named Japanet
literature-comparison parameter set while explicitly retaining the label
`LITERATURE_COMPARISON_NOT_UFOTRI`. Separate project low/central/high bounds
and a recomputable 4 x 3 \(a,b\) grid propagate wet uncertainty through
deposition, soil, plant, food, and dose outputs.

Stage 5 adds ten independent analytic benchmarks, five manual numeric anchors,
and two literature coefficient comparisons. All evidence is explicitly
classified; integration and regression runs are not labelled reference cases.

Stage 6 runs a mode-aware real full-dose LHS audit at n=64/128/256 with a
primary seed and three additional seeds. Quantiles converge at n=256 and the
dominant parameter is stable, while weak-parameter ranks remain explicitly
`LIMITED_WITH_EVIDENCE`.

Stage 7 adds explicit annual/perennial phenology modes, dormant pasture LAI,
multiple partial cuts, cross-year inventory retention, and a conservative
two-year pasture test.

Stage 8 freezes the three-box solver at
`PASS_EXPERIMENTAL_STANDALONE` and documents the interfaces required before any
future formal coupling claim.

Stage 10 adds a common whole-pathway activity protocol to every formal result
row and verifies all six end-to-end cases plus the two-year pasture case. The
expanded driver covers the 72 h dry counterexample, analytic dry/wet
competition, conservative beef, n=64/128/256 LHS, 600/300/120/60 s leaf
convergence, footprint scaling, zero source, closed internal transfers, stack
upper bounds, and combined activity residuals.
The exact Stage 10 command set passed: 158 tests, frozen V1 recomputation, V2
expanded recomputation, compileall over `src tests era5 scripts`, and
`git diff --check`. The known NumPy/NetCDF binary-compatibility warning remains
non-fatal.

The historical V2 status below records the pre-remediation implementation and
must not be interpreted as the current RC1 acceptance state.

Overall status: **FORMAL_MINIMAL_BASELINE_V1 complete**

This `complete` status is strictly bounded to: HTO-only; steady Gaussian
atmosphere; 5 cm single-layer surface soil; plant TFWT and simplified OBT;
soil/plant re-emission; 3600 s delayed atmospheric feedback; short ERA5 forcing;
recomputable acceptance; and surface-box closure rather than whole-domain
dynamic air conservation.

Wet scavenging is not implemented, and advanced REEM remains provisional. This
status does not mean complete UFOTRI, food chain, dose, HT chemistry, multi-layer
soil, whole-domain dynamic atmospheric conservation, or regulatory validation.

| Item | Status | Evidence / limitation |
|---|---|---|
| SURFACE_BOX_CLOSURE_STATUS | PASS | explicit soil + TFWT + OBT ledger; external inputs/outputs and internal transfers tested |
| ATMOSPHERIC_BUDGET_SEMANTICS_STATUS | DOCUMENTED_NOT_DYNAMIC_INVENTORY | steady Gaussian source/sink ledger; no air storage claim |
| RUNOFF_RAIN_HTO_BOUNDARY_STATUS | PASS | 0.6/5.4 Bq m-2 infiltration/runoff audit counterexample tested |
| CALM_WIND_STATUS | PASS | minimum-effective, skip, and error modes; substitution diagnostics |
| GAUSSIAN_DEPLETION_STATUS | PASS_DRY_PROJECT_SIMPLIFICATION | segment-exponential source depletion and monotonic/convergence tests |
| WET_SCAVENGING_STATUS | EXPLICITLY_NOT_IMPLEMENTED | interface disabled in formal baseline |
| FEEDBACK_DELAY_CONTRACT | FROZEN_3600S | 600/300 s tests preserve one-hour delay |
| ROOT_FRACTION_CONTRACT | FROZEN_SINGLE_LAYER_1_0 | single-layer closure, not manual multi-layer 20% |
| EQ40_SHADING_CONTRACT | FROZEN_RADIATION_TERM_ONLY | aerodynamic term unshaded; legacy mode optional |
| FEEDBACK_AREA_CONTRACT | PASS | rectangle is authoritative; inconsistent area rejected |
| REEMISSION_STATUS | BASIC_PASS_ADVANCED_PROVISIONAL | REEM/DIFF/ZT remains an engineering reconstruction |
| ACCEPTANCE_RECOMPUTE_STATUS | PASS | five cases recomputed in temporary output without overwriting saved artifacts |
| PROVENANCE_STATUS | PASS | HEAD/worktree, hashes, runtime, dependencies, modes, and timestamps recorded |
| TEST_STATUS | PASS | 61 passed; one known NetCDF binary-compatibility warning |
| TIMESTEP_STATUS | PASS | 600/300 s: soil 0.02360%, TFWT 0.13859%, OBT 0.12093%, integrated re-emission 0.04974% |

Next command:

```bash
.venv/bin/python scripts/verify_acceptance.py --recompute
```

## Historical environmental pathways V2 status

Development branch: `codex/ufotri-environmental-pathways-v2`

```text
V2_SCOPE_STATUS = FROZEN
MANUAL_EQUATION_INVENTORY_STATUS = COMPLETE_FOR_AVAILABLE_MANUAL
V2_IMPLEMENTATION_STAGE = STAGE_14_COMPLETE
WET_SCAVENGING_STATUS = PASS_PROJECT_PARAMETERIZATION
WET_DEPOSITION_LEDGER_STATUS = PASS
LEAF_AIR_EXCHANGE_STATUS = PASS_MANUAL_DERIVED_PROVISIONAL
BASIC_REEMISSION_STATUS = PASS
ADVANCED_REEMISSION_STATUS = PROVISIONAL_VALIDATED
CROP_PARAMETERIZATION_STATUS = PASS_PROJECT_EXTENSION
PHENOLOGY_STATUS = PASS
EDIBLE_PLANT_STATUS = PASS_PROJECT_EXTENSION
PLANT_INTERNAL_MASS_BALANCE_STATUS = PASS
FOOD_CHAIN_STATUS = PASS_MINIMAL_PATHWAYS
ECOLOGICAL_BOX_CLOSURE_STATUS = PASS
DOSE_MODULE_STATUS = PASS_RESEARCH_SCREENING
PATHWAY_DECOMPOSITION_STATUS = PASS
SINGLE_LAYER_STATUS = PASS_UNCHANGED
THREE_BOX_SOIL_STATUS = PASS_EXPERIMENTAL_STANDALONE
UNCERTAINTY_STATUS = PASS_REPRODUCIBLE
SENSITIVITY_STATUS = PASS
HISTORICAL_BENCHMARK_STATUS = PASS_AVAILABLE_REFERENCE_CASES
PHYSICAL_INVARIANTS_STATUS = PASS
V2_END_TO_END_CASES_STATUS = PASS
V2_ACCEPTANCE_RECOMPUTE_STATUS = PASS
V2_AUDIT_STATUS = ACCEPT_WITH_REMAINING_LIMITATIONS
HISTORICAL_V2_COMPLETE_RECOMMENDATION = FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE
V2_TEST_STATUS = PASS_95
V2_COMPILE_STATUS = PASS
V2_DIFF_CHECK_STATUS = PASS
```

The frozen scope, manual inventory, code mapping, architecture, assumptions,
and validation strategy are in `docs/v2/`. Stage 1 adds three wet-scavenging
modes, competing dry/wet source depletion, and a conservative surface
wet-deposition footprint ledger. The default remains `off`, preserving V1.
The power-law values are explicitly provisional. Stage 2 adds a single signed,
conservative leaf-air exchange using aerodynamic, boundary, and LAI/VPD/day-
night canopy resistance. Its default remains `off` for V1. Planned later
functions are not represented as V1 functionality.

Stage 3 centralizes Eq. (44) calibration at the manual's 20% reference
condition and verifies 10% h-1 radiative plus 1% h-1 diffusive initial rates,
day/night logic, ABFLR, HTO-only C2=1, and ZT decay. Missing manual calibration
detail prevents promotion beyond `PROVISIONAL_VALIDATED`.

Stage 4 adds YAML parameter sets for grass, leafy and root vegetables, cereal,
pasture, and a generic crop. Constant, piecewise-stage, smooth-seasonal, and
external LAI modes share one LAI value across Eq. (40) shading, transpiration,
and leaf exchange. Outside the configured season LAI and associated exchange
are zero. Crop values are `PROJECT_EXTENSION`, not site-specific claims.

Perennial pasture now uses an explicit dormant-season mode rather than the
legacy start-equals-harvest special case. It retains a configurable non-zero
dormant LAI, supports multiple partial cuts, preserves remaining inventories
across year boundaries, and records edible-harvest and removed whole-plant
activity as separate boundaries. A formal two-year case passes six unique cut
events, second-year regrowth, non-negativity, and closure checks.

Stage 5 adds distinct vegetative/whole-plant source pools and edible TFWT/OBT
inventories, internal allocation, growth dilution, decay, harvest, crop reset,
and explicit water/fresh/dry concentration conversions. Harvested HTO and OBT
are cumulative boundary outputs; internal allocation closes at machine
precision.

Stage 6 adds explicit leafy, root, grain, and pasture food concentrations plus
a configurable minimal cow body-water/body-OBT model with feed, drinking water,
formation/turnover, milk, excretion, beef, and slaughter boundaries. Feed
activity is removed from the edible pasture inventory and enters the animal
inventory once; the combined ecological residual is tested.

Stage 7 adds adult, child, and infant HTO/OBT public dose calculations with
separate inhalation, skin, water, plant, milk, and meat diagnostics. Dose
coefficients, habits, source, and version are configuration data. Results are
cumulative by time at the configured spatial receptor and remain explicitly
research-screening outputs.

Stage 8 adds a tested conservative three-box soil API with layer water,
advective HTO, optional diffusion, layer roots, surface-only evaporation, and
deep leakage. It is explicitly experimental and standalone; selecting it in
the formal short-case coupler returns a clear error rather than silently using
the single-layer implementation. RC1 does not promote it; the deferred coupling
interfaces and required calibration/convergence evidence are recorded in
`docs/v2/multibox_integration_roadmap.md`.

Stage 9 adds mode-aware Monte Carlo and Latin Hypercube sampling, median,
5/95-percentile, mean and standard deviation summaries, parameter-output
Spearman correlations, one-at-a-time finite-difference sensitivities, and
normalized pathway contributions. Disabled parameters are recorded as
`inactive_by_mode` instead of zero sensitivity. The real full-dose audit runs
LHS n=64/128/256 with a primary seed and three additional seeds, establishes
n=256 as the formal minimum, and records stable quantiles plus
`LIMITED_WITH_EVIDENCE` for the weak-parameter rank ordering. Parameter
distributions are centralized in YAML as project-level uncertainty assumptions.

Stage 10 provides a recomputable benchmark suite with ten independent analytic
checks, five UFOTRI-manual numeric anchors, two literature coefficient
comparisons, and the original fifteen executable scenarios/invariants. Evidence
is explicitly classified as `analytic_benchmark`, `manual_anchor`,
`literature_comparison`, `physical_invariant`, `integration_scenario`, or
`regression_case`; execution cases are not represented as numeric references.
The analytic set covers exponential wet removal, competing dry/wet allocation,
leaf equilibrium, re-emission, animal production, dose arithmetic, and food
mass/water conversion.

Stage 11 provides five named end-to-end configurations, pathway figures,
results, hashes, runtime provenance, and LHS/OAT artifacts. All were recomputed
in a temporary directory. The 72 h weather record transparently combines the
available 48 h ERA5 input with a 24 h deterministic extension; this limitation
is recorded in every relevant provenance file.

Stage 12 provides one recomputable V2 acceptance command covering frozen V1
regression, wet/leaf/food/dose pathways, fixed-seed LHS, the full categorized
benchmark suite, all end-to-end configurations, required figures, and
provenance hashes.

The historical Stage 13 assessment below is superseded for current-branch
status by the independent audit and this RC1 remediation record. Stage 13
records the earlier formal assessment in
`docs/v2/formal_ufotri_environmental_pathways_v2_assessment.md`. Its verdict is
`ACCEPT_WITH_REMAINING_LIMITATIONS`, and its recommendation is limited to
`FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE`.

Stage 14 passed 95 tests, frozen V1 recomputation, complete V2 recomputation,
Python byte-compilation, and the Git whitespace-error check. One known
NumPy/NetCDF binary-compatibility runtime warning remains in the ERA5 reader
test.

Final V2 acceptance command:

```bash
.venv/bin/python scripts/verify_v2_acceptance.py --recompute
```

## RC2 directed physics remediation

RC2 removes the unequal dry/wet footprint accounting assumption. Dry and wet
local fluxes retain independent `area_m2` values; their authoritative
activities are combined explicitly only after \(M_d=F_dA_d\) and
\(M_w=F_wA_w\) are recorded. The ecological box uses a separate configured
reference area. Combined cases with \(A_w/A_d=0.1,1,10\) close the global Bq
inventory/boundary/decay ledger below \(10^{-12}\), while local flux retains
inverse-area scaling.

UFOTRI Eq. (27) now uses saturated water-vapour density
`rho_v_sat`. Relative humidity remains in VPD-dependent canopy resistance but
does not scale the equilibrium air concentration. Direct tests at 293.15 K and
RH 30/60/90% give the same equilibrium value, and the formal leaf path reaches
HTO flux, TFWT, OBT, food, and dose with surface closure below \(10^{-12}\).

The leaf fixed-meteorology benchmark now obtains its expected conductance,
Eq. (27) factor, and first-order solution from handwritten equations without
using the exchange module. The suite requires at least ten analytic records
and `independent=true` for every analytic benchmark.

Perennial plant output now exposes root/shoot TFWT and OBT inventories. The
provisional root activity fraction is configuration data; partial cuts remove
shoot activity only. Wrap-around phenology uses the actual 365- or 366-day
calendar. Root retention, year crossing, leap/non-leap progression, six
two-year cuts, regrowth LAI, and conservation are tested.

## V2 external validation phase 1 - complete forcing

The validation-readiness infrastructure was fast-forwarded to `main` at
`f0cad0ab4e76e83c7e830f82bbe9329828c521f9` and pushed to `origin/main`.
The V2 candidate and V1 tags remain at
`f097115cbfc052baa18f1e49a1207fa6b3523cff` and
`6918440faa3455b848f43589784672f3bfabfe3d`, respectively.

The formerly missing 24 ERA5 hours were retrieved from the same CDS time-series
product and point. A read-only preparation workflow now yields 72 consecutive
external reanalysis rows with zero interpolated, repeated, extended, or missing
hours. The forcing comparison ran successfully. Wet and dry deposition were
unchanged because the one-hour release is within the shared first 48 h; final
soil HTO changed by -5.668%, TFWT by +0.105%, and OBT by +3.198%. This is a
forcing sensitivity result, not site validation.

```text
VALIDATION_INFRASTRUCTURE_MERGED = PASS
FORCING_72H_STATUS = PASS_72_OF_72_OBSERVED
FORCING_EXTENSION_BIAS_STATUS = PASS_COMPARISON_EXECUTED_NOT_SITE_VALIDATION
```

## V2 external validation phase 1 - independent reference

Independent reference case 001 parses the same frozen case manifest without
importing formal model functions. It covers Gaussian concentration, competing
dry/wet depletion, surface allocation, one-box soil, fixed-conductance TFWT,
first-order OBT, and simple dose. All eight declared comparisons pass their
preregistered thresholds; normalized errors are between `1.37e-15` and
`2.49e-13`, and the independent activity residual is below `5.83e-10 Bq m-2`.
The case is intentionally bounded and is not experimental or field evidence.

```text
REFERENCE_MODEL_STATUS = PASS_INDEPENDENT_REFERENCE_CASE_001
```

## V2 external validation phase 1 - experiment and field search

The controlled-experiment and matched-field search is recorded in a
machine-readable inventory, a licence review, and two blocked requirement
manifests. The IAEA EMRAS soybean scenario is the closest leaf candidate, but
the retrieved public material does not include the organizer meteorology and
air workbooks, a chamber-mixing boundary condition, or a detection limit. No
complete co-located air-meteorology-soil-plant field package was obtained.

No publication table was repackaged, no different sites were spliced, and no
external case, calibration, or holdout validation was run. The registry records
the complete ERA5 reanalysis forcing and independent reference as `PASS`, while
the experiment and field cases remain explicitly blocked.

```text
EXPERIMENTAL_DATA_STATUS = BLOCKED_EXTERNAL_DATA
FIELD_DATA_STATUS = BLOCKED_EXTERNAL_DATA
EXTERNAL_CASES_EXECUTED_COUNT = 0
CALIBRATION_STATUS = NOT_RUN_BLOCKED_EXTERNAL_DATA
PARAMETER_IDENTIFIABILITY_STATUS = NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE
```

## V2 external evidence phase 1 - gate assessment

All 185 collected tests, the five frozen V1 cases, the six V2 end-to-end cases,
validation readiness, byte-compilation, and the Git whitespace check pass. The
candidate and V1 tags remain unchanged. The only runtime warning is the known
NumPy/NetCDF binary-compatibility warning in the ERA5 reader test.

Because no true external experiment or field case was executable, Phase 1 is
infrastructure-complete but externally blocked. V3 may proceed only to
architecture, interfaces, migration planning, and data models; no V3 model
code or formal physics was implemented.

```text
EXTERNAL_VALIDATION_PHASE1_STATUS = INFRASTRUCTURE_COMPLETE_EXTERNAL_EVIDENCE_BLOCKED
V3_GATE_VERDICT = READY_FOR_V3_ARCHITECTURE_ONLY_EXTERNAL_VALIDATION_CONTINUES
MERGE_EXTERNAL_VALIDATION_BRANCH_RECOMMENDATION = READY_FOR_MAINTAINER_REVIEW
```

## V3 H2/H3 slow-mechanism discriminability design

The independently reviewed SB4 benchmark was fast-forwarded to `main` at
`e10c0be1d1fac51eb99643ceac71708426c30dd3`. From that baseline, the
validation-only branch
`codex/v3-slow-mechanism-discriminability-design` froze its protocol before
synthetic execution. H2 and H3 retain the SB1 parameters from
`4b79f62741db4d4b51f4d608df33d2e13c499636`; the parameter-refit count is
zero.

Existing SB1 and SB4 output distances remain insufficient to select H2 or H3.
Six controlled exposure designs were screened with both models as Monte Carlo
truth, 1,000 replicates per design/truth/noise cell, and CV 10/20/30%.
D3, a 24 h low-concentration step followed by samples at 0.2, 48, and 120 h,
is the only screened design that passes every preregistered concentration, RH,
wind, stomatal-resistance, bidirectional classification, strong-separation,
finite/nonnegative, and conservation check. This is an experiment-design
result only, not empirical validation or model selection.

```text
SB1_EXISTING_DATA_DISCRIMINABILITY = INSUFFICIENT_TO_SELECT_H2_OR_H3
SB4_EXISTING_DATA_DISCRIMINABILITY = INSUFFICIENT_TO_SELECT_H2_OR_H3
BEST_DISCRIMINATING_DESIGN = D3_SHORT_STEP_24H
PARAMETER_REFIT_COUNT = 0
SYNTHETIC_DESIGN_STATUS = DESIGN_ONLY
EXPERIMENT_SPECIFICATION = READY_FOR_EXTERNAL_DATA_SEARCH_OR_NEW_EXPERIMENT
FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```
