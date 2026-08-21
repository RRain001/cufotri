# ParameterDatabase UFOTRI Capability Audit

Status: `V3-P5.3_CAPABILITY_FREEZE`; schema unchanged.

This audit evaluates the P5.1 parameter layer as a carrier for a future
UFOTRI database. It does not import UFOTRI values and does not change the
schema, registry, configuration, or physics code.

## Capability matrix

| Capability | P5.1 status | Evidence/disposition |
| --- | --- | --- |
| Scalar | Supported | `ParameterEntry.value` is a finite scalar when activated |
| Unit | Supported | Entry unit is stored and module adapters can require an expected unit |
| Source provenance | Supported | Source type, reference, applicability, confidence, and source registry are retained |
| Hash | Supported | Deterministic package hashing covers entries, migration audit, provenance, and registry metadata |
| Uncertainty | Supported | Scalar or structured uncertainty is carried and finite-checked |
| Table | Not supported | No typed table value, dimensions, or missing-cell policy |
| Crop dependent | Not supported | No crop dimension or applicability-key contract |
| Growth stage dependent | Not supported | No growth-stage dimension or transition/interpolation contract |
| Temperature function | Not supported | No serializable function/formula value contract |
| Interpolation | Not supported | No axis, method, extrapolation, or fail-closed interpolation contract |

P5.1 also supports scalar validity bounds and ordered lifecycle states. These
features do not make a multidimensional or function-valued parameter safe to
use: dimensions, interpolation, applicability, and provenance would still be
undefined.

## UFOTRI database implication

Potential UFOTRI entries such as day/night stomatal resistance, crop- and
growth-stage-dependent transfer factors, temperature-response functions, and
tabulated exchange coefficients cannot be represented faithfully as active
P5.1 scalars. They must remain placeholders until an extension contract is
reviewed.

The current `parameters/databases/ufotri_leaf_exchange.yaml` remains an
interface-only placeholder database. It contains no activated UFOTRI numeric
value.

## Freeze decision

P5.1 is sufficient for scalar, unit, source/provenance, hash, uncertainty,
and lifecycle metadata. It is not sufficient for table, crop-dependent,
growth-stage-dependent, temperature-function, or interpolation semantics.
P6 must select and validate an extension before importing those parameter
forms. P5.3 makes no schema change.
