# V2 candidate release and validation-readiness report

Date: 2026-07-25

## Candidate release result

The RC2 candidate was finalized without changing the accepted model outputs.
`main` was fast-forwarded and pushed, and the annotated candidate tag was
created and pushed. The V1 baseline tag remains unchanged.

```text
CANDIDATE_RELEASE_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE_RELEASED

CANDIDATE_FINALIZATION_COMMIT =
f097115cbfc052baa18f1e49a1207fa6b3523cff

MAIN_HEAD =
f097115cbfc052baa18f1e49a1207fa6b3523cff

REMOTE_MAIN_HEAD =
f097115cbfc052baa18f1e49a1207fa6b3523cff

V2_CANDIDATE_TAG =
ufotri-environmental-pathways-v2-candidate

V2_CANDIDATE_TAG_COMMIT =
f097115cbfc052baa18f1e49a1207fa6b3523cff

V1_TAG_STATUS =
PASS_UNCHANGED_6918440FAA3455B848F43589784672F3BFABFE3D

AUDIT_REPORTS_TRACKED_STATUS =
PASS_RC1_AND_RC2_INDEPENDENT_REPORTS

PROVENANCE_STATUS =
PASS_12_NAMED_FIELDS_CONFIG_HASH_AND_FAIL_CLOSED_CHECKS

TEST_STATUS_AT_RELEASE =
PASS_167_ONE_KNOWN_NUMPY_NETCDF_WARNING

V1_RECOMPUTE_STATUS_AT_RELEASE =
PASS_5_FROZEN_CASES

V2_RECOMPUTE_STATUS_AT_RELEASE =
PASS_6_END_TO_END
```

## Validation-ready result

The post-tag branch adds only documentation, validation data contracts,
adapters, metrics, tests and non-invasive tools. It does not change formal
model physics or configuration semantics and does not modify the candidate
tag.

```text
VALIDATION_BRANCH =
codex/v2-validation-readiness

VALIDATION_HEAD =
RECORDED_BY_GIT_BRANCH_TIP_AND_FINAL_HANDOFF

VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY

VALIDATION_REGISTRY_STATUS =
PASS_42_UNIQUE_ENTRIES_YAML_CSV_SYNCHRONIZED

VALIDATION_RUNNER_STATUS =
PASS_DRY_RUN_AND_COMPLETE_ZERO_SOURCE_CASE

VALIDATION_METRICS_STATUS =
PASS_13_METRICS_WITH_ZERO_MISSING_AND_DETECTION_LIMIT_POLICIES

PARAMETER_PRIORITY_STATUS =
PASS_27_PRIORITIZED_PARAMETERS

EXTERNAL_DATA_STATUS =
BLOCKED_EXPERIMENT_FIELD_REFERENCE_MODEL_AND_SITE_CASE

REEM_CLOSURE_PATH_STATUS =
PARTIAL_TWO_NAMED_MANUAL_MAPPING_PATHS

MULTIBOX_CLOSURE_PATH_STATUS =
PARTIAL_STANDALONE_EVIDENCE_FORMAL_COUPLING_PENDING

FORCING_COMPLETENESS_STATUS =
BLOCKED_EXTERNAL_DATA_48_OF_72_OBSERVED_24_MISSING

SCENARIO_TAXONOMY_STATUS =
READY_5_EXPLICIT_SCENARIO_TYPES_AND_REQUIRED_FIELDS

TEST_STATUS_AT_VALIDATION_HEAD =
PASS_178_ONE_KNOWN_NUMPY_NETCDF_WARNING

MERGE_VALIDATION_BRANCH_RECOMMENDATION =
READY_FOR_MAINTAINER_REVIEW

NEXT_STAGE_RECOMMENDATION =
INGEST_PREREGISTERED_EXTERNAL_EVIDENCE_STOP_BEFORE_V3
```

## Remaining limitations

```text
HTO_ONLY
STEADY_GAUSSIAN_NO_DYNAMIC_AIR_INVENTORY
NOT_SITE_CALIBRATED
NOT_REGULATORY_VALIDATED
WET_PARAMETERS_NOT_SITE_CALIBRATED
WEAK_LHS_RANKS_LIMITED
ADVANCED_REEMISSION_PARTIAL
MULTIBOX_NOT_FORMALLY_COUPLED
FULL_OBSERVED_LONG_FORCING_PENDING
```

The original five MEDIUM limitations remain open as research limitations.
Validation readiness supplies traceable closure paths; it does not claim that
the missing evidence has been obtained.

## Validation branch commits

```text
9dc08fa Add V2 validation registry and evidence taxonomy
0d1adfd Add external validation schemas runners and metrics
0a1493e Define V2 validation closure paths and parameter priorities
01ed8c6 Finalize V2 validation-readiness assessment
12e44ae Harden validation result and reemission evidence handling
<branch tip containing this handoff update> Record final validation handoff
```

The exact branch-tip SHA is intentionally obtained with `git rev-parse HEAD`
after the final commit; a commit cannot embed its own SHA without changing that
SHA. The final handoff records the resolved value.
