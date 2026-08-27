# ADR-032: V4 system priority after soil-root-TFWT-OBT integration

Status: Accepted after review-head machine gate; closure-head CI required before merge

## Context

The opt-in V4 path now contains an implemented and machine-gated three-layer soil -> explicit root-water-flux HTO transfer -> TFWT -> OBT integration seam. This makes earlier planning assumptions that treated three-layer soil and layered root transfer as not yet implemented historical for V4, while leaving the frozen V3 default profile unchanged.

The project north star remains the complete chain from atmospheric forcing to dose. The next step is therefore chosen by missing system connectivity and evidence readiness rather than local subsystem momentum.

## Decision

Select `V4_SYSTEM_REPLAY_INPUT_ADAPTER_DECISION_R1` as the next control-plane stage, effective only after this review is merged without drift.

This is a decision stage, not adapter implementation. It must freeze how the existing Atmos exchange record and separately sourced root/biological forcing are composed into the opt-in V4 pathway.

The next stage must decide:

1. exact mapping of total HTO surface deposition flux to the three-layer soil surface boundary;
2. how air HTO reaches the existing baseline leaf-exchange path without activating dynamic Leaf R5;
3. whether unchanged baseline leaf exchange is composed outside or inside the opt-in V4 orchestration seam;
4. explicit ownership and provenance for root `q_w,i`, which remains non-Atmos external forcing;
5. explicit ownership and provenance for biological forcing;
6. half-open UTC interval alignment, spatial support, common area basis, and fail-closed missing-data rules;
7. replay/synthetic semantics distinct from real CTEAS-Atmos producer binding.

No meteorological coforcing may be silently transformed into new stomatal, transpiration, hydrology, or OBT response physics.

## Alternatives

`FOOD_INTAKE_DOSE_V4_ADAPTER_DECISION` is deferred to second priority because endpoint modules already exist and upstream environmental forcing remains disconnected from the new V4 core.

Leaf R5 is held because R4 lacks the admissible empirical packet needed for dynamic response-law implementation. OBT redesign is held pending matched TFWT/OBT evidence. Full soil hydrology and plant-water dynamics are held because they are unsupported physical expansions beyond the current explicit-flux architecture. Real CTEAS-Atmos binding remains blocked until the producer exposes an unambiguous surface deposition flux product meeting the frozen exchange contract.

## Evidence

Review head `cbd2dafc374e22da17c197b7255444836fdc8393` passed Protected Gate `33029158798` and Remediation CI `33029158729`. Portable regression was `1220 passed, 1 skipped, 57 deselected`; frozen-boundary regression was `295 passed`; sensitivity, operator split, and soil-root-TFWT-OBT integration all remained PASS.

The governance closure head must rerun exact-head CI before merge.

## Non-authorization

This ADR does not authorize adapter implementation, solver physics changes, parameter activation, calibration, real Atmos coupling, Leaf R5, food/intake/dose integration, full hydrology, or plant-water dynamics. No empirical or physical validation claim is made.
