# V3-P6.6A food consumption and intake pathway test report

Status: PASS_INTAKE_PATHWAY_IMPLEMENTED

Branch: codex/v3-p6-6a-intake-pathway

## Required test matrix

| Requirement | Evidence | Result |
|---|---|---|
| Positive food inventory | `test_positive_food_inventory_produces_positive_annual_intake` | PASS |
| Zero food inventory | `test_zero_food_inventory_produces_zero_annual_intake` | PASS |
| Consumption equation | `test_consumption_equation_closes_with_explicit_units` | PASS |
| Adult/child separation | `test_adult_and_child_inputs_remain_separate_states` | PASS |
| Immutable intake boundary | `test_intake_state_is_immutable_and_has_no_downstream_result_fields` | PASS |
| Product and parameter validation | `test_intake_requires_matching_product_and_provisional_parameters` | PASS |
| Full Soil -> Root -> TFWT -> OBT -> Food -> Intake path | `test_soil_root_tfwt_obt_food_intake_toy_pathway_closes` | PASS |

## Commands and results

P6.6A focused command:

    PYTHONPATH=.:src .venv/bin/pytest -q \
      tests/unit/test_intake_v3.py \
      tests/integration/test_intake_interface.py \
      tests/architecture/test_intake_v3_boundary.py

Result: 12 tests passed, including 7 unit, 1 integration, and 4 boundary
tests.

The cross-stage command covered the P6.2B through P6.6A typed boundaries,
related deposition/multibox/wet-deposition tests, and the timestep
regression. Result: 114 tests passed: 30 architecture, 29 integration, 1
regression, and 54 unit tests.

Additional checks passed:

- `PYTHONPATH=.:src .venv/bin/python -m compileall -q
  src/cteas_ufotri/exposure/intake_v3`;
- import smoke for `ConsumptionParameters`, `FoodIntakeSolver`, and
  `IntakeState`;
- `git diff --check`.

## Test boundary

The toy pathway and conservation checks establish a software inventory
interface and dimensional algebra. They do not establish validated food
consumption data, empirical exposure validation, dose validity, regulatory
compliance, or V3 physics readiness. Existing external-evidence tests were
not modified or forced green.
