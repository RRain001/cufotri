# RC2 activity propagation protocol

Every formal V2 result row reports:

```text
external_stack_input_bq
dry_plume_loss_bq
wet_plume_loss_bq
dry_surface_input_bq
wet_surface_input_bq
dry_area_m2
wet_area_m2
dry_activity_bq
wet_activity_bq
total_deposition_activity_bq
ecological_reference_area_m2
environmental_inventory_bq
environmental_boundary_output_bq
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

`dry_area_m2` and `wet_area_m2` are independent local allocation footprints.
Their local fluxes obey
\(M_d=F_dA_d\) and \(M_w=F_wA_w\). `dry_activity_bq` and
`wet_activity_bq` retain those two components explicitly.

The ecological box uses the independent configured
`ecological_reference_area_m2`. The component Bq inputs are divided by this
reference area before the areal box is advanced, then the box inventory,
boundary, and decay terms are multiplied by the same reference area. Thus:

\[
M_d+M_w=M_{\rm inventory}+M_{\rm boundary}+M_{\rm decay}
\]

without assuming \(A_d=A_w\). `environmental_inventory_bq` is the current
surface soil, whole/edible plant, animal, and stored beef activity on this
reference basis.
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

The configured dry and wet footprints and the ecological reference area all
default to 1,000,000 m2, preserving RC1 results for equal areas. Unequal-area
cases now preserve both pathway activities and close the global Bq ledger.
The spatially uniform footprint and ecological reference area remain
replaceable project assumptions, not site-calibrated geometry.

## Recomputed RC2 evidence

The six end-to-end cases and the two-year pasture case have dry and wet
loss/input ratios exactly 1.0. Their maximum absolute relative activity
residual remains below `1e-12`, and every
`accounted_environmental_activity_bq` is below the integrated stack release.

Combined dry/wet cases with \(A_w/A_d=0.1,1,10\) independently recompute
\(M_d+M_w\) and the ecological inventory/boundary/decay sum; each relative
residual is below `1e-12`. The local wet flux changes inversely with \(A_w\),
while total wet Bq is unchanged.

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
