# ADR-009: V3 pipeline numerical coupling semantics

Status: Accepted for the P7.5B software boundary

Date: 2026-08-22

## Context

P7.5 already composes the typed V3 soil, leaf-exchange, TFWT, OBT, root,
food, intake, and dose interfaces.  The purpose of P7.5B is to make the
actual one-interval execution semantics auditable before any parameter
evidence or real atmospheric coupling is introduced.  This decision is about
state ownership and operator ordering; it does not add a physical equation,
activate a parameter database, or establish physical validation.

The repository's earlier V3 ADRs remain under `docs/v3/adr/`.  This task-level
ADR is stored under the requested `docs/adr/` path and continues that sequence
with ADR-009.

## Decision

### Time contract

For one step, let the input endpoint be `t_n` and the interval be
`[t_n, t_{n+1}]`, where `t_{n+1} = t_n + interval_seconds`.

`AtmosphericHTOForcing.timestamp` is the interval-start label `t_n`.  Its
values are interpreted as forcing representative of the complete interval;
they are not claimed to be an instantaneous start or end observation.  The
runner holds that forcing input constant for the interval through the
existing typed adapters.

Every continuous state and downstream record emitted by the runner has the
endpoint timestamp `t_{n+1}`.  The atmospheric forcing retains `t_n` as its
representative interval label.  A restart step is valid only when the next
forcing timestamp equals the serialized state endpoint.

### Frozen operator sequence

The current public API execution is frozen as this explicit sequential split:

```text
S_n, T_n, O_n, F_n(timestamp=t_n)
  |
  +--> SoilStorageSolver(S_n, F_n.to_soil_forcing())
  |       -> S_dep(t_{n+1})
  |
  +--> V3PlantPathway(F_n.to_leaf_forcing())
  |       -> leaf flux
  +--> TFWTStorageSolver(T_n, leaf flux)
  |       -> T_leaf(t_{n+1})
  |
  +--> OBTSolver(T_leaf(t_{n+1}), O_n)
  |       -> O_{n+1} and reported TFWT loss L_TFWT
  |
  +--> RootUptakeSolver(S_n, root forcing)
  |       -> interval root transfer J_root and root ledger
  |
  +--> soil reconciliation:
  |       S_{n+1} = S_dep - J_root
  |
  +--> TFWT reconciliation:
  |       T_{n+1} = T_leaf - L_TFWT + J_root
  |
  +--> FoodTransferSolver(O_{n+1}, T_{n+1})
  +--> FoodIntakeSolver(food endpoint)
  +--> DoseSolver(intake endpoint)
```

The root solver is called after the deposition solver in the runner, but its
input is the retained step-start `S_n`, not `S_dep`.  This is a deliberate
source-snapshot rule.  Its transfer is then reconciled against the
post-deposition soil endpoint.  OBT receives the leaf-only TFWT intermediate;
root input is applied only after the OBT-reported TFWT loss.

### State and record ownership

- `SoilState`, `TFWTState`, and `OBTState` are continuous state reservoirs.
- `RootFlux` and the module balances are interval transfer/ledger records.
- `HarvestState`, `FoodInventory`, `IntakeState`, and `DoseState` are
  downstream endpoint event/readout records.

Food, intake, and dose are therefore a non-mutating endpoint assessment in
P7.5.  `FoodTransferSolver` reports a plant-to-food balance but does not
decrement the emitted TFWT or OBT state, and the pipeline does not model
continuous harvesting or cumulative food consumption.

### Decay and loss ownership

Soil radioactive decay is evaluated inside `SoilStorageSolver` during the
soil interval advance.  OBT formation and OBT-side loss are evaluated inside
`OBTSolver`; its reported TFWT loss is then applied at the explicit TFWT
boundary shown above.  The current TFWT call does not add a separate decay,
water-loss, or transformation term.  Root transfer, food transfer, intake,
and dose are not continuous decay reservoirs in this pipeline step.

### Numerical scope

This is an explicit sequential/operator-split coupling.  It is not a fully
implicit coupled solution.  Timestep refinement is consequently a required
software-numerical check before the semantics can be treated as frozen for
later work.  The P7.5B regression compares `dt`, `dt/2`, and `dt/4` over the
same horizon and requires finite, non-negative continuous inventories with
`E2 < E1`; it does not assign an unverified physical accuracy threshold or
claim a formal convergence order.

The orchestration layer may perform only existing-solver balance arithmetic and
endpoint inventory reconciliation.  Transport, storage, decay, resistance,
root-uptake, food-transfer, intake, and dose equations remain owned by their
typed subsystem modules.

## Consequences

The sequence, timestamp ownership, root soil snapshot, and TFWT/OBT/root
ordering are now testable and reviewable.  Any future change to these rules
requires an ADR update and corresponding ordering/refinement tests.  Passing
these checks means software numerical coupling semantics are frozen only; it
does not mean V3 physical validation, UFOTRI parameter readiness, calibration,
real CTEAS-Atmos coupling, or production/regulatory readiness.

## Revisit conditions

Revisit only with a documented alternative time/operator contract, a
reproducer or mathematical justification, updated conservation and restart
tests, and explicit separation from the P7.6 evidence/calibration gate.
