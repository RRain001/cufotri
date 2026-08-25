# V3-P6.4 root uptake and Soil-Plant coupling test report

Status: PASS_ROOT_UPTAKE_IMPLEMENTED

Branch: codex/v3-p6-4-root-uptake

## Required test matrix

| Requirement | Evidence | Result |
|---|---|---|
| Positive soil concentration gives positive root flux | test_positive_soil_concentration_produces_positive_root_flux | PASS |
| Zero soil concentration gives zero root flux | test_zero_soil_concentration_produces_zero_root_flux | PASS |
| Soil-root conservation closes | test_soil_root_inventory_balance_closes | PASS |
| Root boundary excludes plant compartments | test_root_state_is_immutable_and_has_no_plant_compartment_fields | PASS |
| Root solver boundary excludes forbidden imports | test_root_solver_uses_public_soil_api_and_has_no_forbidden_solver_imports | PASS |
| Soil -> Root -> TFWT toy pathway | test_soil_root_tfwt_toy_pathway_closes_transfer_and_storage | PASS |
| Public TFWT state consumes RootFlux | test_public_tfwt_state_advance_consumes_root_flux_without_root_state | PASS |

## Commands and results

The focused P6.4 and compatible TFWT command was:

    PYTHONPATH=.:src .venv/bin/pytest -q +      tests/unit/test_root_uptake_v3.py +      tests/integration/test_root_uptake_tfwt_interface.py +      tests/architecture/test_root_uptake_v3_boundary.py +      tests/unit/test_tfwt_solver.py +      tests/integration/test_tfwt_storage_interface.py +      tests/architecture/test_tfwt_solver_boundary.py

Result: 28 tests collected and 28 passed.

The cross-stage compatibility command also included the P6.3 soil tests,
P6.2C OBT tests, the V3 pathway tests, and the timestep regression. It passed
without failures. This checks that the optional root input did not regress the
existing leaf-only TFWT path or the prior isolated stages.

Additional checks passed:

- Python compileall for root_v3 and tfwt_v3;
- import smoke for RootFlux, RootState, RootParameters, RootUptakeForcing,
  RootUptakeSolver, and TFWTStorageSolver;
- git diff --check;
- architecture protected-path checks.

## Test boundary

These tests establish a software transfer interface, dimensional unit
contract, fail-closed source-inventory guard, and TFWT storage accounting.
They do not establish a physical root uptake coefficient, root morphology,
soil hydrology, field observation agreement, UFOTRI parameter validity,
foodchain behavior, dose results, or V3 physics readiness.

The unfiltered external-evidence tests were not changed or forced green.
Missing-input and host-dependent external evidence behavior remains outside
this stage.
