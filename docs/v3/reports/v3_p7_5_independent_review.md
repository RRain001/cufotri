# V3-P7.5 independent boundary review

Verdict: `PASS_PIPELINE_INTEGRATION_ONLY`

Reviewed branch: `codex/v3-p7-5-pipeline-integration`

Reviewed baseline: `b31e80ba4532262c20b4dadca24ec26d3d8029a7`

## Architecture review

The implemented direction is:

```text
AtmosphericHTOForcing
        |
        v
V3PipelineRunner
        |
        v
existing typed V3 module APIs
        |
        v
FoodInventory -> IntakeState -> DoseState
```

The new runner is a frozen configuration facade and retains no mutable
inventory. The state is frozen, every downstream endpoint has a common UTC
timestamp, and the runner rejects missing metadata, incomplete initial
states, mismatched identifiers, mismatched restart times, negative endpoint
inventories, and invalid serialized payloads.

The runner uses existing public solver methods and existing state/balance
records. It does not define transport, storage, biological, root-uptake,
food-transfer, intake, or dose equations. The only arithmetic at this layer
is endpoint inventory reconciliation using the transfer balances emitted by
the existing modules.

## Protected-path and dependency review

- New production source is isolated to `src/cteas_ufotri/v3_pipeline/`.
- Existing atmospheric P7 source is not modified.
- V1/V2 runtime, existing plant/soil/food/dose modules, legacy coupling,
  configs, parameters, and the trusted registry are unchanged.
- No UFOTRI parameter database, CTEAS-Atmos executable, CALMET/CALPUFF
  reader, subprocess, or external file reader is imported.
- Default activation remains unchanged and V3 physics readiness remains
  false.

## Evidence

- P7.5 focused tests: 12 passed.
- Cross-stage compatibility tests: 169 passed.
- Architecture tests: 48 passed.
- Compile, import smoke, and whitespace checks passed.

## Limitations and disposition

The synthetic end-to-end path proves controlled software composition only.
It is not real atmospheric coupling, observational validation, physical
calibration, UFOTRI parameter validation, dose validation, regulatory
assessment, or production case execution. P7.6 may address parameter
validation/calibration contracts; P8 may define real CTEAS-Atmos data
exchange, without weakening this orchestration boundary.
