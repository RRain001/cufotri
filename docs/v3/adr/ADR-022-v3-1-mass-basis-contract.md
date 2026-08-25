# ADR-022 — V3.1 mass-basis and tissue-scope contract

## Status

Accepted, with evidence-binding remediation incorporated on
`codex/v3-1-mass-basis-contract` before independent review.

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
match the evidence record supplied to proposal validation. Possessing or
matching an evidence record still does **not** validate a numerical conversion
relation.

Custom tissue or area scopes require explicit identifiers. Missing provenance,
untyped enum values, mismatched tissue scope, mismatched area basis, missing
cross-basis evidence, malformed or reused measurement pairs, mismatched
evidence IDs, and reversed conversion direction all fail closed.

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
2. negative tests for evidence pairing, evidence scope, and evidence-ID binding;
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

## Consequences

V3.1 creates an auditable boundary for future empirical validation and V4 OBT
work without pretending that cross-basis physics is already known. V4 remains
unauthorized by this ADR.

```ini
V3_1_MASS_BASIS_CONTRACT = REMEDIATION_IN_PROGRESS
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```
