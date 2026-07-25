# V2 external evidence phase 1 report

## Outcome

The validation-readiness infrastructure is merged and pushed on `main`.
Complete 72-hour ERA5 reanalysis forcing and one bounded independent reference
model were executed successfully. A documented experiment/field search did not
produce a complete legally usable package, so no true external experiment or
field case, calibration, or holdout validation was executed.

The correct Phase 1 status is therefore:

```text
EXTERNAL_VALIDATION_PHASE1_STATUS =
INFRASTRUCTURE_COMPLETE_EXTERNAL_EVIDENCE_BLOCKED
```

This is not `V2_EXTERNAL_EVIDENCE_PHASE1_COMPLETE` and does not change the
candidate's research-only, not-site-calibrated boundary.

## Required status fields

```text
VALIDATION_INFRASTRUCTURE_MERGE_STATUS = PASS_FAST_FORWARD_MERGED_AND_PUSHED
MAIN_HEAD = f0cad0ab4e76e83c7e830f82bbe9329828c521f9
REMOTE_MAIN_HEAD = f0cad0ab4e76e83c7e830f82bbe9329828c521f9
CANDIDATE_TAG_INTEGRITY_STATUS = PASS_f097115cbfc052baa18f1e49a1207fa6b3523cff
V1_TAG_INTEGRITY_STATUS = PASS_6918440faa3455b848f43589784672f3bfabfe3d

FORCING_72H_STATUS = PASS_72_OF_72_ERA5_REANALYSIS_HOURS
FORCING_EXTENSION_BIAS_STATUS = PASS_COMPARISON_EXECUTED_NOT_SITE_VALIDATION

REFERENCE_MODEL_STATUS = PASS_INDEPENDENT_REFERENCE_CASE_001
REFERENCE_MODEL_PRIMARY_METRICS = EIGHT_OF_EIGHT_PASS_NRMSE_1.37e-15_TO_2.49e-13_ACTIVITY_RESIDUAL_5.823e-10_Bq_m-2

EXPERIMENTAL_DATA_STATUS = BLOCKED_EXTERNAL_DATA
FIELD_DATA_STATUS = BLOCKED_EXTERNAL_DATA
EXTERNAL_CASES_EXECUTED_COUNT = 0
EXTERNAL_CASES_PASS_COUNT = 0
EXTERNAL_CASES_FAIL_COUNT = 0
EXTERNAL_CASES_INCONCLUSIVE_COUNT = 0
EXTERNAL_CASES_BLOCKED_COUNT = 2

CALIBRATION_STATUS = NOT_RUN_BLOCKED_EXTERNAL_DATA
PARAMETER_IDENTIFIABILITY_STATUS = NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE

VALIDATION_REGISTRY_STATUS = UPDATED_AND_SYNCHRONIZED
V1_RECOMPUTE_STATUS = PASS_FIVE_CASES
V2_RECOMPUTE_STATUS = PASS_SIX_END_TO_END_CASES
TEST_STATUS = PASS_185_COLLECTED_AND_EXECUTED_ONE_KNOWN_NUMPY_NETCDF_WARNING

EXTERNAL_VALIDATION_PHASE1_STATUS = INFRASTRUCTURE_COMPLETE_EXTERNAL_EVIDENCE_BLOCKED
V3_GATE_VERDICT = READY_FOR_V3_ARCHITECTURE_ONLY_EXTERNAL_VALIDATION_CONTINUES
V3_SCOPE_CANDIDATE_STATUS = DOCUMENTED_ARCHITECTURE_ONLY_NO_V3_IMPLEMENTATION
MERGE_EXTERNAL_VALIDATION_BRANCH_RECOMMENDATION = READY_FOR_MAINTAINER_REVIEW
NEXT_STAGE_RECOMMENDATION = ACQUIRE_COMPLETE_LICENSED_EXPERIMENT_OR_FIELD_PACKAGE_AND_PREREGISTER_BEFORE_EXECUTION
```

The two blocked counts are the distinct experiment and field requirements.
The site-case registry placeholder refers to the same missing field package
and is not double-counted.

## Evidence summary

### Complete forcing

The same CDS ERA5 single-level time-series product and the same point were used
for all 72 hours. The derived ignored forcing has 72 consecutive hourly rows,
all marked `observed` by the local forcing contract, and zero interpolated,
repeated, extended, or missing rows. Here `observed` means externally retrieved
reanalysis rather than a station measurement.

Relative to the frozen 48-hour plus deterministic 24-hour extension, final wet
and dry deposition were unchanged because the release occurs in the shared
first hour. Final soil HTO changed by -5.668%, TFWT by +0.105%, and OBT by
+3.198%; TFWT peaked eight hours earlier. This is a forcing-substitution
sensitivity result, not site validation.

### Independent reference

The separately coded six-hour reference imports no formal model functions.
All eight preregistered air, depletion, soil, plant, and dose comparisons pass.
The case validates the declared simplified equations only; it does not cover
re-emission, root uptake, edible allocation, animal pathways, or the full
meteorology-responsive leaf resistance.

### Experiment and field evidence

The IAEA EMRAS soybean scenario is the closest controlled leaf candidate. The
public report contains observation tables and partial forcing, but refers to
supporting meteorology and air data in organizer Excel files that were not
obtained. It also lacks a sufficiently explicit chamber-mixing boundary and a
reported detection limit. No complete co-located air-meteorology-soil-plant
field package was located.

No tables were digitized into a runnable substitute, no sites were spliced,
and no data-dependent thresholds were selected. The detailed inventory,
licence decision, checksums, and unblocking requirements are under
`docs/v2/validation/evidence/`.

## Verification actually executed

```bash
.venv/bin/python scripts/run_v2_validation_case.py --case validation/cases/full_observed_72h.yaml --output validation/reports/full_observed_72h
.venv/bin/python scripts/run_v2_validation_case.py --case validation/cases/independent_reference_case_001.yaml --output validation/reports/independent_reference_case_001
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_validation_readiness.py
.venv/bin/python -m compileall -q src tests era5 scripts validation
git diff --check
git rev-parse ufotri-environmental-pathways-v2-candidate^{}
git rev-parse formal-minimal-baseline-v1^{}
```

All commands passed. Pytest executed 185 collected tests. The only warning was
the already known NumPy/NetCDF binary-compatibility runtime warning in the ERA5
reader test.

## Scope and remaining risk

Phase 1 changes validation cases, reference tooling, adapters, registries,
tests, and reports only. It does not modify `src/`, formal equations, or formal
configuration semantics. The strongest unresolved risk is empirical: the
candidate's full leaf, field transfer, re-emission, root/food/animal, and
site-parameter behavior still lacks an executed external experiment or field
case.
