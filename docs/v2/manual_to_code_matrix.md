# Manual-to-code matrix

| Process | Manual anchor | Unified quantity | Code target | Parameter source | Verification | Stage-0 status |
|---|---|---|---|---|---|---|
| Atmospheric transport | Eq. (4),(6),(25) | `Ca`, `Q` | `atmosphere/` | manual + existing YAML | Gaussian and quadrature tests | V1 implemented |
| Fallout | Sec. 2.1; Eq. (48) | `Lambda_d`, `F_dry` | `atmosphere/depletion.py` | project simplification | loss/deposition ledger | V1 implemented |
| Washout | Sec. 2.1; Eq. (49)-(50) | `Lambda_w`, `F_wet` | `atmosphere/wet_deposition.py` | provisional YAML | zero-rain, monotonicity, conservation | S1 pass project parameterization |
| HTO dry deposition | Eq. (1)-(3),(48) | `v_d Ca` | `coupling/integrator.py` | manual/YAML | surface closure | V1 implemented |
| Air-soil exchange | Eq. (1)-(2),(33)-(44) | `F_as`, `F_re,s` | `soil/`, `reemission/` | manual-derived/project extension | sign, limits, one/three-box closure | S8 single pass; three-box experimental |
| Soil re-release | Eq. (38)-(44) | `Es Cs`, `REEMG` | `reemission/fluxes.py` | manual/provisional YAML | calibration and mode comparison | S3 basic pass; advanced provisional validated |
| Air-leaf exchange | Eq. (7)-(32) | `F_ap`, `g_c` | `plant/leaf_exchange.py` | manual-derived/provisional | zero-gradient, sign, LAI/night, closure | S2 pass provisional |
| Root uptake | Sec. 2.2.5; Eq. (57)-(60),(75)-(77) | `U_i C_si` | `soil/`, `plant/` | manual | internal transfer closure | extend S5/S8 |
| TFWT | Eq. (3),(27)-(30) | `Mp/Wp` | `plant/tfwt.py`, `plant/edible.py` | manual-derived/project extension | whole-edible inventory and equilibrium tests | S5 pass |
| OBT | Sec. 2.2.6; Eq. (65)-(66),(105) | `Mobt` | `plant/obt.py`, `plant/edible.py` | manual/project extension | formation-turnover-allocation closure | S5 pass |
| Crop growth | manual limitation after Eq. (107) | LAI, biomass, edible fraction | `crop/` | project extension | phenology, shared LAI, edible harvest | S5 pass project extension |
| Food chain | Eq. (45)-(105) | plant/animal/milk inventories | `foodchain/` | manual + provisional YAML | ecological ledger, milk/beef paths | S6 pass minimal pathways |
| Inhalation | Eq. (106) | inhaled activity | `dose/public.py` | HPA-CRCE-004 YAML | analytic pathway tests | S7 pass |
| Skin absorption | Eq. (106) | separate skin dose | `dose/public.py` | manual factor/YAML | decomposition sum | S7 pass |
| Ingestion | Eq. (107) | food activity intake | `dose/public.py` | HPA-CRCE-004 + habits YAML | food/pathway sums | S7 pass |
| Dose | Eq. (106)-(107) | Sv by HTO/OBT/pathway | `dose/` | versioned YAML | exact arithmetic and totals | S7 research screening pass |
| Age groups | Sec. 4.1-4.3 | adult/child/infant | `dose/public.py` | HPA-CRCE-004 YAML | group-specific regression | S7 pass |
| Probability/uncertainty | Sec. 1 probabilistic use | samples/statistics | `analysis/uncertainty.py` | project extension | fixed-seed reproducibility | planned S9 |

No row marked planned is represented as implemented.
