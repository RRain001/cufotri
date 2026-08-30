# ADR-079 — UFOTRI Native Primary Atmosphere Core R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE_R1`

## Context

Post-G4 review identified a classification error in the replication roadmap. The previous gap disposition treated real atmospheric HT/HTO transport as wholly owned by the future CTEAS-Atmos integration. KfK 4605, however, makes clear that UFOTRI itself contains a primary atmospheric dispersion model based on a modified MUSEMET Gaussian trajectory model. CTEAS-Atmos is therefore a future replaceable/high-fidelity atmospheric backend, not the owner of the recoverable UFOTRI-native primary atmosphere.

KfK 4605 Section 2.1 states that MUSEMET:

- uses hourly wind-speed and wind-direction records for plume trajectories;
- represents straight hourly trajectory segments with a two-dimensional Gaussian segmented-plume model;
- updates dispersion parameters hourly by Pasquill/Gifford A-F category;
- uses power-law sigma parameters;
- limits `sigma_z` to `0.8 * mixing-layer height`;
- represents dry deposition by source depletion;
- treats HT washout as negligible;
- treats HTO wet deposition as whole-plume washout;
- divides source terms longer than one hour into one-hour releases.

Appendix B Table 9 prints the complete S.C.K./C.E.N. Mol coefficient set for A-F. Table 8 prints benchmark HT and HTO dry-deposition velocities and an `Oxidation rate in air = 0.5 %/d` input.

A source-level conflict must be preserved: Section 2.2 explicitly states that atmospheric conversion of HT to HTO is *not included in the program* because the conversion is slow. Therefore the Table-8 oxidation input is evidence-visible but must not be silently activated in the KfK 4605 fidelity path.

## Decision

Create an isolated opt-in UFOTRI-native primary-atmosphere core:

`src/cteas_ufotri/atmosphere/ufotri_native_v4.py`

This first native-atmosphere stage reconstructs only directly recoverable primary-model semantics and deliberately does not claim the unavailable original MUSEMET numerical implementation.

### Recovered in R1

1. Explicit `HT` and `HTO` atmospheric forms.
2. Exact Appendix-B Table-9 Mol A-F coefficients.
3. `sigma_y = p_y x^q_y`, `sigma_z = p_z x^q_z` with `sigma_z <= 0.8 h`.
4. Appendix-B wind-height power law `U = U0 (h/h0)^a`.
5. Straight-segment Gaussian concentration with ground reflection and explicit receptor height.
6. Constant releases split into intervals no longer than one hour with exact activity closure.
7. Species-specific dry-deposition policy.
8. HT wet deposition fails closed; HTO washout requires an explicit coefficient.
9. Source-depletion activity ledger using a controlled first-order compatibility approximation while the original MUSEMET source-depletion discretisation remains unavailable.
10. Atmospheric HT→HTO production is exactly zero in this KfK 4605 path; a non-zero oxidation policy fails closed.
11. Appendix-B 0.5 %/d oxidation input remains machine-visible as conflicting benchmark evidence, not active model physics.

### Not recovered in R1

- complete bent hourly trajectory numerics;
- original MUSEMET source-depletion discretisation;
- original building-wake implementation;
- original thermal-lift implementation;
- primary-atmosphere adapters into the already-qualified E1/E2 HTO/HT interfaces;
- full native atmosphere→soil→plant→food→dose end-to-end qualification;
- real CTEAS-Atmos binding.

These are subsequent native-atmosphere stages or source-limited boundaries and are not replaced by assumptions in R1.

## Claim correction

The previous statement `NO_IMMEDIATE_INTERNAL_REPLICATION_STAGE` is no longer valid after this classification correction. Until the UFOTRI-native primary atmosphere and its internal end-to-end handoff are closed, the project must not use the post-G4 statement as evidence that no recoverable internal mechanism remains.

This ADR does not rewrite historical G4 evidence. It records that a later architectural review discovered an incorrectly externalized recoverable mechanism.

The appropriate top-level state after roadmap synchronization is therefore expected to be:

`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=FALSE_PENDING_NATIVE_ATMOSPHERE_CLOSURE`

while retaining:

`UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED`.

## CTEAS-Atmos boundary

CTEAS-Atmos remains a future alternate backend. Its later adapter must map real HT/HTO atmospheric products into the same typed environmental interfaces, but it must not be required to execute the standalone UFOTRI-native fidelity path.

## Acceptance

R1 may be marked complete only after:

- the focused machine gate passes;
- focused pytest passes;
- exact-head Remediation CI passes;
- exact-head Protected CI passes;
- locked merge uses the certified head;
- post-merge tree/head/main no-drift audit passes.

Passing R1 authorizes the next native-atmosphere stage for hourly bent-trajectory and forcing-adapter closure; it does not restore the whole-model reconstruction-complete flag by itself.
