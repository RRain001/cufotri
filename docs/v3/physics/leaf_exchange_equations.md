# V3-P6.2A Leaf-Exchange Equation Contract

Status: `SPECIFICATION_ONLY_NO_RUNNABLE_CODE`

This document freezes symbols, signs, units, and conservation obligations for
a future leaf-exchange implementation. It deliberately does not choose
parameter values, provide interpolation code, or produce numerical results.

## Symbols and bases

| Symbol | Unit | Definition |
|---|---|---|
| `C_air_HTO` | `Bq m^-3` | HTO activity concentration in the atmospheric forcing |
| `C_TFWT` | `Bq kg^-1 water` | Derived TFWT activity concentration |
| `I_TFWT` | `Bq m^-2` | TFWT inventory on the declared plant/leaf area basis |
| `I_OBT` | `Bq m^-2` | OBT inventory on the same area basis |
| `W_p` | `kg water m^-2` | Plant water content on the same area basis |
| `B_p` | `kg dry matter m^-2` | Dry biomass on the same area basis |
| `r_a` | `s m^-1` | Aerodynamic resistance |
| `r_b` | `s m^-1` | Quasi-laminar leaf boundary-layer resistance |
| `r_c` | `s m^-1` | Canopy/stomatal resistance |
| `r_{tot}` | `s m^-1` | Total exchange resistance |
| `g_{ex}` | `m s^-1` | Exchange transfer coefficient, `1/r_{tot}` |
| `F` | `Bq m^-2 s^-1` | Area-normalized activity flux |
| `k_{OBT}` | `s^-1` | TFWT-to-OBT formation rate |
| `k_{loss,OBT}` | `s^-1` | OBT loss rate |
| `K_{eq}` | `kg water m^-3 air` | Temperature/isotope/normalization conversion from air concentration to equilibrium TFWT concentration |

All rates are per declared modeled area. A future implementation must record
whether that area is leaf area, canopy area, or ground area and must not mix
area bases in one balance.

## Air-to-leaf exchange and resistance chain

The UFOTRI manual defines exchange resistance as concentration difference over
water-vapour flux (§2.2.2, Eq. 8) and gives the plant resistance chain

```text
r_tot = r_a + r_b + r_c                         [s m^-1]
g_ex  = 1 / r_tot                                [m s^-1]
```

The source mappings are:

```text
r_a = r_AV                                       [manual Eq. 12]
r_b = r_BV                                       [manual Eq. 13]
r_c = r_ST / L                                   [manual Eq. 14]
```

where `L` is leaf area index. The manual gives `r_AV` from aerodynamic
boundary-layer information (§2.2.2, Eqs. 10, 15–18) and `r_BV` from roughness
lengths or the representative relation

```text
r_BV = 2 / (k u_x)                               [manual Eq. 21]
```

These are source relations to be reviewed, not a validated V3
parameterization. In particular, the future parameter package must define
wind height, canopy geometry, displacement, stability, roughness, humidity,
temperature, radiation/day-night state, crop, growth stage, valid range,
interpolation, and uncertainty.

Let `C_air,eq` be the atmospheric-equivalent concentration of the current
plant-water state. The aggregate signed boundary flux is frozen as

```text
F_air_to_leaf = g_ex (C_air_HTO - C_air,eq)       [Bq m^-2 s^-1]
```

Positive flux is into the plant. Negative flux is plant-to-air exchange. The
equilibrium conversion is represented without hiding unit conversions as

```text
C_TFWT,eq = K_eq C_air_HTO
C_air,eq  = C_TFWT / K_eq
```

For the manual's units and assumptions, the analytical solution of Eq. 27
implies the equivalent relation `C_TFWT,eq = a C_air_HTO / rho`, where `a` is
the liquid/air isotope ratio and `rho` is saturated water-vapour density in
the manual's unit basis. A V3 implementation must explicitly normalize the
manual `pBq ml^-1`, `pBq g^-1`, `g ml^-1`, and resistance units before using
this relation. No such conversion is implemented here.

The diagnostic pathway split is constrained as follows:

```text
F_air_to_leaf = F_stomatal + F_cuticular       [only if a validated split exists]
```

`F_stomatal` and `F_cuticular` are diagnostics or mutually exclusive pathway
components. They must not each be added to `F_air_to_leaf` as independent
external fluxes. The manual explicitly treats stomatal and atmospheric
resistances and notes epidermal exchange when stomata are closed; it does not
provide a complete V3 crop/stage partition table. The partition remains
`REQUIRED_NOT_VALIDATED`.

## Source dynamic equation and V3 inventory form

UFOTRI Eq. 27 is transcribed symbolically as

```text
mu dC/dt = (1/r) (chi - (rho/a) C)
```

with the manual definitions `mu` = plant water content per unit leaf area,
`chi` = air tritium concentration, `C` = tissue-water tritium concentration,
`r` = total resistance, and `t` in seconds. Its constant-input analytical
solution is Eqs. 28–29:

```text
C(t) = chi (a/rho) (1 - exp(-k t))
k     = rho / (a mu r)                       [s^-1]
```

The manual's `r` and concentration bases differ from the canonical V3 SI
contract. The future inventory equation is therefore the contract-level form,
with every term in `Bq m^-2 s^-1`:

```text
dI_TFWT/dt = F_air_to_leaf
              + F_external_root
              - F_TFWT_to_OBT
              - F_TFWT_loss
```

For P6.2A's leaf-only boundary, `F_external_root` is an explicitly declared
external coupling term and is set to zero at the module boundary; it is not a
soil or root implementation. If `W_p` is constant,

```text
dC_TFWT/dt = (1/W_p) [F_air_to_leaf
                       - F_TFWT_to_OBT
                       - F_TFWT_loss]
```

If `W_p` varies, the state contract must include the storage/dilution term:

```text
dC_TFWT/dt = (1/W_p) dI_TFWT/dt
              - (C_TFWT/W_p) dW_p/dt
```

No hidden water-loss term may be inserted to make a balance pass. The manual
states that evaporation is partly represented by its semi-empirical relation;
P6.2B or later must decide whether that is an explicit `F_TFWT_loss` term or a
validated exchange parameterization.

## TFWT-to-OBT formation, loss, and day/night state

The future formation flux is defined as an internal plant transfer:

```text
F_TFWT_to_OBT = k_OBT C_TFWT W_p
               = k_OBT I_TFWT                        [Bq m^-2 s^-1]
```

and the OBT balance is

```text
dI_OBT/dt = F_TFWT_to_OBT - F_OBT_loss - F_OBT_decay
F_OBT_loss = k_loss,OBT I_OBT                       [Bq m^-2 s^-1]
```

`F_OBT_decay` is a declared activity-loss term only if a later contract
requires it; dose calculations are not part of this specification. The
internal formation flux must appear with equal magnitude and opposite sign in
the TFWT balance.

The manual (§2.2.6) states a daily-average OBT formation assumption of
`0.06% h^-1` of actual plant HTO concentration, with an increased daytime and
reduced nighttime value, and a mean OBT loss assumption of `0.3% h^-1`. These
values are recorded in the source audit as assumptions, not imported
parameters. The V3 lookup contract therefore requires:

```text
k_OBT = k_OBT(crop, growth_stage, temperature, humidity, period)
k_loss,OBT = k_loss,OBT(crop, growth_stage, temperature, humidity, period)
```

where `period` is a declared day/night state. No numeric day/night split is
frozen by P6.2A. A later regression case may require the qualitative relation
`k_OBT,day > k_OBT,night`, but it must be backed by an imported, reviewed
parameter package before use.

## Re-emission and conservation

If the aggregate exchange flux is signed as above, the positive outward
re-emission diagnostic is

```text
F_reemission = max(-F_air_to_leaf, 0)              [Bq m^-2 s^-1]
```

The implementation must choose one authoritative boundary representation:
either the signed `F_air_to_leaf` or the positive `F_reemission` plus a separate
positive uptake flux. It must not add both representations to the atmospheric
ledger.

For the leaf-exchange plant domain, the conservation identity is

```text
d(I_TFWT + I_OBT)/dt
  = F_air_to_leaf + F_external_root
    - F_TFWT_loss - F_OBT_loss - F_OBT_decay
```

`F_TFWT_to_OBT` cancels because it is internal. An implementation that reports
nonzero internal formation without equal TFWT and OBT ledger entries fails the
contract. Interval outputs must be the time integrals of the corresponding
rates over the declared forcing interval.

## Equation disposition

| Contract item | Source basis | P6.2A disposition |
|---|---|---|
| Air/plant exchange resistance | Manual §2.2.2, Eqs. 8–14, 26 | Frozen symbolically; no parameter values |
| Aerodynamic resistance | Manual §2.2.2, Eqs. 15–18 | Frozen as a dependency; no implementation |
| Boundary-layer resistance | Manual §2.2.2, Eqs. 19–21 | Frozen as a dependency; no implementation |
| Stomatal/canopy path | Manual §2.2.2, Eqs. 9, 11, 14 | Frozen as a dependency; crop/stage table missing |
| TFWT dynamic equation | Manual §2.2.2, Eq. 27 | Frozen in source and V3 inventory forms |
| Constant-forcing solution | Manual §2.2.2, Eqs. 28–30 | Traceability only; no runnable solver |
| Re-emission | Manual §2.2.2, Eq. 31 and Eq. 32 | Signed/positive output boundary frozen; source Eq. 32 needs resolution |
| TFWT-to-OBT | Manual §2.2.6 and §3.3.1 | Internal balance frozen; rates remain required and unvalidated |
| Day/night behavior | Manual §2.2.2 and §2.2.6 | State label required; numeric split missing |
| Conservation | V3 flux/state contract | Acceptance obligation for P6.2B, not tested with a solver here |

```ini
LEAF_EXCHANGE_EQUATIONS = FROZEN_SYMBOLIC_ONLY
LEAF_EXCHANGE_NUMERICAL_SOLVER = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
```
