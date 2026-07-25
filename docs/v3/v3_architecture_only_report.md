# V3 architecture-only handoff report

Assessment date: 2026-07-25

Branch: `codex/v3-architecture-only`

## Repository state

```text
PHASE1_MERGE_STATUS =
V2_EXTERNAL_VALIDATION_PHASE1_MERGED_AND_PUSHED

MAIN_HEAD =
f02636f10e900174226edc2659f20a2fdb15d3ce

REMOTE_MAIN_HEAD =
f02636f10e900174226edc2659f20a2fdb15d3ce

V1_TAG_STATUS =
UNCHANGED_6918440faa3455b848f43589784672f3bfabfe3d

V2_CANDIDATE_TAG_STATUS =
UNCHANGED_f097115cbfc052baa18f1e49a1207fa6b3523cff
```

Phase 1 was reviewed before merge. `src/`, `configs/`, and reviewed equation
contracts had zero diff; no raw ERA5, restricted IAEA table, credential, or
large generated output entered Git. The reference implementation imports no
formal model module and is labelled numerical reference rather than experiment
or field validation.

## Architecture state

```text
V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_BRANCH = codex/v3-architecture-only
ARCHITECTURE_BASELINE_HEAD =
e22aa5e718404a6ba8ba31b61cb50aba53eb86b8
CURRENT_V3_BRANCH_HEAD =
RECORDED_IN_FINAL_PUBLICATION_HANDOFF
V2_COMPATIBILITY_CONTRACT_STATUS = PASS
STATE_CONTRACT_STATUS = PASS
FLUX_CONTRACT_STATUS = PASS
LEDGER_CONTRACT_STATUS = PASS
CONFIG_SCHEMA_STATUS = PASS_FAIL_CLOSED
RESULT_SCHEMA_STATUS = PASS_FAIL_CLOSED
PROVENANCE_SCHEMA_STATUS = PASS_FAIL_CLOSED
MODULE_REGISTRY_STATUS = PASS_8_UNIQUE
MIGRATION_TOOL_STATUS = PASS_READ_ONLY_V2_FROZEN
GOLDEN_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
ADR_STATUS = PASS_8_COMPLETE
```

The configuration envelope retains the complete parsed V2 mapping, exact input
SHA-256, canonical resolved SHA-256, immutable candidate anchor, empty V3
feature set, and `compatibility_mode: v2_frozen`. It does not guess parameter,
forcing, source, validation, or physical modes.

Golden results:

- V1 frozen paths: `PASS_5_OF_5`;
- V2 end-to-end paths: `PASS_6_OF_6`;
- complete 72 h ERA5 reanalysis path: `PASS_BITWISE`;
- independent reference case: `PASS_BITWISE`;
- V2 output field mapping: identity.

## Candidate modules

```text
LONG_FORCING_ARCHITECTURE_STATUS = ARCHITECTURE_ONLY
CALIBRATION_DATA_MODEL_STATUS = ARCHITECTURE_ONLY
ADVANCED_REEMISSION_ARCHITECTURE_STATUS = ARCHITECTURE_ONLY
THREE_BOX_SOIL_ARCHITECTURE_STATUS = ARCHITECTURE_ONLY
DYNAMIC_AIR_ARCHITECTURE_STATUS =
DEFERRED_PENDING_EMPIRICAL_AND_REFERENCE_EVIDENCE
HT_CHEMISTRY_STATUS = REJECTED_OUT_OF_SCOPE
```

All candidate modules are default-off. No advanced re-emission formula,
three-box coupling, dynamic-air solver, HT chain, new food/animal path, or
additional dose physics was implemented. Formal V2 physics and configuration
semantics are unchanged.

## External evidence

```text
SOYBEAN_DATA_STATUS = BLOCKED_EXTERNAL_DATA
FIELD_DATA_STATUS = BLOCKED_EXTERNAL_DATA
PREREGISTRATION_STATUS = DRAFT_NOT_PREREGISTERED
CALIBRATION_STATUS = NOT_RUN_BLOCKED_EXTERNAL_DATA
PARAMETER_IDENTIFIABILITY_STATUS =
NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE
```

The soybean manifest still lacks organizer meteorology, complete air HTO,
mixing/ventilation boundaries, detection limits, complete uncertainty/timing,
and a clear local-use/redistribution decision. The local adapter and directory
are ready but fail closed. No publication plot or incomplete table was
converted into runnable evidence.

## Gates

```text
V3_GATE_PREVIOUS =
READY_FOR_V3_ARCHITECTURE_ONLY_EXTERNAL_VALIDATION_CONTINUES

V3_ARCHITECTURE_GATE =
READY_ARCHITECTURE_ONLY

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

V3_PHYSICS_IMPLEMENTATION_STATUS =
NOT_STARTED
```

Unmet prerequisites are a complete licensed external case, a committed
preregistration before holdout inspection, calibration/holdout separation,
parameter-identifiability assessment, and an executed external holdout. The
internal reference case cannot satisfy the empirical gate.

## Verification

```text
TEST_STATUS = PASS_191_ONE_KNOWN_NUMPY_NETCDF_WARNING
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY
ARCHITECTURE_VERIFIER_STATUS = READY_ARCHITECTURE_ONLY
COMPILE_STATUS = PASS
DIFF_CHECK_STATUS = PASS
```

The single warning is the pre-existing NumPy/NetCDF binary-size warning in
`tests/unit/test_era5_reader.py::test_netcdf_mapping`; it is non-fatal.

## Commits before final handoff report

```text
c22f35b Define V3 architecture principles and compatibility boundary
83bc883 Add V3 state flux ledger and schema contracts
f2cc41e Add V2 to V3 migration and compatibility harness
7b562b5 Define evidence-gated V3 candidate module architectures
d174bc1 Add V3 architecture and physics start gate verification
```

The architecture implementation baseline above includes this report and the
initial implementation-status update. Any metadata-only finalization commit is
recorded separately in the publication handoff so this file does not make an
impossible self-referential HEAD claim.

## Key executed commands

```bash
git fetch --all --prune
git diff f0cad0ab...f02636f --stat
git diff f0cad0ab...f02636f --name-status
git switch main
git pull --ff-only
git merge --ff-only codex/v2-external-validation-phase1
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_validation_readiness.py
.venv/bin/python -m compileall -q src tests era5 scripts validation
git diff --check
git push origin main
git fetch origin
git switch -c codex/v3-architecture-only
.venv/bin/python scripts/migrate_v2_config_to_v3.py --input <v2.yaml> --output <v3.yaml> --report <report.md>
.venv/bin/python scripts/verify_v3_compatibility.py
.venv/bin/python scripts/verify_v3_architecture_readiness.py
.venv/bin/python scripts/verify_v3_physics_start_gate.py
git rev-parse formal-minimal-baseline-v1^{}
git rev-parse ufotri-environmental-pathways-v2-candidate^{}
git diff --stat main...HEAD
git diff --name-status main...HEAD
```

## Merge recommendation

```text
MERGE_V3_ARCHITECTURE_BRANCH_RECOMMENDATION =
READY_FOR_MAINTAINER_REVIEW
```

This recommendation is limited to architecture and non-invasive tooling.
The V3 branch must not be merged automatically, tagged as a V3 physics release,
or used to remove the external-evidence blocker.
