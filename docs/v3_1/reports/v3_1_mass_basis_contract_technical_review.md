# V3.1 Mass-Basis Contract Technical Review

Status: `SUPERSEDED_PENDING_REMEDIATION_REREVIEW`

## Review scope

This report covers PR #3 (`codex/v3-1-mass-basis-contract`) against the V3.1
selection and architecture boundary frozen by P7.8B-2. The implementation
baseline is `main` at
`d24aa03b00dcb586a2d93e678f42cb7853b7c078`.

The original technical review was a separate audit pass over the implemented
diff, schema, tests, and CI evidence. It was **not** represented as an
externally independent review because the same assistant also implemented the
changes in that work session.

A second adversarial review has now superseded the earlier PASS. The historical
CI results below remain valid evidence for the earlier head, but they are not
an acceptance result for the remediated head.

## Second adversarial finding

Review target:

`87fc9b2e3226ad028133e070bfd7b89d803adcfb`

The public `BasisConversionEvidence` type represented matched evidence using a
flat tuple of `paired_measurement_ids`. The implementation required at least
two distinct IDs, but did not establish which record was the source-basis
measurement and which was the target-basis measurement for a matched specimen
or event. Consequently, two unrelated measurement IDs could satisfy the
structural gate.

The evidence record also encoded only source and target mass bases. It was not
bound to `TissueScope` or `AreaBasis`, which meant a fresh-to-dry evidence
record could be reused for another tissue or area scope if the calling
contracts happened to match each other.

Finally, `validate_conversion_proposal()` checked mass-basis direction but did
not enforce consistency between the supplied evidence ID and a contract that
already declared `conversion_status = EVIDENCE_DECLARED`.

Verdict for the earlier technical review:

```ini
PRIOR_TECHNICAL_REVIEW = SUPERSEDED
SECOND_ADVERSARIAL_REVIEW = FINDING_REQUIRES_REMEDIATION
MERGE_EXIT_GATE = HOLD_REMEDIATION
```

## Remediation design

The remediation is intentionally limited to the new V3.1 metadata module and
its tests/documentation. It does not modify any frozen solver or numerical
coupling path.

`BasisConversionEvidence` now requires:

- an explicit `TissueScope`;
- an explicit `AreaBasis`;
- one or more immutable `PairedMeasurement` records;
- each pair to contain a unique `pair_id`, source measurement ID, and target
  measurement ID;
- source and target IDs within one pair to be distinct;
- no measurement ID reuse across pairs;
- explicit provenance.

`validate_conversion_proposal()` additionally requires evidence tissue and area
scope to match the source/target contracts and rejects a supplied evidence
record whose ID conflicts with any contract-level declared evidence ID.

These checks remain metadata governance only. No water fraction, dry-matter
fraction, hydrogen fraction, numerical multiplier, fitted relation, or other
physical conversion parameter is introduced.

## Frozen runtime boundary

The remediation must retain:

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

`tests/architecture/test_v3_1_mass_basis_isolation.py` remains the explicit
blob-level guard over the frozen pipeline, leaf resistance, TFWT, OBT, soil,
root, and food runtime paths.

## Historical CI evidence only

Earlier reviewed implementation head:

`cfcdc3128a01f753f30dd8e710d5c1802db9d0dc`

Historical GitHub Actions evidence:

- `V3 Remediation CI`, run `32807272247`: PASS.
- `V3 Protected Integration Gate`, run `32807272253`: PASS.
- Portable current suite: `987 passed, 1 skipped, 57 deselected, 1 warning`.
- Explicit current/frozen/V3.1 invariant suite: `66 passed`.

Those results do not close the current remediation gate because source and test
files changed after that SHA.

## Required next action

1. Run exact-head CI on the remediated implementation.
2. Repeat dimensional/semantic review against that exact SHA.
3. Only after remediation PASS, freeze a new target SHA and create the separate
   independent-review handoff branch.
4. The independent-review gate must still be completed by a reviewer that did
   not author the implementation.

Until those steps complete, PR #3 remains draft and must not be merged.
