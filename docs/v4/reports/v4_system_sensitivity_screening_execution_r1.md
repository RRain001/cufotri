# V4 system sensitivity screening execution R1 — result review

## Verdict

`PASS_SOFTWARE_SCREENING`

This review freezes the actual GitHub Actions result from PR #21 exact branch head
`6a4c87b4daeef672451e14d42a7935401e58c476`. The successful protected-integration
run is `32947990894`; Actions checked out the pull-request synthetic merge
`8ee97771618bc3952fd9d8fb947a252aecad0267`. These identities are deliberately
recorded separately.

The execution is a repository-controlled synthetic software screen. It is not
empirical validation, calibration, global sensitivity analysis, or a physical
uncertainty ranking.

## CI closure

The corrected exact-head run produced:

- portable current integration suite: `1159 passed, 1 skipped, 57 deselected`;
- explicit frozen-boundary suite: `238 passed`;
- sensitivity harness: `V4_SCREENING_STATUS=PASS_SOFTWARE_SCREENING`;
- deterministic repeat: PASS;
- restart equivalence: PASS;
- maximum reported balance residual: `0.0`;
- all structural-zero probes: PASS;
- all 1% versus 0.5% finite-difference probes: converged under the preregistered
  absolute elasticity-change threshold `1e-3`.

The first PR-head attempt (`9bbed395...`) is not hidden. It failed because the
synthetic soil half-life `1e10 s` produced a numerically ill-conditioned
analytic soil balance. No production solver was changed. The fixture alone was
changed to `1000 s`, explicitly as a test-only numerical fixture rather than a
physical parameter choice.

## Actual profile endpoints

| Profile | Dose (Sv, synthetic endpoint) | Food total (Bq) | Soil (Bq m^-2) | TFWT (Bq m^-2) | OBT (Bq m^-2) |
| --- | ---: | ---: | ---: | ---: | ---: |
| OBT-only | 1.4377914011 | 7.1889570055 | 66.2121392525 | 76.0898500512 | 11.9815950091 |
| Mixed OBT+TFWT | 6.0031824042 | 30.0159120208 | 66.2121392525 | 76.0898500512 | 11.9815950091 |
| Day/night mixed | 5.7358606138 | 28.6793030692 | 66.2121392525 | 80.7120241644 | 7.4428263664 |

The numerical dose values above are synthetic-fixture outputs. They have no
regulatory or predictive dose meaning.

## Local computational influence

For the day/night mixed profile, the fine (`0.5%`) normalized dose response was:

| Input | Local dose elasticity |
| --- | ---: |
| food.tfwt_harvest_fraction | +0.844289 |
| atmos.air_hto_concentration | +0.670850 |
| leaf.total_resistance | -0.559056 |
| soil.water_content | -0.276192 |
| root.k_root | +0.276188 |
| initial.soil_inventory | +0.203050 |
| food.harvest_fraction | +0.155711 |
| atmos.surface_deposition_flux | +0.139315 |
| leaf.equilibrium_air_concentration | -0.111808 |
| initial.tfwt_inventory | +0.059187 |
| obt.kf | +0.054705 |
| initial.obt_inventory | +0.039405 |
| obt.daylight_multiplier | +0.038810 |
| obt.nighttime_multiplier | +0.015895 |
| obt.kr | -0.005229 |

This table is **not** a physical importance ranking. The perturbations are
numerical probes around one synthetic fixture, several variables are provisional
abstractions, and the mixed endpoint itself contains provisional food-transfer
fractions.

## Decision-relevant findings

### 1. Soil/root confounding is now directly visible

The nearly equal-and-opposite local responses of `root.k_root` (+0.276188) and
`soil.water_content` (-0.276192) are consistent with the frozen relation
`J_root = k_root * C_soil = k_root * M_soil / W_soil`. This means a successful
fit of the current effective `k_root` could hide an incorrect water-storage or
root-zone representation. Numerical influence therefore does not validate the
one-layer effective-velocity abstraction.

This is the strongest system-level reason to examine the soil/root state
boundary before activating root parameters.

### 2. Leaf remains influential but evidence-blocked

Air HTO concentration (+0.670850) and total resistance (-0.559056) have strong
computational reach through the frozen leaf path. That supports preserving leaf
exchange as an important pathway, but it does not provide the matched empirical
evidence required to leave the V4-2 R4 hold. `LEAF_R5_AUTHORIZED` remains false.

### 3. Food endpoint sensitivity is a warning, not a validation result

The largest fine-step response is the provisional TFWT harvest fraction
(+0.844289). OBT-only and mixed profiles also produce very different synthetic
endpoint doses. This demonstrates that the current endpoint definition can
control downstream dose arithmetic. Because food event-versus-continuous
physics remains unresolved, this result is a reason to avoid interpreting the
mixed dose as a biological validation metric.

### 4. Deposition cannot be downgraded from this short screen

Surface deposition has a smaller six-interval dose response (+0.139315), while
its final-soil response is much larger. The frozen operator split makes root
uptake read step-start soil, so deposition influence propagates downstream with
a delay. A six-step result cannot establish low long-term environmental
importance.

### 5. Structural-zero probes confirm current inactive seams

At fixed resistance/deposition and fixed authoritative inventories, temperature,
RH, wind, precipitation, soil layer depth, TFWT water-content denominator, OBT
plant-mass denominator, OBT temperature/photosynthesis/growth-stage extension
fields all produced exactly zero output change. This confirms the current call
graph only; it does not imply those processes are unimportant in nature.

## Roadmap decision

The screening does not justify Sobol/Monte Carlo analysis because reviewed
physical uncertainty ranges do not exist. It also does not justify leaf R5,
parameter activation, or a three-layer implementation directly.

The next stage is:

`V4_ROOT_SOIL_LAYERED_BOUNDARY_DECISION_R1`

This is a **control-plane-only** decision stage. It must determine whether a
layer-resolved soil/root boundary is scientifically justified, what minimum
state representation is necessary, how transpiration/water uptake and
inter-layer fluxes are owned, and whether a three-layer representation should
be selected. It must not assume three layers merely because they are
convenient, and it must not reopen full Richards/Darcy hydrology without a
separate evidence and complexity decision.

```ini
V4_SYSTEM_SENSITIVITY_SCREENING_EXECUTION_R1 = PASS_SOFTWARE_SCREENING
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_UNCERTAINTY_RANKING = NOT_AVAILABLE
LEAF_R5_AUTHORIZED = FALSE
GLOBAL_SENSITIVITY_AUTHORIZED = FALSE
ROOT_SOIL_LAYERED_IMPLEMENTATION_AUTHORIZED = FALSE
NEXT_STAGE = V4_ROOT_SOIL_LAYERED_BOUNDARY_DECISION_R1
SOLVER_CHANGES_AUTHORIZED = FALSE
NUMERICAL_COUPLING_CHANGES_AUTHORIZED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
REAL_CTEAS_ATMOS_COUPLING_ACTIVE = FALSE
V3_PHYSICS_READY = FALSE
```
