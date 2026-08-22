# V3-P7.5B numerical coupling semantics test report

Status: `PASS_NUMERICAL_COUPLING_SEMANTICS_FROZEN`

## Focused tests

```text
PYTHONPATH=.:src .venv/bin/pytest -q \
  tests/integration/test_v3_pipeline_numerical_semantics.py \
  tests/unit/test_v3_pipeline_parameters.py \
  tests/integration/test_v3_pipeline.py \
  tests/architecture/test_v3_pipeline_boundary.py
```

The P7.5B numerical-semantics module covers:

- frozen operator ordering and step-start root soil ownership;
- interval forcing and common endpoint timestamp invariants;
- non-mutating food/intake/dose endpoint readout semantics;
- multi-step zero-forcing invariance;
- `dt`, `dt/2`, and `dt/4` refinement;
- subsystem ledger closure at each refinement;
- two-step continuous-versus-serialized-restart equivalence.

Result: `19 passed` (`7` P7.5B numerical-semantics tests, `3` P7.5
parameter tests, `5` existing P7.5 integration tests, and `4` P7.5
architecture-boundary tests).

## Refinement case

The case uses the same initial inventories, constant synthetic forcing, and a
fixed 40 s horizon for every step size.  The soil half-life is 1000 s to
produce a non-trivial but controlled refinement signal.  `E1` is the absolute
difference between `dt` and `dt/2`; `E2` is the absolute difference between
`dt/2` and `dt/4`.

| continuous inventory | dt = 10 s | dt/2 = 5 s | dt/4 = 2.5 s | E1 | E2 | E2/E1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Soil | 39.158888134015 | 39.236379166632 | 39.272473747491 | 0.077491032617 | 0.036094580859 | 0.465790423 |
| TFWT | 68.258234685011 | 68.589713271921 | 68.760994416721 | 0.331478586910 | 0.171281144800 | 0.516718580 |
| OBT | 18.350186103291 | 18.008672784009 | 17.835010764654 | 0.341513319282 | 0.173662019355 | 0.508507310 |

All values are finite and non-negative, and all three rows satisfy `E2 < E1`.
The ratios are empirical refinement diagnostics, not claimed formal orders.

The complete requested cross-stage command passed `176` tests:

```text
architecture: 48
unit:         82
integration:  45
regression:    1
```

This includes the P7 atmosphere interface, P6.2B-P6.6B typed boundaries,
the P7.5 pipeline tests, the P7.5B focused module, architecture checks, and
the existing timestep regression.

## Conservation and invariants

For `dt`, `dt/2`, and `dt/4`, the existing soil, TFWT, OBT, root, and food
balance residuals were finite and zero within the existing solver tolerance.
The multi-step zero-forcing case kept Soil, TFWT, OBT, root transfer, food,
intake, and dose at zero without artificial inventory creation.  No new
tolerance or physical accuracy threshold was introduced.

The restart test compared:

```text
initial -> step 1 -> step 2
initial -> step 1 -> JSON serialize/deserialize -> step 2
```

Soil, TFWT, OBT, root, food, intake, dose, endpoint timestamp, and the full
typed state were equal on the two paths.

## Test boundary

These are synthetic typed-interface and numerical-coupling regression tests.
They do not use UFOTRI parameters, real ERA5 data, real CTEAS-Atmos data,
field observations, calibration, production cases, or regulatory assessment.
