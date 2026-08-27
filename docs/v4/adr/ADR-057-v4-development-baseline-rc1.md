# ADR-057: V4 development baseline RC1

## Status

Accepted as the final internal V4 development-baseline freeze candidate, subject to exact-head CI and no-drift merge closure.

## Context

`V4_DEVELOPMENT_COMPLETENESS_REVIEW_R1` concluded `PASS_NO_MANDATORY_INTERNAL_BLOCKERS` with `MANDATORY_INTERNAL_BLOCKER_COUNT=0`. The selected V4 software chain is connected under controlled UFOTRI profiles and synthetic/replay forcing. Real production inputs, real CTEAS-Atmos binding, calibration, empirical validation and physical-accuracy qualification are explicitly outside the current development phase.

The remaining mandatory internal stage is therefore a release-candidate freeze, not another physics-development cycle.

## Decision

Create `V4_DEVELOPMENT_BASELINE_RC1` as a combined regression and baseline-composition gate.

RC1 freezes the already selected internal baseline:

- synthetic/replay atmospheric input mode for internal development;
- three-layer soil state: L1 0–5 cm, L2 5–15 cm, L3 15–30 cm;
- root identity `J_root,i = q_w,i C_w,i`;
- UFOTRI Eq.39 equilibrium-radiation controlled total root-water uptake;
- UFOTRI 20/40/40 root-layer distribution;
- baseline leaf-resistance exchange path;
- connected TFWT solver;
- reduced UFOTRI `k_f/k_r` OBT baseline;
- `PRESERVE_V3_POST_OBT_ROOT_GAIN` operator split;
- `KEEP_HARVEST_EVENT` terminal harvest boundary;
- connected food → intake → dose endpoint.

No new solver equation, numerical coupling, production parameter, production manifest, production input source, Atmos binding or physics subsystem is authorized in RC1.

## Machine composition proof

`scripts/v4/run_development_baseline_rc1.py` must execute and require PASS from the existing machine runners for:

1. controlled UFOTRI full-chain end-to-end integration;
2. V4 software sensitivity screening;
3. root operator-split selection;
4. soil-root-TFWT-OBT integration;
5. replay-input orchestration;
6. food-intake-dose endpoint integration.

The aggregate status must be:

`PASS_V4_DEVELOPMENT_BASELINE_RC1_MACHINE_COMPOSITION`

The repository Protected Integration Gate remains the authoritative combined regression gate because it executes the portable suite, explicit frozen/current-boundary suite and existing machine gates on the exact candidate head.

## Completion semantics

After exact-head Remediation + Protected CI pass, merge must use `expected_head_sha`, followed by parent/tree/head-to-merge/main no-drift verification.

Only after a no-drift merge may the state be interpreted as:

`V4_SOFTWARE_DEVELOPMENT_BASELINE_COMPLETE`

and the lightweight release-candidate tag `v4-development-baseline-rc1` may be created at that verified merge commit.

## Explicit non-claims

RC1 does not establish:

- production readiness;
- production input packet readiness;
- real CTEAS-Atmos binding;
- empirical validation;
- calibration;
- physical accuracy;
- Leaf R5;
- full Richards/Darcy hydrology;
- multi-pool OBT;
- UFOTRI short-term ~3 h delay;
- Penman Eq.38 aerodynamic-term activation.

Those remain future separately authorized work.
