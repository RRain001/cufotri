# UFOTRI environmental pathways V2 validation master plan

## Status and claim boundary

```text
PLAN_STATUS = VALIDATION_INFRASTRUCTURE_READY_FOR_EVIDENCE
MODEL_CLAIM = RESEARCH_CANDIDATE_NOT_SITE_OR_REGULATORY_VALIDATED
CHEMISTRY_SCOPE = HTO_ONLY
ATMOSPHERE_SCOPE = STEADY_GAUSSIAN_NO_DYNAMIC_AIR_INVENTORY
```

`READY` means the comparison can be executed with evidence already in the
repository. `BLOCKED_EXTERNAL_DATA` means the interface and acceptance
criterion exist but the independent dataset is absent. Internal regression,
integration and invariant evidence is never counted as external validation.

## Validation matrix

| Domain | Validation question | Reference source | Input requirements | Comparison observable | Unit | Time scale | Acceptance metric | Acceptance threshold | Current evidence | Missing evidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. Gaussian air and deposition | Are plume concentration and competing dry/wet losses numerically and dimensionally correct? | analytic Gaussian and depletion solutions; independent reference model later | stack geometry, stability, wind, receptor, deposition velocity | air HTO, dry/wet activity loss | Bq m-3; Bq s-1 | step to 72 h | relative error; activity residual | analytic <=1e-6; residual <=1e-10 | analytic dry/wet boxes and unequal-footprint ledgers | independent Gaussian code comparison and observations | PARTIAL |
| 2. Wet scavenging | Does precipitation-dependent removal reproduce the declared power law without false calibration claims? | analytic power law; literature numeric brackets | hourly precipitation with status, wind, source | scavenging coefficient and wet activity | s-1; Bq | event/72 h | relative error; cumulative activity error | analytic <=1e-10; cumulative <=5% when external data exist | analytic wet removal and 12-case bracket grid | full observed 72 h case and site precipitation/deposition data | PARTIAL |
| 3. Bidirectional leaf HTO | Are Eq. (27), VPD resistance and exchange direction correct? | UFOTRI manual anchors and analytic box | temperature, RH, air HTO, plant water HTO, LAI, wind | equilibrium concentration, resistance, flux, TFWT | Bq m-3; s m-1; Bq m-2 s-1; Bq m-2 | seconds to 72 h | relative error; RMSE | analytic <=5e-5; external threshold preregistered per dataset | 24-point Eq. (27), analytic leaf box, on/off end-to-end | chamber or field exchange dataset | PARTIAL |
| 4. Soil HTO | Does the top-layer water/activity ledger conserve activity under infiltration, uptake, runoff and decay? | analytic ledger and controlled soil experiment later | soil water, rain HTO, fluxes, deposition | soil water and HTO inventory | m; Bq m-2 | step to seasonal | mass-balance residual; RMSE | residual <=1e-10 relative; experiment threshold preregistered | zero/very-dry/saturated invariant cases | time-resolved controlled experiment | PARTIAL |
| 5. Re-emission | Are radiative, diffusive, evapotranspiration and rain-start terms faithful to the manual? | UFOTRI manual and future chamber/field data | surface inventories, radiation, ET, rain-start, concentrations | re-emission rate and cumulative loss | Bq m-2 s-1; Bq m-2 | hourly to 14 d | relative error; cumulative activity error | manual anchors <=1e-10; external threshold preregistered | 5 manual anchors; present advanced-mode integration | complete rain-start 3% and concentration-dependent DIFF mapping; observations | PARTIAL |
| 6. TFWT | Does uptake, exchange, turnover and root/shoot partition reproduce water-bound HTO dynamics? | analytic compartment solution; plant experiment later | air/soil HTO, transpiration, leaf conductance, biomass | root, shoot and total TFWT | Bq m-2 | hours to season | RMSE; peak ratio; time-to-peak | analytic <=5e-5; experiment thresholds preregistered | analytic leaf box and conserved root/shoot ledger | controlled exposure/depuration time series | PARTIAL |
| 7. OBT | Does formation/turnover conserve activity and reproduce expected time scale? | analytic first-order box; literature numeric anchors | TFWT, light state, formation and turnover constants | plant/edible OBT | Bq m-2; Bq kg-1 dry | days to season | relative error; RMSE | analytic <=1e-6; external threshold preregistered | analytic conversion boxes and end-to-end propagation | crop-specific formation/turnover observations | PARTIAL |
| 8. Crop and edible material | Are phenology, harvest boundaries and fresh/dry conversions correct? | analytic conversions; crop experiment/site data later | calendar, LAI, biomass, water fraction, harvest schedule | edible TFWT/OBT and harvest boundary | Bq m-2; Bq kg-1 fresh/dry | season/multi-year | mass balance; bias; RMSE | balance <=1e-10; external thresholds preregistered | annual/perennial calendar, conversion and harvest invariants | crop-specific biomass and concentration data | PARTIAL |
| 9. Pasture to milk | Does the minimal cow box reproduce transfer and turnover without double counting? | analytic animal box; controlled feeding data later | pasture intake, water intake, transfer and half-times | milk HTO/OBT and animal inventory | Bq L-1; Bq m-2 | days to season | relative error; cumulative error | analytic <=1e-6; experiment threshold preregistered | analytic animal-product box and integration case | time-resolved feeding study | PARTIAL |
| 10. Pasture to beef | Does herd turnover transfer activity to edible beef conservatively? | analytic product ledger; feeding/slaughter data later | herd turnover, product mass, pasture concentrations | beef HTO/OBT and product inventory | Bq kg-1; Bq m-2 | weeks to years | mass-balance residual; RMSE | residual <=1e-10; experiment threshold preregistered | conservative beef integration and ledger | suitable beef transfer dataset | PARTIAL |
| 11. Intake and inhalation dose | Are pathway activities converted to effective dose with the declared age-group coefficients? | analytic dose boxes and HPA coefficients | air, food, milk, beef, intake rates, dose coefficients | pathway and total dose | Sv | day/year | relative error; cumulative error | analytic <=1e-12; literature numeric within declared tolerance | 2 dose analytics and 2 HPA numeric comparisons | independent assessment-model comparison/site intake data | PARTIAL |
| 12. Uncertainty and sensitivity | Does sampling reproduce parameter distributions and stable dominant ranks? | statistical properties and independent replicated runs | distributions, correlations, seeds, sample sizes | quantiles, convergence, rank stability | observable unit; dimensionless rank | ensemble | interval coverage; relative quantile change | convergence gates in V2 acceptance; target coverage 0.90-0.95 | LHS n=64/128/256 and OAT evidence | external parameter distributions and stable weak-rank evidence | PARTIAL |
| 13. One-box vs three-box soil | Does three-box conserve activity and approach the one-box limit under equivalent conditions? | analytic/numerical conservation and degeneration limits | layer depths/water, exchange, drainage, root fractions | layer and total inventories, boundaries | Bq m-2 | step to season | mass balance; relative difference | residual <=1e-10; degeneration <=1e-6 | standalone three-box invariant | formal coupler interface and external profile data | PARTIAL |
| 14. Routine vs accident releases | Are source duration, time-series basis and follow-up semantics unambiguous? | scenario contract and later reference-model events | explicit scenario taxonomy fields and source series | emitted activity and pathway response | Bq; Bq s-1 | pulse to continuous | checksum; cumulative activity error | schema complete; source integration <=1e-12 | schema and taxonomy available | external event/source definitions | READY |
| 15. Long observed meteorology | Can every forcing interval be traced as observed rather than extended? | ERA5/observational forcing with status column | complete UTC grid, variable units, provenance and status | completeness and pathway time series | hours; pathway units | 72 h, 14 d, 30 d, seasonal | observed coverage; missing count | 100% observed for a full-observed validation case | 48 h ERA5 plus correctly labelled 24 h extension | complete observed 72 h and longer forcing | BLOCKED_EXTERNAL_DATA |
| 16. Site and experimental cases | Does the full candidate reproduce independent environmental observations within preregistered tolerances? | experiment, field observation, reference model and site case | redistributable or locally supplied inputs, uncertainties, detection limits, licence | air/soil/plant/food/dose observations | declared per observable | event to multi-year | RMSE, bias, correlation, interval coverage | set before execution for each dataset | schemas, runner, metrics and placeholder registry entries | actual licensed datasets and site parameters | BLOCKED_EXTERNAL_DATA |

## Evidence hierarchy and execution

Analytic and manual evidence tests implementation fidelity. Literature numeric
comparisons test only scale. Internal integration and regression cases test
connectivity, conservation, reproducibility and compatibility. Only independent
experiment, field, reference-model and site evidence can support empirical or
site validation claims.

Every executable case uses
`scripts/run_v2_validation_case.py`, records the candidate tag and current
commit, and writes an isolated report directory. Thresholds and unit
conversions are declared in the case before execution.
