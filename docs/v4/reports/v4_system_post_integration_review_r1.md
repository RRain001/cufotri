# V4 system post-integration review R1

## Status

`PASS_SYSTEM_POST_INTEGRATION_REVIEW`

This control-plane review was performed after merge of the opt-in three-layer soil -> root -> TFWT -> OBT integration. It changes no solver, numerical coupling, runtime parameter, calibration state, or V3 default pathway.

## Updated system state

The earlier roadmap assumption that three-layer soil was only a candidate is now historical for opt-in V4. The minimal three-layer inventory core and explicit layered root-water-flux HTO transfer are implemented and integrated. The frozen V3 default profile remains unchanged.

The system still has two major connectivity gaps: the frozen Atmos/replay exchange record is not connected to the new V4 core, and the existing food/intake/dose endpoint modules are not connected to the V4 seam. Dynamic Leaf R5, OBT redesign, full hydrology, plant-water dynamics, and real CTEAS-Atmos binding remain outside the authorized scope.

## Priority result

`V4_SYSTEM_REPLAY_INPUT_ADAPTER_DECISION_R1` is selected as the next control-plane/interface decision stage, effective only after this review PR is merged without drift.

The selected stage is not adapter implementation. It must freeze the ownership and mapping of:

- Atmos/replay air HTO and total surface-deposition flux;
- separately sourced and separately provenanced root `q_w,i`;
- explicit biological forcing;
- current baseline leaf exchange without dynamic Leaf R5;
- UTC half-open intervals, spatial support, common area basis, provenance, and fail-closed missing-data behavior.

It must also decide whether the unchanged baseline leaf-exchange operation is composed outside the opt-in V4 integrator or added as an orchestration step. No temperature/humidity/wind field may be silently converted into a new stomatal, transpiration, hydrology, or OBT response law.

`FOOD_INTAKE_DOSE_V4_ADAPTER_DECISION` remains second priority and is deferred until the upstream input boundary is frozen. Leaf R5 and OBT redesign remain HOLD. Full soil hydrology and plant-water dynamics remain HOLD. Real CTEAS-Atmos binding remains BLOCKED by the unconfirmed true surface-deposition-flux producer product.

## Gate evidence

Review head `cbd2dafc374e22da17c197b7255444836fdc8393` passed:

- Protected Gate run `33029158798`: SUCCESS;
- Remediation run `33029158729`: SUCCESS;
- portable suite: `1220 passed`, `1 skipped`, `57 deselected`;
- frozen-boundary suite: `295 passed`;
- sensitivity: `PASS_SOFTWARE_SCREENING`;
- operator split: `PASS_SELECTION`;
- soil-root-TFWT-OBT integration: `PASS_INTEGRATION`.

The closure commit changes only ADR/governance/report/test assertions. Its new exact head must pass the same repository gates before Ready/merge.

## Non-authorization

This review does not authorize adapter implementation, production Atmos binding, solver changes, parameter activation, calibration, Leaf R5, food/intake/dose integration, full hydrology, or plant-water dynamics. It makes no physical-validation or physical-accuracy claim.
