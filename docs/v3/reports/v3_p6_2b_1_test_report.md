# V3-P6.2B-1 Resistance Subsystem Test Report

## Targeted tests

Command:

```text
PYTHONPATH=. ./.venv/bin/python -m pytest -q \
  tests/unit/test_leaf_exchange_resistance.py \
  tests/integration/test_leaf_exchange_resistance_interface.py \
  tests/architecture/test_leaf_exchange_resistance_boundary.py
```

Result:

```text
15 passed
```

Coverage includes:

- `r_a + r_b + r_c` and `g_ex = 1 / r_tot`;
- exact SI unit rejection;
- zero and negative resistance rejection;
- forcing/provenance validation;
- missing parameter rejection without fallback;
- explicit `production=False` database lookup;
- ACTIVE parameter rejection;
- positive air-to-leaf and negative leaf-to-air signed flux;
- absence of a second re-emission field;
- default configuration and protected-path boundaries.

## Existing regression suites

The following commands were executed successfully:

```text
PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/unit
PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/integration
PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/regression
```

All three suites returned exit code `0`. The unit suite emitted one existing
`numpy.ndarray size changed` runtime warning from
`tests/unit/test_era5_reader.py::test_netcdf_mapping`; no test failed.

Additional static verification:

```text
git diff --check origin/main..HEAD
```

## Interpretation

The tests establish the resistance-chain and interface behavior only. They do
not constitute UFOTRI experimental validation, TFWT validation, OBT
validation, or production-model validation.
