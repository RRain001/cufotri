# Implementation status

Updated: 2026-07-24

## V2 physics remediation RC1 progress

Development branch: `codex/v2-physics-remediation-rc1`

```text
V2_STATUS = PHYSICS_REMEDIATION_RC1_IN_PROGRESS
FORMAL_ACCEPTANCE = PENDING_INDEPENDENT_REAUDIT
RC1_STAGE_1 = PASS
RC1_STAGE_2 = PASS
RC1_STAGE_3 = PASS
RC1_STAGE_4 = PASS
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
RC1_TEST_STATUS = PASS_136
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

## Environmental pathways V2

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
BENCHMARK_STATUS = PASS_AVAILABLE_REFERENCE_CASES
PHYSICAL_INVARIANTS_STATUS = PASS
V2_END_TO_END_CASES_STATUS = PASS
V2_ACCEPTANCE_RECOMPUTE_STATUS = PASS
V2_AUDIT_STATUS = ACCEPT_WITH_REMAINING_LIMITATIONS
V2_COMPLETE_RECOMMENDATION = FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE
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
the single-layer implementation.

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

Stage 13 records the formal audit in
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
