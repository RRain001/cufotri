# V3 P7.6C-3 Parameter Decision Matrix

The matrix below is the human-readable rendering of
`docs/v3/parameter_evidence/parameter_validation_feasibility.yaml`. It covers
all 26 P7.6C-2 mapping records plus the requested derived `leaf.g_ex` review
item.

| Parameter | P7.6C-2 mapping | Feasibility | Required action |
| --- | --- | --- | --- |
| `dose.dose_coefficient` | DIRECT_MAPPING | NOT_IMPORTABLE | Keep external dosimetry input |
| `food.crop` | DIRECT_MAPPING | NOT_IMPORTABLE | Keep case metadata explicit |
| `food.harvest_fraction` | NO_MAPPING | PHYSICS_REDESIGN_REQUIRED | Redesign food-chain event/continuous mapping |
| `food.tfwt_harvest_fraction` | NO_MAPPING | PHYSICS_REDESIGN_REQUIRED | Redesign TFWT harvest representation |
| `intake.annual_consumption_amount` | DIRECT_MAPPING | NOT_IMPORTABLE | Keep diet input outside physics validation |
| `intake.food_product_mass` | SOURCE_UNAVAILABLE | INSUFFICIENT_INFORMATION | Recover or define product-mass semantics |
| `leaf.crop` | DIRECT_MAPPING | NOT_IMPORTABLE | Keep crop context explicit |
| `leaf.growth_stage` | CONCEPTUAL_ANALOGUE | PHYSICS_REDESIGN_REQUIRED | Define stage-dependent resistance model |
| `leaf.r_a` | DIRECT_MAPPING | VALIDATION_FEASIBLE | Collect matched aerodynamic resistance data |
| `leaf.r_b` | DIRECT_MAPPING | VALIDATION_FEASIBLE | Collect matched boundary-layer resistance data |
| `leaf.r_c` | DIRECT_MAPPING | VALIDATION_FEASIBLE | Collect matched canopy/surface resistance data |
| `obt.daylight_multiplier` | CONCEPTUAL_ANALOGUE | PHYSICS_REDESIGN_REQUIRED | Freeze daylight formation model |
| `obt.kf` | DIRECT_MAPPING | VALIDATION_FEASIBLE_WITH_LIMITATIONS | Freeze biological scope and test first-order formation |
| `obt.kr` | DIRECT_MAPPING | VALIDATION_FEASIBLE_WITH_LIMITATIONS | Freeze return/loss scope and test turnover |
| `obt.nighttime_multiplier` | CONCEPTUAL_ANALOGUE | PHYSICS_REDESIGN_REQUIRED | Freeze nighttime formation model |
| `obt.photosynthetic_activity` | CONCEPTUAL_ANALOGUE | PHYSICS_REDESIGN_REQUIRED | Design photosynthesis coupling |
| `obt.plant_mass` | CONCEPTUAL_ANALOGUE | PHYSICS_REDESIGN_REQUIRED | Freeze plant-mass/hydrogen basis relation |
| `obt.temperature` | NO_MAPPING | PHYSICS_REDESIGN_REQUIRED | Define temperature-dependent OBT equation or exclude |
| `root.k_root` | CONCEPTUAL_ANALOGUE | PHYSICS_REDESIGN_REQUIRED | Redesign root state and layer aggregation |
| `soil.layer_depth` | DIRECT_MAPPING | VALIDATION_FEASIBLE_WITH_LIMITATIONS | Validate selected case geometry |
| `soil.transport_flux` | TRANSFORMABLE_MAPPING | VALIDATION_FEASIBLE_WITH_LIMITATIONS | Freeze boundary orientation and validate flux |
| `soil.tritium_half_life` | DIRECT_MAPPING | VALIDATION_FEASIBLE | Preserve P7.6C-1 validation |
| `soil.water_content` | TRANSFORMABLE_MAPPING | VALIDATION_FEASIBLE_WITH_LIMITATIONS | Freeze water basis, layer, and density convention |
| `tfwt.transformation_flux` | TRANSFORMABLE_MAPPING | VALIDATION_FEASIBLE_WITH_LIMITATIONS | Freeze TFWT inventory basis and validate flux |
| `tfwt.water_content` | DIRECT_MAPPING | VALIDATION_FEASIBLE_WITH_LIMITATIONS | Freeze plant-water basis and validate inventory |
| `tfwt.water_loss_flux` | TRANSFORMABLE_MAPPING | VALIDATION_FEASIBLE_WITH_LIMITATIONS | Freeze water-loss boundary and validate flux |
| `leaf.g_ex` (derived) | DERIVED_QUANTITY | VALIDATION_FEASIBLE | Derive only from reviewed resistance components |

No row in this matrix supplies a numeric value. The two allowed feasibility
classes indicate only that a future validation pathway can be designed; they
do not override the P7.6B candidate gate or create a runtime parameter.
