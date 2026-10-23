# P3 R4: Direct 1993 printed Eq.(1)–(3) leaf HTO kinetics

**Normative primary source:** [Raskob, KfK 5194 (August 1993), §5.2, printed p.3 / PDF zero-based p.12](https://publikationen.bibliothek.kit.edu/270034158/3813483). The original page image was checked against all three equations and definitions. [P3 R1](P3_R1_CANOPY_MONTEITH.md) supplies 1993 source-anchored dry-day leaf resistances; [P3 R2](P3_R2_NIGHT_RAIN_CANOPY.md) covers explicitly source-limited wet/night branches. [P3 R3](P3_R3_TFWT_COMPAT_COUPLING.md) remains the separately marked 1990-analytical-kernel *compatibility* path, and is not silently relabelled.

## Published 1993 physical equations

Raskob prints the leaf's Belot-model solution for a stationary meteorological interval. With zero initial leaf HTO, Eq.(1) has `C(t)=chi*alpha/rho * (1-exp(-l*t))`. Eq.(2) gives `l=rho/(alpha*mu*r_g)`. With zero atmospheric HTO, Eq.(3) reduces to `C(t)=C0*exp(-l*t)`. Since the same first-order constant governs absorption and loss, linear superposition provides the general interval solution `C_new=C0*exp(-l*dt)+Ceq*(1-exp(-l*dt))`, `Ceq=alpha*chi/rho`. **The general initial-condition superposition and exact discrete interval implementation are analytical consequences of printed equations, not recovered FORTRAN source code.**

The printed units are `mu[g/cm² LEAF]`, `rho[g/ml saturated vapour]`, `chi[Bq/ml]`, `C[Bq/g water]`, `r_g[s/cm]`, `t[s]`. These translate consistently into SI as **kg/m² leaf**, **kg/m³**, **Bq/m³**, **Bq/kg plant water**, **s/m**, **s**. For given temperature/weather, the caller MUST explicitly supply the saturated vapour density: no weather formula/default is invented. Likewise `alpha` (the printed text says 1.1 is *assumed*) remains a required explicit argument, rather than a silent global default. Leaf resistances are sourced from P3 Eq.(4) via **leaf-total** `r_g=r_st+r_av+r_bv`, not the **ground-normalized** Eq.(10) canopy total.

## New independent 1993-anchored physical code

`src/cteas_ufotri/plant/kfk5194_1993_leaf_eq1_3.py` provides `advance_kfk5194_1993_leaf_eq1_to3` and sequential `advance_kfk5194_1993_leaf_intervals` with opt-in P1 profile. Uses `expm1` to avoid precision loss for short exchange intervals and the unchanged signed V3 TFWT storage balance to update inventory.

**Strict area gate:** state MUST declare `area_basis="leaf_area"` and plant water `kg/m² leaf`. The earlier P3 R3 ground-area inventory is **not** silently accepted or converted. Relating total-leaf-area kinetics to plant canopies per ground area requires its own science audit, including where the atmospheric boundary-layer resistance acts. The model outputs Bq/m² leaf integrated transfer and the V3 activity residual; does not couple stomata or transpiration to soil-root mass replacement.

## Verification and limits

Independent hand tests cover Eq.(1) zero-leaf initial uptake, Eq.(3) zero-air exponential loss, their nonzero-initial superposition, exact equilibrium, signed water inventory, day/night/rain resistance ordering, night-rain identity, time-step splitting, multihour activity telescoping, fail-closed dimensional inputs, source version checks, and unmodified old solver/CLI. These **verify the published mathematical model under prescribed inputs**, not the original 1993 FORTRAN program's exact rounding, algorithms, weather interpolation, crop parameters, whole-model transfer, empirical calibration, regulatory use or field observations. P0 #126 remains OPEN, whole 1993 solver selection stays disabled.

The P3 R3 mixed-edition compatibility bridge is intentionally retained for numerical cross-check. A later source-reviewed integration phase may project leaf-area budgets to ground-area vegetation inventory, but **must not** conflate the `r_g` and `r_c` resistance bases or double-scale LAI.
