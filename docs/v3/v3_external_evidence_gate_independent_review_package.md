# V3 external-evidence gate independent review package

## Review decision requested

Determine whether the remediation branch can proceed to maintainer merge
review. Do not merge as part of this review. The expected current production
verdict is:

```text
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Original P1 findings

1. Nonexistent manifest strings plus hand-edited booleans could produce
   `READY_FOR_BOUNDED_V3_PHYSICS`.
2. Soybean intake accepted nonnumeric air HTO and an empty detection-limit
   row because only CSV structure and declared unit strings were checked.

## Threat model

Review attempts should include missing, empty, directory, out-of-root, broken
or untracked artifact paths; malformed JSON/YAML; schema violations; byte and
checksum tampering; NaN/Inf and invalid physical ranges; inconsistent IDs,
hashes, commits, and evidence types; calibration/holdout reuse; invalid Git
chronology; and legacy readiness booleans set to true.

## Modified implementation files

```text
pyproject.toml
schemas/v3/external_*.schema.json
schemas/v3/v3_physics_gate_*.schema.json
validation/evidence_validation.py
validation/adapters/soybean_emras_adapter.py
validation/cases/soybean_emras_template.yaml
validation/v3/physics_start_gate.yaml
scripts/verify_v3_physics_start_gate.py
scripts/verify_v3_external_evidence_unblocking.py
tests/unit/test_v3_architecture_contracts.py
tests/unit/test_v3_external_evidence_adversarial.py
validation/external_local/README.md
docs/implementation_status.md
```

No `src/` or `configs/` file is modified.

## Review focus

- `validation/evidence_validation.py`: path containment, runtime schema
  execution, SHA-256 recomputation, Git object lookup, and ancestry checks.
- `validation/adapters/soybean_emras_adapter.py`: numeric rules,
  detection-limit/uncertainty mapping, timestamp/exposure checks, raw manifest
  validation, and generated-intake schema enforcement.
- `scripts/verify_v3_physics_start_gate.py`: absence of declaration-based
  release logic, cross-artifact hash/ID checks, evidence-type allowlist,
  preregistration/holdout chronology, frozen parameter reuse, finite metrics,
  and regression-result association.
- `tests/unit/test_v3_external_evidence_adversarial.py`: expected results are
  literal and independent; the complete positive-path fixture is isolated in
  a temporary Git repository and never referenced by production config.

## Statements that must not be trusted

The following legacy declarations have no authority and are rejected as
unexpected gate-config properties:

```text
complete_licensed_external_case
data_schema_valid
calibration_executed
external_holdout_executed
parameter_identifiability_assessed
```

The production result must be derived only from opened, schema-validated,
cross-linked artifacts and Git evidence.

## Suggested adversarial commands

```bash
.venv/bin/python -m pytest -q \
  tests/unit/test_v3_external_evidence_adversarial.py

.venv/bin/python scripts/verify_v3_external_evidence_unblocking.py

.venv/bin/python scripts/verify_v3_physics_start_gate.py

git diff main...HEAD -- src configs
git diff --check
```

Expected outcomes:

```text
ADVERSARIAL_TEST_STATUS = PASS
EXTERNAL_EVIDENCE_UNBLOCKING_STATUS =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0
```

## Independent review recommendation

```text
REMEDIATION_VERDICT =
READY_FOR_INDEPENDENT_ADVERSARIAL_REVIEW

MERGE_RECOMMENDATION =
HOLD_PENDING_INDEPENDENT_REVIEW
```
