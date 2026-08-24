# V3-P7.6C-1 physical-constant validation report

## Verdict

```ini
P7_6C1_STATUS = PASS_PHYSICAL_CONSTANT_VALIDATION
PHYSICAL_CONSTANT_VALIDATION_COMPLETE = TRUE
SOIL_TRITIUM_HALF_LIFE = VALIDATED
VALIDATED_PARAMETER_COUNT = 1
ACTIVE_PARAMETER_COUNT = 0
EVIDENCE_RECONCILIATION = PASS
UNCERTAINTY_PROVENANCE = PASS
DECAY_SEMANTIC_BENCHMARK = PASS
CALIBRATION_STARTED = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
```

The decision validates only the universal H-3 radioactive half-life as the
quantity used by the existing V3 decay term. It does not validate soil
retention, transport, plant uptake, OBT dynamics, exposure, dose, or any
environmental effective half-life.

## Equation and applicability

The actual V3 soil implementation keeps `T_half` as an explicit caller-owned
value in seconds and computes:

```text
lambda_T = ln(2) / T_half
```

The validation freezes the semantic mapping:

```text
soil.tritium_half_life = universal H-3 nuclear half-life
```

It rejects the interpretations `effective soil half-life`, `environmental
residence half-life`, `biological elimination half-life`, and `OBT turnover
half-life`. No chemical-form correction is inserted into the V3 equation.

## Selected decision

The selected value is the later DDEP/BIPM evaluated recommendation:

```text
T_half = 388540800 s +/- 777600 s
```

This is the normalized form of `4497 +/- 9 d`. The NIST value remains a
separate source record (`388800000 s +/- 691200 s`) and was not overwritten or
averaged with the selected value.

The decision record is in
`docs/v3/parameter_evidence/physical_constant_validation_registry.yaml`.
The source records are also kept in that manifest under `evidence_records`.

## Limitations

DDEP identifies its evaluated value as a molecular-tritium evaluation and
notes a small atomic-tritium difference. This stage records that limitation;
the current interface deliberately has no chemical-form-specific correction.
The uncertainty is the source one-standard-uncertainty convention, not a
combined environmental or scenario uncertainty. The result is therefore a
decay-constant validation only.
