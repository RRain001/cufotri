# V3.1 Mass-Basis Contract — Independent Review Handoff

## Frozen target

```text
IMPLEMENTATION_PR = 3
IMPLEMENTATION_BRANCH = codex/v3-1-mass-basis-contract
INDEPENDENT_REVIEW_BRANCH = codex/v3-1-mass-basis-independent-review
BASE_MAIN = d24aa03b00dcb586a2d93e678f42cb7853b7c078
FROZEN_TARGET_SHA = 4664e4c09f20bbfd48c5d1c750efafeb6d6e9643
REMEDIATED_IMPLEMENTATION_SHA = f1bdce343e667274c67f5af15ab4520b226122e6
```

The independent review must inspect the frozen target above. The implementation
branch is frozen for review; no reviewer should repair source while issuing a
PASS verdict. A blocking defect must produce `HOLD_REMEDIATION_REQUIRED` and be
fixed on the implementation branch before a new target SHA is frozen.

## Independence requirement

The formal exit gate requires a reviewer that did not author the V3.1
implementation/remediation. The implementation author's own technical rereview
is useful evidence but does not satisfy this gate.

The authoritative machine-readable request is:

`docs/v3_1/reviews/v3_1_mass_basis_independent_review_request.yaml`

## Why a second review is necessary

The first candidate passed tests but a later adversarial review found a semantic
hole: `BasisConversionEvidence` accepted a flat tuple of measurement IDs. That
did not establish source/target pairing and did not bind evidence to tissue or
area scope. Proposal validation also did not verify consistency with an evidence
ID already declared by a contract.

The implementation was reopened and remediated before independent review.
The reviewer should therefore test the new semantics adversarially rather than
relying on the earlier PASS history.

## Required adversarial checks

1. **No numerical conversion** — search the V3.1 module for conversion factors,
   water/dry/hydrogen fractions, multipliers, regressions, or hidden numerical
   transformations. None are authorized.
2. **Explicit pairing** — verify `PairedMeasurement` explicitly distinguishes
   source and target records and evidence requires at least one pair.
3. **Pair integrity** — verify self-pairs, duplicate pair IDs, and measurement
   record reuse across pairs fail closed.
4. **Tissue scope binding** — evidence for one tissue cannot authorize another
   tissue scope.
5. **Area basis binding** — evidence for one area basis cannot authorize another
   area basis.
6. **Evidence ID binding** — a contract that declares an evidence ID cannot be
   validated with a conflicting evidence record.
7. **Schema boundary** — the JSON Schema remains the serialized
   `MassBasisContract` format; the Python evidence record is not silently
   presented as a frozen serialized evidence schema.
8. **Runtime isolation** — no existing solver/state/pipeline runtime semantics
   may change.
9. **P7.8B-2 scope** — no calibration, parameter activation, UFOTRI database
   activation, V3 physics-ready claim, or V4 implementation is allowed.

## Frozen CI evidence

For the remediated implementation SHA
`f1bdce343e667274c67f5af15ab4520b226122e6`:

```text
V3 Remediation CI run 32808331504 = PASS
V3 Protected Integration Gate run 32808331423 = PASS
portable suite = 989 passed, 1 skipped, 57 deselected
explicit current/frozen/V3.1 invariants = 68 passed
```

For the final documentation-complete frozen target
`4664e4c09f20bbfd48c5d1c750efafeb6d6e9643`:

```text
V3 Remediation CI run 32808596664 = PASS
V3 Protected Integration Gate run 32808596714 = PASS
```

## Files that require direct inspection

At minimum:

```text
src/cteas_ufotri/plant/mass_basis_v3_1/contract.py
src/cteas_ufotri/plant/mass_basis_v3_1/__init__.py
tests/v3_1/test_mass_basis_contract.py
tests/architecture/test_v3_1_mass_basis_isolation.py
schemas/v3_1/mass_basis_contract.schema.json
docs/v3/adr/ADR-022-v3-1-mass-basis-contract.md
docs/v3_1/contracts/mass_basis_contract.yaml
docs/v3_1/reports/v3_1_mass_basis_contract_technical_review.md
```

The reviewer must also inspect the complete `main...FROZEN_TARGET_SHA` diff to
ensure no unexpected runtime source file entered the candidate.

## Verdict rules

Use exactly one of:

```text
PASS_INDEPENDENT_REVIEW
PASS_WITH_NONBLOCKING_NOTES
HOLD_REMEDIATION_REQUIRED
REJECT
```

A PASS is permitted only if every blocking check in the machine-readable
request passes against the exact frozen SHA. `PASS_WITH_NONBLOCKING_NOTES` may
contain documentation/maintenance observations that do not weaken the frozen
contract.

A PASS does not mean physical validation. Even after independent review:

```ini
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```
