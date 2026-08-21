# V3-P6.2A Leaf-Exchange Physics Specification Report

## Result

```ini
P6_2A_STATUS = PASS_PHYSICS_SPECIFICATION_READY
LEAF_EXCHANGE_IMPLEMENTATION = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
DEFAULT_MODEL_BEHAVIOR_CHANGED = FALSE
NEXT_PHASE = P6_2B
```

P6.2A freezes the V3 leaf-exchange physics boundary and evidence requirements.
It does not implement a leaf-exchange solver, import a numerical UFOTRI
parameter, enable a runtime path, or change atmospheric, soil, or dose code.

## Git and baseline evidence

```text
SPEC_BRANCH = codex/v3-p6-2a-leaf-exchange-specification
INDEPENDENT_REVIEW_BRANCH = codex/v3-p6-2a-independent-review
BASE = origin/main@6671f5793d04842bf2ceae4904f3c0cf30a0d7e0
SPEC_COMMIT = 0dd11e9
P6_1_REFERENCE = codex/v3-p6-1-independent-review@e3e70b8
P6_1_MERGED_INTO_MAIN = FALSE
```

The specification commit contains only documentation, architecture tests,
and future parameter-acquisition metadata. The independent review branch was
created from the frozen specification commit and was not merged into either
the specification branch or `main`.

## Delivered artifacts

1. `docs/v3/ufotri_database/leaf_exchange_physics_source_audit.md` records
   UFOTRI manual §§2.2.2, 2.2.6 and §3.3.1 evidence, units, dependencies,
   applicability, uncertainty gaps, and the four required classifications.
2. `docs/v3/physics/leaf_exchange_model.md` freezes the future `PlantState`,
   `AtmosphericHTOForcing`, module flow, output ownership, and lifecycle
   boundary.
3. `docs/v3/physics/leaf_exchange_equations.md` freezes the resistance chain,
   air/leaf flux sign, TFWT dynamic and inventory forms, TFWT-to-OBT transfer,
   day/night state, re-emission, and conservation identity without runnable
   code or values.
4. `validation/external_evidence_acquisition/leaf_exchange_parameter_requirements.yaml`
   declares future table requirements for resistance, exchange, and OBT rates;
   every value is `null`, every entry is `REQUIRED`, and imported/validated/
   active flags are false.
5. `tests/architecture/test_leaf_exchange_specification_boundary.py` checks
   implementation absence, lifecycle gating, PlantState/forcing compatibility,
   default behavior, source classification, and regression-contract boundaries.
6. `docs/v3/regression/leaf_exchange_regression_contract.md` freezes future
   Case A/B/C inputs, qualitative expectations, conservation checks, and the
   tolerance-definition method without results.

## Independent review disposition

| Review question | Result | Evidence |
|---|---|---|
| Hidden V3 leaf-exchange implementation added? | PASS | No `src/leaf_exchange/`; no `src/` diff; existing V1/V2 plant files unchanged |
| UFOTRI parameter secretly imported or activated? | PASS | Requirement YAML has null values, `imported: false`, `validated: false`, `active: false`; no production parameter path changed |
| Default configuration changed? | PASS | `plant.leaf_exchange_mode: off`, `direct_leaf_uptake_enabled: false`; no `configs/` diff |
| Model outputs changed? | PASS | No calculation code changed; regression file is specification-only and results are `NOT_EXECUTED` |
| Manual values called validated? | PASS | Audit separates explicit, derived, assumption, and missing; manual representative values remain assumptions or unvalidated source relations |
| Lifecycle exceeded `REVIEWED`? | PASS | Database remains `PLACEHOLDER`; active transition is disabled; no validated claim is made |

## Verification

Executed on the specification branch and repeated on the independent review
branch:

```text
./.venv/bin/python -m pytest -q tests/architecture/test_leaf_exchange_specification_boundary.py
9 passed
```

Also passed:

```text
git diff --check origin/main..HEAD
```

The only path under the protected-path audit output is the permitted future
requirement metadata file under
`validation/external_evidence_acquisition/`. No source, default config,
production parameter, trusted registry, soil, atmosphere, or dose path was
modified.

## Gate conclusion

The database is specification-ready, not runtime-ready. P6.2B may implement
leaf-exchange physics only after preserving this boundary and acquiring the
required evidence/uncertainty package. It must not promote manual values to
`VALIDATED` or `ACTIVE` without independent experimental validation.
