# V3 P7.6C-2 UFOTRI gap analysis

```text
GAP_ANALYSIS_STATUS = PASS_FAIL_CLOSED
PRODUCTION_PARAMETER_VALUES_SELECTED = 0
UFOTRI_RUNTIME_IMPORT = FALSE
CALIBRATION_STARTED = FALSE
```

## Remaining gaps by subsystem

| Subsystem | Blocking gap | Why it cannot be guessed | Safe follow-up |
|---|---|---|---|
| leaf | no recovered value provenance for `r_a/r_b/r_c`; growth-stage ontology differs | resistance values depend on crop, geometry, wind, LAI, and interval | recover source-specific resistance evidence and preserve Eq. (12)-(14) |
| TFWT | source rates must become public V3 activity fluxes | the conversion needs the matching areal state and declared sign/boundary | recover state-basis metadata and audit rate-times-inventory derivations |
| OBT | exchangeable/non-exchangeable pools, day/night normalization, and crop dependence are mixed | an equilibrium rate or 0.06%/h statement is not automatically V3 `kf`/multiplier evidence | define a reviewed pool and normalization contract before candidates |
| soil | UFOTRI water basis and hydraulic/multi-layer transport differ from V3 one-layer interfaces | `BODWA`, `Theta`, and signed flux have different bases; source hydraulic equations are not implemented | recover layer/storage metadata; keep transport as an external signed flux |
| root | UFOTRI rates are `s^-1` and layer/transpiration dependent; V3 `k_root` is `m s^-1` | multiplying by an unselected water depth or aggregating layers would be an assumed conversion | design an effective-velocity mapping only after layer and water-basis freeze |
| food | continuous plant/animal/milk chain versus V3 harvest event | transfer rates cannot supply an event fraction without a harvest model | recover an explicit harvest/product contract or keep V3 boundary isolated |
| intake | original product-mass denominator not recovered | manual specific concentration does not identify the V3 `m_food` definition | recover source software/data schema or document a V3 extension |
| dose | manual `DF` is selected/external and treats OBT like HTO | no claim of age/pathway/regulatory equivalence is justified | maintain versioned external dose data outside UFOTRI mapping |

## Control-plane disposition

The gap set is complete for the 26 mapped parameters. No gap is resolved by a
default, inferred numerical conversion, calibration, or benchmark output.
The source-unavailable record is limited to the exact original definition of
`intake.food_product_mass`; it does not downgrade the availability of the
manual itself.

The following remain frozen from P7.6C-1 and are not reopened by this stage:

```text
SOIL_TRITIUM_HALF_LIFE = VALIDATED
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
NEW_VALIDATION_CANDIDATES = 0
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

## Explicit non-actions

P7.6C-2 does not modify `plant/`, `soil/`, `exposure/`, `coupling/`, or the
V3 pipeline. It does not implement Richards/Darcy transport, animal food
chain, dose coefficients, photosynthesis, dynamic growth, or a UFOTRI
parameter loader. It does not claim complete UFOTRI equivalence, empirical
validation, regulatory validation, or field validation.
