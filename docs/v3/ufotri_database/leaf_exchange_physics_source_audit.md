# V3-P6.2A Leaf-Exchange Physics Source Audit

Status: `SPECIFICATION_ONLY_NOT_IMPLEMENTED`

This audit records what can be traced to the local UFOTRI manual and what is
still required before a future validated parameter package can be assembled.
It is an evidence register, not a parameter import. An explicit manual value
or relation is not a validated parameter: validation requires an independently
traceable experiment or field dataset, a defined applicability domain, and an
uncertainty statement.

## Scope and source baseline

The primary source is `ufotri_manual.md`, identified in the existing V3-P6.1
source audit as the UFOTRI manual by W. Raskob, KfK 4605. The relevant source
locations are:

- §2.2.2, *Plant/Atmosphere Exchange Processes*, pp. 13–18, equations 7–32;
- §2.2.6, *Exchangeable and Non-Exchangeable Tritium*, p. 29;
- §3.3.1, plant compartment transfer rates, including equations 46–47;
- the existing P6.1 audit, `ufotri_database_source_audit.md`, on the
  unmerged P6.1 branch `codex/v3-p6-1-independent-review`.

The P6.2A implementation baseline is `origin/main@6671f579`. P6.1 remains a
separate, pushed, unmerged branch. No P6.1 or UFOTRI numerical parameter is
copied into the production path by this audit.

The equation-level evidence set explicitly includes Eq. 27 (dynamic exchange),
Eq. 28 (constant-forcing solution), Eq. 29 (time constant), Eq. 30 (plant
loss), Eq. 31 (plant re-emission), and Eq. 32 (the source-depletion relation).

## Classification

Each row uses exactly one of these classifications:

- `EXPLICIT_FROM_UFOTRI`: stated in the manual as a value, state, or relation;
- `DERIVED_FROM_UFOTRI`: algebraically derived from explicit manual material,
  with the derivation still requiring review;
- `ASSUMPTION`: a modelling simplification, representative value, or local
  design choice rather than a validated general relation;
- `MISSING`: not available as a traceable, usable, uncertainty-bearing input.

`EXPLICIT_FROM_UFOTRI` never means `VALIDATED` or `ACTIVE`.

## Evidence register

| Item | Manual unit / canonical unit | Source chapter or equation | Dependencies and applicability | Current state | Classification | Uncertainty / limitation |
|---|---|---|---|---|---|---|
| Direct HTO vapour exchange with plant water | Manual uses activity concentration in `pBq ml^-1` for air and `pBq g^-1` for tissue water; V3 forcing is `Bq m^-3` | §2.2.2, Eqs. 7–9 and 27 | HTO atmosphere, plant water, exchange resistance | Physical process and state relation are described | `EXPLICIT_FROM_UFOTRI` | Manual and V3 SI bases are different; conversion and area/water basis must be frozen before implementation |
| Air HTO concentration `chi` | `pBq ml^-1` in Eq. 27; V3 `Bq m^-3` | §2.2.2, Eq. 27 | Atmospheric forcing at plant height / ground-level air | Source variable identified | `EXPLICIT_FROM_UFOTRI` | No crop/stage-specific uncertainty or canonical V3 conversion package is supplied |
| Plant-water TFWT concentration `C` | `pBq g^-1` tissue water in Eq. 27; future V3 concentration must be derived from inventory and water amount | §2.2.2, Eqs. 27–30 | Plant water content, saturated vapour density, isotope ratio, resistance | Source state and dynamic relation identified | `EXPLICIT_FROM_UFOTRI` | `g cm^-2`, `g ml^-1`, `s cm^-1` and `s m^-1` appear across the source; no normalized V3 state implementation exists |
| Plant water per unit leaf area `mu` | `g cm^-2` | §2.2.2, Eq. 27 | Leaf water content and active exchange area | Source parameter named | `EXPLICIT_FROM_UFOTRI` | No crop, growth-stage, temperature, humidity, or uncertainty table |
| Saturated water-vapour density `rho` | `g ml^-1` in Eq. 27 | §2.2.2, Eq. 27 | Temperature-dependent saturation state | Source parameter named | `EXPLICIT_FROM_UFOTRI` | Functional temperature relation and valid range are not specified in the manual section |
| Liquid/air isotope ratio `a = H/T` | Dimensionless; manual assumes `1.1` | §2.2.2, Eq. 27 | Isotopic partition between liquid and air | A representative source assumption is recorded | `ASSUMPTION` | Not a validated universal constant; applicability and uncertainty are absent |
| Total plant resistance `r_G` | `s m^-1` in Eq. 9/26; Eq. 27 lists `s cm^-1` for `r` | §2.2.2, Eqs. 8–11 and 26–27 | Stomatal and atmospheric resistance | Resistance-chain concept is explicit | `EXPLICIT_FROM_UFOTRI` | Unit-base inconsistency must be resolved; the manual does not provide a validated database |
| Stomatal resistance `r_ST` / canopy resistance `r_c` | `s m^-1` | §2.2.2, Eqs. 9, 11 and 14 | Plant type, temperature, PAR/day-night, soil water, precipitation, LAI | Dependencies are explicit; the canopy conversion is source-derived | `DERIVED_FROM_UFOTRI` | Source supplies representative values, not a crop/stage response surface with uncertainty |
| Aerodynamic resistance `r_a` / `r_AV` | `s m^-1` | §2.2.2, Eqs. 10, 12 and 15–18 | Wind, measurement height, vegetation height, displacement, stability and friction velocity | Resistance pathway is explicit | `DERIVED_FROM_UFOTRI` | Requires meteorological and canopy parameterization; no V3 validated lookup table |
| Quasi-laminar boundary resistance `r_b` / `r_BV` | `s m^-1` | §2.2.2, Eqs. 13 and 19–21 | Friction velocity, roughness lengths, Stanton-number representation | Source relation identified | `DERIVED_FROM_UFOTRI` | Roughness and transfer assumptions are not validated for the V3 crop domain |
| Total resistance decomposition `r = r_a + r_b + r_c` | `s m^-1` after normalization | §2.2.2, Eq. 26 | Aerodynamic, boundary-layer and stomatal paths | Algebraic decomposition is frozen as a specification input | `DERIVED_FROM_UFOTRI` | Must not be combined with the existing V2 implementation as a validated UFOTRI database value |
| Daytime single-leaf diffusion resistance | `4 s cm^-1` in the manual | §2.2.2, p. 16 and §4 input table | Representative vegetation and vegetation period | Manual representative value | `ASSUMPTION` | Site, species, season and uncertainty are not supplied; not imported |
| Nighttime single-leaf diffusion resistance | `60 s cm^-1` in the manual | §2.2.2, p. 16 and §4 input table | Stomatal closure / epidermal exchange | Manual representative value | `ASSUMPTION` | Not a validated day/night function; not imported |
| Mean leaf area index | `3 m^2 m^-2` | §2.2.2, p. 16 | Typical German field/forest landscape, mid-April to late October | Representative source value | `ASSUMPTION` | Not a crop-specific or growth-stage value |
| TFWT dynamic equation | `C`: activity per tissue-water mass; `t`: `s`; flux form requires `Bq m^-2 s^-1` | §2.2.2, Eq. 27 | `chi`, `mu`, `rho`, `a`, `r` held constant for the analytical form | Governing source relation identified | `EXPLICIT_FROM_UFOTRI` | The source equation is not a complete V3 inventory equation and omits the future ledger/interface contract |
| Constant-forcing analytical solution | Same as Eq. 27 | §2.2.2, Eqs. 28–29 | Constant `chi`, `mu`, `rho`, `r`; initially `C=0` | Source solution identified | `EXPLICIT_FROM_UFOTRI` | Long releases require superposition/initial-state handling; no implementation is authorized here |
| Plant concentration loss | Same as `C` | §2.2.2, Eq. 30 | Initial plant concentration `C_0`, time constant `k` | Source relation identified | `EXPLICIT_FROM_UFOTRI` | Does not by itself separate exchange, evaporation, transformation, or root pathways |
| Plant re-emission rate `R_P` | Percent per unit time in source text | §2.2.2, Eq. 31 | Initial and residual plant concentration | Source reporting relation identified | `EXPLICIT_FROM_UFOTRI` | OCR/source notation is ambiguous (`delta C_0`); signed flux and inventory normalization are missing |
| Plant deposition velocity `v_dP` | Source gives a ratio of ground-level air concentration to plant concentration; expected velocity would be `m s^-1` | §2.2.2, Eq. 32 | Source-depletion method, ground-level air and plant concentration | Text and equation are explicit | `EXPLICIT_FROM_UFOTRI` | The displayed ratio is dimensionally not a velocity; direction and normalization require independent resolution |
| Water loss by evaporation | No independent unit-bearing equation in §2.2.2 | §2.2.2, after Eq. 31 | Evaporation demand, plant water and re-emission | Source says it is partly represented by the semi-empirical relation | `ASSUMPTION` | High evaporation may overestimate plant-water activity; no separable parameter is supplied |
| Plant species classes | Species classes: nutrient plants and pasture grass | §2.2.2, after Eq. 32; §3.3 | Land use, plant-specific resistance and two vegetation areas | Source domain is limited to two broad classes | `EXPLICIT_FROM_UFOTRI` | No direct mapping to the V3 crop vocabulary or growth stages |
| Vegetation area split | `20%` grazing / `80%` food production | §2.2.2, after Eq. 32 | Missing site-specific land-use data | Representative default | `ASSUMPTION` | Not an experimental validation and must not become a V3 default |
| Day/night plant loss half-time | About one hour daytime; doubled at night | §3.3.1, Eq. 46 and preceding text | Mean diffusion resistance, plant water content, day/night cycle | Source-derived transfer-rate basis | `DERIVED_FROM_UFOTRI` | Representative conditions only; no uncertainty distribution or crop/stage applicability |
| Plant water inventory | `0.4 kg m^-2`; hydrogen content `0.044 kg m^-2` | §3.3.1, Eq. 46 discussion | Plant compartment used for transfer-rate derivation | Manual compartment value | `ASSUMPTION` | It is a model compartment value, not a validated universal biomass/water state |
| Plant-to-atmosphere transfer rate `t_14,1` | `d^-1`; manual derives `8.3 d^-1` | §3.3.1, Eq. 46 | Day/night loss half-time and 24-hour conversion | Algebraic source derivation identified | `DERIVED_FROM_UFOTRI` | Value is not imported; unit conversion and applicability require review |
| Atmosphere-to-plant transfer rate `t_1,14` | `d^-1`; manual derives `0.205 d^-1` | §3.3.1, Eq. 47 | Ratio `0.5`, `t_14,1`, plant hydrogen content, atmospheric water column | Algebraic source derivation identified | `DERIVED_FROM_UFOTRI` | Depends on uncontaminated soil, `8 g m^-3` humidity and `1 km` mixing height; not a universal leaf parameter |
| OBT formation rate | Daily average `0.06% h^-1` of actual plant HTO concentration | §2.2.6, p. 29 | Plant TFWT, photosynthesis/day-night split | Manual assumption is explicit | `ASSUMPTION` | Day/night numeric split, crop/stage response and uncertainty are missing |
| OBT loss rate | Mean `0.3% h^-1`; source also cites half-life range `80 h` to about `10 d` | §2.2.6, p. 29 | OBT inventory and loss model | Manual representative rate is explicit | `ASSUMPTION` | Cited range is heterogeneous; no validated V3 distribution or applicability domain |
| Crop × growth-stage × temperature × humidity tables | Required dimensions; no complete table in the manual | P6.1 database audit; absent from manual evidence above | Future lookup/interpolation, out-of-domain policy and uncertainty | No importable data identified | `MISSING` | Blocks candidate/reviewed package completion and any `ACTIVE` lifecycle state |
| Parameter uncertainty and validation evidence | Structured uncertainty, experiment/field references, hashes and coverage | Manual and P6.1 audit | Every imported value/relation | Not available as a complete package | `MISSING` | This phase records requirements only; no experimental validation is claimed |

## Audit disposition

The manual is sufficient to freeze a traceable *physics specification*: the
state variables, resistance chain, source equations, broad species classes,
and the stated day/night and OBT assumptions can be named with source
locations. It is not sufficient to populate a validated crop-dependent
database. In particular, the manual does not provide a complete
`crop × growth_stage × temperature × humidity` table, interpolation policy,
out-of-domain rule, or structured uncertainty package.

The existing `src/cteas_ufotri/plant/leaf_exchange.py` is an older V2 numerical
path. It is deliberately outside this P6.2A V3 specification and is not
relabelled as UFOTRI-validated. P6.2A adds no V3 solver, no production
parameter, and no default runtime connection.

```ini
LEAF_EXCHANGE_SOURCE_AUDIT = COMPLETE
UFOTRI_MANUAL_EVIDENCE = EXPLICIT_AND_LIMITED
EXPLICIT_DOES_NOT_MEAN_VALIDATED = TRUE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
```
