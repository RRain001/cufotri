# Implementation status

Updated: 2026-07-25

## V3 architecture-only baseline

Branch: `codex/v3-architecture-only`

Base: `main` at `f02636f10e900174226edc2659f20a2fdb15d3ce`

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

## Current formal status

```text
CURRENT_FORMAL_STATUS =
FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE

CURRENT_RELEASE_BASIS =
RC2_INDEPENDENT_REAUDIT_ACCEPTED_WITH_MINOR_CORRECTIONS

CURRENT_BRANCH =
codex/v2-physics-remediation-rc2

CURRENT_SOURCE_HEAD =
CANDIDATE_FINALIZATION_COMMIT_RECORDED_IN_RELEASE_REPORT_AND_TAG

V1_BASELINE =
6918440faa3455b848f43589784672f3bfabfe3d

V1_TAG =
formal-minimal-baseline-v1

TEST_STATUS =
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

VALIDATION_BRANCH =
codex/v2-validation-readiness

EMPIRICAL_VALIDATION_STATUS =
BLOCKED_EXTERNAL_DATA

VALIDATION_TEST_STATUS =
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
