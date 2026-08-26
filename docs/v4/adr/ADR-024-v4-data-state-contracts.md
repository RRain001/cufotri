# ADR-024 — V4 data and state contracts

## Status

Accepted for V4-1 control-plane contract review. This ADR does not authorize
implementation of a selected V4 physical model.

## Context

P7.8C authorized only `V4_DATA_AND_STATE_CONTRACTS`. The selected future leaf,
OBT and root models remain held until their item-specific equation/unit,
ownership, conservation/restart, validation, coupling and independent-review
gates are closed.

V4-1 therefore must turn the P7.8B-2 architecture into explicit contracts
without changing the frozen V3 runtime or admitting candidate parameter values.

## Decision

V4-1 freezes four control-plane contracts:

1. common provenance, unit, timestamp, missing-data, state-ownership, restart
   and validation rules;
2. dynamic stomatal-response equation/unit and forcing contract;
3. precursor/exchangeable/non-exchangeable OBT inventory and conservation
   contract;
4. layered water-flux root boundary and coupling-ownership contract.

A common validation-case envelope makes candidate item, baseline profile,
replicate identity, time alignment, variable units, provenance and
pre-registered metrics explicit.

## Leaf boundary

The future leaf response is represented symbolically as

`g_s = g_s,max F_light F_vpd F_temp F_stage`,

with `g_s [m s^-1]`, `r_c = 1/g_s [s m^-1]`, and the existing resistance chain
remaining the baseline. Response functions are dimensionless and must declare
domains and bounds before any implementation. V4-1 supplies no response shape,
coefficient or `g_s,max` value.

No new persistent candidate leaf state is introduced by V4-1. Radiation/PAR,
VPD, leaf temperature and stage are external forcings; conductance and
resistance are diagnostics.

## OBT boundary

The future OBT package uses candidate inventories `P`, `B_x` and `B_n`, each in
`Bq m^-2`. To remove the ambiguity in the earlier shorthand `dP/dt = u_P-k_P P`,
V4-1 explicitly decomposes precursor removal into an internal transfer and an
external/other precursor loss:

```text
J_P_to_Bx = k_PB P
J_P_other = k_P_other P
k_P = k_PB + k_P_other
```

The candidate balances are

```text
dP/dt   = u_P - J_P_to_Bx - J_P_other
dB_x/dt = J_P_to_Bx - J_Bx_to_Bn - J_Bx_other
dB_n/dt = J_Bx_to_Bn - J_Bn_other
```

so internal transfers cancel exactly in the composite inventory. This is a
symbolic conservation contract only; no rate value is admitted.

`B_total = B_x + B_n` is a derived readout, not an additional storage state.
There is no automatic mapping from the frozen scalar OBT state to `P/B_x/B_n`.

## Root boundary

The future root boundary is defined symbolically by

```text
M_s,i = theta_i Delta_z_i C_w,i
J_root,i = q_w,i C_w,i
```

where `q_w,i [m s^-1]` is an observed water-uptake forcing or an output of a
separately reviewed water model. The root boundary does not generate `q_w,i`,
does not implement hydrology, and does not convert an `s^-1` root rate into a
velocity.

The soil sink and plant source are one transfer identity and must be applied
exactly once. Any future implementation still requires a P7.5/P7.5B numerical
coupling rereview.

## Validation boundary

Empirical validation cases must carry independent provenance, explicit units,
replicate IDs, time alignment and pre-registered metrics. Synthetic cases can
verify software, dimensional and conservation behavior only. Production solver
arithmetic cannot define expected observations.

## Compatibility

`v3_frozen_baseline` remains default and rollback. Missing required V4 fields
fail closed. No V3 scalar state or parameter is silently reinterpreted as a V4
multi-state, layer or response-function quantity.

## Consequences

V4-1 can close the data/state/equation contract preparation step, but it cannot
by itself authorize leaf, OBT or root implementation. Each model still requires
its own later technical and independent review using these contracts.

```ini
V4_1_CONTROL_PLANE_CONTRACTS = DEFINED_PENDING_REVIEW
PRODUCTION_RUNTIME_CHANGED = FALSE
SOLVER_IMPLEMENTATION_AUTHORIZED = FALSE
NUMERICAL_COUPLING_CHANGE_AUTHORIZED = FALSE
CANDIDATE_PARAMETER_VALUES_ADMITTED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```
