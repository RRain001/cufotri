# ADR-041: V4 OBT UFOTRI baseline R1

Status: `IMPLEMENTATION_IN_PROGRESS`

## Context

The previous OBT evidence-acquisition path established a strict request and metadata-intake process. The project owner has now explicitly decided that external data requests are not required for the current route and that the model should use UFOTRI parameters directly.

The recovered UFOTRI manual states a daily-average OBT uptake rate of `0.06 % per hour` of plant HTO and a mean OBT loss rate of `0.3 % per hour`. It also states that formation is higher in daytime and lower at night, but the recovered text does not provide an unambiguous normalized day/night multiplier pair.

The existing `OBTSolver` already supports exactly the required first-order form and accepts explicit `kf`, `kr`, daylight and nighttime multipliers. No solver redesign is required to adopt the UFOTRI baseline.

## Decision

Adopt a controlled UFOTRI OBT baseline profile:

- `kf = 0.0006 h^-1 = 1.6666666666666665e-7 s^-1`;
- `kr = 0.003 h^-1 = 8.333333333333333e-7 s^-1`;
- daylight multiplier = `1.0`;
- nighttime multiplier = `1.0`.

The two multipliers intentionally preserve the stated daily-average formation rate. They do not assert that UFOTRI has no day/night dependence. Instead they avoid inventing a quantitative split that is not explicitly recovered from the source.

The new profile is opt-in and uses the unchanged equation

`dM_OBT/dt = kf * M_TFWT - kr * M_OBT`.

## Consequences

This stage authorizes use of the UFOTRI baseline parameters in numerical integration tests and subsequent controlled runtime wiring. It does not constitute calibration or empirical validation, does not authorize a multi-pool OBT solver, and does not alter soil, root, TFWT, food, dose, hydrology or Atmos contracts.

The external evidence-request path is closed for this route. `REQUESTS_SENT=FALSE` remains historical truth; no message needs to be sent.

## Next transition

After exact-head CI, run the existing soil-root-TFWT-OBT chain with the UFOTRI profile and verify conservation, timestep behavior and deterministic replay before deciding whether to make this profile the V4 default.
