# Formal UFOTRI environmental pathways V2 assessment

Assessment date: 2026-07-24

## Current RC2 candidate disposition

```text
V2_STATUS = FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE
CURRENT_RELEASE_BASIS = RC2_INDEPENDENT_REAUDIT_ACCEPTED_WITH_MINOR_CORRECTIONS
BLOCKER_COUNT = 0
HIGH_COUNT = 0
SITE_CALIBRATED = NO
REGULATORY_VALIDATED = NO
COMPLETE_UFOTRI_EQUIVALENCE = NO
```

The RC2 independent re-audit confirmed unequal-footprint global conservation,
UFOTRI Eq. (27) saturated-vapour equilibrium, ten independent analytic
benchmarks, root-retaining cuts, and actual 365/366-day calendars. Release
finalization adds explicit named provenance and current-status metadata without
changing model physics. The authoritative audit sequence is
`docs/v2/v2_audit_history.md`.

## Previous RC1 status notice

This file records the pre-independent-audit V2 assessment. Its historical
verdict is retained below, but it is not the current branch disposition. The
independent audit rejected commit
`0075708b35baeb6f8b3b5574d5b735316d959097`; the remediation branch has
implemented bounded corrections and now awaits a new independent audit.

```text
V2_STATUS = PHYSICS_REMEDIATION_RC1_CANDIDATE
FORMAL_ACCEPTANCE = PENDING_INDEPENDENT_REAUDIT
```

## Historical verdict

`ACCEPT_WITH_REMAINING_LIMITATIONS`

The repository supports a reproducible
`FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE` for an HTO
atmosphere-soil-plant-food-pathway research model. The recommendation is
strictly limited to that candidate scope.

This verdict does not claim a complete line-by-line UFOTRI implementation,
regulatory acceptance, field validation, HT chemistry, or dynamic
three-dimensional atmospheric mass conservation. The immutable
`formal-minimal-baseline-v1` remains the compatibility baseline.

## Historical subsystem assessment

| Subsystem | Assessment | Evidence / limitation |
|---|---|---|
| V1 regression | `PASS` | all five frozen V1 acceptance cases recompute |
| Wet scavenging | `PASS_PROJECT_PARAMETERIZATION` | off, constant, and power-law modes; power-law coefficients remain provisional |
| Wet deposition | `PASS` | source removal and surface input use one conservative ledger |
| Leaf-air exchange | `PASS_MANUAL_DERIVED_PROVISIONAL` | one signed bidirectional flux; resistance parameterization is not field validated |
| Advanced re-emission | `PROVISIONAL_VALIDATED` | manual reference-rate and day/night checks pass; empirical detail remains incomplete |
| Crop phenology | `PASS_PROJECT_EXTENSION` | configurable crop categories and four LAI modes |
| Edible plant | `PASS_PROJECT_EXTENSION` | distinct TFWT/OBT inventories, allocation, dilution, decay, and harvest boundaries |
| Food chain | `PASS_MINIMAL_PATHWAYS` | plant, pasture, milk, and beef paths close without double counting feed |
| Public dose | `PASS_RESEARCH_SCREENING` | HTO/OBT pathway decomposition for adult, child, and infant; not regulatory dosimetry |
| Single-layer soil | `PASS_UNCHANGED` | formal V1 0-5 cm box remains the coupled default |
| Multi-box soil | `PASS_EXPERIMENTAL_STANDALONE` | conservative three-box API; not integrated into the formal short-case coupler |
| Uncertainty | `PASS_REPRODUCIBLE` | fixed-seed MC/LHS, percentiles, Spearman, and OAT |
| Ecological mass balance | `PASS` | tested soil, plant, edible, harvested, animal, milk, excretion, and slaughter boundaries |
| Benchmarks | `PASS_CATEGORIZED_EVIDENCE` | ten analytic benchmarks, five manual anchors, two literature comparisons, and fifteen executable scenarios/invariants |
| V2 recompute | `PASS` | five end-to-end cases, benchmarks, invariants, artifacts, hashes, and provenance recomputed |

## Recomputed evidence

The acceptance driver recomputes the frozen V1 cases, wet/leaf/food/dose
pathways, fixed-seed LHS, the categorized benchmark suite, and all five end-to-end
configurations in a temporary directory. Each end-to-end case writes
`results.csv`, eight pathway/diagnostic figures, and provenance containing
configuration, input and output hashes, Git/worktree state, runtime versions,
modes, and timestamps.

The 2026-07-24 recomputation produced 432 steps for the 72 h case and 336
steps for each 14 d case. Maximum surface-box relative residuals were no larger
than 6.04e-16. Wet removal, plant OBT, crop dose, milk concentration, and full
adult dose were non-zero in their intended pathway cases.

The final repository test run passed 95 tests with no failures. One known
NumPy/NetCDF binary-compatibility runtime warning remains in the ERA5 reader
test. Source, tests, ERA5 utilities, and scripts also passed `compileall`, and
`git diff --check` reported no whitespace errors.

## Remaining limitations

- Advanced re-emission omits the manual rain-start 3% rule and
  concentration-dependent DIFF detail.
- The three-box soil solver is experimental standalone and is not formally
  coupled.
- The 72 h wet case is 48 h ERA5 plus a deterministic dry 24 h extension.
- Continuous and accident release durations remain scenario assumptions.
- Crop, hydrology, footprint, animal, and intake values remain replaceable
  research-screening parameters.
- The chemistry is HTO-only; HT oxidation and HT-specific soil processes are
  excluded.
- This is not full UFOTRI, a regulatory model, or a field-validated site model.
- Wet power-law coefficients and the uniform deposition-footprint allocation
  are provisional project parameterizations.
- Leaf resistance and bidirectional exchange parameters are provisional and
  lack crop/site calibration.
- Crop properties, phenology, food-chain transfer parameters, and consumption
  habits are replaceable project assumptions rather than site claims.
- The three-box soil solver is experimental and standalone; the formal coupled
  cases retain the single-layer soil.
- Only 48 h of matching ERA5 are present. The 72 h case transparently appends
  a configured 24 h deterministic extension and does not claim 72 h of ERA5.
- The atmosphere uses a steady Gaussian source/sink ledger, not a dynamic
  atmospheric inventory or three-dimensional conservation solver.

## Historical final fields

```text
V2_VERDICT = ACCEPT_WITH_REMAINING_LIMITATIONS
V1_REGRESSION_STATUS = PASS
WET_SCAVENGING_STATUS = PASS_PROJECT_PARAMETERIZATION
WET_DEPOSITION_STATUS = PASS
LEAF_AIR_EXCHANGE_STATUS = PASS_MANUAL_DERIVED_PROVISIONAL
ADVANCED_REEMISSION_STATUS = PROVISIONAL_VALIDATED
CROP_PHENOLOGY_STATUS = PASS_PROJECT_EXTENSION
EDIBLE_PLANT_STATUS = PASS_PROJECT_EXTENSION
FOOD_CHAIN_STATUS = PASS_MINIMAL_PATHWAYS
DOSE_MODULE_STATUS = PASS_RESEARCH_SCREENING
SINGLE_LAYER_SOIL_STATUS = PASS_UNCHANGED
MULTIBOX_SOIL_STATUS = PASS_EXPERIMENTAL_STANDALONE
UNCERTAINTY_STATUS = PASS_REPRODUCIBLE
ECOLOGICAL_MASS_BALANCE_STATUS = PASS
HISTORICAL_BENCHMARK_STATUS = PASS_AVAILABLE_REFERENCE_CASES
V2_RECOMPUTE_STATUS = PASS
TEST_STATUS = PASS_95
HISTORICAL_V2_COMPLETE_RECOMMENDATION = FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE
```

## RC1 remediation disposition

The current branch uses one dry/wet activity ledger, meteorology-responsive
leaf resistance, a formal leaf-to-food/dose case, a conservative beef product
boundary, named/bracketed wet parameters, independent analytic/manual
benchmarks, mode-aware n=64/128/256 full-model LHS, and two-year perennial
pasture evidence. Advanced manual re-emission fidelity, site calibration,
uniform footprint uncertainty, the deterministic 24 h weather extension, and
formal three-box coupling remain limitations.

This remediation is a self-assessed candidate for re-audit only. It does not
reinstate the historical recommendation above.

## Current candidate fields

```text
CURRENT_V2_STATUS = FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE
CURRENT_PHYSICS_ACCEPTANCE = ACCEPT_RC2_WITH_MINOR_CORRECTIONS
PROVENANCE_STATUS = NAMED_FIELDS_AND_HASHED_EFFECTIVE_CONFIG
ANIMAL_STATE_NAMING_STATUS = DOCUMENTED_COMPATIBILITY_LIMITATION
MEDIUM_LIMITATION_COUNT = 5
FORMAL_MODEL_CLAIM = RESEARCH_CANDIDATE_NOT_SITE_OR_REGULATORY_VALIDATED
```
