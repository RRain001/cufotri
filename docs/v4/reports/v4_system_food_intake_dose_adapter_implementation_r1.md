# V4 system food-intake-dose endpoint adapter implementation R1

## Outcome

`PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION_AWAITING_CLOSURE_GATE`

The implementation head `7118fb227045500b58391b0144f2cb639579dce3` passed both exact-head CI systems:

- Protected run `33035667912`: SUCCESS;
- Remediation run `33035667915`: SUCCESS;
- portable suite: `1269 passed, 1 skipped, 57 deselected`;
- explicit frozen/current suite: `337 passed`;
- endpoint machine gate: `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.

This is a software-integration result only. The endpoint runner uses synthetic test inputs and does not establish empirical validation, parameter readiness, physical uncertainty, or real CTEAS-Atmos coupling.

## What was implemented

The opt-in V4 boundary now exposes `V4FoodIntakeDoseEndpointAdapter`. It consumes a completed `V4SoilRootTFWTOBTState` and an explicit `V4TerminalHarvestRequest`, then composes the already existing V3 `FoodTransferSolver`, `FoodIntakeSolver`, and `DoseSolver` without re-deriving or changing their equations.

Two terminal diagnostic modes are explicit: `OBT_ONLY` and `OBT_PLUS_TFWT`. The adapter validates endpoint plant/crop/growth-stage identity, exact food-product and age-group identity, `H-3`, `food-ingestion`, `soil_surface_area`, and direct V3.1 mass/tissue/area-basis compatibility before evaluating the downstream chain.

The endpoint object is fingerprinted before evaluation and compared after evaluation. The certified tests demonstrate that the diagnostic readout does not mutate the upstream replay state. The downstream branch is therefore not inserted as an environmental mass sink.

## Basis and geometry boundary

No numerical fresh/dry/water/hydrogen conversion exists in this implementation. No area conversion exists either. The only geometry operation remains the existing food-transfer operation on the same soil-surface support:

`Bq m^-2 * harvest_area_m2 -> Bq`.

Food-product and consumption mass bases must be declared through two `MassBasisContract` values and pass `require_direct_comparison`. A mismatch fails closed.

## Provenance

The composite audit retains independently owned provenance for replay TFWT, replay OBT, harvest, food-product basis, consumption basis, consumption data, and dose coefficient. It does not collapse these domains into one synthetic provenance record.

## Certified synthetic endpoint result

For the explicit machine fixture:

- mixed OBT+TFWT mode: food = 25 Bq, annual intake = 100 Bq/year, committed dose = `1.9999999999999997e-09 Sv`;
- OBT-only mode: food = 10 Bq, annual intake = 40 Bq/year, committed dose = `7.999999999999999e-10 Sv`;
- endpoint unchanged = true;
- deterministic repeat = true;
- endpoint timestamp preserved = true;
- internal food-transfer balance closed = true;
- independent provenance retained = true;
- no basis conversion = true;
- no area conversion = true;
- not an environmental mass sink = true.

These numbers are fixture outputs, not project predictions or validated dose estimates.

## Superseded first attempt

The earlier head `7df074c25f2ef7aaf7553aa57bf384e86851d5ac` is not certification evidence. Its Remediation run passed, while Protected run `33035343479` failed only because the new synthetic machine runner compared the mathematically expected `2.0e-9 Sv` against binary floating-point output `1.9999999999999997e-09 Sv` with exact equality.

At that failed head, the portable suite, frozen suite, and the four previously established V4 machine gates all passed. The correction was limited to replacing the exact machine assertion with `math.isclose(..., rel_tol=1e-12)`. The branch was rewritten to one clean commit directly based on the unchanged main baseline.

## Interpretation

The north-star software chain can now be exercised, in opt-in synthetic software form, through replay endpoint -> terminal food -> annual intake -> dose without modifying the frozen V3 default. That does not mean the scientific model is production-ready. The principal unresolved items remain evidence/physics/data questions rather than a missing software link at this endpoint.

Accordingly, this stage does not authorize Leaf R5, OBT redesign, full hydrology, parameter activation/calibration, numerical basis conversion, repeated/state-mutating harvest, or real CTEAS-Atmos binding.

## Next-stage gate

If and only if the governance closure exact head passes both Protected and Remediation CI and merges by expected head without tree drift, the next isolated stage is:

`V4_SYSTEM_POST_ENDPOINT_REVIEW_R1`

That stage is control-plane only. Its purpose is to review the full north-star chain after endpoint software closure and select the next evidence or physics blocker. It must not automatically promote any existing hold merely because the synthetic software path is now complete.
