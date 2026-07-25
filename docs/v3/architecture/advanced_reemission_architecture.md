# Advanced re-emission architecture

Status: `ARCHITECTURE_ONLY`

Implementation status: `NOT_STARTED`

Two explicit future modes are reserved:

- `v2_legacy`: exact frozen candidate behavior;
- `v3_manual_fidelity`: opt-in implementation after evidence gates.

The V3 interface consumes surface activity inventory, surface water state,
air/surface concentration diagnostics, meteorology, time-step boundaries, and
an event stream. It returns surface-to-air activity flux, event diagnostics,
updated surface inventory, and a standard activity ledger.

The rain-start 3% rule is represented as a discrete event with event time,
eligible pre-event inventory, removed fraction, emitted activity, and receiving
air-boundary transfer ID. Concentration-dependent DIFF receives an explicitly
unit-tagged concentration and cannot infer water/area bases. Event integration
defines whether an event occurs at the left boundary, right boundary, or
within a split time step.

Atmospheric feedback is a boundary transfer, not activity creation. The
surface output and atmosphere input must match by transfer ID and Bq. Tests
must cover zero inventory, no-rain, repeated rain starts, time-step boundary
placement, DIFF grids, negative-flux prevention, and global feedback closure.

No equation, coefficient, 3% calculation, or DIFF relation is implemented in
this architecture baseline.
