# P5.1 Parameter Migration Registry

This registry is the audit-facing companion to the executable migration layer.
It defines the namespaces that may receive future parameters; it is not a
numerical parameter set.

| Module | Registered path | Current status |
| --- | --- | --- |
| Leaf Exchange | `leaf_exchange.*` | PATH_REGISTERED; VALUES_NOT_IMPORTED |
| Soil | `soil.*` | PATH_REGISTERED; VALUES_NOT_IMPORTED |
| Food Chain | `food_chain.*` | PATH_REGISTERED; VALUES_NOT_IMPORTED |
| Dose | `dose.*` | PATH_REGISTERED; VALUES_NOT_IMPORTED |

## Source metadata contract

Every source record contains:

```text
source_id
citation
organization
year
document
location
accessibility
```

The registry may additionally retain a review status and production-use flag,
but those fields do not replace parameter-level lifecycle evidence.

## Audit rules

1. New migration entries default to `PLACEHOLDER`.
2. `unit`, `source`, and `status` are mandatory.
3. A source declaration does not make a parameter `VALIDATED`.
4. A parameter must follow the ordered lifecycle
   `PLACEHOLDER -> CANDIDATE -> REVIEWED -> VALIDATED -> ACTIVE`.
5. Every transition is recorded; an `ACTIVE` transition without a record is
   invalid.
6. No UFOTRI, ICRP, GB-standard, calibration, or experiment value is imported
   in P5.1.

The machine-readable audit can be obtained from
`ParameterDatabase.migration_audit_report()`. Its status is intentionally
limited to framework completion and does not claim physical validation.
