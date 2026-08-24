# Implementation status

Updated: 2026-08-24

## V3 P7.7B Baseline synthetic benchmark execution

P7.7B executes all five P7.7A synthetic cases through the existing public V3
solver and `V3PipelineRunner` APIs. `validation_v3/benchmark_runner.py` reads
the explicit YAML `execution_definition`, runs `dt`, `dt/2`, and `dt/4`
refinements, checks existing conservation ledgers, repeats each case for
determinism, and checks component/pipeline restart equivalence. Results are
serialized in
`validation/results/v3/p7_7b_synthetic_benchmark_results.yaml` with input
hashes, execution IDs, solver version, test-only snapshots, and provenance.

```text
P7_7B_STATUS = PASS_SYNTHETIC_BENCHMARK_VALIDATION
BENCHMARKS_EXECUTED = TRUE
DECAY_TEST = PASS
LEAF_TFWT_TEST = PASS
TFWT_OBT_TEST = PASS
SOIL_ROOT_TEST = PASS
END_TO_END_TEST = PASS
CONSERVATION = PASS
RESTART_EQUIVALENCE = PASS
SOLVER_CHANGES = FALSE
NUMERICAL_COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

This is synthetic software/interface evidence only. It does not validate
environmental realism, parameter accuracy, field observations, calibration,
regulatory dose coefficients, UFOTRI equivalence, or V3 physical readiness.
The execution policy and independent review are recorded in
`docs/adr/ADR-018-v3-synthetic-benchmark-validation-policy.md` and
`docs/v3/reports/v3_p7_7b_*.md`.

The historical full pytest collection is not used as the P7.7B gate because
its stage-specific architecture baselines intentionally reject follow-on
validation additions. With `--maxfail=1`, the first failure was
`tests/architecture/test_atmos_v3_boundary.py::test_p7_source_scope_is_atmospheric_interface_only`,
which only permits earlier atmospheric/pipeline source paths. The focused
P7.7B/P7.7A and parameter compatibility suites are the recorded stage checks.

## V3 P7.7A Baseline validation framework

P7.7A adds an isolated validation control plane at
`src/cteas_ufotri/validation_v3/`. `ValidationCase` requires named forcing,
initial state, explicit parameter snapshots, model outputs, reference data,
expected metrics, acceptance criteria, and complete artifact provenance.
`ValidationResult` records the metric value, threshold, pass/fail decision,
uncertainty, execution hash, solver version, and parameter snapshot. The
metric layer supports RMSE, MAE, relative error, bias, conservation residual,
trajectory comparison, decay error, and state difference; it audits existing
ledgers without replacing them.

Five synthetic benchmark definitions are stored in
`configs/v3/validation/p7_7a_baseline_benchmarks.yaml`. They are interface
fixtures only: values are test-only, no production solver is called by the
loader, and no physical parameter truth is inferred. `can_enter_validation()`
admits only synthetic/software/analytical baseline cases with explicit
`TEST_ONLY` parameters and rejects active parameters, calibration, physical or
empirical validation classes, UFOTRI database activation, and V3 readiness.

```text
P7_7A_STATUS = PASS_VALIDATION_FRAMEWORK
VALIDATION_SCHEMA = TRUE
VALIDATION_METRICS = TRUE
BASELINE_BENCHMARKS_DEFINED = TRUE
SOLVER_CHANGES = FALSE
NUMERICAL_COUPLING_CHANGES = FALSE
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The machine-readable schema is
`schemas/v3/validation_case.schema.json`; policy and review artifacts are
`docs/adr/ADR-017-v3-validation-framework-policy.md`,
`docs/v3/validation/`, `docs/v3/reports/v3_p7_7a_validation_framework_report.md`,
and `docs/v3/reports/v3_p7_7a_independent_review.md`. Focused schema, metric,
result, gate, benchmark, and source-isolation tests pass. No P7.6D redesign,
solver equation, numerical coupling, pipeline semantic, active parameter, or
calibration path was changed.

## V3-P7.6A Parameter evidence and provenance freeze

P7.6A adds a control-plane-only parameter evidence layer at
`src/cteas_ufotri/parameters_v3/`. The immutable `ParameterEvidenceRecord`
preserves reported and normalized values separately, requires explicit units,
source identifiers, applicability, review state, and repository/file/location
provenance. `ParameterEvidenceRegistry` sorts records deterministically,
rejects duplicate IDs, and rejects `VALIDATED`/`ACTIVE` records at the P7.6A
stage gate. It is not imported by any P6/P7 physics module or by the P7.5
pipeline.

The canonical inventory contains 76 records across the 10 required primary
classes: 56 provisional records and 20 test-only `EVIDENCE_FOUND` records.
The test-only status means reproducible software fixture evidence only; it is
not physical, empirical, calibration, regulatory, or observational evidence.
No production value is resolved, converted, calibrated, or activated.

    P7_6A_STATUS = PASS_PARAMETER_EVIDENCE_PROVENANCE_FROZEN
    PARAMETER_INVENTORY_COMPLETE = TRUE
    PARAMETER_EVIDENCE_SCHEMA_FROZEN = TRUE
    PARAMETER_STATUS_LIFECYCLE_FROZEN = TRUE
    PARAMETER_CALIBRATION_STARTED = FALSE
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE

The manifest and stage records are in
`docs/v3/parameter_evidence/parameter_inventory.yaml`. The implementation,
gap matrix, test report, and independent review are in
`docs/v3/reports/v3_p7_6a_parameter_inventory_report.md`,
`docs/v3/reports/v3_p7_6a_parameter_evidence_report.md`,
`docs/v3/reports/v3_p7_6a_parameter_gap_analysis.md`,
`docs/v3/reports/v3_p7_6a_test_report.md`, and
`docs/v3/reports/v3_p7_6a_independent_review.md`. The formal decision is in
`docs/adr/010-v3-parameter-evidence-lifecycle.md`.

## V3-P7.6B-1 Parameter applicability review

P7.6B-1 adds an immutable source-to-model `ApplicabilityRecord`, a
one-to-one deterministic review matrix for all 76 P7.6A records, and a
fail-closed validation-candidate gate. The five applicability dispositions are
`DIRECT_MATCH`, `PARTIAL_MATCH`, `TRANSFER_REQUIRED`, `NOT_APPLICABLE`, and
`UNKNOWN`. The matrix records 26 unresolved model/evidence reviews as
`UNKNOWN` and 50 scenario/control/test records as `NOT_APPLICABLE`; there are
no direct, partial, or transfer dispositions and no admitted candidates.

`EVIDENCE_FOUND` test fixtures remain software evidence only. The candidate
gate requires a non-test-only `EVIDENCE_FOUND` record plus a direct match, or
a partial match with resolved uncertainty and a direct unit match. It only
identifies candidates for a future protocol; it cannot validate, calibrate,
activate, replace a value, or provide a runtime lookup.

    P7_6B1_STATUS = PASS_PARAMETER_APPLICABILITY_REVIEW
    PARAMETER_APPLICABILITY_SCHEMA = TRUE
    PARAMETER_REVIEW_MATRIX = TRUE
    VALIDATION_CANDIDATES_IDENTIFIED = TRUE
    VALIDATION_CANDIDATE_COUNT = 0
    CALIBRATION_STARTED = FALSE
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE

The canonical matrix is in
`docs/v3/parameter_evidence/parameter_applicability_matrix.yaml`. The review,
matrix, gate, and independent boundary reports are in
`docs/v3/reports/v3_p7_6b1_applicability_review.md`,
`docs/v3/reports/v3_p7_6b1_parameter_review_matrix.md`,
`docs/v3/reports/v3_p7_6b1_validation_gate_report.md`, and
`docs/v3/reports/v3_p7_6b1_independent_review.md`; the test report is in
`docs/v3/reports/v3_p7_6b1_test_report.md`. The formal decision is in
`docs/adr/011-v3-parameter-applicability-review.md`.

## V3-P7.6B-2A Parameter candidate construction

P7.6B-2A adds a deterministic candidate-preparation control plane over the
P7.6A evidence inventory and P7.6B-1 applicability matrix. Each candidate
record carries explicit evidence links, applicability disposition, candidate
lifecycle status, screening disposition, reason, uncertainty source,
validation plan, priority tier, and provenance. The registry contains exactly
the 76 reviewed inventory records and does not contain reported or normalized
parameter values.

Candidate admission requires an evidence record with `EVIDENCE_FOUND`, a
non-test-only source, and an applicability disposition other than `UNKNOWN`
or `NOT_APPLICABLE`. `DIRECT_MATCH`, `PARTIAL_MATCH`, and
`TRANSFER_REQUIRED` are admissible shapes for a future validation candidate,
but every such record remains `validation_required = true`. The current
reviewed inputs produce no admitted candidates: 26 records remain
`PROVISIONAL`/`DEFERRED`, while 50 scenario, numerical-control, or test-only
records are `REJECTED` for this physical-validation screen.

    P7_6B2A_STATUS = PASS_PARAMETER_CANDIDATE_CONSTRUCTION
    PARAMETER_CANDIDATE_REGISTRY = TRUE
    VALIDATION_CANDIDATES_IDENTIFIED = TRUE
    VALIDATION_CANDIDATE_COUNT = 0
    VALIDATED_PARAMETERS = 0
    ACTIVE_PARAMETERS = 0
    CALIBRATION_STARTED = FALSE
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE
    PHYSICS_MODULE_CHANGED = FALSE

`can_enter_validation()` admits only the explicit
`VALIDATION_CANDIDATE` lifecycle state; the P7.6B-2A registry rejects
`VALIDATED` and `ACTIVE` records, so candidate construction cannot activate a
parameter or start calibration. The candidate layer is not imported by any
solver, coupling, or pipeline module.

The canonical registry is in
`docs/v3/parameter_evidence/parameter_candidate_registry.yaml`. The
construction, registry, gate, and independent review records are in
`docs/v3/reports/v3_p7_6b2a_candidate_construction_report.md`,
`docs/v3/reports/v3_p7_6b2a_candidate_registry_report.md`,
`docs/v3/reports/v3_p7_6b2a_validation_gate_report.md`, and
`docs/v3/reports/v3_p7_6b2a_independent_review.md`. The formal decision is in
`docs/adr/012-v3-parameter-candidate-construction.md`.

## V3-P7.6B-2B Evidence recovery and validation-candidate generation

P7.6B-2B adds a fail-closed evidence-recovery gate to the P7.6A/P7.6B-1
control plane. Recovered physical evidence must carry complete bibliographic
metadata, a source identifier match, an explicit equation role, reported and
canonical units, and a visible conversion path. The candidate layer also
records deterministic applicability links, equation/unit compatibility, and
remaining questions.

One external physical-constant record was accepted:
`soil.tritium_half_life`, from Lucas and Unterweger's NIST review. It is a
direct match only for the existing H-3 radioactive-decay term. OBT formation/
turnover, root uptake, leaf resistance, and soil-transport screens remain
deferred because the reviewed material did not close the current V3 equation,
compartment, effective-velocity, or resistance-unit requirements. No source
values were averaged or filled by assumption.

The canonical evidence inventory now contains 55 `PROVISIONAL` records and 21
`EVIDENCE_FOUND` records, of which 20 remain test-only fixtures. The
applicability matrix contains one `DIRECT_MATCH`, 25 `UNKNOWN`, and 50
`NOT_APPLICABLE` records. The candidate registry covers all 76 records and
contains one `VALIDATION_CANDIDATE`, 25 deferred records, and 50 rejected
records; it contains no parameter values.

    P7_6B2B_STATUS = PASS_EVIDENCE_RECOVERY
    EVIDENCE_RECORDS_UPDATED = TRUE
    PARAMETER_APPLICABILITY_REVIEW_UPDATED = TRUE
    PARAMETER_CANDIDATE_REGISTRY = TRUE
    VALIDATION_CANDIDATES_IDENTIFIED = TRUE
    VALIDATION_CANDIDATE_COUNT = 1
    VALIDATED = 0
    ACTIVE = 0
    CALIBRATION_STARTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE
    PHYSICS_CHANGED = FALSE
    NUMERICAL_COUPLING_CHANGED = FALSE

The stage artifacts are
`docs/v3/parameter_evidence/parameter_inventory.yaml`,
`docs/v3/parameter_evidence/parameter_applicability_matrix.yaml`,
`docs/v3/parameter_evidence/parameter_candidate_registry.yaml`,
`docs/v3/reports/v3_p7_6b2b_evidence_recovery_report.md`,
`docs/v3/reports/v3_p7_6b2b_candidate_generation_report.md`,
`docs/v3/reports/v3_p7_6b2b_parameter_review_report.md`, and
`docs/v3/reports/v3_p7_6b2b_independent_review.md`.

The control plane remains isolated from all V3 physics, numerical-coupling,
pipeline, and runtime parameter modules.

## V3-P7.6C-1 Physical-constant validation and evidence reconciliation

P7.6C-1 closes the first formal validation loop for the only current physical
candidate, `soil.tritium_half_life`. The new immutable
`PhysicalConstantEvidenceRecord` preserves each evaluation's reported value,
uncertainty, unit, explicit SI conversion, evaluation basis, and source
lineage. `ParameterValidationRecord` keeps source records separate from the
selected value and enforces equation, unit, applicability, reconciliation,
uncertainty, review, and benchmark gates. Derived or duplicate evidence never
counts as an independent evidence stream, and source conflicts fail closed to
`HOLD` without averaging.

The NIST evaluation reports `4500 +/- 8 d`. The later DDEP/BIPM evaluation
reports `4497 +/- 9 d` and explicitly derives its 3H evidence table from the
Lucas--Unterweger evaluation. The sources are consistent after explicit
normalization; DDEP is selected unchanged under the recorded
`LATEST_RECOGNIZED_EVALUATED_RECOMMENDATION_WITH_EXPLICIT_LINEAGE` policy.
This validates only the universal H-3 radioactive-decay half-life for
`lambda_T = ln(2) / T_half`; it does not validate soil retention, transport,
plant transfer, OBT, exposure, dose, or chemical-form corrections.

```text
P7_6C1_STATUS = PASS_PHYSICAL_CONSTANT_VALIDATION
PHYSICAL_CONSTANT_VALIDATION_COMPLETE = TRUE
SOIL_TRITIUM_HALF_LIFE = VALIDATED
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
EVIDENCE_RECONCILIATION = PASS
UNCERTAINTY_PROVENANCE = PASS
DECAY_SEMANTIC_BENCHMARK = PASS
CALIBRATION_STARTED = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
```

The canonical validation manifest is
`docs/v3/parameter_evidence/physical_constant_validation_registry.yaml`. The
formal policy is in
`docs/v3/adr/ADR-013-v3-physical-constant-validation-policy.md`; stage reports
are in `docs/v3/reports/v3_p7_6c1_physical_constant_validation_report.md`,
`docs/v3/reports/v3_p7_6c1_evidence_reconciliation_report.md`,
`docs/v3/reports/v3_p7_6c1_test_report.md`, and
`docs/v3/reports/v3_p7_6c1_independent_review.md`.

The validation registry is not imported by any solver, coupling, pipeline, or
runtime parameter module. P7.6C-1 does not set `ACTIVE`, start calibration,
modify physics equations, modify numerical coupling, or promote
`V3_PHYSICS_READY`.

## V3-P7.5B Numerical coupling semantics freeze

P7.5B freezes the actual one-interval operator split used by the P7.5
pipeline.  Atmospheric forcing is representative of the complete interval
`[t_n, t_{n+1}]` and carries the interval-start label `t_n`; all emitted
continuous states and downstream records use `t_{n+1}`.  The frozen order is
soil deposition, leaf exchange into a TFWT intermediate, OBT transformation,
root uptake from the step-start soil snapshot, post-deposition soil/root
reconciliation, OBT-loss then root-input TFWT reconciliation, and finally
food/intake/dose endpoint readout.

Soil, TFWT, and OBT remain continuous reservoirs.  Root fluxes and ledgers are
interval transfer records.  Harvest, food, intake, and dose are non-mutating
endpoint assessment/readout records; P7.5B does not model continuous harvest
or cumulative food consumption.

The coupling is an explicit sequential/operator-split composition, not a
fully implicit solution.  Timestep refinement is therefore required and is
checked over a fixed synthetic horizon without introducing an unvalidated
accuracy threshold.

    P7_5B_STATUS = PASS_NUMERICAL_COUPLING_SEMANTICS_FROZEN
    V3_PIPELINE_AVAILABLE = TRUE
    NUMERICAL_COUPLING_FROZEN = TRUE
    TIMESTEP_REFINEMENT = PASS
    RESTART_EQUIVALENCE = PASS
    PIPELINE_CONSERVATION = PASS
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE

The implementation, numerical test, and independent review records are in
`docs/v3/reports/v3_p7_5b_numerical_coupling_implementation_report.md`,
`docs/v3/reports/v3_p7_5b_numerical_coupling_test_report.md`, and
`docs/v3/reports/v3_p7_5b_independent_review.md`.  The formal decision is in
`docs/adr/009-v3-pipeline-numerical-coupling-semantics.md`.

## V3-P7.5 End-to-end pipeline integration

The P7.5 branch adds `v3_pipeline/` as a stateless orchestration layer over
the existing typed V3 modules. `V3PipelineParameters` requires every
interval, resistance, soil, root, OBT, biological, harvest, consumption,
dose, root-zone, and consumer input explicitly. `V3PipelineRunner` retains
no mutable inventory and returns a new frozen `V3SimulationState` for each
step.

The controlled order is atmospheric forcing and soil deposition, leaf
exchange into TFWT, OBT formation, root uptake, root/OBT balance application
back to TFWT and soil, food transfer, intake, and dose. Existing solver
balances are preserved in `V3PipelineLedger`; the orchestration layer adds
only state wiring and cross-module consistency checks. `V3SimulationState`
also supports validated mapping/JSON round-trips for an explicit restart
boundary.

The root solver is called against the step-start soil snapshot because its
public contract advances the supplied soil timestamp by the interval. Its
typed transfer balance is then applied to the post-deposition soil state at
the same endpoint timestamp. Similarly, the OBT solver's reported TFWT loss
is consumed before the root transfer is applied to the final TFWT state.
These are state-boundary operations; P7.5 does not reimplement either
solver's equation.

    P7_5_STATUS = PASS_PIPELINE_INTEGRATION
    V3_PIPELINE_AVAILABLE = TRUE
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

The implementation, test, and independent boundary-review records are in
`docs/v3/reports/v3_p7_5_pipeline_integration_report.md`,
`docs/v3/reports/v3_p7_5_pipeline_test_report.md`, and
`docs/v3/reports/v3_p7_5_independent_review.md`.

## V3-P7 Atmospheric forcing coupling interface

The P7 branch adds a typed atmospheric forcing boundary at
`coupling/atmos_v3/`. `AtmosphericHTOForcing` is immutable and fail-closed:
timestamp, location, air HTO concentration, deposition flux, temperature,
humidity, wind speed, precipitation, source, and provenance are explicit
inputs. Concentration, flux, temperature, humidity, wind-speed,
precipitation, and metadata time-resolution units are checked exactly; no
unit conversion or missing-value repair is performed. The `air_ht0_concentration`
spelling is retained as an explicit alias of the canonical
`air_hto_concentration` field.

`AtmosphericForcingMetadata` records model name, version, grid definition,
time resolution, source dataset, UTC creation time, and quality flag. The
interface has two adapters only: atmospheric forcing can produce the
existing leaf-resistance forcing input or the existing soil deposition
forcing input. It does not import or call TFWT, OBT, root-uptake,
food-transfer, intake, or dose solvers, and it has no CALMET/CALPUFF,
ERA5/WRF file-reader, dispersion, hydrology, or UFOTRI parameter-loader
dependency.

    P7_ATMOS_INTERFACE_STATUS = PASS
    ATMOS_FORCING_INTERFACE = TRUE
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
    NEXT_PHASE = P8_CTEAS_ATMOS_DATA_EXCHANGE

The implementation, test, and independent boundary-review records are in
`docs/v3/reports/v3_p7_atmos_interface_implementation_report.md`,
`docs/v3/reports/v3_p7_atmos_interface_test_report.md`, and
`docs/v3/reports/v3_p7_independent_review.md`.

## V3-P6.6B Intake-to-dose assessment

The P6.6B branch adds an isolated downstream dose boundary at
`exposure/dose_v3/`. `DoseSolver` consumes only the public `IntakeState`
methods `inventory()`, `consumer()`, `age_group()`, `period()`, and `time()`.
It emits an immutable `DoseState` containing the intake inventory, explicit
dose coefficient, committed-dose result, pathway, age group, time, and
provenance. No environmental, plant, food, or assessment-policy state is
created.

The frozen conversion equation is:

    D [Sv]
      = I [Bq] * e [Sv Bq^-1]

The P6.6A annual intake is consumed as one explicit annual exposure-period
inventory at this boundary; no hidden time, coefficient, or database default
is introduced. `DoseParameters` requires an explicit `Sv/Bq` coefficient and
`parameter_status = provisional`. The coefficient is an interface input, not
a validated UFOTRI or regulatory value.

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
    NEXT_PHASE = P7_CTEAS_ATMOS_COUPLING

The implementation, test, and independent boundary-review records are in
`docs/v3/reports/v3_p6_6b_dose_assessment_implementation_report.md`,
`docs/v3/reports/v3_p6_6b_dose_assessment_test_report.md`, and
`docs/v3/reports/v3_p6_6b_independent_review.md`.

## V3-P6.6A Food consumption and intake pathway

The P6.6A branch adds an isolated food-to-human inventory boundary at
`exposure/intake_v3/`. `FoodIntakeSolver` consumes a typed `FoodInventory`
through its public `inventory()` and `product()` methods and emits an
immutable annual `IntakeState`. The state records consumer, age-group,
product, consumption rate, annual intake inventory, UTC time, and provenance;
it does not contain any downstream radiological-result or regulatory fields.

The dimensional calculation is explicit:

    C_food [Bq kg^-1]
      = M_food [Bq] / m_food [kg]

    I_food [Bq year^-1]
      = C_food [Bq kg^-1] * R_consumption [kg year^-1]

The food mass basis `m_food` is an explicit `ConsumptionParameters` input;
there is no hidden mass or unit conversion. Consumption parameters remain
provisional and are not loaded from the UFOTRI database or any regulatory
database. Adult and child records remain separate immutable states.

    P6_6A_STATUS = PASS_INTAKE_PATHWAY_IMPLEMENTED
    LEAF_RESISTANCE = TRUE
    TFWT_SOLVER = TRUE
    OBT_SOLVER = TRUE
    SOIL_SOLVER = TRUE
    ROOT_UPTAKE = TRUE
    FOOD_TRANSFER = TRUE
    INTAKE_PATHWAY = TRUE
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE
    V1_V2_DEFAULT_PATH_CHANGED = FALSE
    NEXT_PHASE = P6.6B_DOSE_ASSESSMENT

The implementation, test, and independent boundary-review records are in
`docs/v3/reports/v3_p6_6a_intake_pathway_implementation_report.md`,
`docs/v3/reports/v3_p6_6a_intake_pathway_test_report.md`, and
`docs/v3/reports/v3_p6_6a_independent_review.md`.

## V3-P6.5 Plant harvest and food transfer

The P6.5 branch adds an isolated plant-to-food inventory boundary at
plant/food_v3/. FoodTransferSolver consumes only the public inventory()
methods of OBTState and TFWTState. It emits an immutable HarvestState and a
FoodInventory record; it does not mutate plant states and does not create dose,
ingestion, population, regulatory, or CTEAS-Atmos state.

The OBT transfer equation is:

    M_food,OBT [Bq]
      = f_h [1] * M_OBT [Bq m^-2] * A_h [m^2]

The optional TFWT branch is:

    M_food,TFWT [Bq]
      = f_w [1] * M_TFWT [Bq m^-2] * A_h [m^2]

The harvest area A_h is explicit in HarvestParameters; no hidden area or
parameter default is used. Both transfer fractions remain provisional. The
FoodTransferBalance verifies:

    plant inventory
      = harvest transfer + remaining plant inventory + residual

    P6_5_STATUS = PASS_FOOD_TRANSFER_IMPLEMENTED
    LEAF_RESISTANCE = TRUE
    TFWT_SOLVER = TRUE
    OBT_SOLVER = TRUE
    SOIL_SOLVER = TRUE
    ROOT_UPTAKE = TRUE
    FOOD_TRANSFER = TRUE
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE
    V1_V2_DEFAULT_PATH_CHANGED = FALSE
    NEXT_PHASE = P6.6_DOSE_ASSESSMENT

The implementation, test, and independent boundary-review records are in
docs/v3/reports/v3_p6_5_food_transfer_implementation_report.md,
docs/v3/reports/v3_p6_5_food_transfer_test_report.md, and
docs/v3/reports/v3_p6_5_independent_review.md.

## V3-P6.4 Root uptake and Soil-Plant coupling

The P6.4 branch adds the first isolated Soil -> Root -> TFWT transfer
interface. The new plant/root_v3 package reads SoilState only through its
public inventory() and concentration() methods. RootUptakeSolver evaluates the
minimal provisional interface equation and emits a typed RootFlux record; it
does not mutate SoilState or create any plant compartment.

The effective coefficient is explicit and provisional:

    J_root = k_root * C_soil

where C_soil is in Bq m^-3 water, k_root is in m s^-1, and J_root is in
Bq m^-2 s^-1. The interval transfer is recorded in Bq m^-2. No value is read
from the UFOTRI parameter database, configs, parameters, or trusted registry.
The TFWT storage solver accepts the optional RootFlux and records its integrated
input in the existing storage balance. The previous leaf-only call path
remains valid.

The root source-inventory ledger verifies:

    initial soil inventory
      = root transfer + remaining soil inventory + other loss + residual

The ledger is a transfer boundary audit; P6.4 does not implement soil
hydrology, root geometry, root competition, or a production soil-state mutation
from uptake.

    P6_4_STATUS = PASS_ROOT_UPTAKE_IMPLEMENTED
    LEAF_RESISTANCE = TRUE
    TFWT_SOLVER = TRUE
    OBT_SOLVER = TRUE
    SOIL_SOLVER = TRUE
    ROOT_UPTAKE = TRUE
    ROOT_TO_TFWT_INTERFACE = TRUE
    ROOT_UPTAKE_COEFFICIENT = PROVISIONAL_EXPLICIT
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE
    V1_V2_DEFAULT_PATH_CHANGED = FALSE
    NEXT_PHASE = P6.5_FOODCHAIN

The implementation, test, and independent boundary-review records are in
docs/v3/reports/v3_p6_4_root_uptake_implementation_report.md,
docs/v3/reports/v3_p6_4_root_uptake_test_report.md, and
docs/v3/reports/v3_p6_4_independent_review.md.

## V3-P6.3 Soil HTO transport

The P6.3 branch adds an isolated inventory-based soil HTO pathway at
`plant/soil_v3/`. `SoilState` stores one immutable layer inventory and a
checked soil-water concentration derived from the explicit water-content
basis. `SoilStorageSolver` consumes only deposition and signed layer-transport
fluxes. A positive transport flux enters the current layer; a negative flux
leaves it. It does not calculate atmospheric dispersion or hydrology.

The first step uses the constant-flux linear storage equation with explicit
tritium half-life:

```text
dM_soil/dt = deposition_flux + transport_flux - lambda_T * M_soil
lambda_T = ln(2) / tritium_half_life_s
```

The state and balance ledger do not contain root, plant, foodchain, dose, or
CTEAS-Atmos state. The old V1/V2 `soil/` and `coupling/` paths remain
untouched; no default runtime or configuration is connected.

```text
P6_3_STATUS = PASS_SOIL_HTO_IMPLEMENTED
LEAF_RESISTANCE = TRUE
TFWT_SOLVER = TRUE
OBT_SOLVER = TRUE
SOIL_SOLVER = TRUE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V1_V2_DEFAULT_PATH_CHANGED = FALSE
P6_3_TARGETED_TESTS = PASS_14_OF_14
P6_3_REGRESSION_TESTS = PASS_1_OF_1
NEXT_PHASE = P6.4_ROOT_UPTAKE_FOODCHAIN
```

The implementation, test, and independent boundary-review records are in
`docs/v3/reports/v3_p6_3_soil_hto_implementation_report.md`,
`docs/v3/reports/v3_p6_3_soil_hto_test_report.md`, and
`docs/v3/reports/v3_p6_3_independent_review.md`.

## V3-P6.2C OBT solver

The P6.2C branch adds an isolated inventory-based TFWT-to-OBT solver at
`plant/obt_v3/`. It consumes only the public `TFWTState.inventory()` and
`TFWTState.activity_concentration()` methods. `OBTState` keeps OBT inventory as
the authoritative quantity and derives a checked fresh-mass concentration;
TFWT/OBT ratios are not stored. The biological forcing boundary currently uses
only `is_daylight`; temperature, photosynthetic activity, and growth stage are
reserved extension fields.

The solver accepts explicit provisional test rates and does not read the
UFOTRI parameter database, configs, or the trusted external-evidence registry.
It is not connected to the existing V1/V2 runtime, foodchain, dose, soil, or
the P6.2B plant facade. The P6.2B public pathway remains a TFWT-only pathway.

```text
P6_2C_STATUS = PASS_OBT_SOLVER_IMPLEMENTED
LEAF_RESISTANCE = TRUE
TFWT_SOLVER = TRUE
OBT_SOLVER = TRUE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V1_V2_DEFAULT_PATH_CHANGED = FALSE
P6_2C_TARGETED_TESTS = PASS_34_OF_34
P6_2C_BOUNDARY_REVIEW = PASS_4_OF_4
FULL_REPOSITORY_PYTEST = NOT_GREEN_17_ENVIRONMENT_OR_STAGE_INCOMPATIBLE_FAILURES
NEXT_PHASE = P6.3_SOIL_HTO
```

The implementation, test, and independent boundary-review records are in
`docs/v3/reports/v3_p6_2c_obt_solver_implementation_report.md`,
`docs/v3/reports/v3_p6_2c_obt_solver_test_report.md`, and
`docs/v3/reports/v3_p6_2c_independent_review.md`.

## V3-P6.2B integration and P6.2B-2.5 public interface freeze

The P6.2B integration branch preserves the P6.2B-1 resistance subsystem and
P6.2B-2 TFWT storage solver as separate V3 packages. The new `plant/v3`
facade only connects atmospheric forcing to a precomputed resistance state,
one signed leaf-exchange flux, and the public TFWT state API. OBT remains a
reserved future interface; no OBT, root, soil, dose, atmosphere, parameter
activation, or default-runtime connection was added.

```text
P6_2B_INTEGRATION_STATUS = PASS
P6_2B_INTERFACE_FREEZE = PASS
P6_2B_2_5_STATUS = PASS_PUBLIC_PATHWAY_INTERFACE_FREEZE
LEAF_EXCHANGE_RESISTANCE_IMPLEMENTED = TRUE
TFWT_SOLVER = TRUE
OBT_SOLVER = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
LEAF_EXCHANGE_COMPLETE = FALSE
V3_PHYSICS_READY = FALSE
NEXT_PHASE = P6_2C
```

The default V1/V2 configuration remains unchanged, including
`leaf_exchange_mode: off` and `direct_leaf_uptake_enabled: false`. The
implementation and boundary reports are in
`docs/v3/reports/v3_p6_2b_2_5_interface_implementation_report.md`,
`docs/v3/reports/v3_p6_2b_integration_review.md`, and
`docs/v3/reports/v3_p6_2b_2_5_boundary_audit.md`.

## V3-P6.2B-2 TFWT dynamic solver

The V3 TFWT storage-only solver consumes the signed P6.2B-1
`LeafExchangeFlux` and updates `TFWTState` at fixed water content. It does not
recompute resistance, create OBT, perform root or soil coupling, connect dose,
foodchain, CTEAS-Atmos, or alter the V1/V2 default path. The existing
`plant/tfwt.py` file remains unchanged; the V3 package is isolated at
`plant/tfwt_v3/`.

```text
P6_2B_2_STATUS = PASS_TFWT_SOLVER_IMPLEMENTED
LEAF_RESISTANCE = TRUE
TFWT_SOLVER = TRUE
OBT_SOLVER = FALSE
UFOTRI_DATABASE_ACTIVE = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
V3_PHYSICS_READY = FALSE
LEAF_EXCHANGE_COMPLETE = FALSE
P6_2B_2_INDEPENDENT_REVIEW = PASS
NEXT_PHASE = P6_2B_3
```

## V3-P6.2B-1 Leaf-exchange resistance subsystem

The resistance-only subsystem is implemented on a branch based on the latest
`origin/main@6671f579`. It is isolated from the existing V1/V2
`plant/leaf_exchange.py` import path. The subsystem validates the atmospheric
forcing boundary, computes `r_a + r_b + r_c` and `g_ex`, and emits one signed
`LeafExchangeFlux` placeholder. The P6.1 ParameterDatabase is consumed only by
a structural `lookup(..., production=False)` seam because its implementation
remains on an unmerged branch. No parameter value, default, trusted registry,
or production path is changed.

```text
P6_2B_1_STATUS = PASS_RESISTANCE_SUBSYSTEM_IMPLEMENTED
LEAF_EXCHANGE_RESISTANCE_IMPLEMENTED = TRUE
LEAF_EXCHANGE_SOLVER = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
LEAF_EXCHANGE_COMPLETE = FALSE
TFWT_SOLVER = FALSE
OBT_SOLVER = FALSE
V3_PHYSICS_READY = FALSE
NEXT_PHASE = P6_2B_2
```

## D3 UFOTRI manual data mapping and laboratory handoff

The working branch `codex/v3-d3-ufotri-manual-data-mapping` was created from
the clean laboratory-handoff branch `codex/v3-d3-lab-feasibility-handoff` at
`72c757159807c692c4a4c792db41302356dbcd7e`. The read-only `ufotri_manual.md`
source was checked at SHA-256
`82c7c7f07975553a51e7ba1666a912f80096e5af4fc138aba6f45a120e6d3562`.
The manual-to-D3 matrix contains 100 fields and keeps manual case values
separate from D3 design values and modern QA fields. The D3 primary endpoint
is explicitly combined stem-and-leaf TFWT; roots, pods and seeds remain outside
the primary endpoint. The D3 planning LOD of 250 Bq/L is not a laboratory
capability claim.

```text
D3_UFOTRI_MANUAL_MAPPING_ID = D3_UFOTRI_MANUAL_DATA_FIELD_MAPPING_V1
D3_UFOTRI_MANUAL_MAPPING_STATUS = FROZEN_PRE_LAB
D3_UFOTRI_MANUAL_MAPPING_FIELDS = 100
D3_UFOTRI_MANUAL_EXPLICIT_FIELDS = 36
D3_UFOTRI_MANUAL_DERIVED_FIELDS = 10
D3_UFOTRI_D3_DESIGN_SPECIFIC_FIELDS = 34
D3_UFOTRI_MODERN_QA_FIELDS = 17
D3_UFOTRI_CONTROLLED_CHAMBER_NA_FIELDS = 7
D3_UFOTRI_UNRESOLVED_FIELDS = 3
D3_UFOTRI_MAPPING_TESTS = PASS_22_OF_22
D3_UFOTRI_MANUAL_MAPPING_REMEDIATION_R1 = HOLD_UNRESOLVED_EXTERNAL_INPUT
D3_UFOTRI_MANUAL_DATA_MAPPING_REMEDIATION_R1 = READY_FOR_INDEPENDENT_REREVIEW
D3_SCOPED_REMEDIATION_SELF_CHECK = PASS_SELF_CHECK
D3_TARGETED_MAPPING_RELATED_TESTS = PASS_107_OF_107_WITH_1_PRIVATE_SKIP
D3_CLEAN_WORKTREE_FULL_PYTEST = PASS_107_OF_108_WITH_1_EXPLICIT_PRIVATE_SKIP
D3_REPOSITORY_FULL_PYTEST_BASELINE = BLOCKED_24_FAILED_6_ERRORS_MISSING_IGNORED_EXTERNAL_INPUTS
D3_PORTABLE_CLEAN_WORKTREE_TESTS = PASS_WITH_DOCUMENTED_EXTERNAL_INPUT_SKIPS
D3_PORTABLE_FULL_PYTEST = PASS_660_WITH_51_DOCUMENTED_EXTERNAL_INPUT_SKIPS
D3_STRICT_EXTERNAL_INPUT_TESTS = BLOCKED_MISSING_SB1_SB4_INPUTS
D3_PRIVATE_SECRET_AUDIT = SKIP_PRIVATE_SECRET_NOT_AVAILABLE
D3_LOCAL_FULL_RECOMPUTE_WITH_EXTERNAL_INPUTS = HISTORICAL_PASS_NOT_REPRODUCED_IN_THIS_WORKTREE
D3_PORTABLE_ERA5_RECOMPUTE = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT
D3_ACCEPTANCE_AND_VERIFIERS = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT_WITH_EXIT_2_STATUS
D3_SRC_DIFF_FROM_MAIN = 0
D3_FORMAL_CONFIGS_DIFF_FROM_MAIN = 0
D3_TRUSTED_REGISTRY_DIFF_FROM_MAIN = 0
D3_REAL_EXPERIMENT = NOT_EXECUTED
D3_REAL_EXTERNAL_EVIDENCE = FALSE
D3_H2_H3_FORMAL_SELECTION = NOT_AUTHORIZED
D3_FORMAL_V3_PHYSICS = NOT_STARTED
D3_LAB_FEASIBILITY_STATUS = AWAITING_LAB_CONFIRMATION
D3_V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
D3_MAPPING_COMMIT_STATUS = R1_PUSHED_NOT_MERGED
```

## D3 UFOTRI manual mapping independent rereview R1

The complete manual mapping and external-input portability remediation were
independently rereviewed in a fresh worktree at fixed target
`0164a99cae30ab44411fe98be9ea9cc512c51966`. No external SB1/SB4/ERA5 input or
private secret was read. The independent rereview test and report are in
`tests/external_evidence_acquisition/test_d3_ufotri_manual_data_mapping_independent_rereview_r1.py`
and
`docs/v3/experiments/d3_ufotri_manual_data_mapping_independent_rereview_r1.md`.

```text
D3_UFOTRI_MANUAL_DATA_MAPPING_INDEPENDENT_REREVIEW_R1 = PASS_TRACEABLE_PORTABLE_AND_FAIL_CLOSED
D3_INDEPENDENT_REREVIEW_TESTS = 21
D3_INDEPENDENT_REREVIEW_MANUAL = PASS_36_EXPLICIT_10_DERIVED_3_DEFERRED
D3_INDEPENDENT_REREVIEW_PORTABILITY = PASS
D3_INDEPENDENT_REREVIEW_STRICT_EXTERNAL = PASS_49_FAIL_CLOSED_MISSING
D3_INDEPENDENT_REREVIEW_ERA5_VERIFIERS = PASS_4_EXIT_2_BLOCKED
D3_INDEPENDENT_REREVIEW_MODEL_OR_PARAMETER_CHANGE = NONE
D3_INDEPENDENT_REREVIEW_REAL_EXTERNAL_EVIDENCE = FALSE
D3_INDEPENDENT_REREVIEW_FORMAL_V3_PHYSICS = NOT_STARTED
D3_INDEPENDENT_REREVIEW_MERGE_RECOMMENDATION = READY_FOR_FAST_FORWARD_MERGE
```

The external-input portability remediation is isolated on branch
`codex/v3-external-input-test-portability-r1`, based on R1 snapshot
`29f59c83cb2ed6b8c4111799a3e3878c8b568b72`. Portable pytest runs preserve all
original numerical assertions and skip only tests marked as direct readers of
missing SB1, SB4, ERA5, or private-secret inputs. `--require-external-inputs`
converts missing required inputs into explicit failures with a complete missing
file list. Malformed or incomplete inputs are failures in both modes. No raw
data, placeholder, synthetic input, key, threshold, model source, or physics
gate was changed; the R1 snapshot was pushed, while this portability branch has
not yet been independently reviewed or merged.

## D3 discriminability review and external-evidence acquisition

The frozen H2/H3 D3 discriminability design was independently reproduced and
reviewed, then fast-forwarded through the design branch into `main` at
`1f44f8f847e8869e09b6f87262b81cafc2f2828e`. The independent review added 35
tests and returned `PASS`; it did not fit either candidate, use a latent pool,
or authorize formal V3 physics.

The acquisition branch froze its search protocol before searching. It found no
executable public Tier A or Tier B dataset. Three sources contain Tier C public
numeric evidence and five primary records are non-executable. The best request
target is the IAEA/KAERI EMRAS soybean package, whose three named forcing
workbooks are `REFERENCED_NOT_ACCESSIBLE`. A fresh worktree independently
reproduced the inventory and gate boundary, passed all 586 repository tests,
and fast-forwarded the reviewed acquisition research into local `main` at
`e0d6f89a34e75b939ec9fe64411d18f23866d76e`; that reviewed baseline was later
included in the D3 true-reblinding integration and pushed with the current
`main`.

```text
MERGED_D3_DESIGN_HEAD =
1f44f8f847e8869e09b6f87262b81cafc2f2828e
D3_MINIMUM_EXPERIMENT =
24H_EXPOSURE_PLUS_120H_FOLLOWUP_EQUALS_144H
D3_EXTENDED_120_DAY_FOLLOWUP = OPTIONAL
D3_INDEPENDENT_REVIEW_TEST_STATUS = PASS_35_OF_35
D3_RESEARCH_MERGE_STATUS = MERGED_AND_PUSHED

D3_ACQUISITION_BRANCH =
codex/v3-d3-external-evidence-acquisition
D3_ACQUISITION_INDEPENDENT_REVIEW =
PASS_REPRODUCIBLE_NO_EXECUTABLE_PUBLIC_DATA
D3_ACQUISITION_REVIEW_HEAD =
e0d6f89a34e75b939ec9fe64411d18f23866d76e
D3_ACQUISITION_BRANCH_MERGE = MERGED_AND_PUSHED_VIA_MAIN
D3_EXTERNAL_SEARCH_STATUS =
COMPLETE_NO_EXECUTABLE_PUBLIC_DATA
D3_TIER_COUNTS = A_0_B_0_C_3_NON_EXECUTABLE_5
D3_PUBLIC_RAW_DATA_FOUND = FALSE
D3_PUBLIC_NUMERIC_DATA_FOUND = TRUE
D3_RAW_FILE_DOWNLOAD_COUNT = 0
D3_EMRAS_ATTACHMENT_STATUS =
REFERENCED_NOT_ACCESSIBLE_ALL_3
D3_DATA_REQUEST_STATUS = DRAFT_READY_NOT_SENT
D3_EXPERIMENT_COMMISSION_PACKAGE_STATUS = READY
D3_ACQUISITION_TEST_STATUS = PASS_20_OF_20
D3_FULL_REPOSITORY_TEST_STATUS = PASS_586

D3_REAL_EXTERNAL_VALIDATION_RUN = NOT_STARTED
D3_TRUSTED_REGISTRY_CHANGE_COUNT = 0
D3_H2_H3_FORMAL_SELECTION = NOT_AUTHORIZED
D3_FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## D3 prospective synthetic experiment dry run

The branch `codex/v3-d3-prospective-experiment-dry-run` was created from the
locally merged acquisition review. V1 exposed a specification defect: the
post-exposure target of at most 0.5% of setpoint had been encoded as an exact
0.5% mean. Its positive-control failure remains archived. The prospectively
committed `D3_PROSPECTIVE_ASSUMPTIONS_V2` amendment separates a 0.25%
operational synthetic mean from the 0.5% target upper bound. It marks every
planning number as `PROJECT_ASSUMPTION_NOT_LITERATURE_FACT` and does not change
the frozen H2/H3 parameters, seeds or classifier thresholds.

The first executable stage generates 5-minute synthetic chamber forcing for a
24 h exposure and 120 h follow-up. The exposure time-weighted mean is exactly
5270 Bq/mL water with CV 5%. The default background remains positive and
measured in the synthetic record; a separate strict-zero background file is a
sensitivity scenario. Both files regenerate byte-for-byte from the frozen
seed and remain Git-ignored local dry-run data.

Terminology note for this historical dry-run paragraph: its unqualified
`5270 Bq/mL water` is shorthand for `5270 Bq/mL air-moisture water` in the
`HTO_IN_CHAMBER_AIR_MOISTURE` medium. It is not a liquid culture, irrigation
or reservoir-water concentration. This note clarifies the historical wording
without changing the synthetic result.

V2 tracked three sample-level datasets under A/B/C. Its classification commit
`f69dee0fb9a7e88e6c3ceebbde6bdd73adc9bdf2` preceded the V2 unblinding
commit, but the commit tree still contained the V1 A/B/C truth mapping. Because
V2 reused that mapping, it is numerically useful only and is not a valid blind
test. This failure is preserved without rewriting V1/V2 history.

V3 true reblinding froze the failure record and protocol before generating
exactly one new private realization. A system-CSPRNG secret produced three new
opaque IDs, a new biological-noise realization and a new private permutation.
The secret and truth key remain Git-ignored; only the secret SHA-256 commitment
is tracked. The preclassification commit contains no new ID-to-truth mapping,
and classification ran in a separate clean worktree with no V3 private files.
The classification commit was created before the first secret/truth-key read.
The single realization passed H2, H3 and out-of-model expectations 3/3. A new
independent review recomputed the sample-level classification and all 60 Monte
Carlo cells without reading the prior result CSVs.

```text
D3_PROSPECTIVE_ASSUMPTIONS = V2_FORCING_FROZEN_AND_TRACEABLE
D3_DRY_RUN_BLINDING_V1 = FAILED_ARCHIVED
D3_V1_ARCHIVE_CONTENT_INTEGRITY = PASS
D3_V1_ARCHIVE_COMMIT_CHRONOLOGY =
NONCOMPLIANT_WITH_PLANNED_ORDER
D3_DRY_RUN_BLINDING_V2 =
INVALID_TRUTH_MAPPING_PREEXPOSED
D3_V2_NUMERICAL_STATUS = SUCCESSFUL_DIAGNOSTIC_ONLY
D3_V2_EMPIRICAL_OR_BLIND_VALIDATION_CLAIM = FALSE
D3_BACKGROUND_OPERATIONAL_MEAN_FRACTION = 0.0025
D3_BACKGROUND_TARGET_MAXIMUM_FRACTION = 0.005
D3_PROSPECTIVE_EVIDENCE_CLASS =
SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN
D3_FORCING_STATUS = PASS_SYNTHETIC_CONTROLLED_FORCING
D3_FORCING_INTERVAL = COMPLETE_5_MINUTE_AXIS
D3_FORCING_REGENERATION = PASS_BYTEWISE
D3_DRY_RUN_BLINDING_V3 = PASS_TRUE_REBLINDING
D3_V3_OPAQUE_IDS = 2L9ET5_4SUJBR_VYBVXE
D3_V3_OBSERVATION_REALIZATION_REUSED = FALSE
D3_V3_GENERATION_ATTEMPTS = 1
D3_V3_CLASSIFICATION_ATTEMPTS = 1
D3_V3_REGENERATION_OR_RETRY = PROHIBITED
D3_V3_SECRET_GIT_TRACKED = FALSE
D3_V3_TRUTH_KEY_GIT_TRACKED = FALSE
D3_V3_TRACKED_SECRET_ARTIFACT = SHA256_ONLY
D3_V3_PRECLASSIFICATION_CONTAMINATION_SCAN = PASS
D3_V3_PRECLASSIFICATION_COMMIT =
b616d934fb0ae9d4abc90543d598de7c3754af23
D3_V3_CLASSIFICATION_COMMIT =
d8ae38373d63f2d4faa9ec0dede3f032077c98d3
D3_V3_UNBLINDING_COMMIT =
48b779980644a86471a049a8b5d3272f5ae9ec7a
D3_V3_CLASSIFIER_WORKTREE_SECRET_STATUS = ABSENT
D3_CLASSIFICATION_PARAMETER_REFIT_COUNT = 0
D3_V3_UNBLINDING_STATUS = PASS_TRUE_REBLINDING
D3_V3_EXPECTATION_PASS_COUNT = 3_OF_3
D3_H2_TRUTH_CLASSIFICATION = PASS
D3_H3_TRUTH_CLASSIFICATION = PASS
D3_OUT_OF_MODEL_CHALLENGE = PASS_DATA_INCONCLUSIVE
D3_CV20_PASSING_REPLICATE_COUNTS_3_TO_6 = 5_AND_6
D3_CV20_H2_CORRECT_RANGE = 0.869_TO_0.955
D3_CV20_H3_CORRECT_RANGE = 0.846_TO_0.955
D3_CV20_CHALLENGE_FALSE_CONFIDENT_RANGE = 0.027_TO_0.067
D3_DEFAULT_PLANNING_REPLICATES = 5_SYNTHETIC_TARGET_PASS
D3_DATA_INTAKE_DRY_RUN = PASS_SYNTHETIC_INTAKE_WORKFLOW
D3_INTAKE_RAW_SNAPSHOT = READ_ONLY_GIT_IGNORED
D3_INTAKE_REGISTRY_ELIGIBLE = FALSE
D3_V3_REMEDIATION_TESTS = PASS_26_OF_26
D3_V3_INDEPENDENT_REVIEW_TESTS = PASS_26_OF_26
D3_V3_INDEPENDENT_REVIEW =
PASS_REPRODUCIBLE_TRUE_REBLINDING
D3_FULL_PYTEST = PASS_671_OF_671_ONE_KNOWN_NUMPY_ABI_WARNING
D3_V1_V2_AND_V3_COMPATIBILITY_ARCHITECTURE = PASS
D3_V3_EXTERNAL_UNBLOCKING_VERIFIER = PASS_FAIL_CLOSED
D3_TRUE_REBLINDING_BRANCH_MERGE = MERGED_AND_PUSHED_TO_MAIN
D3_TRUE_REBLINDING_MAIN_HEAD = 569f6bc9b1e86b15056a0b5f178a656c27c5e6b1
D3_TRUE_REBLINDING_REMOTE_ALIGNMENT = PASS_MAIN_EQUALS_ORIGIN_MAIN
D3_EXPERIMENT_PACKAGE =
READY_FOR_LAB_FEASIBILITY_CONFIRMATION
D3_EXPERIMENT_COMMISSIONING =
READY_SUBJECT_TO_LAB_SAFETY_AND_CAPABILITY_CONFIRMATION
D3_NEXT_STEP = LAB_FEASIBILITY_CONFIRMATION
D3_REAL_EXTERNAL_EVIDENCE = FALSE
D3_TRUSTED_REGISTRY_ELIGIBLE = FALSE
D3_EMPIRICAL_VALIDATION_CLAIM = FALSE
D3_FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## EMRAS soybean SB1 research benchmark branch

This section records the non-production benchmark executed on
`codex/v3-emras-soybean-sb1-pdf-era5` from main baseline
`ae23ac037781caa5d69e2b69adb7de7214549c85`. It does not supersede the
released V2 candidate, register trusted external evidence, or authorize V3
physics.

```text
SB1_CASE_ID = EMRAS_SOYBEAN_SB1_PDF_ERA5_V1
SB1_DATASET_STATUS = READY_PUBLISHED_TABLES_PLUS_ERA5
SB1_SITE_STATUS = PROVISIONAL_WITH_SPATIAL_SENSITIVITY
SB1_CHAMBER_FORCING_STATUS = PUBLISHED_RAW_AND_MEAN_CONSTRAINED
SB1_OUTDOOR_FORCING_STATUS = ERA5_COMPLETE_FIVE_POINTS
SB1_MODEL_INTERFACE_STATUS = RUNNABLE_WITH_VALIDATION_ADAPTER_ONLY
SB1_BASELINE_RUN_STATUS = PASS_7_OF_7
SB1_CALIBRATION_STATUS =
CALIBRATED_MODEL_DEVELOPMENT_ONLY_BOUNDARY_HIT
SB1_PSEUDO_HOLDOUT_STATUS = EXECUTED_7_OF_7_NO_PARAMETER_RECALL
SB1_IDENTIFIABILITY_STATUS = LIMITED_BOUNDARY_OR_CORRELATION
SB1_BENCHMARK_STATUS = EXECUTED_AND_REPRODUCIBLE
SB1_EMPIRICAL_VALIDATION = NOT_CLAIMED
SB1_PRODUCTION_GATE_ELIGIBLE = FALSE
SB1_TARGETED_TEST_STATUS = PASS_16
SB1_FULL_REGRESSION_STATUS = PASS_367_ONE_KNOWN_NUMPY_NETCDF_WARNING
SB1_V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
SB1_V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
SB1_V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
SB1_V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
SB1_FORMAL_PHYSICS_CHANGE_COUNT = 0
SB1_FORMAL_CONFIG_CHANGE_COUNT = 0
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

## V3 P7.6C-2 UFOTRI semantic mapping

The P7.6C-2 audit inventories the available KfK 4605 UFOTRI manual and
separates it from project-derived V3 contracts. No original UFOTRI source code
or executable was recovered. The read-only mapping control plane records the
equation, quantity definition, unit, compartment, time/state basis, and
provenance for every current deferred V3 plant/soil/food/exposure parameter
covered by this stage. It does not load a value into a solver.

```text
P7_6C2_STATUS = PASS_SEMANTIC_MAPPING_COMPLETE
UFOTRI_MAPPING_COMPLETE = TRUE
UFOTRI_SOURCE_INVENTORY = COMPLETE_FOR_AVAILABLE_MANUAL
UFOTRI_SOURCE_CODE = SOURCE_UNAVAILABLE
UFOTRI_SOURCE_ASSETS_INSPECTED = 21
UFOTRI_V3_PARAMETERS_MAPPED = 26
UFOTRI_DIRECT_MAPPINGS = 12
UFOTRI_TRANSFORMABLE_MAPPINGS = 4
UFOTRI_CONCEPTUAL_ANALOGUES = 6
UFOTRI_NO_MAPPINGS = 3
UFOTRI_SOURCE_UNAVAILABLE_MAPPINGS = 1
NEW_VALIDATION_CANDIDATES = 0
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V3_PHYSICS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
```

The mapping manifest is
`docs/v3/parameter_evidence/ufotri_parameter_mapping.yaml`. The immutable
record type is
`src/cteas_ufotri/parameters_v3/ufotri_mapping.py`; it is not imported by
production plant, soil, exposure, coupling, or pipeline modules. P7.6C-2
classifies root rate versus V3 velocity, soil transport versus signed V3 flux,
continuous UFOTRI food-chain rates versus V3 harvest fractions, and external
intake/dose assumptions without guessing conversions. The targeted mapping
suite passes 8/8 tests; no production simulation, calibration, or physics
activation was run.
SB1_MERGE_RECOMMENDATION = READY_FOR_INDEPENDENT_BENCHMARK_REVIEW
```

The public IAEA tables were checked against rendered PDF pages. ERA5 is a
substitution for the unavailable organizer tower data, and the coordinate is
an institutional-area proxy rather than a confirmed plot. The primary model
reproduces only the first-hour scale and substantially underpredicts
plant-body TFWT after 24 h and the late residual platform. These limitations
are retained as scientific findings rather than removed by parameter
expansion.

## Independent SB1 review, merge and validation-only mechanism screen

The independent review branch rebuilt the benchmark from the source PDF and
five read-only raw ERA5 responses at exact benchmark head
`178fb0a3ebae53b20b101000cdbb2b39406088c0`. It added 27 independent tests,
confirmed the 24-2280 h structural underprediction, and returned
`PASS_REPRODUCIBLE_STRUCTURAL_DEFICIT`. The review was fast-forwarded through
the benchmark branch into `main`; merged `main` and `origin/main` are
`2a56c56d6de3ee79c1069b799a5dab90e10a0097`.

The subsequent branch
`codex/v3-sb1-plant-water-mechanism-discrimination` is validation-only. Its
protocol and all candidate ranges were committed before execution, and its
calibration parameters were committed before the late check. H1-H4 do not
modify `src/`, formal `configs/`, the trusted registry or a production gate.

```text
INDEPENDENT_SB1_BENCHMARK_REVIEW =
PASS_REPRODUCIBLE_STRUCTURAL_DEFICIT

SB1_BENCHMARK_MERGE_STATUS = MERGED_AND_PUSHED
MERGED_SB1_BASELINE_HEAD =
2a56c56d6de3ee79c1069b799a5dab90e10a0097

MECHANISM_PROTOCOL_STATUS = FROZEN_BEFORE_CANDIDATE_EXECUTION
MECHANISM_PARAMETER_STATUS = FROZEN_BEFORE_LATE_CHECK
MECHANISM_TARGETED_TEST_STATUS = PASS_17
MECHANISM_FULL_REGRESSION_STATUS =
PASS_411_ONE_KNOWN_NUMPY_NETCDF_WARNING
MECHANISM_V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
MECHANISM_V2_RECOMPUTE_STATUS =
PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
MECHANISM_V2_VALIDATION_READINESS_STATUS = PASS
MECHANISM_V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
MECHANISM_V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
MECHANISM_V3_EXTERNAL_EVIDENCE_STATUS =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA
MECHANISM_MASS_BALANCE_STATUS = PASS_35_OF_35
MECHANISM_FORCING_STATUS =
H1_0_OF_7_H2_7_OF_7_H3_4_OF_7_H4_0_OF_7
MECHANISM_DISCRIMINATION_STATUS =
NO_MINIMAL_MECHANISM_SUPPORTED
BEST_SUPPORTED_MECHANISM = NONE
FORMAL_V3_DESIGN_RECOMMENDATION = NOT_READY
MECHANISM_BRANCH_MERGE = NOT_REQUESTED
FORMAL_V3_PHYSICS_CHANGE = NOT_STARTED
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## EMRAS soybean SB4 frozen cross-experiment transfer

The SB1 mechanism result was independently reviewed at
`5c1d4bf39415be9b6e7960efeda23af50570f518`, fast-forwarded to `main` at
`d08d9d81f3ef10b11c2431e7bebe2f802c56cd18`, and pushed. The SB4 benchmark
branch starts from that exact merged main. It transcribes the SB4 publication
tables, reuses checksum-bound SB1 ERA5 raw inputs, and constructs two
explicitly reconstructed chamber profiles constrained to the reported SB4
mean.

The transfer protocol was committed before predictions. H2 and H3 parameters
come unchanged from SB1 frozen commit
`4b79f62741db4d4b51f4d608df33d2e13c499636`; no SB4 refit or selection
occurred. Both candidates pass all seven forcing scenarios under both profiles,
so the result supports only a bounded comparative design review, not a unique
mechanism or formal V3 implementation.

```text
SB1_MECHANISM_SCREEN = INDEPENDENTLY_REVIEWED_AND_MERGED
MERGED_MAIN_HEAD = d08d9d81f3ef10b11c2431e7bebe2f802c56cd18
SB4_CASE_ID = EMRAS_SOYBEAN_SB4_PDF_ERA5_V1
SB4_BRANCH = codex/v3-emras-soybean-sb4-transfer-benchmark
SB4_TESTED_EVIDENCE_PARENT = 8353611
SB4_DATA_STATUS = PASS_TRACEABLE_PUBLISHED_TABLE_TRANSCRIPTION
SB4_CHAMBER_PROFILE_STATUS = PASS_2_RECONSTRUCTED
SB4_ERA5_STATUS = PASS_REUSED_5_SB1_RAW_FILES_BY_CHECKSUM
SB4_PARAMETER_REFIT_COUNT = 0
SB4_RUN_STATUS = PASS_42_OF_42
SB4_H2_FORCING_STATUS = PASS_7_OF_7_BOTH_PROFILES
SB4_H3_FORCING_STATUS = PASS_7_OF_7_BOTH_PROFILES
SB4_MASS_BALANCE_STATUS = PASS_42_OF_42
SB4_TARGETED_TEST_STATUS = PASS_23
SB4_FULL_REGRESSION_STATUS =
PASS_458_ONE_KNOWN_NUMPY_NETCDF_WARNING
SB4_TRANSFER_STATUS = MULTIPLE_SLOW_MECHANISMS_TRANSFER_SUPPORTED
FORMAL_V3_DESIGN_RECOMMENDATION =
BOUNDED_COMPARATIVE_DESIGN_REVIEW_ONLY
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Current repository and release status

```text
CURRENT_RELEASED_MODEL =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE

CURRENT_MAIN_BASELINE_HEAD =
d08d9d81f3ef10b11c2431e7bebe2f802c56cd18

CURRENT_MAIN_HEAD =
d08d9d81f3ef10b11c2431e7bebe2f802c56cd18

CURRENT_DEVELOPMENT_BRANCH =
codex/v3-emras-soybean-sb4-transfer-benchmark

CURRENT_DEVELOPMENT_BASELINE_HEAD =
d08d9d81f3ef10b11c2431e7bebe2f802c56cd18

CURRENT_DEVELOPMENT_HEAD =
FINALIZED_ON_TOP_OF_TESTED_EVIDENCE_PARENT_8353611

CURRENT_DEVELOPMENT_STATUS =
SB4_TRANSFER_BENCHMARK_EXECUTED_AND_REPRODUCIBLE

CURRENT_TEST_STATUS =
PASS_458_ONE_KNOWN_NUMPY_NETCDF_WARNING

CURRENT_SB1_BENCHMARK_STATUS =
INDEPENDENTLY_REVIEWED_AND_MERGED

CURRENT_MECHANISM_BRANCH =
codex/v3-sb1-plant-water-mechanism-discrimination

CURRENT_MECHANISM_STATUS =
NO_MINIMAL_MECHANISM_SUPPORTED

CURRENT_MECHANISM_TEST_STATUS =
PASS_435_ONE_KNOWN_NUMPY_NETCDF_WARNING

CURRENT_V1_RECOMPUTE_STATUS =
PASS_5_FROZEN_CASES

CURRENT_V2_RECOMPUTE_STATUS =
PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE

CURRENT_V3_ARCHITECTURE_STATUS =
READY_ARCHITECTURE_ONLY

CURRENT_V3_PHYSICS_STATUS =
NOT_STARTED

FORMAL_V3_PHYSICS_STATUS =
NOT_STARTED

CURRENT_V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

CURRENT_EXTERNAL_EVIDENCE_PACKAGE_STATUS =
READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA

CURRENT_EXTERNAL_EVIDENCE_GATE_REMEDIATION_STATUS =
PASS_ADVERSARIAL_REVIEW_MERGED

CURRENT_SOYBEAN_DATA_STATUS =
BLOCKED_EXTERNAL_DATA

CURRENT_PREREGISTRATION_STATUS =
DRAFT_NOT_PREREGISTERED

CURRENT_CALIBRATION_STATUS =
NOT_RUN_BLOCKED_EXTERNAL_DATA

CURRENT_PARAMETER_IDENTIFIABILITY_STATUS =
NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE
```

The current released model is the immutable V2 candidate. The current `main`
publishes V3 architecture and the fail-closed external-evidence gate only.
The merged remediation replaces declaration
booleans with a runtime-validated artifact chain, strengthens numeric/checksum
intake validation, and passed the third independent adversarial review. It is
not a V3 physics release and contains no empirical data, calibration result,
or accepted holdout. The second remediation added a protected-ref approval
registry, stable-FD snapshots with final identity/hash rechecks, and
preregistered holdout-verdict recomputation. The third remediation binds
calibration, identifiability, and holdout to a canonical frozen parameter
contract.

## V3 external-evidence gate third remediation before independent review

The second independent review exposed an unbound preregistered parameter set.
The third remediation replaces the list with a canonical semantic contract
and binds calibration, identifiability, and holdout to the same names, units,
transforms, bounds, contract hash, and canonical result hash.

```text
F_04_STATUS = FIXED_PENDING_THIRD_INDEPENDENT_REVIEW
PREVIOUS_TARGETED_ATTACK_COUNT = 78
THIRD_REMEDIATION_ATTACK_COUNT = 37
TARGETED_ATTACK_STATUS = PASS_115
FULL_REGRESSION_STATUS = PASS_317
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY
V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
MERGE_RECOMMENDATION = HOLD_PENDING_THIRD_INDEPENDENT_REVIEW
```

### Third independent review and merge

The third independent worktree added 34 new cases without importing the
remediation fixture builder. All 149 targeted gate cases and all 351
repository tests passed on the merged main worktree.

```text
THIRD_INDEPENDENT_REVIEW_STATUS = PASS_ADVERSARIAL_REVIEW
F_01_STATUS = CONFIRMED_FIXED
F_02_STATUS = CONFIRMED_FIXED
F_03_STATUS = CONFIRMED_FIXED
F_04_STATUS = CONFIRMED_FIXED
THIRD_INDEPENDENT_ATTACK_COUNT = 34
TOTAL_TARGETED_GATE_STATUS = PASS_149
POST_MERGE_FULL_REGRESSION_STATUS = PASS_351
REMEDIATION_3_MERGE_STATUS = MERGED_BY_STRICT_FAST_FORWARD
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## V3 external-evidence gate second remediation

The three independent-review weaknesses were reproduced as three failing
attacks before repair. The imported attacks now pass together with the
original 32 attacks and 40 second-remediation tests.

```text
F_01_STATUS = FIXED_PENDING_SECOND_INDEPENDENT_REVIEW
F_02_STATUS = FIXED_PENDING_SECOND_INDEPENDENT_REVIEW
F_03_STATUS = FIXED_PENDING_SECOND_INDEPENDENT_REVIEW
TRUSTED_POLICY_PATH =
validation/v3/policy/trusted_external_evidence_registry.yaml
PRODUCTION_REGISTRY_ENTRY_COUNT = 0
TARGETED_ATTACK_STATUS = PASS_77
FULL_REGRESSION_STATUS = PASS_279
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY
V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
MERGE_RECOMMENDATION = HOLD_PENDING_SECOND_INDEPENDENT_REVIEW
```

## V3 external-evidence gate directed remediation

The two reproduced P1 issues were fixed without changing `src/` or `configs/`.
The physics gate now opens and validates raw, intake, preregistration,
calibration, identifiability, holdout, and regression artifacts; recomputes
raw/result checksums; verifies cross-artifact identifiers and hashes; and uses
Git object/history checks to prove that the frozen preregistration predates the
tracked holdout result. Synthetic/internal evidence types are explicitly
ineligible.

The soybean intake now parses required numeric columns, rejects empty,
non-numeric, NaN/Inf, invalid ranges, nonpositive chamber/mixing values,
invalid detection-limit/uncertainty mappings, duplicate or discontinuous
forcing timestamps, incomplete exposure coverage, split overlap, and checksum
tampering. Generated intake manifests are validated at runtime with
`jsonschema`.

```text
P1_01_STATUS = FIXED_PENDING_INDEPENDENT_REVIEW
P1_02_STATUS = FIXED_PENDING_INDEPENDENT_REVIEW
TEST_STATUS = PASS_234_ONE_KNOWN_NUMPY_NETCDF_WARNING
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
REMEDIATION_STATUS = READY_FOR_INDEPENDENT_ADVERSARIAL_REVIEW
MERGE_RECOMMENDATION = HOLD_PENDING_INDEPENDENT_REVIEW
```

## V3 architecture-only baseline

```text
MILESTONE_1 = V2_EXTERNAL_VALIDATION_PHASE1_MERGED
MILESTONE_2 = V3_ARCHITECTURE_BASELINE_READY
MILESTONE_3 = V3_EXTERNAL_EVIDENCE_INTAKE_READY
MILESTONE_4 = V3_PHYSICS_IMPLEMENTATION_GATE_REEVALUATED

V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_PHYSICS_IMPLEMENTATION_STATUS = NOT_STARTED
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

V2_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V1_GOLDEN_CASES = PASS_5_OF_5
V2_GOLDEN_CASES = PASS_6_OF_6
FORCING_72H_GOLDEN_STATUS = PASS_BITWISE
INDEPENDENT_REFERENCE_GOLDEN_STATUS = PASS_BITWISE

STATE_SCHEMA_STATUS = PASS
FLUX_SCHEMA_STATUS = PASS
LEDGER_CONTRACT_STATUS = PASS
CONFIG_RESULT_PROVENANCE_SCHEMA_STATUS = PASS
MODULE_REGISTRY_STATUS = PASS_8_UNIQUE
ADR_STATUS = PASS_8_COMPLETE
MIGRATION_MATRIX_STATUS = PASS_32_ROWS_COMPLETE
EXTERNAL_DATA_INTAKE_STATUS = PASS_FAIL_CLOSED

SOYBEAN_DATA_STATUS = BLOCKED_EXTERNAL_DATA
FIELD_DATA_STATUS = BLOCKED_EXTERNAL_DATA
PREREGISTRATION_STATUS = DRAFT_NOT_PREREGISTERED
CALIBRATION_STATUS = NOT_RUN_BLOCKED_EXTERNAL_DATA
PARAMETER_IDENTIFIABILITY_STATUS =
NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE

TEST_STATUS = PASS_191_ONE_KNOWN_NUMPY_NETCDF_WARNING
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END_AND_EXPANDED_ACCEPTANCE
VALIDATION_READINESS_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY
COMPILE_STATUS = PASS
DIFF_CHECK_STATUS = PASS
```

The V3 branch changes no `src/` file and no V2 configuration. It contains
architecture, ADRs, fail-closed schemas, a lossless `v2_frozen` migration
envelope, deterministic golden compatibility checks, evidence-intake
scaffolding, and architecture/physics gates. It implements no advanced
re-emission equation, formal three-box coupling, dynamic-air solver, HT
chemistry, or broader food/dose physics.

The next stronger gate remains unavailable until a complete legally usable
experiment or field case is acquired, preregistered before holdout inspection,
calibrated with a separate holdout, assessed for parameter identifiability, and
executed against that holdout.

## Historical released-model and validation-readiness milestones

```text
HISTORICAL_RELEASE_MILESTONE =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE

HISTORICAL_RELEASE_BASIS =
RC2_INDEPENDENT_REAUDIT_ACCEPTED_WITH_MINOR_CORRECTIONS

HISTORICAL_RELEASE_BRANCH =
codex/v2-physics-remediation-rc2

HISTORICAL_RELEASE_SOURCE_HEAD =
CANDIDATE_FINALIZATION_COMMIT_RECORDED_IN_RELEASE_REPORT_AND_TAG

V1_BASELINE =
6918440faa3455b848f43589784672f3bfabfe3d

V1_TAG =
formal-minimal-baseline-v1

HISTORICAL_RELEASE_TEST_STATUS =
PASS_167_ONE_KNOWN_WARNING

FORMAL_SCOPE =
HTO_ONLY_RESEARCH_CANDIDATE

SITE_CALIBRATED =
NO

REGULATORY_VALIDATED =
NO

COMPLETE_UFOTRI_EQUIVALENCE =
NO

ANIMAL_STATE_NAMING_STATUS =
DOCUMENTED_COMPATIBILITY_LIMITATION_WITH_BQ_M2_ALIASES

VALIDATION_INFRASTRUCTURE_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_VALIDATION_READY

HISTORICAL_VALIDATION_READINESS_BRANCH =
codex/v2-validation-readiness

EMPIRICAL_VALIDATION_STATUS =
BLOCKED_EXTERNAL_DATA

HISTORICAL_VALIDATION_READINESS_TEST_STATUS =
PASS_178_ONE_KNOWN_NUMPY_NETCDF_WARNING
```

The current physics acceptance basis is
`docs/v2/v2_rc2_independent_reaudit.md`, whose verdict is
`ACCEPT_RC2_WITH_MINOR_CORRECTIONS`. Release finalization resolves the named
provenance and current-status LOW findings without changing model results.
The five retained MEDIUM research limitations are frozen in
`docs/v2/v2_candidate_limitations.yaml`.

The post-candidate validation branch adds a 42-entry evidence registry,
external-data schemas, general metrics, an isolated validation runner,
forcing-completeness checks, parameter priorities, and closure plans for all
five MEDIUM limitations. `VALIDATION_READY` describes infrastructure, not
empirical validation: experiment, field, reference-model, complete observed
forcing, and site-case evidence remain absent and correctly blocked.

## Historical milestones

- V1 formal minimal baseline:
  `formal-minimal-baseline-v1` at `6918440faa3455b848f43589784672f3bfabfe3d`.
- Initial V2 self-assessment: historical candidate recommendation.
- Initial V2 independent audit: rejected for cross-module conservation and
  other evidence gaps.
- RC1 self-assessment: ready for independent re-audit.
- RC1 independent re-audit: `REJECT_RC1_REMEDIATION`.
- RC2 remediation status: candidate ready, held for independent review.
- RC2 independent re-audit:
  `ACCEPT_RC2_WITH_MINOR_CORRECTIONS`, with no BLOCKER or HIGH.

The complete immutable evidence chain is indexed in
`docs/v2/v2_audit_history.md`.

## Previous assessment: V2 physics remediation RC1 progress

Development branch: `codex/v2-physics-remediation-rc1`

```text
V2_STATUS = PHYSICS_REMEDIATION_RC1_CANDIDATE
FORMAL_ACCEPTANCE = PENDING_INDEPENDENT_REAUDIT
RC1_STAGE_1 = PASS
RC1_STAGE_2 = PASS
RC1_STAGE_3 = PASS
RC1_STAGE_4 = PASS
RC1_STAGE_5 = PASS
RC1_STAGE_6 = PASS
RC1_STAGE_7 = PASS
RC1_STAGE_8 = PASS
RC1_STAGE_9 = PASS
RC1_STAGE_10 = PASS
RC1_STAGE_11 = PASS
RC1_STAGE_12 = PASS_PREPARED_FOR_INDEPENDENT_REAUDIT
DRY_INTERFACE_CONSERVATION_STATUS = PASS
WET_INTERFACE_CONSERVATION_STATUS = PASS
DRY_WET_COMPETITION_STATUS = PASS
ACTIVITY_PROPAGATION_STATUS = PASS_STAGE_1_SCOPE
LEAF_RESISTANCE_METEOROLOGY_STATUS = PASS
LAI_APPLICATION_STATUS = PASS_NO_DOUBLE_COUNT
LEAF_END_TO_END_STATUS = PASS
BEEF_PRODUCTION_BOUNDARY_STATUS = PASS
MEAT_DOSE_CONSERVATION_STATUS = PASS
WET_PARAMETER_SOURCE_STATUS = PASS_DOCUMENTED_LITERATURE_COMPARISON
WET_PARAMETER_UNCERTAINTY_STATUS = PASS
ANALYTIC_BENCHMARK_COUNT = 10
MANUAL_OR_LITERATURE_NUMERIC_COUNT = 7
EXECUTION_ONLY_CASES_NOT_LABELLED_REFERENCE = PASS
FULL_MODEL_LHS_STATUS = PASS
SAMPLE_SIZE_CONVERGENCE_STATUS = PASS
MODE_AWARE_PARAMETER_STATUS = PASS
RANK_STABILITY_STATUS = LIMITED_WITH_EVIDENCE
PERENNIAL_PHENOLOGY_STATUS = PASS
MULTIYEAR_PASTURE_STATUS = PASS
MULTIBOX_SCOPE_STATUS = CLEAR_EXPERIMENTAL_STANDALONE
BLOCKER_REMAINING = 0
HIGH_REMAINING = 1_PARTIAL_H06_RANK_STABILITY
RC1_VERDICT = READY_FOR_INDEPENDENT_REAUDIT
INDEPENDENT_REAUDIT_RECOMMENDATION = PROCEED_BEFORE_FORMAL_ACCEPTANCE
RC1_TEST_STATUS = PASS_158
RC1_V1_RECOMPUTE_STATUS = PASS
RC1_V2_RECOMPUTE_STATUS = PASS
```

Stage 1 replaced the independent `v_d C_air` surface inventory input with
explicit dry and wet allocations of the plume-side loss. The two deposition
footprints are independent configuration objects and are not inferred from the
re-emission feedback area. The former `v_d C_air` value remains diagnostic
only. Tests cover the audited 72 h case, all five V2 configurations, footprint
scaling, dry/wet switches and zero limits, segment counts, the stack-input
upper bound, and surface inventory plus boundary-output closure.

Stage 2 replaced the fixed 50 s m-1 aerodynamic and boundary resistances with
the manual wind-profile equations plus a documented Golder
Pasquill-to-Monin-Obukhov mapping and a laminar flat-plate water-vapour
boundary correlation. The implementation is explicitly labelled
`LITERATURE_PARAMETERIZATION`, not validated UFOTRI equivalence. A new 72 h
formal case disables deposition and root uptake and independently propagates
air-leaf exchange through TFWT, OBT, edible leafy crop, and ingestion dose.
The mode-off control is zero, and the 600/300/120/60 s endpoints converge
within 1%.

Stage 3 adds a continuous representative-herd turnover boundary. Slaughter
HTO/OBT is removed from the animal once, becomes produced beef activity,
decays or remains in explicit product storage, and can be consumed only up to
the available product mass. The dose module uses actual consumed activity.
Mode `off`, zero turnover, product exhaustion, stopped production, product
closure, and combined animal/product closure are independently tested.

Stage 4 replaces the unsourced wet coefficient default with a named Japanet
literature-comparison parameter set while explicitly retaining the label
`LITERATURE_COMPARISON_NOT_UFOTRI`. Separate project low/central/high bounds
and a recomputable 4 x 3 \(a,b\) grid propagate wet uncertainty through
deposition, soil, plant, food, and dose outputs.

Stage 5 adds ten independent analytic benchmarks, five manual numeric anchors,
and two literature coefficient comparisons. All evidence is explicitly
classified; integration and regression runs are not labelled reference cases.

Stage 6 runs a mode-aware real full-dose LHS audit at n=64/128/256 with a
primary seed and three additional seeds. Quantiles converge at n=256 and the
dominant parameter is stable, while weak-parameter ranks remain explicitly
`LIMITED_WITH_EVIDENCE`.

Stage 7 adds explicit annual/perennial phenology modes, dormant pasture LAI,
multiple partial cuts, cross-year inventory retention, and a conservative
two-year pasture test.

Stage 8 freezes the three-box solver at
`PASS_EXPERIMENTAL_STANDALONE` and documents the interfaces required before any
future formal coupling claim.

Stage 10 adds a common whole-pathway activity protocol to every formal result
row and verifies all six end-to-end cases plus the two-year pasture case. The
expanded driver covers the 72 h dry counterexample, analytic dry/wet
competition, conservative beef, n=64/128/256 LHS, 600/300/120/60 s leaf
convergence, footprint scaling, zero source, closed internal transfers, stack
upper bounds, and combined activity residuals.
The exact Stage 10 command set passed: 158 tests, frozen V1 recomputation, V2
expanded recomputation, compileall over `src tests era5 scripts`, and
`git diff --check`. The known NumPy/NetCDF binary-compatibility warning remains
non-fatal.

The historical V2 status below records the pre-remediation implementation and
must not be interpreted as the current RC1 acceptance state.

Overall status: **FORMAL_MINIMAL_BASELINE_V1 complete**

This `complete` status is strictly bounded to: HTO-only; steady Gaussian
atmosphere; 5 cm single-layer surface soil; plant TFWT and simplified OBT;
soil/plant re-emission; 3600 s delayed atmospheric feedback; short ERA5 forcing;
recomputable acceptance; and surface-box closure rather than whole-domain
dynamic air conservation.

Wet scavenging is not implemented, and advanced REEM remains provisional. This
status does not mean complete UFOTRI, food chain, dose, HT chemistry, multi-layer
soil, whole-domain dynamic atmospheric conservation, or regulatory validation.

| Item | Status | Evidence / limitation |
|---|---|---|
| SURFACE_BOX_CLOSURE_STATUS | PASS | explicit soil + TFWT + OBT ledger; external inputs/outputs and internal transfers tested |
| ATMOSPHERIC_BUDGET_SEMANTICS_STATUS | DOCUMENTED_NOT_DYNAMIC_INVENTORY | steady Gaussian source/sink ledger; no air storage claim |
| RUNOFF_RAIN_HTO_BOUNDARY_STATUS | PASS | 0.6/5.4 Bq m-2 infiltration/runoff audit counterexample tested |
| CALM_WIND_STATUS | PASS | minimum-effective, skip, and error modes; substitution diagnostics |
| GAUSSIAN_DEPLETION_STATUS | PASS_DRY_PROJECT_SIMPLIFICATION | segment-exponential source depletion and monotonic/convergence tests |
| WET_SCAVENGING_STATUS | EXPLICITLY_NOT_IMPLEMENTED | interface disabled in formal baseline |
| FEEDBACK_DELAY_CONTRACT | FROZEN_3600S | 600/300 s tests preserve one-hour delay |
| ROOT_FRACTION_CONTRACT | FROZEN_SINGLE_LAYER_1_0 | single-layer closure, not manual multi-layer 20% |
| EQ40_SHADING_CONTRACT | FROZEN_RADIATION_TERM_ONLY | aerodynamic term unshaded; legacy mode optional |
| FEEDBACK_AREA_CONTRACT | PASS | rectangle is authoritative; inconsistent area rejected |
| REEMISSION_STATUS | BASIC_PASS_ADVANCED_PROVISIONAL | REEM/DIFF/ZT remains an engineering reconstruction |
| ACCEPTANCE_RECOMPUTE_STATUS | PASS | five cases recomputed in temporary output without overwriting saved artifacts |
| PROVENANCE_STATUS | PASS | HEAD/worktree, hashes, runtime, dependencies, modes, and timestamps recorded |
| TEST_STATUS | PASS | 61 passed; one known NetCDF binary-compatibility warning |
| TIMESTEP_STATUS | PASS | 600/300 s: soil 0.02360%, TFWT 0.13859%, OBT 0.12093%, integrated re-emission 0.04974% |

Next command:

```bash
.venv/bin/python scripts/verify_acceptance.py --recompute
```

## Historical environmental pathways V2 status

Development branch: `codex/ufotri-environmental-pathways-v2`

```text
V2_SCOPE_STATUS = FROZEN
MANUAL_EQUATION_INVENTORY_STATUS = COMPLETE_FOR_AVAILABLE_MANUAL
V2_IMPLEMENTATION_STAGE = STAGE_14_COMPLETE
WET_SCAVENGING_STATUS = PASS_PROJECT_PARAMETERIZATION
WET_DEPOSITION_LEDGER_STATUS = PASS
LEAF_AIR_EXCHANGE_STATUS = PASS_MANUAL_DERIVED_PROVISIONAL
BASIC_REEMISSION_STATUS = PASS
ADVANCED_REEMISSION_STATUS = PROVISIONAL_VALIDATED
CROP_PARAMETERIZATION_STATUS = PASS_PROJECT_EXTENSION
PHENOLOGY_STATUS = PASS
EDIBLE_PLANT_STATUS = PASS_PROJECT_EXTENSION
PLANT_INTERNAL_MASS_BALANCE_STATUS = PASS
FOOD_CHAIN_STATUS = PASS_MINIMAL_PATHWAYS
ECOLOGICAL_BOX_CLOSURE_STATUS = PASS
DOSE_MODULE_STATUS = PASS_RESEARCH_SCREENING
PATHWAY_DECOMPOSITION_STATUS = PASS
SINGLE_LAYER_STATUS = PASS_UNCHANGED
THREE_BOX_SOIL_STATUS = PASS_EXPERIMENTAL_STANDALONE
UNCERTAINTY_STATUS = PASS_REPRODUCIBLE
SENSITIVITY_STATUS = PASS
HISTORICAL_BENCHMARK_STATUS = PASS_AVAILABLE_REFERENCE_CASES
PHYSICAL_INVARIANTS_STATUS = PASS
V2_END_TO_END_CASES_STATUS = PASS
V2_ACCEPTANCE_RECOMPUTE_STATUS = PASS
V2_AUDIT_STATUS = ACCEPT_WITH_REMAINING_LIMITATIONS
HISTORICAL_V2_COMPLETE_RECOMMENDATION = FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE
V2_TEST_STATUS = PASS_95
V2_COMPILE_STATUS = PASS
V2_DIFF_CHECK_STATUS = PASS
```

The frozen scope, manual inventory, code mapping, architecture, assumptions,
and validation strategy are in `docs/v2/`. Stage 1 adds three wet-scavenging
modes, competing dry/wet source depletion, and a conservative surface
wet-deposition footprint ledger. The default remains `off`, preserving V1.
The power-law values are explicitly provisional. Stage 2 adds a single signed,
conservative leaf-air exchange using aerodynamic, boundary, and LAI/VPD/day-
night canopy resistance. Its default remains `off` for V1. Planned later
functions are not represented as V1 functionality.

Stage 3 centralizes Eq. (44) calibration at the manual's 20% reference
condition and verifies 10% h-1 radiative plus 1% h-1 diffusive initial rates,
day/night logic, ABFLR, HTO-only C2=1, and ZT decay. Missing manual calibration
detail prevents promotion beyond `PROVISIONAL_VALIDATED`.

Stage 4 adds YAML parameter sets for grass, leafy and root vegetables, cereal,
pasture, and a generic crop. Constant, piecewise-stage, smooth-seasonal, and
external LAI modes share one LAI value across Eq. (40) shading, transpiration,
and leaf exchange. Outside the configured season LAI and associated exchange
are zero. Crop values are `PROJECT_EXTENSION`, not site-specific claims.

Perennial pasture now uses an explicit dormant-season mode rather than the
legacy start-equals-harvest special case. It retains a configurable non-zero
dormant LAI, supports multiple partial cuts, preserves remaining inventories
across year boundaries, and records edible-harvest and removed whole-plant
activity as separate boundaries. A formal two-year case passes six unique cut
events, second-year regrowth, non-negativity, and closure checks.

Stage 5 adds distinct vegetative/whole-plant source pools and edible TFWT/OBT
inventories, internal allocation, growth dilution, decay, harvest, crop reset,
and explicit water/fresh/dry concentration conversions. Harvested HTO and OBT
are cumulative boundary outputs; internal allocation closes at machine
precision.

Stage 6 adds explicit leafy, root, grain, and pasture food concentrations plus
a configurable minimal cow body-water/body-OBT model with feed, drinking water,
formation/turnover, milk, excretion, beef, and slaughter boundaries. Feed
activity is removed from the edible pasture inventory and enters the animal
inventory once; the combined ecological residual is tested.

Stage 7 adds adult, child, and infant HTO/OBT public dose calculations with
separate inhalation, skin, water, plant, milk, and meat diagnostics. Dose
coefficients, habits, source, and version are configuration data. Results are
cumulative by time at the configured spatial receptor and remain explicitly
research-screening outputs.

Stage 8 adds a tested conservative three-box soil API with layer water,
advective HTO, optional diffusion, layer roots, surface-only evaporation, and
deep leakage. It is explicitly experimental and standalone; selecting it in
the formal short-case coupler returns a clear error rather than silently using
the single-layer implementation. RC1 does not promote it; the deferred coupling
interfaces and required calibration/convergence evidence are recorded in
`docs/v2/multibox_integration_roadmap.md`.

Stage 9 adds mode-aware Monte Carlo and Latin Hypercube sampling, median,
5/95-percentile, mean and standard deviation summaries, parameter-output
Spearman correlations, one-at-a-time finite-difference sensitivities, and
normalized pathway contributions. Disabled parameters are recorded as
`inactive_by_mode` instead of zero sensitivity. The real full-dose audit runs
LHS n=64/128/256 with a primary seed and three additional seeds, establishes
n=256 as the formal minimum, and records stable quantiles plus
`LIMITED_WITH_EVIDENCE` for the weak-parameter rank ordering. Parameter
distributions are centralized in YAML as project-level uncertainty assumptions.

Stage 10 provides a recomputable benchmark suite with ten independent analytic
checks, five UFOTRI-manual numeric anchors, two literature coefficient
comparisons, and the original fifteen executable scenarios/invariants. Evidence
is explicitly classified as `analytic_benchmark`, `manual_anchor`,
`literature_comparison`, `physical_invariant`, `integration_scenario`, or
`regression_case`; execution cases are not represented as numeric references.
The analytic set covers exponential wet removal, competing dry/wet allocation,
leaf equilibrium, re-emission, animal production, dose arithmetic, and food
mass/water conversion.

Stage 11 provides five named end-to-end configurations, pathway figures,
results, hashes, runtime provenance, and LHS/OAT artifacts. All were recomputed
in a temporary directory. The 72 h weather record transparently combines the
available 48 h ERA5 input with a 24 h deterministic extension; this limitation
is recorded in every relevant provenance file.

Stage 12 provides one recomputable V2 acceptance command covering frozen V1
regression, wet/leaf/food/dose pathways, fixed-seed LHS, the full categorized
benchmark suite, all end-to-end configurations, required figures, and
provenance hashes.

The historical Stage 13 assessment below is superseded for current-branch
status by the independent audit and this RC1 remediation record. Stage 13
records the earlier formal assessment in
`docs/v2/formal_ufotri_environmental_pathways_v2_assessment.md`. Its verdict is
`ACCEPT_WITH_REMAINING_LIMITATIONS`, and its recommendation is limited to
`FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE`.

Stage 14 passed 95 tests, frozen V1 recomputation, complete V2 recomputation,
Python byte-compilation, and the Git whitespace-error check. One known
NumPy/NetCDF binary-compatibility runtime warning remains in the ERA5 reader
test.

Final V2 acceptance command:

```bash
.venv/bin/python scripts/verify_v2_acceptance.py --recompute
```

## RC2 directed physics remediation

RC2 removes the unequal dry/wet footprint accounting assumption. Dry and wet
local fluxes retain independent `area_m2` values; their authoritative
activities are combined explicitly only after \(M_d=F_dA_d\) and
\(M_w=F_wA_w\) are recorded. The ecological box uses a separate configured
reference area. Combined cases with \(A_w/A_d=0.1,1,10\) close the global Bq
inventory/boundary/decay ledger below \(10^{-12}\), while local flux retains
inverse-area scaling.

UFOTRI Eq. (27) now uses saturated water-vapour density
`rho_v_sat`. Relative humidity remains in VPD-dependent canopy resistance but
does not scale the equilibrium air concentration. Direct tests at 293.15 K and
RH 30/60/90% give the same equilibrium value, and the formal leaf path reaches
HTO flux, TFWT, OBT, food, and dose with surface closure below \(10^{-12}\).

The leaf fixed-meteorology benchmark now obtains its expected conductance,
Eq. (27) factor, and first-order solution from handwritten equations without
using the exchange module. The suite requires at least ten analytic records
and `independent=true` for every analytic benchmark.

Perennial plant output now exposes root/shoot TFWT and OBT inventories. The
provisional root activity fraction is configuration data; partial cuts remove
shoot activity only. Wrap-around phenology uses the actual 365- or 366-day
calendar. Root retention, year crossing, leap/non-leap progression, six
two-year cuts, regrowth LAI, and conservation are tested.

## V2 external validation phase 1 - complete forcing

The validation-readiness infrastructure was fast-forwarded to `main` at
`f0cad0ab4e76e83c7e830f82bbe9329828c521f9` and pushed to `origin/main`.
The V2 candidate and V1 tags remain at
`f097115cbfc052baa18f1e49a1207fa6b3523cff` and
`6918440faa3455b848f43589784672f3bfabfe3d`, respectively.

The formerly missing 24 ERA5 hours were retrieved from the same CDS time-series
product and point. A read-only preparation workflow now yields 72 consecutive
external reanalysis rows with zero interpolated, repeated, extended, or missing
hours. The forcing comparison ran successfully. Wet and dry deposition were
unchanged because the one-hour release is within the shared first 48 h; final
soil HTO changed by -5.668%, TFWT by +0.105%, and OBT by +3.198%. This is a
forcing sensitivity result, not site validation.

```text
VALIDATION_INFRASTRUCTURE_MERGED = PASS
FORCING_72H_STATUS = PASS_72_OF_72_OBSERVED
FORCING_EXTENSION_BIAS_STATUS = PASS_COMPARISON_EXECUTED_NOT_SITE_VALIDATION
```

## V2 external validation phase 1 - independent reference

Independent reference case 001 parses the same frozen case manifest without
importing formal model functions. It covers Gaussian concentration, competing
dry/wet depletion, surface allocation, one-box soil, fixed-conductance TFWT,
first-order OBT, and simple dose. All eight declared comparisons pass their
preregistered thresholds; normalized errors are between `1.37e-15` and
`2.49e-13`, and the independent activity residual is below `5.83e-10 Bq m-2`.
The case is intentionally bounded and is not experimental or field evidence.

```text
REFERENCE_MODEL_STATUS = PASS_INDEPENDENT_REFERENCE_CASE_001
```

## V2 external validation phase 1 - experiment and field search

The controlled-experiment and matched-field search is recorded in a
machine-readable inventory, a licence review, and two blocked requirement
manifests. The IAEA EMRAS soybean scenario is the closest leaf candidate, but
the retrieved public material does not include the organizer meteorology and
air workbooks, a chamber-mixing boundary condition, or a detection limit. No
complete co-located air-meteorology-soil-plant field package was obtained.

No publication table was repackaged, no different sites were spliced, and no
external case, calibration, or holdout validation was run. The registry records
the complete ERA5 reanalysis forcing and independent reference as `PASS`, while
the experiment and field cases remain explicitly blocked.

```text
EXPERIMENTAL_DATA_STATUS = BLOCKED_EXTERNAL_DATA
FIELD_DATA_STATUS = BLOCKED_EXTERNAL_DATA
EXTERNAL_CASES_EXECUTED_COUNT = 0
CALIBRATION_STATUS = NOT_RUN_BLOCKED_EXTERNAL_DATA
PARAMETER_IDENTIFIABILITY_STATUS = NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE
```

## V2 external evidence phase 1 - gate assessment

All 185 collected tests, the five frozen V1 cases, the six V2 end-to-end cases,
validation readiness, byte-compilation, and the Git whitespace check pass. The
candidate and V1 tags remain unchanged. The only runtime warning is the known
NumPy/NetCDF binary-compatibility warning in the ERA5 reader test.

Because no true external experiment or field case was executable, Phase 1 is
infrastructure-complete but externally blocked. V3 may proceed only to
architecture, interfaces, migration planning, and data models; no V3 model
code or formal physics was implemented.

```text
EXTERNAL_VALIDATION_PHASE1_STATUS = INFRASTRUCTURE_COMPLETE_EXTERNAL_EVIDENCE_BLOCKED
V3_GATE_VERDICT = READY_FOR_V3_ARCHITECTURE_ONLY_EXTERNAL_VALIDATION_CONTINUES
MERGE_EXTERNAL_VALIDATION_BRANCH_RECOMMENDATION = READY_FOR_MAINTAINER_REVIEW
```

## V3 H2/H3 slow-mechanism discriminability design

The independently reviewed SB4 benchmark was fast-forwarded to `main` at
`e10c0be1d1fac51eb99643ceac71708426c30dd3`. From that baseline, the
validation-only branch
`codex/v3-slow-mechanism-discriminability-design` froze its protocol before
synthetic execution. H2 and H3 retain the SB1 parameters from
`4b79f62741db4d4b51f4d608df33d2e13c499636`; the parameter-refit count is
zero.

Existing SB1 and SB4 output distances remain insufficient to select H2 or H3.
Six controlled exposure designs were screened with both models as Monte Carlo
truth, 1,000 replicates per design/truth/noise cell, and CV 10/20/30%.
D3, a 24 h low-concentration step followed by samples at 0.2, 48, and 120 h,
is the only screened design that passes every preregistered concentration, RH,
wind, stomatal-resistance, bidirectional classification, strong-separation,
finite/nonnegative, and conservation check. This is an experiment-design
result only, not empirical validation or model selection.

```text
SB1_EXISTING_DATA_DISCRIMINABILITY = INSUFFICIENT_TO_SELECT_H2_OR_H3
SB4_EXISTING_DATA_DISCRIMINABILITY = INSUFFICIENT_TO_SELECT_H2_OR_H3
BEST_DISCRIMINATING_DESIGN = D3_SHORT_STEP_24H
PARAMETER_REFIT_COUNT = 0
SYNTHETIC_DESIGN_STATUS = DESIGN_ONLY
EXPERIMENT_SPECIFICATION = READY_FOR_EXTERNAL_DATA_SEARCH_OR_NEW_EXPERIMENT
FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## V3 integration review and P7.7 validation preparation

The independent `codex/v3-integration-review` branch was created from
`origin/main` and sequentially integrated P7.5, P7.5B, P7.6A, P7.6B-1,
P7.6B-2A, P7.6B-2B, P7.6C-1, and P7.6C-2. The review uses new integration
commits and does not merge `origin/main`. The final tree is unchanged from
the P7.6C-2 source tree before the review report was added, so this phase
introduced no physics-module, numerical-coupling, or solver changes.

```text
V3_INTEGRATION_REVIEW = PASS
CODE_CONFLICTS = 0
NEW_TEST_FAILURES = 0
PHYSICS_MODULE_CHANGES = 0
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
CALIBRATION = NOT_STARTED
REAL_ATMOS_INPUT = FALSE
V3_PHYSICS_READY = FALSE
```

The requested unit, integration, architecture, and regression scopes pass
with `PYTHONPATH=.`. The only test-suite warning is the existing NumPy/NetCDF
binary-compatibility warning in the ERA5 reader test. The full integration
review is recorded in
`docs/v3/reports/v3_integration_readiness_review.md`. The next stage is
preparation-only and is defined in
`docs/v3/physics/p7_7_physics_validation_preparation.md`; it does not start
calibration or activate any parameter.

## V3 P7.6C-3 UFOTRI validation-feasibility assessment

P7.6C-3 evaluates every P7.6C-2 UFOTRI semantic mapping record without
searching for or importing a parameter value. The decision matrix separates
future validation pathways from V3 equation gaps, external exposure/dose
inputs, and unrecovered source definitions. The derived leaf conductance is
reviewed separately from its three resistance components.

```text
P7_6C3_STATUS = PASS_VALIDATION_FEASIBILITY_ASSESSMENT
ALL_PARAMETERS_ASSESSED = TRUE
MAPPED_PARAMETERS_ASSESSED = 26
DERIVED_REVIEW_ITEMS = 1
VALIDATION_FEASIBLE = 4
VALIDATION_FEASIBLE_WITH_LIMITATIONS = 8
PHYSICS_REDESIGN_REQUIRED = 9
NOT_IMPORTABLE = 4
INSUFFICIENT_INFORMATION = 1
NEW_VALIDATION_CANDIDATES = 0
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
PHYSICS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
CALIBRATION_STARTED = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The typed control plane is
`src/cteas_ufotri/parameters_v3/validation_feasibility.py`; its canonical
matrix is `docs/v3/parameter_evidence/parameter_validation_feasibility.yaml`.
ADR-015 freezes the five states and the fail-closed validation gate. Reports
are `v3_p7_6c3_validation_feasibility_report.md`,
`v3_p7_6c3_physics_gap_analysis.md`,
`v3_p7_6c3_parameter_decision_matrix.md`, and
`v3_p7_6c3_independent_review.md`. No solver, equation, numerical coupling,
runtime parameter lookup, calibration, or active database was added.

## V3 P7.6D physics adoption decision and redesign roadmap

P7.6D converts the P7.6C-3 feasibility assessment into an explicit model
adoption decision. All 26 mapped records and the derived `leaf.g_ex` review
item are covered exactly once. The current V3 model remains frozen; nine
records require a future physics redesign, while metadata, exposure, and dose
records remain outside the UFOTRI environmental-physics path.

```text
P7_6D_STATUS = PASS_PHYSICS_ADOPTION_DECISION
ALL_FEASIBILITY_ITEMS_REVIEWED = TRUE
CURRENT_V3_MODEL = FROZEN
REDESIGN_ITEMS_IDENTIFIED = TRUE
IMPLEMENTATION_STARTED = FALSE
NEW_VALIDATION_CANDIDATES = 0
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
PHYSICS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
V3_PHYSICS_READY = FALSE
```

Adoption counts are `KEEP_CURRENT_V3=2`, `VALIDATE_CURRENT_MODEL=9`,
`EXTEND_V3_PHYSICS=2`, `REDESIGN_REQUIRED=9`, `DO_NOT_IMPORT=4`, and
`WAIT_FOR_EVIDENCE=1`. The canonical registry and priority matrix are
`docs/v3/physics/p7_6d_physics_adoption_decision.yaml` and
`docs/v3/physics/p7_6d_redesign_priority_matrix.yaml`. The policy is frozen in
`docs/v3/adr/ADR-016-v3-physics-adoption-and-redesign-policy.md`; reports are
`v3_p7_6d_physics_adoption_report.md`,
`v3_p7_6d_redesign_roadmap.md`,
`v3_p7_6d_coupling_impact_report.md`, and
`v3_p7_6d_independent_review.md`.

The P7.6D control-plane loader and focused unit/architecture tests pass. No
solver, equation, P7.5/P7.5B pipeline, numerical coupling, parameter value,
calibration routine, runtime lookup, or active database was added.

## V3 P7.8A physics redesign prioritization and planning

P7.8A converts the P7.6C-3 feasibility findings and P7.6D adoption decisions
into a ranked, evidence-gated physics roadmap. The current V3 model remains
frozen. The registry covers all nine P7.6D `REDESIGN_REQUIRED` records,
separates two deferred water/hydrology extensions, and permanently rejects
four shortcuts or scope expansions. The coupling matrix classifies every
governed item as `NO_IMPACT`, `INTERFACE_CHANGE_ONLY`,
`PIPELINE_CHANGE_REQUIRED`, or
`NUMERICAL_COUPLING_REDESIGN_REQUIRED` without reopening P7.5/P7.5B.

```text
P7_8A_STATUS = PASS_PHYSICS_REDESIGN_PRIORITIZATION
REDESIGN_ITEMS_REVIEWED = TRUE
PRIORITY_MATRIX_COMPLETE = TRUE
ROADMAP_DEFINED = TRUE
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The primary outputs are
`docs/v3/physics/p7_8a_redesign_priority_registry.yaml`,
`docs/v3/physics/p7_8a_coupling_impact_matrix.yaml`,
`docs/v3/reports/v3_p7_8a_redesign_prioritization_report.md`,
`docs/v3/reports/v3_p7_8a_physics_evolution_roadmap.md`,
`docs/v3/reports/v3_p7_8a_coupling_impact_report.md`,
`docs/v3/reports/v3_p7_8a_independent_review.md`, and
`docs/v3/adr/ADR-019-v3-physics-redesign-governance.md`.

The P7.8A governance test validates registry completeness, subsystem review,
priority states, coupling coverage, direct-activation rejection, required
artifacts, and runtime isolation. The compatibility command completed with
`32 passed`; `git diff --check` passed. No plant, soil, exposure, coupling,
pipeline, or parameter-runtime source was changed.

## V3 P7.8B-1 physics redesign specification

P7.8B-1 converts the P7.8A redesign priorities into candidate scientific
specifications without implementing them. The specification registry covers
the nine redesign records and two deferred extensions, including current
equations, equation gaps, candidate formulations, state variables, symbolic
parameters, interface changes, validation data, coupling impact, backward
compatibility, and migration strategy.

```text
P7_8B1_STATUS = PASS_REDESIGN_SPECIFICATION
HIGH_PRIORITY_ITEMS_SPECIFIED = TRUE
EQUATION_GAPS_DOCUMENTED = TRUE
VALIDATION_REQUIREMENTS_DEFINED = TRUE
COUPLING_IMPACTS_DEFINED = TRUE
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
NUMERICAL_COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The primary outputs are
`docs/v3/physics/p7_8b1_redesign_specification.yaml`,
`docs/v3/reports/v3_p7_8b1_redesign_specification_report.md`,
`docs/v3/reports/v3_p7_8b1_equation_gap_analysis.md`,
`docs/v3/reports/v3_p7_8b1_coupling_impact_report.md`,
`docs/v3/reports/v3_p7_8b1_independent_review.md`, and
`docs/v3/adr/ADR-020-v3-redesign-specification-policy.md`.

The current `v3_frozen_baseline` remains runnable and unchanged. Candidate
equations and parameters are control-plane-only, value-free, and not runtime
admissible. Root, layered soil, and food event/continuous candidates are
explicit `NUMERICAL_COUPLING_CHANGE` designs; OBT/leaf candidates are
interface extensions; TFWT dynamic water turnover is a pipeline change.

The P7.8B-1 specification test validates schema completeness, candidate
options, dimensional markers, conservation-boundary markers, activation
governance, baseline compatibility, required artifacts, and runtime
isolation. The focused suite completed with `12 passed`; `git diff --check`
passed. No production source was changed.

## V3 P7.8B-2 physics selection and architecture decision

P7.8B-2 selects the future physics direction after the P7.8A prioritization
and P7.8B-1 specification review. V3.1 is limited to a typed plant/product
mass-basis contract. V4 selects the OBT precursor and exchangeable/non-
exchangeable pool direction, dynamic stomatal response at the existing leaf
resistance boundary, and water-flux-coupled layered root uptake. The current
one-layer soil signed-transport interface, fixed TFWT storage, food harvest
event, external consumption, and external dose layers remain unchanged.

```text
P7_8B2_STATUS = PASS_PHYSICS_SELECTION
FINAL_MODEL_CHOICES_DEFINED = TRUE
V3_1_ROADMAP_DEFINED = TRUE
V4_ITEMS_DEFINED = TRUE
VALIDATION_DEPENDENCY_DEFINED = TRUE
IMPLEMENTATION_ORDER_FROZEN = TRUE
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The primary outputs are
`docs/v3/physics/p7_8b2_physics_selection.yaml`,
`docs/v3/physics/p7_8b2_architecture_roadmap.yaml`,
`docs/v3/physics/p7_8b2_coupling_decision.yaml`,
`docs/v3/physics/p7_8b2_validation_dependency.yaml`,
`docs/v3/reports/v3_p7_8b2_physics_selection_report.md`,
`docs/v3/reports/v3_p7_8b2_architecture_roadmap.md`,
`docs/v3/reports/v3_p7_8b2_validation_dependency_report.md`,
`docs/v3/reports/v3_p7_8b2_independent_review.md`, and
`docs/v3/adr/ADR-021-v3-physics-selection-policy.md`.

The registry remains control-plane-only. Selected equations are not
implemented, candidate parameters have no values, no calibration is started,
and the root candidate is explicitly gated by a future P7.5/P7.5B numerical-
coupling review. Soil hydrology, TFWT water turnover, and continuous/hybrid
food transfer remain `INSUFFICIENT_EVIDENCE`; unreviewed values, guessed
conversions, continuous-only food transfer, and dose-driven environmental
redesign remain rejected.
