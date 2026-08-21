# Parameter Database Extensions: P5.2 audit and P6.1 preparation

P5.2 identified the gap between scalar parameter metadata and the typed values
needed by UFOTRI. P6.1 now prepares that boundary without importing UFOTRI
values or connecting the database to physics.

## Capability matrix

| Parameter form | P6.1 disposition |
| --- | --- |
| Scalar | Existing P0/P5.1 support retained |
| Range or bounds | Existing `valid_range`/bounds support retained |
| Unit, source, provenance, uncertainty | Existing required metadata retained |
| Table | Typed `type: table` metadata, axes, and lookup cells supported |
| Crop dependent | Categorical `crop` dimension supported |
| Growth-stage dependent | Categorical `growth_stage` dimension supported |
| Temperature dependent | Numeric axis with explicit unit, e.g. `K`, supported |
| Humidity dependent | Numeric axis with explicit unit, e.g. `1` for RH, supported |
| Interpolation | `exact` or multilinear `linear` supported |
| Extrapolation | Reject only; no hidden clamp or nearest repair |
| Function parameter | No serializable function/formula contract |

## UFOTRI form audit

Potential UFOTRI inputs include daytime/nighttime stomatal resistance,
boundary-layer or exchange coefficients, OBT formation rates, and soil
transfer coefficients. Their likely shapes are not all scalar:

```yaml
type: table
dimensions: [crop, growth_stage, temperature, humidity]
```

The P6.1 contract adds explicit `dimensions`, per-axis `unit` and `values`,
`lookup_table` cells, and interpolation/extrapolation metadata. Categorical
axes require exact matches. Numeric axes use multilinear interpolation only
when the rectangular grid is complete. Out-of-domain coordinates fail closed.

## Lifecycle and boundary

```text
PLACEHOLDER -> CANDIDATE -> REVIEWED -> VALIDATED -> ACTIVE
```

P6.1 permits preparation and review only. Runtime lookup with `production=True`
requires the existing validated source and parameter checks plus an `ACTIVE`
migration record. The UFOTRI source identifier remains reserved and
`production_allowed: false`; no UFOTRI numerical table is present.

The source classification and missing-input inventory are recorded in
`docs/v3/ufotri_database/ufotri_database_source_audit.md`.
