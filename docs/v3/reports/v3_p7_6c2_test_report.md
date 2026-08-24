# V3 P7.6C-2 test report

```text
TEST_STATUS = PASS
TARGETED_TESTS = 8
PYTHON_COMPILE = PASS
GIT_DIFF_CHECK = PASS
```

## Executed checks

Command:

```text
PYTHONPATH=. .venv/bin/pytest -q tests/unit/test_ufotri_mapping.py
```

Result: `8 passed`.

The targeted suite verifies:

1. all 26 required V3 parameters are represented exactly once;
2. deterministic mapping-status counts;
3. P7.6C-1 `validated=1/active=0` and P7.6C-2 fail-closed flags;
4. immutable record construction and YAML round-trip;
5. direct mappings reject incompatible equation/unit relationships;
6. transformable mappings require an explicit derivation;
7. conceptual/no/source-unavailable records cannot enter validation;
8. intake/dose scenario or external mappings do not enter physical validation;
9. runtime plant/soil/exposure/coupling code has no mapping-control-plane
   import.

Additional checks:

```text
PYTHONPATH=. .venv/bin/python -m compileall -q \
  src/cteas_ufotri/parameters_v3/ufotri_mapping.py \
  tests/unit/test_ufotri_mapping.py
git diff --check
```

Both returned success. No long production simulation, benchmark execution,
calibration, or V3 physics readiness check was run because those actions are
outside this stage.

## Broader regression context

The existing parameter-control and architecture suites were also run in the
same checkout:

```text
unit parameter suites = PASS
integration parameter-manifest suites = PASS
architecture parameter-boundary suites = PASS
```

The three existing D3 UFOTRI external-evidence test modules were not counted
as a P7.6C-2 pass because the checkout contains pre-existing external-state
failures unrelated to the new files. The observed failures were:

- protected-path comparison against `main` rejects the already-present V3
  implementation history between `main` and the authorized P7.6C-1 base;
- the local SB1 external dataset is available, while the test expects the
  no-environment missing state;
- ERA5 verifier exit-code expectations do not match the currently installed
  local input state;
- the local private true-reblinding secret exists, while the public-contract
  test expects it to be absent;
- the external-evidence unblocking script consequently returns non-zero.

No source, config, private-data, or external-evidence file was changed to
force those tests. These failures are recorded as environment/base-branch
risks, not as evidence for or against the semantic mapping.
