# V3-P6.2B-2 TFWT Solver Test Report

## New physical and boundary tests

Command:

```text
PYTHONPATH=. ./.venv/bin/python -m pytest -q \
  tests/unit/test_tfwt_solver.py \
  tests/integration/test_tfwt_storage_interface.py \
  tests/architecture/test_tfwt_solver_boundary.py
```

Result: `15 passed`.

The tests cover:

- positive constant leaf input increasing TFWT;
- negative signed leaf input decreasing TFWT when air input is zero;
- `input = storage increase + water loss + transformation`;
- fixed water-content concentration/inventory consistency;
- direct P6.2B-1 resistance-flux-to-TFWT flow;
- no resistance recomputation in the TFWT solver;
- invalid interval, loss, transformation, state, and negative-inventory gates;
- no OBT/root/soil/dose state creation;
- configs, trusted registry, and legacy V1/V2 paths unchanged.

## Existing regression suites

The P6.2B-1 baseline suites were rerun after the TFWT addition:

```text
PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/unit
PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/integration
PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/regression
```

All three commands returned exit code `0`. The unit suite retains one existing
NumPy/netCDF binary-compatibility warning from
`tests/unit/test_era5_reader.py::test_netcdf_mapping`; it is unrelated to the
new TFWT package.

Additional static check:

```text
git diff --check origin/main..HEAD
```
