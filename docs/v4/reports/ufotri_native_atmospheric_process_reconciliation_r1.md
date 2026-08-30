# UFOTRI Native Atmospheric Process Reconciliation R1

Stage: `UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION_R1`

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Base: `main@85adef07d15cd319384db41ed8668dcd59e9832a`

## 1. Scope

H4 reconciles the atmospheric-process gaps intentionally left by H1. It does not alter the retained RC1/default Gaussian path and does not introduce CTEAS-Atmos as a dependency.

The H4+ native fidelity path is now:

`native source`
→ `KfK 4332 Eq. (2.20) dry source depletion`
→ `KfK 4332 Eq. (2.27) wet source correction`
→ `Gaussian segment concentration`
→ `species-specific dry surface flux`
→ existing H3 HT/HTO environmental adapters.

H1 `source_depletion_compatibility` remains available solely as historical compatibility evidence. H4+ qualification uses `transport_straight_segment_reconciled`.

## 2. KfK 4332 dry source depletion

KfK 4332 describes source depletion by reducing source strength with downwind distance and prints Eq. (2.20):

`Q(x)/Q0 = exp[-sqrt(2/pi) * (v_d/u) * I]`

where

`I = integral_0^x exp[-H^2/(2 sigma_z^2)] / sigma_z dx`.

H4 evaluates this direct equation with the already-qualified Mol vertical-dispersion relation and the existing `sigma_z <= 0.8 hmix` boundary.

For numerical stability at a ground release, the uncapped integral is transformed with `t=x^(1-q_z)`. The transformed integrand is finite at the source. A deterministic Simpson rule is then used on the regularized interval, with the capped part integrated directly when `sigma_z` reaches `0.8 hmix`.

The ground-release, uncapped identity

`I = x^(1-q_z) / [p_z (1-q_z)]`

is independently tested.

This is direct-equation reconstruction, not a claim that the unavailable original MUSEMET three-case closed-form implementation has been reproduced numerically.

## 3. KfK 4332 wet correction

KfK 4332 Eq. (2.27) treats washout source depletion as an exponential factor using washout coefficient `lambda`, travel distance `x`, and wind speed `u`:

`f_w = exp(-lambda*x/u)`.

H4 applies the dry and wet factors multiplicatively. The activity ledger records dry loss and wet loss separately and requires zero residual.

## 4. KfK 5194 HTO washout options

H4 recovers both documented UFOTRI 4.0 choices.

### `IWASH=0`

The precipitation-class boundaries are 1 and 3 mm/h. For HTO:

- `<1 mm/h`: `lambda=6.0e-5 s^-1`, `REGTIM=0.5`;
- `1<=I<3 mm/h`: `lambda=1.0e-4 s^-1`, `REGTIM=0.75`;
- `I>=3 mm/h`: `lambda=4.0e-4 s^-1`, `REGTIM=0.72`.

HT values are zero. At an actual precipitation intensity of zero, the runtime washout coefficient is zero rather than applying the first rain-class coefficient in dry weather.

### `IWASH=1`

For HTO:

`lambda = 9.0e-5 * I^0.6`.

For HT the coefficient remains zero.

The recovered KfK 5194 text does not expose an unambiguous numeric `REGTIM` default for this power-law path. H4 therefore leaves that value `None` and marks it `SOURCE_LIMITED_DO_NOT_INVENT`.

## 5. Lift-off, building wake and thermal rise

KfK 4332 supports the semantic criterion that thermal buoyancy dominates when `Lp > 30`.

However, the currently recoverable rendering of Eq. (3.22) is OCR-ambiguous in the numerical coefficient and equation layout. A numerical `Lp` calculator would therefore require guessing. H4 records the threshold but leaves Eq. (3.22) numerical evaluation source-limited.

The reports also establish the roles of building-wake correction, `LIFTOF`, `PLRISE-HOEHE` and `RISEFX`, but the complete numerical relations needed for faithful reconstruction have not been recovered. Those mechanisms remain explicit source-limited boundaries. No modern plume-rise or wake model is substituted.

## 6. Chemistry and provenance boundaries

Atmospheric HT→HTO conversion remains disabled for the KfK 4605 fidelity route. H4 does not activate the conflicting ITER `0.5 %/d` input.

H4 does not change H3 provenance contracts, infer local wet surface deposition from plume source loss, or change the existing environmental model.

## 7. Qualification

Focused qualification covers:

- exact `IWASH=0` class boundaries, coefficients and HTO `REGTIM` values;
- exact `IWASH=1` HTO power law;
- zero HT washout in both modes;
- direct Eq. (2.20) ground-release analytic identity;
- reduced dry depletion for elevated versus ground release;
- exact Eq. (2.27) wet-only exponential factor;
- zero source-depletion activity residual;
- numerical distinction between H4 recovered depletion and H1 controlled compatibility approximation;
- H4 reconciled transport concentration/flux/ledger closure;
- retained zero atmospheric HT→HTO generation;
- explicit source-limited lift-off/building-wake/plume-rise boundaries.

Expected machine result:

`PASS_UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION`

## 8. Non-claims

This stage does not establish original MUSEMET closed-form three-case numerical equivalence, numerical Eq. (3.22) equivalence, complete building-wake or plume-rise equivalence, CTEAS-Atmos binding, production calibration, empirical validation, or original UFOTRI executable numerical equivalence.

H5 is not authorized until H4 passes exact-head CI, locked merge/no-drift certification, and a separate roadmap status sync.
