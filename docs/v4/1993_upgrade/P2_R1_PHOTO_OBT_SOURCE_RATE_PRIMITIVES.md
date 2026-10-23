# UFOTRI 1993 P2 R1 — opt-in photo/OBT source-rate primitives

Status: **RESEARCH SOFTWARE CANDIDATE**, not a validated P2 photosynthesis/OBT solver.

## Primary sources and explicit boundaries

- Original: W. Raskob, **KfK 5194 (August 1993)**, *Description of the New Version 4.0 of the Tritium Model UFOTRI Including User Guide*, §5.5.1 printed pp.19–21 / PDF0 28–30, §5.5.2 pp.21–23 / PDF0 30–32. Official PDF: https://publikationen.bibliothek.kit.edu/270034158/3813483
- Historical contrast: KfK 4605 (1990), §2.2.6, and the current frozen `plant/obt_ufotri_v4/model.py`. Its original first-order rate defaults and separate exchangeable/NE-OBT semantics are **unchanged**.
- Current upstream: P0 Issue #126 and P1 contract `versioned_inputs_1993.py`. Dedicated P2 Issue #128. Earlier P3 source work is **not** automatically bound to this P2 candidate.
- **Original executable/source and independent scientific review are unavailable**; the mathematical source tests below do not establish FORTRAN equivalence, experimental photosynthesis, root/leaf physics or production use.

## Formula, dimensional and identity ledger

All conversions below require **explicit historical profile selection** and opt-in function calls. The caller supplies coefficients and source-specific context; no 1993 runtime mode is turned on.

| Printed source | Scoped R1 operation | Input and output / units | Boundary |
|---|---|---|---|
| Eq.(27), p.19 | `I_abs(L)=I_in*0.6*exp(-0.6 L)` | `I_in`, `I_abs`: W m⁻²; L and LAI: m² leaf per m² ground | No incident-PAR reconstruction. Leaf-area normalization needs independent audit before numerical original parity. |
| Eq.(26), p.19 | `P_pot=(P_max*epsilon*I_abs)/(P_max+epsilon*I_abs)-R_d` | `P_max, R_d, P_pot`: g CO₂ m⁻² h⁻¹ on **explicit R1 leaf-area-normalized input basis**; epsilon: g CO₂ W⁻¹ h⁻¹ | The manual prints m⁻² without unambiguous explicit **leaf vs ground** superscript. No original canopy-area equivalence claimed. Zero PAR produces **−R_d**, not a forced zero. |
| Eq.(31), p.21 | `P_act=P_c*1.5*f(r)` | `P_c`: g CO₂ m⁻² ground h⁻¹; `P_act`: g dry-matter m⁻² ground h⁻¹; f(r): dimensionless, declared [0,1] | `P_c` is externally integrated; Eq.(28) canopy integration, Eq.(29) temperature-max response and Eq.(30) respiration law are **NOT_IMPLEMENTED**. The P3 stomatal weighting `f(r)` is explicitly supplied, not guessed. |
| Eq.(32), p.22 | `T_act=T_m*(fact1)*(fact2)` | `T_m` caller-supplied **d⁻¹**; explicit conversion `T_m,h=T_m/24` h⁻¹; `fact1` externally supplied from Figure 11 (dimensionless); fact2=1.75 day or 0.25 night | Figure 11 function and developmental calendar **NOT_RECONSTRUCTED**. Historic diurnal multipliers are empirical, not a proven physiological night process. |
| Eq.(33), p.23 | `T_act=(P_act/P_mean)*T_m,h*fact2*dis` | `P_act` and **`P_mean` are both g dry-matter m⁻² ground h⁻¹**; dis explicitly supplied [0,1], with documented historical default **0.5** | **Daylight only** until original night routing resolved. `P_mean` is a mean *dry-matter* production rate and **must not** be replaced by Eq.(26)'s `P_max` CO₂ rate. |

`T_m` is a crop/compartment-specific long-term transfer rate (KfK5194 Tables 9–12) supplied by the caller, **not** the frozen 1990 Eq.(65)/(66) coefficient and not an implicit modern mass-activity factor. The R1 module validates four printed crop/organ roles (grass and leafy vegetable whole plant, potato tuber, wheat *seedlings* as worded in §5.5). Source rates/compartments and the original spelling of wheat edible organ must be reconciled with P5 before coupling. No numerical rate is inferred from crop identity alone.

An explicit 12 h day + 12 h night split makes the average of 1.75 and 0.25 equal to one. This elementary algebra is **not** a valid normalization claim for arbitrary daylight duration, growth stage, latitude or forcing.

## Night-time Eq.(33) contradiction and implementation decision

Section 5.5.2 prints `T_act=(P_act/P_mean)*T_m*fact2*dis`, where `P_act` comes from measured/modelled daytime photosynthesis. The same printed pp.22–23 state night formation is fixed to **one quarter of the daily mean**, and the daytime factor is 1.75, while acknowledging night processes are not resolved physiologically.

The source does **not** unambiguously state whether the Eq.(33) nocturnal `P_act` is replaced with a uniform mean, set to a positive historical surrogate, or handled by a separate branch. Applying zero solar input directly to Eq.(33) would give zero (or a negative net CO₂ result from respiration), inconsistent with a positive night formation hypothesis.

**P2 R1 therefore deliberately rejects `ADVANCED_EQ33_DAYLIGHT_ONLY + NIGHT`.** The simple Eq.(32) night branch applies its expressly documented 0.25 coefficient without claiming physical mechanism. No silent fallback, clamp of negative Eq.(26) net assimilation, fake PAR, or original FORTRAN algorithm is introduced.

## Interfaces and checks

- `src/cteas_ufotri/plant/kfk5194_1993_photo_obt_rates.py` — standalone typed primitives, source identity, fail-closed source-version/mode/organ/units/zero-input contracts and provenance. No changes to frozen V2/V3/V4 solver, CLI or adapters.
- `tests/unit/test_ufotri_1993_p2_r1_photo_obt_rates.py` — external arithmetic oracles for light saturation, canopy PAR attenuation, negative zero-light net photosynthesis, Eq.(31) externally supplied stress, explicit four crop roles, both Eq.(32) day/night coefficients, daytime Eq.(33) dry matter P_mean distinct from CO₂ P_max, invalid input and night-branch rejection.
- **Not yet implemented/accepted:** Eq.(28)-(30) exact canopy–temperature–respiration implementation; verified external f(r); Figure 11 function; source-table crop coefficient selection; time-integrated TFWT→OBT activity transfer and HTO+OBT conservation; 1993 grass 15 d / leafy 22 d whole outgoing edge ledgers; wheat/potato edible organ integration; external source/executable replay.

## Review and acceptance gates

R1 software tests only verify equations *under the explicitly supplied research input basis*. Code review, exact-HEAD software testing, independent scientific source/unit review and eventual original-model comparison remain separate. There is no basis to assert full P2, whole 1993 model, original executable numerical equivalence, empirical validation or regulatory readiness. Keep unreviewed research PR in Draft. P0 #126 and P2 #128 remain open.
