# ADR-042: V4 UFOTRI OBT baseline numerical integration R1

## Status

Accepted for execution.

## Context

PR #38 adopted the UFOTRI OBT daily-average parameter baseline without changing the existing OBT solver equation. The accepted profile is `kf = 0.06 %/h` and `kr = 0.3 %/h`, converted to SI, with daylight/nighttime multipliers held at `1.0/1.0` solely to preserve the directly stated daily-average value without inventing an unrecovered normalized split.

The next step on the existing V4 route is numerical integration through the already selected `soil_v4 -> root_v4 -> tfwt_v3 -> obt_v3` chain. No external evidence request is required for this route.

## Decision

Run a 24 h synthetic numerical exercise using the accepted UFOTRI OBT profile and the frozen `PRESERVE_V3_POST_OBT_ROOT_GAIN` operator split. Require conservation closure, exact deterministic repeat, restart equivalence, nonzero OBT formation, and convergence under timestep refinement against a 225 s reference.

Synthetic soil and root forcing are retained only to exercise the existing numerical coupling. They are not promoted to production inputs.

## Non-decisions

This stage does not authorize calibration, empirical validation, physical-accuracy claims, a multi-pool OBT solver, Leaf R5, production `q_w`, full hydrology, or real CTEAS-Atmos binding. It does not alter the V3 default path.

## Consequence

A passing result authorizes use of the UFOTRI OBT baseline as the controlled OBT parameter profile in subsequent V4 integration work. It does not by itself make the whole system `PHYSICS_READY` or `PRODUCTION_READY`.
