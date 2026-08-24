# V3-P6.3 soil HTO transport test report

Status: `PASS_SOIL_HTO_IMPLEMENTED`

## Required test matrix

| Requirement | Test | Result |
|---|---|---|
| Positive deposition increases soil inventory | `test_positive_deposition_increases_soil_inventory` | PASS |
| Zero deposition permits decay | `test_zero_input_causes_soil_inventory_to_decay` | PASS |
| Input equals storage change plus losses | `test_soil_input_equals_storage_change_transport_loss_and_decay` | PASS |
| Upper-layer loss routes to lower-layer gain | `test_upper_layer_loss_equals_lower_layer_gain_plus_remaining_loss` | PASS |

Additional tests cover the immutable state, derived concentration, explicit
half-life requirement, signed transport, negative-inventory protection,
invalid fluxes, public `SoilState.advance`, and V1/V2/configuration boundary
checks.

## Commands and results

P6.3 unit, architecture, and integration tests:

```text
PYTHONPATH=.:src .venv/bin/pytest -q \
  tests/unit/test_soil_hto_v3.py \
  tests/architecture/test_soil_hto_v3_boundary.py \
  tests/integration/test_soil_hto_v3_interface.py
14 passed
```

Existing timestep regression:

```text
PYTHONPATH=.:src .venv/bin/pytest -q tests/regression/test_timestep.py
1 passed
```

The P6.3 tests were also run with the P6.2B/P6.2C public-pathway tests and the
existing deposition, wet-deposition, and legacy multibox-soil tests; the
combined targeted command passed without failures. Python bytecode compilation,
package import smoke, and `git diff --check` also passed.

The unfiltered external-evidence test groups were not rerun or modified. Their
host-dependent failures and missing-input assumptions remain documented by the
previous P6.2C test report, consistent with this stage plan.

## Test boundary

These tests establish software storage, transport-interface, unit, and balance
behavior only. They do not establish soil hydrology, field measurements,
UFOTRI parameter validity, root uptake, plant transfer, foodchain behavior,
dose results, or V3 physics readiness.
