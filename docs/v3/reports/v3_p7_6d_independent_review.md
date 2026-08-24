# V3 P7.6D Independent Review

```text
REVIEW_STATUS = PASS_PHYSICS_ADOPTION_DECISION_AND_FAIL_CLOSED
REVIEW_TYPE = CONTROL_PLANE_COMPLETENESS_AND_BOUNDARY_REVIEW
ALL_REDESIGN_ITEMS_REVIEWED = TRUE
PHYSICS_REDESIGN_IMPLEMENTED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
PARAMETER_VALUES_IMPORTED = FALSE
```

## Review checklist

| # | Review question | Verdict | Evidence |
|---:|---|---|---|
| 1 | Does the registry cover every P7.6C-3 item exactly once? | PASS | 26 mapped records plus one derived `leaf.g_ex` record are cross-checked by the registry loader |
| 2 | Are all nine `PHYSICS_REDESIGN_REQUIRED` items reviewed? | PASS | Each source feasibility record has one `REDESIGN_REQUIRED` decision and a priority-matrix entry |
| 3 | Is the current V3 baseline explicitly frozen? | PASS | Registry and ADR set `CURRENT_V3_MODEL = FROZEN` and forbid implementation |
| 4 | Are feasible records distinguished from adoption decisions? | PASS | `VALIDATE_CURRENT_MODEL`/`EXTEND_V3_PHYSICS` retain scope and do not select values |
| 5 | Are metadata, exposure, and dose items excluded? | PASS | Four records are `DO_NOT_IMPORT` and are blocked from physical validation |
| 6 | Is the unresolved product-mass item fail-closed? | PASS | `intake.food_product_mass` is `WAIT_FOR_EVIDENCE` |
| 7 | Are OBT `kf`/`kr` separated from missing OBT mechanisms? | PASS | `kf`/`kr` are scoped reduced-model extensions; day/night, photosynthesis, mass basis, and temperature require redesign |
| 8 | Is root rate prevented from becoming V3 velocity by name or unit scaling? | PASS | `root.k_root` is `REDESIGN_REQUIRED` with a rate/state/layer gap |
| 9 | Are food event and continuous representations separated? | PASS | Both harvest-fraction records require redesign and numerical-coupling review |
| 10 | Are coupling effects classified without changing coupling? | PASS | The impact report distinguishes no-impact, interface-only, and future numerical-coupling changes; current flag remains false |
| 11 | Can redesign records enter validation? | PASS | The P7.6D gate rejects every `REDESIGN_REQUIRED` record |
| 12 | Can any decision activate a parameter or start calibration? | PASS | Registry invariants require active=0, candidates=0, calibration=false, and activation=false |
| 13 | Do runtime owners import the decision registry? | PASS | Architecture boundary test scans plant, soil, exposure, coupling, and pipeline owners |

## Findings

The P7.6D adoption decisions are complete and consistent with the P7.6C-3
feasibility classes. The accepted baseline is deliberately conservative:
feasible means “future validation can be designed,” while redesign-required
means “validation is blocked until the V3 representation is redesigned.”

The highest-risk future work is the OBT formation scope, layered root uptake,
and food-chain event/continuous boundary. Root uptake and food-chain redesign
are the only current blockers explicitly classified as requiring a future
numerical-coupling change. No such change is part of P7.6D.

## Review boundary

This review is not an empirical validation, independent field comparison,
calibration, regulatory assessment, or claim of UFOTRI equivalence. It reviews
the decision-control artifacts and their runtime isolation only.

## Executed verification

- Targeted P7.6D, P7.6C-3, mapping, evidence, candidate, and applicability
  tests: `66 passed`.
- `compileall` for `src/cteas_ufotri/parameters_v3`: pass.
- YAML registry/reference and `git diff --check`: pass.
