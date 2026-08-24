# ADR-014: V3 UFOTRI semantic-mapping policy

- Status: Accepted for P7.6C-2 control-plane scope
- Date: 2026-08-24
- Decision owner: CTEAS_UFOTRI repository

## Context

The repository has a recovered UFOTRI manual and a set of typed V3 interfaces,
but it does not contain the original UFOTRI source implementation. Familiar
symbols such as `U_P`, `V_P`, `t_15,14`, `r_a`, and `DF` therefore cannot be
treated as self-authenticating V3 parameters. The V3 architecture also uses
different state bases in several places: areal inventories rather than source
concentrations, signed boundary fluxes rather than derived transport rates,
one soil layer rather than the manual's multi-layer system, and an explicit
plant-to-food harvest event rather than a continuous cow/food-chain matrix.

## Decision

P7.6C-2 introduces a read-only semantic mapping control plane at
`src/cteas_ufotri/parameters_v3/ufotri_mapping.py` and the canonical manifest
at `docs/v3/parameter_evidence/ufotri_parameter_mapping.yaml`.

Each immutable record must state the V3 and UFOTRI equation, quantity
definition, unit, compartment, time/state basis, relationship fields,
transformation derivation, review status, and provenance. The only allowed
mapping statuses are:

- `DIRECT_MAPPING`: same physical quantity and equation role; at most an
  explicit unit scale is needed;
- `TRANSFORMABLE_MAPPING`: an explicit dimensional/physical derivation exists
  without a fitted or guessed coefficient;
- `CONCEPTUAL_ANALOGUE`: the mechanism is related but transformation requires
  additional assumptions;
- `NO_MAPPING`: the quantities or equation roles are materially different;
- `SOURCE_UNAVAILABLE`: the original definition was not recovered.

Only direct or explicitly transformable records may be considered for later
evidence recovery, and even those records do not create a candidate during
P7.6C-2. Conceptual, no-mapping, and source-unavailable records are blocked.

## Consequences

The manifest covers 26 current deferred/P7.6C-1-related V3 parameters with
counts `12/4/6/3/1` for direct/transformable/conceptual/no/source-unavailable.
It preserves `validated=1`, `active=0`, and `new_validation_candidates=0`.
The runtime remains unchanged: production plant, soil, exposure, coupling,
and pipeline modules do not import the mapping module.

The policy makes several distinctions explicit:

1. a UFOTRI first-order root rate in `s^-1` is not a V3 root velocity in
   `m s^-1` without a declared state/length conversion;
2. a manual food-chain transfer rate is not a V3 harvest fraction;
3. an external dose coefficient or consumption habit is not UFOTRI biological
   evidence;
4. a rate-to-flux transformation is admissible only when its state basis,
   sign, and units are written in the record.

## Non-goals and safeguards

This ADR does not implement or activate UFOTRI physics, change V3 equations,
add calibration, select production values, import an UFOTRI database, claim
regulatory or empirical validation, or establish numerical equivalence.
Richards/Darcy transport, dynamic photosynthesis/growth, animal food chains,
and dose-data loading remain outside the stage. The manifest's fail-closed
flags and tests are mandatory safeguards for future changes.

## Follow-up

Any future admission of a mapping as a validation candidate must provide a
versioned source artifact, exact equation and unit evidence, applicability,
compartment/state-basis review, and an independent review record. A future
implementation that changes a V3 equation or solver must use a separate ADR
and stage gate; it may not reinterpret this control-plane manifest as runtime
configuration.
