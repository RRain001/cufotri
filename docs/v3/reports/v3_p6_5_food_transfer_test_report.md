# V3-P6.5 plant harvest and food-transfer test report

Status: PASS_FOOD_TRANSFER_IMPLEMENTED

Branch: codex/v3-p6-5-food-transfer

## Required test matrix

| Requirement | Evidence | Result |
|---|---|---|
| Positive OBT transfer | test_positive_obt_inventory_transfers_to_food_product | PASS |
| Zero OBT and TFWT inventory | test_zero_plant_inventory_produces_zero_food_inventory | PASS |
| Harvest conservation | test_harvest_conservation_closes_for_obt_and_tfwt_components | PASS |
| Product boundary | test_harvest_and_food_states_are_immutable_and_have_no_downstream_fields | PASS |
| End-to-end Soil -> Root -> TFWT -> OBT -> Food | test_soil_root_tfwt_obt_food_toy_pathway_closes | PASS |

Additional tests cover explicit provisional parameters, public inventory and
product methods, component closure, timestamp alignment, and two-output
result unpacking.

## Commands and results

P6.5 focused command:

    PYTHONPATH=.:src .venv/bin/pytest -q +      tests/unit/test_food_transfer_v3.py +      tests/integration/test_food_transfer_interface.py +      tests/architecture/test_food_transfer_v3_boundary.py

Result: 11 tests collected and 11 passed.

The cross-stage command included P6.2B/P6.2C, P6.3, P6.4, P6.5, the V3
pathway, existing deposition/wet-deposition/multibox-soil tests, and the
timestep regression. Result: 102 tests passed.

Additional checks passed:

- Python compileall for food_v3;
- import smoke for FoodInventory, HarvestState, HarvestParameters, and
  FoodTransferSolver;
- git diff --check;
- 26 architecture-boundary tests across P6.2C through P6.5.

The unfiltered external-evidence tests were not modified or forced green.
Their missing-input and host-dependent behavior remains outside this stage.

## Test boundary

These tests establish a software inventory-transfer interface, explicit unit
conversion, public source access, and algebraic conservation. They do not
establish food mass/yield realism, validated UFOTRI fractions, ingestion,
dose, population exposure, regulatory compliance, or V3 physics readiness.
