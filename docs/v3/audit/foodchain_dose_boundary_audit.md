# Food Chain and Dose Boundary Audit

Audit basis: actual Python files under `src/cteas_ufotri/food_chain/` and
`src/cteas_ufotri/dose/`, plus the specified unit tests.

## Food chain

The food-chain package contains valid state/ledger records and a fail-closed
default kernel. It also contains behavior beyond a passive interface:

- `SyntheticTransferKernel` performs explicit-Euler first-order TFWT-to-OBT
  transfer and OBT decay.
- `CropCompartment.harvest()` produces edible activity, edible mass, and an
  activity concentration.
- `FoodChainModel` applies leaf inputs and can produce a harvested product.

These are generic/test-only framework behaviors and are not UFOTRI crop
transfer factors or validated food-chain physics. Under the literal P5 audit
rule, they are nevertheless numerical physics/output behavior.

## Dose

The dose package contains interface state and provenance records, but also:

- `AgeGroup` and `ConsumptionPathway` with food activity, consumption rate,
  duration, and intake activity;
- `DoseCoefficient` and committed-dose state fields;
- `SyntheticDoseKernel`, which multiplies intake activity by a supplied dose
  coefficient to produce a calculated dose.

The kernels and tests explicitly label values as test-only and not regulatory
or UFOTRI calculations. They are still more than a future API placeholder,
and the code path includes age-group ingestion and committed-dose arithmetic.

## Test classification

The requested unit tests contain numerical physics assertions:

| Test file | Evidence | Classification |
| --- | --- | --- |
| `test_leaf_exchange.py` | `SyntheticLinearLeafExchangePhysics`, expected TFWT/OBT and timestep values | `PREMATURE_PHYSICS_TEST` for synthetic numerical cases |
| `test_food_chain.py` | `SyntheticTransferKernel`, expected transfer/decay and harvest concentration | `PREMATURE_PHYSICS_TEST` for synthetic numerical cases |
| `test_dose.py` | `SyntheticDoseKernel`, expected committed dose and coefficient arithmetic | `PREMATURE_PHYSICS_TEST` for synthetic dose cases |

Placeholder/fail-closed and state-shape assertions remain architecture tests;
the classification applies specifically to numerical kernel tests.

## Boundary conclusion

No validated UFOTRI food-chain or dose model is imported. The repository does
contain test-only numerical food-chain/dose behavior and numerical expected
values, so the accumulated branch is not strictly interface-only.
