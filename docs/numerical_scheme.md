# Numerical scheme

The default solver is a conservative explicit inventory update with 600 s
steps and piecewise forcing. Water losses are capacity-limited. Concurrent HTO
outflows are proportionally scaled if they would exceed the source compartment;
this avoids using a final `max(0)` to conceal imbalance. One-step-lagged
re-emission prevents an algebraic feedback loop.

Mass balance is calculated after every step. In the final acceptance runs,
maximum relative errors were `3.999127e-16` (synthetic 48 h),
`4.336388e-16` (ERA5 48 h), and `4.425898e-16` (advanced modes 24 h).

SciPy `DOP853` references are provided for both the fixed-rate inventory system
and a continuous four-state water/soil/TFWT/OBT forcing step. A refined explicit
solution converges to the continuous reference.

For the complete synthetic 48 h case, 600 s versus 300 s final relative
differences were:

| Quantity | Relative difference |
|---|---:|
| soil HTO inventory | 0.03898% |
| plant TFWT inventory | 0.13154% |
| plant OBT inventory | 0.11007% |
| total re-emission flux | 0.18287% |

These are below the 2% engineering regression threshold while both step sizes
retain machine-precision mass closure.

## Formal minimal baseline v1 update

The ledger is explicitly the soil + TFWT + OBT surface box. The steady Gaussian
atmosphere has a separate source/sink budget and no dynamic air inventory.
Re-emission uses a physical 3600 s FIFO delay at either internal step. Rain is
partitioned into infiltration and runoff before rainwater HTO is routed.

Recomputed 600/300 s differences are soil 0.02360%, TFWT 0.13859%, OBT
0.12093%, and integrated re-emission 0.04974%. Maximum surface-box relative
residuals are `4.320656e-16` (synthetic), `4.040362e-16` (ERA5), and
`2.478100e-16` (advanced).
