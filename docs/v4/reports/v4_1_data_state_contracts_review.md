# V4-1 Data and State Contracts — Technical Review

## Scope

V4-1 is the control-plane stage authorized by P7.8C. It freezes symbolic
contracts for leaf exchange, OBT formation, root water-flux uptake, provenance,
validation cases, state ownership and restart behavior. It does not implement
candidate physics.

Entry baseline:

```text
MAIN = 175c5d7ed7fbec916485aa44c0ae733d330b661f
P7_8C = PASS_CONTRACT_PREPARATION_AUTHORIZATION
```

## Contract set

- `docs/v4/contracts/v4_data_state_contract_registry.yaml`
- `docs/v4/contracts/v4_common_data_contract.yaml`
- `docs/v4/contracts/leaf_dynamic_stomatal_contract.yaml`
- `docs/v4/contracts/obt_formation_package_contract.yaml`
- `docs/v4/contracts/root_water_flux_contract.yaml`
- `schemas/v4/v4_validation_case_envelope.schema.json`
- `docs/v4/adr/ADR-024-v4-data-state-contracts.md`

## Leaf review

The leaf contract keeps the current resistance chain as the baseline and defines
a future dimensionally typed conductance response only. `g_s` and `g_ex` are
velocities `[m s^-1]`; `r_a`, `r_b`, `r_c`, and `r_tot` are resistances
`[s m^-1]`. Light/PAR, VPD, leaf temperature, and stage remain external
forcings. V4-1 introduces no persistent leaf candidate state and no response
coefficients.

Result: structurally suitable for later item-specific review; not implementation
ready because response functions, domains, empirical evidence and parameter
values remain absent.

## OBT review

The OBT contract uses `P`, `B_x`, and `B_n` as candidate activity inventories
`[Bq m^-2]`. It explicitly separates precursor-to-`B_x` transfer from other
precursor loss:

```text
J_P_to_Bx = k_PB P
J_P_other = k_P_other P
k_P = k_PB + k_P_other
```

This removes the conservation ambiguity in treating `k_P P` as a sink while
using `k_PB P` as a separate source. Internal transfers cancel exactly in the
composite `P + B_x + B_n` ledger. `B_total = B_x + B_n` is a diagnostic, not a
fourth storage state.

No rate or response-function value is admitted. Aggregate-only OBT observations
are explicitly insufficient to validate the component pools.

Result: conservation contract is coherent and auditable; biological
implementation remains held pending data, identifiability, numerical tests and
independent review.

## Root review

The root contract uses

```text
M_s,i = theta_i Delta_z_i C_w,i
J_root,i = q_w,i C_w,i
```

with explicit layer geometry and water basis. `q_w,i` is owned by empirical
forcing or a separately reviewed water model. The root boundary cannot generate
water flux, infer hydrology, assume uniform layer uptake, or convert a scalar
`s^-1` rate into `m s^-1`.

The soil sink and TFWT source are the same internal transfer identity. Any
future implementation remains a numerical-coupling change and therefore still
requires P7.5/P7.5B rereview.

Result: dimensional and ownership boundary is coherent; implementation remains
held.

## Validation envelope

The JSON Schema requires:

- explicit candidate item and `v3_frozen_baseline` comparator;
- empirical versus synthetic case classification;
- replicate identifier;
- timezone/offset, interval semantics and alignment rule;
- variable role, unit and provenance;
- pre-registered metrics.

Empirical validation cases cannot contain `SOFTWARE_EXPECTATION` variables.
Synthetic cases remain software evidence only.

## Runtime isolation

V4-1 is required to remain outside `src/`, current runtime serialization,
production parameter activation, and P7.5/P7.5B numerical semantics. The stage
scope test freezes this boundary against the V4-1 content tip.

## Review status

The document review finds the contracts internally coherent subject to the
repository tests and exact-head CI. Passing those checks will close V4-1 as a
**control-plane contract review only**. It will not satisfy any candidate
model's independent implementation review.

```ini
V4_1_STATUS = CONTRACTS_DEFINED_PENDING_EXACT_HEAD_CI
CONTROL_PLANE_ONLY = TRUE
LEAF_IMPLEMENTATION_AUTHORIZED = FALSE
OBT_IMPLEMENTATION_AUTHORIZED = FALSE
ROOT_IMPLEMENTATION_AUTHORIZED = FALSE
PRODUCTION_RUNTIME_CHANGED = FALSE
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
CANDIDATE_PARAMETER_VALUES_ADMITTED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```
