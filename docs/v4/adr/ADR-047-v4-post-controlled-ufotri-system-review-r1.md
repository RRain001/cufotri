# ADR-047: Post-controlled-UFOTRI system review R1

## Status

Accepted as a control-plane review decision, pending exact-head CI and clean merge.

## Context

PR #43 closed the synthetic/replay numerical chain using the controlled UFOTRI profiles already adopted in V4. The chain now exercises:

`replay atmosphere + explicit net radiation -> UFOTRI Eq.39 total root uptake -> UFOTRI 20/40/40 root distribution -> leaf/three-layer soil/root -> TFWT -> UFOTRI reduced OBT baseline -> harvest -> intake -> dose`.

The clean PR #43 merge is `589d23a81fb27509fb8591dac8695971dc14905f`; its merge tree is `b75843f57bb2fdb308083f76d6267f68933133a1`, with parent1 `2814579b6bc345d31cabf36f7712ede78292ce46` and parent2 `64ea75593b34f864cc4c96f36bc8561ebaac5279`. Head and merge trees are identical and head-to-merge has no changed files, so `MERGE_TREE_DRIFT=FALSE`.

The earlier post-endpoint ranking is now stale in two material respects. OBT evidence acquisition is no longer the selected route because the project has explicitly adopted the UFOTRI reduced OBT baseline rather than waiting for external matched-data acquisition. Root `q_w` construction is also no longer unresolved because the controlled Eq.39 total-uptake boundary and UFOTRI 20/40/40 layer profile are implemented and numerically integrated.

## Decision

Do not admit another physics subsystem immediately. Select `V4_PRODUCTION_INPUT_READINESS_AUDIT_R1` as the next stage.

That audit will enumerate the inputs required to move the currently connected synthetic/replay chain toward a production case and classify every input as one of:

- controlled UFOTRI baseline/profile;
- physical constant;
- explicit external scenario input;
- real upstream data prerequisite;
- unresolved/synthetic-only.

The audit must cover at least atmospheric HTO concentration/deposition and meteorology, Eq.39 net radiation/LAI/soil-water state and water thresholds, the explicit leaf-resistance boundary, harvest/food basis, consumption, dose coefficient, timestamps, units and provenance.

## Remaining blocker ranking

1. `V4_PRODUCTION_INPUT_READINESS_AUDIT_R1` — advance. This is the highest-value control-plane step because software connectivity is already closed and the next question is which inputs prevent a truthful production run.
2. `REAL_CTEAS_ATMOS_BINDING` — hold as an external prerequisite. The production exchange contract exists, but a true surface-deposition-flux product remains unconfirmed. No real binding is authorized.
3. `LEAF_R5_DYNAMIC_STOMATAL_IMPLEMENTATION` — hold at the existing R4 evidence checkpoint. The current baseline resistance pathway is runnable and system-connected; no evidence checkpoint has been executed that justifies R5.
4. `FULL_SOIL_HYDROLOGY_OR_PLANT_WATER_DYNAMICS` — hold. It is not required to preserve the selected controlled Eq.39 root-uptake construction and must not be added merely for completeness.
5. `OBT_MULTI_POOL_OR_EXTERNAL_MATCHED_EVIDENCE_TRACK` — hold/superseded for the controlled baseline route. The reduced UFOTRI `kf/kr` profile remains the selected runtime baseline; no multi-pool implementation or external-email acquisition is authorized.

## Interpretation of current readiness

`SOFTWARE_CHAIN_CONNECTED_WITH_CONTROLLED_UFOTRI_PROFILES=TRUE` is a software/numerical statement. `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=TRUE` means the controlled V4 construction path is explicit when its required caller inputs are supplied.

Neither flag establishes real CTEAS-Atmos coupling, empirical validation, calibration, complete production-input availability, or physical-accuracy validation. Therefore `FULL_MODEL_PRODUCTION_READY=FALSE` remains.

## Non-decisions

This review does not change solver equations, numerical coupling, V3 defaults, UFOTRI parameter values, operator ordering, Leaf R5, full hydrology, the Eq.38 empirical aerodynamic term, the UFOTRI short-term 3 h delay, OBT multi-pool runtime, calibration, empirical validation, or real CTEAS-Atmos binding.
