# ADR-022 — V3.1 mass-basis and tissue-scope contract

## Status

Accepted for implementation review on `codex/v3-1-mass-basis-contract`.

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
`BasisConversionEvidence` record may establish that a proposed relation has
explicit provenance and paired measurements, but V3.1 stores no numerical
conversion factor and performs no numerical conversion.

Custom tissue or area scopes require explicit identifiers. Missing provenance,
untyped enum values, mismatched tissue scope, mismatched area basis, missing
cross-basis evidence, duplicate paired-measurement identifiers, and reversed
conversion direction all fail closed.

## Scientific boundary

This ADR does **not** establish any fresh/dry/water/hydrogen conversion
relation. In particular it does not infer water fraction, dry-matter fraction,
hydrogen fraction, tissue composition, or crop-specific mass ratios.

Any future numerical conversion must have a separate evidence record,
scientific relation, uncertainty treatment, dimensional review, and independent
approval. Merely possessing `BasisConversionEvidence` is not physical
validation of such a relation.

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
2. JSON Schema validation for serialized metadata;
3. an isolation test that locks the frozen V3 solver and pipeline Git blobs;
4. the existing portable integration suite;
5. independent dimensional and semantic review before merge.

## Consequences

V3.1 creates an auditable boundary for future empirical validation and V4 OBT
work without pretending that cross-basis physics is already known. V4 remains
unauthorized by this ADR.

```ini
V3_1_MASS_BASIS_CONTRACT = IMPLEMENTED_FOR_REVIEW
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```
