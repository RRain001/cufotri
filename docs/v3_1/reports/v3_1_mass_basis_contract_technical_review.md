# V3.1 Mass-Basis Contract Technical Review

## Review scope

This review covers PR #3 (`codex/v3-1-mass-basis-contract`) against the V3.1
selection and architecture boundary frozen by P7.8B-2.  The implementation
baseline is `main` at
`d24aa03b00dcb586a2d93e678f42cb7853b7c078`.

This is a separate audit pass over the implemented diff, schema, tests, and CI
evidence.  It is **not** represented as an externally independent review,
because the same assistant that performed this audit also implemented the
changes in this work session.  The formal independent-review exit gate remains
open.

## Technical findings

### Scope isolation — PASS

The only new production-source path is
`src/cteas_ufotri/plant/mass_basis_v3_1/`.  No pre-existing V3 solver, state,
food, exposure, parameter, or pipeline source file is modified.

`tests/architecture/test_v3_1_mass_basis_isolation.py` locks the Git blob IDs
for the frozen pipeline, leaf resistance, TFWT, OBT, soil, root, and food
solver/state paths and verifies that none imports `mass_basis_v3_1`.

Result:

```text
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
P7_5_SEMANTICS_CHANGED = FALSE
P7_5B_SEMANTICS_CHANGED = FALSE
EXISTING_STATE_SERIALIZATION_CHANGED = FALSE
```

### Typed basis semantics — PASS

`MassBasis` distinguishes `fresh_mass`, `dry_mass`, `water_mass`, and
`hydrogen_mass`.  `TissueScope` and `AreaBasis` are separately typed, with an
explicit identifier required for custom scopes.  Provenance requires a source
identifier, source locator, and revision.

Direct comparison is admitted only when mass basis, tissue scope, and area
basis are identical.  A mismatch raises `BasisCompatibilityError`; there is no
implicit denominator or area conversion.

### Cross-basis conversion boundary — PASS

V3.1 does not contain a numerical conversion coefficient, water fraction,
dry-matter fraction, hydrogen fraction, or crop-specific composition factor.
`BasisConversionEvidence` records only source/target basis, paired measurement
identifiers, and provenance.

A cross-basis proposal fails closed when evidence is absent or when the
source/target direction does not match.  `EVIDENCE_DECLARED` is a governance
state only and is explicitly not physical validation.

During review, the implementation was tightened so that a contract using
`conversion_status = EVIDENCE_DECLARED` must carry a non-empty
`conversion_evidence_id`; other statuses are forbidden from carrying that ID.
This prevents an evidence-status label from self-authorizing without a
traceable evidence record.

### Python/schema parity — PASS

The JSON Schema and Python contract use the same mass-basis values,
conversion-status values, evidence-ID binding rule, and fixed contract version
`v3.1-mass-basis-v1`.

During review, the Python constructor was tightened to reject an arbitrary
non-empty `version`; it now fails closed unless the value equals the schema
constant.

### Dimensional review — PASS WITH EXPLICIT SCOPE

V3.1 defines denominator/biological/area **metadata**, not a physical
conversion equation.  Therefore its dimensional claim is intentionally
limited:

- identical declared bases may be compared directly;
- different mass bases are dimensionally non-equivalent for direct comparison;
- different area bases are non-equivalent without an explicit future area
  relation;
- different tissue scopes are biologically non-equivalent without an explicit
  future mapping;
- evidence metadata does not itself supply a conversion relation.

No new physical parameter or numerical transformation is introduced by this
contract.

## CI evidence for implementation head

Verified implementation head:

`cfcdc3128a01f753f30dd8e710d5c1802db9d0dc`

GitHub Actions:

- `V3 Remediation CI`, run `32807272247`: PASS.
- `V3 Protected Integration Gate`, run `32807272253`: PASS.
- Python: 3.12.14 on Ubuntu 24.04.
- Portable current suite: `987 passed, 1 skipped, 57 deselected, 1 warning`.
- Explicit current/frozen/V3.1 invariant suite: `66 passed`.
- Compile/import smoke: PASS.
- Linear ancestry and `git diff --check`: PASS.

The remaining warning is the pre-existing NumPy/netCDF binary-compatibility
runtime warning in `tests/unit/test_era5_reader.py::test_netcdf_mapping`; that
test passes and the warning is unrelated to the V3.1 contract.

## Scientific and governance boundary

The review does not establish a fresh/dry/water/hydrogen conversion relation,
validate a biological parameter, calibrate the model, activate UFOTRI data, or
authorize V4 physics.

```ini
V3_1_IMPLEMENTATION = PASS_TECHNICAL_REVIEW
V3_1_DIMENSIONAL_SEMANTIC_REVIEW = PASS
FROZEN_RUNTIME_ISOLATION = PASS
FORMAL_EXTERNAL_INDEPENDENT_REVIEW = PENDING
MERGE_EXIT_GATE = HOLD_INDEPENDENT_REVIEW
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

## Required next action

Obtain an independent review by a reviewer that did not author the V3.1
implementation.  That review should inspect the exact final PR diff and verify
at minimum:

1. no hidden numerical conversion or basis inference;
2. code/schema semantic parity;
3. fail-closed evidence and scope behavior;
4. frozen-runtime isolation;
5. compatibility with the P7.8B-2 V3.1 boundary.

Until that review passes, PR #3 remains draft and must not be merged.
