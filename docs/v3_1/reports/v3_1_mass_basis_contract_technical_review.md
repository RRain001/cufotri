# V3.1 Mass-Basis Contract Technical Review

Status: `PASS_SCHEMA_REMEDIATION_PENDING_INDEPENDENT_REREVIEW`

## Scope

This report covers PR #3 (`codex/v3-1-mass-basis-contract`) against the V3.1
boundary selected by P7.8B-2. The baseline remains `main` at
`d24aa03b00dcb586a2d93e678f42cb7853b7c078`.

The implementation author's technical review is not treated as the formal
independent review. Independent reviewer evidence is recorded separately.

## Evidence-pairing remediation — PASS

A second adversarial technical review found that the first evidence type used a
flat tuple of measurement IDs and did not bind evidence to tissue/area scope or
a declared evidence ID. That earlier PASS was superseded before merge.

The remediated API uses immutable `PairedMeasurement` records with explicit
`pair_id`, `source_measurement_id`, and `target_measurement_id`.
`BasisConversionEvidence` also binds `TissueScope`, `AreaBasis`, mass-basis
direction, provenance, and evidence ID. It fails closed on self-pairs,
duplicate pair IDs, measurement reuse across pairs, direction mismatch,
tissue/area mismatch, and declared evidence-ID mismatch.

No numerical fresh/dry/water/hydrogen conversion, water fraction, dry-matter
fraction, hydrogen fraction, coefficient, multiplier, or fitted relation is
introduced.

Verified remediation head:

`f1bdce343e667274c67f5af15ab4520b226122e6`

- V3 Remediation CI `32808331504`: PASS.
- V3 Protected Integration Gate `32808331423`: PASS.
- portable suite: `989 passed, 1 skipped, 57 deselected`;
- explicit current/frozen/V3.1 invariants: `68 passed`.

## First reviewer-independent review — HOLD

A reviewer-independent GitHub Copilot code review was requested on PR #4 for
frozen target:

`4664e4c09f20bbfd48c5d1c750efafeb6d6e9643`

Review ID:

`PRR_kwDOTiMPdM8AAAABKupe9g`

Reviewer:

`github-copilot-code-review`

Verdict derived from the actual review finding:

`HOLD_REMEDIATION_REQUIRED`

The review correctly identified a Python/JSON-Schema mismatch: serialized text
fields used only `minLength: 1`, so the schema admitted whitespace-only strings,
while Python `_require_text()` strips and rejects them. The issue affected
`subject_id`, string tissue/area identifiers, provenance strings, and declared
conversion evidence IDs.

The finding is treated as blocking. PR #4 was returned to draft and its old
target is retained as failed-review evidence rather than reused as a PASS.

## Schema/Python whitespace remediation — PASS

The JSON Schema now requires every serialized text field governed by
`_require_text()` to contain at least one non-whitespace character. A dedicated
negative test module covers:

- whitespace-only `subject_id`;
- provenance `source_id`, `source_locator`, `revision`, and string `note`;
- typed and custom tissue identifiers;
- typed and custom area identifiers;
- `conversion_evidence_id` under `evidence_declared`.

The new test module is also included explicitly in the protected integration
gate, not only discovered by the portable suite.

Verified schema-remediation head:

`6926ebf405b976ef58c66e17f6bfc0aacca551dd`

GitHub Actions:

- V3 Remediation CI `32809809259`: PASS.
- V3 Protected Integration Gate `32809809310`: PASS.
- portable suite: `994 passed, 1 skipped, 57 deselected, 1 warning`;
- explicit current/frozen/V3.1 invariants: `73 passed`;
- compile/import smoke: PASS;
- ancestry and `git diff --check`: PASS.

The warning is the existing NumPy/netCDF binary-compatibility warning in the
ERA5 reader test; the test passes and the warning is unrelated to V3.1.

## Frozen runtime boundary — PASS

The only V3.1 production-source path remains
`src/cteas_ufotri/plant/mass_basis_v3_1/`. No pre-existing leaf, TFWT, OBT,
soil, root, food, exposure, parameter, or pipeline runtime source is modified.
The frozen-runtime blob isolation test remains in the gate.

```ini
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
P7_5_SEMANTICS_CHANGED = FALSE
P7_5B_SEMANTICS_CHANGED = FALSE
EXISTING_STATE_SERIALIZATION_CHANGED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

## Current governance verdict

```ini
V3_1_IMPLEMENTATION = PASS_SCHEMA_REMEDIATION_TECHNICAL_REREVIEW
EVIDENCE_PAIRING_GATE = PASS
EVIDENCE_SCOPE_BINDING_GATE = PASS
EVIDENCE_ID_BINDING_GATE = PASS
PYTHON_SCHEMA_WHITESPACE_PARITY = PASS
FROZEN_RUNTIME_ISOLATION = PASS
FIRST_INDEPENDENT_REVIEW = HOLD_REMEDIATION_REQUIRED
FORMAL_INDEPENDENT_REREVIEW = PENDING
MERGE_EXIT_GATE = HOLD_INDEPENDENT_REREVIEW
```

## Required next action

1. Freeze the documentation-complete PR #3 head after exact-head CI.
2. Create a new independent-rereview branch from that exact SHA; do not reuse
   failed-review PR #4 as if it had passed.
3. Request a reviewer-independent rereview against the new frozen SHA.
4. Only a rereview with no blocking finding can close the V3.1 merge gate.

PR #3 remains draft until that sequence completes.
