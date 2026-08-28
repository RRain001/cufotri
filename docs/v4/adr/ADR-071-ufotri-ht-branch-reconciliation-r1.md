# ADR-071 — UFOTRI HT branch reconciliation R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_HT_BRANCH_RECONCILIATION_R1`

## Context

Phase D closed the recoverable HTO food-chain and public-exposure semantics. Phase E now restores the gaseous-tritium branch that the formal minimal HTO core intentionally excluded.

The existing V4 atmospheric exchange contract is explicitly HTO-only. It forbids HT, T2, total tritium or an unspecified mixture from being passed through `air_hto_concentration` without a separately reviewed species-conversion contract. The retained `AtmosphericHTOForcing` likewise contains HTO concentration and HTO deposition only.

KfK 4605, however, models the two chemical forms separately. The manual states that:

- gaseous tritium is represented as HT/T2;
- HT deposition depends on soil type and soil moisture;
- deposited HT is rapidly transformed into HTO by microorganism activity;
- only the transformed part remains in the soil;
- HTO re-emission then becomes important for HT releases;
- the benchmark parameter set used HT dry deposition `0.05 cm/s`, atmospheric oxidation `0.5 %/d`, and HT soil diffusion `5.0e-2 cm2/s`;
- those benchmark values are case evidence, not proof of universal production defaults.

The roadmap deliberately splits these responsibilities: E1 owns the typed contract/manual mapping, E2 owns HT→HTO soil conversion, E3 owns HT-derived secondary HTO re-emission, and E4 owns real CTEAS-Atmos HT transport/binding.

## Decision

Add one isolated opt-in source module:

`src/cteas_ufotri/coupling/ht_v4.py`

E1 freezes the following contracts.

### 1. Chemical identity

The manual-replication E1 species set is explicit `HT` or `T2`. HTO, total tritium, unspecified mixtures and DT are not silently normalized into this contract.

This is a manual-fidelity boundary, not a statement that other physical isotopologues cannot exist.

### 2. Atmospheric quantity

`air_ht_concentration_bq_m3` is an atmospheric gaseous-tritium concentration in `Bq m-3`.

It is a distinct field and a distinct type from the frozen HTO forcing.

### 3. Soil-facing deposition quantity

`surface_ht_deposition_flux_bq_m2_s` is a true surface HT deposition flux in `Bq m-2 s-1`.

E1 may integrate that rate over an explicit interval to form a deposited HT boundary inventory in `Bq m-2`. The chemistry remains HT. `converted_to_hto_bq_m2` is required to remain zero in E1.

### 4. Time, space and provenance

Every record is a positive, explicit UTC interval with:

- explicit spatial support;
- concentration sampling height;
- source identity;
- provenance identity;
- explicit source kind.

No timezone conversion, silent interval repair, interpolation or chemistry substitution is authorized.

### 5. Synthetic/replay-only execution in E1

E1 accepts `synthetic` and `replay` forcing.

`real_cteas_atmos` fails closed because real HT atmospheric transport and product binding are owned by E4. This allows E2/E3 internal reconstruction to proceed without waiting on Atmos while preventing a replay fixture from being mislabeled production coupling.

### 6. Benchmark evidence remains inactive

The E1 evidence profile exposes the KfK benchmark values:

- HT dry deposition velocity: `0.05 cm/s = 5e-4 m/s`;
- atmospheric oxidation fraction: `0.005 d-1`;
- HT soil diffusion coefficient: `5e-2 cm2/s = 5e-6 m2/s`.

It also exposes the benchmark HTO comparison values (`1.8 cm/s` dry deposition and `2e-5 cm2/s` soil diffusion) to make the chemical-form distinction machine-visible.

None of these is activated as a global or production parameter by E1.

### 7. Ownership boundary

E1 does not implement:

- atmospheric HT oxidation;
- microbial HT→HTO soil conversion;
- HT-derived HTO re-emission;
- real HT CTEAS-Atmos binding.

These remain E4, E2, E3 and E4 responsibilities respectively.

## Qualification

The E1 machine gate must verify:

- explicit HT/T2 chemical identity;
- correct HT concentration/deposition units;
- exact integration of surface flux to HT areal amount;
- one-hour versus four-quarter-hour deposition partition equivalence;
- zero HTO production in E1;
- separation from `AtmosphericHTOForcing`;
- real CTEAS-Atmos fail-closed behavior;
- manual benchmark values visible but inactive;
- machine-readable E1/E2/E3/E4 ownership;
- invalid species, units, time, negative/NaN/Inf inputs fail closed.

## Consequences

If exact-head CI, locked merge and post-merge no-drift pass, the scoped claim may become:

`UFOTRI_HT_BRANCH_RECONCILIATION=COMPLETE`

This claim means the HT state/unit/interface/manual-mapping contract is closed. It does not mean HT→HTO conversion, HT-derived re-emission, real atmospheric HT transport, calibration, empirical validation, physical accuracy, production readiness or original-executable equivalence are complete.

The next stage after a separate roadmap sync is:

`UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1`.
