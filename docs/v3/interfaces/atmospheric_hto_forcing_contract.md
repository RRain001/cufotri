# Atmospheric HTO Forcing Contract

Status: `V3-P5.3_INTERFACE_FROZEN`; interface only, no UFOTRI physics
implementation.

## Canonical boundary

The UFOTRI modules receive one opaque `AtmosphericHTOForcing` record. The
record is the only atmospheric input boundary visible to UFOTRI physics. The
upstream producer and its numerical method are outside this interface.

The canonical payload is:

| Field | Required | Unit and validation |
| --- | --- | --- |
| `time` | Yes | Timezone-aware UTC timestamp |
| `air_hto_concentration` | Yes | HTO activity concentration, Bq/m3; finite and non-negative |
| `air_temperature` | Yes | Absolute air temperature, K; finite and positive |
| `relative_humidity` | Yes | Fraction in [0, 1]; finite |

The field names above are frozen. `air_concentration_bq_m3`,
`temperature_k`, and other aliases are not part of the V3 P5.3 payload.

## Optional fields

Optional values are present only when the producer has a valid value. They
must not be silently defaulted, nearest-time repaired, or converted from an
unrelated field.

| Field | Unit and semantics |
| --- | --- |
| `precipitation` | Precipitation rate, m/s; finite and non-negative |
| `shortwave_radiation` | Downward shortwave radiation, W/m2; finite and non-negative |
| `longwave_radiation` | Net longwave radiation at the declared interface, W/m2; finite, with the sign convention recorded in provenance |
| `wind_speed` | Wind speed, m/s; finite and non-negative |
| `boundary_layer_height` | Boundary-layer height, m; finite and positive when present |
| `surface_deposition_flux` | Externally supplied HTO deposition flux, Bq/m2/s; finite and non-negative |

If a physics kernel requires an optional field and it is absent, the kernel
must return a declared `FAIL_CLOSED` outcome. If the kernel does not require
the field, absence remains explicit and no substitute is inferred. Required
field absence, non-finite values, invalid units, and invalid ranges are always
`FAIL_CLOSED`.

## Time continuity

Each record carries a UTC timestamp. A forcing sequence must be strictly
increasing, contain no duplicate timestamps, and use the declared case
cadence without gaps. The cadence is case metadata, not a hidden default in
the UFOTRI module. A missing sample or an unexpected interval is rejected
before the physics kernel runs.

## Provenance envelope

The forcing record is accompanied by opaque provenance metadata:

| Metadata | Requirement |
| --- | --- |
| `source_id` | Non-empty identifier for the source artifact or adapter |
| `source_version` | Producer/adapter version string |
| `artifact_sha256` | SHA-256 of the source artifact or manifest |
| `spatial_reference` | Declared location/grid identifier and coordinate convention |
| `temporal_resolution_s` | Positive declared source resolution in seconds |

UFOTRI may record this metadata for reproducibility, but it must not branch on
the producer identity or method. Provenance is not a license to infer missing
physics fields.

## Producer independence

UFOTRI must not know whether the producer is Gaussian, CALPUFF, CTEAS-Atmos,
ERA5, an observation adapter, or a test fixture. Those systems are upstream
adapters and must publish the same canonical record. No producer-specific
field, conversion, or fallback is permitted in the UFOTRI module.

## P6 entry criteria

P6 must implement the record only after freezing serialization, location/grid
semantics, concentration averaging period, optional-field missingness, unit
conversion ownership, and the relationship between air concentration and
surface deposition. P5.3 adds no production record class or conversion code.
