# P5.1-P5.3 Interface Consistency Review

Status: `PASS_WITH_DECLARED_P6_PREREQUISITES`

## Cross-document consistency

| Boundary | Consistent evidence | Open implementation boundary |
| --- | --- | --- |
| Atmosphere | `AtmosphericHTOForcing` has one canonical required-field set, units, UTC time, provenance, and fail-closed behavior across the P5.3 contract, tests, and report | Raw 3D fields still require an upstream adapter |
| Plant | Plant architecture and ADR-010 agree that leaf/root paths converge only at `PlantState` | Root uptake and path-resolved ledger are not implemented |
| Leaf flux | ADR-009 and the P5.3 flux contract are reconciled by the canonical future names `air_to_leaf_flux`, `stomatal_flux`, `cuticular_flux`, `tfwt_to_obt_flux`, and `decay_flux` | `LeafExchangeFlux` remains design-only |
| Parameters | P5.3 capability audit and ADR-011 agree that scalar metadata is supported while multidimensional/function semantics are not | No schema extension is allowed before P6 review |
| Validation | Regression contract and P5.3 report agree on constant, pulse/step, and diurnal benchmarks with no frozen tolerance | Reference artifacts and tolerance remain P6 inputs |

## Interface invariants

1. UFOTRI does not branch on Gaussian, CALPUFF, CTEAS-Atmos, ERA5, or any
   other producer identity.
2. Soil owns soil inventory only; leaf exchange owns leaf physics only;
   `PlantState` owns plant integration.
3. Internal TFWT-to-OBT transfer is not counted as a boundary input.
4. Placeholder parameters fail closed and are never converted into hidden
   defaults.
5. P5.4 adds no production class, equation, parameter value, schema, or
   configuration.

## Review conclusion

The P5.1-P5.3 architecture is internally consistent as a staged migration
framework. The remaining limitations are explicit P6 entry conditions rather
than contradictory ownership or unit contracts.
