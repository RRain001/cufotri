# RC1 activity propagation protocol

Every formal V2 result row reports:

```text
external_stack_input_bq
dry_plume_loss_bq
wet_plume_loss_bq
dry_surface_input_bq
wet_surface_input_bq
environmental_inventory_bq
harvested_activity_bq
milk_activity_bq
beef_activity_bq
excreted_activity_bq
deep_loss_bq
runoff_bypass_bq
decay_loss_bq
activity_residual_bq
```

The Gaussian plume is steady and has no stored air inventory.
`external_stack_input_bq` is the time-integrated stack release.
`dry_plume_loss_bq` and `wet_plume_loss_bq` are plume-side removals; their
corresponding surface inputs must match exactly. The remaining plume source is
not treated as a dynamic inventory.

`environmental_inventory_bq` is the current surface soil, whole/edible plant,
animal, and stored beef activity over `activity_accounting_area_m2`.
Harvested/cut plant, milk, consumed beef, excretion, deep loss, runoff bypass,
and decay are explicit diagnostics. `accounted_environmental_activity_bq`
also includes other surface boundaries such as re-emission, transpiration,
leaf release, and harvest loss.

The ecological residual cancels internal feed and animal-to-beef transfers:

\[
R=I_{\rm surface}+I_{\rm animal,external}
 -M_{\rm soil/plant/animal/product}
 -B_{\rm external}-D.
\]

The accounting area is the dry-deposition footprint. All formal RC1 cases use
equal dry and wet footprints (1,000,000 m2), so plume loss, local flux, and
reported domain activity are directly comparable. A case with unequal
footprints remains a local representative-box calculation and must not
interpret this scaled total as a whole-domain integral.

## Recomputed RC1 evidence

The six end-to-end cases and the two-year pasture case have dry and wet
loss/input ratios exactly 1.0. Their maximum absolute relative activity
residual is `2.30e-15`, and every
`accounted_environmental_activity_bq` is below the integrated stack release.

For the actual 48 h ERA5 plus 24 h deterministic-extension wet case:

```text
external stack input = 3.600000000000e12 Bq
dry plume loss = dry surface input = 3.236040597510e9 Bq
wet plume loss = wet surface input = 2.763990574196e10 Bq
environmental/ecological inventory = 1.730270884986e10 Bq
deep loss = 7.535743945580e9 Bq
decay loss = 1.079596278283e7 Bq
activity relative residual = 5.76e-16
```

The pre-remediation dry counterexample was:

```text
dry plume loss = 3.246027849313e9 Bq
independently computed surface input = 2.901284607250e10 Bq
surface/plume ratio = 8.937953529463
```

Immediately after the ledger repair, the same plume loss and surface input
were both `3.246027849313e9 Bq` (ratio 1.0). Later selection of the named wet
parameter set changed the dry/wet competition allocation slightly, producing
the current RC1 dry value above while preserving exact interface equality.
