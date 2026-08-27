# Independent review: V4 food-intake-dose endpoint adapter implementation R1

## Verdict

`PASS_INDEPENDENT_REVIEW_WITH_INTERPRETATION_BOUNDARIES`

The implementation is consistent with the merged terminal-adapter decision and remains within the authorized scope.

## Review findings

1. The implementation is opt-in under `cteas_ufotri.v4_integration`; the frozen V3 default pipeline is not changed.
2. The adapter composes existing V3 food, intake, and dose solvers instead of replacing their equations.
3. `OBT_ONLY` and `OBT_PLUS_TFWT` are explicit request modes. No TFWT fraction is inferred from the OBT fraction.
4. Plant, crop, growth-stage, product, age, radionuclide, and pathway identities fail closed at the system boundary.
5. `H-3` and `food-ingestion` are explicit exact identities for this R1 path.
6. Replay source support remains `soil_surface_area`. No leaf/harvest/other area conversion is introduced.
7. Food-product and consumption bases require direct V3.1 mass/tissue/area compatibility. No numerical fresh/dry/water/hydrogen conversion is implemented.
8. Endpoint state is fingerprinted before evaluation and confirmed unchanged after evaluation.
9. The food/intake/dose readout is terminal diagnostic output, not an environmental mass sink or a depleted continuation state.
10. Provenance remains separately attributable to replay TFWT, replay OBT, harvest, both basis declarations, consumption, and dose.
11. The certified machine fixture passed deterministic repeat, timestamp preservation, internal food balance, identity, provenance, and no-conversion checks.
12. The exact implementation head passed both Protected and Remediation CI.

## CI evidence

Certified implementation head: `7118fb227045500b58391b0144f2cb639579dce3`.

- Protected `33035667912`: SUCCESS.
- Remediation `33035667915`: SUCCESS.
- portable: `1269 passed, 1 skipped, 57 deselected`.
- frozen/current: `337 passed`.
- sensitivity: `PASS_SOFTWARE_SCREENING`.
- root operator split: `PASS_SELECTION`.
- soil-root-TFWT-OBT: `PASS_INTEGRATION`.
- replay orchestration: `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`.
- endpoint adapter: `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.

The GitHub pull-request workflow checked out synthetic merge ref `8e7656b741ee27948952d36606bf9d8dab6cee26`; this is not substituted for the certified branch head above.

## Failed-attempt disposition

Head `7df074c25f2ef7aaf7553aa57bf384e86851d5ac` is explicitly non-certified. Its Protected failure was confined to an exact binary floating-point comparison in the newly introduced synthetic machine assertion. The observed dose `1.9999999999999997e-09 Sv` is numerically the expected `2.0e-9 Sv` within the subsequently frozen `1e-12` relative tolerance. No adapter source, upstream solver, replay physics, or V3 runtime failure was identified.

## Interpretation boundaries

This review does not claim:

- empirical validation;
- production parameter readiness;
- physical uncertainty characterization;
- real CTEAS-Atmos coupling;
- correctness of provisional harvest fractions, food masses, consumption rates, or dose coefficients for any real scenario;
- authorization for repeated/state-mutating harvest or continuous food-chain kinetics.

The successful synthetic endpoint execution proves only that the frozen software contracts compose coherently under the tested inputs and fail closed at the reviewed boundaries.

## Holds preserved

- `ACTIVE_PARAMETERS=0`;
- calibration = false;
- Leaf R5 = HOLD;
- OBT redesign = HOLD;
- full hydrology = HOLD;
- real CTEAS-Atmos binding = false;
- numerical mass-basis conversion = false;
- numerical area conversion = false;
- state-mutating/repeated harvest = false.

## Roadmap recommendation

After closure exact-head CI and no-drift merge, proceed only to `V4_SYSTEM_POST_ENDPOINT_REVIEW_R1` on a new isolated branch.

The post-endpoint review should reassess the full chain as a system and select the next blocker based on scientific importance, evidence availability, and coupling necessity. It should not reopen Leaf R5, OBT redesign, hydrology, parameter activation, or real Atmos binding by default.
