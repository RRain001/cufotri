# ADR-051: V4 Eq.39 physical-property source decision R2

## Status

Accepted as a source-policy decision, pending exact-head CI and clean merge.

## Context

R1 classified `root_eq39.latent_heat`, `root_eq39.water_density`, and `root_eq39.psychrometric_constant` as `CONDITION_DEPENDENT_PHYSICAL_PROPERTY_SOURCE_REQUIRED`. The controlled Eq.39 implementation already keeps all three values caller-owned and independently provenanced. R2 must decide where those inputs come from without changing Eq.39 itself, introducing Eq.38, adding a thermodynamic solver, or promoting synthetic test values as universal physical constants.

`PRODUCTION_INPUT_PACKET_READY=FALSE`, `FULL_MODEL_PRODUCTION_READY=FALSE`, and `ACTIVE_PARAMETERS=0` remain hard boundaries.

## Decision

Select a deliberately bounded `FAO56_EQ39_REFERENCE_PROPERTY_POLICY_R1` with three distinct source semantics.

### Latent heat

Select:

```text
policy = FAO56_REFERENCE_ET_FIXED_CONVENTION
lambda = 2.45e6 J kg^-1
```

FAO-56 states that latent heat varies with temperature but uses a single `2.45 MJ kg^-1` value in the simplified FAO Penman-Monteith procedure, corresponding to an air temperature of about 20 degC. R2 adopts this value only as a controlled reference-ET model convention for the existing Eq.39 boundary. It is not declared to be a universal or exact latent heat of vaporization.

No temperature-dependent latent-heat submodel is authorized by this decision.

### Water density

Select:

```text
policy = REFERENCE_WATER_DEPTH_CONVERSION_CONVENTION
rho_w = 1000 kg m^-3
```

This value is deliberately treated as a water-depth conversion convention for converting `kg m^-2 s^-1` to `m water s^-1`, not as a claim that real liquid-water density is invariant. IAPWS-95 remains the boundary authority showing that ordinary-water thermodynamic properties, including density, depend on thermodynamic state.

R2 does not authorize an IAPWS-95 runtime solver because that would add complexity without changing the selected UFOTRI Eq.39 source model. Any later decision to replace the reference conversion convention with state-dependent density requires a separate reviewed stage.

### Psychrometric constant

Select:

```text
policy = FAO56_CASE_PRESSURE_DERIVED
```

A fixed `66 Pa K^-1` value is rejected as a production source. FAO-56 defines the psychrometric constant from atmospheric pressure and the same reference latent heat convention. Under the frozen FAO-56 simplification:

```text
gamma_kPa_per_K = 0.665e-3 * P_kPa
gamma_Pa_per_K  = 0.665 * P_kPa
```

The pressure source is fail-closed and follows this precedence:

1. an explicit case mean atmospheric pressure with provenance;
2. otherwise, pressure derived from an explicitly sourced site elevation using FAO-56 Eq.7:

```text
P_kPa = 101.3 * ((293 - 0.0065*z_m)/293)^5.26
```

where `z_m` is site elevation above mean sea level.

There is no silent sea-level fallback. `P=101.3 kPa`, `z=0 m`, or `gamma=66 Pa K^-1` cannot be inserted merely because the case source is missing.

## Source-resolution meaning

R2 resolves the source policy, not the production case packet:

- latent heat: source policy resolved, fixed model convention selected, not runtime-activated;
- water density: source policy resolved, fixed conversion convention selected, not runtime-activated;
- psychrometric constant: derivation policy resolved, but the case-specific value remains unavailable until pressure/elevation provenance is supplied.

The existing manifest is intentionally not edited in R2. Source-policy resolution must not be confused with `production_use_authorized=true`.

## External Atmos boundary

The decision has no effect on `atmosphere.surface_deposition_flux` or `soil_three_layer.surface_deposition_flux`. Both remain blocked by `BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED`, and `REAL_CTEAS_ATMOS_BINDING=FALSE` remains frozen.

## Rejected alternatives

- `FIX_ALL_THREE_TO_SYNTHETIC_TEST_VALUES`: rejected because test values are not source evidence.
- `IAPWS_RUNTIME_PROPERTY_SOLVER`: rejected for R2 because it adds a new thermodynamic implementation not required by the selected UFOTRI/FAO reference Eq.39 policy.
- `FIX_GAMMA_66_PA_K`: rejected because gamma is location-pressure dependent in FAO-56.
- `SEA_LEVEL_PRESSURE_FALLBACK`: rejected because it would silently replace missing case provenance.

## Next stage

After clean merge, proceed only to `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R3`, focused on `EQ39_CASE_PRESSURE_AND_SITE_ELEVATION_SOURCE_CONTRACT_ONLY`. R3 may define how case pressure/elevation provenance is represented and projected into the production-case source packet. It must not change Eq.39 physics, activate Eq.38, add full hydrology, implement Leaf R5, redesign OBT, calibrate parameters, bind real CTEAS-Atmos data, or make physical-accuracy claims.
