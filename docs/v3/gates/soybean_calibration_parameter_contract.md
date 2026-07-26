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

## Executable frozen-contract representation

The formal V3 evidence gate accepts only `parameter_contract`; the legacy
`parameter_set` list has no production authority. Parameter order has no
semantic meaning. Names are case-sensitive ASCII and must match:

```text
^[a-z][a-z0-9_]*$
```

Each parameter is frozen as:

```yaml
parameter_contract:
  - name: turnover_rate
    unit: s-1
    lower_bound: 0.0
    upper_bound: 1.0e-6
    lower_inclusive: true
    upper_inclusive: true
    transform: IDENTITY
```

Allowed transforms are `IDENTITY`, `LOG`, `LOG10`, and `LOGIT`. The gate
rejects duplicate names, unknown fields, missing units, non-finite bounds,
reversed/empty intervals, and dynamic expressions.

The canonical contract is sorted by parameter name before hashing. A
calibration artifact must provide every frozen parameter exactly once:

```yaml
parameters:
  turnover_rate:
    value: 1.78e-9
    unit: s-1
    transform: IDENTITY
```

Names, units, transforms, values, and inclusive/exclusive bounds are checked
semantically before `parameter_result_hash` is computed. Identifiability must
report every frozen name, and holdout must carry the same contract hash,
canonical parameter hash, and full parameter mapping.
