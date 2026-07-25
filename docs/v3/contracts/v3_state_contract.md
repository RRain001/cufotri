# V3 state contract

Status: `ARCHITECTURE_ONLY`

A state definition contains:

```text
name
physical_medium
activity_form
unit
normalization_basis
area_basis
volume_basis
water_basis
time_basis
is_inventory
is_diagnostic
version
```

`unit` is selected from an explicit activity/dose vocabulary:

| Unit | Meaning |
|---|---|
| `Bq` | total activity inventory |
| `Bq m-2` | activity normalized by declared area |
| `Bq m-3 air` | activity concentration in air |
| `Bq m-3 water` | activity concentration in water |
| `Bq kg-1 fresh` | fresh-mass concentration |
| `Bq kg-1 dry` | dry-mass concentration |
| `Bq L-1` | liquid-volume concentration |
| `Sv` | accumulated effective dose |

An inventory has `is_inventory=true`, one physical medium, and a declared
normalization basis. A diagnostic has `is_diagnostic=true` and cannot be used
as a conserved inventory unless a separate state definition explicitly
promotes it. Area-normalized states must name their area basis; water
concentrations must distinguish liquid volume from bulk material volume.

The machine contract is `schemas/v3/state.schema.json`. Contract examples are
validated by the architecture gate.
