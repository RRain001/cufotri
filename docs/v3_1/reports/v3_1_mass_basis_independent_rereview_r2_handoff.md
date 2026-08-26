# V3.1 Mass-Basis Contract — Independent Rereview R2 Handoff

## Frozen target

```text
IMPLEMENTATION_PR = 3
PRIOR_REREVIEW_PR = 5
FROZEN_TARGET = 95f78801d0fa3b507e6bd76249b192adf8b107cb
BASE_MAIN = d24aa03b00dcb586a2d93e678f42cb7853b7c078
REREVIEW_BRANCH = codex/v3-1-mass-basis-independent-rereview-r2
```

This was the fresh reviewer-independent rereview after Luna R1 found a blocking
same-basis evidence-state bypass. The R1 HOLD remains historical review evidence
and must not be rewritten into PASS.

## Luna R1 blocker

Luna R1 reviewed `e28fd18033984e9fda252aa87b81b399b60ece1e` and recorded
`HOLD_REMEDIATION_REQUIRED` at `d2014f584a3fa6fc373bf32a6477e950ace01b5a`.
The defect was in `validate_conversion_proposal()`: same-basis source/target
returned `IDENTITY_ONLY` before validating `EVIDENCE_DECLARED` /
`conversion_evidence_id` state.

## Remediation semantics

- `require_direct_comparison()` handles actual same-basis direct comparison.
- `validate_conversion_proposal()` returns `IDENTITY_ONLY` only for clean
  same-basis proposals without cross-basis evidence state/object.
- Same-basis proposals with supplied `BasisConversionEvidence` fail closed.
- Same-basis proposals with source- or target-side `EVIDENCE_DECLARED` fail closed.
- No same-basis conversion evidence or numerical conversion factor is invented.

## Verified remediation evidence

Code/test/workflow remediation head:
`cc5aabe0c331664a005ac3ec0579c993e1397757`

```text
V3 Remediation CI 32916837652 = PASS
V3 Protected Integration Gate 32916837645 = PASS
portable current suite = 1000 passed / 1 skipped / 57 deselected
explicit current/frozen/V3.1 invariants = 79 passed
```

Documentation-complete frozen target:
`95f78801d0fa3b507e6bd76249b192adf8b107cb`

```text
V3 Remediation CI 32917177880 = PASS
V3 Protected Integration Gate 32917177883 = PASS
```

## R2 blocking checks

R2 independently checked all prior boundaries, including whitespace/schema
parity, absence of numerical basis conversion, explicit pairing and pair reuse,
tissue/area/evidence-ID binding, the R1 same-basis bypass, Python/schema
coherence, frozen-runtime isolation, and P7.8B-2 scope compliance.

The final reviewer verdict is preserved in
`docs/v3_1/reviews/v3_1_mass_basis_independent_rereview_r2_request.yaml` and
`docs/v3_1/reports/v3_1_mass_basis_independent_rereview_r2_result.md`.

```ini
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```
