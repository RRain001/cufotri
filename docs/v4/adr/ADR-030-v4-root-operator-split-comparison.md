# ADR-030: V4 root operator-split comparison R1

Status: Proposed pending exact-head machine gate

## Context

The merged V4 root coupling rereview deliberately left one numerical choice unresolved after `root_v4` implementation: when the interval-integrated three-layer root HTO transfer enters plant TFWT relative to OBT formation.

The two frozen candidates are:

1. `PRESERVE_V3_POST_OBT_ROOT_GAIN`: OBT formation consumes interval-start TFWT; the root transfer accumulated over the interval is added to the endpoint TFWT after the OBT transfer is reconciled.
2. `ROOT_GAIN_BEFORE_OBT`: the complete root transfer accumulated over the interval is added to TFWT before the same interval's OBT solve.

This is a numerical-coupling decision. It is not a parameter-validation or physical-validation decision.

## Comparison contract

R1 must use only explicit synthetic three-layer `q_w,i` forcing. UFOTRI 20/40/40 fractions, the reference 0.026/0.026/0.017 d^-1 rates, and the short-term ~3 h delay remain inactive.

The harness must prove for both candidates:

- the root transfer is applied once to soil loss and once to plant gain as one transfer identity;
- layer-root/soil and coupled soil+TFWT+OBT ledgers close;
- deterministic repeat;
- JSON restart equivalence;
- monotonic timestep refinement against a finer numerical reference;
- the expected multi-step root-to-OBT lag distinction is explicit rather than hidden.

The comparison uses one explicitly common `soil_surface_area` basis. It does not infer a soil-area-to-plant-area conversion. Any future integration with distinct area bases requires an explicit adapter.

## Conditional selection rule

If and only if every R1 gate passes, select `PRESERVE_V3_POST_OBT_ROOT_GAIN` for the next opt-in V4 integration stage.

The basis is software time semantics:

- P7.5B already defines forcing/state semantics at interval start and uses the post-OBT root gain order.
- `root_v4` reports a transfer accumulated across `[t_n, t_n+1]`; that integrated transfer is not an interval-start TFWT state.
- Applying the entire integrated root transfer before the OBT solve makes the full end-of-interval transfer available to the OBT source for the whole same interval, a right-biased Lie split.
- The post-OBT split keeps OBT on the interval-start TFWT state and lets the root contribution enter the endpoint state. Its one-step lag shrinks with timestep refinement.

Synthetic error magnitude is not used as physical evidence. If any conservation, restart, determinism, refinement, or lag gate fails, the decision remains HOLD.

## Consequences

A passing R1 may authorize only an opt-in `V4_SOIL_ROOT_TFWT_OBT_INTEGRATION_R1`. It does not modify V3, activate parameters, implement the UFOTRI 3 h delay, solve transpiration/hydrology, or bind real CTEAS-Atmos forcing.
