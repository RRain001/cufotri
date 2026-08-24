# V3 P7.8B-2 Validation Dependency Report

The canonical dependency map is
`docs/v3/physics/p7_8b2_validation_dependency.yaml`.

## Validation boundary

P7.8B-2 records what data and observables are required before a selected
future model can be implemented or activated. It does not claim that the data
are already available, that a candidate is validated, or that P7.7B synthetic
benchmarks are empirical evidence.

Each future model must be compared with the unchanged
`v3_frozen_baseline`. Production arithmetic is not an independent expected
value. A candidate parameter remains a symbol with a unit and provenance
requirement; no numerical value is admitted by this dependency map.

## Dependency matrix

| Item | Required observations | Core observables | Required metrics |
|---|---|---|---|
| OBT two-pool package | Time-resolved TFWT, exchangeable/non-exchangeable OBT, light/day-night, activity, temperature, stage, basis, replicates | `T`, `P`/formation proxy, `B_x`, `B_n`, aggregate OBT | Pool and aggregate trajectories, integrated inventory, conservation residual, out-of-sample replicates, restart |
| OBT mass-basis contract | Paired fresh/dry/water/hydrogen mass where used; plant/product activity and basis | Basis/tissue/area/provenance labels and inventories | Completeness, dimensional reconciliation, correct fail-closed rejection |
| Dynamic leaf response | Conductance/resistance, radiation, VPD/humidity, leaf temperature, stage, TFWT flux | `g_s`, `r_c`, `r_a`, `r_b`, `r_tot`, `g_ex` | Conductance/resistance error, reciprocal-unit identity, domain/bound checks, cross-condition generalization |
| Root water-flux boundary | Layer HTO, moisture, geometry, root profile, transpiration/water uptake, plant TFWT, boundary fluxes | `C_w,i`, `theta_i`, `Delta_z_i`, `q_w,i`, `J_root,i`, layer/global inventories | Layer/global conservation, root/TFWT trajectory error, restart, refinement, boundary sensitivity |
| Current soil interface | Declared one-layer deposition/signed transport and initial inventory | `M_s`, signed terms, decay | Conservation and restart under current contract |
| Current TFWT boundary | Explicit activity fluxes/losses, water/area basis, timing | `M_T` and ledger terms | Activity conservation, restart, units |
| Current food event | Plant/product OBT/TFWT at harvest, product basis/water, repeated harvest metadata | Separate `M_food,O`, `M_food,T` and event inputs | Event/basis reconciliation, product inventory error, no downstream feedback |
| Consumption boundary | Case scenario amount/timing/product/mass basis | Intake scenario and provenance | Scenario completeness and units |
| Dose boundary | External coefficient source/version/applicability and intake contract | Intake, coefficient, dose with separate provenance | Independent dosimetry audit and units |

## Model-specific gates

### OBT

The validation case must pre-register the day/night transition convention and
define exchangeable and non-exchangeable pool scope before fitting or
comparison. Option A and Option B must use the same timestamps and basis. The
case must distinguish component conservation from total OBT agreement; a good
aggregate trajectory cannot hide compensating errors between pools.

### Root uptake

`q_w,i` must be observed or supplied by a separately reviewed water model. A
scalar rate cannot be divided by an assumed layer length. Layer geometry,
storage basis, signs, root activity ownership, and boundary conditions are
part of the case contract. Global conservation is required in addition to
layer-level conservation.

### Leaf exchange

Every response function must declare its domain, units, bounds, provenance,
and missing-data behavior. Conductance and resistance must retain reciprocal
units. Validation must cover the response domain rather than only one
light/VPD/temperature/stage condition.

### Maintained boundaries

The current soil, TFWT, and food boundaries are not revalidated as redesigned
physics in this stage. Their baseline conservation, restart, basis, and event
checks remain applicable. Dynamic TFWT water turnover, layered soil hydrology,
and continuous/hybrid food transfer require new dependency maps if later
reopened.

## Validation sequence

1. Freeze dataset schema, units, timestamps, basis, tissue scope, and replicate
   identifiers.
2. Run the unchanged baseline and preserve its outputs as the comparison
   reference.
3. Run candidate-specific dimensional, conservation, restart, and fail-closed
   checks.
4. Compare candidates with independent observations using pre-registered
   metrics and held-out cases or replicates.
5. Complete independent review and obtain explicit implementation
   authorization.

No step above has been executed as a biological validation by P7.8B-2.

## Limitations

The registry does not assert that the listed datasets exist in the repository,
nor does it supply missing biological parameters. Synthetic software evidence
can test conservation and interface behavior, but it cannot establish field
realism, parameter accuracy, empirical validation, or CALMET/UFOTRI
equivalence. These limitations are release gates, not optional caveats.
