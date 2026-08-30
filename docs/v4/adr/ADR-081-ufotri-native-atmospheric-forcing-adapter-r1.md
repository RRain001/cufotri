# ADR-081 — UFOTRI Native Atmospheric Forcing Adapter R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1`

## Context

H1 reconstructs the UFOTRI-native straight-segment Gaussian transport core and H2 reconstructs the hourly segmented MUSEMET trajectory. The existing environmental chain already owns typed HTO forcing (P7), typed HT forcing (E1), HT soil deposition, and the E2 HT→HTO soil conversion boundary.

H3 must connect these components without creating a parallel environmental API or falsely attributing UFOTRI-native results to replay or CTEAS-Atmos.

## Decision

1. Add `HTForcingSourceKind.UFOTRI_NATIVE` to the existing E1 HT contract. `REAL_CTEAS_ATMOS` remains fail-closed.
2. Native HT is mapped by identity into `AtmosphericHTForcing`, then through the existing `HTSoilDepositionBoundary` and E2 `convert_deposited_ht_to_soil_hto` path.
3. Native HTO is mapped by identity into the existing P7 `AtmosphericHTOForcing` contract.
4. H1/H2 do not own every ancillary field required by the P7 HTO contract. H3 therefore requires interval, temperature, humidity, precipitation, sampling height and provenance explicitly through `NativeForcingContext`; none are inferred.
5. `NativePrimaryTransportResult.wet_source_loss_bq_s` is a plume/source ledger quantity and is not a local ground flux. If it is nonzero, H3 requires an explicit local wet-deposition flux. Without one, adaptation fails closed.
6. H3 never claims a numerical spatial integral linking plume wet source loss to one local surface flux. That reconciliation belongs to atmospheric-process/spatial deposition work, not an interface adapter.
7. Atmospheric HT→HTO conversion remains disabled on the KfK 4605 path and any nonzero generated atmospheric HTO is rejected.

## Ledger requirements

- native concentration equals mapped concentration;
- mapped surface flux equals native dry surface flux plus an explicitly supplied local wet flux;
- the H1 source-depletion residual must already close;
- native HT deposition integrated over the interval equals the E1 soil boundary amount;
- E2 generated HTO equals deposited HT activity and its activity ledger closes;
- chemical form and provenance remain explicit at every handoff.

## Non-decisions

H3 does not recover washout coefficients, source-depletion numerics, building wake, thermal lift/effective release height, secondary re-emission transport, CTEAS-Atmos binding, production parameters, calibration, empirical validation, or original-executable numerical equivalence. Those topics remain outside H3.

## Acceptance

Expected machine result:

`PASS_UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER`

After exact-head CI and merge/no-drift certification, a separate roadmap status sync must mark H3 complete and authorize H4.
