# V3.1 Mass-Basis Contract — Independent Rereview R1 Result

## Verdict

```ini
REVIEWER = codex-local-gpt-5.6-luna
REVIEW_ID = LOCAL_CODEX_GPT56LUNA_V3_1_REREVIEW_R1
REVIEW_DATE = 2026-08-26
REVIEWED_SHA = e28fd18033984e9fda252aa87b81b399b60ece1e
BASELINE_SHA = d24aa03b00dcb586a2d93e678f42cb7853b7c078
REREVIEW_BRANCH = codex/v3-1-mass-basis-independent-rereview-r1
VERDICT = HOLD_REMEDIATION_REQUIRED
IMPLEMENTATION_PR_MERGE_READY = FALSE
MAIN_MERGE_AUTHORIZED = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

The frozen target was independently checked in a detached worktree at
`/private/tmp/cteas_ufotri_mass_basis_rereview_r1`. Review artifacts are written
only on the rereview branch. The frozen implementation worktree was not edited.

## Target and ancestry gate

After `git fetch --all --prune`, the remote refs were:

```text
origin/codex/v3-1-mass-basis-contract                 e28fd18033984e9fda252aa87b81b399b60ece1e
origin/codex/v3-1-mass-basis-independent-rereview-r1 40bb9e75f6b649ca3a4df1663a101936662dc10a
origin/main                                           d24aa03b00dcb586a2d93e678f42cb7853b7c078
```

The baseline is an ancestor of the frozen target, and the frozen target is an
ancestor of the rereview branch. No target drift was observed:

```ini
REREVIEW_TARGET_DRIFT = PASS
```

The reviewer entered from the rereview handoff head
`40bb9e75f6b649ca3a4df1663a101936662dc10a`; the handoff packet tip
`5c5bb1148d83fb6cc34e7e21ef1f298439b7240a` remains historical pre-verdict
evidence and was not rewritten.

## Blocking checks

### 1. Prior whitespace-schema blocker — PASS

The serialized fields governed by Python `_require_text()` were enumerated:
`subject_id`, string tissue and area identifiers, four provenance text fields,
and string `conversion_evidence_id`. The focused tests passed, and a reviewer
side matrix tested all eight field locations against `""`, `" "`, `"   "`,
`"\\t"`, `"\\n"`, and `" \\t\\n "` with no Python/schema rejection mismatch.

The matrix also checked all 29 Python whitespace code points for
`subject_id`; none was accepted by the schema while rejected by Python.

### 2. Numerical basis conversion — PASS

The V3.1 production source diff adds only
`src/cteas_ufotri/plant/mass_basis_v3_1/`. `BasisConversionEvidence` contains
only basis/scope/provenance/evidence-ID/pair metadata. There is no conversion
factor, multiplier, fraction, density, ratio, or numerical conversion path.
`validate_conversion_proposal()` returns governance status only and performs no
value calculation. No existing runtime imports the module.

### 3. Explicit source/target pairing — PASS

`PairedMeasurement` in `contract.py` requires `pair_id`,
`source_measurement_id`, and `target_measurement_id`. The implementation does
not accept a flat measurement-ID list as evidence.

### 4. Pair reuse fail-closed — PASS

The implementation rejects self-pairs, duplicate `pair_id` values, and any
reused measurement ID across the flattened source/target positions. Reviewer
side attacks rejected duplicate pair IDs, source reuse, target reuse, and reuse
of a prior target as a later source.

### 5. Tissue-scope evidence binding — PASS

`validate_conversion_proposal()` requires source and target contracts to have
the same tissue scope, then requires evidence tissue scope to equal that
scope. A mismatched tissue evidence record was rejected independently of the
existing tests.

### 6. Area-basis evidence binding — PASS

The same fail-closed path requires identical source/target area bases and
requires evidence area basis to equal that basis. A mismatched area evidence
record was rejected independently of the existing tests.

### 7. Evidence-ID binding — FAIL, BLOCKING

Finding:

```text
file: src/cteas_ufotri/plant/mass_basis_v3_1/contract.py
symbol: validate_conversion_proposal
lines: 313-315, before the evidence-ID checks at 329-338
failure: same-basis proposals return IDENTITY_ONLY before validating declared evidence
```

Reproduction on the frozen target:

```python
source = MassBasisContract(
    subject_id="s", mass_basis=MassBasis.FRESH_MASS,
    tissue_scope=TissueScope(TissueScopeKind.LEAF),
    area_basis=AreaBasis(AreaBasisKind.GROUND_AREA),
    provenance=BasisProvenance("src", "loc", "rev"),
    conversion_status=ConversionStatus.EVIDENCE_DECLARED,
    conversion_evidence_id="declared-id",
)
target = MassBasisContract(
    subject_id="t", mass_basis=MassBasis.FRESH_MASS,
    tissue_scope=TissueScope(TissueScopeKind.LEAF),
    area_basis=AreaBasis(AreaBasisKind.GROUND_AREA),
    provenance=BasisProvenance("src", "loc", "rev"),
)

validate_conversion_proposal(source, target, None)
# returns ConversionStatus.IDENTITY_ONLY

validate_conversion_proposal(source, target, evidence_with_id("other-id"))
# also returns ConversionStatus.IDENTITY_ONLY
```

Thus a contract that declares `EVIDENCE_DECLARED` can bypass both missing and
conflicting supplied evidence-ID checks whenever the two contracts have the
same mass basis. This violates the contract's explicit evidence-ID binding and
the rereview requirement that no bypass path is allowed. It is blocking even
though same-basis numerical conversion is not performed.

Required remediation boundary: the implementation owner must make the
same-basis path validate or reject an `EVIDENCE_DECLARED` state before returning
`IDENTITY_ONLY`, while preserving the no-numerical-conversion boundary. The
reviewer did not modify `src/` or `schemas/` to make the gate pass.

### 8. Python/JSON Schema boundary — PASS for the declared V3.1 boundary

The schema enum values, required fields, nullability, version, conditional
`conversion_evidence_id`, additional-property restrictions, and custom
identifier rules align with the Python contract. Whitespace parity is covered
above. The schema persists `MassBasisContract` metadata only; the Python
`BasisConversionEvidence` and `PairedMeasurement` governance objects have no
claimed persisted schema in V3.1, consistent with the contract documents.

### 9. Frozen runtime isolation — PASS

The complete baseline-to-target source diff contains only the new V3.1 module;
there are no changes under the existing leaf-resistance, TFWT, OBT, soil, root,
food, exposure, or `v3_pipeline` paths. A direct protected-runtime diff returned
zero differences, and no protected runtime file imports `mass_basis_v3_1`.
The existing isolation test and blob checks passed in the focused run.

The separate current invariant run had one failure in the unchanged P7.7B
synthetic benchmark registry check; that failure is recorded below and is not
attributed to the V3.1 source diff.

### 10. P7.8B-2 scope compliance — PASS

The changed implementation is limited to mass basis, tissue scope, area basis,
provenance, paired evidence metadata, and fail-closed governance checks. No
solver physics, dynamic stomata, OBT/root/soil/food implementation, calibration,
parameter activation, physical-validation declaration, or V4 implementation was
added. The declared boundary remains:

```ini
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

## Local verification

Environment:

```text
Darwin 25.4.0 arm64
Python 3.12.13 (uv isolated project environment)
pytest 9.1.1
jsonschema 4.26.0
```

Results on the frozen target:

```ini
LOCAL_FOCUSED_TESTS = 20 passed
COMPILEALL = PASS
IMPORT_SMOKE = PASS
LOCAL_PORTABLE_SUITE = 993 passed, 1 skipped, 57 deselected, 1 failed, 1 warning
LOCAL_INVARIANTS = 72 passed, 1 failed
GIT_DIFF_CHECK = PASS
FROZEN_RUNTIME_ISOLATION = PASS
```

The portable-suite failure and invariant-suite failure are both
`tests/v3/test_p7_7b_synthetic_benchmarks.py::test_checked_in_result_registry_matches_a_fresh_execution`.
The target-vs-baseline diff confirms that this test, its validation module, and
the checked-in result registry were unchanged by V3.1. The warning was the
existing NumPy/netCDF binary-compatibility warning from
`tests/unit/test_era5_reader.py::test_netcdf_mapping`.

The focused commands were:

```text
python -m pytest tests/v3_1/test_mass_basis_contract.py \
  tests/v3_1/test_mass_basis_schema_whitespace.py \
  tests/architecture/test_v3_1_mass_basis_isolation.py
python -m compileall -q src
python -c '<V3 import smoke>'
python -m pytest -m 'not external_sb1_data and not external_sb4_data and not external_era5_data and not private_reblinding_secret and not historical_review_context'
```

`uv run` supplied the isolated Python environment because the host did not
provide a `python` command or preinstalled pytest/project dependencies.

## Exit decision

The whitespace/schema remediation, numerical-conversion boundary, pair
governance, scope binding, schema boundary, runtime isolation, and P7.8B-2
scope checks passed. The same-basis `EVIDENCE_DECLARED` early-return path is a
reproducible blocking defect. Therefore this rereview cannot authorize merge
readiness:

```ini
STATUS = HOLD_REMEDIATION_REQUIRED
IMPLEMENTATION_PR_MERGE_READY = FALSE
MAIN_MERGE_AUTHORIZED = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

No implementation remediation, parameter activation, physical validation, or
V4 work was performed by this review.
