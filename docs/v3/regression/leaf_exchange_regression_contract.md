# V3-P6.2B Leaf-Exchange Regression Contract

Status: `P6_2B_BENCHMARK_SPECIFICATION_ONLY`

This document freezes future benchmark cases and acceptance logic. P6.2A does
not implement or execute a leaf-exchange solver, so this file contains no
results, fitted values, tolerance numbers, or baseline artifacts.

## Common contract

Each future case must declare:

- crop and growth stage;
- initial `PlantState`, including `tfwt_inventory_bq_m2`, `obt_inventory_bq_m2`,
  `biomass_dry_kg_m2`, and `water_content_kg_m2`;
- an explicitly timestamped UTC `AtmosphericHTOForcing` sequence;
- temperature (`K`), relative humidity (fraction), radiation/day-night state,
  wind/boundary information, and their provenance;
- every parameter package hash, lifecycle status, interpolation rule, and
  uncertainty representation;
- output rates and interval changes with their area basis and sign convention.

The reference calculation must be independent of the production implementation
and must not derive expected values by calling the system under test. The
future acceptance record will include:

```text
finite outputs                         = required
non-negative inventories                = required
air/leaf/OBT ledger conservation       = required
declared sign convention               = required
deterministic serialization/hash        = required
comparison tolerance                    = declared by case before execution
```

Tolerance definition is frozen as a method, not a number: each case must state
an absolute tolerance for near-zero quantities and a relative tolerance for
nonzero quantities, together with the independent reference precision and the
reason for the tolerance. No tolerance is silently inherited from V1/V2.

## Case A — constant air concentration

**Purpose:** verify uptake under a constant positive atmospheric HTO forcing.

**Input contract:**

- constant finite `C_air_HTO > 0` for the full forcing interval;
- fixed temperature and humidity within the declared parameter domain;
- a declared daytime state with valid radiation/day-night metadata;
- positive initial plant water content and finite initial TFWT/OBT inventories;
- no root or soil transfer in the isolated leaf-exchange case;
- one fixed crop/growth-stage lookup point or a declared interpolation path.

**Expected qualitative behavior:**

- aggregate net `F_air_to_leaf` is positive while the plant state is below its
  equilibrium state;
- `leaf_TFWT_change` is positive over the uptake interval;
- TFWT-to-OBT formation, if enabled by the reviewed test parameter package,
  appears as an equal internal TFWT loss and OBT gain;
- conservation residual meets the case tolerance.

No numerical trajectory or final value is defined in P6.2A.

## Case B — air concentration falls to zero

**Purpose:** verify plant-to-air re-emission after a positive TFWT state is
established.

**Input contract:**

- a first interval with positive air concentration to establish a nonzero
  plant state, followed by an interval with `C_air_HTO = 0`;
- fixed temperature/humidity and a declared day/night state in each interval;
- positive initial TFWT inventory at the start of the zero-air interval;
- no root or soil transfer in the isolated leaf-exchange case.

**Expected qualitative behavior:**

- the signed aggregate exchange becomes negative when plant-equivalent
  concentration exceeds air concentration;
- `leaf_reemission` is positive and is not also counted as a second negative
  boundary flux;
- TFWT decreases through the outward boundary and any separately declared
  internal transformation/loss terms;
- the ledger remains closed within the case tolerance.

No numerical trajectory or re-emission magnitude is defined in P6.2A.

## Case C — day/night exchange contrast

**Purpose:** verify that the declared day/night parameter state changes the
exchange response in the intended direction.

**Input contract:**

- the same crop, growth stage, air concentration, temperature/humidity, and
  plant initial state for paired daytime and nighttime intervals;
- radiation/day-night metadata sufficient to select the two declared states;
- a reviewed parameter package with an explicit day/night resistance or
  transfer-coefficient distinction;
- no hidden soil/root forcing and no change of area basis between intervals.

**Expected qualitative behavior:**

- the magnitude of the daytime exchange response is greater than the nighttime
  response under otherwise paired conditions;
- the comparison uses the same sign convention and interval duration;
- any OBT formation contrast is reported separately from the air/leaf exchange
  contrast;
- both paired runs satisfy conservation and finiteness checks.

The relation `exchange_day > exchange_night` is a benchmark expectation, not a
numeric UFOTRI parameter claim. If a future evidence package does not support
it for a crop/stage domain, the case must fail closed rather than invert the
parameter silently.

## P6.2A boundary

```ini
LEAF_EXCHANGE_REGRESSION_CASES = SPECIFIED_A_B_C
LEAF_EXCHANGE_REGRESSION_RESULTS = NOT_EXECUTED
LEAF_EXCHANGE_NUMERICAL_IMPLEMENTATION = FALSE
NEXT_PHASE = P6_2B
```
