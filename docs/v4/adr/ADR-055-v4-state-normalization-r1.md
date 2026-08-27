# ADR-055: V4 state normalization R1

## Status

Accepted for governance normalization, subject to exact-head CI and no-drift merge closure.

## Context

The controlled V4 software chain has been connected end to end under synthetic/replay forcing, while real production inputs and real CTEAS-Atmos binding remain intentionally deferred. Subsequent production-input governance stages correctly stayed fail-closed, but they reused the legacy token `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED` with a different meaning from ADR-045.

ADR-045 defines `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=TRUE` as: the controlled V4 construction path for root water uptake is explicit and complete when the caller supplies the required meteorology, LAI, soil-water state and physical constants. R5 later records the same token as `FALSE` to mean that a real production case does not yet have all case-specific input sources bound. These statements refer to different readiness layers and must not share one current-state flag.

Historical ADR, report and governance files remain immutable stage snapshots. They are not rewritten by this normalization.

## Decision

Create `docs/v4/governance/v4_current_system_state.yaml` as the single current-state authority for V4 development status.

Split the ambiguous root-water state into two explicit flags:

- `root_q_w_controlled_construction_path_resolved: true`
- `root_q_w_production_case_input_ready: false`

The legacy token `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED` is deprecated as a current-state authority. Historical occurrences retain their original stage-local meaning.

The project phase is normalized to `INTERNAL_V4_DEVELOPMENT_COMPLETION`. Real production-case input binding and real CTEAS-Atmos binding are deferred external/deployment concerns and are not current internal-development blockers.

The remaining mandatory internal-development sequence is:

1. `V4_DEVELOPMENT_COMPLETENESS_REVIEW_R1`
2. `V4_DEVELOPMENT_BASELINE_RC1`

No additional physics subsystem is mandatory by default. Leaf R5, full Richards/Darcy hydrology, multi-pool OBT, UFOTRI 3 h delay and Eq.38 aerodynamic-term activation remain evidence-driven optional extensions or holds, not completion blockers.

## Current normalized interpretation

The following are true for the selected controlled V4 baseline:

- software chain connected under controlled synthetic/replay forcing;
- three-layer soil architecture selected and implemented;
- UFOTRI Eq.39 controlled root-water construction path implemented;
- 20/40/40 controlled root-layer profile implemented;
- baseline leaf resistance pathway connected;
- TFWT and reduced UFOTRI OBT baseline connected;
- food, intake and dose endpoint connected;
- deterministic/restart/conservation software gates exist and have passed in prior certified stages.

The following remain false or deferred:

- full-model production readiness;
- real production input packet readiness;
- real CTEAS-Atmos binding;
- empirical validation;
- physical-accuracy claim;
- calibration;
- active production parameters.

## Non-decisions

This normalization changes no `src/` file, solver equation, numerical coupling, production manifest, runtime parameter import, calibration path, Atmos interface or physical parameter value. It does not authorize R6 from the production-case declaration track. Issue #52 remains a parked future intake channel until production-case work is resumed.

## Next stage

`V4_DEVELOPMENT_COMPLETENESS_REVIEW_R1`

That review must determine whether any mandatory internal software/physics blocker remains after excluding deferred production inputs and deferred real Atmos binding. It must not manufacture new physics merely to continue stage numbering.
