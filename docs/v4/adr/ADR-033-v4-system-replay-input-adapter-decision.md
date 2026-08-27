# ADR-033: V4 replay-input system orchestration decision

## Status

`PASS_SYSTEM_REPLAY_ORCHESTRATION_DECISION`

The architecture decision passed its first exact-head protected/remediation gate. A final closure exact-head gate and no-drift merge are still required before implementation authorization becomes effective.

## Context

The opt-in V4 path now has a machine-gated three-layer soil -> layered root -> TFWT -> OBT core, while the atmospheric exchange contract is separately frozen. The next gap is therefore not another leaf, root, soil, or OBT physics redesign. It is the input and orchestration boundary that connects replay/Atmos records to the integrated V4 core without changing the frozen numerical semantics.

A direct field-only adapter is insufficient for two concrete software reasons. First, `AtmosphericHTOForcing.to_soil_forcing()` currently targets the V3 one-layer `SoilForcing`, not `ThreeLayerSoilForcing`. Second, `V4SoilRootTFWTOBTIntegrator` has no leaf-exchange input. A complete V4 replay path must still preserve the established ordering in which same-interval leaf exchange is visible to OBT, while same-interval root gain is not.

## Decision

Select an **opt-in replay-input system orchestrator** as the architecture for the next implementation stage. Do not modify or replace the current four-module V4 integrator; freeze it as the reference baseline for equivalence testing.

The future orchestrator will compose existing component solvers and fail-closed input mappings. It may not alter component solver equations, the V3 default pipeline, or the selected `PRESERVE_V3_POST_OBT_ROOT_GAIN` operator split.

The selected interval order is:

1. validate all records for the common UTC half-open interval `[t_n, t_n+1)`;
2. map total HTO surface-deposition flux only to the L1 atmospheric-deposition boundary of the three-layer soil forcing;
3. compute the existing baseline signed leaf-exchange flux from the atmospheric/replay record plus explicit resistance/equilibrium inputs;
4. advance TFWT with leaf exchange to the leaf-updated intermediate inventory;
5. advance OBT using that leaf-updated TFWT inventory;
6. plan root transfer from the interval-start three-layer soil state `S_n`;
7. advance the three-layer soil with that exact root plan applied once;
8. reconcile endpoint TFWT as leaf-updated TFWT minus OBT loss plus root gain.

This preserves the previously selected semantics: OBT sees same-interval leaf exchange; OBT does not see same-interval root gain; root reads `S_n`; root gain enters endpoint TFWT after OBT.

## Input ownership

Atmos/replay owns air HTO concentration, total HTO surface-deposition flux, temperature, relative humidity, wind speed, precipitation rate, interval identity, spatial support, and provenance.

Atmos/replay does **not** own root layer water uptake `q_w,i`, inter-layer soil transport, lower-boundary loss, surface re-emission, biological forcing, leaf resistance state, or leaf equilibrium-air concentration. Root `q_w,i` must have independent provenance and must not be inferred from temperature, humidity, wind, or precipitation by the replay adapter.

Precipitation is meteorological co-forcing only. It must not be silently converted into soil water input. Soil hydrological/transport boundary fluxes remain explicit external forcing until a separately authorized simple-hydrology stage exists.

## Why the existing four-module integrator remains frozen

The existing `V4SoilRootTFWTOBTIntegrator` already passes conservation, deterministic repeat, restart, and operator-split gates. Reopening it merely to insert a leaf step would mix a new system boundary with already-closed internal integration semantics.

A higher-level opt-in orchestrator is therefore preferred. The strongest compatibility gate is zero-leaf equivalence: with identical state, soil/root/biological forcing and parameters, and exactly zero leaf exchange, the future orchestrator must reproduce the frozen four-module integrator endpoint state and ledgers within the existing closure tolerance.

## Timestamp semantics

The current TFWT solver advances its returned state timestamp to the interval end. The OBT solver reads TFWT inventory/concentration but does not use the TFWT timestamp to advance its own state. This is an existing numerical composition convention, not permission to forge or reset timestamps.

The future orchestration layer must therefore keep the common forcing interval explicit and must not mutate timestamps merely to satisfy an API. Start forcing must match the composite state timestamp; endpoint state must be `t_n+1`; silent resampling or nearest-time substitution remains forbidden.

## First exact-head gate evidence

Decision head `45298061c58cbf8f558f4b25de02ca6288dcb104` passed:

- Protected Gate run `33030199770`: SUCCESS;
- Remediation run `33030199769`: SUCCESS;
- portable suite: `1226 passed, 1 skipped, 57 deselected`;
- frozen-boundary suite: `295 passed`;
- sensitivity: `PASS_SOFTWARE_SCREENING`;
- operator split: `PASS_SELECTION`;
- soil-root-TFWT-OBT integration: `PASS_INTEGRATION`.

## Authorization boundary

This closure still does not authorize implementation on the current branch. It does not authorize dynamic Leaf R5, food/intake/dose V4 integration, full Richards/Darcy hydrology, plant-water dynamics, parameter activation, calibration, real CTEAS-Atmos binding, or any empirical/physical-accuracy claim.

Real CTEAS-Atmos binding remains blocked until an identifiable true surface-deposition-flux product satisfies the already frozen exchange contract.

If the closure exact head passes both protected and remediation CI and the PR merges with expected-head and no tree drift, authorization becomes effective for a **new isolated branch**:

`V4_SYSTEM_REPLAY_INPUT_ORCHESTRATION_IMPLEMENTATION_R1`
