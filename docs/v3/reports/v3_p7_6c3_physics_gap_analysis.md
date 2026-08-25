# V3 P7.6C-3 Physics Gap Analysis

This report separates a future evidence path from a missing V3 equation. A
`VALIDATION_FEASIBLE` result is not a validation result, and a
`PHYSICS_REDESIGN_REQUIRED` result must not be worked around by selecting a
plausible number.

## Leaf exchange resistance

`leaf.r_a`, `leaf.r_b`, and `leaf.r_c` are `VALIDATION_FEASIBLE`: UFOTRI and
V3 use the same resistance component roles and `s m^-1` units. A future case
must pair each component with leaf/canopy geometry and meteorology. The
derived `leaf.g_ex` is also feasible only as
`1 / (r_a + r_b + r_c)`; it has no independent UFOTRI value.

`leaf.crop` is `NOT_IMPORTABLE` because it is pathway metadata.
`leaf.growth_stage` is `PHYSICS_REDESIGN_REQUIRED`: the recovered
vegetation-period context does not define the current V3 stage ontology or a
stage-dependent resistance equation.

## TFWT

`tfwt.water_content`, `tfwt.transformation_flux`, and `tfwt.water_loss_flux`
are `VALIDATION_FEASIBLE_WITH_LIMITATIONS`. Their future data must preserve
plant-water basis, areal inventory, rate-versus-flux timing, and water-loss
boundary semantics. The dimensional rate-times-inventory transformations do
not authorize importing a UFOTRI rate.

## OBT

`obt.kf` and `obt.kr` retain the same first-order roles as the current V3
equation and are `VALIDATION_FEASIBLE_WITH_LIMITATIONS`. The future dataset
must distinguish TFWT, exchangeable/non-exchangeable OBT, biological scope,
day/night state, and any equilibrium-derived source assumptions.

`obt.daylight_multiplier` and `obt.nighttime_multiplier` are
`PHYSICS_REDESIGN_REQUIRED` because the recovered day/night statements do not
define a normalized V3 multiplier. `obt.photosynthetic_activity` requires a
photosynthesis equation. `obt.plant_mass` requires a fresh/dry/water/hydrogen
mass-basis relation. `obt.temperature` requires an OBT-specific temperature
response equation. None of these gaps can be closed by renaming a manual
quantity.

## Root uptake

`root.k_root` is `PHYSICS_REDESIGN_REQUIRED`. UFOTRI uses layer-distributed
first-order transfer tied to transpiration and soil hydrogen content; V3 uses a
one-layer effective velocity multiplying soil-water concentration. A rate to
velocity conversion would require a selected storage length and an aggregation
model that are not currently defined.

## Soil

`soil.tritium_half_life` is `VALIDATION_FEASIBLE` and remains the one existing
validated physical constant from P7.6C-1. `soil.layer_depth`,
`soil.transport_flux`, and `soil.water_content` are
`VALIDATION_FEASIBLE_WITH_LIMITATIONS`: future cases must select the layer,
freeze sign/boundary orientation, and declare water mass/volume/depth basis.
The UFOTRI multi-layer hydraulic/diffusive model is not imported by this
assessment.

## Food chain and exposure

`food.harvest_fraction` and `food.tfwt_harvest_fraction` are
`PHYSICS_REDESIGN_REQUIRED`: continuous UFOTRI plant/cow/product rates are not
the current V3 event fractions. `food.crop` is metadata and therefore
`NOT_IMPORTABLE`.

`intake.annual_consumption_amount` is an exposure habit and
`NOT_IMPORTABLE`. `intake.food_product_mass` is
`INSUFFICIENT_INFORMATION` because the original UFOTRI product-mass
definition was not recovered. `dose.dose_coefficient` is
`NOT_IMPORTABLE` from the environmental-physics path because it is an
external/regulatory dose coefficient.

## Gate consequence

Only the 12 mapped records in the first two feasibility classes may be
considered by a future validation workflow. P7.6C-3 itself admits none of
them as a candidate and leaves all active/runtime gates closed.
