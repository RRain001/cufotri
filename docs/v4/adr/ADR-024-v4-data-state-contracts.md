# ADR-024 — V4 data and state contracts

## Status

Accepted after V4-1 control-plane contract review. This ADR does not authorize
implementation of a selected V4 physical model.

Reviewed content head:

`27ddffeaa2d88aac34f197ce2a4bcf3a67f42ec6`

Verification:

```text
V3 Remediation CI 32923288035 = PASS
V3 Protected Integration Gate 32923288127 = PASS
portable suite = 1036 passed / 1 skipped / 57 deselected
explicit invariants = 115 passed
```

## Context

P7.8C authorized only `V4_DATA_AND_STATE_CONTRACTS`. The selected future leaf,
OBT and root models remain held until their item-specific equation/unit,
ownership, conservation/restart, validation, coupling and independent-review
gates are closed.

V4-1 therefore turns the P7.8B-2 architecture into explicit contracts without
changing the frozen V3 runtime, admitting candidate parameter values, or
silently selecting a biological functional form that P7.8B-2 left open.

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
`Bq m^-2`. P7.8B-2 selected a generic precursor source
`u_P(T,A,d,s,T_leaf,...)`; V4-1 therefore keeps the source functional form
unresolved. It does **not** assume a multiplicative, additive or other unreviewed
composition of day/night, photosynthetic and temperature response functions.

To make the selected shorthand

`dP/dt = u_P - k_P P`

conservative when `k_PB P` feeds `B_x`, V4-1 decomposes precursor removal
without adding a new biological parameter:

```text
J_P_to_Bx = k_PB P
J_P_other = (k_P - k_PB) P
0 <= k_PB <= k_P
```

The candidate balances are

```text
dP/dt   = u_P - k_P P
dB_x/dt = J_P_to_Bx - J_Bx_to_Bn - J_Bx_other
dB_n/dt = J_Bx_to_Bn - J_Bn_other
```

so internal transfers cancel exactly in the composite inventory. This is a
symbolic conservation contract only; no rate or response-function value is
admitted.

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

## Review corrections

Two issues were caught without weakening the scientific gates:

1. An intermediate OBT draft over-specified the unresolved source composition
   and introduced an unnecessary precursor-loss symbol. The final contract
   restores the P7.8B-2 generic source boundary and uses only the selected
   `k_P`/`k_PB` rates for conservation bookkeeping.
2. An initial CI run found that the stage-scope test omitted its own test file
   from the expected changed-file set. The test governance error was corrected;
   no contract or runtime semantics changed as a result.

## Compatibility

`v3_frozen_baseline` remains default and rollback. Missing required V4 fields
fail closed. No V3 scalar state or parameter is silently reinterpreted as a V4
multi-state, layer or response-function quantity.

## Consequences

V4-1 closes the data/state/equation contract-preparation stage as a reviewed
control-plane boundary. It does not authorize leaf, OBT or root implementation.
Each model still requires its own later technical and independent review.

The next roadmap item is `V4_LEAF_DYNAMIC_STOMATAL_RESPONSE`, entering an
item-specific review/authorization gate rather than production implementation.

```ini
V4_1_CONTROL_PLANE_CONTRACTS = PASS_CONTROL_PLANE_CONTRACT_REVIEW
PRODUCTION_RUNTIME_CHANGED = FALSE
SOLVER_IMPLEMENTATION_AUTHORIZED = FALSE
NUMERICAL_COUPLING_CHANGE_AUTHORIZED = FALSE
CANDIDATE_PARAMETER_VALUES_ADMITTED = FALSE
LEAF_IMPLEMENTATION_AUTHORIZED = FALSE
OBT_IMPLEMENTATION_AUTHORIZED = FALSE
ROOT_IMPLEMENTATION_AUTHORIZED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```
