# UFOTRI HT→HTO Soil Conversion R1

Stage: `UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1`

Candidate status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

## 1. Result

E2 reconstructs the recoverable UFOTRI boundary by which effective HT deposition becomes HTO in soil. It does not introduce a separately evolving soil-HT compartment or an invented microorganism conversion half-time.

The candidate adds an isolated opt-in conversion/projection module, a conservation ledger, explicit primary-HTO versus HT-derived-HTO provenance, one machine gate and independent pytest qualification.

## 2. Manual interpretation

The controlling manual evidence is stronger than the general statement that deposited HT converts rapidly.

The secondary-model soil balance explicitly describes direct soil HT→HTO conversion as being indicated only by the deposition rate. Eq. (1) and Eq. (2) use `C_S,HTO` as the soil state and add the atmospheric HT contribution directly as `v_d,HT X_HT`.

Section 2.2.3 then explains the physical interpretation: HT deposition depends on soil type and moisture; microorganism activity transforms deposited HT to HTO very rapidly; only the transformed part remains in soil; and an integral, seasonally varying HT deposition rate is therefore selected in the model.

Consequently, the recoverable software boundary is not a first-order HT-soil oxidation solver. The effective deposition term already carries the conversion-selection semantics.

## 3. E1→E2 handoff

E1 intentionally emits a chemically-HT `HTSoilDepositionBoundary` and requires `converted_to_hto_bq_m2=0`.

E2 consumes only that reviewed type. For its interval-integrated deposited HT activity:

`generated HTO activity = input HT activity`

`residual independent soil HT activity = 0`

`HT input - HTO generated - residual HT = 0`.

The conversion is on an activity basis (`Bq m-2`). Upstream HT/T2 identity and provenance remain visible in the E2 result even though the receiving environmental state is HTO.

## 4. No invented microbial kinetics

E2 deliberately has no API for:

- microbial half-time;
- generic oxidation rate;
- partial conversion fraction;
- independent soil-HT storage.

This is a fidelity decision, not a claim that such kinetics do not exist physically. The available manual describes the transformation as very rapid and represents it through the effective deposition rate, so adding an unconstrained kinetic pool would exceed the recoverable source authority.

## 5. Entry into the existing three-layer soil system

The existing `ThreeLayerSoilForcing.surface_deposition_flux_bq_m2_s` is the external HTO input to L1. E2 projects generated HTO into that field without changing the soil solver.

If primary atmospheric HTO deposition is present simultaneously, the projection is additive:

`combined = primary HTO + HT-derived HTO`.

The projection record retains all three fluxes separately so later E3 work can identify secondary HTO provenance. No direct HTO injection is made into L2 or L3; subsequent movement remains owned by the already qualified soil hydrology/transport path.

## 6. Benchmark boundary

E1 exposed the KfK benchmark values `v_d,HT=0.05 cm/s`, atmospheric HT oxidation `0.5 %/d`, and HT soil diffusion `5e-2 cm2/s` as evidence.

E2 does not use any of those values as a new conversion-rate parameter:

- HT deposition velocity remains an upstream forcing/deposition responsibility;
- atmospheric oxidation is not soil conversion;
- HT soil diffusion is not reinterpreted as a microbial oxidation rate;
- no benchmark value becomes a production default.

## 7. Time and conservation constraints

The E1 deposition interval and E2 soil projection interval must match exactly. The `ThreeLayerSoilForcing.timestamp` must equal the conversion interval start.

The qualification checks:

- exact HT-loss/HTO-gain ledger closure;
- generated flux × interval = generated amount;
- one-hour versus four 15-minute conversion additivity;
- existing soil global HTO balance closure including radioactive decay;
- primary HTO preservation when HT-derived HTO is added;
- zero direct deeper-layer injection.

No interpolation or silent interval repair is permitted.

## 8. Source-change boundary

The intended E2 PR adds exactly:

- `src/cteas_ufotri/coupling/ht_to_hto_soil_v4.py`;
- `scripts/v4/run_ufotri_ht_to_hto_soil_conversion_r1.py`;
- `tests/v4/test_ufotri_ht_to_hto_soil_conversion_r1.py`;
- `docs/v4/adr/ADR-072-ufotri-ht-to-hto-soil-conversion-r1.md`;
- `docs/v4/governance/ufotri_ht_to_hto_soil_conversion_r1.yaml`;
- this report.

No existing E1, HTO, `soil_v4`, `soil_ufotri_v4`, root, TFWT/OBT, integration, workflow or roadmap file is intentionally modified.

## 9. Qualification and claims

The candidate may claim only after exact-head CI, locked-head merge and post-merge no-drift:

`UFOTRI_HT_TO_HTO_SOIL_CONVERSION=COMPLETE`

That scoped claim means the recoverable manual direct-conversion boundary, conservation ledger and existing-soil projection are closed.

It does not mean E3 HT-derived HTO re-emission/secondary feedback, E4 real CTEAS-Atmos HT binding, production parameterization, calibration, empirical validation, physical accuracy, production readiness, original numerical-discretization recovery or original-executable equivalence are complete.
