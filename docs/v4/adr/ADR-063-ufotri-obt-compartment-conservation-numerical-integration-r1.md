# ADR-063: UFOTRI OBT compartment conservation and numerical integration R1

## Status

Proposed closure for:

`UFOTRI_OBT_COMPARTMENT_CONSERVATION_NUMERICAL_INTEGRATION_R1`

## Context

B1 (`UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`) closed the recoverable plant OBT state-role semantics:

- exchangeable OBT is not an independent activity pool and remains co-represented with free plant HTO on the `TFWTState` pathway;
- `OBTState` represents the non-exchangeable organic-tritium compartment in the opt-in UFOTRI fidelity mapping;
- the recoverable compartment topology is first order: plant HTO drives non-exchangeable OBT formation and non-exchangeable OBT undergoes a first-order loss;
- a generic multi-pool OBT model is not required for UFOTRI replication.

B1 also identified two linked but numerically non-identical manual rate descriptions:

1. KfK 4605 Section 2.2.6 hourly atmospheric/dispersion context:
   - formation `0.0006 h^-1`;
   - loss `0.003 h^-1`.
2. Section 3.3.3 Eq. (65)-(66) ingestion-compartment context:
   - `t15,14 = ln(2)/10 d`;
   - `t14,15 = t15,14 * M_OBT * 9 / (M_HTO * 13)` using stated masses `M_OBT=0.1 kg m^-2`, `M_HTO=0.4 kg m^-2`;
   - converted hourly values are approximately `0.0028881133 h^-1` loss and `0.0004998658 h^-1` formation.

The original executable/source is unavailable, so B2 must quantify numerical behavior without choosing one description as recovered original truth.

## Decision

B2 is a qualification-only stage. It does not modify:

- `plant/obt_v3`;
- `plant/tfwt_v3`;
- the V4 soil-root-TFWT-OBT integrator;
- the selected operator split;
- the frozen RC1/V3 default parameter path.

A new machine-visible harness runs two explicit profiles under identical controlled synthetic forcing:

- `SECTION_2_2_6_DAILY_AVERAGE_CONTROLLED_BASELINE`;
- `EQ65_66_DERIVED_HOURLY_COMPARISON`.

Both use day/night multipliers `1/1` only to hold the rate constant during this controlled numerical comparison. That does not reconstruct the missing original diurnal split.

## Required numerical gates

### 1. Coupled-chain conservation

For each rate profile, run the existing V4 soil-root-TFWT-OBT chain and require all existing auditable residuals to remain within the established numerical tolerance:

- soil-root HTO identity residual;
- plant inventory residual;
- coupled inventory residual;
- soil HTO balance residual.

### 2. Deterministic repeat

The same profile, forcing, timestep and initial state must produce an identical result on repeat execution.

### 3. Restart equivalence

Serialize/restore the coupled state at the midpoint and require an identical final result to the uninterrupted run.

### 4. Timestep refinement

For the controlled 24 h chain, compare `3600`, `1800`, `900`, and `450 s` steps against a `225 s` reference and require monotonically decreasing state error.

This is a numerical convergence check for the existing operator split, not evidence that the physical parameterization is correct.

### 5. Independent analytic OBT oracle

Under constant TFWT inventory and constant OBT coefficients, independently evaluate:

`M(t) = S/kr + (M0 - S/kr) exp(-kr t)`

with `S = kf * M_TFWT`.

Require the existing analytic `OBTSolver` to reproduce the independently calculated value and its formation/loss ledger for both profiles.

### 6. Zero-TFWT decay limit

With zero TFWT and nonzero initial OBT, require:

`M(t) = M0 exp(-kr t)`.

This separately verifies the loss branch without formation.

### 7. Frozen reduced-baseline identity

The Section-2.2.6 qualification profile must use exactly the existing frozen controlled OBT parameters and must reproduce the same coupled numerical result as a reference run constructed directly from `ufotri_obt_baseline_parameters()`.

### 8. Manual-profile consequence must remain visible

Because B1 established that the two recoverable rate descriptions are not numerically identical, B2 requires their controlled OBT outcomes to differ. A nonzero difference is reported as a profile consequence, not as a ranking of physical validity.

### 9. No exchangeable-OBT double counting

The B1 role map remains authoritative. No third exchangeable OBT inventory may appear in the B2 calculation.

## Interpretation

A successful B2 result establishes that:

- the reconstructed OBT state roles can be propagated through the existing numerical chain without violating current conservation contracts;
- the existing Section-2.2.6 controlled baseline remains a strict numerical reference;
- the Eq. (65)-(66)-derived profile can be run through the same frozen interfaces;
- the consequence of the manual rate discrepancy is deterministic and auditable;
- restart and timestep behavior remain controlled for both profiles.

It does not establish which manual rate set the unavailable original executable selected in every context.

## Claim boundary

B2 does not authorize or establish:

- normalized original day/night OBT formation multipliers;
- exact original executable parameter selection;
- empirical validation;
- calibration;
- production parameter activation;
- physical-accuracy claims;
- generic multi-pool OBT physiology;
- real CTEAS-Atmos binding;
- whole-model UFOTRI completion.

## Completion rule

B2 may be marked `COMPLETE` only after:

- all B2 machine gates pass;
- portable and frozen-boundary CI pass on the exact candidate head;
- all existing V4 machine gates remain green;
- the PR merges with an expected-head lock;
- merge parents/tree and remote `main` are audited for no drift.

A clean B2 merge closes Phase B OBT fidelity at the recoverable manual/software level. The next authorized replication stage is:

`UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1`.
