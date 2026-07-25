# V3 flux contract

Status: `ARCHITECTURE_ONLY`

A flux definition contains:

```text
source_state
destination_state
activity_rate_unit
normalization_area
positive_direction
integration_rule
boundary_or_internal
diagnostic_name
```

Two integration forms are distinct:

\[
Q = \int \dot{Q}\,dt
\]

where \(\dot{Q}\) is an activity rate in `Bq s-1`, and

\[
Q = \int F A\,dt
\]

where \(F\) is an areal activity flux in `Bq m-2 s-1` and \(A\) is the exact
declared normalization area in `m2`. A component cannot substitute one form
for the other or infer \(A\) from an unrelated footprint.

`positive_direction` is defined from source to destination. Internal
transfers must appear with equal integrated activity in the source output and
destination input ledgers. Boundary fluxes identify the modeled-domain
boundary. The machine contract is `schemas/v3/flux.schema.json`.
