# ADR-070 — UFOTRI inhalation/skin/ingestion exposure reconciliation R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1`

## Context

D1 established that the retained V2 public-dose path is continuous and useful, but it mixes recoverable UFOTRI pathway topology with later application policy. D4 has now closed the recoverable cow/milk/beef environmental compartments. The remaining Phase-D replication gap is the public exposure policy in KfK 4605 Eq. (106)-(107).

The existing `src/cteas_ufotri/dose/public.py` must remain available as the modern application path. It uses age-specific HTO coefficients, a distinct OBT ingestion coefficient, drinking water, leafy/root/grain foods, milk and beef. Those features are useful application extensions but are not evidence that the historical UFOTRI dose calculation used the same policy.

## Manual evidence

KfK 4605 Section 4 records:

- an adult HTO dose-conversion reference of `1.7e-11 Sv/Bq`;
- a quality factor `QF=1` in Eq. (106);
- skin absorption represented as 50% of inhalation, hence the Eq. (106) multiplier `1.5`;
- Eq. (106) uses breathing rate in `m3/s` and time-integrated air concentration in `Bq s/m3`;
- Eq. (107) uses three representative food classes only: one green vegetable, beef and milk;
- Eq. (107) uses mass consumption rates and time-integrated specific food concentrations;
- HTO and OBT are calculated separately in plant/cow/milk compartments but are added before historical ingestion dose calculation;
- ingested OBT is treated with the same HTO dose coefficient in the present manual version, with the manual itself noting the resulting limitation.

The manual also states that the selected dose coefficient depends on integration time and age. Therefore D5 does not hide the adult reference value as an unchangeable solver default: a manual policy object requires an explicit coefficient, while a named helper provides the stated adult reference profile.

## Decision

Add one isolated opt-in source module:

`src/cteas_ufotri/dose/ufotri_manual_v4.py`

The module:

1. preserves Eq. (106) literally as inhalation plus 50% skin absorption;
2. preserves Eq. (107) as green-vegetable + beef + milk ingestion only;
3. tracks HTO and OBT food activity separately, then applies one selected manual dose coefficient to their sum;
4. accumulates air in `Bq s/m3` and food specific activity in `Bq d/kg`;
5. requires breathing and food consumption habits explicitly with provenance;
6. performs no implicit milk litre-to-kilogram conversion;
7. leaves `dose.public.calculate_public_dose_step` untouched as the modern application path.

No adapter is allowed to silently add drinking water, root crops or grain to Eq. (107). Those remain application extensions outside the manual-fidelity equation.

## Numerical/verification decision

Eq. (106)-(107) are integral algebraic equations, not a differential solver. D5 therefore qualifies exact integral additivity rather than inventing a timestep-discretization claim. A one-day controlled exposure must agree with 24 hourly and 96 quarter-hour partitions to floating-point tolerance.

The machine gate also demonstrates that the manual adult reference (`1.7e-11 Sv/Bq`) and retained modern adult HPA HTO coefficient (`1.8e-11 Sv/Bq`) produce deliberately distinct air-only results. Neither policy is relabelled as the other.

## Boundaries

D5 does not establish:

- production breathing or consumption habits;
- modern coefficients as original UFOTRI coefficients;
- a separate OBT coefficient as original UFOTRI behavior;
- drinking-water/root-crop/grain inclusion in manual Eq. (107);
- empirical validation or calibration;
- physical accuracy or production readiness;
- real CTEAS-Atmos binding;
- original-executable equivalence.

If exact-head CI and merge/no-drift pass, the scoped claim may become:

`UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION=COMPLETE`
