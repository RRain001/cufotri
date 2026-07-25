# Parameter-identifiability protocol

```text
PARAMETER_IDENTIFIABILITY_STATUS =
NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE
```

Allowed final states are only:

```text
IDENTIFIABLE
PARTIALLY_IDENTIFIABLE
NON_IDENTIFIABLE
NOT_ASSESSED
```

## Required diagnostics

1. Profile likelihood or an equivalent one-parameter profile for every free
   parameter, using preregistered confidence/likelihood thresholds.
2. Parameter correlation matrix from the local Hessian, posterior samples, or
   profile-equivalent evidence.
3. Scaled Jacobian/Fisher information singular values and condition number.
4. Explicit lower/upper boundary-hit flags and distance from bounds.
5. Posterior or profile interval width relative to the prior/bound range.
6. Stability across independent experimental repeats or preregistered
   calibration resamples.
7. Separate calibration and untouched holdout metrics.
8. Multi-parameter compensation diagnostics using profiles, pairs, or
   sensitivity directions.

Numerical thresholds for correlation, condition number, profile closure,
interval width, and repeat stability must be frozen in the preregistration.
Optimizer convergence alone never proves identifiability.

## Decision and reduction rules

- `IDENTIFIABLE`: every required active parameter has a bounded profile,
  acceptable conditioning/correlation, no unexplained boundary hit, and stable
  repeat/holdout behavior.
- `PARTIALLY_IDENTIFIABLE`: only a documented subset or parameter combination
  is supported; unsupported degrees of freedom are fixed or reparameterized.
- `NON_IDENTIFIABLE`: bounds, profiles, Jacobian rank, compensation, or repeat
  instability prevent a defensible parameter conclusion.
- `NOT_ASSESSED`: complete executable data or required diagnostics are absent.

When non-identifiable, reduce dimensionality by fixing the weakest parameter to
a sourced value, replacing correlated parameters by one identifiable
combination, or removing the unsupported process. Repeat diagnostics on
calibration data without inspecting or tuning to the holdout.
