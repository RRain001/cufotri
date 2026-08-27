# V4 production-case input manifest R1

Status: `MANIFEST_CONTRACT_COMPLETE_AWAITING_EXACT_HEAD_GATE`

Base main: `211cfe6799e8a4285466c6836fc849a701eff8bb`

## Result

PR #45 established `PRODUCTION_INPUT_PACKET_READY=FALSE` after auditing the actual controlled UFOTRI runtime path. This stage implements the next frozen control-plane step without changing production code or model physics.

A single case manifest, JSON Schema, and fail-closed validator now define the boundary between a structurally valid packet and a production-complete packet.

The checked-in template enumerates all 49 records in the PR #45 input registry: 48 required and one optional endpoint record. It deliberately preserves the current unresolved readiness states and contains no newly selected production values.

Expected template result:

```text
SCHEMA_VALID = TRUE
INVENTORY_COMPLETE = TRUE
PRODUCTION_COMPLETE = FALSE
STATUS = FAIL_CLOSED_INCOMPLETE
PRODUCTION_INPUT_PACKET_READY = FALSE
FULL_MODEL_PRODUCTION_READY = FALSE
```

The external Atmos surface-deposition input remains `BLOCKED_EXTERNAL` / `BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED`. No puff-ledger amount, accumulated inventory, API default, or silent zero can satisfy that field.

## Completeness semantics

The audit registry is the authority for quantity identity, required/optional state, classification, and frozen canonical unit where specified. The manifest cannot silently omit a required input or introduce a new quantity without a separate review.

`READY_PROVENANCED_SOURCE` requires an explicit artifact and revision, missing-data policy, and production-use authorization. External/upstream records additionally require temporal, spatial, and identity support. `DERIVED_FROM_READY_STATE` requires a complete derivation record and production-ready dependencies. `READY_CONTROLLED` requires a frozen controlled source reference.

An explicit zero must carry its own artifact/revision/rationale evidence. A software default of zero is not an explicit scientific zero policy.

## Controlled profiles retained

- reduced UFOTRI OBT daily-average `kf/kr` baseline;
- Eq.39 equilibrium-radiation root-total-uptake semantics;
- UFOTRI 20/40/40 root distribution;
- `PRESERVE_V3_POST_OBT_ROOT_GAIN`;
- `KEEP_HARVEST_EVENT`.

These remain controlled software/model-profile decisions. They do not make unresolved case inputs production-ready.

## Non-decisions

This stage does not add real CTEAS-Atmos binding, production leaf-resistance values, hydrology, multi-pool OBT, calibration, empirical validation, physical-accuracy claims, Eq.38 aerodynamic production use, UFOTRI reference-layer rates, or the short-term 3 h delay.

## Next stage after clean merge

`V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R1` with control-plane/source-evidence scope only. The next task is to resolve sources and explicit-zero policies against the manifest, not to add solver complexity.
