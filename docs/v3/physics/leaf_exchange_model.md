# V3-P6.2A Leaf-Exchange Model Specification

Status: `DESIGN_ONLY_NOT_IMPLEMENTED`

This document freezes the boundary and data contract for a future V3 leaf
exchange module. It does not implement a solver, import a parameter, enable a
runtime path, or change the existing V1/V2 plant calculations.

## Scope boundary

The future module covers direct atmospheric HTO exchange with plant leaf water,
TFWT-to-OBT transformation, and reporting of plant re-emission. Root uptake,
soil transport, atmospheric dispersion, dose, and food-chain calculations are
outside this module. They may provide or consume explicitly owned interface
terms in a later phase, but they are not implemented by P6.2A.

The existing V2 implementation in
`src/cteas_ufotri/plant/leaf_exchange.py` remains unchanged. The P6.2A
`LeafExchangeModule` below is a future V3 design name, not an import of that
implementation.

## PlantState

`PlantState` is a future V3 state record. Every quantity must carry its area,
water, time, and activity basis in the serialized contract; the names below
make the intended basis explicit.

| Field | Unit | Meaning and invariant |
|---|---|---|
| `tfwt_inventory_bq_m2` | `Bq m^-2` | Tissue-free-water-tritium inventory on the declared plant/leaf area basis; finite and non-negative |
| `obt_inventory_bq_m2` | `Bq m^-2` | Organic-bound-tritium inventory on the same declared area basis; finite and non-negative |
| `biomass_dry_kg_m2` | `kg dry matter m^-2` | Dry biomass basis used for any future OBT normalization; finite and non-negative |
| `water_content_kg_m2` | `kg water m^-2` | Plant water inventory used to relate activity concentration to TFWT inventory; finite and strictly positive when a concentration is evaluated |
| `crop` | controlled identifier | Crop class; required for a future table lookup, not a free-form parameter value |
| `growth_stage` | controlled identifier | Growth-stage label; required for a future table lookup |
| `area_basis` | metadata | Declares whether the state is per leaf area, canopy area, or modeled ground area |
| `time` | timezone-aware UTC timestamp | State time at the end of the forcing interval |
| `version` | string | State schema/version identifier |

The derived TFWT concentration is defined only when
`water_content_kg_m2 > 0`:

```text
C_TFWT = tfwt_inventory_bq_m2 / water_content_kg_m2
```

The concentration unit is `Bq kg^-1 water` (numerically compatible with
`Bq L^-1` only after the density convention is stated). `C_TFWT` is a derived
view, not an additional independently updated inventory. `PlantState` does
not silently include soil, root, dose, or edible-product state.

This future record is compatible with the existing V3 state/flux contract
requirements for physical medium, activity form, unit, normalization, time
basis, inventory/diagnostic status, and version. It does not replace the
current V1/V2 `coupling.state.State` dataclass in this phase.

## AtmosphericHTOForcing

The future module consumes the P5.3 frozen atmospheric forcing interface. The
canonical field names and units are:

| Field | Required | Unit / constraint |
|---|---:|---|
| `time` | yes | timezone-aware UTC timestamp; sequence strictly increasing with declared cadence |
| `air_hto_concentration` (`C_air_HTO`) | yes | `Bq m^-3`, finite and non-negative |
| `air_temperature` | yes | `K`, finite and positive |
| `relative_humidity` | yes | fraction in `[0, 1]` |
| `precipitation` | no | `m s^-1`, non-negative |
| `shortwave_radiation` | no | `W m^-2`, non-negative |
| `longwave_radiation` | no | net `W m^-2`, with sign convention in provenance |
| `wind_speed` | no | `m s^-1`, non-negative |
| `boundary_layer_height` | no | `m`, positive |
| `surface_deposition_flux` | no | `Bq m^-2 s^-1`, non-negative |
| `provenance` | yes | source id/version, artifact hash, spatial reference, temporal resolution |

Missing required fields, unavailable required optional inputs, non-monotonic
time, duplicate timestamps, undeclared gaps, or invalid values are
fail-closed conditions. The module must not repair them with hidden defaults,
nearest-time values, or synthetic weather. Dispersion-model identity and
calculation are not part of this forcing consumer contract.

## Module flow

```text
AtmosphericHTOForcing
        |
        v
LeafExchangeModule  [future V3 interface; not implemented in P6.2A]
        |
        +--> PlantState(next)
        +--> LeafExchangeFlux [future typed diagnostic/boundary product]
        +--> leaf_TFWT_change
        +--> leaf_OBT_change
        +--> leaf_reemission
```

The module inputs are explicitly:

1. `C_air_HTO`: atmospheric HTO activity concentration;
2. humidity: relative humidity and, where required by the frozen parameter
   relation, the derived water-vapour state;
3. temperature: air temperature for the saturation and parameter axes;
4. radiation/day-night: shortwave radiation and a declared day/night rule;
5. wind/boundary information: wind speed, boundary-layer height, and the
   declared canopy/measurement geometry needed by a resistance chain.

These are inputs to a future module interface, not permission to infer missing
parameter values. Crop, growth stage, temperature, and humidity lookup axes
must be resolved by the future parameter package with explicit interpolation,
extrapolation, missing-cell, uncertainty, and lifecycle rules.

## Outputs and ownership

The future output record must distinguish rates from interval changes:

| Output | Unit | Sign / ownership |
|---|---|---|
| `leaf_TFWT_change` | `Bq m^-2` per forcing interval | Net change in `tfwt_inventory_bq_m2`; includes only terms declared by the module boundary |
| `leaf_OBT_change` | `Bq m^-2` per forcing interval | Net change in `obt_inventory_bq_m2` caused by formation and loss terms declared by the module |
| `leaf_reemission` | `Bq m^-2 s^-1` and interval-integrated `Bq m^-2` | Positive outward plant-to-air boundary flux; must not be double counted with a signed net exchange field |
| `air_to_leaf_flux` | `Bq m^-2 s^-1` | Positive into plant; the only external atmospheric boundary flux owned by this module |
| `tfwt_to_obt_flux` | `Bq m^-2 s^-1` | Internal plant transfer; appears as TFWT loss and OBT gain with equal magnitude |

The exact signed-versus-positive reporting representation is frozen in the
equation contract and must be kept consistent with the V3 flux contract. Root
uptake, soil-to-plant transfer, soil re-emission, atmospheric transport,
inventory dose, and food-chain outputs are not produced here.

## Lifecycle and non-activation rule

This specification may define required parameter names and dimensions, but it
does not create a database record. No parameter can enter `ACTIVE` from this
document. The lifecycle remains:

```text
PLACEHOLDER -> CANDIDATE -> REVIEWED -> VALIDATED -> ACTIVE
```

P6.2A stops at a design specification. Experimental evidence, uncertainty,
and independent review are prerequisites for later transitions. The current
default model remains unchanged and leaf exchange remains disabled in the
default configuration.

```ini
LEAF_EXCHANGE_MODULE = DESIGN_ONLY
PLANT_STATE_CONTRACT = SPECIFIED_NOT_IMPLEMENTED
ATMOSPHERIC_HTO_FORCING = SPECIFIED_NOT_IMPLEMENTED
LEAF_EXCHANGE_IMPLEMENTATION = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
```
