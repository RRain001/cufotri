# V3.1 Mass-Basis Contract Technical Review

Status: `PASS_REMEDIATION_TECHNICAL_REREVIEW_INDEPENDENT_REVIEW_PENDING`

## Review scope

This report covers PR #3 (`codex/v3-1-mass-basis-contract`) against the V3.1
selection and architecture boundary frozen by P7.8B-2. The implementation
baseline is `main` at
`d24aa03b00dcb586a2d93e678f42cb7853b7c078`.

This technical review is not represented as an externally independent review,
because the same assistant also authored the implementation/remediation in
this work session. The reviewer-independent exit gate remains open.

## Second adversarial finding and remediation

The first reviewed candidate used a flat tuple of `paired_measurement_ids`.
Although it required distinct IDs, that representation did not establish which
record was the source-basis measurement and which was the target-basis
measurement for a matched specimen/event. Evidence also encoded only mass-basis
direction and was not bound to tissue or area scope. In addition,
`validate_conversion_proposal()` did not enforce consistency with an evidence
ID already declared on a `MassBasisContract`.

The earlier technical-review PASS was therefore superseded and PR #3 was
reopened for remediation before any independent-review branch was created.

The remediated public API now uses immutable `PairedMeasurement` records with:

- `pair_id`;
- `source_measurement_id`;
- `target_measurement_id`.

`BasisConversionEvidence` now also carries explicit `TissueScope` and
`AreaBasis`. Construction/validation fails closed when:

- no explicit pair exists;
- source and target IDs within a pair identify the same record;
- a pair ID is reused;
- a measurement record is reused across pairs;
- evidence mass-basis direction is reversed;
- evidence tissue scope differs from the compared contracts;
- evidence area basis differs from the compared contracts;
- a contract-level declared `conversion_evidence_id` conflicts with the
  supplied evidence record.

The pair record is a traceable declaration of matching; V3.1 does not claim to
scientifically prove that the declared measurements are biologically paired.
Likewise, one or more declared pairs are evidence metadata only and are not a
validated numerical fresh/dry/water/hydrogen conversion relation.

## Scope isolation — PASS

The only production-source path introduced by V3.1 remains
`src/cteas_ufotri/plant/mass_basis_v3_1/`. No pre-existing V3 solver, state,
food, exposure, parameter, or pipeline source file is modified.

`tests/architecture/test_v3_1_mass_basis_isolation.py` continues to lock the
Git blob IDs for the frozen pipeline, leaf resistance, TFWT, OBT, soil, root,
and food solver/state paths and verifies that none imports
`mass_basis_v3_1`.

```ini
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
P7_5_SEMANTICS_CHANGED = FALSE
P7_5B_SEMANTICS_CHANGED = FALSE
EXISTING_STATE_SERIALIZATION_CHANGED = FALSE
```

## Typed basis and dimensional semantics — PASS

`MassBasis` distinguishes `fresh_mass`, `dry_mass`, `water_mass`, and
`hydrogen_mass`. `TissueScope` and `AreaBasis` are separately typed. Direct
comparison is admitted only when mass basis, tissue scope, and area basis are
identical.

Different mass bases are not dimensionally interchangeable. Different tissue
or area scopes are not treated as equivalent by inference. The evidence object
contains no water fraction, dry-matter fraction, hydrogen fraction,
composition factor, regression coefficient, multiplier, or executable
conversion equation.

Therefore `EVIDENCE_DECLARED` means only that traceable, direction- and
scope-matched evidence metadata has been supplied. It is not physical
validation and does not authorize conversion of a numerical value.

## Python/schema boundary — PASS WITH EXPLICIT SCOPE

The JSON Schema continues to define the serialized `MassBasisContract` record.
Its mass-basis values, conversion statuses, fixed version, and evidence-ID
binding rules remain aligned with the Python contract.

`BasisConversionEvidence` and `PairedMeasurement` are typed Python governance
records in V3.1; no standalone serialized evidence-file format is frozen by
this stage. A future persisted evidence database would require a separately
reviewed schema rather than silently extending the current contract schema.

## Exact-head CI evidence for remediated implementation

Verified remediated implementation head:

`f1bdce343e667274c67f5af15ab4520b226122e6`

GitHub Actions:

- `V3 Remediation CI`, run `32808331504`: PASS.
- `V3 Protected Integration Gate`, run `32808331423`: PASS.
- Python: 3.12 on Ubuntu 24.04.
- Portable current suite: `989 passed, 1 skipped, 57 deselected, 1 warning`.
- Explicit current/frozen/V3.1 invariant suite: `68 passed`.
- Compile/import smoke: PASS.
- Linear ancestry and `git diff --check`: PASS.

The only test warning remains the pre-existing NumPy/netCDF binary-compatibility
runtime warning in `tests/unit/test_era5_reader.py::test_netcdf_mapping`; the
test passes and the warning is unrelated to V3.1.

## Historical review evidence

The earlier reviewed head `cfcdc3128a01f753f30dd8e710d5c1802db9d0dc`
and its PASS runs are retained only as historical evidence. They do not
supersede the remediation verification above.

The second adversarial review trigger head was
`87fc9b2e3226ad028133e070bfd7b89d803adcfb`.

## Governance verdict

```ini
V3_1_IMPLEMENTATION = PASS_REMEDIATION_TECHNICAL_REREVIEW
V3_1_DIMENSIONAL_SEMANTIC_REREVIEW = PASS
EVIDENCE_PAIRING_GATE = PASS
EVIDENCE_SCOPE_BINDING_GATE = PASS
EVIDENCE_ID_BINDING_GATE = PASS
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

Freeze the final documentation-complete PR head after exact-head CI, then create
an independent-review handoff branch from that exact SHA. The independent
reviewer must not author the implementation and must verify at minimum:

1. no hidden numerical basis conversion or basis inference;
2. explicit source/target evidence pairing semantics;
3. evidence tissue/area scope binding;
4. evidence-ID consistency and fail-closed behavior;
5. Python/schema boundary clarity;
6. frozen-runtime isolation;
7. compatibility with the P7.8B-2 V3.1 boundary.

Until that independent review passes, PR #3 remains draft and must not be
merged.
