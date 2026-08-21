# Atmospheric Interface Independent Review

Status: `PASS_WITH_DECLARED_ADAPTER_BOUNDARY`

## Review scope

This review checks whether the frozen V3 `AtmosphericHTOForcing` contract is
complete, dimensionally coherent, time-defined, provenance-aware, and
fail-closed. It also checks whether representative future CTEAS-Atmos outputs
can be consumed without modification.

## Contract findings

The required payload is complete for a normalized scalar forcing sample:

| Field | Frozen contract |
| --- | --- |
| `time` | Timezone-aware UTC timestamp; sequences are strictly increasing and cadence-checked |
| `air_hto_concentration` | Bq/m3, finite and non-negative |
| `air_temperature` | K, finite and positive |
| `relative_humidity` | Fraction in [0, 1] |

Optional precipitation, shortwave radiation, longwave radiation, wind speed,
boundary-layer height, and surface deposition flux have declared units. Missing
optional fields remain explicit. A required-by-kernel optional field produces
`FAIL_CLOSED`; no silent default, nearest-time repair, or missing-to-zero rule
is allowed.

The provenance envelope carries source identity/version, artifact hash,
spatial reference, and temporal resolution. UFOTRI may record provenance but
cannot branch on the upstream producer or numerical method.

## CTEAS-Atmos interoperability matrix

| Potential upstream output | Directly consumable without modification? | Review disposition |
| --- | --- | --- |
| 3D air-concentration field | No | Requires a declared spatial sampling/aggregation adapter that produces one scalar `air_hto_concentration` per contract location and time, retaining grid and averaging provenance |
| Surface concentration | No | No canonical surface-concentration field exists; it must be semantically mapped to a reviewed boundary quantity and must not be overloaded into air concentration or deposition flux |
| Surface deposition flux | Conditional | Direct only when it is a scalar Bq/m2/s value on the same area, location, time basis, and sign convention; otherwise an adapter is required |
| Meteorology | Conditional | Temperature and humidity are required; precipitation, radiation, wind speed, and boundary-layer height are optional. Other producer fields require an adapter or remain unavailable |

Therefore the interface is closed for a normalized forcing record, but raw
CTEAS-Atmos products do not all connect without modification. The required
adapter boundary is an explicit architecture condition, not a physics
implementation.

## Review conclusion

```text
ATMOSPHERIC_CONTRACT = COMPLETE_FOR_NORMALIZED_SCALAR_FORCING
RAW_3D_OUTPUT_DIRECT_COMPATIBILITY = FALSE
ADAPTER_BOUNDARY = REQUIRED
PRODUCER_COUPLING_IN_UFOTRI = FORBIDDEN
```

P6 must freeze the spatial sampling rule, concentration averaging period,
surface-concentration semantics, deposition relationship, and adapter
provenance before a CTEAS-Atmos connector is implemented.
