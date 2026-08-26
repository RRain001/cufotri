# V4-2 Leaf Dynamic Stomatal Readiness — Technical Review

## Entry state

```text
main = 61dfee175d5b16fe358417e0beba75a776d6f394
V4-1 = PASS_CONTROL_PLANE_CONTRACT_REVIEW
leaf implementation authorized = false
```

V4-2 reviews whether the selected leaf dynamic stomatal candidate has enough
scientific and data definition to enter production implementation. It does not
implement the candidate.

## Existing evidence

Repository evidence supports a future validation path for `r_a`, `r_b`, and
`r_c`: their current roles and units are semantically compatible with the leaf
resistance chain. The same evidence classifies growth-stage handling as a
physics-redesign problem because a stage ontology and stage-dependent equation
were not established in V3.

The V4-1 leaf contract already freezes the symbolic candidate and forcing/state
ownership, but deliberately leaves response shapes, parameter values, empirical
domains, and the closed-stomata numerical policy unresolved.

## Readiness work completed in V4-2

V4-2 adds:

- `docs/v4/leaf/v4_2_leaf_dynamic_stomatal_readiness.yaml`
- `docs/v4/leaf/v4_2_growth_stage_ontology_contract.yaml`
- `docs/v4/leaf/v4_2_response_domain_admission.yaml`
- `docs/v4/leaf/v4_2_validation_protocol.yaml`
- `docs/v4/leaf/v4_2_evidence_acquisition_requirements.yaml`
- `schemas/v4/v4_leaf_empirical_evidence_packet.schema.json`
- `docs/v4/adr/ADR-025-v4-2-leaf-dynamic-stomatal-readiness.md`

These artifacts convert the prior generic HOLD into a precise evidence gate.

## Growth-stage review

The stage contract is deliberately dataset-bound. An ontology instance must
identify its source field, source taxonomy or category basis, crop identity,
revision and mapping records. String equality or numeric-code equality across
datasets does not establish semantic equivalence.

This closes the governance rule but not the evidence gate: no concrete dataset-
specific ontology instance is currently checked in.

Result: **contract PASS; empirical instance HOLD**.

## Response-domain review

Light/PAR, VPD and leaf-temperature domains must be declared from matched
observations with provenance and a preregistered derivation rule. Stage support
is categorical membership in the dataset-specific ontology. V4-2 intentionally
does not choose min/max, quantiles, clipping limits, or other support estimators.

Univariate ranges are insufficient to prove joint support; condition coverage
must also be declared for future generalization assessment.

Result: **admission rule PASS; empirical domains HOLD**.

## Evidence-packet review

The specialized JSON Schema requires an empirical packet to identify:

- dataset/revision/access provenance;
- crop identity;
- stage ontology and source stage records;
- time alignment;
- independent groups;
- observed stomatal conductance or leaf/surface resistance;
- light/PAR;
- VPD, or an explicit humidity-to-VPD derivation contract;
- leaf temperature;
- growth stage;
- response-domain records for light/PAR, VPD, `T_leaf`, and stage;
- calibration/final-validation group declarations;
- the four preregistered metric families.

The schema is a packet contract, not a checked-in empirical result. No matching
packet is currently present.

Result: **schema PASS subject to repository tests; empirical packet HOLD**.

## Validation protocol review

The protocol forbids leakage from final validation into calibration, model
selection, preprocessing, response-domain estimation, and acceptance-threshold
selection. It also forbids random row splitting across the same independent
biological/experimental group as the sole final-validation separation.

No numerical acceptance thresholds are selected here. They must be justified
and preregistered with a concrete dataset before physical validation.

Result: **protocol defined; validation not executed**.

## Runtime and parameter boundary

V4-2 contains no production `src/` implementation and admits no candidate
parameter values. It does not alter P7.5/P7.5B numerical coupling or current
state serialization. The V3 profile remains default and rollback.

## Readiness verdict

The current blocker is no longer missing governance design. It is missing
matched empirical evidence and its dataset-specific ontology/domain/split
instantiation.

```ini
V4_2_LEAF_STATUS = HOLD_EMPIRICAL_EVIDENCE_REQUIRED
GROWTH_STAGE_ONTOLOGY_RULE = PASS
DATASET_SPECIFIC_STAGE_ONTOLOGY = MISSING
RESPONSE_DOMAIN_RULE = PASS
EMPIRICAL_RESPONSE_DOMAINS = MISSING
EVIDENCE_PACKET_SCHEMA = DEFINED
MATCHED_EMPIRICAL_PACKET = MISSING
VALIDATION_PROTOCOL = DEFINED_NOT_EXECUTED
INDEPENDENT_ITEM_REVIEW = NOT_STARTED
LEAF_IMPLEMENTATION_AUTHORIZED = FALSE
PRODUCTION_RUNTIME_CHANGED = FALSE
CANDIDATE_PARAMETER_VALUES_ADMITTED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```

The next phase is evidence acquisition/registration. Solver implementation must
remain blocked until a complete empirical packet and independent item review
exist.
