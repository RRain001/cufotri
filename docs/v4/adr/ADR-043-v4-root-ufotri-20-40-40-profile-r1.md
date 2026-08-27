# ADR-043: V4 UFOTRI 20/40/40 root-distribution profile R1

## Status

Accepted for implementation.

## Context

The V4 three-layer root core already requires explicit layer water-uptake fluxes `q_w,i` and evaluates `J_root,i = q_w,i C_w,i`. It deliberately does not infer hydrology or transpiration.

UFOTRI KfK 4605 chapter 3.3.2 assigns 20%, 40% and 40% of total plant water uptake to the 0–5, 5–15 and 15–30 cm root-zone layers. UFOTRI does not establish one universal fixed total plant-water uptake flux; total uptake is tied to plant water demand/transpiration. The manual also reports long-term compartment transfer rates near 0.026, 0.026 and 0.017 d^-1, but those are not m/s layer water fluxes and cannot be substituted for `q_w,i`.

## Decision

Implement an opt-in controlled UFOTRI root profile that accepts an explicit total plant water-uptake flux in `m s^-1` and maps it to the existing typed V4 forcing as:

`(q_w,L1, q_w,L2, q_w,L3) = q_w,total * (0.2, 0.4, 0.4)`.

The adapter must preserve plant identity, UTC timestamp, provenance and unit identity and fail closed on negative, non-finite or wrong-unit input.

## Activation meaning

After this stage passes, `UFOTRI_20_40_40_CONTROLLED_PROFILE_ACTIVE=TRUE` means only that the UFOTRI layer fractions are available as an explicit V4 profile. It does not mean the upstream total water-uptake forcing has been resolved for production.

`ROOT_Q_W_PRODUCTION_INPUT_RESOLVED` therefore remains `FALSE`.

## Non-decisions

This stage does not activate the UFOTRI 0.026/0.026/0.017 d^-1 compartment rates as water fluxes, does not implement the short-term 3 h delay, and does not add hydrology or plant-water dynamics. It does not alter V3, calibrate parameters, claim empirical validation or physical accuracy, enable Leaf R5, implement multi-pool OBT, or bind real CTEAS-Atmos output.

## Verification

Tests must prove the exact 20/40/40 fractions, total-flux identity, zero behavior, fail-closed validation, provenance/time preservation and compatibility with the existing root solver's `J=q_w C_w` and conservation ledger.
