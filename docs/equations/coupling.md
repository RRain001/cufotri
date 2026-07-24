# Coupling

Each 600 s step reads forcing, computes primary Gaussian concentration, adds the
previous step's integrated re-emission area plume, calculates deposition and water fluxes,
updates water/soil/plant/OBT inventories, then stores re-emission for the next
step. This explicit lag implements the manual's secondary-plume sequencing in a
stable, testable form.

Per-step HTO closure is:

\[
M_0+I_{external}-O_{boundary}-D-M_1=\epsilon.
\]

Root uptake, OBT formation, and OBT turnover are internal transfers and appear
on both sides of compartment balances, not as system boundaries.

The forcing provider is rejected if it has insufficient rows or a start time
different from the UTC case start; the final row is never silently repeated.

Feedback is delayed exactly 3600 s, independent of internal step. Closure
applies only to the soil + TFWT + OBT surface box. The steady Gaussian
atmosphere reports a source/sink ledger, not a dynamic air inventory.

## Deposition activity interface

Dry and wet deposition use the plume loss as the only authoritative activity
source. For pathway \(p\in\{d,w\}\) and an explicitly configured uniform
footprint \(A_p\),

\[
\dot Q_{p,\mathrm{surface}}=\dot Q_{p,\mathrm{plume\ loss}},
\qquad
F_p=\frac{\dot Q_{p,\mathrm{plume\ loss}}}{A_p}.
\]

The dry and wet footprints are separate configuration objects. Neither is
inferred from the re-emission feedback rectangle. Changing a footprint
therefore changes only the local surface flux, not the total activity
transferred across the interface.

Dry and wet losses compete for the same source within each plume segment:

\[
Q_{j+1}=Q_j\exp[-(\Lambda_d+\Lambda_w)\Delta t],
\]

\[
\Delta Q_d=(Q_j-Q_{j+1})
\frac{\Lambda_d}{\Lambda_d+\Lambda_w},\qquad
\Delta Q_w=(Q_j-Q_{j+1})
\frac{\Lambda_w}{\Lambda_d+\Lambda_w}.
\]

Both losses are zero when the combined rate is zero. The local diagnostic
\(v_dC_a\) is retained for comparison only and is not an inventory input.
