# V3 P7.6D Physics Adoption Decision Report

Date: 2026-08-24
Branch: `codex/v3-p7-6d-physics-adoption-decision`
Baseline: `e27badfe7aabb5a030607e8604c73e0598322a0f`

## Decision summary

```ini
P7_6D_STATUS = PASS_PHYSICS_ADOPTION_DECISION
ALL_FEASIBILITY_ITEMS_REVIEWED = TRUE
CURRENT_V3_MODEL = FROZEN
REDESIGN_ITEMS_IDENTIFIED = TRUE
IMPLEMENTATION_STARTED = FALSE
NEW_VALIDATION_CANDIDATES = 0
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
PHYSICS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
V3_PHYSICS_READY = FALSE
```

The canonical record is
`docs/v3/physics/p7_6d_physics_adoption_decision.yaml`. It reviews all 26
P7.6C-2 mapping records plus the derived `leaf.g_ex` item. No record supplies
a numeric value.

| Decision | Count | P7.6D interpretation |
| --- | ---: | --- |
| `KEEP_CURRENT_V3` | 2 | Retain the current decay role and deterministic `g_ex` derivation |
| `VALIDATE_CURRENT_MODEL` | 9 | Future evidence may test the frozen current equation under explicit contracts |
| `EXTEND_V3_PHYSICS` | 2 | OBT first-order `kf`/`kr` remain scoped reduced-model baselines |
| `REDESIGN_REQUIRED` | 9 | Current representation is insufficient for the target mechanism |
| `DO_NOT_IMPORT` | 4 | Metadata, exposure, and dose roles remain outside environmental physics |
| `WAIT_FOR_EVIDENCE` | 1 | Product-mass semantics are unresolved |

## Complete item review

| Parameter | Feasibility | Adoption | Coupling impact | Priority |
| --- | --- | --- | --- | --- |
| `dose.dose_coefficient` | `NOT_IMPORTABLE` | `DO_NOT_IMPORT` | `NO_IMPACT` | LOW |
| `food.crop` | `NOT_IMPORTABLE` | `DO_NOT_IMPORT` | `NO_IMPACT` | LOW |
| `food.harvest_fraction` | `PHYSICS_REDESIGN_REQUIRED` | `REDESIGN_REQUIRED` | `NUMERICAL_COUPLING_CHANGE_REQUIRED` | HIGH |
| `food.tfwt_harvest_fraction` | `PHYSICS_REDESIGN_REQUIRED` | `REDESIGN_REQUIRED` | `NUMERICAL_COUPLING_CHANGE_REQUIRED` | HIGH |
| `intake.annual_consumption_amount` | `NOT_IMPORTABLE` | `DO_NOT_IMPORT` | `NO_IMPACT` | LOW |
| `intake.food_product_mass` | `INSUFFICIENT_INFORMATION` | `WAIT_FOR_EVIDENCE` | `INTERFACE_ONLY` | MEDIUM |
| `leaf.crop` | `NOT_IMPORTABLE` | `DO_NOT_IMPORT` | `NO_IMPACT` | LOW |
| `leaf.growth_stage` | `PHYSICS_REDESIGN_REQUIRED` | `REDESIGN_REQUIRED` | `INTERFACE_ONLY` | MEDIUM |
| `leaf.r_a` | `VALIDATION_FEASIBLE` | `VALIDATE_CURRENT_MODEL` | `NO_IMPACT` | MEDIUM |
| `leaf.r_b` | `VALIDATION_FEASIBLE` | `VALIDATE_CURRENT_MODEL` | `NO_IMPACT` | MEDIUM |
| `leaf.r_c` | `VALIDATION_FEASIBLE` | `VALIDATE_CURRENT_MODEL` | `NO_IMPACT` | MEDIUM |
| `obt.daylight_multiplier` | `PHYSICS_REDESIGN_REQUIRED` | `REDESIGN_REQUIRED` | `NO_IMPACT` | HIGH |
| `obt.kf` | `VALIDATION_FEASIBLE_WITH_LIMITATIONS` | `EXTEND_V3_PHYSICS` | `NO_IMPACT` | HIGH |
| `obt.kr` | `VALIDATION_FEASIBLE_WITH_LIMITATIONS` | `EXTEND_V3_PHYSICS` | `NO_IMPACT` | HIGH |
| `obt.nighttime_multiplier` | `PHYSICS_REDESIGN_REQUIRED` | `REDESIGN_REQUIRED` | `NO_IMPACT` | HIGH |
| `obt.photosynthetic_activity` | `PHYSICS_REDESIGN_REQUIRED` | `REDESIGN_REQUIRED` | `INTERFACE_ONLY` | HIGH |
| `obt.plant_mass` | `PHYSICS_REDESIGN_REQUIRED` | `REDESIGN_REQUIRED` | `INTERFACE_ONLY` | HIGH |
| `obt.temperature` | `PHYSICS_REDESIGN_REQUIRED` | `REDESIGN_REQUIRED` | `INTERFACE_ONLY` | HIGH |
| `root.k_root` | `PHYSICS_REDESIGN_REQUIRED` | `REDESIGN_REQUIRED` | `NUMERICAL_COUPLING_CHANGE_REQUIRED` | HIGH |
| `soil.layer_depth` | `VALIDATION_FEASIBLE_WITH_LIMITATIONS` | `VALIDATE_CURRENT_MODEL` | `NO_IMPACT` | MEDIUM |
| `soil.transport_flux` | `VALIDATION_FEASIBLE_WITH_LIMITATIONS` | `VALIDATE_CURRENT_MODEL` | `INTERFACE_ONLY` | MEDIUM |
| `soil.tritium_half_life` | `VALIDATION_FEASIBLE` | `KEEP_CURRENT_V3` | `NO_IMPACT` | LOW |
| `soil.water_content` | `VALIDATION_FEASIBLE_WITH_LIMITATIONS` | `VALIDATE_CURRENT_MODEL` | `INTERFACE_ONLY` | MEDIUM |
| `tfwt.transformation_flux` | `VALIDATION_FEASIBLE_WITH_LIMITATIONS` | `VALIDATE_CURRENT_MODEL` | `INTERFACE_ONLY` | HIGH |
| `tfwt.water_content` | `VALIDATION_FEASIBLE_WITH_LIMITATIONS` | `VALIDATE_CURRENT_MODEL` | `INTERFACE_ONLY` | HIGH |
| `tfwt.water_loss_flux` | `VALIDATION_FEASIBLE_WITH_LIMITATIONS` | `VALIDATE_CURRENT_MODEL` | `INTERFACE_ONLY` | HIGH |
| `leaf.g_ex` (derived) | `VALIDATION_FEASIBLE` | `KEEP_CURRENT_V3` | `NO_IMPACT` | MEDIUM |

## Accepted current baseline

The resistance components remain the current V3 resistance chain. Their future
validation must retain the same component roles, units, crop context, canopy
geometry, and meteorological basis. `leaf.g_ex` is derived only from reviewed
components and is not an independent UFOTRI parameter.

The TFWT storage interface remains the current V3 baseline. Future evidence
must declare plant-water basis, areal inventory, rate-versus-flux timing,
water-loss boundary, and transformation boundary. A dimensional
rate-times-inventory relation does not import a UFOTRI rate.

The H-3 radioactive half-life remains the one existing validated physical
constant. This stage preserves the P7.6C-1 record and does not generalize it to
soil retention, plant transfer, or biological turnover.

OBT `kf` and `kr` are retained only as a reduced first-order baseline. Their
future validation must distinguish TFWT, exchangeable/non-exchangeable OBT,
biological scope, day/night state, and equilibrium-derived assumptions. The
`EXTEND_V3_PHYSICS` decision is not an implementation or value-admission gate.

## Blocking redesign findings

The nine `REDESIGN_REQUIRED` records are complete and are not bypassed by
selecting a plausible number:

- OBT daylight/nighttime treatment lacks a normalized state equation.
- OBT photosynthetic activity lacks a V3 forcing or state equation.
- OBT plant mass lacks a fresh/dry/water/hydrogen basis relation.
- OBT temperature lacks an OBT-specific response equation.
- Root `k_root` is a rate/velocity and layer-state mismatch.
- Food harvest fractions are event quantities, while the recovered UFOTRI
  representation is continuous.
- Growth-stage metadata lacks a stage ontology and stage-dependent resistance
  relation.

The priority and proposed sequence are frozen in
`docs/v3/physics/p7_6d_redesign_priority_matrix.yaml` and described in
`v3_p7_6d_redesign_roadmap.md`.

## Scope boundary

Crop identifiers, annual consumption amounts, and dose coefficients remain
explicit scenario/external inputs. The product-mass denominator is held at
`WAIT_FOR_EVIDENCE` until its original definition or an independently governed
contract is available.

P7.6D changes no solver, equation, numerical coupling, configuration default,
parameter value, calibration routine, active database, or production pipeline.
