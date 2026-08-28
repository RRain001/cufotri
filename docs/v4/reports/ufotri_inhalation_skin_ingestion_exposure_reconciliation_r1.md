# UFOTRI Inhalation/Skin/Ingestion Exposure Reconciliation R1

Stage: `UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1`

Candidate status: `PENDING_EXACT_HEAD_CI`

## 1. Result in one sentence

D5 reconstructs a separate opt-in public-exposure policy that follows the recoverable KfK 4605 Eq. (106)-(107) semantics exactly enough to distinguish them from the retained modern application dose path: HTO inhalation plus 50% skin uptake, three representative ingestion foods, and one selected HTO dose coefficient applied after HTO+OBT food activity is summed.

## 2. Why a second policy path is required

The retained `src/cteas_ufotri/dose/public.py` is useful and remains unchanged. It is a modern application path:

- continuous per-step accumulation using `dt_s / 86400`;
- age-specific HTO dose coefficients;
- a distinct OBT ingestion coefficient;
- drinking water;
- leafy vegetables, root crops and grain;
- milk and beef.

Those semantics exceed the recoverable historical Eq. (106)-(107) policy. Rewriting them to mimic the manual would regress the application layer and would erase provenance. D5 therefore adds an opt-in manual path in parallel.

## 3. Eq. (106) reconstruction

The manual defines:

`D_IH = BR × DF × C_air,t × QF × 1.5`

The D5 compatibility path retains:

- `BR` in `m3/s`;
- time-integrated HTO air concentration in `Bq s/m3`;
- explicit selected `DF` in `Sv/Bq`;
- `QF=1`;
- inhalation dose reported separately;
- skin dose reported separately as exactly `0.5 × inhalation`;
- combined Eq. (106) dose therefore exactly equal to the `1.5` multiplier form.

The manual adult reference helper exposes `DF=1.7e-11 Sv/Bq`. The policy type itself still requires an explicit coefficient because the manual states that the selected coefficient depends on integration time and age.

## 4. Eq. (107) reconstruction

The manual selects one representative food from each of three classes:

1. green vegetable;
2. beef;
3. milk.

The D5 path therefore contains exactly these three classes. It does not silently add drinking water, root crops or grain.

Food inputs are accumulated as time-integrated specific activity in `Bq d/kg`. Consumption rates are explicit `kg/d` inputs. Milk is intentionally mass based because that is the literal Eq. (107) unit; no litre-to-kilogram conversion is hidden in the compatibility solver.

HTO and OBT food activities remain separately visible in diagnostics, but the historical manual policy adds them before dose evaluation and applies the same selected HTO coefficient to both. The manual itself describes this treatment as a limitation. D5 preserves the limitation as fidelity evidence rather than promoting it as modern dose practice.

## 5. Modern application policy remains intact

The machine gate imports and executes the existing `calculate_public_dose_step`.

A controlled air-only comparison isolates coefficient policy:

- manual adult reference HTO coefficient: `1.7e-11 Sv/Bq`;
- retained modern adult HPA HTO coefficient: `1.8e-11 Sv/Bq`.

With identical controlled air exposure, breathing and 50% skin factor, the outputs are deliberately distinct. This proves that the two policies coexist rather than one being silently relabelled as the other.

The retained modern path also keeps its distinct adult OBT ingestion coefficient (`4.2e-11 Sv/Bq`) and age-specific coefficient sets. D5 does not claim those values are original UFOTRI parameters.

## 6. Habit and provenance boundary

KfK Eq. (106)-(107) require breathing and consumption rates, but the current project's numeric habits are not recovered historical UFOTRI defaults.

D5 therefore requires explicit:

- breathing rate;
- green-vegetable consumption rate;
- beef consumption rate;
- milk consumption rate;
- habit provenance identifier;
- exposure provenance identifier.

The machine qualification uses synthetic controlled habits only.

## 7. Numerical qualification

Eq. (106)-(107) are integral algebraic equations. The relevant numerical invariant is exact additivity of the time-integrated exposure, not convergence of an invented differential solver.

The candidate machine gate checks:

- Eq. (106) inhalation identity;
- skin = 50% of inhalation;
- combined Eq. (106) = multiplier `1.5`;
- Eq. (106) residual closure;
- Eq. (107) three-food identity;
- Eq. (107) residual closure;
- separate upstream HTO/OBT activity diagnostics;
- same historical dose coefficient applied to ingested HTO and OBT;
- deterministic repeat;
- one-day versus 24 hourly partition equivalence;
- one-day versus 96 quarter-hour partition equivalence;
- zero-exposure zero-dose limit;
- manual-versus-modern coefficient-policy distinction;
- fail-closed invalid timestep/concentration/policy/habit handling.

## 8. Source decision

`NEW_OPT_IN_SOURCE_ONLY`

Candidate source:

`src/cteas_ufotri/dose/ufotri_manual_v4.py`

No existing `dose.public`, V2, RC1, D3/D4, V4 integration, workflow or roadmap file is modified in the D5 stage PR.

## 9. Candidate claim

If exact-head CI, locked merge and post-merge no-drift all pass, D5 may claim:

`UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION=COMPLETE`

This closes the recoverable Phase-D public-exposure semantics. It does not make the historical coefficient policy a modern production recommendation.

## 10. Hard boundaries

The following remain false:

- production exposure parameter activation;
- project breathing/consumption habits as recovered UFOTRI defaults;
- modern HPA coefficients as original UFOTRI values;
- separate OBT ingestion coefficient as original UFOTRI behavior;
- drinking water, root crops or grain as Eq. (107) terms;
- calibration;
- empirical validation;
- physical-accuracy/production-readiness claim;
- real CTEAS-Atmos binding;
- original-executable equivalence.

After a successful D5 merge/no-drift and separate roadmap synchronization, the selected next replication stage is:

`UFOTRI_HT_BRANCH_RECONCILIATION_R1`
