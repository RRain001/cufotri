# V3-P5.4 UFOTRI Physics Migration Readiness Independent Review

Date: 2026-08-21

## Verdict

```text
V3_P5_4_STATUS = PASS_INDEPENDENT_ARCHITECTURE_REVIEW
UFOTRI_PHYSICS_IMPLEMENTED = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
V3_FORMAL_PHYSICS = NOT_STARTED
SCHEMA_CHANGE = 0
SRC_CHANGE = 0
CONFIG_CHANGE = 0
TRUSTED_REGISTRY_CHANGE = 0
V2_BEHAVIOR_CHANGE = 0
```

This is an independent architecture review, not a claim of UFOTRI physical
equivalence, numerical validation, or regulatory suitability.

## Review baseline

```text
BASE_MAIN_SHA = 6671f5793d04842bf2ceae4904f3c0cf30a0d7e0
P5.1_SHA = 92772160a236ee7e0038107038c384c3e74580cb
P5.2_SHA = c6a58b6c40ef05e2557b5201decfc40a38997045
P5.3_SHA = 14e490759459b5beedff1c71591d1aa5f7d1776a
BRANCH = codex/v3-ufotri-interface-freeze-independent-review
BRANCH_BASE = P5.3_SHA
```

The P5.4 working changes are restricted to review documents, status text, and
architecture tests. The protected paths have zero diff relative to P5.3.

## Independent findings

### Atmospheric interface

The normalized scalar `AtmosphericHTOForcing` contract is complete for required
fields, units, UTC time, provenance, and fail-closed missingness. Raw CTEAS-
Atmos 3D concentration fields and surface concentration are not directly
consumable without a spatial/semantic adapter. Scalar deposition flux and
meteorology are conditionally consumable when their unit, time, location, and
area basis exactly match the frozen contract.

### Plant pathways

The independent leaf/root topology is consistent. Leaf uptake and soil
deposition/root uptake branch independently and converge only through
`PlantState`. The current implementation has no root uptake and no
path-resolved plant ledger; these remain explicit P6 prerequisites. Soil does
not own plant state, and leaf exchange does not own soil.

### Parameter database

P5.1 supports scalar values, exact unit checks, uncertainty, provenance,
source registry metadata, lifecycle, bounds, and deterministic hashing. It
does not support the table, crop-specific, growth-stage, temperature-function,
interpolation, or unit-conversion capabilities required by a full UFOTRI
database. ADR-011 is the correct fail-closed disposition; the schema remains
unchanged and the placeholder database contains no activated UFOTRI values.

### Physics migration boundary

The future `LeafExchangeFlux` shape can express the required pathway outputs,
but it does not replace reviewed resistance, leaf-water, TFWT, OBT, or decay
equations. The fixed three-layer soil structure is structurally compatible
with a future surface/root/deep mapping; P6 must freeze semantic labels and a
typed root-uptake output without changing `PlantState` ownership.

### Validation readiness

The regression contract contains the required constant-HTO, step/pulse, and
diurnal cases, with trajectory, pathway, provenance, and ledger output formats.
Reference data and numerical tolerances remain explicit P6 inputs and can be
added without changing the interface shape.

## Acceptance evidence

```text
INTERFACE_CONSISTENCY = PASS_WITH_DECLARED_P6_PREREQUISITES
ATMOSPHERIC_RAW_OUTPUT_DIRECT_COMPATIBILITY = FALSE
PLANT_PATHWAY_OWNERSHIP = CONSISTENT
PARAMETER_DATABASE_FULL_UFOTRI_READY = FALSE
LEAF_EXCHANGE_FLUX = DESIGN_ONLY_NOT_IMPLEMENTED
REGRESSION_CONTRACT = COMPLETE_FORMAT_ONLY
```

The capability limitations above are review findings, not hidden defaults or
implementation failures. No P5.4 change weakens the fail-closed boundary.

## P6 entry conditions

P6 may begin only after the following are separately reviewed: CTEAS-Atmos
spatial/semantic adapters, parameter table/function and unit-conversion
extension, leaf resistance and TFWT/OBT equations, typed root-uptake flux,
surface/root/deep layer semantics, reference data, and numerical tolerances.
