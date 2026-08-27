# ADR-030: V4 root operator-split comparison R1

Status: Accepted after machine-gated comparison

## Context

The merged V4 root coupling rereview left one numerical choice unresolved after `root_v4` implementation: when the interval-integrated three-layer root HTO transfer enters plant TFWT relative to OBT formation.

The two frozen candidates were:

1. `PRESERVE_V3_POST_OBT_ROOT_GAIN`: OBT formation consumes interval-start TFWT; the root transfer accumulated over the interval is added to endpoint TFWT after OBT reconciliation.
2. `ROOT_GAIN_BEFORE_OBT`: the complete root transfer accumulated over the interval is added to TFWT before the same interval's OBT solve.

This is a numerical-coupling decision, not parameter validation or physical validation.

## Machine evidence

The R1 harness used only explicit synthetic three-layer `q_w,i` forcing. UFOTRI 20/40/40 fractions, reference 0.026/0.026/0.017 d^-1 rates, and the short-term ~3 h delay remained inactive.

The exact-head PR gate reported `V4_ROOT_OPERATOR_SPLIT_STATUS=PASS_SELECTION`. Both candidates passed:

- single-application soil-root transfer identity and coupled soil+TFWT+OBT conservation;
- deterministic repeat;
- JSON restart equivalence;
- monotonic timestep refinement against a finer numerical reference;
- explicit root-pulse lag discrimination.

The comparison used one declared `soil_surface_area` basis. No soil-area-to-plant-area conversion was inferred.

## Decision

Select `PRESERVE_V3_POST_OBT_ROOT_GAIN` for the next opt-in V4 integration stage.

The basis is software time semantics:

- P7.5B defines forcing/state semantics at interval start and uses the post-OBT root-gain order.
- `root_v4` reports transfer accumulated across `[t_n, t_n+1]`; this is not an interval-start TFWT state.
- Applying the full interval-integrated transfer before OBT would make the complete end-of-interval root gain available to the OBT source for the whole same interval, a right-biased Lie split.
- The post-OBT split keeps OBT on the interval-start TFWT state and lets root contribution enter the endpoint state. Its one-step lag contracts with timestep refinement.

Synthetic error magnitude is not treated as physical evidence. The decision is numerical-semantics compatibility only.

## Consequences

After this decision PR itself passes a new exact-head CI and is merged without tree drift, it authorizes only an isolated opt-in `V4_SOIL_ROOT_TFWT_OBT_INTEGRATION_R1` stage. It does not modify V3, activate parameters, implement the UFOTRI 3 h delay, solve transpiration/hydrology, authorize Leaf R5, or bind real CTEAS-Atmos forcing.
