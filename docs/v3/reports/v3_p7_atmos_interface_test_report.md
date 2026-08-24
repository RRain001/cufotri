# V3-P7 atmospheric forcing coupling interface test report

Status: PASS

Branch: `codex/v3-p7-atmos-coupling-interface`

## Focused command

```text
PYTHONPATH=.:src .venv/bin/pytest -q \
  tests/unit/test_atmos_v3.py \
  tests/integration/test_atmos_coupling_interface.py \
  tests/architecture/test_atmos_v3_boundary.py
```

Result: 16 tests passed: 9 unit, 2 integration, and 5 architecture-boundary
tests.

The focused tests cover immutable forcing and metadata records, explicit
units, UTC and range validation, the `air_ht0_concentration` alias, leaf and
soil adapter types, leaf-to-TFWT public propagation, soil deposition
propagation, protected-path checks, source scope, and forbidden-import
checks.

## Cross-stage command

The compatibility command covered all current architecture tests, the
P6.2B–P6.6B typed unit/integration boundaries, deposition/multibox/wet-
deposition tests, the timestep regression, and the new P7 tests:

```text
PYTHONPATH=.:src .venv/bin/pytest -q \
  tests/architecture \
  tests/unit/test_leaf_exchange_resistance.py \
  tests/unit/test_tfwt_solver.py \
  tests/unit/test_obt_solver.py \
  tests/unit/test_soil_hto_v3.py \
  tests/unit/test_root_uptake_v3.py \
  tests/unit/test_food_transfer_v3.py \
  tests/unit/test_intake_v3.py \
  tests/unit/test_dose_v3.py \
  tests/unit/test_v3_plant_pathway_interface.py \
  tests/unit/test_atmos_v3.py \
  tests/unit/test_multibox_soil.py \
  tests/unit/test_wet_deposition.py \
  tests/integration/test_leaf_exchange_resistance_interface.py \
  tests/integration/test_tfwt_storage_interface.py \
  tests/integration/test_v3_plant_pathway_toy.py \
  tests/integration/test_soil_hto_v3_interface.py \
  tests/integration/test_root_uptake_tfwt_interface.py \
  tests/integration/test_food_transfer_interface.py \
  tests/integration/test_intake_interface.py \
  tests/integration/test_dose_interface.py \
  tests/integration/test_atmos_coupling_interface.py \
  tests/integration/test_deposition_activity_ledger.py \
  tests/regression/test_timestep.py
```

Result: 157 tests passed: 44 architecture, 33 integration, 79 unit, and 1
regression test.

## Additional checks

- `PYTHONPATH=.:src .venv/bin/python -m compileall -q
  src/cteas_ufotri/coupling/atmos_v3`;
- import and adapter smoke check for `AtmosphericHTOForcing`,
  `AtmosphericForcingMetadata`, the existing leaf forcing input, and the
  existing soil forcing input;
- `git diff --check`.

## Test boundary

These tests establish a typed software interface and public-pathway
propagation. They do not establish atmospheric dispersion, CALMET/CALPUFF
equivalence, ERA5/WRF or measured-meteorology validity, deposition realism,
plant physical validation, UFOTRI parameter validity, regulatory compliance,
or V3 physics readiness. External-evidence tests remain outside this stage.
