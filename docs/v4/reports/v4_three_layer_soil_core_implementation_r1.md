# V4 three-layer soil core implementation R1

## Scope

This stage implements the soil state selected by `V4_ROOT_SOIL_LAYERED_BOUNDARY_DECISION_R1` without changing the frozen V3 soil solver or default V3 pipeline.

The new core is opt-in at `src/cteas_ufotri/plant/soil_v4/`.

## Implemented state

The canonical UFOTRI soil geometry is fixed to:

| Layer | Depth |
| --- | --- |
| L1 | 0–5 cm |
| L2 | 5–15 cm |
| L3 | 15–30 cm |

Each layer owns two authoritative quantities:

- water inventory/depth in `m water`;
- HTO activity inventory in `Bq m^-2`.

Specific HTO concentration in soil water is derived as `M_HTO / W_water` in `Bq m^-3 water`. Geometry, units, positive water inventory, non-negative HTO inventory and UTC timestamps fail closed.

The UFOTRI manual's 25% volumetric-water reference gives 0.0125, 0.0250 and 0.0375 m water for the three layers, corresponding to 12.5, 25.0 and 37.5 kg m^-2. These values are used only by a repository-controlled reference fixture and are not activated as physical runtime parameters.

## Conservative transport boundary

The core intentionally does not derive hydrology. The forcing boundary supplies explicit interval-start fluxes:

- surface water input to L1;
- surface water loss from L1, providing the conservative inventory boundary required for evaporation/re-emission adapters without deriving an evaporation rate in this core;
- atmospheric HTO deposition into L1;
- signed L1↔L2 water and HTO fluxes;
- signed L2↔L3 water and HTO fluxes;
- lower-boundary water and HTO loss from L3;
- surface HTO re-emission sink from L1;
- explicit per-layer root water/HTO sink slots.

Every forcing bundle now carries an explicit UTC timestamp with fixed `interval_semantics="start"`. The solver rejects any forcing whose timestamp does not equal the current three-layer state timestamp. This closes the V4 common time-contract requirement before pipeline integration rather than relying on caller convention.

Inter-layer signs are positive downward. Negative values are allowed and represent upward transport, consistent with the UFOTRI manual's statement that capillary forces may move water toward the upper layers in dry conditions.

The soil core does not infer HTO transport from water flux, derive a Darcy flux, solve a Richards equation, infer rainfall percolation, calculate surface evaporation, or calculate root uptake. Those physical closures remain separate stages. Surface water loss and HTO re-emission are separate explicit forcing fields; no silent concentration or phase relation is assumed between them.

## Numerical semantics

Water inventory uses a conservative constant-flux update over the interval. HTO inventory uses constant explicit boundary fluxes plus analytic first-order radioactive decay. The same inter-layer transfer is entered as an equal loss and gain on adjacent layers, so internal transport cancels from the global ledger.

Both per-layer and global balances are returned. Surface water loss is included in the L1 ledger and in global external water loss. A step fails closed if water is exhausted or if an HTO sink would overdraw a layer.

Restart is provided directly on the three-layer state through mapping/JSON round-trip; it is intentionally not wired into `V3SimulationState` yet.

## UFOTRI root evidence retained for the next stage

KfK 4605 distinguishes the short-term summary that roughly 20% of root water comes from the top 5 cm and 80% from deeper soil from the explicit three-layer ingestion-compartment model in Chapter 3.3.2. In the latter, the root uptake distribution is explicitly 20% from 0–5 cm, 40% from 5–15 cm, and 40% from 15–30 cm. Equation (57) converts total plant uptake and the layer hydrogen inventory into a layer transfer rate; Equations (58)–(60) give reference rates of approximately 0.026, 0.026 and 0.017 d^-1 for the manual's reference inventories.

Those values and fractions are retained as UFOTRI reference evidence only in this soil-core stage. They are not activated here. `V4_THREE_LAYER_ROOT_WATER_UPTAKE_R1` must implement the transpiration-controlled root boundary separately and must preserve provenance/status for any selected runtime profile.

## What this stage does not claim

This is an architecture/solver-core implementation, not physical validation. It does not select or calibrate inter-layer transport rates, soil hydraulic properties, surface evaporation rates, the UFOTRI 0.4% h^-1 short-term deeper-transport reference, or the UFOTRI 20/40/40 root-water distribution as an active parameterization.

It does not implement full Richards/Darcy hydrology. KfK 4605 presents the Darcy-continuity nonlinear unsaturated-flow equation as physical background and then explicitly states that such complex models cannot be used in the UFOTRI application; the baseline therefore remains a simplified layer-compartment transport model.

## Independent audit remediation

The first branch head exposed all explicit HTO surface-loss semantics but omitted an explicit surface water-loss boundary from the authoritative water inventory. The independent audit rejected that asymmetry for a conservative three-layer state. R1 therefore adds `surface_water_loss_m_s`, validates it as a non-negative explicit forcing, applies it only to L1, includes it in layer/global water ledgers, and tests both conservation and fail-closed overdraw. This is a storage-boundary repair, not a new hydrology model.

A second audit check compared the implementation against the already-frozen V4 common time contract. The original forcing object had no timestamp despite claiming interval-start semantics. R1 therefore requires an explicit UTC forcing timestamp and exact alignment with `state.timestamp`; this is a contract repair only and does not change the numerical equations.

## Gate

The branch must pass the complete portable regression, the frozen-boundary suite, the new three-layer tests, exact-head CI and independent review before it can be merged. Until then:

```ini
V4_THREE_LAYER_SOIL_CORE_IMPLEMENTATION_R1 = IMPLEMENTED_AWAITING_EXACT_HEAD_CI
THREE_LAYER_SOIL_CORE_AVAILABLE = BRANCH_ONLY
DEFAULT_V3_SOIL = UNCHANGED
FULL_RICHARDS_DARCY_SOLVER = FALSE
ROOT_LAYER_MODEL = NOT_IMPLEMENTED
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```
