# V4-1 Data and State Contracts — Technical Review Closure

## Scope

V4-1 is the control-plane stage authorized by P7.8C. It freezes symbolic
contracts for leaf exchange, OBT formation, root water-flux uptake, provenance,
validation cases, state ownership and restart behavior. It does not implement
candidate physics.

Entry baseline:

```text
MAIN = 175c5d7ed7fbec916485aa44c0ae733d330b661f
P7_8C = PASS_CONTRACT_PREPARATION_AUTHORIZATION
REVIEWED_CONTENT_HEAD = 27ddffeaa2d88aac34f197ce2a4bcf3a67f42ec6
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

Result: the equation/unit, ownership, restart, validation-envelope and
fail-closed boundaries are defined. Leaf implementation is not authorized;
response functions, domains, matched empirical evidence, parameter values and
an independent item-specific review remain open.

## OBT review

The OBT contract uses `P`, `B_x`, and `B_n` as candidate activity inventories
`[Bq m^-2]`. An intermediate V4-1 draft over-specified the unresolved precursor
source as a product of day/night, photosynthetic and temperature response
functions and introduced `k_P_other` as an extra symbol. Technical review
rejected that overreach because P7.8B-2 selected only a generic
`u_P(T,A,d,s,T_leaf,...)` source boundary and the existing candidate rates.

The final contract keeps the source functional form unresolved and retains the
selected `k_P` and `k_PB` notation. Conservation is made explicit without
adding a biological parameter:

```text
J_P_to_Bx = k_PB P
J_P_other = (k_P - k_PB) P
0 <= k_PB <= k_P
```

with

```text
dP/dt   = u_P - k_P P
dB_x/dt = J_P_to_Bx - J_Bx_to_Bn - J_Bx_other
dB_n/dt = J_Bx_to_Bn - J_Bn_other
```

Internal transfers therefore cancel exactly in the composite
`P + B_x + B_n` ledger. `B_total = B_x + B_n` is a diagnostic, not a fourth
storage state.

No rate, response-function value, or response-function composition is admitted.
Aggregate-only OBT observations are explicitly insufficient to validate the
component pools.

Result: the conservation and ownership boundary is coherent and auditable;
biological implementation remains held pending source-function selection,
matched data, identifiability, numerical tests and independent item review.

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

Result: dimensional and ownership boundaries are coherent; implementation
remains held.

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

V4-1 remains outside `src/`, current runtime serialization, production parameter
activation, and P7.5/P7.5B numerical semantics. The stage-scope test freezes the
control-plane file set. No production runtime file was changed.

## CI and review evidence

Final reviewed content head:

`27ddffeaa2d88aac34f197ce2a4bcf3a67f42ec6`

Exact-head GitHub Actions:

```text
V3 Remediation CI 32923288035 = PASS
V3 Protected Integration Gate 32923288127 = PASS
portable suite = 1036 passed / 1 skipped / 57 deselected
explicit current/frozen/V4-1 invariants = 115 passed
```

A prior integration run (`32923036669`) found one stage-scope governance-test
error: the expected changed-file set omitted the V4-1 test file even though the
frozen content tip already contained it. The other tests in that run reported
`1035 passed, 1 skipped, 57 deselected`. The expected set was corrected at
`27ddffeaa2d88aac34f197ce2a4bcf3a67f42ec6`; no contract or runtime semantics
were weakened to obtain the PASS.

## Closure

V4-1 is closed as a **control-plane contract review**. This closure is not an
independent implementation review, does not establish physical validity, and
does not authorize implementation of leaf, OBT or root candidate physics.

The next roadmap item is the leaf dynamic stomatal response, but it must enter
an item-specific equation/domain/data/review/authorization gate before any
solver implementation.

```ini
V4_1_STATUS = PASS_CONTROL_PLANE_CONTRACT_REVIEW
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
