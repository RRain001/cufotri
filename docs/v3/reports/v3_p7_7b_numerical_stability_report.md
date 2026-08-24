# V3 P7.7B Numerical Stability Report

## Timestep schedules

The declared schedules use `dt`, `dt/2`, and `dt/4`. The decay, leaf/TFWT,
and TFWT/OBT cases run a 40-second horizon from a 10-second base step. The
Soil/Root case runs a 20-second horizon from the same base step. The
end-to-end case runs a 40-second horizon and uses the frozen pipeline operator
split.

## Refinement evidence

The values below are absolute differences between adjacent final states. The
acceptance rule allows a `1e-12` floating-point comparison tolerance and
requires a non-increasing refinement trend.

| Case | `|dt - dt/2|` | `|dt/2 - dt/4|` | Trend |
| --- | ---: | ---: | --- |
| radioactive decay | `4.440892098500626e-15` | `7.105427357601002e-15` | PASS within tolerance |
| leaf exchange → TFWT | `0` | `0` | PASS |
| TFWT → OBT | `3.552713678800501e-15` | `5.329070518200751e-15` | PASS within tolerance |
| Soil → Root | `1.0000000000331966e-4` | `4.995000624319346e-5` | PASS |
| end-to-end pathway | `1.0240590275390566` | `5.002245510404428e-1` | PASS |

The decay and TFWT/OBT increases are below the declared floating-point
tolerance; they are not interpreted as numerical divergence. The end-to-end
differences are expected from the existing operator split and are recorded as
a convergence trend only.

## Boundary

This report is a software numerical-stability result. It is not a claim that
the selected half-life, resistance, `kf`, `kr`, root coefficient, harvest,
consumption, or dose values are physically valid.
