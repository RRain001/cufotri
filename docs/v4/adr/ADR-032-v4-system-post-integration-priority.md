# ADR-032: V4 system priority after soil-root-TFWT-OBT integration

Status: Proposed pending exact-head review gate

## Decision context

The opt-in V4 path now contains an implemented and machine-gated three-layer soil -> explicit root-water-flux HTO transfer -> TFWT -> OBT integration seam. This invalidates earlier planning assumptions that treated three-layer soil and layered root transfer as not yet implemented, while leaving the frozen V3 default profile unchanged.

The project north star remains the complete chain from atmospheric forcing to dose. The next step must therefore be chosen by missing system connectivity and evidence readiness, not by local subsystem development momentum.

## Decision

Recommend `V4_SYSTEM_REPLAY_INPUT_ADAPTER_DECISION_R1` as the next control-plane stage after this review is accepted.

This is a decision stage, not adapter implementation. It must freeze how the already-frozen Atmos exchange record and separately sourced root/biological forcing are composed into the opt-in V4 pathway.

The next stage must explicitly decide:

1. exact mapping of total HTO surface deposition flux to the three-layer soil surface boundary;
2. how air HTO reaches the existing baseline leaf-exchange path without activating dynamic Leaf R5;
3. whether baseline leaf exchange is composed outside or inside the opt-in V4 orchestration seam;
4. explicit ownership and provenance for root `q_w,i`, which remains non-Atmos external forcing;
5. explicit ownership and provenance for biological forcing;
6. half-open UTC interval alignment, spatial support, common area basis, and fail-closed missing-data rules;
7. replay/synthetic execution semantics distinct from real CTEAS-Atmos producer binding.

No meteorological coforcing may be silently transformed into new stomatal, transpiration, hydrology, or OBT response physics.

## Alternatives

`FOOD_INTAKE_DOSE_V4_ADAPTER_DECISION` is deferred to second priority because endpoint modules already exist and upstream environmental forcing remains disconnected from the new V4 core.

Leaf R5 is held because its R4 checkpoint lacks the admissible empirical packet needed for dynamic response-law implementation. OBT redesign is held pending matched TFWT/OBT evidence. Full soil hydrology and plant-water dynamics are held because they are physical expansions beyond the currently sufficient explicit-flux architecture. Real CTEAS-Atmos binding remains blocked until the producer exposes an unambiguous surface deposition flux product meeting the frozen exchange contract.

## Non-authorization

This ADR does not authorize adapter implementation, new solver physics, parameter activation, calibration, real Atmos coupling, Leaf R5, food/intake/dose integration, full hydrology, or plant-water dynamics. Exact-head CI must pass before this review can be accepted.
