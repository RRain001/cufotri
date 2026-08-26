# ADR-027 — V4 system atmospheric exchange contract

## Status

Accepted for control-plane contract review.

## Context

The V4 system roadmap reset makes the CTEAS-Atmos to CTEAS-UFOTRI exchange contract the next project stage. The current V3 consumer already accepts a typed `AtmosphericHTOForcing` carrying air HTO concentration, one deposition flux, temperature, relative humidity, wind speed, precipitation, location, time and provenance. P7.5/P7.5B freeze the forcing timestamp as the interval-start label for values representative of the complete model interval.

A read-only compatibility audit was performed against CTEAS-Atmos revision `341d9d6b3b45b6e2416e09aec0b381adf137fd3e`. Its core time contract uses UTC and half-open intervals `[start,end)` with explicit temporal meaning. Its receptor concentration contract publishes radionuclide concentration in `Bq/m^3`. Its Stage18 deposition/activity ledger, however, owns per-puff/per-interval removal amounts in Bq and explicitly distinguishes those amounts from receptor or surface deposition flux products. Therefore a Stage18 dry/wet removal amount must never be relabeled as the `Bq m^-2 s^-1` soil forcing consumed by CTEAS-UFOTRI.

The goal of this ADR is to freeze the producer/consumer semantics now, without waiting for the CTEAS-Atmos solver roadmap to finish and without changing the current UFOTRI runtime.

## Decision

### 1. Exchange record and time semantics

One exchange record represents one spatial support over one positive half-open UTC interval:

```text
[start_utc, end_utc)
```

The normalized exchange values are interval-representative means or rates. The current V3 adapter mapping is frozen as:

```text
AtmosphericHTOForcing.timestamp = start_utc
```

No implicit local time, nearest-time substitution, silent resampling, or interval-boundary repair is allowed.

### 2. Chemical identity

This contract is for atmospheric **HTO** forcing only. `HT`, `DT`, `T2`, total tritium, or an unspecified tritium mixture cannot be supplied as `air_hto_concentration` without a separate reviewed species-conversion/model contract.

### 3. Required normalized quantities

Each accepted exchange record must provide:

- air HTO concentration: `Bq m^-3`;
- total surface deposition flux of HTO: `Bq m^-2 s^-1`;
- air temperature: `K`;
- relative humidity: dimensionless fraction `[0,1]`;
- horizontal wind speed: `m s^-1`;
- precipitation rate: `m s^-1`;
- explicit spatial support, sampling height/reference, interval, quality state and provenance.

The meteorological quantities are co-forcings. They may originate from the accepted CTEAS-Atmos meteorological input dataset or another explicitly reviewed aligned source; CTEAS-Atmos need not numerically derive them. Their source and transformation lineage remain explicit per record.

### 4. Concentration spatial support

The air concentration must be a typed receptor or grid-support concentration product with explicit vertical sampling support. A ground-level label without sampling-height semantics is insufficient. The producer must preserve the relevant receptor/grid identity and vertical reference so the consumer can prove that the HTO concentration and meteorological co-forcings are co-located or explicitly reconciled.

### 5. Deposition product boundary

The soil-facing quantity is a true **surface deposition flux** in `Bq m^-2 s^-1`.

Allowed normalized forms are:

1. a directly produced total surface deposition flux; or
2. an explicitly derived total equal to separately supplied dry and wet surface flux components, with the derivation and input variables recorded.

The following are explicitly forbidden substitutes:

- Stage18 `dry_deposited` or `wet_deposited` ledger amounts in Bq;
- puff inventory loss divided by an inferred or hidden area;
- accumulated deposition in `Bq m^-2` relabeled as a rate;
- a dry or wet removal coefficient relabeled as flux;
- silent zero substitution when a surface-flux product is unavailable.

If no valid surface deposition flux product exists for an interval, the real CTEAS-Atmos binding fails closed. Replay or synthetic records may still be used for software testing when labeled accordingly.

### 6. Provenance and quality

Each record must preserve producer model/revision, source dataset, immutable artifact identity where applicable, source-variable mapping, spatial support, time basis, units and any explicit transformation log. Synthetic and replay sources must remain distinguishable from real CTEAS-Atmos production output.

Missing required values, NaN/Inf, ambiguous units, ambiguous species, ambiguous temporal meaning, or ambiguous spatial support fail closed. No automatic interpolation, forward fill, zero fill, clipping, unit conversion or chemistry conversion is authorized by this contract.

### 7. Compatibility with the frozen V3 consumer

This stage does not modify `src/cteas_ufotri/coupling/atmos_v3`.

A future adapter may map a validated exchange record to the existing V3 fields as follows:

```text
start_utc                         -> timestamp
air_hto_concentration_bq_m3      -> air_hto_concentration
surface total deposition flux    -> deposition_flux
air_temperature_k                -> temperature
relative_humidity                -> humidity
wind_speed_m_s                   -> wind_speed
precipitation_rate_m_s           -> precipitation
location/spatial support         -> location + provenance/metadata
```

Any adapter implementation is a later software stage. This control-plane contract does not activate real CTEAS-Atmos coupling.

### 8. Cross-project binding state

The CTEAS-Atmos snapshot demonstrates compatible time semantics and receptor concentration quantity semantics. It does **not** yet establish that a production surface deposition flux product matching this contract is available and frozen. Therefore:

```text
CONTRACT_DEFINITION = FROZEN
CTEAS_ATMOS_CONCENTRATION_SEMANTICS = COMPATIBLE
CTEAS_ATMOS_TIME_SEMANTICS = COMPATIBLE
CTEAS_ATMOS_SURFACE_DEPOSITION_FLUX_BINDING = BLOCKED_UNCONFIRMED
REAL_CTEAS_ATMOS_COUPLING = NOT_ACTIVE
```

This is a deliberate fail-closed result, not a failure of the exchange contract.

## Next stage

With the consumer-facing exchange semantics frozen, the roadmap may proceed to `V4_SYSTEM_PHYSICS_GAP_SENSITIVITY_AUDIT`. That audit must use replay/synthetic forcing where needed and must not treat the blocked real Atmos binding as completed physical validation.

```ini
V4_SYSTEM_ATMOS_EXCHANGE_CONTRACT = PASS_CONTROL_PLANE_CONTRACT_FROZEN
V3_ATMOS_RUNTIME_CHANGED = FALSE
CTEAS_ATMOS_REFERENCE_SHA = 341d9d6b3b45b6e2416e09aec0b381adf137fd3e
PUFF_LEDGER_AMOUNT_AS_SURFACE_FLUX = FORBIDDEN
REAL_PRODUCER_BINDING = BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED
REAL_CTEAS_ATMOS_COUPLING_ACTIVE = FALSE
SOLVER_CHANGES_AUTHORIZED = FALSE
NUMERICAL_COUPLING_CHANGES_AUTHORIZED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
V3_PHYSICS_READY = FALSE
NEXT_STAGE = V4_SYSTEM_PHYSICS_GAP_SENSITIVITY_AUDIT
```
