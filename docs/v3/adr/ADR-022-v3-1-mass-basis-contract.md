# ADR-022 — V3.1 mass-basis and tissue-scope contract

## Status

Accepted as the V3.1 contract design, with Luna R1 identity/evidence remediation
incorporated on `codex/v3-1-mass-basis-contract`. Formal independent rereview
R2 remains required before merge.

## Context

P7.8B-2 selected an explicit plant/product mass-basis contract as the only
V3.1 change. The frozen V3 runtime reports plant and food activity without a
single typed relation that distinguishes fresh-mass, dry-mass, water-mass, or
hydrogen-mass denominators across validation datasets. Introducing a guessed
conversion factor would turn a metadata problem into an unsupported physical
parameter.

The current V3 solver equations, state serialization, P7.5/P7.5B operator
split, and parameter activation gates are already frozen. V3.1 therefore must
improve comparability without silently changing those runtime semantics.

## Decision

Add an independent public module, `cteas_ufotri.plant.mass_basis_v3_1`, that
provides immutable typed declarations for:

- mass basis: fresh, dry, water, or hydrogen mass;
- tissue/product scope;
- area basis;
- provenance;
- conversion governance status.

The contract is intentionally not embedded into `OBTState`, `FoodInventory`,
`HarvestState`, or `V3PipelineRunner` in V3.1. Existing constructors and
serialized states therefore remain unchanged.

Direct comparison is allowed only when mass basis, tissue scope, and area basis
are identical. Cross-basis comparison fails closed. A separate
`BasisConversionEvidence` record may establish only that a proposed relation
has explicit provenance and matched measurements; V3.1 stores no numerical
conversion factor and performs no numerical conversion.

### Same-basis identity versus conversion-proposal governance

V3.1 deliberately separates direct comparison from conversion-proposal
validation.

`require_direct_comparison()` is the API for a true same-basis comparison. It
requires identical mass, tissue, and area bases and does not consume
cross-basis conversion evidence metadata.

`validate_conversion_proposal()` governs a proposed basis relation. When the
source and target have the same mass basis, it may return `IDENTITY_ONLY` only
if no `BasisConversionEvidence` object is supplied and neither contract uses
`conversion_status = EVIDENCE_DECLARED` for that proposal path. A same-basis
conversion proposal carrying a cross-basis evidence object or declared
evidence state fails closed rather than silently ignoring that state.

This rule avoids inventing a same-basis `BasisConversionEvidence`; that record
is intentionally valid only when source and target mass bases differ. Records
that happen to carry conversion evidence metadata can still be directly
compared through `require_direct_comparison()` when their actual bases and
scopes are identical.

### Evidence binding

A cross-basis evidence record must be scoped to the exact `TissueScope` and
`AreaBasis` for which it is proposed. Evidence cannot be reused across a
different tissue or area basis merely because the mass-basis direction is the
same.

Matched measurements are represented as explicit `PairedMeasurement` records
with:

- a unique `pair_id`;
- one source-basis measurement ID;
- one target-basis measurement ID.

The source and target IDs in a pair must identify distinct records, pair IDs
must be unique, and one measurement record cannot be reused across multiple
pairs. A flat list of unrelated IDs is not sufficient evidence of pairing.

If a `MassBasisContract` already declares
`conversion_status = EVIDENCE_DECLARED`, its `conversion_evidence_id` must
match the evidence record supplied to a valid cross-basis proposal. Possessing
or matching an evidence record still does **not** validate a numerical
conversion relation.

Custom tissue or area scopes require explicit identifiers. Missing provenance,
untyped enum values, mismatched tissue scope, mismatched area basis, missing
cross-basis evidence, malformed or reused measurement pairs, mismatched
evidence IDs, reversed conversion direction, and evidence attached to an
identity conversion proposal all fail closed.

## Scientific boundary

This ADR does **not** establish any fresh/dry/water/hydrogen conversion
relation. In particular it does not infer water fraction, dry-matter fraction,
hydrogen fraction, tissue composition, or crop-specific mass ratios.

Any future numerical conversion must have a separate evidence record,
scientific relation, uncertainty treatment, dimensional review, and independent
approval. `EVIDENCE_DECLARED` means only that traceable, scope-matched evidence
metadata exists.

## Compatibility

The `v3_frozen_baseline` remains the default and rollback target. V3.1 does not
change:

- `dB/dt = k_f T - k_r B`;
- leaf resistance equations;
- TFWT storage;
- soil signed-transport storage;
- root uptake;
- harvest-event food transfer;
- exposure/dose equations;
- P7.5/P7.5B ordering, restart, or ledger semantics;
- active-parameter count.

## Verification

The implementation must provide:

1. unit tests for immutable typed contracts and fail-closed behavior;
2. negative tests for evidence pairing, evidence scope, evidence-ID binding,
   and same-basis identity/evidence-state bypasses;
3. JSON Schema validation for serialized mass-basis metadata;
4. an isolation test that locks the frozen V3 solver and pipeline Git blobs;
5. the existing portable integration suite;
6. dimensional and semantic review followed by a reviewer-independent gate.

## Review history

A second adversarial review of head
`87fc9b2e3226ad028133e070bfd7b89d803adcfb` found that the first evidence
representation used a flat tuple of measurement IDs. That representation did
not prove source/target pairing, did not bind evidence to tissue/area scope,
and proposal validation did not enforce consistency with a declared evidence
ID. The earlier technical-review PASS was therefore superseded and remediation
was required before the independent-review branch could be opened.

A first external GitHub Copilot review of target
`4664e4c09f20bbfd48c5d1c750efafeb6d6e9643` found that JSON Schema admitted
whitespace-only text that Python `_require_text()` rejected after stripping.
That finding was remediated and independently preserved as a HOLD review.

Local GPT-5.6 Luna rereview R1 then reviewed target
`e28fd18033984e9fda252aa87b81b399b60ece1e` and returned
`HOLD_REMEDIATION_REQUIRED`: `validate_conversion_proposal()` returned
`IDENTITY_ONLY` for same-basis records before checking a declared evidence
state. The review is preserved at
`d2014f584a3fa6fc373bf32a6477e950ace01b5a`.

The identity/evidence-state remediation is verified at code/test/workflow head
`cc5aabe0c331664a005ac3ec0579c993e1397757` by V3 Remediation CI run
`32916837652` and V3 Protected Integration Gate run `32916837645`.
The portable suite reports `1000 passed, 1 skipped, 57 deselected`; the
explicit invariant suite reports `79 passed`.

## Consequences

V3.1 creates an auditable boundary for future empirical validation and V4 OBT
work without pretending that cross-basis physics is already known. V4 remains
unauthorized by this ADR.

```ini
V3_1_MASS_BASIS_CONTRACT = PASS_LUNA_R1_REMEDIATION_PENDING_R2
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```
