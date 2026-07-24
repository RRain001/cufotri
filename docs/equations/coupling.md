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
