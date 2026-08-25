# V3 P7.6C-2 parameter mapping report

```text
MAPPED_V3_PARAMETERS = 26
DIRECT_MAPPING = 12
TRANSFORMABLE_MAPPING = 4
CONCEPTUAL_ANALOGUE = 6
NO_MAPPING = 3
SOURCE_UNAVAILABLE = 1
NEW_VALIDATION_CANDIDATES = 0
```

The canonical record set is sorted by `mapping_id` in
`docs/v3/parameter_evidence/ufotri_parameter_mapping.yaml`. Every listed
parameter is a current deferred V3 model/biological/soil parameter, or the
already validated P7.6C-1 physical half-life. Scenario-only identifiers and
test fixtures are intentionally outside this mapping set.

## Decision matrix

| Parameter | Current status | UFOTRI mapping | Equation match | Unit match | Compartment/state | Transformation | Next action |
|---|---|---|---|---|---|---|---|
| `dose.dose_coefficient` | PROVISIONAL | `DF`, Eq. (106)-(107) | compatible role | exact | compatible exposure role | none | keep external/regulatory; no import |
| `food.crop` | PROVISIONAL | representative plant/vegetable identity | compatible metadata role | exact | compatible | none | retain metadata only |
| `food.harvest_fraction` | PROVISIONAL | no event fraction | incompatible | N/A | incompatible event basis | blocked | future V3 food-event evidence |
| `food.tfwt_harvest_fraction` | PROVISIONAL | no separate event fraction | incompatible | N/A | incompatible event basis | blocked | future V3 food-event evidence |
| `intake.annual_consumption_amount` | PROVISIONAL | `c_N`, Eq. (107) | compatible role | day-to-year scale | compatible scenario | unit scale only | keep as scenario input |
| `intake.food_product_mass` | PROVISIONAL | original definition unavailable | unknown | unknown | unknown | blocked | recover original definition or declare V3 extension |
| `leaf.crop` | PROVISIONAL | vegetation/crop identity | compatible metadata role | exact | compatible | none | metadata only |
| `leaf.growth_stage` | PROVISIONAL | vegetation-period/canopy context | compatible mechanism | N/A | state transfer required | blocked | define stage ontology before evidence recovery |
| `leaf.r_a` | PROVISIONAL | Eq. (12) `r_a=r_aV` | exact role | exact | exact | none | future resistance evidence recovery |
| `leaf.r_b` | PROVISIONAL | Eq. (13) `r_b=r_bV` | exact role | exact | exact | none | future boundary-layer evidence recovery |
| `leaf.r_c` | PROVISIONAL | Eq. (14) `r_c=r_ST/L` | exact role | exact | exact | none | future canopy evidence recovery |
| `obt.daylight_multiplier` | PROVISIONAL | day/night OBT formation split | conceptual | transfer required | transfer required | blocked | define V3 normalization |
| `obt.kf` | PROVISIONAL | `V_P`/`t_14,15`, Eq. (3),(66) | exact first-order role | day-to-second scale | compatible plant compartments | unit scale | review crop/equilibrium applicability |
| `obt.kr` | PROVISIONAL | `t_15,14`/`t_6,5`, Eq. (65),(105) | exact first-order role | day-to-second scale | compatible but mixed OBT pools | unit scale | resolve turnover allocation |
| `obt.nighttime_multiplier` | PROVISIONAL | day/night OBT formation split | conceptual | transfer required | transfer required | blocked | define V3 normalization |
| `obt.photosynthetic_activity` | PROVISIONAL | photosynthesis mechanism text | conceptual | unknown | compatible mechanism | blocked | future biological model design |
| `obt.plant_mass` | PROVISIONAL | plant/hydrogen compartment masses | compatible diagnostic role | transfer required | state basis transfer | blocked | define fresh-plant denominator |
| `obt.temperature` | PROVISIONAL | no OBT-specific relation | incompatible | incompatible | incompatible | blocked | no mapping until an equation exists |
| `root.k_root` | PROVISIONAL | `U_P`/layer rates, Eq. (57)-(60) | compatible mechanism | rate vs velocity differs | multi-layer mismatch | blocked | future effective-velocity contract |
| `soil.layer_depth` | PROVISIONAL | 0-5/5-15/15-30 cm layers | compatible | cm-to-m | compatible selected layer | unit scale | select layer explicitly |
| `soil.transport_flux` | PROVISIONAL | `F_S`, Eq. (2) | compatible flux role | exact | boundary orientation required | sign/orientation | preserve signed V3 interface |
| `soil.tritium_half_life` | VALIDATED | H-3 half-life, Sec. 4.1 | compatible physical role | year-to-second | compatible physical decay | unit scale | preserve P7.6C-1 validation |
| `soil.water_content` | PROVISIONAL | `BODWA`/`Theta`, Eq. (33)-(44) | compatible water basis | mass/fraction to depth | layer basis required | water-depth transform | recover basis metadata |
| `tfwt.transformation_flux` | PROVISIONAL | `V_P C_P`, Eq. (3) | compatible flux role | rate to flux | compatible plant pool | rate times inventory | future explicit flux recovery |
| `tfwt.water_content` | PROVISIONAL | `mu`, Eq. (27) | exact water role | g cm^-2 to kg m^-2 | area basis required | unit/area scale | verify leaf/plant area basis |
| `tfwt.water_loss_flux` | PROVISIONAL | `T_P C_P`, Eq. (3) | compatible flux role | rate to flux | compatible plant pool | rate times inventory | future explicit loss recovery |

## Status interpretation

`DIRECT_MAPPING` means semantic identity with at most an explicit unit scale;
it is not evidence found, validation, or activation. `TRANSFORMABLE_MAPPING`
is reserved for the four records whose algebraic transformation is written in
the record and does not require a fitted or guessed coefficient.
`CONCEPTUAL_ANALOGUE`, `NO_MAPPING`, and `SOURCE_UNAVAILABLE` are blocked from
validation admission. The manifest nevertheless records them so that a later
stage cannot silently reinterpret a missing or incompatible quantity as a
positive mapping.
