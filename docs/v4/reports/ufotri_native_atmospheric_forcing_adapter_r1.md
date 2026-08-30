# UFOTRI Native Atmospheric Forcing Adapter R1

Stage: `UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1`

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Base: `main@297bd85500f268cc0114f9f41b3904a8a66ca5ee`

## 1. Scope

H3 connects the already reconstructed UFOTRI-native atmosphere to the existing environmental forcing contracts. It adds no new dispersion, chemistry, soil or biological model.

Implemented path:

`NativePrimaryTransportResult(HT)`
→ `AtmosphericHTForcing(source_kind=UFOTRI_NATIVE)`
→ `HTSoilDepositionBoundary`
→ existing E2 `convert_deposited_ht_to_soil_hto`

and:

`NativePrimaryTransportResult(HTO)`
→ existing P7 `AtmosphericHTOForcing`.

## 2. Provenance correction

The historical E1 source-kind vocabulary had only `SYNTHETIC`, `REPLAY`, and `REAL_CTEAS_ATMOS`. Using any of those for the newly reconstructed standalone UFOTRI atmosphere would be semantically wrong. H3 therefore adds one source kind only:

`UFOTRI_NATIVE = "ufotri_native"`

The existing `REAL_CTEAS_ATMOS` fail-closed behavior is unchanged.

## 3. HT mapping and E2 handoff

Native HT air concentration and native dry surface flux are copied without numerical conversion into the reviewed E1 fields. The E1 interval integration produces deposited HT activity. H3 then calls the existing E2 conversion implementation, which maps the effective deposited HT activity 1:1 to soil HTO under the already-qualified KfK 4605 Eq. (1)-(2) semantics.

H3 does not introduce a soil-HT kinetic pool, oxidation rate, conversion fraction, or production parameter.

## 4. HTO mapping and wet-deposition boundary

The native H1 result exposes local air concentration and dry surface flux plus atmospheric dry/wet source-loss ledger terms. The wet source-loss term is not dimensionally or spatially interchangeable with a receptor surface flux.

Therefore:

- dry-only native HTO maps directly to P7 deposition flux;
- if native wet source loss is nonzero, the adapter requires an explicit local wet surface deposition flux;
- without that flux the adapter fails closed;
- H3 records plume wet source loss and local wet surface flux separately and does not claim source-loss-to-ground-area spatial closure.

This prevents double counting and prevents a Bq/s plume loss from being silently relabelled as Bq m^-2 s^-1.

## 5. Ancillary meteorology

The existing P7 HTO forcing requires temperature, relative humidity, wind speed and precipitation. H1/H2 do not own every one of those fields. `NativeForcingContext` therefore requires all ancillary values, interval support, sampling height, SHA-256 artifact provenance and spatial support explicitly. H3 performs no meteorological inference or fallback.

## 6. Chemical boundary

HT and HTO remain separate typed paths. H3 rejects any native result that reports nonzero atmospheric HT→HTO generation. This preserves the KfK 4605 Section 2.2 decision that atmospheric conversion is disabled on the manual-fidelity path.

## 7. Qualification

Focused tests cover native HT → E1 identity mapping; `UFOTRI_NATIVE` provenance; retained CTEAS-Atmos fail-closed behavior; E1 deposited HT → E2 HTO activity closure; native HTO → P7 identity mapping; wet-source-loss fail-closed behavior; explicit wet surface flux added exactly once; crossed HT/HTO adapter rejection; atmospheric HT→HTO generation rejection; interval/provenance validation; and absence of H4 wake/lift/plume-rise ownership.

Expected machine result:

`PASS_UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER`

## 8. Non-claims

H3 does not establish KfK 5194 washout coefficients as active H4 physics, original MUSEMET source-depletion numerical equivalence, building-wake equivalence, thermal-lift/plume-rise equivalence, CTEAS-Atmos binding, production readiness, calibration, empirical validation, or original UFOTRI executable numerical equivalence.

After exact-head CI, locked merge and no-drift audit, the roadmap may mark H3 complete and authorize H4.
