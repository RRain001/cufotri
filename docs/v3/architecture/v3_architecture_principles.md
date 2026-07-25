# V3 architecture principles

Status: `ARCHITECTURE_ONLY`  
Anchor: `ufotri-environmental-pathways-v2-candidate`

## Compatibility boundary

```text
V2_COMPATIBILITY_RULE =
V2_CASES_MUST_RETAIN_V2_NUMERICAL_BEHAVIOR
```

V3 configurations declare both `model_version` and `compatibility_mode`.
The only architecture-baseline combinations are:

| model_version | compatibility_mode | Meaning |
|---|---|---|
| `v2` | `v2_frozen` | Execute the immutable V2 contract |
| `v3` | `v2_frozen` | V3 envelope carrying a lossless V2 configuration |
| `v3` | `v3` | Future opt-in V3 behavior; no formal implementation exists |

V2 YAML remains readable by the V2 loader. A migrated document stores the
original mapping verbatim under `v2_compatibility.original_config`; it never
injects V3 defaults into that mapping. V2 output fields and state semantics are
not renamed in the frozen mode, and provenance must identify that mode and the
candidate anchor. Migration is explicit and reviewable, never implicit.

## Opt-in physics

Every V3 candidate module must have an explicit feature flag, semantic version,
declared input/output states, SI units, a module ledger, and a validation
status. Candidate modules are disabled by default and cannot replace V2
behavior silently. Architecture documents and validators are not physics
implementations.

## Evidence-driven development

Formal implementation work is inadmissible unless its registry entry has:

```text
evidence_gap_id
validation_case_id
scientific_question
acceptance_gate
```

The external evidence must be legally usable, reproducible, and separated into
calibration and holdout evidence before empirical claims are made.

## Activity conservation first

Each future module exposes, separately:

```text
external_input
internal_transfer
final_inventory
boundary_output
decay
numerical_residual
```

A small local residual does not prove cross-module conservation. Transfers
must match by activity, unit, normalization area, time interval, and positive
direction at both sides of an interface.

## Research-claim boundary

All V3 architecture artifacts retain these claims:

```text
NOT_SITE_CALIBRATED
NOT_REGULATORY_VALIDATED
HTO_ONLY_UNLESS_SEPARATE_GATE_APPROVES_HT
```

Architecture readiness does not imply physical, empirical, regulatory, or
site-specific validation.
