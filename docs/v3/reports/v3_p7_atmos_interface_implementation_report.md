# V3-P7 atmospheric forcing coupling interface implementation report

Status: PASS

Branch: `codex/v3-p7-atmos-coupling-interface`

Base commit: `0ff463336409e74814d7d676577178b2e3680adc`

## Scope

P7 adds `src/cteas_ufotri/coupling/atmos_v3/` as an isolated, typed
atmospheric forcing interface. The package contains no atmospheric solver,
file-format reader, parameter database lookup, or production activation.

`AtmosphericHTOForcing` is frozen and validates the following required
fields:

| Field | Contract |
|---|---|
| `timestamp` | timezone-aware UTC `datetime` |
| `location` | non-empty location label or `(latitude, longitude)` in degrees |
| `air_hto_concentration` | non-negative `Bq m^-3` |
| `air_ht0_concentration` | immutable spelling alias with the same value |
| `deposition_flux` | non-negative `Bq m^-2 s^-1` |
| `temperature` | positive `K` |
| `humidity` | relative fraction in `[0, 1]`, unit `1` |
| `wind_speed` | non-negative `m s^-1` |
| `precipitation` | non-negative water-equivalent `m s^-1` |
| `source` | non-empty source identifier |
| `provenance` | existing immutable `ForcingProvenance` record |

No required forcing field has a guessed default. Unit tokens are exact and
there is no implicit conversion. `AtmosphericForcingMetadata` separately
records `model_name`, `version`, `grid_definition`, `time_resolution`
(`s`), `source_dataset`, UTC `creation_time`, and `quality_flag`.

## Coupling boundary

The only public adapters are:

```text
AtmosphericHTOForcing -> to_leaf_forcing() -> existing leaf-resistance forcing input
AtmosphericHTOForcing -> to_soil_forcing() -> existing soil deposition forcing input
```

The leaf adapter passes the validated air concentration, temperature,
humidity, wind speed, timestamp, and provenance to the existing leaf
resistance boundary. The soil adapter passes only the validated deposition
flux to the existing `SoilForcing` input. Precipitation remains an explicit
future atmospheric input; P7 does not turn it into hydrology or wet-deposition
calculation.

There is no atmospheric-module edge to TFWT, OBT, root uptake, food transfer,
intake, or dose. Those downstream pathways remain reachable only through
their existing public interfaces and their own stage boundaries.

## Explicit exclusions

- CALMET, CALPUFF, ERA5, WRF, or measured-meteorology readers;
- dispersion, deposition parameterization, hydrology, or precipitation
  partitioning;
- UFOTRI parameter import or active UFOTRI database use;
- production activation, V1/V2 changes, calibration, field validation,
  regulatory assessment, or V3 physics readiness.

The interface is therefore a software coupling contract, not atmospheric or
plant physical validation.
