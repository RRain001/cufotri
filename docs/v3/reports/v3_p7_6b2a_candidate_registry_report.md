# V3-P7.6B-2A candidate registry report

Status: `PASS_PARAMETER_CANDIDATE_CONSTRUCTION`

## Canonical artifact

The registry is:

```text
docs/v3/parameter_evidence/parameter_candidate_registry.yaml
```

It is a schema-`v1`, stage-`P7.6B-2A` control-plane artifact generated from:

```text
docs/v3/parameter_evidence/parameter_inventory.yaml
docs/v3/parameter_evidence/parameter_applicability_matrix.yaml
```

The source inventory revision recorded in the registry is
`838634f3af85e205fb15e10cbf15ee298ad4f017`. The registry contains exactly 76
records, sorted by `parameter_id`, with unique IDs and one-to-one evidence and
applicability references.

## Record contract

Each row carries:

```text
parameter_id
parameter_name
subsystem
parameter_class
evidence_ids
applicability_status
candidate_status
candidate_screening
candidate_reason
validation_required
validation_plan
uncertainty_source
review_notes
priority_tier
provenance
```

No row contains `reported_value` or `normalized_value`. The registry is not a
parameter database and has no API for solver lookup.

## Integrity checks

The registry loader and tests enforce:

- deterministic ordering and unique `parameter_id` values;
- exact coverage of the 76-record P7.6A inventory;
- matching parameter name, subsystem, class, applicability status, and
  evidence identifier against the source records;
- explicit screening disposition for every row;
- `validation_required = true` for deferred or future candidate records;
- zero validated and active records at P7.6B-2A;
- false calibration, active-database, and V3-physics-ready flags.

The loaded result is:

```text
records = 76
CANDIDATE = 0
DEFERRED = 26
REJECTED = 50
VALIDATED = 0
ACTIVE = 0
```

The registry successfully round-trips through its mapping representation and
passes reference validation against both upstream artifacts.

## Runtime isolation

The candidate registry is a control-plane artifact. It is not imported by any
plant, soil, food-chain, dose, coupling, or `v3_pipeline` module, and it does
not alter configuration or numerical semantics. A future validation protocol
must consume candidate metadata explicitly and must not treat a candidate row
as a validated or active parameter.
