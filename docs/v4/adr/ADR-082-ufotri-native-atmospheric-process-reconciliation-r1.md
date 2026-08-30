# ADR-082 — UFOTRI Native Atmospheric Process Reconciliation R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION_R1`

## Context

H1 recovered the UFOTRI-native Gaussian/MUSEMET core but deliberately used a controlled first-order source-depletion compatibility approximation because KfK 4605 does not print the full relation. H2 recovered the hourly segmented trajectory and H3 connected native HT/HTO products to the existing environmental forcing contracts.

H4 is authorized to replace that H1 approximation for H4-and-later execution wherever the original atmospheric-process relation is now recoverable from authoritative UFOMOD/UFOTRI reports, while preserving source-limited boundaries instead of introducing surrogate physics.

Primary sources used for this reconciliation:

- KfK 4332, *UFOMOD — atmospheric dispersion and deposition* (1989), DOI `10.5445/IR/270028151`, especially Eq. (2.20), Eq. (2.27), and the building-wake/lift-off discussion around Eq. (3.22).
- KfK 5194, *Description of the New Version 4.0 of the Tritium Model UFOTRI Including User Guide* (1993), DOI `10.5445/IR/270034158`, especially the HTO washout discussion and `IWASH`, `IREGGR`, `AMDA`, `REGTIM`, `AWASH`, `BWASH` user-guide inputs.

## Decision 1 — KfK 4332 source depletion supersedes the H1 approximation

The H1 `source_depletion_compatibility` function remains unchanged as historical stage evidence. It is not the H4+ fidelity authority.

H4 adds `source_depletion_kfk4332` and `transport_straight_segment_reconciled`.

For dry deposition, the recovered KfK 4332 Eq. (2.20) relation is evaluated as:

`Q(x)/Q0 = exp[-sqrt(2/pi) * (v_d/u) * I]`

with

`I = integral_0^x exp[-H^2/(2 sigma_z^2)] / sigma_z dx`.

The already qualified Mol `sigma_z` power law and `sigma_z <= 0.8 hmix` boundary are retained. The integral is evaluated deterministically after the substitution `t=x^(1-q_z)`, which removes the ground-release singularity at `x=0`.

This directly implements the printed depletion equation. It does **not** claim byte-for-byte or numerical equivalence to the unavailable original MUSEMET closed-form three-case code.

For wet deposition, KfK 4332 Eq. (2.27) supplies the independent exponential correction `exp(-lambda*x/u)`. Dry and wet correction factors are multiplicative. The implementation records dry loss first and wet loss second only for ledger attribution; the final source strength is independent of this bookkeeping order.

## Decision 2 — recover both KfK 5194 HTO washout modes

`IWASH=0` is represented as the three printed precipitation classes:

| precipitation intensity | HTO lambda (s^-1) | HTO REGTIM |
| --- | ---: | ---: |
| `< 1 mm/h` | `6.0e-5` | `0.5` |
| `1 <= I < 3 mm/h` | `1.0e-4` | `0.75` |
| `I >= 3 mm/h` | `4.0e-4` | `0.72` |

The corresponding HT values are zero, preserving negligible HT wet deposition.

`IWASH=1` is represented by the printed HTO power law:

`lambda = 9.0e-5 * I^0.6`.

KfK 5194 prints `REGTIM(NN,1): see above` for this mode but the recovered evidence does not expose one unambiguous numeric default for the power-law `REGTIM`. H4 therefore returns `None` and marks that field source-limited. No value is inferred from the three class-specific durations.

## Decision 3 — lift-off/building wake/plume rise remain explicitly source-limited

KfK 4332 supports the semantic boundary that thermal buoyancy dominates when the lift-off Richardson quantity `Lp > 30`. That threshold is retained as evidence.

The currently recovered Eq. (3.22) text is OCR-ambiguous in its numeric coefficient/layout and cannot safely support a numerical implementation. H4 therefore does not implement an `Lp` calculator.

Likewise, the existence and roles of building-wake correction, `LIFTOF`, `PLRISE-HOEHE`, and `RISEFX` are evidenced, but the complete original numerical relations required for a fidelity implementation are not yet recovered. They remain `SOURCE_LIMITED`; no Briggs, AERMOD, CALPUFF, or other surrogate model is inserted.

## Chemical boundary

Atmospheric HT→HTO conversion remains disabled on the KfK 4605 fidelity route. H4 changes no chemistry.

## Acceptance

Expected machine result:

`PASS_UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION`

After exact-head CI, locked merge and merge-tree/no-drift certification, a separate roadmap-only sync may mark H4 complete and authorize H5 `UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1`.

## Non-claims

H4 does not establish original MUSEMET closed-form numerical equivalence, numeric KfK 4332 Eq. (3.22) lift-off equivalence, complete building-wake equivalence, complete plume-rise/rising-phase equivalence, CTEAS-Atmos binding, production parameter readiness, calibration, empirical validation, or original UFOTRI executable numerical equivalence.
