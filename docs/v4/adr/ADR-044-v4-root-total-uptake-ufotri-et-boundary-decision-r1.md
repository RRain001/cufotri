# ADR-044: V4 root total-uptake UFOTRI ET boundary decision R1

## Status

Accepted.

## Context

The V4 root core now has a controlled UFOTRI 20/40/40 layer-distribution profile, but it still requires an explicit total plant-water uptake/transpiration flux. `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED` therefore remains false.

The repository already implements UFOTRI equations 38–43 in `meteorology/fallback_fluxes.py`. That path computes potential evapotranspiration, partitions soil evaporation and plant transpiration by LAI, applies the UFOTRI moisture-reduction function and wilting cutoff, and returns `root_uptake_m_s = plant_transpiration_m_s`.

The recovered UFOTRI Eq.38 empirical aerodynamic term is not dimensionally closed by the available manual. The current configuration coefficient `0.001 W m^-2 Pa^-1` is explicitly a project assumption. Promoting it would conflict with the selected route of using UFOTRI parameters rather than inventing or calibrating new values.

## Decision

Select the existing UFOTRI Eq.39 equilibrium-radiation form as the controlled total-uptake baseline for the next V4 implementation stage. In the existing formulation this is obtained by setting the unresolved aerodynamic coefficient to exactly zero.

The total root-water uptake boundary is:

`q_w,total = plant_transpiration_m_s`.

The subsequent already-adopted root profile maps that total as:

`q_w,i = q_w,total * (0.2, 0.4, 0.4)`.

The Eq.39 adapter must keep meteorological forcing, LAI, soil-water state, maximum/wilting-water values and physical conversion quantities explicit and provenance-bearing. It must not infer any of them inside `root_v4`.

## Rejected alternative

The full Eq.38 Penman reconstruction is not selected for the controlled V4 baseline because its empirical aerodynamic coefficient remains provisional/project-defined.

## Authorization

Authorize `V4_ROOT_TOTAL_UPTAKE_UFOTRI_EQ39_IMPLEMENTATION_R1` to implement a typed opt-in V4 boundary around the already existing Eq.39-compatible calculations and connect it to the 20/40/40 root profile.

This decision does not yet set `ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=TRUE`; that state can change only after implementation and numerical integration demonstrate an explicit, complete input path.

## Non-decisions

No full hydrology, 3 h physiological delay, calibration, empirical validation, physical-accuracy claim, Leaf R5, multi-pool OBT, real CTEAS-Atmos binding, or V3 default-path change is authorized.
