# V4 system physics-gap and sensitivity audit R1 review

Status: `READY_FOR_EXACT_HEAD_CI`

Branch: `codex/v4-system-physics-gap-sensitivity-audit-r1`

Base main: `ae315f9e3f1108c9e527508728e28a6fbbce75e7`

## Scope

This stage is a structural system audit and numerical-screening preregistration only. It changes no production source and reports no empirical uncertainty ranking.

The audit reconciles the existing P7.6 parameter-feasibility records with the actual frozen V3/V3.1 call graph. The existing feasibility registry contains 26 mapped parameters and 27 assessment records: 4 validation-feasible, 8 validation-feasible-with-limitations, 9 physics-redesign-required, 4 not-importable, 1 insufficient-information, and only the H-3 radioactive half-life validated. Those evidence labels are retained rather than replaced.

## Main correction to earlier priority records

Earlier redesign priorities identify scientific importance, but they are not numerical sensitivity results. R1 separates:

- physical/evidence gap;
- whether the current runtime has an equation for the quantity;
- how far the quantity can propagate in the current operator ordering;
- whether an end-to-end perturbation is legal without changing model semantics;
- whether a numerical response can be interpreted physically.

No weighted composite importance score is used.

## High-value structural findings

1. **Atmospheric concentration** directly enters current leaf exchange and is eligible for replay/synthetic screening.
2. **Atmospheric surface deposition flux** directly changes soil, but root reads step-start soil, so its plant/OBT/dose effect is delayed across intervals. Real CTEAS-Atmos surface-flux binding remains unconfirmed.
3. **Temperature, RH, wind and precipitation are currently co-forcings without direct numeric influence** when concentration, deposition and precomputed resistance are held fixed. The current leaf equation does not dynamically recalculate resistance from those fields.
4. **Leaf `r_a/r_b/r_c` are runnable**, but the current equation depends on their sum. Screen total resistance first; component-specific ranking requires component-specific uncertainty evidence.
5. **Soil transport flux and TFWT water-loss/transformation flux are not integrated into `V3PipelineRunner`**. They cannot receive an end-to-end sensitivity score without a separate integration decision.
6. **Soil water content is basis-sensitive** because root uptake uses `C_soil = M_soil / W_soil`; any perturbation must declare whether inventory or concentration is held fixed.
7. **Root `k_root` is runnable but is still a provisional one-layer abstraction**. A large numerical response would justify layered root/soil redesign priority, not validate the m/s coefficient.
8. **OBT `kf/kr` are runnable with evidence limitations**. Current day/night multipliers are also runnable placeholders, but remain physics-redesign-required.
9. **OBT temperature, photosynthetic activity and growth-stage fields are inactive in the current OBT equation**; no sensitivity to a missing mechanism will be fabricated.
10. **TFWT water content and OBT plant mass are diagnostic/basis denominators at fixed inventory**. Current downstream OBT/food arithmetic consumes inventories, so they are structural-zero controls for the declared activity-dose path.
11. **Food harvest fractions are runnable endpoint abstractions**, while continuous food kinetics remain redesign-required.
12. **Consumption amount, food mass and dose coefficient are external endpoint arithmetic**. Their exact linear/inverse-linear dose scaling is kept outside environmental-physics prioritization.

## Numerical screening preregistration

The next stage is `V4_SYSTEM_SENSITIVITY_SCREENING_EXECUTION_R1`. It will use synthetic/replay forcing and existing public APIs only.

Required safeguards:

- multi-step execution to expose delayed soil/root effects;
- separate OBT-only and TFWT-inclusive endpoint profiles;
- explicit day/night sequence for multiplier identifiability;
- final soil/TFWT/OBT/food/intake/dose outputs plus ledgers;
- finite-difference step-convergence check before reporting local elasticities;
- no log elasticity for zero baselines;
- no arbitrary empirical uncertainty ranges;
- no global Monte Carlo/Sobol analysis until reviewed ranges/distributions exist;
- external scenario scalings reported separately;
- all results labeled synthetic/replay software sensitivity, not physical validation.

## Current subsystem disposition

```text
Atmosphere      -> ADVANCE_NUMERICAL_SCREENING; real surface-flux binding still blocked
Soil            -> KEEP one-layer baseline for screening; three-layer implementation HOLD
Leaf            -> ADVANCE current resistance screening; dynamic stomatal R4 remains HOLD
TFWT            -> KEEP current; non-integrated loss terms HOLD
OBT             -> ADVANCE kf/kr and baseline multiplier screening; mechanisms HOLD redesign
Root            -> ADVANCE current-abstraction screening; layered water-flux implementation HOLD
Food            -> ADVANCE endpoint-abstraction screening; continuous kinetics HOLD redesign
Intake/Dose     -> KEEP_EXTERNAL_GOVERNANCE
```

## Exit state

```ini
V4_SYSTEM_PHYSICS_GAP_SENSITIVITY_AUDIT_R1 = PASS_STRUCTURAL_AUDIT
NUMERICAL_SENSITIVITY_RESULTS = NOT_YET_EXECUTED
PHYSICAL_UNCERTAINTY_RANKING = NOT_AVAILABLE
SOLVER_CHANGES_AUTHORIZED = FALSE
NUMERICAL_COUPLING_CHANGES_AUTHORIZED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
V3_PHYSICS_READY = FALSE
NEXT_STAGE = V4_SYSTEM_SENSITIVITY_SCREENING_EXECUTION_R1
```

Exact-head CI must pass the portable suite and the new audit-governance tests before merge.
