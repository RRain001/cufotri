# V3-P7.6C-1 test report

## Focused validation suite

Command:

```text
.venv/bin/python -m pytest tests/unit/test_v3_parameter_validation.py tests/integration/test_v3_parameter_validation_manifest.py tests/architecture/test_v3_parameter_validation_boundary.py -q
```

Result: `11 passed`.

Coverage includes source preservation, explicit lineage, independent-stream
counting, duplicate/derived evidence, conflict-to-HOLD behavior, required
reconciliation method, candidate-to-validated lifecycle, ACTIVE rejection,
manifest round-trip, runtime isolation, and the one-half-life inventory
benchmark.

## P7.6A/P7.6B parameter regression

Command:

```text
.venv/bin/python -m pytest tests/unit/test_v3_parameter_evidence.py tests/unit/test_v3_parameter_candidate.py tests/unit/test_v3_parameter_applicability.py tests/unit/test_v3_pipeline_parameters.py tests/integration/test_v3_parameter_evidence_manifest.py tests/integration/test_v3_parameter_applicability_matrix.py tests/integration/test_v3_parameter_candidate_registry.py tests/architecture/test_v3_parameter_evidence_boundary.py -q
```

Result: `37 passed`.

The P7.6B source and candidate manifests remain stage-specific inputs. The new
P7.6C validation manifest adds the validation decision without overwriting
reported source records or changing candidate-screening history.

## Additional gates

Command:

```text
.venv/bin/python -m pytest tests/unit tests/integration tests/architecture -q
```

Result: exit 0; all `504` collected non-external unit, integration, and
architecture tests passed. One pre-existing NumPy binary-compatibility warning
was emitted by `tests/unit/test_era5_reader.py::test_netcdf_mapping`; it did
not fail the suite and no external/private data test was altered.

Additional checks:

```text
.venv/bin/python -m compileall -q src                         PASS
.venv/bin/python -c '<package and solver import smoke>'       PASS
git diff --check                                              PASS
```

No production simulation or GUI was started.
