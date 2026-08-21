# V3-P5.1 Parameter Migration Layer

Status: `FRAMEWORK_COMPLETE`

P5.1 adds an auditable data layer between external parameter sources and the
future Leaf Exchange, Soil, Food Chain, and Dose physics modules. It does not
change a physical equation, import a UFOTRI numerical value, or connect the
new document format to the V1/V2 runtime.

## Data flow

```text
external source
      |
      v
ParameterSourceRegistry
      |
      v
ParameterDatabase (v2.0 migration document)
      |
      v
future physics module
```

The existing P0 v1 document remains readable. P5.1 adds a v2 document whose
entry fields are:

| Field | Contract |
| --- | --- |
| `parameter_id` | Dotted stable identifier, rooted in a registered module |
| `value` | Finite scalar or `null` for a placeholder |
| `unit` | Required unit string; no implicit conversion |
| `description` | Human-readable meaning |
| `module` | One of `leaf_exchange`, `soil`, `food_chain`, `dose` |
| `status` | `PLACEHOLDER`, `CANDIDATE`, `REVIEWED`, `VALIDATED`, or `ACTIVE` |
| `source` | Identifier resolved through the source registry |
| `source_type` | Provenance class such as manual, literature, or regulation |
| `reference` | Traceable citation/location record |
| `uncertainty` | Optional finite scalar or structured metadata |
| `valid_range` | Optional explicit finite bounds for non-placeholder values |
| `notes` | Audit notes; may state why a value is not yet usable |

All required fields are schema-checked. Semantic validation is fail-closed:
non-finite values, empty provenance, namespace mismatches, unit mismatches,
and out-of-range values raise an error. No missing value is replaced by zero or
by a default.

## Source registry

`ParameterSourceRegistry` records `source_id`, `citation`, `organization`,
`year`, `document`, `location`, and `accessibility`. A source declaration is
provenance metadata, not evidence that a parameter has been reviewed or
validated. Duplicate source identifiers are rejected. The future source
classes `UFOTRI_manual_vX`, `ICRP_publication`, and `GB_standard` are interface
targets only; this stage imports no values from them.

## Lifecycle and activation

```text
PLACEHOLDER -> CANDIDATE -> REVIEWED -> VALIDATED -> ACTIVE
```

Transitions are sequential. Each transition is represented by a
`ParameterMigrationRecord` containing `parameter_id`, `old_status`,
`new_status`, `changed_by`, `timestamp`, and `reason`. Direct skips are
rejected. An `ACTIVE` entry cannot be loaded unless its activation record is
present, so activation is never inferred from a field edit.

`ParameterDatabase.transition()` returns a new database and appends the audit
record. It does not modify a physics module. `migration_audit_report()` emits
deterministic status counts, entry provenance, and the complete record list.

## Reproducibility

The database package hash covers the canonical parameter document, values,
statuses, uncertainty/provenance fields, source registry, and migration audit.
Equivalent documents produce the same SHA-256; changing a status or source
registry changes the hash.

## P5.1 boundary

```yaml
Parameter migration: FRAMEWORK COMPLETE
UFOTRI values: NOT IMPORTED
Physics activation: NOT STARTED
Calibration: NOT STARTED
```

P5.2 may introduce reviewed Leaf Exchange equations and candidate values. It
must retain this lifecycle and evidence boundary.
