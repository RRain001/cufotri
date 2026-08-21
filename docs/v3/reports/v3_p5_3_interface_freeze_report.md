# V3-P5.3 UFOTRI Interface Freeze Report

Date: 2026-08-21

## Verdict

```text
P5.3_STATUS = PASS_INTERFACE_FREEZE
ATMOSPHERIC_HTO_FORCING = FROZEN
PLANT_DUAL_PATHWAY = FROZEN
LEAF_EXCHANGE_FLUX = DESIGN_ONLY_NOT_IMPLEMENTED
PARAMETER_DATABASE = CAPABILITY_AUDITED
UFOTRI_PARAMETERS_IMPORTED = FALSE
UFOTRI_PHYSICS_IMPLEMENTED = FALSE
V3_FORMAL_PHYSICS = NOT_STARTED
PARAMETER_SCHEMA_CHANGED = FALSE
MAIN_BEHAVIOR_CHANGED = FALSE
SRC_DIFF = 0
CONFIG_DIFF = 0
TRUSTED_REGISTRY_DIFF = 0
```

P5.3 freezes interface contracts only. It does not implement UFOTRI physics,
activate parameters, alter production configuration, or change V1/V2
behavior. Existing V2 manual/UFOTRI formulas remain a separate frozen legacy
path and are not imported into V3.

## Baseline

```text
BASE_MAIN_SHA = 6671f5793d04842bf2ceae4904f3c0cf30a0d7e0
P5.2_SHA = c6a58b6c40ef05e2557b5201decfc40a38997045
PARAMETER_LAYER_SHA = 92772160a236ee7e0038107038c384c3e74580cb
LEAF_MODULE_SHA = 20a93a6464fd937947c501683b9a27e8ea9e82b2
BRANCH = codex/v3-ufotri-interface-freeze
BRANCH_BASE = P5.2_SHA
```

`main` predates the P1-P5.2 V3 framework. The P5.3 branch therefore starts
from the pushed P5.2 commit while retaining `BASE_MAIN_SHA` for the repository
baseline. The zero-diff statuses above describe changes introduced by P5.3
relative to P5.2, not the intentional P1-P5.2 framework difference from
`main`.

## Frozen decisions

### Atmospheric boundary

`AtmosphericHTOForcing` now has exact required names `time`,
`air_hto_concentration`, `air_temperature`, and `relative_humidity`. Optional
precipitation, shortwave radiation, longwave radiation, wind speed,
boundary-layer height, and surface deposition flux have declared units and
fail-closed missingness rules. Time sequences are UTC, strictly increasing,
and cadence-checked. Provenance is opaque metadata and cannot expose producer
logic to UFOTRI.

### Plant dual pathways

Leaf absorption and soil/root absorption remain independent until `PlantState`.
`leaf_exchange` owns leaf physics, `soil` owns soil inventory, `PlantState`
owns integration and convergence accounting, and `food_chain` consumes the
declared plant state. Soil does not own plant state, and leaf exchange does not
own soil.

### LeafExchangeFlux

The future internal design names `air_to_leaf_flux`, `stomatal_flux`,
`cuticular_flux`, `tfwt_to_obt_flux`, and `decay_flux`, all as declared
area-normalized rates. The record remains design-only and is not added to the
current physics protocol.

### Parameter capability

P5.1 is adequate for scalar values, units, source provenance, hashes,
uncertainty, bounds, and lifecycle. It is inadequate for tables, crop or
growth-stage dimensions, temperature functions, and interpolation. ADR-011
records a future extension requirement; the schema remains unchanged.

### Regression format

Constant HTO, step/pulse release, and diurnal benchmarks are frozen with
required inputs, `TFWT(t)`, `OBT(t)`, pathway outputs, provenance, and ledger
requirements. Numerical tolerances remain `TO_BE_FROZEN_IN_P6`.

## Deliverables

- `docs/v3/interfaces/atmospheric_hto_forcing_contract.md`
- `docs/v3/architecture/plant_pathway_architecture.md`
- `docs/v3/architecture/ADR-010-plant-dual-pathway-model.md`
- `docs/v3/architecture/leaf_exchange_flux_contract.md`
- `docs/v3/architecture/parameter_database_ufotri_capability_audit.md`
- `docs/v3/architecture/ADR-011-parameter-database-extension.md`
- `docs/v3/validation/ufotri_physics_regression_contract.md`
- `tests/architecture/test_atmospheric_hto_forcing_contract.py`
- `tests/architecture/test_v3_p5_3_interface_freeze.py`

The implementation status document records the same verdict.

## P6 entry gate

P6 may begin only after reviewed physical equations, validated parameter
extension and values, executable forcing serialization, root-uptake ownership,
reference artifacts, and concrete regression tolerances are separately
approved. P5.3 is not a claim of physical validation or regulatory suitability.
