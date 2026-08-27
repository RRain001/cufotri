# ADR-029: V4 three-layer root coupling re-review

## Status

Accepted for isolated root-flux implementation; V4 pipeline integration remains unselected.

## Context

The V4 root-water-flux contract selected `J_root,i = q_w,i C_w,i` but required P7.5/P7.5B coupling to be re-reviewed before implementation. The merged V4 soil core now owns explicit three-layer water/HTO inventories and root sink slots. Applying a root transfer independently after the soil step could therefore double-count the soil loss.

KfK 4605 provides distinct short- and long-term root descriptions. The short-term secondary model links root uptake to plant transpiration with an approximately 3 h delay. The long-term ingestion model uses the 0–5, 5–15 and 15–30 cm compartments and assigns 20/40/40 of root water uptake, with reference layer transfer rates near 0.026/0.026/0.017 d^-1. The original UFOTRI source code is unavailable, so exact software operator ordering cannot be recovered.

## Decision

1. Authorize an isolated non-mutating `root_v4` flux core whose authoritative equation is `J_root,i = q_w,i C_w,i(S_n)`.
2. Require explicit, timestamped, provenance-bearing layer water flux `q_w,i`; the root core must not generate or guess hydrology.
3. Keep short-term transpiration/3 h lag semantics separate from long-term daily-mean 20/40/40 ingestion semantics.
4. Treat the UFOTRI fractions and transfer rates as reference evidence, not active defaults.
5. Make `soil_v4` the sole owner of applying root water/HTO sinks. A future TFWT adapter must add exactly the same integrated HTO transfer once.
6. Leave the V4 pipeline operator split unselected. The legacy post-OBT root gain and same-interval pre-OBT root gain must be compared before integration.
7. Preserve V3/P7.5/P7.5B exactly as the default baseline.

## Consequences

The next implementation can build and test root flux physics without contaminating the frozen V3 pipeline. Pipeline integration requires a later comparison with conservation, timestep refinement, restart equivalence, deterministic repeat, multi-step lag behavior and explicit time-profile semantics.

No full Richards/Darcy hydrology, transpiration solver, hidden delay buffer, calibration or parameter activation is authorized by this ADR.
