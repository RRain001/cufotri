# ADR-034: V4 replay-input system orchestration implementation R1

## Status

`PASS_IMPLEMENTATION_EXACT_HEAD_AWAITING_CLOSURE_GATE`

## Context

ADR-033 selected a higher-level opt-in replay-input system orchestrator because a field-only adapter cannot complete the V4 chain. The frozen atmospheric adapter targets V3 one-layer soil, while the frozen four-module V4 integrator contains no leaf-exchange step. The selected numerical semantics require same-interval leaf exchange to be visible to OBT while same-interval root gain remains post-OBT.

## Implementation decision

Add a new isolated `replay_input_orchestration` module under `cteas_ufotri.v4_integration`. The existing `V4SoilRootTFWTOBTIntegrator` remains unchanged and is used as the compatibility reference.

The new layer composes existing solvers only. It does not alter equations in leaf exchange, TFWT, OBT, root, or three-layer soil.

For each explicit UTC half-open replay interval `[t_n, t_n+1)` it performs:

1. fail-closed validation of the atmospheric record, soil external forcing, root forcing, biological forcing, resistance/equilibrium inputs, interval, spatial support, area basis, and per-domain provenance;
2. mapping of the atmospheric total HTO surface-deposition flux to `ThreeLayerSoilForcing.surface_deposition_flux_bq_m2_s` only;
3. existing baseline signed leaf exchange from the atmospheric record;
4. TFWT leaf update;
5. OBT update from the leaf-updated TFWT inventory;
6. root transfer planning from the interval-start three-layer soil state;
7. three-layer soil advance with the exact root plan applied once;
8. endpoint TFWT reconciliation as leaf-updated TFWT minus OBT transfer plus root gain.

The selected split remains `PRESERVE_V3_POST_OBT_ROOT_GAIN`.

## Input ownership and provenance

The replay envelope uses the existing atmospheric forcing provenance and root `RootWaterFluxProvenanceV4`, plus explicit orchestration-level provenance for soil external forcing, biological forcing, and leaf exchange parameters. These domains remain independent; root provenance is never copied from atmospheric provenance.

R1 accepts only identical spatial support across the replay/soil/plant domains. A mismatched spatial reference fails closed because explicit spatial reconciliation is not implemented in this stage.

Atmospheric precipitation remains meteorological co-forcing. It is not converted to infiltration, soil surface-water input, inter-layer water flux, root water flux, or any hydrological boundary.

The base three-layer soil forcing must have zero atmospheric deposition and zero root extraction slots. This prevents double ownership: atmospheric replay exclusively supplies total surface deposition, while `root_v4` exclusively supplies the root plan.

## Coupled conservation ledger

The new system balance treats leaf exchange as a signed external activity transfer. Positive values are external input from air to plant; negative values are external loss from plant to air.

The plant closure is:

`leaf_signed_transfer + root_transfer - OBT_external_loss - plant_storage_change = 0`.

The coupled soil+plant closure is:

`soil_external_input + leaf_signed_transfer - soil_nonroot_external_loss - soil_decay_loss - OBT_external_loss - coupled_storage_change = 0`.

Root transfer is internal to the coupled system and is therefore removed from the soil external-loss term before global closure is evaluated.

## Compatibility gate

The mandatory R1 compatibility gate is `ZERO_LEAF_EXCHANGE_EQUIVALENCE`.

When atmospheric HTO concentration equals the explicit leaf equilibrium-air concentration, the signed leaf flux is exactly zero. Under identical initial state, soil forcing, root forcing, biological forcing, interval, and solver parameters, the new orchestrator must reproduce the frozen `V4SoilRootTFWTOBTIntegrator` endpoint state, root plan, applied soil forcing, soil result, OBT result, and core balance residuals.

The machine harness also checks nonzero same-interval leaf influence on OBT, post-OBT root gain, deposition mapping, no precipitation-to-infiltration inference, independent root provenance, deterministic repeat, restart equivalence, plant closure, and coupled closure.

## First exact-head evidence

Implementation head `dc309089d667fbd4ca0ab5ca4498b75b02a909d1` passed both required workflows without a corrective implementation commit:

- V3 Remediation CI run `33031238565`: `SUCCESS`;
- V3 Protected Integration Gate run `33031238577`: `SUCCESS`;
- portable suite: `1245 passed, 1 skipped, 57 deselected`;
- frozen/current-boundary suite: `313 passed`;
- sensitivity machine gate: `PASS_SOFTWARE_SCREENING`;
- root operator-split gate: `PASS_SELECTION`;
- four-module soil-root-TFWT-OBT gate: `PASS_INTEGRATION`;
- replay orchestration machine gate: `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`.

The replay machine result explicitly reported all mandatory invariants true: atmospheric deposition mapped to L1 surface input, coupled and plant balances closed, deterministic repeat, precipitation not inferred as soil water, restart equivalence, post-OBT root gain, independent root provenance, same-interval leaf influence on OBT, and zero-leaf equivalence.

This evidence is software/numerical integration evidence only. It is not empirical validation and does not establish physical accuracy.

## Governance closure decision

The first exact-head implementation gate is now closed. The only permitted follow-up on this branch is a governance-only closure update recording the evidence above. The closure must not alter `src/`, the replay machine harness, workflow execution semantics, functional tests, solver equations, or runtime coupling semantics.

Merge remains unauthorized until the governance-closure exact head independently passes both Protected and Remediation workflows. The eventual merge must use `expected_head_sha` and must be followed by parent/tree no-drift verification.

## Non-authorization

This implementation does not authorize or implement:

- any change to the V3 default pipeline;
- any change to existing component solver equations;
- dynamic stomatal Leaf R5;
- food/intake/dose V4 integration;
- Richards/Darcy or hidden hydrology;
- plant-water dynamics;
- inference of root `q_w,i` from atmospheric meteorology;
- parameter activation or calibration;
- real CTEAS-Atmos binding;
- empirical validation or physical-accuracy claims.

After successful closure exact-head CI and no-drift merge, the next stage remains `SYSTEM_LEVEL_POST_ORCHESTRATION_REVIEW`; no downstream physics expansion is authorized by this closure.
