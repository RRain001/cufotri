# P5.5 Git Boundary Report

Audit target: `9e783acb0734d40347e845f1cf17d10f10cef9ab`

The following commands were run against the audit target and `main`:

```text
git diff main...HEAD -- src
git diff main...HEAD -- configs
git diff main...HEAD -- parameters
git diff main...HEAD -- schemas
```

## Cumulative branch result relative to main

| Region | Allowed by P5.5 boundary | Actual `main...HEAD` result |
| --- | --- | --- |
| `docs` | Yes | P5.1-P5.4 documentation exists; P5.5 review docs are new working changes |
| `tests` | Yes | P1-P5 architecture/unit tests exist; some numerical synthetic tests are present |
| `src` | Skeleton only | 39 changed paths relative to main, including leaf/soil/food-chain/dose/parameter framework files and test-only numerical kernels |
| `configs` | No change | No changed path relative to main |
| `parameters` | No validated database | Placeholder UFOTRI database and parameter source registry were added; no active numeric UFOTRI value |
| `schemas` | No P5.5 schema modification | P5.1 schema files exist relative to main; no P5.5 change relative to the audit target |

The cumulative source diff is therefore not literally “only skeleton” if
test-only numerical kernels are included in the word implementation. The
P5.4 delta itself is narrower: relative to P5.3, P5.4 changed only review
documents, status text, and an architecture test; it did not change `src/`,
`configs/`, `parameters/`, `schemas/`, or the trusted registry.

## Boundary interpretation

```text
P5_4_DELTA_PROTECTED_PATH_CHANGE = 0
CONFIG_CHANGE = 0
P5_5_AUDIT_PROTECTED_PATH_CHANGE = 0
VALIDATED_DATABASE_CHANGE = 0
NO_MERGE = TRUE
NO_REBASE = TRUE
```

The difference between the clean P5.4 delta and the accumulated P1-P5 source
tree is material to final phase classification.
