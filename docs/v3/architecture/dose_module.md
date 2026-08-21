# V3-P4 Dose Interface Framework

Status: `FRAMEWORK_COMPLETE`

UFOTRI dose physics: `NOT_IMPLEMENTED`

Validated dose coefficients: `NOT_IMPORTED`

UFOTRI numerical equivalence: `NOT_CLAIMED`

## Responsibility and boundary

P4 establishes the software boundary from an edible food product to a future
dose calculation:

```text
V3-P3 HarvestProduct
          |
          v
  ConsumptionPathway
          |
          v
  DoseCoefficient seam
          |
          v
     DoseState + DoseLedger
```

The package owns typed pathway and age-group records, coefficient provenance,
an injected calculation seam, an interface result state, and an auditable
activity ledger. It does not import UFOTRI dose equations, ICRP coefficients,
GB/T 18871 parameters, Chinese dietary survey data, public-dose compliance
rules, or regulatory assessment logic.

The existing V2 research-screening implementation in
`src/cteas_ufotri/dose/public.py` is retained unchanged. P4 adds interface
records and kernels alongside that legacy path; it does not route V2 cases
through P4 or change V2 configuration semantics.

## Consumption pathway

`ConsumptionPathway` is crop-agnostic and contains:

| Field | Contract |
|---|---|
| `food_id` | caller-defined product identifier |
| `food_activity` | product activity concentration, `Bq kg-1 food` |
| `consumption_rate` | interface consumption rate, `kg s-1` |
| `exposure_duration` | exposure duration, `s` |
| `age_group` | one of `infant`, `child`, `adult` |

The interface intake activity is the dimensionally explicit product
`food_activity * consumption_rate * exposure_duration` in Bq. The framework
does not contain rice, vegetable, local-fraction, dietary-survey, or age-group
rate values.

`ConsumptionPathway.from_product()` accepts a V3-P3 `HarvestProduct` and
maps its edible activity concentration and crop identifier into this generic
boundary without adding a human-intake or dose assumption.

## Age-group abstraction

`AgeGroup` is an enum with exactly three labels:

```text
infant
child
adult
```

It contains no consumption rates, dose coefficients, body masses, or other
age-specific numerical assumptions. Those values remain future parameter and
evidence inputs.

## Dose state and coefficient interface

`DoseState` contains `radionuclide`, `pathway`, `age_group`,
`intake_activity`, `dose_coefficient`, `committed_dose`, and `time`.

| Quantity | Unit |
|---|---|
| `intake_activity` | Bq |
| `DoseCoefficient.coefficient` | `Sv Bq-1` |
| `DoseState.committed_dose` | Sv |
| `DoseState.time` | `datetime` |

`DoseCoefficient` additionally records the radionuclide, explicit coefficient
unit, source provenance, parameter name, and `PLACEHOLDER` status. Numeric
values used by P4 are resolved only with `ParameterDatabase`; the framework
test database is synthetic and has no validated scientific status.

## Physics seam

The canonical low-level interface is:

```python
result = calculate(pathway, coefficients, parameters, kernel=kernel)
```

`FrameworkOnlyPhysics` fails closed until reviewed dose physics is available.
`ZeroDoseKernel` preserves the activity transfer but returns zero dose solely
for flow tests. `SyntheticDoseKernel` calculates
`consumption_transfer * dose_coefficient` solely to test the numerical chain.
Neither kernel represents UFOTRI, ICRP, GB/T 18871, regulatory, or public-dose
calculation.

## Dose ledger

`DoseLedger` records:

```text
input_activity
consumption_transfer
dose_coefficient
calculated_dose
uncertainty
closure
status
```

`input_activity` and `consumption_transfer` are Bq; the coefficient is `Sv
Bq-1`; dose and uncertainty are Sv; closure is an activity residual in Bq:

```text
closure = input_activity - consumption_transfer
```

The ledger rejects non-finite or negative activity, coefficient, dose, and
uncertainty values. Zero and synthetic kernels both close the activity audit;
the zero kernel's status explicitly records that dose arithmetic was skipped.

## Provenance

`DoseParameters`, `DoseCoefficient`, and `DoseModel.provenance()` retain the
parameter database SHA-256, entry-level source provenance, kernel status,
implementation status, and the explicit `NOT_CLAIMED`/`NOT_IMPLEMENTED`
boundary. No coefficient is silently defaulted, replaced, or imported from an
external regulatory database.

## Validation status

The deterministic P4 tests cover state initialization and consistency,
finite/non-negative failure modes, generic pathways, age-group labels,
coefficient unit and provenance validation, placeholder parameter rejection,
zero-dose flow, synthetic dose arithmetic, deterministic repeatability,
fail-closed default physics, ledger closure, and invalid results.

```yaml
Framework: COMPLETE
Dose_state: PASS
Consumption_pathway: PASS
Age_group_interface: PASS
Coefficient_interface: PASS
Dose_ledger: PASS
Parameter_integration: PASS_SYNTHETIC_TEST_ONLY_FAIL_CLOSED_PLACEHOLDER
UFOTRI_dose_physics: NOT_IMPLEMENTED
Validated_coefficients: NOT_IMPORTED
Regulatory_assessment: NOT_IMPLEMENTED
UFOTRI_numerical_equivalence: NOT_CLAIMED
```
