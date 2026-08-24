# V3-P6.6B intake-to-dose assessment implementation report

Status: PASS_DOSE_ASSESSMENT_IMPLEMENTED

Branch: codex/v3-p6-6b-dose-assessment

Base: a6200569154b90ab90c8dc9c5332b70401da8ec1

## Scope

This stage establishes the downstream intake-to-dose boundary:

    IntakeState
         |
         v
    DoseSolver
         |
         v
    DoseState

The package is opt-in and isolated from the V1/V2 runtime. It does not modify
environmental transport, plant, soil, food, atmosphere, configuration,
parameter, or legacy dose modules. It does not implement assessment policy,
risk, emergency criteria, or external coupling.

## dose_v3 package

The package is `src/cteas_ufotri/exposure/dose_v3`:

- `dose_state.py` defines the immutable `DoseState` result record;
- `dose_solver.py` defines `DoseParameters` and `DoseSolver`;
- `validation.py` applies fail-closed identity, timestamp, provenance, unit,
  coefficient, non-negativity, provisional-status, and equation checks;
- `__init__.py` exposes the public boundary.

`DoseState` contains the required fields:

| Field | Contract |
|---|---|
| `consumer_identifier` | Consumer identity copied through the public intake API |
| `age_group_identifier` | Explicit age group matched against `DoseParameters` |
| `pathway_identifier` | Explicit dose-pathway identity |
| `intake_inventory_bq` | Annual exposure-period intake inventory in Bq |
| `dose_coefficient` | Explicit coefficient value |
| `dose_coefficient_unit` | Exact `Sv/Bq` contract |
| `committed_dose_sv` | Calculated result in Sv |
| `time_period` | Exact `annual` contract |
| `timestamp` | UTC timestamp copied through the public intake API |
| `provenance` | Checked coefficient/result provenance |

The public methods are `inventory()`, `dose()`, and `consumer()`.
`DoseSolver.advance()` returns `DoseState` and does not mutate the input
`IntakeState`.

## Dose equation and units

The conversion is explicit and checked at construction:

    D [Sv]
      = I [Bq] * e [Sv/Bq]

The upstream P6.6A record represents one annual exposure-period intake. At
this boundary its annual inventory is consumed as the period-integrated Bq
input required by the coefficient contract. This is a declared stage
boundary, not an implicit time conversion or a claim about a validated
exposure-rate model.

## Parameter and activation boundary

`DoseParameters` requires explicit age-group, radionuclide, pathway,
coefficient, unit, provenance, and `parameter_status = "provisional"`.
Non-finite, negative, non-`Sv/Bq`, or non-provisional inputs fail closed. No
UFOTRI database, regulatory database, configuration, or trusted registry is
read. The coefficient is a supplied interface value and is not represented as
validated UFOTRI physics.

## Deliberate exclusions

P6.6B does not implement:

- regulatory assessment or compliance flags;
- risk metrics, emergency criteria, or decision thresholds;
- population distributions or uncertainty analysis;
- inhalation, skin, water, animal, or environmental dose pathways;
- dose-coefficient lookup or automatic database loading;
- CTEAS-Atmos coupling or V3 physics validation.

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
    V1_V2_DEFAULT_PATH_CHANGED = FALSE
