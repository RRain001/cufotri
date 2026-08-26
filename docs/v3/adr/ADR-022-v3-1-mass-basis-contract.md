# ADR-022 — V3.1 mass-basis and tissue-scope contract

## Status

Accepted, independently rereviewed, and merged to `main`.

```text
IMPLEMENTATION_SHA = 95f78801d0fa3b507e6bd76249b192adf8b107cb
R2_REVIEW_SHA = 7a06733f3201cc60c4c6599799892899cdb61d7f
R2_VERDICT = PASS_INDEPENDENT_REREVIEW
MAIN_MERGE_SHA = 43eabee5fc5029441c00cc0221d84bf887bc4660
```

The merge was a standard two-parent merge commit; its tree is identical to the
frozen implementation tree. V3.1 is closed. This ADR does not authorize V4.

## Context

P7.8B-2 selected an explicit plant/product mass-basis contract as the only
V3.1 runtime-source addition. The frozen V3 runtime reports plant and food
activity without a typed relation distinguishing fresh-mass, dry-mass,
water-mass, or hydrogen-mass denominators across validation datasets. Guessing
a conversion factor would turn a metadata problem into an unsupported physical
parameter.

The V3 solver equations, state serialization, P7.5/P7.5B operator split, and
parameter activation gates were already frozen. V3.1 therefore improves
auditable comparability without changing those runtime semantics.

## Decision

Provide `cteas_ufotri.plant.mass_basis_v3_1` with immutable typed declarations
for:

- mass basis: fresh, dry, water, or hydrogen mass;
- tissue/product scope;
- area basis;
- provenance;
- conversion-governance status.

The contract is not embedded into `OBTState`, `FoodInventory`, `HarvestState`,
or `V3PipelineRunner` in V3.1. Existing constructors and serialized states are
unchanged.

Direct comparison is permitted only when mass basis, tissue scope, and area
basis are identical. Cross-basis comparison fails closed. A separate
`BasisConversionEvidence` record can establish only that a proposed relation
has explicit provenance and matched measurements; V3.1 stores no numerical
conversion factor and performs no numerical conversion.

### Same-basis identity versus conversion-proposal governance

`require_direct_comparison()` is the API for true same-basis comparison. It
requires identical mass, tissue, and area bases and does not consume unrelated
cross-basis evidence metadata.

`validate_conversion_proposal()` governs a proposed basis relation. It may
return `IDENTITY_ONLY` for same-basis source/target only when no
`BasisConversionEvidence` is supplied and neither contract declares
`EVIDENCE_DECLARED` on that proposal path. A same-basis proposal carrying a
cross-basis evidence object or declared evidence state fails closed.

### Evidence binding

Cross-basis evidence is bound to exact source/target direction, `TissueScope`,
`AreaBasis`, provenance, and evidence ID. Matched observations are represented
as `PairedMeasurement` records containing a unique pair ID and distinct source
and target measurement IDs. Self-pairs, duplicate pair IDs, and reuse of one
measurement across pair roles fail closed.

`EVIDENCE_DECLARED` means only that traceable, scope-matched evidence metadata
exists. It is not physical validation and does not authorize a numerical
conversion relation.

## Scientific boundary

This ADR establishes no fresh/dry/water/hydrogen numerical conversion. It does
not infer water fraction, dry-matter fraction, hydrogen fraction, tissue
composition, or crop-specific mass ratios. Any future numerical conversion
requires a separate scientific relation, evidence, uncertainty treatment,
dimensional review, and independent approval.

## Compatibility

The `v3_frozen_baseline` remains the rollback target. V3.1 does not change:

- `dB/dt = k_f T - k_r B`;
- leaf resistance equations;
- TFWT storage;
- soil signed-transport storage;
- root uptake;
- harvest-event food transfer;
- exposure/dose equations;
- P7.5/P7.5B ordering, restart, or ledger semantics;
- active-parameter count.

## Review and remediation history

A second adversarial technical review found that the original flat measurement
ID representation did not prove source/target pairing or bind evidence to
exact tissue/area scope. That defect was remediated.

A first external GitHub Copilot review found a Python/JSON Schema whitespace
parity defect. That defect was remediated.

Local GPT-5.6 Luna rereview R1 reviewed
`e28fd18033984e9fda252aa87b81b399b60ece1e` and returned
`HOLD_REMEDIATION_REQUIRED` at
`d2014f584a3fa6fc373bf32a6477e950ace01b5a`. The valid blocking finding was an
early same-basis `IDENTITY_ONLY` return that bypassed declared evidence-state
checks.

The R1 remediation was verified at
`cc5aabe0c331664a005ac3ec0579c993e1397757` by V3 Remediation CI run
`32916837652` and V3 Protected Integration Gate run `32916837645`.

Luna R2 then independently reviewed exact frozen implementation
`95f78801d0fa3b507e6bd76249b192adf8b107cb` and returned
`PASS_INDEPENDENT_REREVIEW` with zero blocking findings at
`7a06733f3201cc60c4c6599799892899cdb61d7f`. The final implementation SHA also
passed exact-head V3 Remediation CI `32917177880` and Protected Integration
Gate `32917177883`.

PR #3 was subsequently merged with merge commit
`43eabee5fc5029441c00cc0221d84bf887bc4660`. Its parents are the prior main
`d24aa03b00dcb586a2d93e678f42cb7853b7c078` and implementation
`95f78801d0fa3b507e6bd76249b192adf8b107cb`; its tree equals the implementation
tree `b2d06370e5c1ec2f7322aceabbbc2e909ae6f442`.

## Consequences

V3.1 now provides an auditable basis contract for future validation and model
redesign work. The next decision point is P7.8C / V4 Implementation
Authorization Gate. That gate may consider authorization of control-plane
`V4_DATA_AND_STATE_CONTRACTS`; it must not be interpreted as automatic
authorization of dynamic stomata, two-pool OBT, root water-flux, or other new
solver physics.

```ini
V3_1_MASS_BASIS_CONTRACT = PASS_MAIN_MERGED
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```
