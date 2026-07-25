# V3 start gate assessment

## Sole verdict

```text
V3_GATE_VERDICT =
READY_FOR_V3_ARCHITECTURE_ONLY_EXTERNAL_VALIDATION_CONTINUES
```

This verdict allows V3 architecture, interfaces, migration planning, data
models, and experimental branches. It does not authorize formal V3 physics
expansion, a claim of accepted V3 physics, or merging broad new physics to
`main`.

## Gate assessment

| Gate | Result | Evidence and limitation |
|---|---|---|
| 1. Stable V2 baseline | PASS | Candidate and V1 tags are unchanged; V1 and V2 recomputation pass; this validation-only diff introduces no new formal-physics BLOCKER/HIGH. |
| 2. External forcing | PASS | 72/72 ERA5 reanalysis hours were executed. The third day changes downstream inventories, proving that deterministic extension was not neutral. ERA5 remains forcing, not site HTO evidence. |
| 3. Independent reference model | PASS | One independently coded bounded case executed; all eight declared metrics pass. |
| 4. Experiment or field evidence | BLOCKED_EXTERNAL_DATA | No complete controlled experiment or matched field package met the minimum reproducibility and licence contract. No empirical case was executed. |
| 5. Parameter identifiability | NOT_ASSESSED | With no executable external experiment or field case, no parameter has a defensible calibration/holdout identifiability conclusion. |
| 6. Evidence-driven V3 gaps | PASS_BOUNDED | Candidate topics are tied to documented manual-fidelity gaps, architecture limits, forcing workflow evidence, or explicit missing calibration data. Feature-list-only expansion is excluded. |

## Why the stronger verdict is not allowed

`READY_FOR_V3_ARCHITECTURE_AND_BOUNDED_IMPLEMENTATION` requires at least one
executed experimental or field case and a conclusion about key bias and
parameter identifiability. Both are absent. The independent reference result,
although strong, is numerical rather than empirical.

## Why the not-ready verdict is not selected

The baseline is stable, validation infrastructure is on `main`, complete
72-hour reanalysis forcing was executed, an independent reference case was
executed, and the remaining V3 boundaries are explicit. These facts are
sufficient for architecture work, even though they are insufficient for formal
physics expansion.

## Conditions for the next stronger verdict

Before bounded V3 physics implementation:

1. acquire one complete, legally usable experiment or co-located field package;
2. commit a preregistration before inspecting validation-period performance;
3. use separate calibration and holdout data or independent repeats;
4. report parameter bounds, correlations, boundary hits, and non-identifiability;
5. diagnose any failure by equation, state definition, units, area, time
   discretization, boundary, and parameter semantics before tuning;
6. rerun V1 regression, full V2 acceptance, validation readiness, and the
   external holdout case.

## Preservation boundary

The V2 candidate tag remains the immutable reproducibility anchor. Future V3
architecture must load or migrate V2 cases without changing the behavior
identified by that tag. No V3 branch or V3 model code was created in this
phase.
