# Soybean calibration-parameter contract

Status: `DRAFT_NO_EXECUTABLE_EXTERNAL_CASE`

Calibration is restricted to the smallest leaf/plant parameter subset that the
available observables can support. Bounds remain placeholders until a reviewed
source and complete data package are frozen.

| Candidate parameter | Unit | Prior | Lower bound | Upper bound | Source required | Identifiability risk | Active observable |
|---|---|---|---|---|---|---|---|
| `canopy_resistance_scale` | 1 | positive, centred on 1 | `TO_BE_FROZEN_FROM_SOURCE` | `TO_BE_FROZEN_FROM_SOURCE` | reviewed resistance evidence | compensates boundary-layer scale | plant-water HTO uptake/depuration |
| `boundary_layer_resistance_scale` | 1 | positive, centred on 1 | `TO_BE_FROZEN_FROM_SOURCE` | `TO_BE_FROZEN_FROM_SOURCE` | chamber mixing and leaf geometry evidence | strongly correlated with canopy resistance | early uptake rate |
| `leaf_exchange_area_or_LAI_scale` | 1 | positive, centred on measured LAI | `TO_BE_FROZEN_FROM_MEASUREMENT` | `TO_BE_FROZEN_FROM_MEASUREMENT` | measured leaf area/LAI | amplitude compensation | uptake amplitude |
| `initial_plant_water_activity` | Bq L-1 plant water | observation-informed | `TO_BE_FROZEN_FROM_UNCERTAINTY` | `TO_BE_FROZEN_FROM_UNCERTAINTY` | pre-exposure measurements | confounds early uptake | initial TFWT |
| `turnover_rate` | s-1 | positive literature/source prior | `TO_BE_FROZEN_FROM_SOURCE` | `TO_BE_FROZEN_FROM_SOURCE` | depuration/physiology evidence | correlated with exchange rate | post-exposure depuration |
| `fractionation_factor` | 1 | source-supported only | `TO_BE_FROZEN_FROM_SOURCE` | `TO_BE_FROZEN_FROM_SOURCE` | explicit isotope evidence | weakly identifiable without paired water/vapour data | equilibrium TFWT |

`initial_plant_water_activity` should be fixed from a measured baseline when
available rather than calibrated. `fractionation_factor` is excluded unless a
source and observable directly support it.

The following complete-chain groups must not be adjusted simultaneously:

```text
source
deposition
soil
leaf
OBT
food
dose
```

At most one parameter from a strongly compensating pair may remain free after
profile/Jacobian diagnostics unless independent repeats identify both. Every
active parameter, prior, bound, transform, and source must be frozen in the
preregistration before calibration.
