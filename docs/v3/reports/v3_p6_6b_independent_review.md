# V3-P6.6B independent intake-to-dose boundary review

Review verdict: PASS_DOSE_ASSESSMENT_BOUNDARY

Review target: codex/v3-p6-6b-dose-assessment

Review base: a6200569154b90ab90c8dc9c5332b70401da8ec1

## Review method

The review uses the current worktree, the P6.6B architecture tests, the
cross-stage typed-boundary suite, and explicit Git path diffs. Software
interface behavior is kept separate from physical, empirical, and policy
claims.

## Findings

| Review item | Evidence | Verdict |
|---|---|---|
| New module is isolated | Source additions are under `exposure/dose_v3` | PASS |
| Required `DoseState` exists | All ten required fields are present | PASS |
| State is immutable | `DoseState` is a frozen dataclass | PASS |
| Public result boundary exists | `inventory()`, `dose()`, `consumer()` are exposed | PASS |
| Intake source is public-only | Solver calls only public `IntakeState` accessors | PASS |
| Units are explicit | `Bq` times `Sv/Bq` produces `Sv` | PASS |
| Equation closes | State validation checks `D = I * e` | PASS |
| Age groups remain separate | Mismatched groups fail and adult/child states stay distinct | PASS |
| Coefficients remain provisional | Non-provisional status is rejected | PASS |
| Upstream boundary is clean | No plant, soil, food, atmosphere, or V1/V2 imports | PASS |
| Policy boundary is clean | No risk, emergency, or regulatory assessment state | PASS |
| Protected paths are unchanged | No config, parameter, registry, legacy, or CTEAS-Atmos diff | PASS |
| External activation is absent | No UFOTRI database or automatic lookup | PASS |

## Boundary disposition

Implemented:

    IntakeState -> DoseSolver -> DoseState

Not implemented:

    DoseState -> regulatory assessment / risk / emergency criteria

The solver consumes the annual intake-period inventory and an explicit
provisional coefficient. It emits a committed-dose result state without
mutating the intake source or importing upstream transport state.

## Limitations retained

The coefficient is a design/test input, not validated UFOTRI data. The stage
does not model dose-coefficient lookup, multi-pathway exposure, population
risk, policy thresholds, emergency decisions, observational validation, or
CTEAS-Atmos coupling.

## Acceptance flags

    P6_6B_STATUS = PASS_DOSE_ASSESSMENT_IMPLEMENTED
    LEAF_RESISTANCE = TRUE
    TFWT_SOLVER = TRUE
    OBT_SOLVER = TRUE
    SOIL_SOLVER = TRUE
    ROOT_UPTAKE = TRUE
    FOOD_TRANSFER = TRUE
    INTAKE_PATHWAY = TRUE
    DOSE_SOLVER = TRUE
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE
