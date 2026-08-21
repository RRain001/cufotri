# V3-P0 Parameter Database Layer

Status: `ARCHITECTURE_IMPLEMENTED`

This layer establishes a typed, provenance-bearing parameter interface for
future V3 modules. It is not connected to the V2 configuration loader, the V2
physics modules, the CLI, or the V3 physics gate. Loading a database therefore
does not change any current calculation result.

## Package layout

```text
src/cteas_ufotri/parameters/
├── database.py       # ParameterDatabase public API
├── exceptions.py     # fail-closed exception types
├── legacy.py         # opt-in legacy YAML adapter
├── provenance.py     # provenance records and SHA-256 canonical hashing
├── registry.py       # declared parameter-source registry
└── schema.py         # ParameterEntry, bounds, applicability, validation

parameters/
├── parameter_sources.yaml
└── databases/ufotri_leaf_exchange.yaml

schemas/
├── parameter_database.schema.json
└── parameter_sources.schema.json
```

## ParameterEntry contract

Every entry has `name`, `value`, `unit`, `category`, `source`, `reference`,
`confidence`, `applicability`, `transform`, and `bounds`. Names are dotted
lower-case paths such as `leaf.stomatal_resistance_day`. Numeric values and
bounds must be finite. Bounds include explicit lower/upper inclusivity and the
value must be inside them.

`value: null`, `bounds: null`, `confidence:
placeholder_pending_validation`, `applicability.status:
pending_validation`, and the explicit `PENDING_VALIDATION` unit sentinel are
reserved for interface-only declarations. Such an entry can be listed and
audited but `ParameterDatabase.get()` raises `ParameterUnavailableError`.
There is no missing-to-zero or default substitution.

## Provenance and source policy

`source` is an identifier, not a free-form claim. It must resolve in
`parameters/parameter_sources.yaml`. Each source declares its status,
description, reference, and `production_allowed` flag. The current registry
contains `CTEAS_DEFAULT`, `PROJECT_CUSTOM`, and `UFOTRI_VALIDATED`, but all are
non-production in this architecture-only stage. In particular,
`UFOTRI_VALIDATED` is a reserved source identifier with
`external_reference_required`; it does not assert that UFOTRI evidence has
been validated.

`get(name, production=True)` additionally requires a validated source, a
validated entry confidence, an applicable scope, and source-registry
permission. The database package hash is a deterministic SHA-256 over the
canonical parameter document and source registry, so provenance changes are
observable.

## Public interface

```python
database = ParameterDatabase.load(
    "parameters/databases/ufotri_leaf_exchange.yaml"
)
database.get_entry("leaf.stomatal_resistance_day")
database.list_parameters()
database.validate()
database.hash()
```

Unknown names, missing units or sources, invalid transforms, non-finite
numbers, malformed bounds, and out-of-range values fail closed. The
`LegacyParameterAdapter` is an opt-in inspection/migration seam. It exposes
numeric leaves from an existing mapping with exact-value compatibility bounds;
it has no call site in V2 and does not rewrite `configs/default_parameters.yaml`.

## Leaf Exchange preparation

`ufotri_leaf_exchange.yaml` reserves the boundary-layer resistance, daytime
and nighttime stomatal resistance, humidity-response, and temperature-response
names. It deliberately contains no UFOTRI numerical values. Leaf Exchange
calculation, TFWT pathways, soil-layer coupling, and mass-balance benchmarks
remain outside V3-P0 and must wait for the separately controlled V3 physics
gate.

## Future CTEAS-Atmos interface

The database layer provides a stable scalar parameter/provenance seam for a
future CTEAS-Atmos integration. That integration must exchange an explicit
parameter package hash, units, source status, applicability scope, and model
version. It must not infer missing parameters or treat a source declaration as
independent physical validation.

## Boundary conditions

V3-P0 makes no change to formal V2 equations, default YAML values, CLI behavior,
trusted external-evidence registry, or `V3_PHYSICS_START_GATE`. The current
physics status remains `NOT_STARTED` and the gate remains
`BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA`.
