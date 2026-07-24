# UFOTRI manual extraction and implementation scope

Primary source: repository-root `ufotri_manual.md`.

## Chemical and compartment scope

The manual secondary model includes atmospheric HT and HTO, soil conversion of
deposited HT to HTO, vegetation, re-emission, deeper soil, OBT, animals, food
chains, inhalation, ingestion, and dose. This project release intentionally
solves only the HTO environmental core:

```text
primary HTO plume
→ topsoil HTO
→ plant TFWT
↔ plant non-exchangeable OBT
→ soil/plant HTO re-emission
→ secondary atmospheric area source
```

HT atmospheric oxidation is excluded because the manual also treats it as slow.
The manual's `v_d,HT X_HT` soil source, the HT-specific `C2` re-emission
correction, animals, food chains, and dose are documented boundaries, not silent
zero-valued implementations.

## Symbol conflict resolved

Manual Eq. (1)-(3) calls the soil and plant areal activities
`C_{S,HTO}` and `C_{P,HTO}` with units Bq m-2. In this code, `C` is reserved
for volumetric concentration:

| Manual symbol | Unified symbol | Code | Unit |
|---|---|---|---|
| `X_HTO` | `Ca` | `air_hto_concentration_bq_m3` | Bq m-3 |
| `C_{S,HTO}` | `Ms` | `soil_hto_bq_m2` | Bq m-2 |
| derived | `Cs=Ms/Ws` | `soil_hto_concentration` | Bq m-3 water |
| `C_{P,HTO}` | `Mp` | `plant_tfwt_bq_m2` | Bq m-2 |
| derived | `Cp=Mp/Wp` | `plant_tfwt_concentration` | Bq m-3 water |
| plant OBT compartment | `Mobt` | `plant_obt_bq_m2` | Bq m-2 |

This mapping is mandatory; the manual's areal inventory must never be passed to
an API expecting water concentration.

## State variables and initial conditions

| State | Initial source | Constraint |
|---|---|---|
| `Ws` | `soil.initial_water_m` | minimum through maximum water storage |
| `Ms` | clean-start zero in `State` | non-negative Bq m-2 |
| `Mp` | clean-start zero in `State` | non-negative Bq m-2 |
| `Mobt` | clean-start zero in `State` | non-negative Bq m-2 |

`Wp` is a configured constant in the first version, not a dynamic state.
Non-clean initial inventories can be passed through `State`.

## Diagnostic variables

- `Ca`, `Cs=Ms/Ws`, `Cp=Mp/Wp`
- RH, VPD, saturation-pressure slope, wind speed/direction, stack-height wind
- potential ET, potential soil evaporation, moisture factor
- `Es`, `Tp`, `Us`, `Ls`, runoff
- primary and secondary air concentration
- soil, plant, and total re-emission flux
- absolute and relative HTO mass-balance residual

## Meteorological and external inputs

Required forcing is air/dew-point temperature (K), 10 m wind components or
speed/direction (m s-1/degrees from north), precipitation rate (m s-1), and net
radiation (W m-2). Optional inputs are rainwater HTO concentration, boundary
layer height, cloud cover, and true ERA5 net radiation components. Time is UTC;
conversion to local civil time is presentation-only.

## Implemented manual anchors

- Eq. (1)-(3): rewritten as areal HTO inventories with explicit water
  concentrations and HTO-only sources.
- Eq. (4): rectangular uniform area-source integration by midpoint quadrature.
- Eq. (6): reflected Gaussian point source.
- Eq. (25): configurable rural wind power profile.
- Eq. (38)-(43): Penman/equilibrium radiation route, LAI shading, soil-moisture
  reduction, actual soil evaporation and transpiration.
- Eq. (44-1)/(44-2): optional, explicitly provisional REEM/DIFF/ZT
  reconstruction; basic activity mass flux is the default.
- Manual OBT text: configurable daily-average formation, day/night multipliers,
  and turnover.

## Inputs and parameters

All site/source, atmospheric, soil, plant, re-emission, physical, and numerical
parameters are centralized in `configs/default_parameters.yaml` and
`configs/test_case.yaml`. The calculation modules contain physical constants
only where they define an algorithm (for example standard gravity and Earth
radius), not case values.

## Day/night and time logic

- Piecewise forcing is hourly; the internal default step is 600 s.
- Re-emission feedback is lagged one internal step.
- Day is diagnosed from positive net radiation.
- OBT uses configured day/night multipliers whose equal 12 h mean is the
  configured daily-average rate.
- Root HTO uptake can be immediate (`Us=Tp`, default) or delayed by a configured
  integral number of steps, including the manual's three-hour option.
- Empirical ZT decreases exponentially with time after release.

## Explicitly deferred manual content

Multi-layer Richards/Darcy soil transport, HT chemistry, exchange resistance,
dynamic vegetation/phenology, animals, food-chain transfer Eq. (45)-(105), and
dose Eq. (106)-(107) are outside the requested minimal environmental system.
Their absence must not be represented as full-formula UFOTRI equivalence.

## Formal minimal baseline v1 contracts

- Conservation is limited to the surface soil + TFWT + OBT box.
- Atmosphere is a steady Gaussian source/sink ledger, not dynamic inventory.
- Calm wind uses a recorded 0.5 m s-1 minimum-effective default.
- Dry fallout is a project simplification; wet washout is absent.
- The one-layer root fraction is 1.0; Eq. (40) shades radiation only.
- Feedback uses an authoritative rectangle and a 3600 s delay.
