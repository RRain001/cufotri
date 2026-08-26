# V4 root/soil layered boundary decision R1

## Verdict

`PASS_THREE_LAYER_UFOTRI_TARGET_SELECTED`

The V4 soil target is now fixed to three layers matching the recovered UFOTRI KfK 4605 ingestion/soil compartment structure:

- L1: 0–5 cm;
- L2: 5–15 cm;
- L3: 15–30 cm.

The current V3 one-layer soil remains the default frozen baseline until an opt-in V4 three-layer implementation independently passes its gates.

## What the UFOTRI manual actually says

The recovered manual is `ufotri_manual.md`, W. Raskob, KfK 4605. The P7.6C-2 source inventory records its SHA-256 as `82c7c7f07975553a51e7ba1666a912f80096e5af4fc138aba6f45a120e6d3562`.

The manual contains two soil representations that must not be conflated.

### Short-term secondary atmospheric module

The manual says HTO is assumed to be concentrated in the top 5 cm soil layer, with only a small fraction transported into deeper layers at a constant diffusion rate of 0.4% per hour. Agricultural roots take up water from soil down to 30 cm. The text gives a first-order split in which 20% of root water uptake carries the specific HTO concentration of the top 5 cm and 80% carries the concentration characteristic of deeper soil.

This proves a top-layer/deeper-soil distinction, but the recovered manual text does not prove that the short-term secondary implementation itself stored three explicit state layers.

### Ingestion / soil compartment module

The long-term compartment subsystem is explicit. With a stated mean volumetric water content of 25% in each layer, the manual defines:

| Layer | Depth | Water inventory |
| --- | --- | ---: |
| soil11 / L1 | 0–5 cm | 12.5 kg m^-2 |
| soil12 / L2 | 5–15 cm | 25.0 kg m^-2 |
| soil13 / L3 | 15–30 cm | 37.5 kg m^-2 |

Figure 12 and the surrounding transfer-rate equations connect the three soil compartments. A corresponding three-layer structure is also described for the grass/second ingestion subsystem.

Therefore, for a project whose explicit goal is to reproduce UFOTRI semantics rather than preserve the earlier V3 simplification, a three-layer 0–30 cm soil state is scientifically and historically justified.

## Richards / Darcy decision

The manual does discuss physically complete unsaturated water transport. It introduces soil water potential in Eq. (33), the continuity equation in Eq. (34), applies Darcy's law, and arrives at Eq. (37):

`dTheta/dt = d/dz [ K(Theta) (dPsi_m/dz - 1) ] - S(z,t)`

In modern terminology this is a Richards-type unsaturated-flow equation derived from Darcy + continuity. The manual itself does not use the word “Richards”.

Critically, the next paragraph states that this second-order nonlinear PDE requires soil-water-potential curves, initial soil water content and vegetation information that are not available, and concludes that such “complex but rather accurate models” cannot be used here. UFOTRI instead estimates transport rates and soil moisture as daily averages for selected soil layers using a simple soil-moisture/vegetation model. It also notes low vertical motion and possible upward capillary transport in dry weather, and larger downward transport during rain.

Consequently:

`FULL_RICHARDS_DARCY_SOLVER = NOT_AUTHORIZED`

A full Richards solver would be an extension beyond the recovered UFOTRI baseline, not a faithful replication choice.

## V4 architecture selected

The V4 soil state will be an opt-in three-layer water/HTO inventory model. Each layer owns its water depth/inventory, HTO inventory and derived water concentration. The solver boundary must expose:

- atmospheric deposition into L1;
- signed L1↔L2 and L2↔L3 water/HTO transfer;
- bottom loss from L3;
- layer-resolved root extraction;
- surface re-emission from L1;
- radioactive decay in every layer.

Signed inter-layer flux is required because the manual explicitly allows upward capillary transport in dry periods as well as enhanced downward transport in rainfall.

The core must close both per-layer and total activity balances. Internal layer-to-layer transfer must cancel exactly in the global ledger. Missing fluxes, units, timestamps or geometry must fail closed.

## Root boundary consequence

The current V3 effective relation `J_root = k_root * C_soil` is not suitable for parameter activation as the final UFOTRI-replication root model. R1 sensitivity screening showed the expected strong confounding between `k_root` and the soil-water basis. UFOTRI instead connects root uptake to transpiration/root distribution across soil depth.

The three-layer soil core therefore precedes root redesign. The manual 20% top / 80% deeper split is retained as evidence, not yet activated as a production parameterization. Detailed per-layer root allocation will be resolved in the dedicated root stage.

## Authorization

The next stage is authorized:

`V4_THREE_LAYER_SOIL_CORE_IMPLEMENTATION_R1`

It may add a new opt-in `soil_v4` package, state/validation, conservative three-layer transport, restart serialization, synthetic UFOTRI-reference fixtures, tests and reports.

It may not modify the frozen V3 soil equations, make V4 the default, add a full Richards solver, calibrate transfer rates, activate root fractions, change P7.5/P7.5B default coupling, resume Leaf R5, or activate real CTEAS-Atmos coupling.

```ini
V4_ROOT_SOIL_LAYERED_BOUNDARY_DECISION_R1 = PASS_THREE_LAYER_UFOTRI_TARGET_SELECTED
SELECTED_LAYER_COUNT = 3
L1 = 0-5_cm
L2 = 5-15_cm
L3 = 15-30_cm
UFOTRI_DARCY_CONTINUITY_BACKGROUND = TRUE
FULL_RICHARDS_RUNTIME_IN_UFOTRI = FALSE
FULL_RICHARDS_DARCY_AUTHORIZED = FALSE
THREE_LAYER_SOIL_CORE_IMPLEMENTATION_AUTHORIZED = TRUE
V3_DEFAULT_PROFILE_CHANGED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
NEXT_STAGE = V4_THREE_LAYER_SOIL_CORE_IMPLEMENTATION_R1
```
