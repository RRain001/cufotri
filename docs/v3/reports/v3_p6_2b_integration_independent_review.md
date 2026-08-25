# V3-P6.2B Integration Independent Review

Status: `PASS_INDEPENDENT_SCOPE_AND_BOUNDARY_REVIEW`

## Review target

```ini
IMPLEMENTATION_BRANCH = codex/v3-p6-2b-integration
INDEPENDENT_BRANCH = codex/v3-p6-2b-integration-independent-review
TARGET_COMMIT = 523c517
P6_2B_INTEGRATION_STATUS = PASS
P6_2B_INTERFACE_FREEZE = PASS
```

The review was run from a separate branch at the implementation commit. No
implementation source or runtime configuration was changed during review.

## Adversarial checks

| Question | Result | Evidence |
|---|---|---|
| Were P6.2B-1 and P6.2B-2 histories preserved? | PASS | Both implementation commits are ancestors of the target |
| Was a new UFOTRI numeric value imported? | PASS | No new parameter file, value, or validated claim |
| Was an ACTIVE database enabled? | PASS | No `production=True` path; P6.2B-1 lookup remains non-production |
| Was the V1/V2 default path changed? | PASS | Default config and legacy plant/coupling files have zero diff from `origin/main` |
| Was resistance recalculated in the facade? | PASS | `plant/v3/pathway.py` consumes `ResistanceState` and calls the existing signed-flux function |
| Was OBT, root, soil, dose, or CTEAS-Atmos connected? | PASS | No implementation imports or runtime registration were added |
| Did the public TFWT interface exist? | PASS | `inventory()`, `activity_concentration()`, and `advance(dt, forcing)` are tested |
| Does the toy conservation boundary close? | PASS | Constant forcing residual is below `1e-12 Bq m^-2` |
| Did protected directories change? | PASS | `configs/`, `parameters/`, and trusted registry diff are empty |

## Reproduction

```text
P6.2B combined targeted tests = PASS 40/40
tests/unit = PASS 259/259
tests/integration = PASS 61/61
tests/regression = PASS 1/1
git diff --check origin/main..HEAD = PASS
ancestry checks = PASS
```

The unit suite retains one pre-existing NumPy/netCDF binary-compatibility
warning in `tests/unit/test_era5_reader.py::test_netcdf_mapping`. It is
unrelated to the P6.2B changes.

## Review disposition

```ini
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
OBT_SOLVER = FALSE
V3_PHYSICS_READY = FALSE
INTEGRATION_BRANCH_MERGE = NOT_PERFORMED
REVIEW_RESULT = PASS
```

The branch is suitable for the next explicitly authorized integration action,
but this review does not authorize production activation or describe the V3
plant pathway as validated physics.
