# V3.1 Mass-Basis Contract — Independent Rereview R2 Handoff

## Frozen target

```text
IMPLEMENTATION_PR = 3
PRIOR_REREVIEW_PR = 5
FROZEN_TARGET = 95f78801d0fa3b507e6bd76249b192adf8b107cb
BASE_MAIN = d24aa03b00dcb586a2d93e678f42cb7853b7c078
REREVIEW_BRANCH = codex/v3-1-mass-basis-independent-rereview-r2
```

This is a fresh reviewer-independent rereview after Luna R1 found a blocking
same-basis evidence-state bypass. The R1 HOLD is retained as historical review
evidence and must not be rewritten into PASS.

## Luna R1 blocker

Luna R1 reviewed `e28fd18033984e9fda252aa87b81b399b60ece1e`
and recorded `HOLD_REMEDIATION_REQUIRED` at review branch head
`d2014f584a3fa6fc373bf32a6477e950ace01b5a`.

The defect was in `validate_conversion_proposal()`: same-basis source/target
returned `IDENTITY_ONLY` before validating a contract's
`EVIDENCE_DECLARED`/`conversion_evidence_id` state. Missing or conflicting
conversion evidence could therefore be silently bypassed on that path.

## Remediation semantics

The implementation now separates direct comparison from conversion-proposal
governance:

- `require_direct_comparison()` handles actual same-basis direct comparison;
- `validate_conversion_proposal()` returns `IDENTITY_ONLY` for same-basis only
  when no cross-basis evidence object is supplied and neither contract declares
  `EVIDENCE_DECLARED`;
- same-basis proposals with a supplied `BasisConversionEvidence` fail closed;
- same-basis proposals with source- or target-side `EVIDENCE_DECLARED` fail
  closed rather than ignoring the declared evidence state.

The remediation does not invent same-basis conversion evidence. A
`BasisConversionEvidence` record remains restricted to different source and
target mass bases and still contains no numerical conversion factor.

## Verified remediation evidence

Code/test/workflow remediation head:

`cc5aabe0c331664a005ac3ec0579c993e1397757`

GitHub Actions on that head:

```text
V3 Remediation CI 32916837652 = PASS
V3 Protected Integration Gate 32916837645 = PASS
portable current suite = 1000 passed / 1 skipped / 57 deselected
explicit current/frozen/V3.1 invariants = 79 passed
```

Documentation-complete frozen target:

`95f78801d0fa3b507e6bd76249b192adf8b107cb`

Exact-head GitHub Actions:

```text
V3 Remediation CI 32917177880 = PASS
V3 Protected Integration Gate 32917177883 = PASS
```

## R2 blocking checks

The independent reviewer must re-run all prior V3.1 checks, not only the R1
blocker:

1. reproduce the old whitespace/schema boundary and confirm it remains closed;
2. confirm no numerical fresh/dry/water/hydrogen conversion exists;
3. confirm explicit source/target pairing;
4. attack self-pairs, duplicate pair IDs, and record reuse across pair roles;
5. confirm evidence tissue-scope binding;
6. confirm evidence area-basis binding;
7. confirm source- and target-side cross-basis evidence-ID binding;
8. attack the Luna R1 same-basis bypass in every direction:
   - clean same-basis + no evidence state -> `IDENTITY_ONLY`;
   - source `EVIDENCE_DECLARED` -> reject;
   - target `EVIDENCE_DECLARED` -> reject;
   - same-basis + supplied cross-basis evidence -> reject;
   - `require_direct_comparison()` still admits valid same-basis comparison;
9. confirm Python/JSON Schema boundary remains coherent;
10. independently verify frozen-runtime isolation with Git diff/blob evidence;
11. confirm P7.8B-2 scope and all activation/readiness gates remain closed.

Existing regression coverage includes
`tests/v3_1/test_mass_basis_identity_evidence_gate.py`, but the reviewer should
not treat existing tests as proof and should construct independent adversarial
checks where useful.

## P7.7B cross-platform note

Luna R1's macOS detached review worktree observed a checked-in synthetic result
registry mismatch in one P7.7B test. The V3.1 diff did not touch that benchmark,
and the same P7.7B invariant passes in Ubuntu GitHub Actions, including on the
R1 remediation. Treat this as separate cross-platform reproducibility technical
debt unless R2 finds evidence that V3.1 causes it. It is synthetic software
evidence only, not physical validation.

## Required verdict

A PASS may be recorded only against exact frozen target
`95f78801d0fa3b507e6bd76249b192adf8b107cb` and only if no blocking finding
remains.

```ini
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

Do not modify the implementation while acting as reviewer. If any blocking
finding remains, record HOLD and stop.
