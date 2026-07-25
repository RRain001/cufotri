# Dynamic-air inventory architecture

Status: `ARCHITECTURE_ONLY`

```text
IMPLEMENTATION_STATUS =
DEFERRED_PENDING_EMPIRICAL_AND_REFERENCE_EVIDENCE
```

This is the highest-risk candidate because a dynamic inventory can duplicate
activity already represented by steady Gaussian transport.

The reserved state is total air HTO activity in Bq within a declared control
volume. Inputs are source activity and separately identified re-emission
feedback. Outputs are transport-boundary export, ventilation, deposition, and
decay. Storage is the final inventory. Every term has a transfer ID and control
volume; concentration is derived from inventory and volume.

Responsibility boundary:

- a Gaussian plume may provide boundary concentration or through-flow, but not
  simultaneously own the same stored activity;
- deposition is removed once from the chosen transport owner;
- re-emission enters once through a matched surface-to-air transfer;
- ventilation and advection are boundary outputs, not numerical residuals.

Required analytic cases are a closed-box pulse, ventilated exponential pulse,
constant source/ventilation equilibrium, zero-volume rejection, and
time-step-convergence case. Formal implementation additionally requires an
independent transport reference and empirical mixing/ventilation evidence.

No air-state solver, Gaussian coupling, storage equation, or coefficient is
implemented here.
