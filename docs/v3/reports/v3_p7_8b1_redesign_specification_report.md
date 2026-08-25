# V3 P7.8B-1 Physics Redesign Specification Report

Date: 2026-08-24
Branch: `codex/v3-p7-8b1-redesign-specification`
Baseline: `codex/v3-p7-8a-physics-redesign-prioritization` at `986e375`

## Disposition

```ini
P7_8B1_STATUS = PASS_REDESIGN_SPECIFICATION
HIGH_PRIORITY_ITEMS_SPECIFIED = TRUE
EQUATION_GAPS_DOCUMENTED = TRUE
VALIDATION_REQUIREMENTS_DEFINED = TRUE
COUPLING_IMPACTS_DEFINED = TRUE
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
NUMERICAL_COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

P7.8B-1 turns the P7.8A priority decisions into reviewable candidate
specifications. It defines candidate equations, states, parameters, data,
interfaces, compatibility, and migration boundaries. It does not implement a
candidate, choose a parameter value, or reopen P7.5/P7.5B semantics.

The machine-readable source is
`docs/v3/physics/p7_8b1_redesign_specification.yaml`.

## Design rule

The current V3 profile remains the default and is called
`v3_frozen_baseline`. Future redesigns are opt-in profiles. A candidate
parameter is a symbol with a unit and evidence requirement, not a runtime
value. A candidate equation is a design object, not an implemented solver
path.

The P7.8A high-priority records are specified as follows:

| Item group | Records | Candidate disposition |
|---|---|---|
| OBT formation | R1, R2, R3 | Two-pool biological extension requires more research; reduced first-order model remains the baseline |
| OBT basis/temperature | R4, R5 | Basis contract can be prepared; temperature response requires more research |
| Root uptake | R6 | Layered water-flux model requires more research and numerical-coupling review |
| Food transfer | R7, R8 | Continuous/event or hybrid product model requires more research and numerical-coupling review |
| Leaf exchange | R9 | Stage/stomatal extension requires more research; current resistance chain remains compatible |

The deferred TFWT water-turnover and soil-hydrology records are also specified
so that their future boundaries are explicit rather than implicit.

## OBT specification

### Current model and gap

The frozen equation is

\[
\frac{dB}{dt}=k_fT-k_rB,
\]

where `B` is plant OBT activity inventory and `T` is plant TFWT activity
inventory on the declared area basis. The current implementation exposes
daylight, temperature, photosynthetic activity, and growth-stage fields as
forcing/interface concepts, but the reduced equation does not resolve their
biological mechanisms.

### Candidate models

Option A keeps the first-order equation. It is simple, stable, and directly
compatible with existing cases, but it cannot claim resolved carbon fixation,
day/night residual activity, growth allocation, or organ-specific pools.

Option B introduces a precursor/activity pool and two OBT pools:

\[
\begin{aligned}
\frac{dP}{dt} &= u_P(T,A,d,s,T_{leaf})-k_PP,\\
\frac{dB_x}{dt} &= k_{PB}P-(k_x+k_{xn})B_x,\\
\frac{dB_n}{dt} &= k_{xn}B_x-k_nB_n.
\end{aligned}
\]

`P`, `B_x`, and `B_n` are candidate inventories in `Bq m^-2`. The source
`u_P` must decide whether light/activity/temperature are measured forcings or
new states. `B_x` and `B_n` must be defined biologically before they are
called exchangeable and non-exchangeable OBT. No rate or forcing value is
selected here.

Option C adds organ-specific pools and growth allocation. It is retained as a
research option, not as the first implementation target, because it requires
organ-level data and introduces additional identifiability risk.

### OBT state and interface specification

The minimum future state contract must identify TFWT, precursor/activity,
exchangeable OBT, non-exchangeable OBT, plant mass basis, tissue scope,
day/night state, temperature provenance, and activity provenance. The current
public TFWT/OBT inventory boundary remains the compatibility boundary for
Option A.

The R1/R2/R3/R5 package requires time-resolved plant TFWT and OBT, daylight or
light-state information, activity or PAR information, temperature, crop
stage, mass basis, and independent biological replicates. Validation must
compare the reduced and extended candidates, test component and total
inventory conservation, and keep synthetic software evidence separate from
biological validation.

## Root uptake specification

### Current model and options

The current root boundary is

\[
J_{root}=k_{root}C_{soil},
\]

with `k_root` in `m s^-1`, soil-water concentration in `Bq m^-3 water`, and
activity flux in `Bq m^-2 s^-1`.

The three options are:

1. Effective velocity, `J=v_r C`: retain the current abstraction and current
   compatibility, but do not claim a layer-resolved mechanism.
2. Water-flux coupled, `J_i=q_{w,i}C_{w,i}`: represent layer-specific water
   flux and soil-water concentration, with
   `M_{s,i}=theta_i Delta_z_i C_{w,i}`.
3. Moisture-dependent, `J_i=v_{r,i}f_theta(theta_i)C_{w,i}`: treat moisture
   limitation as a bounded closure, not as a replacement for layer state or
   water-flux ownership.

The preferred candidate for future study is Option 2 with Option 3 only as an
explicit closure. Required states include layer activity inventories, water
content, layer geometry, root activity distribution, water uptake, and root
flux. Required data include soil HTO and moisture profiles, root profiles,
transpiration/water uptake, plant TFWT, and boundary conditions.

### Coupling and compatibility

Selecting a layered candidate changes soil/root/plant state ownership and is a
`NUMERICAL_COUPLING_CHANGE`. The scalar effective-velocity profile remains
the default. No assumed storage length, layer depth, or scalar-to-layer
mapping is allowed. A future implementation requires a P7.5/P7.5B review,
layer/global conservation, restart, refinement, and failure-behavior tests.

## Soil transport specification

### Current model and gap

The current soil boundary is

\[
\frac{dM_s}{dt}=F_{dep}+F_{transport}-\lambda M_s,
\]

where signed transport is an explicit interface input. It does not derive
hydrology, diffusion, evaporation, or layer interaction.

The candidate layered conservative form is

\[
\frac{dM_i}{dt}=F_{adv,i-1/2}+F_{diff,i-1/2}
 -F_{adv,i+1/2}-F_{diff,i+1/2}
 +S_i-\lambda M_i-J_{root,i}-J_{evap,i}.
\]

This is a design form only. It requires layer water state, interface fluxes,
root extraction, evaporation boundary, signs, and a water/HTO basis. It is
not a claim that the recovered UFOTRI source supplies these values.

### Interface decision

The current signed-transport interface remains unchanged for the baseline.
Selecting the layered candidate is a `NUMERICAL_COUPLING_CHANGE` because it
changes soil state ownership and interacts with root uptake and water
forcing. Required data are layer-resolved soil profile, moisture, infiltration,
drainage, evaporation, HTO transport, root-zone data, and boundary
conditions.

## Leaf exchange specification

### Current model and gap

The current chain is

\[
r_{tot}=r_a+r_b+r_c,\qquad g_{ex}=1/r_{tot}.
\]

Growth stage is metadata/coordinate information, not a stage-dependent
equation. The current chain is sufficient as a frozen validation baseline.

### Candidate extension

An opt-in dynamic stomatal candidate is

\[
g_s(t)=g_{s,max}F_{light}(L)F_{vpd}(VPD)
F_{temp}(T_{leaf})F_{stage}(s),\qquad r_c(t)=1/g_s(t).
\]

The response functions must have declared domains, provenance, and bounds;
their values are not specified here. New interface fields may include a typed
stage state, stage transitions, leaf temperature, and dynamic canopy
conductance. The likely impact is `INTERFACE_EXTENSION`; the existing
`r_a/r_b/r_c` units and ownership remain unchanged.

Validation requires crop-specific stage timestamps, canopy geometry/LAI,
matched meteorology, component resistances or conductance, and independent
cases. Metadata-only stratification must be evaluated before dynamic
stomatal response.

## TFWT specification

### Current model and gap

The current activity balance is

\[
\frac{dM_T}{dt}=J_{leaf}+J_{root}-J_{loss}-J_{transformation},
\]

with fixed water content in the current state contract. Water mass is not
advanced by the TFWT solver.

### Candidate extension

The candidate dynamic-water form is

\[
\frac{dW}{dt}=I_W-O_W+G_W,\qquad C_T=M_T/W,
\]

\[
\frac{dM_T}{dt}=J_{leaf}+J_{root}+J_{in,W}-C_TO_W-J_{transformation}.
\]

`W` is plant water mass and `C_T` is activity concentration on the declared
water basis. This avoids hiding dilution in an activity multiplier. It
requires separate water fluxes, plant growth/stage, and a decision whether
growth water carries activity. The impact is `PIPELINE_CHANGE`, not a silent
change to the current activity-loss input.

Validation requires plant water/biomass trajectories, transpiration,
irrigation/precipitation, water loss, TFWT activity, stage, area, and timing.
The fixed-water baseline remains the default until a water-balance dataset and
pipeline ownership review are complete.

## Food transfer specification

P7.8A identified food OBT and TFWT boundaries as high-priority redesigns even
though they were not listed as a separate subsection in the P7.8B-1 prompt.
They are included because the objective covers every approved redesign
candidate.

### OBT product boundary

The current event relation is

\[
M_{food,O}^{+}=h_OM_{plant,O}(t_h).
\]

A candidate continuous/hybrid form is

\[
\frac{dM_{food,O}}{dt}=k_{p,O}M_{plant,O}-k_{loss,O}M_{food,O},
\]

with an explicit harvest operator if an event is retained. Product OBT must
remain distinct from plant OBT, TFWT, intake, and dose. The change is a
`NUMERICAL_COUPLING_CHANGE`.

### TFWT product boundary

The current event relation is

\[
M_{food,T}^{+}=h_TM_{plant,T}(t_h).
\]

A candidate continuous/hybrid form is

\[
\frac{dM_{food,T}}{dt}=k_{p,T}M_{plant,T}-k_{loss,T}M_{food,T},
\]

with an explicit product-water mass `W_food`. OBT and TFWT product states
must not share a fraction by assumption. Required data include plant/product
activity, product water and mass basis, harvest timing, remaining plant
inventory, loss, repeated harvests, and independent replicates. Annual
consumption and dose coefficients remain external scenario/dosimetry inputs.

## Parameter and evidence boundary

All new symbols in the registry are candidate parameters, forcing functions,
or state descriptors. P7.8B-1 assigns no numerical values, does not import
UFOTRI parameters, and does not alter the active parameter count. Before any
candidate can enter implementation, its source, equation, units,
applicability, validation data, and independent review must be recorded.

## Conclusion

P7.8B-1 specifies what a future redesign would need to mean and how it would
be tested. It deliberately leaves model selection open for OBT, root, soil,
leaf, TFWT, and food where evidence or coupling design is incomplete. The
current V3 implementation remains the only runnable profile, and
`V3_PHYSICS_READY` remains false.
