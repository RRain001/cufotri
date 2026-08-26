# ADR-025 — V4-2 leaf dynamic stomatal readiness

## Status

Accepted as a **readiness HOLD** decision. This ADR authorizes evidence and
ontology preparation only. It does not authorize production implementation of
the dynamic stomatal response.

## Context

V4-1 closed the common data/state/equation contract preparation stage and kept
all selected V4 physical models unauthorized. The next roadmap item is the leaf
dynamic stomatal response:

```text
g_s = g_s,max F_light(L) F_vpd(VPD) F_temp(T_leaf) F_stage(stage)
r_c = 1 / g_s
r_tot = r_a + r_b + r_c
g_ex = 1 / r_tot
```

The existing resistance chain and the roles/units of `r_a`, `r_b`, and `r_c`
have a viable validation path. That does not establish the response functions,
response domains, stage semantics, parameter values, or empirical performance
of the dynamic stomatal candidate.

## Decision

V4-2 freezes four pre-implementation boundaries:

1. growth stage is dataset-bound metadata with explicit ontology identity and
   provenance; no universal stage taxonomy or silent cross-dataset mapping is
   admitted;
2. light/PAR, VPD, leaf-temperature and stage response domains must be derived
   from a concrete matched empirical packet using a preregistered support rule;
3. the empirical packet must contain an observed stomatal-conductance or
   leaf/surface-resistance target together with matched forcing/context,
   timestamps, independent-group identity, units and provenance;
4. calibration/model selection and final empirical validation must use
   explicitly separated independent groups, with the final holdout excluded
   from response-domain estimation and post-hoc threshold tuning.

The specialized packet schema is:

`schemas/v4/v4_leaf_empirical_evidence_packet.schema.json`.

## Growth-stage boundary

Stage labels are not portable merely because strings or numeric codes match.
Every admitted stage value must travel with a dataset-specific ontology ID and
revision. Automatic mappings from vegetation period, calendar month, day of
year, or a different crop taxonomy are forbidden unless a separate mapping is
explicitly reviewed.

No ordinal distance between categories may be inferred unless the source
ontology itself defines that ordering and interpretation.

## Response-domain boundary

V4-2 does not select numerical bounds or a statistical support estimator.
Concrete response domains must be evidence-bound. Synthetic inputs, production
solver output, convenience defaults, and unreviewed literature ranges cannot
create an empirical domain.

Independent univariate ranges do not prove joint multivariate support. A future
packet must document joint condition coverage or an equivalent preregistered
support assessment.

A future runtime implementation must fail closed outside its admitted domain;
silent clipping or extrapolation is not an accepted default.

## Validation boundary

The final empirical validation group must remain independent of calibration,
model selection, preprocessing learned from the holdout, domain estimation, and
acceptance-threshold selection. Random row splitting across the same biological
or experimental group is not sufficient for final validation.

Synthetic cases remain software verification only.

## Current evidence disposition

No checked-in packet currently satisfies the matched leaf evidence contract.
No dataset-specific stage ontology instance or empirical response-domain record
has been admitted. Physical validation has not been executed.

Therefore the item remains:

```ini
V4_2_LEAF_STATUS = HOLD_EMPIRICAL_EVIDENCE_REQUIRED
CONTROL_PLANE_PREPARATION = COMPLETE
LEAF_IMPLEMENTATION_AUTHORIZED = FALSE
CANDIDATE_PARAMETER_VALUES_ADMITTED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```

## Consequences

The next legitimate work is evidence acquisition/registration and construction
of a dataset-specific ontology/domain/split packet. Production solver coding is
not the next step. After a complete empirical packet exists, the leaf item must
undergo a separate technical and independent review before implementation can
be authorized.
