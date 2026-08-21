# ParameterDatabase Independent Stress Review

Status: `CAPABILITY_LIMITED_NOT_UFOTRI_READY`

## Required UFOTRI capability matrix

| Capability | P5.1 result | Review finding |
| --- | --- | --- |
| Scalar parameter | Supported | Finite scalar values, lifecycle, bounds, and unit metadata are represented |
| Table parameter | Not supported | No typed table, axes, cells, or missing-cell policy |
| Crop-specific parameter | Not supported | No crop dimension or crop applicability key |
| Growth-stage parameter | Not supported | No growth-stage dimension or transition semantics |
| Unit conversion | Not supported | Units are stored and checked for exact equality; no conversion engine or conversion provenance exists |
| Uncertainty/provenance | Supported | Uncertainty, source metadata, references, applicability, and source registry are retained and validated |
| Deterministic hash | Supported | Package hash covers parameter and provenance/migration content |
| Temperature function | Not supported | No serializable function/formula representation |
| Interpolation | Not supported | No axis, method, extrapolation, or fail-closed out-of-domain policy |

## Stress example

The following prospective parameter cannot be safely activated in P5.1:

```text
crop = soybean
growth_stage = flowering
parameter = stomatal resistance
dependence = temperature
```

It requires at least crop and growth-stage dimensions, a temperature axis or
function, unit conversion semantics if source units differ, interpolation and
extrapolation policy, and complete provenance for the source table/function.
P5.1 can retain a scalar declaration and provenance seam, but cannot represent
this value without losing those semantics.

## Schema and disposition

The current P5.1 schema is unchanged. The existing UFOTRI database remains
placeholder-only and contains no activated UFOTRI value. ADR-011 is the only
permitted response to the capability gap at this stage; P6 must review and
validate a typed extension before importing table/function values.

```text
PARAMETER_DATABASE_FULL_UFOTRI_READY = FALSE
PARAMETER_SCHEMA_CHANGED = FALSE
UFOTRI_VALUES_IMPORTED = FALSE
FAIL_CLOSED_ON_UNSUPPORTED_FORM = REQUIRED
```
