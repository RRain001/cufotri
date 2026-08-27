# V4 system post-integration review R1

## Status

`REVIEW_COMPLETE_AWAITING_EXACT_HEAD_GATE`

This review is control-plane only. It is performed after merge of the opt-in three-layer soil -> root -> TFWT -> OBT integration and does not change any solver, numerical coupling, runtime parameter, or default V3 pathway.

## What changed since the earlier roadmap reset

Two assumptions in the earlier system documents are now historical rather than current for the opt-in V4 path:

1. three-layer soil is no longer merely a candidate; the minimal three-layer inventory core is implemented and integrated;
2. layered root transfer is no longer only a redesign concept; explicit externally forced `q_w,i` transfer is implemented and integrated with the frozen post-OBT root-gain operator split.

These statements do not apply to the frozen V3 default profile, which remains unchanged.

## Current system chain

| Subsystem | Current V4 status | Boundary |
|---|---|---|
| Atmos exchange | frozen contract; replay/synthetic usable | real producer binding blocked because a true surface deposition flux product is still unconfirmed |
| Leaf exchange | existing baseline solver available | dynamic Leaf R5 remains HOLD; not included in the new soil-root-TFWT-OBT integrator |
| Soil | three-layer opt-in inventory core implemented and integrated | explicit flux forcing only; no Richards/Darcy hydrology |
| Root | three-layer explicit water-flux HTO transfer implemented and integrated | `q_w,i` remains separately supplied forcing; no internal transpiration/hydrology generation |
| TFWT | existing fixed-water-basis storage integrated | no plant-water dynamics |
| OBT | existing reduced first-order solver integrated | no organ-specific growth redesign |
| Food | existing endpoint module | not yet connected to the V4 integration seam |
| Intake | existing endpoint module | not yet connected to the V4 integration seam |
| Dose | existing endpoint module | not yet connected to the V4 integration seam |

## Priority decision

The next useful gap is system connectivity, not additional subsystem physics.

The recommended next stage is `V4_SYSTEM_REPLAY_INPUT_ADAPTER_DECISION_R1`, with control-plane/interface-decision scope only. It should decide how a frozen Atmos exchange record and separately sourced non-Atmos forcings enter the V4 pathway before any adapter implementation is authorized.

The decision must keep these ownership boundaries explicit:

- Atmos/replay may provide air HTO, surface deposition, meteorological coforcing, interval/spatial identity, and provenance;
- root `q_w,i` remains separately sourced and separately provenanced and must not be silently inferred from Atmos meteorology;
- biological forcing remains explicitly sourced and interval aligned;
- the current baseline leaf-exchange solver may be used to close system connectivity, but temperature/humidity/wind must not be converted into an unvalidated dynamic stomatal law;
- surface deposition may enter the three-layer soil surface boundary only with exact rate/area/time semantics; accumulated activity or puff-ledger loss may not be relabeled as surface flux;
- replay/synthetic execution remains distinct from live CTEAS-Atmos production binding.

Whether leaf exchange should be composed outside the existing V4 integrator or added as an opt-in orchestration step is a decision for that next control-plane stage. No leaf physics change is implied.

## Deferred tracks

`FOOD_INTAKE_DOSE_V4_ADAPTER_DECISION` is second priority. Existing endpoint modules already exist, and current screening shows important endpoint quantities are primarily explicit scenario/geometry scaling. It should follow the upstream input-boundary decision so that downstream integration is exercised against a coherent environmental pathway.

Leaf R5 remains HOLD at R4; OBT redesign remains HOLD pending matched time-resolved evidence; full hydrology and plant-water dynamics remain HOLD; real CTEAS-Atmos binding remains BLOCKED by the producer surface-flux product issue.

## Non-claims

This review does not convert synthetic screening into empirical uncertainty, does not validate physical parameters, and does not establish physical accuracy. `ACTIVE_PARAMETERS=0`, calibration remains false, and no next implementation stage is authorized yet.
