# V2 validation strategy

V2 validation is evidence-layered; passing a lower layer does not imply
regulatory or field validation.

## Layer 1: compatibility and arithmetic

- all 61 V1 tests remain passing;
- mode `off` reproduces V1;
- configuration rejects invalid modes, units, probabilities, and negative
  physical parameters;
- pure transfer and dose functions have analytic unit tests.

## Layer 2: dimensional and conservation checks

- each new equation has a documented SI mapping;
- atmospheric loss equals dry plus wet deposition ledgers;
- soil/plant/food internal transfers cancel exactly;
- harvest, deep drainage, excretion, milk, slaughter, decay, and atmospheric
  re-emission are explicit boundaries;
- fresh/dry/water concentration conversions round-trip.

## Layer 3: physical invariants

Zero source produces zero activity and dose. Increasing washout lowers remaining
plume source. Equal leaf/air equilibrium concentrations give zero net exchange.
No vegetation gives zero leaf flux. Inventories and doses remain finite and
non-negative under specified extremes. Grid/time refinement converges.

## Layer 4: manual and reference anchors

Eq. (44) calibration targets, plant exchange half-times/equilibrium, soil layer
fractions, OBT turnover, animal transfer constants, and Eq. (106)-(107)
arithmetic are compared independently. Disagreements are recorded rather than
silently tuned.

## Layer 5: scenarios and recomputation

The Stage-10 benchmark matrix covers V1, dry/wet deposition, day/night leaf
exchange, 72 h re-emission, crop/harvest, pasture-milk, full adult dose, and
extreme limits. `scripts/verify_v2_acceptance.py --recompute` must create and
run cases in a temporary directory and record HEAD/worktree, Python and
dependency versions, hashes, seed, modes, and timestamps.

Acceptance thresholds belong beside each benchmark. A candidate may be
`ACCEPT_WITH_REMAINING_LIMITATIONS` when all declared project invariants pass
but an optional module remains honestly experimental or deferred.

