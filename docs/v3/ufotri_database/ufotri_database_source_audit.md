# V3-P6.1 UFOTRI database source audit

## Scope and verdict

This is a source and data-shape audit for the future UFOTRI parameter database.
It does not import a numerical UFOTRI parameter set, implement leaf exchange,
change the atmosphere, change the soil solver, or change dose.

The primary physical source is `ufotri_manual.md`, the local reviewed text of:

> W. Raskob, *UFOTRI: Program for Assessing the Off-Site Consequences from
> Accidental Tritium Releases*, KfK 4605.

The existing source-registry identifier `UFOTRI_VALIDATED` is only a reserved
source identifier. Its registry status is `external_reference_required` and
`production_allowed: false`; the identifier must not be read as evidence that
any value is validated.

The audit classifications below describe the source record, not the database
lifecycle. In particular, `EXPLICIT_FROM_UFOTRI` means that the manual states a
value or relation. It does not mean experimentally validated for every crop,
site, season, or environmental condition.

## Parameter and relation audit

| Classification | Parameter or relation | Unit in source | Crop / vegetation | Growth stage | Environmental condition / domain | Uncertainty and limitation | Source location |
|---|---|---|---|---|---|---|---|
| `EXPLICIT_FROM_UFOTRI` | Plant HTO loss half-time, about 1 h daytime; night exchange reduced and represented by a doubled half-time | h | Nutrient plants; grass is treated separately | Vegetation-period mean; day/night split | Mean diffusive resistance; stomata normally closed at night | Measurement/model combination; no crop-specific distribution or uncertainty law | Manual §2.2.2, p. 13; §3.3.1, Eq. (46), p. 34 |
| `EXPLICIT_FROM_UFOTRI` | Plant water mass, 0.4 kg m-2; hydrogen content 0.044 kg m-2 | kg m-2 | Nutrient plants | Vegetation-period equilibrium | Plant compartment assumption | Explicit model assumption tied to the compartment setup, not a universal crop value | Manual §3.3.1, Eqs. (46)-(47), p. 34 |
| `EXPLICIT_FROM_UFOTRI` | Grass inorganic water mass range 0.4-1.2 kg m-2; selected mean 0.6 kg m-2; organic mass selected 0.15 kg m-2 | kg m-2 | Grass / pasture | Vegetation-period equilibrium | Plant water content 80%; wet weight 0.5-1.5 kg m-2 | Range and selected mean are a model parameterization; no uncertainty distribution supplied | Manual §3.4.1, p. 43 |
| `EXPLICIT_FROM_UFOTRI` | Plant-water to atmospheric-water specific-activity ratio 0.5 | dimensionless | Nutrient plants and grass subsystem | Vegetation period | Uncontaminated soil; assumed air humidity 8 g m-3 and mixing height 1000 m | Based on measurements cited by the manual, but applicability across crops and conditions is not quantified | Manual §3.3.1, Eq. (47), p. 34; §3.4.1, Eq. (69), p. 43 |
| `EXPLICIT_FROM_UFOTRI` | HTO dry-deposition velocity 0.005 m s-1 | m s-1 | Not crop-dependent | Not applicable | Mean deposition condition | Manual says derived from many measurements; no dataset, spread, or site transfer rule is included | Manual §3.3.1, Eq. (48), p. 34 |
| `EXPLICIT_FROM_UFOTRI` | Deepest-soil loss rate `t13,13 = 8.2e-3 d-1` | d-1 | Nutrient-plant soil subsystem; reused for grass subsystem | Not a biological growth stage | Three soil layers, 15-30 cm deepest layer | Taken from an English COMA version and cited measurements; source uncertainty is not structured | Manual §3.3.1, Eq. (45), p. 34; §3.4.2, Eq. (67), p. 46 |
| `EXPLICIT_FROM_UFOTRI` | Root-uptake distribution 20% / 40% / 40% over 0-5 / 5-15 / 15-30 cm | fraction | Agricultural / nutrient plants | Vegetation-period equilibrium | Root zone to 30 cm | Based on lysimeter results, model hypothesis, and assumptions; not a crop-specific validated table | Manual §2.2.5, p. 29; §3.3.2, Eqs. (57)-(60), p. 38 |
| `EXPLICIT_FROM_UFOTRI` | Root-uptake distribution 40% / 60% over the first two grass-root-zone layers | fraction | Grass / pasture | Vegetation-period equilibrium | Grass root zone; three soil layers represented | Explicit model assumption; no uncertainty or crop transfer rule | Manual §3.4.2, p. 46 |
| `EXPLICIT_FROM_UFOTRI` | Daily-average OBT formation rate 0.06% h-1; mean OBT loss rate 0.3% h-1 | h-1 | Plants; later food-chain compartments | Day/night values are to be split, but the split is not numerically specified here | Actual plant HTO concentration; photosynthesis day/night distinction | Manual cites measurement ranges and chooses rates; no formal uncertainty distribution or crop-stage table | Manual §2.2.6, p. 29 |
| `DERIVED_FROM_UFOTRI` | Plant-to-atmosphere transfer rate `t14,1 = 8.3 d-1` | d-1 | Nutrient plants | Vegetation-period day/night average | Derived from half-time and plant compartment mass | Derived value is conditional on the selected half-time and mass; it must not be stored as an independent validated scalar | Manual §3.3.1, Eq. (46), p. 34 |
| `DERIVED_FROM_UFOTRI` | Atmosphere-to-plant transfer rate `t1,14 = 0.205 d-1` | d-1 | Nutrient plants | Vegetation-period equilibrium | Ratio 0.5, plant hydrogen mass, atmospheric hydrogen mass | Derived from Eq. (47); dependent on fixed humidity and mixing-layer assumptions | Manual §3.3.1, Eq. (47), p. 34 |
| `DERIVED_FROM_UFOTRI` | Soil/plant transfer rates `t11,14`, `t12,14`, `t13,14` | d-1 | Nutrient plants | Vegetation-period equilibrium | 25% volumetric water content; 0-30 cm, three layers | Derived from total uptake, layer hydrogen mass, and 20/40/40 distribution | Manual §3.3.2, Eqs. (57)-(60), p. 38 |
| `DERIVED_FROM_UFOTRI` | Grass atmosphere/plant/soil transfer rates `t5,1`, `t1,5`, `t1,2`, `t2,1` | d-1 | Grass / pasture | Vegetation-period equilibrium | 8 g m-3 atmospheric water, 1000 m mixing height, grass mass assumptions | Derived values are tied to the selected grass parameterization and equilibrium construction | Manual §3.4.1, Eqs. (68)-(72), p. 43 |
| `DERIVED_FROM_UFOTRI` | Actual evapotranspiration and soil re-emission relation, including `alpha`, `REEM`, `DIFF`, `ZT` | kg m-2 s-1; fraction per time | Sparse vegetation / short-rooted plants in the stated domain | Depends on release time and day/night condition | Radiation, vapour-pressure terms, soil water content, downward flux, HT fraction, time since release | Formula exists, but constants, applicability, and uncertainty are not a complete crop/stage lookup database | Manual §2.2.3, Eqs. (38)-(43), p. 22; §2.2.4, Eqs. (44-1)-(44-2), p. 26 |
| `ASSUMPTION` | Crop taxonomy mapping from manual “nutrient plants” / “grass” to project crop identifiers | dimensionless key | Current manual categories do not enumerate project crop IDs | No formal stage vocabulary | Project-specific crop configuration | Must not be silently inferred; mapping requires a reviewed decision record | Manual §§3.3-3.4, pp. 34-48 |
| `ASSUMPTION` | Growth-stage dimension and stage labels | dimensionless key | Not specified as a UFOTRI lookup axis | Only vegetation-period and day/night language is explicit | Seasonal/stage dependence not parameterized | Schema supports the axis, but no stage values are imported in P6.1 | Manual §§2.2.2, 2.2.6, 3.3.1, pp. 13, 29, 34 |
| `ASSUMPTION` | Temperature and relative-humidity lookup axes for leaf exchange | K and 0-1 if later frozen | Not specified as a table | Not specified | Manual examples use fixed/mean humidity and vegetation-period conditions | No UFOTRI temperature/humidity response table or interpolation rule is present in the audited source | Manual §§2.2.2-2.2.3, pp. 13-22; §3.3.1, p. 34 |
| `ASSUMPTION` | Interpolation and extrapolation policy | method metadata | All crops/stages if later tabulated | All stages if later tabulated | Environmental axes if later tabulated | No policy in the manual; P6.1 schema permits `linear` interpolation but rejects extrapolation | P6.1 database contract; no manual value claimed |
| `MISSING` | Crop × growth-stage × temperature × humidity lookup cells for leaf exchange resistance or exchange coefficients | parameter-specific | Missing | Missing | Missing | No complete source table, coverage, cell provenance, or uncertainty distribution available | P5.2 capability audit; manual §§2.2.2-2.2.3 |
| `MISSING` | Structured uncertainty distributions and covariance for the above parameters | parameter-specific | Missing | Missing | Missing | Manual ranges and qualitative caveats cannot be promoted to machine-readable uncertainty without a separate review | Manual §§2.2.2-2.2.6 and cited references |

## Database contract prepared by P6.1

The migration schema now accepts a typed table entry with the following shape:

```yaml
parameter_id: leaf_exchange.example_table_parameter
type: table
dimensions: [crop, growth_stage, temperature, humidity]
axes:
  crop: {unit: "1", values: [grass, nutrient_plant]}
  growth_stage: {unit: "1", values: [vegetative, mature]}
  temperature: {unit: K, values: [293.15, 303.15]}
  humidity: {unit: "1", values: [0.4, 0.8]}
interpolation: linear
extrapolation: reject
lookup_table:
  - coordinates:
      crop: grass
      growth_stage: vegetative
      temperature: 293.15
      humidity: 0.4
    value: 0.0
```

The surrounding P5.1 fields remain mandatory: `unit`, `source`,
`source_type`, `reference`, `uncertainty`, `status`, and `notes`. The source
identifier is resolved through `parameters/parameter_sources.yaml`; the
registry's `UFOTRI_VALIDATED` entry is not production-approved. `linear`
lookup is multilinear over numeric axes, categorical axes are exact matches,
and out-of-domain coordinates fail closed.

The example above is a schema illustration only. P6.1 adds no UFOTRI table
file and no numerical UFOTRI value to the runtime. The only table values used
by the new tests are synthetic fixtures explicitly marked `TEST_ONLY`.

## Lifecycle and final boundary

```text
PLACEHOLDER -> CANDIDATE -> REVIEWED -> VALIDATED -> ACTIVE
```

P6.1 permits table metadata and review records through `REVIEWED` only. No
UFOTRI table is `VALIDATED` or `ACTIVE`, and `production=True` requires the
existing validated source/entry checks plus an `ACTIVE` migration record.

```ini
P6_1_STATUS = PASS_DATABASE_READY
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
LEAF_EXCHANGE_IMPLEMENTATION = FALSE
NEXT_PHASE = P6_2_LEAF_EXCHANGE_PHYSICS
```

Manual values remain source-audited or derived/assumed records. They are not
called validated in this phase; manual values are not validated by P6.1.
