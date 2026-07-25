# V2 validation-readiness assessment

Date: 2026-07-25
Branch: `codex/v2-validation-readiness`
Candidate basis:
`ufotri-environmental-pathways-v2-candidate`
(`f097115cbfc052baa18f1e49a1207fa6b3523cff`)

## Assessment

The candidate now has a reproducible validation intake and reporting
framework. The YAML/CSV registry has 42 unique entries and retains the
original evidence levels: 10 analytic benchmarks, 5 manual anchors, 2
literature numeric comparisons, 5 physical invariants, 9 internal integration
scenarios and 1 regression case. Internal integration/regression evidence is
not counted as external validation.

The executable zero-source case independently supplies its reference and
generates all required artifacts. Metrics cover scalar, time-series,
conservation, interval and detection-limit comparisons with explicit zero and
missing-value policies. All five candidate MEDIUM limitations map to named
registry closure entries.

The local weather evidence is not a complete 72 h observed record: the
available raw file has 48 consecutive observed hourly rows, so 24 hours remain
missing. The formal candidate's deterministic extension remains correctly
labelled and is not counted as observation.

No experiment, complete field dataset, independent reference-model output or
site case is bundled. Those entries remain `BLOCKED_EXTERNAL_DATA`; therefore
this assessment makes no empirical, site, regulatory, or complete-UFOTRI
validation claim.

## External data required next

1. A licensed time-resolved leaf or plant HTO uptake/depuration experiment.
2. A matched air-soil-plant field observation case with uncertainty and
   detection limits.
3. Independent reference-model outputs for a fully specified source and
   forcing case.
4. Complete observed 72 h forcing, followed by 14 d, 30 d and seasonal inputs.
5. Site source terms, geometry, land/soil/crop parameters and receptor habits.

## Final status fields

```text
VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY

ANALYTIC_VALIDATION_STATUS =
READY_10_INDEPENDENT_BENCHMARKS_5_PHYSICAL_INVARIANTS

MANUAL_MAPPING_STATUS =
READY_5_ANCHORS_REEM_ADVANCED_MAPPING_PARTIAL

LITERATURE_COMPARISON_STATUS =
READY_2_NUMERIC_SCALE_COMPARISONS_NOT_CALIBRATION

EXPERIMENTAL_DATA_STATUS =
BLOCKED_EXTERNAL_DATA

FIELD_DATA_STATUS =
BLOCKED_EXTERNAL_DATA

REFERENCE_MODEL_STATUS =
BLOCKED_EXTERNAL_DATA

SITE_CASE_STATUS =
BLOCKED_EXTERNAL_DATA

FORCING_COMPLETENESS_STATUS =
BLOCKED_EXTERNAL_DATA_48_OF_72_OBSERVED_24_MISSING

PARAMETER_VALIDATION_STATUS =
READY_PRIORITIZED_NOT_SITE_CALIBRATED

REEM_VALIDATION_STATUS =
PARTIAL_RAIN_START_AND_CONCENTRATION_DIFF_MAPPING_PENDING

MULTIBOX_VALIDATION_STATUS =
PARTIAL_STANDALONE_READY_FORMAL_COUPLING_PENDING

VALIDATION_RUNNER_STATUS =
PASS_DRY_RUN_AND_COMPLETE_EXAMPLE_ARTIFACTS

VALIDATION_REGISTRY_STATUS =
PASS_42_UNIQUE_YAML_CSV_SYNCHRONIZED

CANDIDATE_TAG_INTEGRITY_STATUS =
PASS_F097115CBFC052BAA18F1E49A1207FA6B3523CFF

V1_TAG_INTEGRITY_STATUS =
PASS_6918440FAA3455B848F43589784672F3BFABFE3D

TEST_STATUS =
PASS_176_ONE_KNOWN_NUMPY_NETCDF_WARNING

NEXT_EXTERNAL_DATA_REQUIREMENTS =
EXPERIMENT_FIELD_REFERENCE_MODEL_FULL_OBSERVED_FORCING_AND_SITE_CASE
```
