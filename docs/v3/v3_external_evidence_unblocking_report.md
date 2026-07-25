# V3 external-evidence unblocking handoff

Assessment date: 2026-07-25

## Publication status

```text
V3_ARCHITECTURE_MERGE_STATUS =
V3_ARCHITECTURE_ONLY_MERGED_AND_PUBLISHED

ARCHITECTURE_BASELINE_HEAD =
e22aa5e718404a6ba8ba31b61cb50aba53eb86b8

ARCHITECTURE_FINALIZATION_HEAD =
f618515caef22a19867d75d59b1d4c78f1cb212f

MAIN_HEAD =
f618515caef22a19867d75d59b1d4c78f1cb212f

REMOTE_MAIN_HEAD =
f618515caef22a19867d75d59b1d4c78f1cb212f

V1_TAG_STATUS =
UNCHANGED_6918440faa3455b848f43589784672f3bfabfe3d

V2_CANDIDATE_TAG_STATUS =
UNCHANGED_f097115cbfc052baa18f1e49a1207fa6b3523cff
```

The architecture branch was fast-forwarded to `main`, verified after merge,
and pushed. No V3 tag was created.

## Unblocking work package

```text
EXTERNAL_EVIDENCE_BRANCH =
codex/v3-external-evidence-unblocking

EXTERNAL_EVIDENCE_IMPLEMENTATION_HEAD =
184351908ebd32ca00f713d6284b61cb958c9418

EXTERNAL_EVIDENCE_HEAD =
RECORDED_IN_FINAL_HANDOFF

SOYBEAN_UNBLOCKING_MANIFEST_STATUS =
COMPLETE

DATA_REQUEST_PACKAGE_STATUS =
COMPLETE_NOT_SENT

LOCAL_INTAKE_STATUS =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA

DATA_FREEZE_PROTOCOL_STATUS =
COMPLETE_NOT_EXECUTED

PREREGISTRATION_TEMPLATE_STATUS =
DRAFT_NOT_PREREGISTERED

CALIBRATION_CONTRACT_STATUS =
COMPLETE_NOT_EXECUTED

IDENTIFIABILITY_PROTOCOL_STATUS =
COMPLETE_NOT_EXECUTED

SYNTHETIC_CONTRACT_TEST_STATUS =
PASS_NOT_EMPIRICAL
```

The request package specifies desired files, fields, temporal resolution,
units, local-use/redistribution decision, checksum/provenance handling, and
contact placeholders. It was generated only as text and was not sent.

The adapter validates required file roles, fields, explicit units, continuous
meteorology/air HTO time series, exposure coverage, chamber volume and
mixing/ventilation boundary, detection limits, uncertainties, replicates,
checksums, and disjoint calibration/holdout identifiers. It produces only a
metadata manifest, field mapping, checksums, and report. It does not OCR
figures, digitize plots, splice experiments, or commit raw values.

## Actual evidence state

```text
SOYBEAN_DATA_STATUS =
BLOCKED_EXTERNAL_DATA

FIELD_DATA_STATUS =
BLOCKED_EXTERNAL_DATA

PREREGISTRATION_STATUS =
DRAFT_NOT_PREREGISTERED

CALIBRATION_STATUS =
NOT_RUN_BLOCKED_EXTERNAL_DATA

PARAMETER_IDENTIFIABILITY_STATUS =
NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE
```

Missing soybean inputs include the organizer meteorology workbook, complete air
HTO time series, exact exposure timing, chamber volume, ventilation/mixing
rate, replacement-air boundary, continuous temperature/RH, wind or chamber
mixing condition, complete plant-water HTO/optional OBT observations, sampling
and replicate identifiers, uncertainty, detection limit, explicit unit bases,
licence/local-use terms, and file checksums.

## Gates

```text
V3_ARCHITECTURE_STATUS =
READY_ARCHITECTURE_ONLY

V3_PHYSICS_IMPLEMENTATION_STATUS =
NOT_STARTED

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

The strengthened physics gate additionally requires recorded raw-data
checksums, a valid data schema, executed calibration, and an executed external
holdout. Internal reference and synthetic contract evidence are explicitly
ineligible for the complete-external-case and external-holdout prerequisites.

## Verification

```text
TEST_STATUS =
PASS_202_ONE_KNOWN_NUMPY_NETCDF_WARNING

V1_RECOMPUTE_STATUS =
PASS_5_FROZEN_CASES

V2_RECOMPUTE_STATUS =
PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE

VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY

V3_COMPATIBILITY_STATUS =
PASS_BITWISE_WHERE_DETERMINISTIC

V3_ARCHITECTURE_VERIFIER_STATUS =
READY_ARCHITECTURE_ONLY

V3_PHYSICS_GATE_STATUS =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

EXTERNAL_EVIDENCE_UNBLOCKING_VERIFIER_STATUS =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA

COMPILE_STATUS =
PASS

DIFF_CHECK_STATUS =
PASS
```

The 11 new checks cover missing meteorology, missing air HTO, missing mixing
boundary, invalid units, discontinuous time series, missing detection limits,
metadata-only manifest/report generation, synthetic evidence exclusion,
internal-reference exclusion, preregistration enforcement, and prohibition of
premature holdout inspection. The one warning is the pre-existing
NumPy/NetCDF binary-size warning.

## Commits before final report

```text
ae686b3 Add soybean external evidence acquisition manifest
07414d7 Define external data freeze and preregistration protocol
0c6c4a7 Add calibration and identifiability contracts
1843519 Harden V3 empirical physics start gate
```

The report and implementation-status update are delivered in the final
unblocking handoff commit.

## Key executed commands

```bash
git fetch --all --prune
git diff main...codex/v3-architecture-only --stat
git diff main...codex/v3-architecture-only --name-status
git diff main...codex/v3-architecture-only -- src configs
git push origin codex/v3-architecture-only
git switch main
git pull --ff-only
git merge --ff-only codex/v3-architecture-only
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_validation_readiness.py
.venv/bin/python scripts/verify_v3_compatibility.py
.venv/bin/python scripts/verify_v3_architecture_readiness.py
.venv/bin/python scripts/verify_v3_physics_start_gate.py
.venv/bin/python scripts/verify_v3_external_evidence_unblocking.py
.venv/bin/python -m compileall -q src tests era5 scripts validation
git diff --check
git push origin main
git switch -c codex/v3-external-evidence-unblocking
git rev-parse formal-minimal-baseline-v1^{}
git rev-parse ufotri-environmental-pathways-v2-candidate^{}
```

## Merge recommendation

```text
MERGE_EXTERNAL_EVIDENCE_BRANCH_RECOMMENDATION =
READY_FOR_MAINTAINER_REVIEW
```

The recommendation is limited to non-invasive data-intake, preregistration,
identifiability, and gate tooling. This branch must not be interpreted as
empirical validation, V3 physics acceptance, or authorization to calibrate
without a complete frozen external package.
