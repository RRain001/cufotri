# UFOTRI Native Primary Atmosphere Core R1

Stage: `UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE_R1`

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Base: `main@63461c42cce2bb13719500f7693ab507b6a66245`

## 1. Why this stage exists

A post-G4 review found that the roadmap had externalized too much atmospheric responsibility to CTEAS-Atmos. KfK 4605 explicitly describes a UFOTRI-native primary atmospheric model based on modified MUSEMET. Therefore standalone UFOTRI reconstruction must recover the manual-supported primary HT/HTO atmosphere independently; CTEAS-Atmos is a future alternate backend, not a prerequisite for reproducing UFOTRI's own atmospheric path.

This stage begins that correction without touching the retained RC1/default atmosphere.

## 2. Manual evidence recovered directly

KfK 4605 Section 2.1 states that the primary model:

- uses hourly wind velocity and direction records;
- constructs plume trajectories from straight hourly segments;
- uses a two-dimensional Gaussian segmented-plume model;
- classifies dispersion A-F by Pasquill/Gifford;
- represents `sigma_y` and `sigma_z` as power functions of source distance;
- limits `sigma_z` to `0.8` of the mixing-layer height;
- models dry deposition with source depletion;
- treats HT washout as negligible;
- treats HTO wet deposition as whole-plume washout;
- divides releases longer than one hour into one-hour source intervals.

Appendix B Table 9 gives the complete smooth-terrain Mol coefficient set:

| Class | p_y | q_y | p_z | q_z |
|---|---:|---:|---:|---:|
| A | 0.946 | 0.796 | 1.321 | 0.711 |
| B | 0.826 | 0.796 | 0.950 | 0.711 |
| C | 0.586 | 0.796 | 0.700 | 0.711 |
| D | 0.418 | 0.796 | 0.520 | 0.711 |
| E | 0.297 | 0.796 | 0.382 | 0.711 |
| F | 0.235 | 0.796 | 0.311 | 0.711 |

Appendix B also preserves the wind-height relation `U = U0 (h/h0)^a` and benchmark dry-deposition velocities `0.05 cm/s` for HT and `1.8 cm/s` for HTO.

## 3. Atmospheric oxidation correction

The repository previously exposed the Appendix-B input `Oxidation rate in air = 0.5 %/d` as benchmark evidence. That must not be interpreted as proof that KfK 4605 UFOTRI actively converted HT to HTO in air.

Section 2.2 explicitly states that conversion of tritium gas into HTO within the atmosphere is not included in the program because the conversion is slow. R1 therefore records a source conflict:

`KFK4605_AIR_OXIDATION_SECTION22_VS_ITER_TABLE8`

The implementation policy is fail-closed:

- the 0.5 %/d number remains visible as benchmark input evidence;
- the KfK 4605 fidelity path generates exactly zero atmospheric HTO from HT;
- any attempt to activate a non-zero air-conversion rate raises an error.

This does not affect the already-complete *soil* HT→HTO conversion stage E2, which remains a separate and required environmental mechanism.

## 4. Implementation

New isolated source:

`src/cteas_ufotri/atmosphere/ufotri_native_v4.py`

It provides:

- typed HT/HTO chemical forms;
- exact Mol A-F coefficient registry;
- `mol_sigma_m()` with the `0.8 h` vertical cap;
- Appendix-B wind-speed height scaling;
- straight-segment Gaussian concentration at explicit receptor height with ground reflection;
- exact activity-preserving splitting of long constant releases into intervals no longer than 3600 s;
- species-specific dry-deposition policy;
- HT wet-deposition rejection and explicit HTO washout input;
- controlled source-depletion activity ledger;
- straight-segment primary transport output containing air concentration, dry surface flux, dry/wet plume loss, and a zero atmospheric HT→HTO production term;
- machine-readable preservation of the oxidation-source conflict.

No existing `case.py`, Gaussian implementation, config/default file or workflow is changed.

## 5. Source-depletion claim boundary

KfK 4605 identifies the primary dry-deposition method as a source-depletion model but does not print the original MUSEMET numerical discretisation. R1 therefore uses the already auditable first-order compatibility form over travel time:

`k = v_d / h + Lambda_w`

and closes the source ledger exactly as:

`source_before = source_after + dry_loss + wet_loss`.

This is explicitly *not* evidence of original MUSEMET numerical equivalence. It is a controlled interim numerical realization of the recovered source-depletion role until stronger source material is available.

## 6. What remains after R1

R1 is deliberately not the whole native atmosphere. Remaining required work is:

1. hourly bent/segmented trajectory reconstruction under changing wind direction and speed;
2. typed adapters from native HT/HTO atmospheric results into the already-qualified E1/E2 and HTO environmental interfaces;
3. recovery/qualification of the two HTO rain-regime washout coefficients or explicit source-limited handling if the values cannot be recovered;
4. building-wake fidelity;
5. thermal-lift fidelity;
6. native atmosphere→soil→plant→food→dose end-to-end qualification;
7. only after the native path is closed, optional CTEAS-Atmos backend binding/qualification.

## 7. Claim boundary

The earlier G4 statement that no recoverable internal mechanism remained is no longer sufficient after this classification correction. Historical G4 evidence is not rewritten, but the project must reopen the manual-reconstruction completion flag during the following roadmap-sync step until native atmosphere closure is demonstrated.

R1 itself does **not** claim:

- complete UFOTRI atmospheric reconstruction;
- original MUSEMET numerical equivalence;
- original UFOTRI executable equivalence;
- real CTEAS-Atmos binding;
- empirical validation;
- production readiness;
- active atmospheric HT→HTO oxidation.

Expected machine result:

`PASS_UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE`
