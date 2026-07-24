# Manual-to-code matrix

| Process | Manual anchor | Unified quantity | Code target | Parameter source | Verification | Stage-0 status |
|---|---|---|---|---|---|---|
| Atmospheric transport | Eq. (4),(6),(25) | `Ca`, `Q` | `atmosphere/` | manual + existing YAML | Gaussian and quadrature tests | V1 implemented |
| Fallout | Sec. 2.1; Eq. (48) | `Lambda_d`, `F_dry` | `atmosphere/depletion.py` | project simplification | loss/deposition ledger | V1 implemented |
| Washout | Sec. 2.1; Eq. (49)-(50) | `Lambda_w`, `F_wet` | `atmosphere/wet_deposition.py` | manual/literature/provisional YAML | zero-rain, monotonicity, conservation | planned S1 |
| HTO dry deposition | Eq. (1)-(3),(48) | `v_d Ca` | `coupling/integrator.py` | manual/YAML | surface closure | V1 implemented |
| Air-soil exchange | Eq. (1)-(2),(44) | `F_as`, `F_re,s` | `soil/`, `reemission/` | manual-derived | sign, limits, closure | extend S3/S8 |
| Soil re-release | Eq. (38)-(44) | `Es Cs`, `REEMG` | `reemission/fluxes.py` | manual/provisional YAML | calibration and mode comparison | extend S3 |
| Air-leaf exchange | Eq. (7)-(32) | `F_ap`, `g_c` | `plant/leaf_exchange.py` | manual-derived/provisional | zero-gradient, sign, LAI/night | planned S2 |
| Root uptake | Sec. 2.2.5; Eq. (57)-(60),(75)-(77) | `U_i C_si` | `soil/`, `plant/` | manual | internal transfer closure | extend S5/S8 |
| TFWT | Eq. (3),(27)-(30) | `Mp/Wp` | `plant/tfwt.py` | manual-derived | inventory and equilibrium tests | extend S2/S5 |
| OBT | Sec. 2.2.6; Eq. (65)-(66),(105) | `Mobt` | `plant/obt.py` | manual/manual-derived | formation-turnover closure | extend S5 |
| Crop growth | manual limitation after Eq. (107) | LAI, biomass, edible fraction | `crop/` | project extension | phenology/harvest tests | planned S4/S5 |
| Food chain | Eq. (45)-(105) | plant/animal/milk inventories | `foodchain/` | manual + literature YAML | ecological ledger | planned S6 |
| Inhalation | Eq. (106) | inhaled activity | `dose/public.py` | manual + versioned YAML | analytic pathway tests | planned S7 |
| Skin absorption | Eq. (106) | separate skin dose | `dose/public.py` | configurable ratio | decomposition sum | planned S7 |
| Ingestion | Eq. (107) | food activity intake | `dose/public.py` | manual + YAML | food/pathway sums | planned S7 |
| Dose | Eq. (106)-(107) | Sv by HTO/OBT/pathway | `dose/` | versioned YAML | exact arithmetic and totals | planned S7 |
| Age groups | Sec. 4.1-4.3 | adult/child/infant | `dose/parameters.py` | literature YAML | group-specific regression | planned S7 |
| Probability/uncertainty | Sec. 1 probabilistic use | samples/statistics | `analysis/uncertainty.py` | project extension | fixed-seed reproducibility | planned S9 |

No row marked planned is represented as implemented.

