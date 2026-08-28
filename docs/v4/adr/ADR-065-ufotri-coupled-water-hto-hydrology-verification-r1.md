# ADR-065 — UFOTRI coupled water/HTO hydrology verification R1

## Status

`PROPOSED_C2_CANDIDATE`

Stage: `UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION_R1`

## Context

C1 reconstructed the recoverable KfK 4605 Section 2.2.3 Eq. (33)-(37) hydrologic mechanism as an opt-in closure. The frozen `soil_v4` core still owns water/HTO inventory and conservation, while `root_v4` owns the explicit Eq. (37) root-water sink and the existing V4 integrator owns the selected soil→root→TFWT→OBT operator split.

C2 must qualify those already-selected boundaries dynamically. It must not create a second soil solver, a second hydrology solver, or a production hydraulic parameterization.

## Decision

C2 is a qualification-only stage with `NO_EXISTING_SOURCE_CHANGE`.

For every numerical interval:

1. evaluate the C1 `Theta -> (Psi_m, K)` closure from the **current** three-layer soil state;
2. generate signed L1↔L2 and L2↔L3 water/HTO fluxes;
3. project those fluxes into a base `ThreeLayerSoilForcing` whose internal and root slots are initially zero;
4. pass that projected forcing plus explicit `root_v4` water-uptake forcing to the existing `V4SoilRootTFWTOBTIntegrator`;
5. audit the frozen soil ledger, root-transfer identity and coupled HTO ledger.

No new production runtime path is activated.

## Controlled constitutive inputs

All C2 hydraulic relations are synthetic, explicit and provenance-bearing. They exist only to exercise the recovered mechanism.

Three controlled profiles are used:

- gravity profile: equal matric head with theta-dependent conductivity, giving positive/downward gravity flow while making step-to-step recomputation observable;
- capillary profile: matric head increases with water content, producing a sufficiently positive downward gradient to exercise negative/upward signed transport;
- dry/wet limiting profile: zero conductivity at the dry endpoint and positive conductivity at the wet endpoint.

These profiles are not UFOTRI production parameters and are not empirical soil calibration.

## Required qualification

### Conservation

The existing ledger must close for:

- per-step soil water;
- per-step soil HTO;
- per-step coupled soil+TFWT+OBT HTO;
- cumulative water over a multi-step trajectory;
- cumulative coupled HTO over the same trajectory;
- root water/HTO transfer identity.

### Signed transport

C2 must demonstrate both:

- `q > 0` and `J_HTO > 0` for downward gravity transport;
- `q < 0` and `J_HTO < 0` for upward capillary-direction transport.

The upward sign must persist across a multi-step dynamically recomputed sequence, not only a single algebraic probe.

### Boundary and root coupling

The qualification explicitly exercises non-zero lower-boundary water/HTO loss and non-zero root uptake. Root uptake remains planned by `root_v4` from the interval-start soil state and is applied exactly once to soil and once as endpoint TFWT gain under `PRESERVE_V3_POST_OBT_ROOT_GAIN`.

### Dry/wet limits

A dry endpoint with `K=0` must give zero internal water flow. A wet equal-head state with positive `K` must give positive gravity drainage.

### Determinism and restart

A repeated run must be exactly deterministic. JSON round-trip restart at an aligned interval boundary must reproduce the uninterrupted result.

### Timestep refinement

The same 4-hour coupled synthetic case is evaluated at `3600`, `1800`, `900`, `450` and `225 s`. The `225 s` trajectory is the numerical comparison reference only. The distance to that reference must decrease from coarse to fine within a small monotonicity tolerance. This is numerical qualification, not a claim that `225 s` is physically correct.

## Consequences

If exact-head CI passes, C2 closes the required controlled numerical qualification of Phase C. This allows Phase C to be marked `COMPLETE` for recoverable manual-based mechanism plus software/numerical closure.

The unavailable original UFOTRI constitutive curves and exact original discretization remain source boundaries; their absence is not converted into invented parameters.

## Explicit non-claims

- `PRODUCTION_HYDROLOGY_READY=FALSE`
- `PRODUCTION_HYDRAULIC_PARAMETERS=FALSE`
- `CALIBRATION=FALSE`
- `EMPIRICAL_VALIDATION=FALSE`
- `PHYSICAL_ACCURACY_CLAIM=FALSE`
- `ORIGINAL_CONSTITUTIVE_CURVES_RECOVERED=FALSE`
- `ORIGINAL_NUMERICAL_DISCRETIZATION_RECOVERED=FALSE`
- `REAL_CTEAS_ATMOS_BINDING=FALSE`
- `UFOTRI_ORIGINAL_EXECUTABLE_EQUIVALENCE=FALSE`

## Next stage if complete

`UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`
