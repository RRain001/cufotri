# ADR-072 — UFOTRI HT→HTO soil conversion R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1`

## Context

E1 established a chemically explicit HT/T2 atmospheric/deposition boundary and intentionally stopped before soil chemistry. Its output `HTSoilDepositionBoundary` contains an interval-integrated `deposited_ht_bq_m2` amount and requires zero E1-side HTO conversion.

The E2 question is whether the recoverable UFOTRI manual supports a separately parameterised soil-HT kinetic inventory, or whether HT deposition is already an effective direct source to the soil HTO compartment.

KfK 4605 resolves this at two levels.

First, the secondary-model balance explicitly says that the soil balance is for HT and/or HTO **with direct conversion in soil of HT into HTO indicated only by the deposition rate**. Eq. (1) and Eq. (2) contain only the soil HTO state `C_S,HTO`; the HT atmospheric contribution enters that HTO state directly as `v_d,HT X_HT`.

Second, Section 2.2.3 states that the HT deposition rate depends on soil type and soil moisture, that deposited HT is transformed into HTO very quickly by microorganism activity, and that only the transformed part remains in soil. Because the transformation is assumed very rapid, UFOTRI selects an integral/seasonally varying HT deposition rate rather than a separate microbial conversion half-time.

Therefore the recoverable manual model does not expose an independently evolving soil-HT pool or a microbial oxidation rate that can be reconstructed without inventing source semantics.

## Decision

Add one isolated opt-in source module:

`src/cteas_ufotri/coupling/ht_to_hto_soil_v4.py`

It consumes the reviewed E1 `HTSoilDepositionBoundary` and implements the Eq. (1)/(2) effective boundary semantics.

### 1. Chemical-form conversion boundary

For activity already accepted by the E1 HT deposition boundary:

`input deposited HT activity = generated soil HTO activity`

and

`residual independent soil HT activity = 0`.

This is an activity identity in Bq/m², not a mass or molecule-count conversion. HT and T2 retain their upstream species identity in the conversion provenance, while the soil receiver is HTO.

### 2. No invented soil-HT kinetic pool

E2 does **not** add:

- a soil HT storage state;
- a microbial oxidation half-time;
- a tunable conversion fraction;
- a soil-HT decay/transport solver independent of the manual HTO state.

A partial conversion fraction would contradict the recoverable Eq. (1)/(2) implementation boundary unless new source evidence establishes an original algorithm that retained an HT pool.

### 3. Deposition ownership remains upstream

The effective HT deposition rate is the quantity that already carries the dependence on soil type, soil moisture and microorganism activity in the manual model.

E2 therefore does not recompute `v_d,HT` from the KfK benchmark `0.05 cm/s` value and does not promote that benchmark value to a production default. The E1 input flux is accepted as an explicit/provenanced boundary quantity.

The manual benchmark atmospheric oxidation rate `0.5 %/d` is unrelated to this soil conversion and remains outside E2.

### 4. Existing three-layer soil state is reused

Generated HTO is projected into the existing `ThreeLayerSoilForcing.surface_deposition_flux_bq_m2_s`, which already represents external HTO input to L1.

E2 does not modify `soil_v4`, `soil_ufotri_v4`, the hydrology solver, root solver, TFWT/OBT solver, or the RC1 default path.

The projection is additive:

`combined HTO surface input = primary HTO input + HT-derived HTO input`.

It must never overwrite a simultaneously present primary HTO deposition flux.

### 5. Provenance is retained outside the aggregate soil field

Because `ThreeLayerSoilForcing` stores the aggregate HTO surface flux, E2 returns a projection record that keeps separately visible:

- primary HTO surface flux;
- HT-derived HTO surface flux;
- combined HTO surface flux;
- HT/T2 source species;
- source kind;
- provenance ID;
- spatial support.

This preserves the evidence needed by E3 to distinguish primary atmospheric HTO from HTO generated after HT deposition.

### 6. Conservation ledger

Every conversion result exposes:

`HT input - generated HTO - residual HT = 0`.

For the recoverable Eq. (1)/(2) path, residual HT is exactly zero and generated HTO equals HT input activity. The generated HTO flux must integrate over the E1 interval to the generated HTO amount.

### 7. Time ownership

The E1 conversion interval and the soil forcing interval must match exactly, and the soil forcing timestamp must equal the E1 interval start. Mismatches fail closed rather than being interpolated or silently repartitioned.

### 8. Explicitly excluded scope

E2 does not implement:

- E3 HTO re-emission/secondary atmospheric feedback;
- atmospheric HT oxidation;
- real CTEAS-Atmos HT binding;
- production HT deposition parameter selection;
- calibration or empirical validation;
- original UFOTRI numerical-discretization or executable equivalence.

## Qualification

The E2 machine/pytest gates must verify:

- Eq. (1)/(2) direct HT-deposition-to-soil-HTO identity;
- exact 1:1 activity conservation and zero residual soil HT;
- one-hour versus four-quarter-hour partition additivity;
- HT and T2 upstream species/provenance retention;
- additive primary-HTO + HT-derived-HTO projection;
- entry into existing L1 HTO inventory and soil global balance closure;
- no direct L2/L3 injection;
- no invented microbial half-time/conversion fraction;
- benchmark values remain evidence-only;
- no atmospheric oxidation, E3 re-emission, real Atmos binding or production activation;
- interval/timestamp/type errors fail closed.

## Consequences

If exact-head CI, locked-head merge and post-merge no-drift pass, the scoped claim may become:

`UFOTRI_HT_TO_HTO_SOIL_CONVERSION=COMPLETE`

This means only the recoverable manual E1→soil-HTO conversion boundary and its conservation/provenance projection are closed. It does not close E3 secondary HTO re-emission, E4 real atmospheric HT transport, calibration, empirical validation, physical accuracy, production readiness or original-executable equivalence.
