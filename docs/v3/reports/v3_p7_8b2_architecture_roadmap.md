# V3 P7.8B-2 Architecture Roadmap

The machine-readable roadmap is
`docs/v3/physics/p7_8b2_architecture_roadmap.yaml`. It defines the future
evolution boundary without starting implementation.

## Architecture rule

`v3_frozen_baseline` remains the only runnable V3 profile. V3.1 is a contract
and evidence-preparation stage. V4 is an opt-in future profile for the three
selected redesign directions: OBT biological pools, dynamic leaf exchange,
and water-flux-coupled root uptake. A future profile must fail closed when a
required field, unit, provenance record, or validation case is absent.

## V3.1 scope

V3.1 contains one bounded scientific change in the control-plane design:

1. Define typed mass-basis, tissue-scope, area-basis, and provenance metadata
   for plant and product activity.
2. Run dimensional and completeness checks on that contract.
3. Preserve the current first-order OBT, one-layer soil, fixed TFWT, harvest
   event, consumption, dose, and P7.5/P7.5B contracts.

The V3.1 mass-basis item does not provide fresh/dry/water/hydrogen conversion
values. Missing or conflicting basis metadata blocks cross-basis comparison.
It does not change `dB/dt = k_f T - k_r B` and does not change state
serialization or runtime parameter admissibility.

## V4 direction and order

The future implementation order is frozen as follows:

| Order | Future item | Why this order | Hard gate |
|---:|---|---|---|
| 1 | Typed data and state contracts | Freeze units, ownership, forcing provenance, and case schema before equations | Dimensional/unit, ownership, and restart design review |
| 2 | Dynamic leaf stomatal response | Add a bounded conductance response at the existing resistance boundary | Matched exchange data and interface review |
| 3 | OBT precursor and two-pool extension | Use explicit forcing/basis contracts before adding formation and pool states | Biological validation, conservation, and independent review |
| 4 | Layered root water-flux boundary | Change root/soil state ownership only after the plant-side contracts are stable | P7.5/P7.5B coupling review, conservation, restart, refinement |

The order is a future work constraint, not a current implementation plan. No
step is authorized by this report alone.

## Kept-current modules

The following remain unchanged and are not silently promoted into future
physics:

- soil one-layer storage plus signed transport interface;
- TFWT fixed-water-basis activity storage and explicit activity ledger;
- plant-to-food OBT/TFWT harvest-event transfer with separate product states;
- consumption as an external exposure scenario;
- dose as an external dosimetry/regulatory layer;
- P7.5/P7.5B interval ordering, endpoint, ledger, restart, and failure
  semantics.

The root V4 design may consume an explicit, separately owned layer-water input
contract. It must not infer a soil hydrology model or modify the current soil
profile by implication.

## Deferred and rejected work

Full soil hydrology, TFWT water turnover, and hybrid food product kinetics are
not selected because the required data and ownership decisions are incomplete.
Organ-specific OBT allocation is rejected as the first target. Continuous-only
food transfer, standalone moisture-dependent root uptake, guessed root-rate
conversion, unreviewed UFOTRI value import, and dose-driven environmental
redesign are rejected by policy.

## Compatibility and rollback

The baseline is always a valid comparison and rollback target. Future profiles
must declare their additional states and inputs explicitly. There is no
automatic mapping from a day/night multiplier to a biological forcing
function, from a scalar root coefficient to a layer flux, from activity loss
to water loss, or from an event harvest fraction to a continuous product
rate. Returning to `v3_frozen_baseline` must not require converting candidate
states or parameters.

## Gate to P7.8C

P7.8C may start only after the selected item receives a reviewed equation and
unit contract, state ownership, conservation/restart tests, validation data
contract, applicable coupling review, independent review, and explicit
implementation authorization. Until then:

```ini
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
NUMERICAL_COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
V3_PHYSICS_READY = FALSE
```
