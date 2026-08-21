# Atmospheric HTO Forcing Contract

Status: proposed V3 interface; no implementation in P5.2.

## Ownership rule

The V3 UFOTRI modules receive atmospheric HTO as a typed forcing record. They
must not know whether the upstream producer is a Gaussian model, CALPUFF,
CTEAS-Atmos, an observation adapter, or a test fixture. Those producers belong
behind adapters that satisfy this contract and carry their own provenance.

## Proposed record

The conceptual record is `AtmosphericHTOForcing`:

| Field | Required | Unit and contract |
| --- | --- | --- |
| `time` | Yes | Timezone-aware UTC timestamp |
| `air_concentration_bq_m3` | Yes | HTO activity concentration in air, Bq m^-3; finite and non-negative |
| `temperature_k` | Yes | Absolute air temperature, K; finite and positive |
| `relative_humidity` | Yes | Fraction in [0, 1] |
| `precipitation_m_s` | No | Precipitation rate, m s^-1; non-negative when present |
| `radiation_w_m2` | No | Declared radiation quantity, W m^-2; sign and net/shortwave meaning must be fixed by the adapter |
| `boundary_layer_height_m` | No | Boundary-layer height, m; positive when present |
| `deposition_flux_bq_m2_s` | No | Externally supplied deposition flux, Bq m^-2 s^-1; non-negative when present |

The record must preserve source, grid/location, unit, and temporal-resolution
metadata in the surrounding case contract. Missing optional fields must be
represented explicitly rather than silently inferred.

## Current implementation comparison

| Existing source | Available fields | Gap to proposed contract |
| --- | --- | --- |
| V3 P1 `LeafExchangeForcing` | Air HTO, air temperature, relative humidity | No timestamp or optional atmospheric fields; type remains unchanged in P5.2 |
| V3 P2 `SoilForcing` | Air HTO, externally supplied deposition flux | No timestamp or meteorological context; deposition remains an input seam |
| ERA5 hourly adapter | Timestamp, temperature, radiation, precipitation, boundary-layer height when available | Standard meteorology does not provide HTO concentration; it needs an independent HTO adapter |

## Acceptance boundary

P6 must freeze timestamp semantics, location/grid semantics, concentration
averaging period, optional-field missingness, and the relationship between
deposition flux and air concentration. P5.2 adds no record class and no
conversion from meteorological data to HTO forcing.
