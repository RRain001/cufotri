# ADR-026 — V4 system roadmap reset

## Status

Accepted for roadmap-control review.

## Context

The V3 line now provides a runnable, restartable and conservation-checked software chain from typed atmospheric forcing through soil, leaf exchange, TFWT, OBT, root uptake, food transfer, intake and dose. V3.1 adds the mass-basis contract without changing solver physics. V4-2 R4 has reached a prospective soybean experiment design for the dynamic stomatal-response candidate, but no experiment has been executed, no empirical packet has been collected, no parameter has been calibrated and no V4 solver implementation is authorized.

The project now needs a system-level sequencing decision. Continuing to deepen one leaf-evidence branch before closing atmospheric exchange, system-wide physical gaps, sensitivity priorities and the intended soil architecture would risk optimizing one subsystem while the complete environmental-transfer and dose chain remains physically provisional.

## Decision

The project north star is the complete, traceable pathway:

```text
CTEAS-Atmos forcing
  -> atmospheric HTO concentration and deposition
  -> soil and plant HTO state
  -> TFWT / OBT
  -> food transfer
  -> intake
  -> dose
```

Every future increase in model complexity must be justified by its role in this complete chain and by independent physical evidence.

### 1. Frozen runnable baseline

The current V3/V3.1 runtime remains the default runnable reference and rollback target. This roadmap reset changes no production solver equation, numerical coupling rule, runtime state, parameter value or activation state.

### 2. Leaf R4 checkpoint

V4-2 R4 is retained as a design checkpoint only. No R5-style public-data search, experiment execution, response-function selection, calibration or leaf-solver implementation is authorized by this decision. Leaf work may resume only after a later system-priority review or arrival of a complete admissible empirical packet.

### 3. Next project work

The next two system stages are, in order:

1. **Atmospheric exchange contract closure** — freeze the production-facing data contract between CTEAS-Atmos and CTEAS-UFOTRI without waiting for CTEAS-Atmos solver completion. The UFOTRI side must be able to consume replay/synthetic forcing under the same contract.
2. **System physics-gap and sensitivity audit** — classify every active/provisional input in the Atmos -> soil/plant -> food -> dose chain and determine which unresolved quantities materially control final model outputs before allocating further validation effort.

### 4. Soil architecture clarification

The current V3 soil runtime is a one-layer HTO inventory model with signed transport input. It is not a three-layer hydrology model. A future minimal three-layer soil-water/HTO inventory model is therefore treated as a candidate system target, not an existing capability.

Any future three-layer implementation must first define layer water and HTO ownership, inter-layer fluxes, surface input, lower-boundary loss, root extraction, radioactive decay, layer/global conservation, restart and failure behavior. Full Richards/Darcy hydrology is not authorized by this roadmap reset.

### 5. Downstream model restraint

The current food -> intake -> dose endpoint pathway remains sufficient as the reference assessment boundary. Continuous food kinetics, cumulative harvest, or additional dose complexity are not priority work unless the system audit shows they materially limit the target application.

## Explicit non-authorization

This decision does not authorize:

- changes to `src/cteas_ufotri/plant/**` solver equations;
- changes to `src/cteas_ufotri/v3_pipeline/**` numerical ordering;
- a three-layer soil solver;
- full soil hydrology;
- dynamic stomatal solver implementation;
- OBT two-pool implementation;
- root water-flux implementation;
- calibration or parameter fitting;
- parameter activation;
- real CTEAS-Atmos runtime coupling.

## Consequences

The repository may now proceed with control-plane and interface work that supports the complete system rather than a single subsystem. The first implementation-bearing physics change after this reset requires a separate stage, explicit evidence, independent review and authorization.

```ini
V4_SYSTEM_ROADMAP_RESET = PASS_CONTROL_PLANE
V3_FROZEN_BASELINE_DEFAULT = TRUE
V3_1_BASELINE_PRESERVED = TRUE
LEAF_R4_CHECKPOINT_FROZEN = TRUE
LEAF_R5_AUTHORIZED = FALSE
ATMOS_EXCHANGE_CONTRACT = NEXT
SYSTEM_PHYSICS_GAP_SENSITIVITY_AUDIT = AFTER_ATMOS_CONTRACT
CURRENT_SOIL_RUNTIME = ONE_LAYER_SIGNED_TRANSPORT
THREE_LAYER_SOIL = CANDIDATE_NOT_IMPLEMENTED
FULL_SOIL_HYDROLOGY_AUTHORIZED = FALSE
SOLVER_CHANGES_AUTHORIZED = FALSE
NUMERICAL_COUPLING_CHANGES_AUTHORIZED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
V3_PHYSICS_READY = FALSE
```
