# ADR-069 — UFOTRI cow/milk/beef compartment closure R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1`

## Context

D1 established that the retained V2 animal chain contains useful continuous topology but mixes KfK 4605 transfer evidence with later project assumptions. D3 closed vegetable Eq. (65)-(66) and left grass OBT Eq. (105-1)-(105-2) explicitly for D4 because Eq. (105-2) subtracts grass-OBT losses to cow and milk.

The available KfK 4605 manual defines the recoverable D4 scope in Eq. (82)-(105-2):

- Eq. (82)-(84): cow-water overall loss and cow HTO losses to atmosphere and top soil;
- Eq. (85)-(91): milk HTO/OBT pathways;
- Eq. (92)-(97): cow OBT turnover/formation and grass OBT to cow OBT;
- Eq. (98): atmosphere to cow HTO through breathing plus the 1.5 skin-absorption factor;
- Eq. (99)-(104): grass HTO/OBT uptake by the cow;
- Eq. (105-1)-(105-2): grass HTO/OBT reversible pair after accounting for animal/milk organic losses.

The retained V2 `foodchain.model.step_animal` has no Eq. (98) atmosphere-to-cow route. Its public inhalation/skin dose code is a human dose pathway and cannot be relabeled as animal uptake.

## Source ambiguity retained

The OCR heading around Eq. (86) is inconsistent with the surrounding prose. The compartment indices, the following milk-production balance, and the text describing the organic milk pool support the D4 role `cow OBT -> milk OBT` for `t_8,10 = 2.1e-3 d^-1`.

D4 records this as `eq86_heading_ocr_ambiguous=True` and `eq86_role_resolved_from_compartment_indices_and_context=True`. This is a reviewed manual-role resolution, not recovery of the unavailable original source code.

## Decision

1. Add a new opt-in `foodchain/ufotri_cow_milk_beef_v4.py`; do not modify historical V2, frozen RC1, D3, or existing V4 integrators.
2. Use explicit area-normalized activity inventories for grass HTO/OBT, cow HTO/OBT, milk HTO/OBT, and beef HTO/OBT.
3. Treat Eq. (98) as a distinct atmosphere-column-inventory input to cow HTO. It is not public dose and requires explicit atmosphere provenance.
4. Preserve the manual-rounded equation rates as written. Do not renormalize them to force exact equality with the half-time summaries: Eq. (82) exact `ln(2)/3.5 ~= 0.198042 d^-1`, while the D4 cow-HTO competing hazard including internal HTO->OBT is `0.2014 d^-1`; Eq. (92) exact `ln(2)/40 ~= 0.017329 d^-1`, while Eq. (94)+Eq. (86) gives `0.0171 d^-1`.
5. Close Eq. (105-2) literally with the animal/milk loss terms: `0.069 - (0.0033 + 0.021 + 0.0017) = 0.043 d^-1`.
6. Reject nonzero external feed/drinking-water inputs in the D4 manual path. Eq. (99)-(104) uses the manual grass-surrogate transfer system; V2 screening assumptions of 50 kg fresh feed/day and 50 L water/day are not D4 manual defaults.
7. Do not activate V2 project assumptions for 4000 m2/animal support area, 200 kg/head edible beef mass, or `0.002 d^-1` continuous herd turnover.
8. Provide only an explicit caller-declared slaughter activity transfer from cow HTO/OBT to beef HTO/OBT. This is a post-RC1 conservation boundary, not a recovered original slaughter algorithm or production parameterization.
9. Do not duplicate radioactive decay inside this Eq. (82)-(105-2) transfer closure.

## Numerical method

For each source compartment and internal numerical interval, D4 applies an exact constant competing-hazard outflow:

```text
L = sum_i k_i
Delta_source = M * (1 - exp(-L * dt))
Delta_i = Delta_source * k_i / L
```

All transfers are computed from the state at the start of the numerical substep and then applied simultaneously. This preserves activity across internal transfers; only Eq. (83) atmosphere return and Eq. (84) soil return are external D4 boundaries, while Eq. (98) is an external input.

The selected controlled numerical step is 3600 s. Refinement is checked at 3600/1800/900/450 s against a 225 s comparison reference. This operator split is an implementation choice, not recovered original UFOTRI discretization.

## Required gates

- exact Eq. (98) geometry (`4.875e-5 d^-1`) and manual-rounded `4.9e-5 d^-1` both visible;
- Eq. (105-2) identity closes with Eq. (85), Eq. (97), and Eq. (104);
- Eq. (82)/(92) rounded-rate tensions remain visible and are not renormalized;
- Eq. (98) increases cow HTO and is never represented as public dose;
- grass OBT reaches grass HTO, cow HTO, cow OBT, and milk OBT receivers;
- milk HTO/OBT receivers are explicit;
- activity conservation with Eq. (83)/(84) external boundaries;
- deterministic repeat, restart equivalence, and hourly partition equivalence;
- monotonic timestep refinement and zero-inventory stability;
- explicit slaughter-to-beef activity conservation;
- fail-closed project feed/drinking-water activation and invalid inputs.

## Consequences

If exact-head CI and merge/no-drift pass, D4 may claim:

`UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE=COMPLETE`

This scoped claim does not establish public Eq. (106)-(107) exposure fidelity, production animal parameters, empirical validation, real CTEAS-Atmos binding, physical accuracy, original numerical discretization, or original-executable equivalence.

The next stage after a separate roadmap-status PR is `UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1`.
