# P3 R1 — Opt-in KfK 5194 (1993) daytime plant/soil resistance–Monteith physics

This P3 PR contains **new physical code**, not solely source documentation. It uses [official KfK 5194 (1993)](https://publikationen.bibliothek.kit.edu/270034158/3813483), §§5.2, 5.3.1, printed pp.4–5, 7 (PDF zero-based indices 13–14,16). These page images and E04–E11 source-registry entries were compared before implementation.

## Implemented

- Eq.(4)–(6): leaf transfer resistance `r_g = r_st + r_av + r_bv`, aerodynamic `r_av=u(z)/u_*²`, boundary `r_bv=1/(u_* B)`. All resistances `s/m`. Eq.(10): `r_c=r_st/LAI` and an independent canopy total. `LAI` is dimensionless; friction and mean wind are `m/s`.
- Eq.(7)–(9): daylight extended stomatal `r_st=r_st,min(1+c/I_p)/(f_l f_w f_t)`; `f_l=1-b_v Δe`, with **Δe in hPa, b_v in 1/hPa**; `f_t=((T-Te)/(T0-Te))*((Th-T)/(Th-T0))**((Th-T0)/(T0-Te))`. Soil-water factor `f_w` is **required from the caller**, bounded (0,1], and deliberately not inferred from a historical curve described only qualitatively.
- Eq.(11): double-use Monteith resistance energy balance for the leaf canopy (`r_x=r_c`) and soil (`r_x=r_soil`). Leaf/soil radiation split as printed: `R_leaf=Rn*(1-exp(-0.398*LAI))`, `R_soil=Rn*exp(-0.398*LAI)`. `r_AV=r_av+r_bv` is used for both as an **explicitly disclosed reconstruction assumption**. The same vapour-pressure deficit enters Eq.(7) as hPa and Eq.(11) in Pa (×100). Input `δ,γ` in Pa/K (equivalent J/m³/K), heat capacity density `ρc_p` in J/(m³ K), latent heat in J/kg; result W/m² and kg/(m² s).

`src/cteas_ufotri/plant/kfk5194_1993_canopy_et.py` exposes `kfk5194_1993_daylight_canopy` and `kfk5194_1993_monteith_et`; both require the independently validated `KFK5194_1993_V4` P1 source-profile object (`IMODEL=1`, `IMONT=1`). This is independent of the previously existing 1990-compatibility `leaf_ufotri_v4` path, which is untouched.

**No fabricated source defaults:** crop minimum stomatal resistance, humidity sensitivity, half-response radiation, soil water factor, upper/lower/optimum temperatures, LAI, wind/friction/Stanton, meteorological thermodynamics, and soil resistance must be provided explicitly, with units. Tests use **illustrative synthetic values only**, not evidence of default parameter values in the 1993 binary.

## Deliberately excluded from R1

The printed source describes night-time epidermal resistance, daytime rainfall change, and step-like soil-water response but does not establish a universal quantitative parameterization. R1 **fails closed** for night/rain regimes and for undefined/zero temperature-factor denominators. It is *not* a full-day/year evaporation product, an OBT/TFWT coupling, a calibration to field data, or an activated 1993 default runtime. Later P3 increments will implement separately reviewed night/wet branches and dynamic coupling.

Validation: independent hand-calculation of resistance terms; photosynthesis temperature optimum/sensitivities; 0.398 LAI energy partition and ET units; radiation-budget closure; input-domain rejection; profile option gates and legacy CLI/config/leaf-isolation test. Full P0 #126 remains open; original FORTRAN source is unavailable and executable numerical equivalence is **NOT_ESTABLISHED**.

Usage (synthetic illustration):

```python
from cteas_ufotri.versioned_inputs_1993 import load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_canopy_et import (
    kfk5194_1993_daylight_canopy, kfk5194_1993_monteith_et,
)

profile = load_1993_source_profile(
    "configs/ufotri_1993_manual_source_profile.yaml",
    selected_profile="KFK5194_1993_V4",
)
# Supply site/crop-specific, source-reviewed physical values (no silent defaults).
```
