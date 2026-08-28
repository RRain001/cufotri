# UFOTRI Cow/Milk/Beef Compartment Closure R1

Stage: `UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1`

Candidate status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

## 1. Result

D4 reconstructs the recoverable KfK 4605 Eq. (82)-(105-2) animal-chain roles as a separate opt-in activity-conserving path. It closes the missing Eq. (98) animal inhalation/skin route, preserves milk/cow/grass HTO-OBT transfer semantics, and completes the Eq. (105-2) grass-OBT reverse-rate dependency without activating V2 project feed, herd-geometry or continuous beef-production assumptions.

## 2. Manual equation map

| Manual equation | D4 role |
|---|---|
| (82) | cow-water overall-loss half-time reference, 3.5 d |
| (83) | cow HTO -> atmosphere, `0.03 d^-1` |
| (84) | cow HTO -> soil layer 1, `0.13 d^-1` |
| (85) | grass OBT -> milk OBT, `0.0017 d^-1` |
| (86) | cow OBT -> milk OBT, `0.0021 d^-1`, with OCR-heading ambiguity retained |
| (90) | cow HTO -> milk HTO, `0.039 d^-1` |
| (91) | cow HTO -> milk OBT, `0.0013 d^-1` |
| (92) | cow-OBT overall-loss half-time reference, 40 d |
| (94) | cow OBT -> cow HTO, `0.015 d^-1` |
| (96) | cow HTO -> cow OBT, `0.0011 d^-1` |
| (97) | grass OBT -> cow OBT, `0.0033 d^-1` |
| (98) | atmosphere -> cow HTO through breathing + skin |
| (99)-(104) | grass HTO/OBT -> cow balance; Eq. (103) `0.024 d^-1`, Eq. (104) `0.021 d^-1` |
| (105-1) | grass HTO -> grass OBT, `0.012 d^-1` |
| (105-2) | grass OBT -> grass HTO, `0.043 d^-1` |

Eq. (87)-(89), (93), (95), and (100)-(102) are retained as derivation/equilibrium evidence rather than introduced as additional independent hazards.

## 3. Eq. (86) OCR ambiguity

The available Markdown/OCR heading around Eq. (86) conflicts with its surrounding prose. D4 does not hide that defect. The transfer indices `t_8,10`, the description of the organic milk pool, and the subsequent milk-production balance support the role `cow OBT -> milk OBT`.

The implementation therefore records both facts: source heading ambiguity remains; D4 selects the compartment role from the reviewed equation context. This is not an original-source-code recovery claim.

## 4. Eq. (98) closes a genuine V2 gap

D1 proved that the historical `foodchain.model.step_animal` has no atmosphere-to-cow route. Public inhalation/skin code in `dose.public` concerns human dose and cannot be reused as animal uptake.

D4 therefore adds Eq. (98) directly to the animal inventory ledger. The manual geometry is retained explicitly:

```text
130 m3 cow-1 d-1 * 250 cows * 1.5
---------------------------------- = 4.875e-5 d-1
1.0e6 m2 * 1000 m
```

The manual-rounded value `4.9e-5 d^-1` is used as the transfer profile value, while the exact geometry value remains machine-visible. Atmospheric forcing is an explicit area-normalized column inventory with required provenance. This controlled interface is not a real CTEAS-Atmos binding.

## 5. Manual rounding is not silently repaired

D4 deliberately retains the manual equation-specific rounded values.

For the cow HTO source, the implemented competing hazards are Eq. (83), (84), (90), (91), and internal Eq. (96), whose sum is `0.2014 d^-1`. The Eq. (82) half-time gives `ln(2)/3.5 ~= 0.198042 d^-1`.

For cow OBT, Eq. (94)+Eq. (86) gives `0.0171 d^-1`, while Eq. (92) gives `ln(2)/40 ~= 0.017329 d^-1`.

No coefficient is rescaled to erase these differences. They are retained as source-rounding/equilibrium tension, not interpreted as numerical failure.

## 6. D3/D4 grass OBT closure

D3 could not complete grass Eq. (105-2) because the reverse rate depends on animal/milk organic losses. D4 now closes the identity:

```text
0.069 - (0.0033 + 0.021 + 0.0017)
= 0.043 d^-1
```

Thus the D4 grass OBT source has four explicit routes: `0.043 d^-1` to grass HTO; `0.021 d^-1` to cow HTO; `0.0033 d^-1` to cow OBT; and `0.0017 d^-1` to milk OBT. The sum is the manual `0.069 d^-1` overall grass-OBT loss.

## 7. State and conservation boundary

The opt-in D4 state uses Bq/m2 ecological-area inventories: grass HTO/OBT, cow HTO/OBT, milk HTO/OBT, and beef HTO/OBT.

Internal grass/cow/milk transfers conserve activity. Eq. (98) is an external input. Eq. (83) cow-to-atmosphere and Eq. (84) cow-to-soil are explicit D4 external outputs. Radioactive decay is not duplicated in this transfer closure.

Milk HTO/OBT are explicit receiver compartments. Beef is populated only through a caller-declared slaughter activity event.

## 8. Beef boundary and project assumptions

The manual food-chain uses beef as a representative ingestion product, but the retained V2 engineering adds assumptions that are not evidence of original UFOTRI behavior.

D4 does not activate `50 kg fresh d^-1` representative feed intake, `50 L d^-1` representative cow drinking water, `4000 m2 animal^-1` support-area normalization, `200 kg head^-1` edible beef mass, or `0.002 d^-1` continuous herd turnover.

Instead, a caller may declare a slaughter fraction. That event transfers the same fraction of cow HTO and cow OBT activity to beef HTO and beef OBT with an exact activity ledger. No default slaughter schedule, herd size, edible mass or consumption rate is inferred.

## 9. Numerical method and qualification

D4 uses a conservative competing-hazard split at each internal numerical step. Source outflows are integrated exactly for constant hazards during that substep and distributed among routes in proportion to their rates. All source-compartment transfers are computed from the substep-start state and applied simultaneously.

The selected controlled step is `3600 s`. The D4 machine gate verifies one-step/cumulative activity closure, deterministic repeat, 12 h + 12 h restart equivalence against a 24 h run on the same grid, 24 x 1 h partition equivalence, zero-inventory stability, explicit Eq. (98) animal input, all grass-OBT receivers, milk HTO/OBT receivers, explicit slaughter-to-beef conservation, fail-closed project feed/drinking-water inputs, and refinement at `3600 -> 1800 -> 900 -> 450 s` toward a `225 s` numerical comparison reference.

The refinement comparison is numerical qualification only. It is not an original UFOTRI executable benchmark.

## 10. Source-change boundary

D4 adds one new opt-in source module: `src/cteas_ufotri/foodchain/ufotri_cow_milk_beef_v4.py`.

It does not modify historical V2 `foodchain/model.py`, frozen V4 RC1, D3 `ufotri_vegetable_grass_v4.py`, existing V4 integrators, public dose code, or the replication roadmap.

The stage PR also adds one machine script, one pytest file, ADR-069, governance YAML, and this report.

## 11. Candidate claim and remaining gap

Only after exact-head CI, locked-head merge, and post-merge no-drift audit may D4 claim `UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE=COMPLETE`.

Remaining Phase-D work is public exposure reconciliation: `UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1`.

D4 makes no claim of public Eq. (106)-(107) completion, production animal parameter readiness, empirical validation, calibration, physical accuracy, real CTEAS-Atmos integration, original numerical discretization recovery, or original-executable equivalence.
