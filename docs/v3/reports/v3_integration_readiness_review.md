# V3 Integration Readiness Review

Date: 2026-08-24

Branch: `codex/v3-integration-review`

Base: `origin/main` at `6671f5793d04842bf2ceae4904f3c0cf30a0d7e0`

## Decision

The sequential integration review passes. The review branch is a frozen
software baseline for the next parameter-validation preparation stage. It does
not promote V3 to physics readiness and does not make a validated parameter
available to a production solver.

```ini
V3_INTEGRATION_REVIEW = PASS
CODE_CONFLICTS = 0
NEW_TEST_FAILURES = 0
PHYSICS_MODULE_CHANGES = 0
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
CALIBRATION = NOT_STARTED
REAL_ATMOS_INPUT = FALSE
V3_PHYSICS_READY = FALSE
```

`VALIDATED_PARAMETERS = 1` is limited to the universal H-3 radioactive
half-life in the P7.6C-1 control-plane record. It does not validate soil
transport, plant transfer, exposure, dose, or the full V3 physics chain.

## Sequential integration

Each stage was integrated from the adjacent remote branch. The resulting
commits are new integration commits; source branch history was not rewritten,
and no `origin/main` merge was performed.

| Stage | Source branch | Integration commit |
| --- | --- | --- |
| P7.5 | `codex/v3-p7-5-pipeline-integration` | `5477cec` |
| P7.5B | `codex/v3-p7-5b-numerical-coupling-freeze` | `1e1d69c` |
| P7.6A | `codex/v3-p7-6a-parameter-evidence-freeze` | `44b3c92` |
| P7.6B-1 | `codex/v3-p7-6b1-applicability-review` | `85f1d41` |
| P7.6B-2A | `codex/v3-p7-6b2a-parameter-candidates` | `53eb9fa` |
| P7.6B-2B | `codex/v3-p7-6b2b-evidence-recovery` | `74ca600` |
| P7.6C-1 | `codex/v3-p7-6c1-physical-constant-validation` | `7a5d607` |
| P7.6C-2 | `codex/v3-p7-6c2-ufotri-semantic-mapping` | `60e2557` |

The P7.5B squash attempt exposed tree-overlap pseudo-conflicts caused by the
previous P7.5 squash commit not being present in Git's merge-base history. No
merge commit or conflict resolution was committed. The staged state was
restored and the exact adjacent branch diff was applied and reviewed instead.
There are no unresolved or committed code conflicts in the final branch.

## Protected-path and content audit

The complete review delta contains 180 paths relative to `origin/main`. The
protected-path scan returned no matches for:

```text
configs/
parameters/
docs/v1/
docs/v2/
src/**/v1/
src/**/v2/
validation/**/trusted_external_evidence_registry.yaml
```

The review branch tree is identical to
`origin/codex/v3-p7-6c2-ufotri-semantic-mapping` before this report was added:
the tree delta was zero. Therefore the review phase itself made no changes to
production physics modules, numerical coupling, or the existing V3 solver.

## Runtime activation audit

The evidence, applicability, candidate, validation, and UFOTRI mapping
records remain control-plane artifacts. The production soil and pipeline
owners do not import `ParameterValidationRegistry`,
`parameters_v3.validation`, or any parameter registry. The source-wide scan
outside `src/cteas_ufotri/parameters_v3/` found no `parameters_v3` runtime
imports.

The manifests retain the following gates:

```text
physical_constant_validation_registry.yaml:
  validated_parameters = 1
  active_parameters = 0
  ufotri_parameter_imported = false
  ufotri_active_database = false

ufotri_parameter_mapping.yaml:
  new_validation_candidates = 0
  validated_parameters = 1
  active_parameters = 0
  ufotri_parameter_imported = false
  ufotri_active_database = false
  v3_physics_ready = false
```

Occurrences of `ACTIVE` in the V3 control plane are lifecycle enum values or
explicit rejection guards. They do not constitute runtime activation.

## Implemented software chain

The integrated branches provide software interfaces and fail-closed boundary
tests for:

- atmospheric interface;
- leaf exchange resistance;
- TFWT;
- OBT;
- soil;
- root uptake;
- food transfer;
- intake;
- dose;
- end-to-end V3 pipeline orchestration.

These are implemented interfaces and numerical/software contracts, not a
claim that the corresponding physical parameters or pathways are validated.

## Not validated

The following remain provisional, deferred, or otherwise unavailable for
production validation:

- leaf resistance and other leaf parameters;
- root coefficient `k_root`;
- OBT transfer parameters `kf` and `kr`;
- food-transfer parameters and crop transfer evidence;
- intake and dose-pathway parameters;
- soil transport and retention parameters.

P7.6C-1 validates only the universal H-3 nuclear half-life for the radioactive
decay term `lambda_T = ln(2) / T_half`. It does not validate an environmental
soil half-life, biological elimination half-life, OBT turnover half-life, or
the rest of the soil model.

## Blocked boundaries

```ini
UFOTRI_ACTIVE_DATABASE = FALSE
CALIBRATION = NOT_STARTED
REAL_ATMOS_INPUT = FALSE
V3_PHYSICS_READY = FALSE
```

The current P7.5 atmospheric path uses typed interface/test forcing. No real
CTEAS-Atmos production input was introduced by this review, and no calibration
or observation fitting was started.

## Regression and verification

The first invocation without the repository-root `PYTHONPATH` stopped during
test collection with `ModuleNotFoundError: validation`. This was an invocation
environment issue, not a test result. The repository-compatible commands were
then run with `PYTHONPATH=.`:

| Scope | Command | Result |
| --- | --- | --- |
| Unit | `PYTHONPATH=. .venv/bin/pytest -q tests/unit` | PASS, 351/351 |
| Integration | `PYTHONPATH=. .venv/bin/pytest -q tests/integration` | PASS, 96/96 |
| Architecture | `PYTHONPATH=. .venv/bin/pytest -q tests/architecture` | PASS, 65/65 |
| Regression | `PYTHONPATH=. .venv/bin/pytest -q tests/regression` | PASS, 1/1 |

Additional checks passed:

- `PYTHONPATH=. .venv/bin/python -m compileall -q src tests`;
- package import smoke for `cteas_ufotri`, `parameters_v3`, and `v3_pipeline`;
- `git diff --check` against `origin/main`.

The unit suite emitted the existing NumPy/NetCDF binary-compatibility runtime
warning in `tests/unit/test_era5_reader.py::test_netcdf_mapping`; it did not
fail the suite. No historical or new failure occurred in the four requested
test scopes. External/private-evidence suites were not part of this review
regression command set.

## Readiness conclusion

`V3_INTEGRATION_REVIEW = PASS` is justified for software integration and
regression only. The stable next boundary is
`P7.7-physics-validation-preparation`, defined in
`docs/v3/physics/p7_7_physics_validation_preparation.md`.

The following actions remain prohibited until that preparation and its later
validation gates are completed:

- automatic runtime parameter resolution;
- setting any parameter `ACTIVE`;
- empirical calibration or observation fitting;
- claiming full V3 physics validation or production atmospheric coupling;
- merging this branch into `main`.
