# Parameter Database Future Extensions

This document records the P5.2 capability audit of the P5.1 migration layer.
It is an architecture decision boundary, not a schema change. The existing
schema and validator are unchanged.

## Capability matrix

| Parameter form | Current P5.1 support | Readiness disposition |
| --- | --- | --- |
| Scalar | `value` with unit and lifecycle metadata | Supported |
| Range or bounds | `valid_range`/bounds with semantic validation | Supported |
| Unit | Required or checked against a module expectation | Supported |
| Source | Source type, reference, and registry metadata | Supported |
| Provenance | Migration audit, source metadata, and package hash | Supported |
| Table | No typed array/table value contract | Not supported |
| Time dependent | No time-indexed value or interpolation contract | Not supported |
| Crop dependent | No crop-keyed parameter dimension | Not supported |
| Growth-stage dependent | No growth-stage dimension or transition contract | Not supported |
| Function parameter | No serializable function/formula contract | Not supported |

## UFOTRI form audit

Potential future UFOTRI inputs include daytime/nighttime stomatal resistance,
boundary-layer or exchange coefficients, OBT formation rates, and soil
transfer coefficients. Their likely shapes are not all scalar:

```yaml
type: table
dimensions: [crop, growth_stage, temperature]
```

This is an example of a future value shape, not a parameter value or a change
to the current schema. The current database can carry a scalar declaration
and provenance seam, but cannot safely represent the table dimensions,
interpolation policy, missing-cell policy, or function dependencies needed for
such a parameter.

## Recommendation

Before importing any UFOTRI parameter set, introduce a versioned typed-value
extension or a separate validated table/function package. That extension must
define dimensions, units per axis, interpolation/extrapolation, applicability,
provenance, and fail-closed behavior. P5.2 deliberately creates no such
schema, no table, and no numerical UFOTRI entry.
