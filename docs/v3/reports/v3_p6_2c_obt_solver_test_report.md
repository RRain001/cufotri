# V3-P6.2C OBT solver test report

Status: `PASS_OBT_SOLVER_IMPLEMENTED`

## Required test matrix

| Requirement | Test | Result |
|---|---|---|
| Constant positive TFWT forms OBT | `test_tfwt_driven_obt_formation_increases_inventory` | PASS |
| Zero TFWT makes OBT decrease or remain stable | `test_zero_tfwt_causes_obt_to_decrease` | PASS |
| TFWT loss equals OBT increase plus other loss | `test_tfwt_loss_equals_obt_increase_plus_other_loss` | PASS |
| Day formation exceeds night formation | `test_daytime_formation_exceeds_nighttime_formation` | PASS |

Additional tests cover inventory/concentration consistency, absence of a stored
TFWT/OBT ratio, explicit-rate requirements, invalid state rejection, public
TFWT API use, and isolation from configuration/parameter/legacy paths.

## Commands and results

The focused P6.2C unit and architecture tests passed:

```text
PYTHONPATH=.:src .venv/bin/pytest -q \
  tests/unit/test_obt_solver.py \
  tests/architecture/test_obt_solver_boundary.py
11 passed
```

The P6.2C tests plus the relevant P6.2B TFWT and plant-pathway regression tests
passed:

```text
PYTHONPATH=.:src .venv/bin/pytest -q \
  tests/unit/test_obt_solver.py \
  tests/architecture/test_obt_solver_boundary.py \
  tests/unit/test_tfwt_solver.py \
  tests/integration/test_tfwt_storage_interface.py \
  tests/unit/test_v3_plant_pathway_interface.py \
  tests/architecture/test_tfwt_solver_boundary.py \
  tests/architecture/test_v3_plant_pathway_boundary.py
34 passed
```

The package also passed a Python bytecode compilation check and an import smoke
check using the repository `.venv`/source path. The P6.2C targeted tests used
no production simulation or external raw data.

## Broader repository test note

The unfiltered repository command was also run:

```text
PYTHONPATH=.:src .venv/bin/pytest -q
```

It reported 17 failures outside the P6.2C gate. The failures are from existing
external-evidence and stage-boundary assumptions: several tests expect SB1 or
ERA5 inputs to be unavailable although this host has local external artifacts;
one test detects the intentionally new V3 `src/` implementation against the
architecture-only `main` baseline; private reblinding payloads are present on
this host; and one SB1 benchmark sees an empty local forcing CSV. The focused
P6.2C/P6.2B command above has no failures, and no V1/V2 source or protected
configuration path was changed to make the broader suite appear green.

## Test boundary

These tests establish implementation and interface behavior only. They do not
establish UFOTRI parameter validity, empirical calibration, field validation,
soil coupling, foodchain behavior, dose results, or V3 physics readiness.
