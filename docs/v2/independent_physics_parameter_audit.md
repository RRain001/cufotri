# UFOTRI environmental pathways V2 independent physics and parameter audit

Audit date: 2026-07-24

Audited branch: `codex/ufotri-environmental-pathways-v2`

Audited commit: `0075708b35baeb6f8b3b5574d5b735316d959097`

V1 comparison commit: `6918440faa3455b848f43589784672f3bfabfe3d`

Auditor stance: independent acceptance review; existing V2 assessment conclusions were treated as claims to test, not as evidence.

## 1. Final conclusion

`REJECT_CURRENT_V2_PARAMETERIZATION`

The code is reproducible, numerically stable in the tested time-step range, and internally conservative inside the soil/plant/food and animal boxes. The HPA dose coefficients and most manual-derived rate conversions are correct. Those successes do not support formal V2 physics acceptance because the atmosphere-to-surface dry-deposition interface is not conservative.

In the 72 h wet-deposition case, the plume depletion calculation removes \(3.2460\times10^9\) Bq by dry deposition, while the coupled surface box independently receives \(v_d C_{\rm air}A=2.9013\times10^{10}\) Bq from the primary plume over the configured \(10^6\ {\rm m^2}\) area. The surface input is 8.94 times the corresponding atmospheric dry loss. Wet deposition does use one exact loss/input ledger; dry deposition does not. The reported `depletion_deposition_mismatch_bq_s` only closes the plume-side partition and therefore cannot detect this cross-module mismatch.

This is a `BLOCKER`, not a documentation-only limitation: it violates the required activity propagation invariant

\[
\text{atmospheric source loss}=\text{surface input}
\]

at the dry-deposition boundary. A passing compartment residual after injecting the independently calculated surface flux proves only that the compartment conserves what it was given.

## 2. Scope, baseline, and repository hygiene

Stage 0 checks passed:

- repository root was `/Users/rain/Documents/Doctor/Topic/CETAS_ufotri`;
- branch was `codex/ufotri-environmental-pathways-v2`;
- `HEAD` was `0075708b35baeb6f8b3b5574d5b735316d959097`;
- `main` was `6918440faa3455b848f43589784672f3bfabfe3d`;
- annotated tag `formal-minimal-baseline-v1` peeled to the same V1 commit `6918440faa3455b848f43589784672f3bfabfe3d`;
- initial worktree was clean and `git diff --check` passed;
- V2 relative to V1 contains 55 changed files, 3998 insertions, and 36 deletions;
- no credential was found in tracked content; `era5_key.example.txt` contains only a replacement placeholder;
- no raw ERA5 data, virtual environment, cache, or generated result directory is tracked.

The audit did not modify model code, tests, YAML, V1 assessment documents, implementation status, tags, branches, or Git history. It added only this report and the parameter-source CSV; temporary diagnostics use ignored `*.tmp` files under `audit_tmp/v2_physics_audit/`.

## 3. Severity-ranked findings

| ID | Severity | Finding | Acceptance consequence |
|---|---|---|---|
| B-01 | BLOCKER | Dry plume depletion and coupled dry surface input are calculated by different ledgers; the tested surface input is 8.94 times plume dry loss. | Reject current parameterization until the interface is made activity-conservative and regression-tested. |
| H-01 | HIGH | Leaf aerodynamic and boundary resistances are fixed at 50 s m-1; wind 0.5, 2, and 5 m s-1 produces exactly the same conductance. | The implementation is a signed provisional exchange law, not the claimed meteorology-responsive UFOTRI resistance closure. |
| H-02 | HIGH | None of the 15 V2 benchmark cases has an external/manual numeric reference or analytic numeric target; eight have no scenario-specific assertion beyond finite/nonnegative/closure. | `PASS_AVAILABLE_REFERENCE_CASES` overstates validation strength. |
| H-03 | HIGH | All five end-to-end configurations leave `leaf_exchange_mode=off`; the bidirectional pathway is exercised only by a separate two-hour acceptance case. | There is no integrated leaf-to-food/dose validation despite V2 provenance naming bidirectional resistance. |
| H-04 | HIGH | Routine cases compute and consume beef concentration continuously but never invoke `slaughter_event`; there is no beef production/slaughter boundary paired with dose consumption. | Meat dose is a diagnostic screening calculation, not a conservative animal-product transfer boundary. |
| H-05 | HIGH | Wet-scavenging \(a=10^{-5}\) has source grade E and no direct calibration. An IAEA comparison model uses \(5\times10^{-5}J^{0.8}\ {\rm s^{-1}}\), five times the current coefficient. | Wet results are project parameterization only; a direct UFOTRI/site source or calibrated uncertainty range is required. |
| H-06 | HIGH | Formal acceptance tests uncertainty on a toy linear function. End-to-end LHS uses only 12 samples and four parameters; several configured parameters are inactive in the selected case. | Reproducibility is demonstrated, but parameter uncertainty and rank sensitivity are not validated. |
| M-01 | MEDIUM | Advanced re-emission omits the manual rain 3% rule and does not modify DIFF with water specific activity as instructed by the manual. | Keep explicitly provisional; do not claim complete Eq. (44) fidelity. |
| M-02 | MEDIUM | `perennial=true` affects LAI only when growth start equals harvest. Grass and pasture use 90/300 and therefore become zero-LAI outside that window and are reset at harvest. | Perennial pasture semantics and multi-year behavior are not represented. |
| M-03 | MEDIUM | Three-box soil is conservative and convergent but is rejected by the full coupler. | Standalone experimental status is accurate; it cannot support coupled V2 claims. |
| M-04 | MEDIUM | The 72 h forcing contains 48 h ERA5 plus 24 h deterministic extension. The extension contains no rain. | Wet deposition is determined entirely by the first 48 h; 72 h is a follow-up, not a 72 h observed forcing benchmark. |
| M-05 | MEDIUM | The \(10^6\ {\rm m^2}\) wet/deposition/feedback footprint is a source-grade D uniform allocation. | Total wet activity is invariant to area, but all local soil and food concentrations scale inversely with it. |
| M-06 | MEDIUM | Crop, pasture-milk, and full-dose 14 d cases inherit a continuous 336 h source; only the accident and wet cases define a one-hour release. | Scenario interpretation must distinguish routine continuous release from accident follow-up. |
| M-07 | MEDIUM | Intake, crop yield, phenology, animal support area, feed, water, and most hydrology inputs are source-grade D project assumptions. | Dose remains research screening and cannot be treated as a site or regulatory result. |
| L-01 | LOW | `psychrometric_constant_pa_k` appears twice with the same value in the default YAML. | No numerical effect under YAML last-key behavior, but it weakens configuration QA. |
| L-02 | LOW | `AnimalState` field names end in `_bq` although routine coupled values are normalized Bq m-2. | Outputs are labeled Bq m-2; internal naming is misleading but arithmetic ratios cancel area consistently. |

Counts: 1 BLOCKER, 6 HIGH, 7 MEDIUM, 2 LOW.

## 4. Five-dimension subsystem audit matrix

| Subsystem | Dimensional correctness | Magnitude / limits | Conservation | Parameter provenance | Validation strength | Audit status |
|---|---|---|---|---|---|---|
| Wet scavenging | PASS | plausible but coefficient-sensitive | PASS for wet loss/input | \(a\) E; \(b\) C | weak comparison only | PROVISIONAL |
| Dry deposition | PASS locally | plausible local fractions | **FAIL at atmosphere/surface interface** | \(v_d\) A; footprint D | blocker not covered | REJECT |
| Leaf-air exchange | PASS after liquid/vapour conversion | day/night timescales plausible | box closure PASS | \(r_a,r_b,\) VPD E | two-hour synthetic only | PROVISIONAL_HIGH |
| Advanced re-emission | PASS | anchors reproduced | inventory-limited PASS | mixed A/D | no external trajectory | PROVISIONAL |
| Crop phenology | PASS | bounded LAI and biomass | allocation/harvest close | mostly D | no multi-year test | PROJECT_EXTENSION |
| Edible TFWT/OBT | PASS | hand conversions exact | internal transfers close | rates B; yields D | analytic/unit tests | ACCEPT_ARITHMETIC |
| Animal/milk | PASS | combined HTO/OBT residence plausible | feed/milk/excretion close | rates B; habits D | no beef boundary case | PROVISIONAL_HIGH |
| Public dose | PASS | hand arithmetic exact | pathway sums exact | coefficients A; habits D | no external scenario total | SCREENING_ONLY |
| Single-layer soil | PASS | tested extremes finite | residual near machine precision | depth A; water D | V1 and V2 regression | ACCEPT_WITH_INTERFACE_BLOCKER |
| Three-box soil | PASS | stable at 600–60 s | residual near machine precision | mixed A/E | standalone only | EXPERIMENTAL |
| Uncertainty | PASS arithmetic | \(n=12\) too small for stable rank claims | model reruns occur | ranges mostly D | formal driver uses toy model | INSUFFICIENT |
| Benchmarks | PASS execution | no numeric external targets | generic closure gates | mixed | 0 external/analytic | INSUFFICIENT |
| End-to-end | PASS execution | outputs finite/nonnegative | internal residuals pass; B-01 fails global interface | mixed | pathways incompletely activated | REJECT |

## 5. Wet scavenging and deposition

### 5.1 Dimensional reconstruction

The implementation is

\[
\Lambda_w=aP^b,
\]

with \(P\) converted from m s-1 to mm h-1. Therefore \(a\) has units
\(\mathrm{s^{-1}(mm\,h^{-1})^{-b}}\), not simply s-1 when \(b\ne0\). This is documented in code and is dimensionally usable.

The current \(a=10^{-5}\), \(b=0.8\) produces:

| Rain (mm h-1) | \(\Lambda_w\) (s-1) | Half-life | Removed in 1 h |
|---:|---:|---:|---:|
| 0.1 | 1.585e-6 | 121.5 h | 0.569% |
| 1 | 1.000e-5 | 19.25 h | 3.536% |
| 5 | 3.624e-5 | 5.31 h | 12.23% |
| 10 | 6.310e-5 | 3.05 h | 20.32% |
| 50 | 2.287e-4 | 50.5 min | 56.10% |

The 50 mm h-1 case is strong but not an instantaneous all-removal singularity. Zero rain gives exactly zero wet removal.

For the same 10 mm total precipitation, removal varies with intensity because \(b<1\):

| Rain pattern | Removed fraction |
|---|---:|
| 1 mm h-1 for 10 h | 30.23% |
| 2 mm h-1 for 5 h | 26.90% |
| 5 mm h-1 for 2 h | 22.97% |
| 10 mm h-1 for 1 h | 20.32% |

This is a transparent consequence of the chosen nonlinear parameterization, not a time-integration error.

### 5.2 Segment and footprint checks

At fixed rates, 1, 2, 5, 20, 100, and 1000 plume segments gave the same remaining, dry, and wet source rates to floating-point precision. Segment refinement is therefore algebraically invariant for the current constant-rate formulation.

Changing wet footprint area from \(10^5\) to \(10^6\) to \(10^7\ {\rm m^2}\) changes local flux by factors of ten but preserves

\[
F_{\rm wet}A=\dot Q_{\rm wet,loss}
\]

exactly. This wet ledger passes.

### 5.3 Independent source comparison

The current value of \(a\) is explicitly provisional and has no assigned direct source. The IAEA EMRAS tritium model-comparison report documents a Japanet formulation \(\Lambda=5.0\times10^{-5}J^{0.8}\ {\rm s^{-1}}\) with \(J\) in mm h-1, while also showing that UFOTRI used time-dependent resistance-model deposition rather than that Japanet law. The IAEA value is therefore a useful magnitude comparison, not permission to relabel the current coefficient as UFOTRI-derived: [IAEA EMRAS report, Table 9.6 and Eq. II.8.7](https://www-ns.iaea.org/downloads/rw/projects/emras/draft-final-reports/emras-tritium-wg.pdf).

### 5.4 Dry-deposition blocker

The plume code uses a source-depletion model. Separately, the coupled surface box receives

\[
F_{\rm dry}=v_d C_{\rm air}.
\]

The latter is multiplied by the full \(10^6\ {\rm m^2}\) feedback area but is not constrained to equal the plume loss allocated to that area. Results for the 72 h case are:

| Ledger term | Integrated activity |
|---|---:|
| Stack release | \(3.6000\times10^{12}\) Bq |
| Plume dry depletion | \(3.2460\times10^9\) Bq |
| Primary-air dry input to local surface | \(2.9013\times10^{10}\) Bq |
| Wet plume depletion / wet surface input | \(5.5450\times10^9\) Bq / same |
| Final environmental inventory over footprint | \(1.9596\times10^{10}\) Bq |

The coarse upper bound remains below stack release, but the interface ratio

\[
\frac{Q_{\rm dry,surface}}{Q_{\rm dry,plume\ loss}}=8.94
\]

fails conservation. The same ratio is approximately 8.94 in all five end-to-end cases, so it is structural rather than scenario noise.

## 6. Leaf-air exchange

### 6.1 Physical form and equilibrium

The implementation correctly avoids subtracting liquid-water Bq m-3 directly from air Bq m-3. Plant-water activity is converted to equilibrium air activity using vapour density, water density, and isotope fractionation:

\[
C_{a,\mathrm{eq}}=
C_{p,w}\frac{\rho_v}{\alpha\rho_w},
\qquad
F=g(C_a-C_{a,\mathrm{eq}}).
\]

At 293.15 K, RH 60%, LAI 3, and \(\alpha=1.1\), \(C_a=10^6\ {\rm Bq\,m^{-3}}\) corresponds to \(C_{p,w,\rm eq}=1.061\times10^{11}\ {\rm Bq\,m^{-3}}\). Flux was positive at 0.5 times that plant concentration, zero at equality, and negative at twice equality. `AIR_WATER_EQUILIBRIUM` is therefore not a blocker.

### 6.2 Resistance and timescale checks

At 293.15 K, RH 60%, LAI 3:

| Condition | Conductance (m s-1) | Linear equilibration half-life |
|---|---:|---:|
| day | 3.382e-3 | 3.02 h |
| night | 3.295e-4 | 31.0 h |

The day/night contrast is physically plausible and derives mainly from manual day/night stomatal resistances. A two-hour coupled test changed final plant TFWT by only 0.36% between 600 s and 60 s time steps.

However, conductance at wind 0.5, 2, and 5 m s-1 is identical because neither wind nor stability enters the leaf function and \(r_a=r_b=50\ {\rm s\,m^{-1}}\) are fixed. The original manual describes hourly resistances as functions of wind, stability, roughness, precipitation, and temperature. Current status must remain `MANUAL_DERIVED_PROVISIONAL`, with a HIGH limitation.

All five formal end-to-end configs use `leaf_exchange_mode=off`. Their plant TFWT comes from root uptake, not direct air-leaf exchange.

## 7. Re-emission

For unit soil inventory at the configured reference water and evaporation:

| Time since release | Day nominal fraction h-1 | Night nominal fraction h-1 |
|---:|---:|---:|
| 0 h | 0.110 | 0.010 |
| 24 h | 0.055 | 0.005 |
| 72 h | 0.01375 | 0.00125 |
| 14 d | 6.71e-6 | 6.10e-7 |

The 10% h-1 radiative and 1% h-1 diffusive anchors are reproduced, and the configured 24 h \(ZT\) half-life behaves monotonically. Inventory limiting prevents negative inventories at coarse steps.

The reconstruction is incomplete in two manual-specific respects:

- the rain-start re-emission rule of 3% is not represented;
- DIFF remains a fixed fraction rather than being modified for water specific activity.

No independent field trajectory or external numeric benchmark is present. The appropriate status is `PROVISIONAL`, not validated UFOTRI equivalence.

## 8. Crop, edible plant, and harvest

LAI is bounded and smooth for the configured seasonal mode. All annual crops give zero LAI on the start and harvest dates, peak at mid-season, and zero outside the season. Edible fresh mass is biomass × edible fraction × growth fraction; zero growth gives zero mass and protected zero concentration.

The same LAI state affects:

- radiation-term shading and transpiration;
- leaf canopy resistance;
- growth fraction and edible dilution mass.

These are different physical uses of one phenotype state, not an arithmetic double multiplication in one equation. They do create correlated sensitivity and should not be independently calibrated as though unrelated.

The `perennial` flag is only effective when `growth_start_doy == harvest_doy`. Grass and pasture are marked perennial but use 90/300, so their LAI is zero outside days 90–300 and harvest reset remains active. No multi-year continuity test exists.

Hand conversion with 680 Bq TFWT, 68 Bq OBT, 0.68 kg fresh mass, and 85% water gave:

- TFWT water concentration \(1.17647\times10^6\ {\rm Bq\,m^{-3}}\);
- TFWT fresh concentration \(1000\ {\rm Bq\,kg^{-1}}\);
- OBT fresh concentration \(100\ {\rm Bq\,kg^{-1}}\);
- OBT dry concentration \(666.67\ {\rm Bq\,kg^{-1}}\).

Allocation, turnover, decay, feed removal, harvest, and harvest loss are represented as explicit internal or boundary terms and close to floating-point precision.

## 9. Animal, milk, and beef

Configured animal rates reproduce the intended manual conversions:

| Process | Rate (d-1) | Individual half-life |
|---|---:|---:|
| HTO excretion | 0.160 | 4.33 d |
| HTO milk transfer | 0.039 | 17.77 d |
| OBT excretion | 0.0020 | 346.6 d |
| OBT milk transfer | 0.0021 | 330.1 d |
| OBT turnover | 0.015 | 46.2 d |

The combined HTO removal plus OBT formation is about 0.200 d-1, corresponding to 3.46 d, consistent with the manual 3.5 d body-water time. Combined OBT loss is about 0.0193 d-1, or about 36 d, close to the manual 40 d scale.

Feed is removed from the pasture edible inventory once; the limited actual feed flux is passed to the animal, avoiding double feed. Milk activity is removed from the animal inventory and divided by the milk-production rate, so milk concentration has a conservative product boundary.

The explicit slaughter API also conserves activity: a 600 s test moved the complete 0.375 Bq m-2 normalized body inventory to the slaughter boundary with zero residual. But `run_short_case` never calls it. Instead, every time step reports current body inventory divided by 200 kg as beef concentration and the dose module assumes daily beef consumption without removing or producing beef. This may be used as a concentration-screening surrogate for a representative herd, but that interpretation and its production boundary are absent. It is not a conservative beef pathway acceptance.

## 10. Dose

The configured HTO and OBT coefficients exactly match HPA-CRCE-004 Table 1 for infant 1 y, child 10 y, and adult 20 y; HTO inhalation values also match Table 2. The official source lists adult HTO \(1.8\times10^{-11}\), adult OBT ingestion \(4.2\times10^{-11}\), child HTO \(2.3\times10^{-11}\), child OBT \(5.7\times10^{-11}\), infant HTO \(4.8\times10^{-11}\), and infant OBT \(1.2\times10^{-10}\ {\rm Sv\,Bq^{-1}}\): [HPA-CRCE-004 Tables 1–2](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/340172/HPA-CRCE-004_for_website.pdf).

The implementation applies `dt/86400` once, uses separate HTO and OBT coefficients, adds skin absorption once at 0.5 inhalation, and sums pathway totals consistently. A one-day hand case produced:

| Pathway | Dose (Sv) |
|---|---:|
| inhalation | 3.6000e-7 |
| skin | 1.8000e-7 |
| drinking water | 3.6000e-9 |
| plant | 4.4400e-9 |
| milk | 3.3300e-9 |
| meat | 1.3320e-9 |
| total | 5.52702e-7 |

The arithmetic passes. Habit data remain source-grade D screening assumptions, and meat inherits H-04.

## 11. Activity propagation protocol

| Boundary / transfer | Correct unit | Internal transfer cancels? | External boundary explicit? | Result |
|---|---|---:|---:|---|
| plume dry loss | Bq s-1 | n/a | yes | plume ledger closes |
| dry air-to-soil | Bq m-2 s-1 | no | should match plume loss allocation | **FAIL B-01** |
| plume wet loss → soil wet input | Bq s-1 → Bq m-2 s-1 | n/a | exact area conversion | PASS |
| soil → plant root uptake | Bq m-2 s-1 | yes | no | PASS |
| air ↔ plant leaf | Bq m-2 s-1 | signed | leaf release boundary explicit | PASS locally |
| plant TFWT ↔ OBT | Bq m-2 s-1 | yes | decay explicit | PASS |
| plant → edible | Bq m-2 s-1 | yes | harvest/loss explicit | PASS |
| edible → animal feed | Bq m-2 s-1 | yes | excretion/milk explicit | PASS |
| animal → milk | Bq m-2 s-1 | no | product output explicit | PASS |
| animal → beef | Bq kg-1 diagnostic | no | routine production/slaughter absent | HIGH |
| food/air → public dose | Bq intake → Sv | n/a | receptor sink | arithmetic PASS |

Surface-box residuals of \(4.17\times10^{-16}\) to \(6.04\times10^{-16}\) and zero plume partition mismatch are real, but neither metric spans the dry interface. This is why B-01 survives all current formal tests.

## 12. Uncertainty and sensitivity

The uncertainty engine deep-copies sampled configs and reruns the model; it is not post-processing only. Fixed-seed sampling is reproducible.

Acceptance strength is nevertheless insufficient:

- `verify_v2_acceptance.py` tests reproducibility on \(x+2y\), not on UFOTRI;
- end-to-end LHS uses 12 samples and four parameters, too few for stable Spearman ranking;
- the default config declares 64 samples and nine parameters, but the formal artifact does not use that design;
- inactive modes make some selected parameters structurally zero in a given case.

An independent ±10% one-at-a-time run on the 336 h full-adult-dose case ranked normalized dose elasticities:

| Rank | Parameter | Source grade | Elasticity | Interpretation |
|---:|---|:---:|---:|---|
| 1 | adult HTO dose coefficient | A | 0.9991 | dominant linear dose scale |
| 2 | initial soil water | D | 0.02572 | weak but highest environmental assumption |
| 3 | deposition velocity | A | 0.02546 | affected by the dry-interface blocker |
| 4 | feed intake | D | 0.01407 | animal pathway |
| 5 | pasture maximum LAI | D | 0.01066 | phenotype/yield coupling |
| 6 | milk HTO transfer | A | 0.00702 | animal product |
| 7 | maximum soil water | D | 0.00319 | water-balance control |
| 8 | animal support area | D | 0.000526 | normalization area |
| 9 | plant OBT formation | A/B | 0.000412 | small in total-dose metric |
| 10 | wet-scavenging \(a\) | E | 0 | wet mode off in this case |

Re-emission radiative rate, adult leafy intake, and leaf aerodynamic resistance also had zero response because this case uses basic re-emission, pasture rather than leafy crop, and leaf exchange off. Zero sensitivity here is structural inactivity, not evidence that those parameters are unimportant.

Parameter-source inventory: 111 rows total; A 21, B 10, C 6, D 67, E 7. Thirty-six are accepted for their stated narrow use and 75 remain provisional. The full inventory is in `docs/v2/v2_parameter_source_audit.csv`.

## 13. Benchmark classification

| Benchmark | Class | Scenario-specific numeric acceptance |
|---|---|---|
| `v1_regression` | internal regression label | none; no V1 output equality |
| `no_rain_dry_deposition` | physical comparison member | only used as wet comparator |
| `strong_rain_wet_scavenging` | physical invariant | final air lower than dry case |
| `day_short_hto_release` | execution only | none |
| `night_short_hto_release` | execution only | none |
| `post_accident_reemission_72h` | execution only | none |
| `crop_growing_season_release` | execution only | none |
| `pre_harvest_release` | execution only | none |
| `pasture_milk_pathway` | physical invariant | final milk HTO positive |
| `full_adult_dose` | physical invariant | final total dose positive |
| `zero_source` | physical invariant | final air exactly zero |
| `extremely_low_wind` | execution only | none |
| `extremely_dry_soil` | execution only | none |
| `saturated_rain` | execution only | none |
| `single_vs_three_box_soil` | internal conservation | finite/nonnegative/closure only; no single-box comparison |

Classification counts:

- external/reference-model numeric benchmarks: 0;
- manual numeric trajectory benchmarks: 0;
- analytic numeric solution benchmarks: 0;
- cases participating in scenario-specific physical assertions: 5;
- internal regression/conservation labels without external target: 2;
- execution-only cases: 8.

All 15 also share finite, nonnegative, and internal residual gates. Those are valuable invariants, but they are not reference benchmarks.

## 14. Three-box soil

The standalone three-box solver passed:

- water and HTO closure at approximately \(10^{-17}\) m and \(10^{-13}\ {\rm Bq\,m^{-2}}\);
- nonnegative donor-limited transfers;
- correct concentration-gradient diffusion direction;
- zero-transfer degeneration, where \((1000,0,0)\) Bq m-2 remains unchanged;
- one-day refinement from 600 to 300 to 60 s, with total final HTO changing from 999.835209 to 999.835021 Bq m-2.

It is not called by `run_short_case`, which explicitly raises an error for `surface_root_deep_3box`. `PASS_EXPERIMENTAL_STANDALONE` is accurate; it does not establish formal coupled multi-layer performance.

## 15. End-to-end cases and 72 h forcing boundary

| Case | Release | Leaf mode | Key nonzero result | Dry input / dry plume loss |
|---|---:|---|---|---:|
| ERA5 72 h wet | 1 h | off | wet input \(5.545e9\) Bq | 8.94 |
| accident plant OBT 14 d | 1 h | off | max plant OBT 120.7 Bq m-2 | 8.94 |
| crop ingestion 14 d | 336 h | off | total dose \(1.532e-5\) Sv | 8.94 |
| pasture milk 14 d | 336 h | off | max milk HTO 4488.8 Bq L-1 | 8.94 |
| full adult dose 14 d | 336 h | off | total dose \(1.529e-5\) Sv | 8.94 |

The 24 h deterministic extension contains zero precipitation. Comparing the wet case at 48 and 72 h:

| Quantity | 48 h | 72 h | Change |
|---|---:|---:|---:|
| soil HTO (Bq m-2) | 24501.1 | 18951.8 | -22.6% |
| plant TFWT (Bq m-2) | 440.8 | 630.6 | +43.1% |
| plant OBT (Bq m-2) | 5.956 | 13.422 | +125% |
| cumulative rain | 16.195 mm | 16.195 mm | 0 |
| cumulative wet input | \(5.545e9\) Bq | \(5.545e9\) Bq | 0 |

The extension changes post-deposition redistribution and OBT formation but not wet deposition. It is transparently documented and is not itself a blocker.

Time-step refinement for the same 72 h case from 600 to 60 s changed final soil HTO by 0.22%, plant TFWT by 0.28%, plant OBT by 0.08%, and final total environmental inventory by 0.22%. Numerical convergence is adequate for screening.

## 16. Traceability and formal acceptance claims

| Existing claim | Independent result |
|---|---|
| wet deposition uses one conservative ledger | confirmed for wet only |
| atmospheric loss equals dry plus wet surface input | rejected for dry interface |
| bidirectional resistance is manual-derived provisional | signed equilibrium confirmed; meteorological resistance response incomplete |
| food chain closes without double-counting feed | confirmed for feed/milk; beef routine boundary incomplete |
| uncertainty passes reproducibly | sampler reproducibility confirmed; model uncertainty validation insufficient |
| 15 available reference cases pass | all execute; none has external/manual/analytic numeric reference |
| five end-to-end cases cover V2 pathways | all leave bidirectional leaf exchange off |
| ecological mass balance passes | compartment balances pass; cross-module dry boundary fails |

The present report therefore supersedes the acceptance strength of `docs/v2/formal_ufotri_environmental_pathways_v2_assessment.md` for this commit without editing that historical assessment.

## 17. Required corrections before re-audit

These are acceptance requirements, not changes made by this audit:

1. Define one dry-deposition activity ledger and use the same allocated activity for plume loss and surface input; add a cross-module integrated conservation test over the configured footprint.
2. Either calculate \(r_a\) and \(r_b\) from meteorology/roughness/stability or narrow the leaf claim to a fixed-resistance project model; run at least one end-to-end case with bidirectional leaf exchange active.
3. Replace or explicitly calibrate wet \(a,b\), document a directly applicable source and uncertainty range, and retain the footprint as a separate spatial assumption.
4. Add an explicit beef production/slaughter boundary or label and exclude the current beef diagnostic from conservative pathway claims.
5. Add at least one analytic/reference numeric target per core new pathway and external/manual comparison cases for wet, leaf, re-emission, animal, and dose.
6. Run full-model uncertainty with a justified sample count, all active influential parameters, mode-aware parameter selection, and reported confidence/stability of rankings.
7. Resolve perennial pasture semantics and add multi-year phenology/harvest tests.

## 18. Final statement

The current V2 is a useful, reproducible development candidate with several sound compartment calculations. It is not acceptable as a formal environmental-pathways V2 parameterization at this commit because a core atmospheric-to-surface activity boundary is non-conservative and the new-pathway validation matrix lacks external or analytic numeric targets.

`REJECT_CURRENT_V2_PARAMETERIZATION`

## 19. Audit status fields

```text
V2_PHYSICS_AUDIT_VERDICT = REJECT_CURRENT_V2_PARAMETERIZATION
V1_REGRESSION_STATUS = PASS
WET_SCAVENGING_PHYSICS_STATUS = PROVISIONAL_PARAMETERIZATION
LEAF_EXCHANGE_PHYSICS_STATUS = PROVISIONAL_HIGH_LIMITATION
REEMISSION_PHYSICS_STATUS = PROVISIONAL_INCOMPLETE_MANUAL_FIDELITY
CROP_PHENOLOGY_STATUS = PROJECT_EXTENSION_WITH_PERENNIAL_GAP
EDIBLE_PLANT_STATUS = PASS_ARITHMETIC_AND_INTERNAL_CONSERVATION
FOOD_CHAIN_STATUS = PROVISIONAL_BEEF_BOUNDARY_GAP
DOSE_PARAMETER_STATUS = PASS_COEFFICIENTS_SCREENING_HABITS
MULTIBOX_SOIL_STATUS = PASS_EXPERIMENTAL_STANDALONE
UNCERTAINTY_STATUS = REPRODUCIBLE_BUT_INSUFFICIENT
BENCHMARK_STATUS = INSUFFICIENT_EXTERNAL_VALIDATION
END_TO_END_STATUS = FAIL_DRY_INTERFACE_AND_PATHWAY_COVERAGE
BLOCKER_COUNT = 1
HIGH_SEVERITY_COUNT = 6
MEDIUM_SEVERITY_COUNT = 7
LOW_SEVERITY_COUNT = 2
REQUIRED_CORRECTIONS_COUNT = 7
FINAL_RECOMMENDATION = DO_NOT_ACCEPT_FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2
```

## 20. Remediation status at RC1

This section is a post-audit remediation record. It does not alter the audit
findings, counts, verdict, or recommendation above, which remain the independent
conclusion for audited commit
`0075708b35baeb6f8b3b5574d5b735316d959097`.

| ID | RC1 status | Remediation evidence / remaining boundary |
|---|---|---|
| B-01 | `RESOLVED` | One plume-loss ledger now allocates dry/wet surface activity; the audited 72 h dry ratio changed from 8.9379535 to exactly 1.0. |
| H-01 | `RESOLVED` | Golder/Monin-Obukhov aerodynamic resistance and flat-plate boundary resistance respond to wind, stability, roughness, geometry, and diffusion; literature limits are explicit. |
| H-02 | `RESOLVED` | The suite now contains ten analytic benchmarks, five manual anchors, and two literature comparisons; execution cases have separate labels. |
| H-03 | `RESOLVED` | `v2_leaf_exchange_food_dose_72h` propagates air to TFWT, OBT, edible plant, and dose with a zero mode-off control. |
| H-04 | `RESOLVED` | Continuous herd turnover removes animal activity into explicit beef storage; consumption and dose are inventory limited. |
| H-05 | `RESOLVED` | A named Japanet comparison set is the research default, explicitly not UFOTRI; project bounds and a 4 x 3 \(a,b\) grid propagate uncertainty. |
| H-06 | `PARTIALLY_RESOLVED` | A real full-dose case runs mode-aware LHS n=64/128/256 and four seeds. Quantiles converge, but weak-parameter rank order is only `LIMITED_WITH_EVIDENCE`. |
| M-01 | `DOCUMENTED_LIMITATION` | Rain-start 3% and concentration-dependent DIFF detail remain outside the provisional advanced re-emission reconstruction. |
| M-02 | `RESOLVED` | Explicit perennial modes, dormant LAI, three partial cuts per year, retained state, and a conservative two-year test are implemented. |
| M-03 | `DOCUMENTED_LIMITATION` | Three-box soil remains `PASS_EXPERIMENTAL_STANDALONE`; formal selection still raises an explicit error and a future-interface roadmap is recorded. |
| M-04 | `DOCUMENTED_LIMITATION` | The 72 h case still uses 48 h ERA5 plus a documented dry deterministic 24 h extension. |
| M-05 | `DOCUMENTED_LIMITATION` | Dry/wet footprint areas are explicit and independent from feedback area; local concentrations retain inverse-area sensitivity and no site calibration. |
| M-06 | `DOCUMENTED_LIMITATION` | Formal provenance distinguishes one-hour accidents from continuous 14 d routine releases; the scenario assumption remains. |
| M-07 | `DOCUMENTED_LIMITATION` | Crop, habit, animal, footprint, and hydrology values remain replaceable research-screening assumptions rather than regulatory/site inputs. |

```text
V2_STATUS = PHYSICS_REMEDIATION_RC1_CANDIDATE
FORMAL_ACCEPTANCE = PENDING_INDEPENDENT_REAUDIT
BLOCKER_REMAINING = 0
HIGH_RESOLVED = 5
HIGH_PARTIALLY_RESOLVED = 1
INDEPENDENT_REAUDIT_RECOMMENDATION = REAUDIT_REQUIRED_BEFORE_FORMAL_ACCEPTANCE
```
