# V4 state normalization R1 report

## Outcome

`PASS_STATE_SEMANTICS_NORMALIZED_AWAITING_EXACT_HEAD_GATE`

This stage normalizes project state only. It does not change any production source, solver equation, numerical coupling, physical parameter, production manifest, runtime parameter import, calibration path or real CTEAS-Atmos binding.

## Why normalization was required

ADR-045 established `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=TRUE` with a narrow controlled-path meaning: the Eq.39 root-water construction is explicit and complete when required caller inputs are supplied. Later production-case governance used the same token as `FALSE` to mean that a real production case does not yet have all case-specific sources bound.

Both local statements can be true about different readiness layers, but the shared token is unsuitable as a current-state authority.

The normalized current authority therefore uses two flags:

```text
ROOT_Q_W_CONTROLLED_CONSTRUCTION_PATH_RESOLVED = TRUE
ROOT_Q_W_PRODUCTION_CASE_INPUT_READY = FALSE
```

Historical files are not rewritten.

## Development route after scope clarification

Real production inputs are not required during the current development phase, and the real CTEAS-Atmos model is still under separate development. Both are therefore deferred rather than treated as current internal blockers.

The project is now in:

`INTERNAL_V4_DEVELOPMENT_COMPLETION`

The remaining mandatory internal sequence is only:

1. `V4_DEVELOPMENT_COMPLETENESS_REVIEW_R1`
2. `V4_DEVELOPMENT_BASELINE_RC1`

The first stage is a no-new-physics completeness review. It must determine whether any mandatory internal blocker remains in the already selected V4 controlled architecture. If none exists, the second stage performs the final development-baseline regression/RC freeze.

## Existing controlled baseline retained

The normalized state preserves the already selected and integrated baseline:

- synthetic/replay atmospheric forcing for internal development;
- three-layer soil state at 0–5, 5–15 and 15–30 cm;
- signed inter-layer transport and conservation ledger;
- UFOTRI Eq.39 controlled total root-water uptake construction;
- 20/40/40 root-layer distribution;
- baseline leaf resistance pathway;
- TFWT;
- reduced UFOTRI OBT baseline;
- `PRESERVE_V3_POST_OBT_ROOT_GAIN` operator split;
- `KEEP_HARVEST_EVENT` endpoint boundary;
- food, intake and dose endpoint chain.

## Non-blocking extensions

The following are not mandatory for internal V4 completion under the current selected route:

- Leaf R5 dynamic stomatal implementation;
- full Richards/Darcy hydrology;
- multi-pool OBT;
- UFOTRI short-term 3 h delay;
- Penman Eq.38 aerodynamic term.

They remain future evidence-driven extensions or explicit holds. Their absence must not be interpreted as a reason to manufacture new implementation stages before the development-completeness review.

## Deferred work

Production-case declaration Issue #52 remains open as a future controlled intake channel but is parked for the later production phase. No R6 is authorized now.

Real production input binding, real CTEAS-Atmos binding, calibration, empirical validation, physical-accuracy qualification and full production readiness all remain outside the present internal-development completion target.

## Next stage

`V4_DEVELOPMENT_COMPLETENESS_REVIEW_R1`

No solver or physics change is pre-authorized by this transition.
