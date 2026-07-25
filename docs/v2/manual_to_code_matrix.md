# Manual-to-code matrix

Current matrix disposition:
`FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE`, accepted by the RC2
independent re-audit with no BLOCKER/HIGH. Rows labelled provisional,
experimental, project extension, or research screening remain limited exactly
as stated and are also registered in `v2_candidate_limitations.yaml`.

| Process | Manual anchor | Unified quantity | Code target | Parameter source | Verification | Stage-0 status |
|---|---|---|---|---|---|---|
| Atmospheric transport | Eq. (4),(6),(25) | `Ca`, `Q` | `atmosphere/` | manual + existing YAML | Gaussian and quadrature tests | V1 implemented |
| Fallout | Sec. 2.1; Eq. (48) | `Lambda_d`, `F_dry`, `M_d=F_dA_d` | `atmosphere/depletion.py`, `atmosphere/deposition.py` | project simplification | loss/deposition ledger and unequal-footprint closure | RC2 N-01 pass |
| Washout | Sec. 2.1; Eq. (49)-(50) | `Lambda_w`, `F_wet`, `M_w=F_wA_w` | `atmosphere/wet_deposition.py`, `atmosphere/deposition.py` | named Japanet literature comparison plus project brackets | zero-rain, monotonicity, conservation, unequal-footprint and 4 x 3 uncertainty grid | RC2 N-01 pass |
| HTO dry deposition | Eq. (1)-(3),(48) | plume dry/wet activities remain separate through the ecological reference-area interface; `v_d Ca` diagnostic only | `coupling/integrator.py` | manual/YAML | cross-module interface and global closure | RC2 N-01 pass |
| Air-soil exchange | Eq. (1)-(2),(33)-(44) | `F_as`, `F_re,s` | `soil/`, `reemission/` | manual-derived/project extension | sign, limits, one/three-box closure | S8 single pass; three-box experimental |
| Soil re-release | Eq. (38)-(44) | `Es Cs`, `REEMG` | `reemission/fluxes.py` | manual/provisional YAML | calibration and mode comparison | S3 basic pass; advanced provisional validated |
| Air-leaf exchange | Eq. (7)-(32) | `F_ap`, `r_a+r_b+r_c`, `g_c`, Eq. (27) saturated vapour density | `plant/leaf_exchange.py` | manual + Golder/flat-plate literature parameterization | RH-invariant equilibrium, wind/stability/geometry/VPD/LAI, sign, closure, analytic and formal E2E | RC2 N-02 pass literature parameterization |
| Root uptake | Sec. 2.2.5; Eq. (57)-(60),(75)-(77) | `U_i C_si` | `soil/`, `plant/` | manual | internal transfer closure | extend S5/S8 |
| TFWT | Eq. (3),(27)-(30) | `Mp/Wp` | `plant/tfwt.py`, `plant/edible.py` | manual-derived/project extension | whole-edible inventory and equilibrium tests | S5 pass |
| OBT | Sec. 2.2.6; Eq. (65)-(66),(105) | `Mobt` | `plant/obt.py`, `plant/edible.py` | manual/project extension | formation-turnover-allocation closure | S5 pass |
| Crop growth | manual limitation after Eq. (107) | LAI, biomass, edible fraction, root/shoot activity | `crop/`, `coupling/state.py` | project extension | actual 365/366 d calendars, root-retaining partial cuts, two-year closure | RC2 perennial pass project extension |
| Food chain | Eq. (45)-(105) | plant/animal/milk/beef-product inventories | `foodchain/` | manual + provisional YAML | ecological ledger, milk, continuous herd turnover, product-limited beef dose | RC1 S3 pass minimal conservative pathways |
| Inhalation | Eq. (106) | inhaled activity | `dose/public.py` | HPA-CRCE-004 YAML | analytic pathway tests | S7 pass |
| Skin absorption | Eq. (106) | separate skin dose | `dose/public.py` | manual factor/YAML | decomposition sum | S7 pass |
| Ingestion | Eq. (107) | food activity intake | `dose/public.py` | HPA-CRCE-004 + habits YAML | food/pathway sums | S7 pass |
| Dose | Eq. (106)-(107) | Sv by HTO/OBT/pathway | `dose/` | versioned YAML | exact arithmetic and totals | S7 research screening pass |
| Age groups | Sec. 4.1-4.3 | adult/child/infant | `dose/public.py` | HPA-CRCE-004 YAML | group-specific regression | S7 pass |
| Probability/uncertainty | Sec. 1 probabilistic use | samples/statistics | `analysis/uncertainty.py`, `analysis/full_model_uncertainty.py` | project extension | toy analytic check plus mode-aware full model n=64/128/256 and four seeds | RC1 S6 pass; ranks limited with evidence |

No row marked planned is represented as implemented.
