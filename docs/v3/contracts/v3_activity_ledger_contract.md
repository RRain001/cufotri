# V3 activity-ledger contract

Status: `ARCHITECTURE_ONLY`

Every future numerical module returns:

```text
external_input_bq
internal_input_bq
internal_output_bq
boundary_output_bq
decay_bq
final_inventory_bq
numerical_residual_bq
relative_residual
```

All values are cumulative over the declared interval and non-negative except
the signed `numerical_residual_bq`. The required identity is:

\[
r =
I_\mathrm{external} + I_\mathrm{internal}
- O_\mathrm{internal} - O_\mathrm{boundary}
- D - S_\mathrm{final}.
\]

`numerical_residual_bq` equals \(r\). `relative_residual` divides its absolute
value by the maximum of total entering activity, final inventory plus all
outputs and decay, and a declared absolute floor.

Internal transfers are also reconciled globally by transfer ID. Therefore a
module can pass locally while the system still fails if source and destination
areas, time windows, units, or activity differ. The machine schema is embedded
as `$defs.activity_ledger` in `schemas/v3/result.schema.json`, and the
architecture verifier validates a closed example.
