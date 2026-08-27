# ADR-045: V4 UFOTRI Eq.39 total root-water uptake implementation R1

## Status

Accepted for implementation and numerical integration.

## Context

ADR-044 selected the UFOTRI Eq.39 equilibrium-radiation form as the controlled V4 total root-water uptake boundary. The already merged root profile distributes total uptake to L1/L2/L3 as 20/40/40, but production root `q_w` remained unresolved until the total-uptake boundary was implemented with explicit inputs.

## Decision

Implement an opt-in typed V4 adapter with explicit, provenance-bearing inputs for meteorology, case/state quantities and physical conversion constants. The selected total potential evapotranspiration is evaluated directly from Eq.39:

`E_p = [Delta / (Delta + gamma)] R_n / (lambda rho_w)`.

No dewpoint, wind or empirical aerodynamic coefficient enters this Eq.39 calculation. Negative net radiation is clipped to zero consistently with the existing fallback-flux semantics.

Existing UFOTRI Eq.40-43 logic then partitions potential evapotranspiration using LAI, applies the Eq.41 moisture-reduction factor and the wilting cutoff, and retains the identity:

`q_w,total = root_uptake_m_s = plant_transpiration_m_s`.

The existing controlled root profile then applies:

`(q_w,L1, q_w,L2, q_w,L3) = q_w,total * (0.2, 0.4, 0.4)`.

## Provenance and fail-closed contract

Meteorology, case/state inputs and physical constants retain independent provenance records. UTC time, units and physical-domain bounds are checked before evaluation. Missing/wrong provenance types, wrong units, non-finite values and physically invalid bounds fail closed.

## Resolution state

After the implementation and numerical integration gates pass, `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=TRUE` means the controlled V4 construction path for root `q_w` is explicit and complete when the caller supplies the required meteorology, LAI, soil-water state and physical constants.

This does not imply full-model production readiness, empirical validation, calibration, a full hydrology model, the UFOTRI 3 h delay, real CTEAS-Atmos binding or physical-accuracy validation.

## Non-decisions

The Eq.38 empirical aerodynamic coefficient remains rejected from the controlled baseline. The UFOTRI 0.026/0.026/0.017 d^-1 compartment rates remain distinct evidence and are not converted to m/s. V3 defaults and the selected `PRESERVE_V3_POST_OBT_ROOT_GAIN` operator split remain unchanged.
