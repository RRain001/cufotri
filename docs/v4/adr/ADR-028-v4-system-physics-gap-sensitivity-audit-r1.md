# ADR-028 — V4 system physics-gap and sensitivity audit R1

## Status

Accepted for control-plane audit review.

## Context

The system roadmap reset and atmospheric exchange contract are now merged. The runnable V3/V3.1 baseline is intentionally preserved, while most physical quantities remain provisional or externally supplied. Earlier P7.6/P7.8 prioritization correctly identified scientific redesign gaps, but those records did not distinguish three materially different questions:

1. does a quantity actually enter the frozen end-to-end runtime equation;
2. can it be perturbed without inventing a new physical model or changing state basis;
3. is its physical evidence sufficient to interpret a numerical sensitivity as a real uncertainty contribution.

A parameter may be scientifically important yet have no current equation, and a parameter may produce a large direct dose scaling while belonging only to an external exposure scenario. These cases must not be ranked together.

## Decision

The system audit separates **physics gap**, **structural reach**, **current-runtime perturbation eligibility**, and **physical-evidence status**. No combined scalar importance score is created in R1.

### 1. Structural reach classes

The following classes describe the frozen V3/V3.1 runtime only:

- `DIRECT_SAME_STEP`: the quantity can alter a downstream endpoint in the same pipeline interval;
- `DELAYED_MULTI_STEP`: the quantity changes a prognostic state that can affect dose only after a later restart/interval;
- `DIAGNOSTIC_ONLY_FIXED_INVENTORY`: the quantity changes a reported concentration/basis but not the authoritative activity inventory used downstream;
- `PRESENT_BUT_INACTIVE`: the typed field is carried but is not used by the current equation;
- `SUBSYSTEM_ONLY_NOT_INTEGRATED`: a subsystem API accepts the quantity, but `V3PipelineRunner` does not expose/apply it;
- `EXTERNAL_ENDPOINT_SCALING`: the quantity belongs to exposure/scenario arithmetic rather than environmental-transfer physics.

A structural zero is a statement about the current frozen equation and the declared held-fixed basis. It is not evidence that the real-world process is unimportant.

### 2. Perturbation eligibility classes

- `RUNNABLE_CURRENT_PIPELINE`: legal to perturb inside the frozen runtime without changing model semantics;
- `RUNNABLE_STATE_BASIS_REVIEW_REQUIRED`: perturbation is possible only after declaring which state quantity is held fixed;
- `RUNNABLE_PROVISIONAL_ABSTRACTION_ONLY`: the current abstraction can be numerically perturbed, but the result may not validate or endorse that abstraction;
- `NOT_INTEGRATED_CURRENT_PIPELINE`: no end-to-end perturbation is allowed until a separate integration decision exists;
- `NO_EFFECT_CURRENT_EQUATION`: changing the field alone cannot change the declared current output;
- `EXTERNAL_SCENARIO_ANALYTIC`: endpoint effect may be derived from explicit exposure arithmetic and must remain outside environmental-physics prioritization.

### 3. Exact current-runtime findings

The audit freezes these important call-graph conclusions:

- Leaf exchange uses only air HTO concentration, equilibrium air-equivalent concentration, and the precomputed exchange velocity `1/(r_a+r_b+r_c)`. Current temperature, humidity, wind and radiation metadata do not dynamically recalculate resistance.
- `V3PipelineRunner` does not pass TFWT `water_loss_flux` or `transformation_flux`, and does not expose soil signed `transport_flux`; those inputs remain subsystem-only in the integrated baseline.
- Root uptake reads the **step-start** soil state. Therefore same-interval atmospheric deposition cannot affect same-interval root uptake; its plant/dose influence is delayed to a later step through the updated soil state.
- OBT reads the leaf-only TFWT intermediate before root input is reconciled. Therefore root input cannot affect OBT in the same interval; its OBT/dose influence is delayed to a later interval unless the endpoint food pathway directly transfers TFWT.
- TFWT water content and OBT plant mass are concentration/basis denominators. At fixed authoritative activity inventory, the current OBT and food solvers consume inventories, so those denominators do not change the current activity-dose pathway.
- OBT temperature, photosynthetic activity and growth-stage extension fields do not alter the current first-order OBT equation.
- Food, consumption and dose are endpoint/readout operations. Harvest area, annual consumption and dose coefficient can create direct arithmetic scaling without proving environmental-physics importance.

### 4. Physics-gap decision classes

Each subsystem receives one of these R1 dispositions:

- `ADVANCE_NUMERICAL_SCREENING`: current equation is runnable and numerical influence can be screened without claiming physical validation;
- `ADVANCE_EVIDENCE_AFTER_SCREENING`: current equation is runnable and evidence acquisition should be prioritized only after structural/numerical influence is established;
- `HOLD_REDESIGN_REQUIRED`: no admissible sensitivity to a missing mechanism is manufactured from a placeholder field;
- `HOLD_NOT_INTEGRATED`: subsystem input exists but is not part of the end-to-end baseline;
- `KEEP_EXTERNAL_GOVERNANCE`: exposure/regulatory/scenario quantity remains outside environmental physics ranking;
- `KEEP_VALIDATED_CONSTANT`: validated constant remains governed separately;
- `DEFER_CURRENT_STRUCTURAL_ZERO`: field is inactive or diagnostic-only in the frozen baseline; a future model may reopen it.

### 5. Numerical screening boundary

R1 performs exact structural sensitivity only. It does **not** report empirical uncertainty, Sobol indices, calibrated ranges, or physical sensitivity coefficients.

A later `V4_SYSTEM_SENSITIVITY_SCREENING_EXECUTION_R1` may run deterministic multi-step synthetic/replay cases using only existing public APIs. That execution must:

- keep all test values explicitly `SYNTHETIC_TEST_ONLY` or `REPLAY`;
- use at least two intervals so delayed soil/root pathways are observable;
- separate OBT-only and TFWT-inclusive food readouts when needed;
- report final soil, TFWT, OBT, food-component, intake and dose endpoints;
- preserve all subsystem conservation and restart invariants;
- use scale-aware finite-difference/elasticity screening only after a nonzero baseline and perturbation rule are preregistered;
- keep zero-baseline and categorical day/night cases separate from log-elasticity calculations;
- never interpret arbitrary perturbation size as a physical uncertainty distribution.

No physical parameter range is invented by this ADR.

### 6. System-priority consequences

R1 changes the ordering logic from documentation volume to system dependency:

- `leaf.r_a/r_b/r_c`, OBT `kf/kr`, root `k_root`, air HTO concentration and surface deposition forcing enter or can propagate through the current runnable chain and are appropriate for controlled screening, subject to their evidence caveats.
- root `k_root` remains a provisional one-layer effective-velocity abstraction; a large numerical influence would strengthen the case for the already-planned layered soil/root redesign, not validate `k_root`.
- OBT day/night multipliers are runnable placeholders but remain redesign-required; screening may expose baseline dependence only.
- OBT photosynthesis/temperature mechanisms, three-layer soil hydrology, continuous food kinetics and non-integrated TFWT loss terms remain HOLD rather than receiving guessed sensitivity scores.
- consumption amount, product mass and dose coefficient remain external scenario/dosimetry controls even when their dose elasticities are algebraically large.

## Non-authorization

This audit does not authorize:

- production solver changes;
- real CTEAS-Atmos adapter activation;
- three-layer soil implementation;
- root water-flux redesign implementation;
- dynamic stomatal solver implementation;
- OBT two-pool or photosynthesis/temperature model implementation;
- continuous food-chain implementation;
- calibration, fitting or parameter activation;
- physical uncertainty ranges or probability distributions.

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
