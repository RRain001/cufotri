# V3 P7.6C-2 equation mapping report

```text
P7_6C2_STATUS = PASS_EQUATION_SEMANTICS_AUDITED
V3_PHYSICS_READY = FALSE
V3_EQUATIONS_CHANGED = FALSE
UFOTRI_EQUATIONS_IMPORTED = FALSE
```

## Frozen V3 contracts

The comparison uses the current V3 equations as fixed contracts. No equation
was edited for P7.6C-2.

| Subsystem | Frozen V3 contract | Canonical basis |
|---|---|---|
| leaf | `r_total = r_a + r_b + r_c`; `g_ex = 1/r_total`; signed exchange is `g_ex*(C_air-C_eq)` | `docs/equations/plant.md`, `plant/leaf_exchange_resistance/resistance.py` |
| TFWT | `dM_TFWT/dt = F_leaf + F_root - F_water_loss - F_TFWT_to_OBT`; `C_TFWT=M_TFWT/W_p` | `docs/equations/plant.md`, `plant/tfwt_v3/tfwt_solver.py` |
| OBT | `dM_OBT/dt = k_f*M_TFWT - k_r*M_OBT`; formation is balanced against the public TFWT inventory | `docs/equations/plant.md`, `plant/obt_v3/obt_solver.py` |
| soil | `dM_s/dt = F_deposition + F_transport - F_loss - lambda_T*M_s`; `C_s=M_s/W_s` | `docs/equations/soil.md`, `plant/soil_v3/soil_solver.py` |
| root | `J_root = k_root*C_soil`, with `k_root` in `m s^-1` and `C_soil` in `Bq m^-3 water` | `plant/root_v3/root_solver.py` |
| food | explicit event transfer from public OBT/TFWT inventories using configured harvest fractions | `plant/food_v3/food_transfer_solver.py` |
| intake | `C_food=M_food/m_food`; `I_food=C_food*R_consumption` | `exposure/intake_v3/intake_solver.py` |
| dose | `D=I*e`, with `e` in `Sv/Bq` | `exposure/dose_v3/dose_solver.py` |

## Recovered UFOTRI equation semantics

### Leaf

UFOTRI Eq. (12)-(14) explicitly identify `r_a=r_aV`, `r_b=r_bV`, and
`r_c=r_ST/L`, all in `s m^-1`. This is a direct semantic match to the three
V3 resistance components. The manual's additional aerodynamic, boundary,
stomatal, LAI, wind, and meteorological relations are not silently activated
by the mapping.

### TFWT and leaf exchange

UFOTRI Eq. (3) contains plant HTO loss/transfer terms such as `T_P C_P` and
`V_P C_P`. The current V3 TFWT solver accepts external activity fluxes, so a
rate-to-flux relation can be recorded only as an explicit transformation:
`F = rate * areal activity inventory`. The manual Eq. (27) also uses plant
water content and an exchange resistance; the V3 resistance module still
receives the equilibrium atmospheric quantity through its public interface.

### OBT

UFOTRI describes OBT formation from plant HTO/organic hydrogen, gives a
biological loss half-time, and records Eq. (65)-(66) as equilibrium/mass-based
transfer rates. The first-order roles are compatible with the V3 `k_f/k_r`
equation after an explicit day-to-second conversion, but the manual also
distinguishes exchangeable and non-exchangeable OBT and uses crop/day/night
assumptions. Therefore no rate value is admitted. The manual's
photosynthesis mechanism is a conceptual analogue to a V3 forcing extension,
not a current V3 equation.

### Soil and root

UFOTRI Eq. (1)-(2) uses areal soil activity and a downward flux `F_S`, while
the V3 soil solver uses a signed boundary flux. For a selected topsoil
boundary, the explicit orientation relation is `F_V3=-F_S` when downward
UFOTRI transport leaves the current layer. UFOTRI Eq. (33)-(37) further
describes water potential, Darcy/Richards transport, and root sinks; those
PDE/layer mechanics remain outside the V3 one-layer contract.

The root equations Eq. (57)-(60) use layer-distributed first-order rates
linked to plant uptake and soil-compartment hydrogen content. A rate in
`s^-1` is not automatically the V3 `k_root` in `m s^-1`; the current
one-layer effective velocity therefore remains a conceptual analogue.

### Food, intake, and dose

UFOTRI Eq. (45)-(105) is a continuous plant/grass/cow/milk compartment model
with daily transfer rates, equilibrium assumptions, and explicit boundary
losses. V3 food transfer is a plant-to-food event, so no harvest fraction is
inferred from a UFOTRI transfer rate. UFOTRI Eq. (107) does expose a
consumption-rate role `c_N` and a dose-conversion factor `DF`; these are
scenario/exposure or external/regulatory quantities, not UFOTRI biological
parameters. The V3 generic `D=I*e` role is compatible, while the manual's
HTO treatment of OBT limits any claim of V3 pathway/age equivalence.

## Equation decision summary

| Subsystem | Decision | Boundary |
|---|---|---|
| leaf | direct component mapping | no value or dynamic resistance import |
| TFWT | transformable flux roles plus direct water-basis role | no solver or coupling change |
| OBT | direct first-order roles; conceptual day/night multiplier and photosynthesis | no biological value selection |
| soil | transformable signed transport/water basis; direct layer depth/physical half-life | no Richards/Darcy implementation |
| root | conceptual analogue | no `s^-1` to `m s^-1` coercion |
| food | crop metadata direct; harvest fractions no mapping | no food-chain activation |
| intake | consumption rate direct by time-unit scaling; food mass source unavailable | no diet import |
| dose | generic coefficient role direct, external/non-UFOTRI | no ICRP/regulatory value import |

The full per-parameter record, including equation/unit/compartment/state
relationships, is in the canonical YAML manifest.
