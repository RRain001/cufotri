# V3 Framework vs Physics Boundary

Status: `P5.6_ARCHITECTURE_RECONCILED`

This document is the terminology and activation boundary for the current V3
repository. It distinguishes reusable computational scaffolding from formal
UFOTRI physics. A passing framework test is not evidence that UFOTRI physics is
validated.

## Definitions

Framework material may include:

- state containers and typed interfaces;
- provenance and parameter-registry records;
- activity and mass-balance ledgers;
- fail-closed placeholders and dispatch seams;
- deterministic synthetic numerical test harnesses.

Formal physics requires all of the following before it can be described as
started:

1. an equation or algorithm traced to the reviewed UFOTRI source;
2. numerical coefficients or functions with an approved source citation;
3. units, applicability, uncertainty, and lifecycle metadata;
4. an independently reproducible benchmark or reference result; and
5. an explicit activation review that keeps the V2 compatibility path isolated.

The words `implemented`, `validated`, `UFOTRI equivalent`, and `production
ready` must not be used without the qualifier and evidence that identify which
of these two categories is meant. In particular, `FRAMEWORK_READY = TRUE` does
not imply `PHYSICS_READY = TRUE`.

## Current repository classification

| Module | Current classification | What is present | What is not established |
|---|---|---|---|
| Atmosphere | `RESEARCH_PROTOTYPE` | Gaussian HTO transport in the V1/V2 baseline | V3 formal UFOTRI physics |
| Soil | `EXPERIMENTAL_NUMERICAL_FRAMEWORK` | state/inventory seams, synthetic transport, inherited experimental multibox code | UFOTRI soil equations and reviewed root uptake |
| Leaf exchange | `NUMERICAL_HARNESS` | TFWT/OBT state, ledger, and test-only synthetic kernels | UFOTRI exchange equation, resistance, conductance, or validated coefficient |
| Food chain | `COMPUTATIONAL_FRAMEWORK` | plant/crop state, harvest seam, test-only transfer kernel | UFOTRI transfer factors and validated food-chain pathway |
| Dose | `COMPUTATIONAL_FRAMEWORK` | pathway, age-group types, and test-only intake arithmetic | regulatory or UFOTRI dose coefficients and assessment |
| Parameter DB | `GOVERNANCE_LAYER` | schema, provenance, lifecycle, and placeholder declarations | active validated UFOTRI values |
| UFOTRI physics | `ABSENT` | fail-closed migration seams | formal V3 physics implementation |

## Synthetic kernel policy

`SyntheticLinearLeafExchangePhysics`, `SyntheticTransportKernel`,
`SyntheticTransferKernel`, and `SyntheticDoseKernel` are computational test
harnesses. Their numerical outputs are useful for state, ledger, and adapter
checks only. They are not UFOTRI equations, reference outputs, empirical
validation, or regulatory evidence.

The unit modules that exercise them declare
`TEST_CLASSIFICATION = "FRAMEWORK_TEST_ONLY"`. Architecture tests must keep
that declaration and the `TEST_ONLY` kernel status visible.

## Parameter activation policy

`parameters/databases/ufotri_leaf_exchange.yaml` contains null placeholder
values. `UFOTRI_VALIDATED` is a reserved source identifier whose registry
status is `external_reference_required` and whose production permission is
false. Therefore:

```text
UFOTRI_VALIDATED_DATABASE = ABSENT
UFOTRI_PARAMETER_IMPORTED = FALSE
```

No P5.6 change may add a parameter value, change formal configuration, or
modify the trusted external-evidence registry.

## Frozen boundary

```text
FRAMEWORK_READY = TRUE
PHYSICS_READY = FALSE
FORMAL_PHYSICS_STARTED = FALSE
V3_FORMAL_PHYSICS = NOT_STARTED
NEXT_PHASE = UFOTRI_PARAMETER_AND_PHYSICS_IMPLEMENTATION
```

Formal V3 physics has not started.

The ordered work packages for that next phase are frozen in
`docs/v3/roadmap/v3_physics_roadmap.md`.
