# V3-P7.6B-2B candidate generation report

## Result

The candidate registry covers all 76 inventory records and identifies one
future validation candidate:

| parameter | candidate status | evidence ID | applicability record | equation compatible | unit compatible |
| --- | --- | --- | --- | --- | --- |
| `soil.tritium_half_life` | `VALIDATION_CANDIDATE` | `doi:10.6028/jres.105.043` | `applicability:soil.tritium_half_life` | `true` | `true` |

The candidate carries `validation_required = true`, a literature-comparison
plan, sensitivity analysis, experimental-data requirement, an explicit
uncertainty source, and remaining questions. The registry contains no
parameter values.

## Gate

Candidate admission requires all of the following:

1. `EVIDENCE_FOUND` with a non-test source and complete source metadata;
2. applicability other than `UNKNOWN` or `NOT_APPLICABLE`;
3. compatible equation role and explicit unit compatibility;
4. a non-empty future validation plan and remaining questions.

The direct-match half-life record satisfies these conditions. The gate rejects
the 75 other records at this stage: 25 remain `PROVISIONAL`/`DEFERRED` and 50
are scenario, numerical-control, or test-only `REJECTED` records.

## Subsystem disposition

| subsystem | candidate | deferred | rejected |
| --- | ---: | ---: | ---: |
| leaf | 0 | 5 | 4 |
| TFWT | 0 | 3 | 1 |
| OBT | 0 | 7 | 2 |
| soil | 1 | 3 | 1 |
| root | 0 | 1 | 1 |
| food | 0 | 3 | 2 |
| intake | 0 | 2 | 4 |
| dose | 0 | 1 | 3 |
| atmos | 0 | 0 | 9 |
| pipeline | 0 | 0 | 3 |
| tests | 0 | 0 | 20 |

The exact machine-readable disposition is in
`docs/v3/parameter_evidence/parameter_candidate_registry.yaml`. The candidate
layer remains isolated from all physics, coupling, pipeline, and runtime
parameter modules.

## Safety flags

```ini
VALIDATED = 0
ACTIVE = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
```
