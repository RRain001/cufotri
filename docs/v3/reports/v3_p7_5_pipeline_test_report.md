# V3-P7.5 end-to-end pipeline integration test report

Status: `PASS_PIPELINE_INTEGRATION`

Branch: `codex/v3-p7-5-pipeline-integration`

## Focused command

```text
PYTHONPATH=.:src .venv/bin/pytest -q \
  tests/unit/test_v3_pipeline_parameters.py \
  tests/integration/test_v3_pipeline.py \
  tests/architecture/test_v3_pipeline_boundary.py
```

Result: 12 tests passed: 3 unit, 5 integration, and 4 architecture-boundary
tests.

Coverage includes:

- complete synthetic Atmosphere -> Soil/Leaf -> TFWT/OBT -> Root -> Food ->
  Intake -> Dose state production;
- zero atmospheric forcing with no artificial inventory generation;
- soil, root, TFWT, OBT, and food ledger residuals;
- mapping/JSON round-trip and a second step after restart;
- missing metadata, mismatched restart time, and tampered serialization;
- immutable explicit configuration;
- source scope, protected paths, default activation, and forbidden-import /
  local-equation checks.

## Cross-stage compatibility command

The P6.2B–P7.5 compatibility command covered the current architecture suite,
all existing typed V3 unit/integration boundaries, deposition/multibox/wet-
deposition tests, the timestep regression, P7 atmospheric interface tests,
and P7.5 tests.

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
  tests/unit/test_v3_pipeline_parameters.py \
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
  tests/integration/test_v3_pipeline.py \
  tests/integration/test_deposition_activity_ledger.py \
  tests/regression/test_timestep.py
```

Result: 169 tests passed: 48 architecture, 38 integration, 82 unit, and 1
regression test.

## Additional checks

- `PYTHONPATH=.:src .venv/bin/python -m compileall -q
  src/cteas_ufotri/v3_pipeline`;
- import smoke for `V3PipelineParameters`, `V3PipelineRunner`,
  `V3SimulationState`, and `V3PipelineLedger`;
- `git diff --check`.

## Test boundary

These tests establish executable software orchestration, typed endpoint
state, balance wiring, and restart serialization. They do not establish
physical V3 readiness, real atmospheric data exchange, CALMET/CALPUFF
equivalence, empirical validation, calibration, dose validity, regulatory
compliance, or production capacity.
