# ADR-050: V4 production-case input source resolution R1

## Status

Accepted as a control-plane source-resolution audit, pending exact-head CI and clean merge.

## Context

PR #46 froze a fail-closed production-case manifest containing 49 input records (48 required, 1 optional). The manifest is inventory-complete but intentionally production-incomplete. The next authorized step is source resolution, not solver development, parameter activation, calibration, or real CTEAS-Atmos binding.

`PRODUCTION_INPUT_PACKET_READY=FALSE` and `FULL_MODEL_PRODUCTION_READY=FALSE` remain hard boundaries.

## Decision

R1 creates a source-resolution overlay for every manifest quantity. Resolution status is evidence metadata only. It does not alter runtime defaults, import a parameter database, authorize a production value, or convert a source record into a production-ready case packet.

The 49 manifest quantities are partitioned exactly once into nine dispositions:

1. `SOURCE_RESOLVED_NOT_ACTIVATED` — existing independently reviewed evidence is sufficient to identify a source, but production use remains unauthorized.
2. `ALREADY_CONTROLLED` — the manifest already contains a controlled baseline/profile; this stage does not change it.
3. `BLOCKED_EXTERNAL` — an external upstream product is still unavailable.
4. `LIVE_CASE_BINDING_REQUIRED` — a contract exists, but a real case artifact and time/space/identity support are still required.
5. `DERIVED_DEPENDENCY_NOT_READY` — the quantity can only become ready after its dependencies become production-ready.
6. `CASE_SOURCE_REQUIRED` — a case/scenario source is required and has not been selected.
7. `CONDITION_DEPENDENT_PHYSICAL_PROPERTY_SOURCE_REQUIRED` — the quantity is a physical property or conversion input whose value depends on environmental/model conditions; a convenient test value must not be promoted as a universal constant.
8. `PROCESS_SOURCE_OR_EXPLICIT_ZERO_POLICY_REQUIRED` — a process forcing must have either a real source or an evidenced explicit-zero policy.
9. `PROVISIONAL_EVIDENCE_REQUIRED` — the current evidence remains provisional and cannot be promoted by this stage.

## H-3 half-life resolution

`soil_three_layer.tritium_half_life` is the only newly source-resolved quantity in R1. It maps semantically to the independently reviewed V3 evidence record `soil.tritium_half_life` in `docs/v3/parameter_evidence/physical_constant_validation_registry.yaml`.

The source-resolution overlay records the validated universal H-3 nuclear half-life as `388540800 s +/- 777600 s`, selected from `evidence.ddep.tritium_half_life.2006` under the existing reconciliation policy. This value is evidence metadata only. It is not imported into a solver and does not change `ACTIVE_PARAMETERS=0`.

The evidence must not be reinterpreted as an environmental residence time, soil-retention half-life, biological elimination half-life, or OBT turnover half-life.

## Eq.39 physical-property disposition

The Eq.39 inputs `root_eq39.latent_heat`, `root_eq39.water_density`, and `root_eq39.psychrometric_constant` remain unresolved for production use.

FAO-56 states that latent heat varies with temperature and uses `2.45 MJ kg^-1` as a Penman-Monteith simplification corresponding to about 20 degC. It also defines the psychrometric constant from atmospheric pressure and latent heat rather than as an unconditional universal number. IAPWS treats water density as a thermodynamic property derived from state. Therefore the synthetic/test values `2.45e6 J kg^-1`, `1000 kg m^-3`, and `66 Pa K^-1` are not promoted by R1.

R1 freezes only their source class: `CONDITION_DEPENDENT_PHYSICAL_PROPERTY_SOURCE_REQUIRED`.

## External Atmos blocker

Both `atmosphere.surface_deposition_flux` and its downstream `soil_three_layer.surface_deposition_flux` remain blocked. `BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED` remains the governing blocker token. No zero, puff ledger, accumulated deposition quantity, or inferred surrogate is accepted as the real surface flux.

## Consequences

- Source resolution is now exhaustive at the classification/disposition level for all 49 manifest quantities.
- Only one unresolved source becomes source-resolved: the universal H-3 half-life evidence record.
- No manifest record becomes production-authorized because of this stage.
- No `src/` code, solver equation, numerical coupling, workflow, calibration state, or physical model is changed.
- API/test defaults remain non-evidence.

## Next stage

After a clean merge, proceed to `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R2`, restricted to the Eq.39 physical-property source decision for latent heat, water density, and psychrometric constant. That stage must decide whether each quantity is case-derived, state-derived, or a deliberately frozen model convention with explicit applicability. It must not activate Eq.38, full hydrology, Leaf R5, multi-pool OBT, calibration, empirical validation, or real CTEAS-Atmos binding.
