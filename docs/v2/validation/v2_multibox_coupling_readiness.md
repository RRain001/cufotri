# Three-box soil formal-coupling readiness

```text
LIMITATION = M_MULTIBOX_STANDALONE
VAL_MULTIBOX_COUPLING_READINESS = PARTIAL
CANDIDATE_FORMAL_COUPLER = SINGLE_TOP_5CM
THREE_BOX_STATUS = EXPERIMENTAL_STANDALONE
```

The candidate deliberately rejects `surface_root_deep_3box` in
`run_short_case`. This plan defines evidence and interfaces needed for a later
reviewed coupling; it does not connect the solver to the released candidate.

## Required validation matrix

| Requirement | Inputs | Observable | Unit | Gate |
|---|---|---|---|---|
| one-box degeneration | identical total depth/water/activity, disabled internal gradients | total inventory and boundary loss | Bq m-2 | relative difference <=1e-6 |
| three-box conservation | arbitrary nonnegative inventories and all enabled fluxes | input - boundary - decay - final | Bq m-2 | absolute <=1e-10 Bq m-2 or relative <=1e-10 |
| water conservation | rain, evaporation, uptake, drainage | water residual | m | absolute <=1e-12 m |
| root distribution | normalized three-layer root vector | per-layer and total root uptake | m s-1; Bq m-2 s-1 | fractions sum to one and ledger closes |
| surface evaporation | nonzero surface concentration | layer-1 evaporation only | m s-1; Bq m-2 s-1 | layers 2/3 have no direct evaporation |
| deep leakage | layer-3 water/activity | external deep boundary | m s-1; Bq m-2 s-1 | named once in global boundary |
| interlayer diffusion | concentration gradients of both signs | interface flux and recipient activity | Bq m-2 s-1 | internal transfer cancels globally |

## Formal coupler interface contract

The later coupler must provide, at every step:

- three water storages and three HTO inventories;
- precipitation water and HTO surface inputs;
- requested surface evaporation;
- total plant root-water demand and a normalized layer distribution;
- interlayer advective and diffusive fluxes;
- deep leakage and radioactive decay;
- explicit external boundary totals;
- no direct use of local layer inventories as global Bq without the same
  ecological reference area used by the formal surface ledger.

The output contract must return updated layer states, per-process fluxes,
stepwise water/activity residuals, and aggregate compatibility values. The
formal global ledger must count interlayer transfer only internally and deep
leakage, evaporation, plant uptake/harvest and decay exactly once.

## Current evidence and missing evidence

Standalone tests already cover conservation, surface-only evaporation,
optional diffusion and formal-coupler rejection. Missing before formal
coupling:

- a reviewed one-box degeneration harness with equivalent boundary semantics;
- multi-step high-gradient and dry-layer stability vectors;
- explicit handoff of plant uptake and ecological activity ledgers;
- soil-profile observations or an independent reference-model comparison;
- independent review of any formal integration patch.

The readiness status remains `PARTIAL`; it is not evidence that the candidate
uses or validates the three-box solver.
