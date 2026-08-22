# V3-P7.5 end-to-end pipeline integration report

Status: `PASS_PIPELINE_INTEGRATION`

Branch: `codex/v3-p7-5-pipeline-integration`

Base commit: `b31e80ba4532262c20b4dadca24ec26d3d8029a7`

## Implemented boundary

The new package is `src/cteas_ufotri/v3_pipeline/` and contains:

- `V3PipelineParameters`: an immutable, explicit configuration record;
- `V3PipelineRunner`: a stateless one-interval orchestration facade;
- `V3SimulationState`: the complete immutable output state;
- `V3PipelineLedger`: the existing subsystem balances retained for audit;
- fail-closed input/state/serialization validation;
- mapping and JSON restart round-trip methods.

The output state records atmospheric forcing, soil, TFWT, OBT, root,
harvest, food, intake, dose, top-level provenance, and the last-step ledger.
No global inventory or hidden parameter state is retained by the runner.

## Controlled execution order

```text
AtmosphericHTOForcing
        |
        +--> SoilStorageSolver -> soil deposition endpoint
        |
        +--> V3PlantPathway.leaf_flux -> TFWTStorageSolver
                                      |
                                      v
                                  OBTSolver
        |
        +--> RootUptakeSolver -> soil/root transfer ledger
                                      |
                                      v
                         TFWT and soil endpoint state wiring
                                      |
                                      v
                             FoodTransferSolver
                                      |
                                      v
                             FoodIntakeSolver
                                      |
                                      v
                                DoseSolver
```

The pipeline calls public APIs only. It does not reconstruct resistance,
reimplement storage/transfer/dose equations, or create parameter defaults.
The OBT balance's `tfwt_loss_bq_m2` is applied through the existing
`TFWTState.with_inventory` API before food transfer. The root balance's
transfer inventory is applied through existing `SoilState.with_inventory` and
TFWT state APIs at the common endpoint timestamp.

The root solver receives the step-start soil snapshot after the soil solver
has been called for the atmospheric deposition operation. This preserves the
root solver's public timestamp contract: its returned root record ends at the
same timestamp as the soil deposition endpoint. If the two existing public
balances cannot produce a non-negative endpoint inventory, the pipeline
raises a validation error rather than clamping or repairing the state.

## Explicit inputs and exclusions

All of the following remain caller-supplied and validated: interval,
equilibrium air concentration, resistance state, soil half-life, root
coefficient, OBT rates and biological forcing, harvest parameters,
consumption parameters, dose coefficient, root-zone identifier, and consumer
identifier. No value is imported from UFOTRI data or a regulatory database.

P7.5 does not add:

- CTEAS-Atmos executable or process coupling;
- CALMET/CALPUFF/ERA5/WRF/measured-data readers;
- transport, hydrology, plant, food, intake, or dose equations;
- calibration, observational validation, regulatory assessment, or
  production activation.

The JSON methods define only a typed in-memory state restart representation;
they are not an external atmospheric data-exchange format.
