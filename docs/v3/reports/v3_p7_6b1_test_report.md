# V3-P7.6B-1 applicability review test report

Status: `PASS_PARAMETER_APPLICABILITY_REVIEW`

## Focused command

```text
PYTHONPATH=.:src .venv/bin/pytest -q \
  tests/unit/test_v3_parameter_applicability.py \
  tests/integration/test_v3_parameter_applicability_matrix.py \
  tests/architecture/test_v3_parameter_applicability_boundary.py \
  tests/unit/test_v3_parameter_evidence.py \
  tests/integration/test_v3_parameter_evidence_manifest.py \
  tests/architecture/test_v3_parameter_evidence_boundary.py
```

Result: **24 tests passed**. The P7.6B-1-only subset is 12/12; the other 12
are the P7.6A evidence/provenance regression tests.

Coverage includes:

- immutable applicability records and strict required-field decoding;
- all five applicability dispositions and alias round-trip behavior;
- direct/partial candidate criteria, uncertainty requirement, and
  provisional/test-only blocking;
- exact 76-record inventory coverage, metadata consistency, deterministic
  ordering, and matrix round-trip;
- `UNKNOWN`/`NOT_APPLICABLE` gate blocking and zero-candidate result;
- protected-path, solver-import, and fresh-process isolation checks.

## Cross-stage compatibility

The explicit P6.2B–P7.5B compatibility selection retained the P7.6A
evidence-boundary test and excluded only the new P7.6B-1 boundary test from
the historical set. It passed **180 tests**. The new P7.6B-1 tests were
executed separately above, so the historical regression and current-stage
acceptance remain distinguishable.

Additional checks passed:

- `PYTHONPATH=.:src .venv/bin/python -m compileall -q
  src/cteas_ufotri/parameters_v3`;
- manifest/matrix import smoke: 76 inventory records, 76 review records,
  0 candidates, 76 blocked, `VALIDATED=0`, `ACTIVE=0`;
- `git diff --check`.

## Test boundary

These checks establish the applicability control plane and its software
isolation only. They do not establish literature applicability, physical
validation, empirical evidence, parameter calibration, regulatory validity,
UFOTRI database activation, or V3 physics readiness.
