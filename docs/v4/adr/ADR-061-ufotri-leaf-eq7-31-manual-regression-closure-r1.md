# ADR-061: UFOTRI leaf Eq. (7)-(31) manual regression closure R1

## Status

Proposed closure for:

`UFOTRI_LEAF_EQ7_31_MANUAL_REGRESSION_CLOSURE_R1`

## Context

A1 reconciled the recoverable KfK 4605 Section 2.2.2 leaf/atmosphere mechanism and selected source changes. A2 then implemented an opt-in `plant/leaf_ufotri_v4` compatibility path while preserving the frozen V4 RC1 and historical V2 defaults.

The replication master plan requires a separate A3 stage before Phase A can close. A3 is not an empirical validation stage and is not the Canada 1987 or ITER benchmark stage. Its purpose is to test the selected compatibility path against equations and qualitative/numerical properties directly recoverable from the available manual, without inventing unavailable original-executable regression data.

## Independent manual-regression authority

The primary oracle is `ufotri_manual.md`, KfK 4605 Section 2.2.2, including:

- Eq. (12)-(14), including `r_c = r_ST / LAI`;
- reported representative daytime resistance `4 s cm^-1`, nighttime resistance `60 s cm^-1`, and mean LAI `3 m^2 m^-2`;
- the soil-available-water exhaustion switch to nighttime resistance;
- daytime precipitation driving `r_c` toward zero while nighttime epidermal resistance remains;
- Eq. (18), `r_a = u(z) / u_*^2`;
- Eq. (21), `r_b = 2/(k u_*)`;
- Eq. (22)-(25), including `z0=0.1H`, `d=0.6H`, `FLQH=0.8H` and the 1 m area-source-height floor;
- Eq. (27)-(31), with liquid/air isotope ratio `a=1.1` in the manual;
- the manual's explicit statement that long-duration interval solutions are additive, illustrated by the constant 40-interval envelope being recoverable by adding four shifted 10-interval pulse responses.

Canada 1987 and ITER remain Phase G obligations. Their missing or case-specific inputs are not filled or inferred in A3.

## A3 finding: Eq. (23)-(24) height semantics

Independent re-reading of the literal manual equations identified one A2 fidelity defect.

For stable Eq. (23), the manual is:

`ln((z-d)/z0) + 4.7 z/L`.

For unstable Eq. (24), the logarithmic term likewise uses `(z-d)/z0`, while the Dyer-Businger function uses actual height `z` through:

`Phi_m = (1 - 15 z/L)^(-1/4)`.

The A2 implementation had passed `z-d` as one combined "effective height" into both the logarithmic term and the stability correction. This is not the literal recoverable manual equation.

A3 therefore changes only the opt-in UFOTRI compatibility implementation so that:

- `z-d` is used for the logarithmic roughness/displacement term;
- actual `z` is used for stable `4.7 z/L`;
- actual `z` is used in the unstable Dyer-Businger `Phi_m` term.

Neutral Eq. (22) is unchanged by this correction.

## Regression strategy

A3 adds independent tests that calculate expected values directly from the manual equations instead of calling the same implementation helper twice.

Required closure cases are:

1. Manual representative canopy values and day/night/soil-water/rain branches.
2. Geometry relations `z0`, `d`, `FLQH`, including the 1 m minimum emission height.
3. Neutral, stable and unstable Eq. (18), Eq. (21) and Eq. (22)-(25) wind/resistance oracles.
4. A discrimination test proving stable results use actual `z/L` rather than the superseded `(z-d)/L` interpretation.
5. Eq. (27)-(31) independent closed-form uptake and zero-air re-emission checks with manual `a=1.1`.
6. Constant-forcing monotonic convergence without equilibrium overshoot.
7. Figure-8-style additivity: one 40-interval constant exposure equals the pointwise sum of four shifted 10-interval pulse responses under the same interval-constant coefficients.
8. Isolation proof that RC1 and historical V2 source paths remain unchanged.

## Scope boundary

A3 does not authorize:

- generic empirical Leaf R5 physiology;
- new crop calibration;
- production parameter activation;
- Canada 1987 or ITER case completion;
- real CTEAS-Atmos binding;
- empirical site validation;
- original UFOTRI executable-equivalence claims.

The strongest result available after A3 is a manual-based functional leaf-mechanism reconstruction claim for the recoverable Eq. (7)-(31) scope.

## Completion rule

A3 may be marked complete only after:

- all manual-regression tests pass;
- portable and frozen-boundary CI pass on the exact candidate head;
- existing V4 machine gates remain green;
- the PR merges with an expected-head lock;
- merge parents/tree and remote `main` are audited for no drift.

After a clean A3 merge, the next replication stage is:

`UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`.
