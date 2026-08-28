# UFOTRI leaf Eq. (7)-(31) manual regression closure R1

## Stage

`UFOTRI_LEAF_EQ7_31_MANUAL_REGRESSION_CLOSURE_R1`

## Candidate status

`CANDIDATE_PENDING_EXACT_HEAD_CI`

## Base

`main = 61248e4abdfe80e9bce41e898e6c8d159caaa9d5`

This is the clean post-roadmap-sync state after A2 was merged and recorded as complete.

## Purpose

A3 closes the deterministic manual-semantic regression obligation for the opt-in A2 leaf fidelity path. It does not substitute synthetic cases for empirical validation and does not consume the Canada 1987 or ITER benchmark obligations reserved for Phase G.

The manual oracle is KfK 4605 Section 2.2.2, Eq. (12)-(31) where directly recoverable.

## Independent regression finding

A3 identified one manual-literal discrepancy in the A2 stability-dependent wind profile.

A2 used the displacement-adjusted height `z-d` for both:

- the logarithmic term; and
- the stable/unstable Monin-Obukhov correction.

The manual distinguishes these roles:

- Eq. (23): `ln((z-d)/z0) + 4.7 z/L`;
- Eq. (24): the logarithmic term uses `z-d`, while `Phi_m=(1-15 z/L)^(-1/4)` uses actual `z`.

A3 therefore applies a minimal correction only inside the opt-in `leaf_ufotri_v4` model. The log term still uses `z-d`; stability corrections use actual `z`. Neutral Eq. (22) is unchanged.

The frozen RC1 and historical V2 paths are untouched.

## Independent manual-regression matrix

The new A3 test file checks:

1. Manual representative canopy values:
   - daytime `4 s cm^-1 = 400 s m^-1`;
   - nighttime `60 s cm^-1 = 6000 s m^-1`;
   - mean LAI `3`;
   - Eq. (14) therefore gives approximately `133.333 s m^-1` daytime and `2000 s m^-1` nighttime canopy resistance.
2. Soil-water exhaustion, daytime rain and nighttime rain branches.
3. `z0=0.1H`, `d=0.6H`, `FLQH=0.8H` and the 1 m area-source-height minimum.
4. Independent neutral, stable and unstable Eq. (18), Eq. (21), Eq. (22)-(25) calculations.
5. A stable-case discrimination test that would fail the superseded `(z-d)/L` interpretation.
6. Independent Eq. (27)-(31) closed-form uptake and zero-air decay/re-emission with manual isotope ratio `a=1.1`.
7. Monotonic convergence to equilibrium without overshoot under constant forcing.
8. The manual Figure-8/additivity statement: the 40-interval constant-exposure trajectory equals the pointwise sum of four shifted 10-interval pulse/clean-air responses under the same interval-constant coefficients.
9. Isolation of the opt-in fidelity path from historical V2 and frozen RC1 sources.

## Benchmark boundary

A3 deliberately does not claim or perform:

- Canada 1987 reconstruction;
- ITER reconstruction;
- original UFOTRI executable comparison;
- empirical site validation;
- production parameter calibration;
- real CTEAS-Atmos coupling.

Those obligations remain where the master plan places them.

## Expected closure interpretation

If exact-head CI and merge/no-drift pass, A3 supports:

`UFOTRI_LEAF_EQ7_31_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION = COMPLETE`

for the recoverable leaf Eq. (7)-(31) scope only.

It does not imply whole-model UFOTRI reconstruction is complete. The next required stage remains:

`UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`.
