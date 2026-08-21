# V3-P3 Food Chain Framework

Status: `FRAMEWORK_COMPLETE`

UFOTRI food-chain physics: `NOT_IMPLEMENTED`

Validated food-chain parameters: `NOT_IMPORTED`

UFOTRI numerical equivalence: `NOT_CLAIMED`

## Responsibility and boundary

The P3 package establishes the plant-to-edible-product boundary:

```text
V3-P1 leaf exchange seam       V3-P2 soil root-zone seam
             |                            |
             v                            v
                    PlantState
                         |
                         v
                  CropCompartment
                         |
                         v
                   HarvestProduct
                         |
                         v
             future human-intake interface
```

The package owns immutable plant state, crop-agnostic compartments, typed
leaf/soil coupling inputs, a replaceable physics seam, ParameterDatabase
provenance, edible-product records, and an activity ledger. It does not import
UFOTRI food-chain equations or transfer factors, perform root uptake, connect
resident consumption, calculate dose, or perform regulatory assessment.

The package is isolated under `src/cteas_ufotri/food_chain/`. The existing V2
`src/cteas_ufotri/foodchain/` pathway and its configuration are not replaced or
modified by P3.

## State and units

`PlantState` uses one declared plant reference basis:

| Field | Contract |
|---|---|
| `plant_id` | non-empty plant identifier |
| `growth_stage` | non-empty caller-defined stage label |
| `total_activity` | total plant activity inventory, Bq |
| `tfwt_activity` | TFWT activity inventory, Bq |
| `obt_activity` | OBT activity inventory, Bq |
| `dry_matter_inventory` | plant dry-matter inventory, kg dry matter |

The state requires `total_activity = tfwt_activity + obt_activity` within the
declared numerical tolerance. All activity and mass values are finite and
non-negative. No activity concentration is inferred for a plant state.

`CropCompartment` contains a caller-defined `crop_id`, a `PlantState`, an
edible fraction in `[0, 1]`, and an explicit harvest-state label. Crop names
such as rice, wheat, or lettuce are not hard-coded.

## Coupling seams

Leaf exchange is recorded with:

```python
inputs = inputs.receive_leaf_activity(
    tfwt_activity, obt_activity, plant_exposure_time_s
)
```

The activities are integrated Bq inputs for the framework interval. Exposure
time is retained as metadata; P3 does not infer an exposure or transfer
equation.

Soil coupling is recorded with:

```python
inputs = inputs.receive_root_zone_activity(
    root_zone_activity, soil_water_activity
)
```

The values are retained as a read-only seam with status
`SEAM_ONLY_NO_ROOT_UPTAKE`. `FoodChainModel.advance()` deliberately uses
`soil_input = 0` because root uptake is not implemented.

## ParameterDatabase integration

Executable synthetic-kernel values are resolved only through
`FoodChainParameters.from_database()`:

```text
food_chain.transfer_rate   [s-1]
food_chain.decay_rate      [s-1]
```

Missing, placeholder, non-finite, negative, or unit-incompatible entries fail
closed. The bundle retains the package SHA-256 and entry-level provenance, but
its status remains `PLACEHOLDER`. Tests construct an explicit synthetic
database; no values are added to the reviewed project parameter database.

## Physics seam

The canonical functional interface is:

```python
new_state, balance = advance(plant_state, inputs, dt, parameters, kernel=kernel)
```

`FrameworkOnlyPhysics` fails closed until reviewed equations and parameters are
available. `ZeroTransferKernel` preserves the plant state after applying leaf
inputs. `SyntheticTransferKernel` performs a first-order TFWT-to-OBT movement
and OBT decay using test-only rates. Both kernels are software contract
harnesses and are not UFOTRI physics or physical validation.

## Harvest product interface

`CropCompartment.harvest(harvest_time)` returns `HarvestProduct` with:

| Field | Contract |
|---|---|
| `crop_id` | source crop identifier |
| `harvest_time` | caller-supplied `datetime` |
| `edible_activity` | edible activity boundary inventory, Bq |
| `edible_mass` | edible dry matter, kg |
| `activity_concentration` | derived edible activity concentration, Bq kg-1 dry matter |

The product record is a boundary interface only. It has no consumption rate,
dose coefficient, resident scenario, or public dose calculation.

## Mass-balance contract

All ledger quantities are integrated activity in Bq:

```text
closure_error =
    initial_inventory
  + leaf_input
  + soil_input
  - harvest_output
  - decay_loss
  - final_inventory
```

`internal_transfer` is reported as a positive, balanced internal movement and
does not appear in the global identity. For the current no-root-uptake seam,
`soil_input` is zero. The ledger rejects non-finite or negative terms and fails
closed when the closure error exceeds its declared tolerance.

## Validation status

The deterministic P3 tests cover plant and crop state validation, invalid
finite/non-negative values, leaf and soil coupling, placeholder parameter
rejection, provenance, zero transfer, synthetic transfer, deterministic
timestep repeatability, positivity protection, harvest product generation,
concentration calculation, and ledger closure.

```yaml
Framework: COMPLETE
Plant_state: PASS
Crop_abstraction: PASS
Harvest_interface: PASS
Mass_balance: PASS
Parameter_integration: PASS_SYNTHETIC_TEST_ONLY_FAIL_CLOSED_PLACEHOLDER
UFOTRI_food_chain_physics: NOT_IMPLEMENTED
Validated_parameters: NOT_IMPORTED
Human_intake: NOT_IMPLEMENTED
Dose_calculation: NOT_IMPLEMENTED
```
