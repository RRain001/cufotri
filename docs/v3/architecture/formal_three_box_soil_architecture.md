# Formal three-box soil architecture

Status: `ARCHITECTURE_ONLY`

Implementation status: `NOT_STARTED`

The reserved layers are surface, root, and deep. Each layer owns water storage
in metres, HTO activity in `Bq m-2`, water concentration in `Bq m-3 water`,
depth, and a versioned parameter set. Transfers declare water rate and activity
rate separately.

Boundary interfaces:

- surface: precipitation/deposition input, evaporation/re-emission output, and
  runoff boundary;
- interlayer: drainage and diffusive exchange with equal source/destination
  activity;
- root: normalized root fractions and inventory-limited plant uptake;
- deep: explicit deep-boundary loss, never silent disappearance.

The global ledger reconciles all three inventories plus surface, root uptake,
runoff, deep loss, re-emission, and decay. Layer-local closure does not replace
the global ledger.

Acceptance requires:

1. one-box degeneration under identical concentrations and collapsed transfer
   time scales;
2. layer refinement convergence under a declared tolerance;
3. dry/wet surface footprint independence;
4. zero-flow, zero-activity, and saturated/empty limits;
5. an external soil-water/HTO case with identifiable layer parameters.

The V2 one-box model remains the default. Migration cannot enable the layered
model, and the existing experimental standalone solver is not formal coupling
evidence.
