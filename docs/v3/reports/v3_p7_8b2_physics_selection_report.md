# V3 P7.8B-2 Physics Selection Report

Date: 2026-08-24
Branch: `codex/v3-p7-8b2-physics-selection`
Baseline: `codex/v3-p7-8b1-redesign-specification` at `9d3ba09`

## Disposition

```ini
P7_8B2_STATUS = PASS_PHYSICS_SELECTION
FINAL_MODEL_CHOICES_DEFINED = TRUE
V3_1_ROADMAP_DEFINED = TRUE
V4_ITEMS_DEFINED = TRUE
VALIDATION_DEPENDENCY_DEFINED = TRUE
IMPLEMENTATION_ORDER_FROZEN = TRUE
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The canonical decision registry is
`docs/v3/physics/p7_8b2_physics_selection.yaml`. This stage selects future
architecture and implementation order. It does not implement a candidate,
assign a parameter value, start calibration, or change the runnable V3
profile.

## Final choices

| Scope | Selected direction | Stage | Decision | Future impact |
|---|---|---:|---|---|
| OBT formation, day/night, activity, temperature | Precursor plus exchangeable/non-exchangeable OBT pools | V4 | `SELECTED_FOR_V4` | `INTERFACE_EXTENSION` |
| OBT plant mass basis | Typed basis/tissue/area/provenance contract | V3.1 | `SELECTED_FOR_V3_1` | `INTERFACE_EXTENSION` |
| Root uptake | Layered water-flux coupling `J_root,i = q_w,i C_w,i` | V4 | `SELECTED_FOR_V4` | `NUMERICAL_COUPLING_CHANGE_REQUIRED` |
| Leaf exchange | Dynamic stomatal response at the existing resistance boundary | V4 | `SELECTED_FOR_V4` | `INTERFACE_EXTENSION` |
| Soil transport | Existing one-layer signed transport interface | Maintained | `KEEP_CURRENT` | `NO_IMPACT` |
| TFWT water storage | Existing fixed-storage activity ledger | Maintained | `KEEP_CURRENT` | `NO_IMPACT` |
| Food environmental transfer | Existing separate OBT/TFWT harvest-event transfer | Maintained | `KEEP_CURRENT` | `NO_IMPACT` |
| Consumption | External scenario input | Maintained | `KEEP_CURRENT` | `NO_IMPACT` |
| Dose | External dosimetry/regulatory layer | Maintained | `KEEP_CURRENT` | `NO_IMPACT` |

The word “selected” means selected for a future, separately authorized profile.
It does not mean implemented, validated, calibrated, or equivalent to UFOTRI.

## OBT decision

The current equation remains

\[
\frac{dB}{dt}=k_fT-k_rB.
\]

The selected V4 direction is the smallest candidate that separates formation
forcing from OBT turnover:

\[
\begin{aligned}
\frac{dP}{dt} &= u_P(T,A,d,s,T_{leaf})-k_PP,\\
\frac{dB_x}{dt} &= k_{PB}P-(k_x+k_{xn})B_x,\\
\frac{dB_n}{dt} &= k_{xn}B_x-k_nB_n.
\end{aligned}
\]

The candidate retains the aggregate readout `B = B_x + B_n`, but only after
the biological scope of the two pools is frozen. Day/night, activity, and
temperature are forcing/state contracts with provenance, not hard-coded
values. Organ-specific growth/allocation is rejected as the first target
because current evidence cannot identify the added states.

## Root decision

The current effective-velocity boundary remains the baseline. The selected
V4 direction is

\[
J_{root,i}=q_{w,i}C_{w,i}, \qquad
M_{s,i}=\theta_i\Delta z_i C_{w,i}.
\]

This selection is based on dimensional transparency and a possible validation
path through layer-resolved soil-water activity, moisture, root distribution,
and transpiration. It does not authorize a scalar-to-layer conversion. The
moisture-dependent response is rejected as a standalone architecture; it may
be reconsidered only as a bounded closure inside a water-flux/layer contract.

Because the root state changes ownership and conservation boundaries, it is a
`NUMERICAL_COUPLING_CHANGE_REQUIRED` item. A future implementation must pass a
new P7.5/P7.5B review, layer/global conservation, restart, refinement, and
failure-behavior tests.

## Soil, leaf, TFWT, and food decisions

The leaf candidate is selected for V4 only at the interface-architecture
level:

\[
g_s(t)=g_{s,max}F_{light}F_{vpd}F_{temp}F_{stage},
\qquad r_c(t)=1/g_s(t).
\]

The current resistance chain remains the default. Response functions,
domains, bounds, and values require matched data and independent review.

The soil signed-transport interface and fixed TFWT storage remain unchanged.
Full soil hydrology and TFWT water turnover are recorded as
`INSUFFICIENT_EVIDENCE`; neither is inferred from synthetic trajectories or
from an activity-only input.

Food environmental transfer remains the current harvest-event boundary, with
OBT and TFWT product inventories kept separate. A continuous-only product
rate is rejected for this roadmap and a hybrid product state remains
`INSUFFICIENT_EVIDENCE`. Consumption and dose remain external layers and
cannot select environmental equations.

## Rejected and unresolved candidates

The registry explicitly rejects:

- importing unreviewed UFOTRI values;
- converting a root rate to a velocity with an assumed length;
- relabelling a continuous food rate as a harvest fraction;
- using dose behavior to redesign environmental physics;
- organ-specific OBT growth as the first future target;
- a standalone moisture response for root uptake;
- continuous-only food product physics;
- a TFWT growth correction in place of a water-mass ledger.

It keeps the following candidates unresolved rather than guessing:

- full or layered soil hydrology;
- dynamic TFWT water turnover;
- hybrid product-state transfer;
- bounded moisture closure inside the selected root architecture.

## Non-changes and scientific boundary

No solver, plant, soil, food, exposure, pipeline, coupling, or parameter-runtime
source is changed by this decision. P7.5 and P7.5B semantics remain frozen.
`ACTIVE_PARAMETERS` remains zero and `V3_PHYSICS_READY` remains false.

The P7.7B synthetic benchmark continues to be software/interface evidence
only. It does not supply empirical observations, validate candidate rates, or
establish environmental realism. Every selected model remains value-free and
requires its own equation, unit, state, validation, coupling, and independent
review gates before P7.8C implementation.
