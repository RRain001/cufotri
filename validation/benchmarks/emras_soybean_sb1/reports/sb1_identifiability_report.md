# SB1 identifiability report

```text
CALIBRATION_POINTS = 0.2,1,24,120,336 h
PARAMETER_COUNT = 2
JACOBIAN_RANK = 2_OF_2
MAX_ABS_PARAMETER_CORRELATION = 0.307438
BOUNDARY_HIT = TRUE
IDENTIFIABILITY_STATUS = LIMITED_BOUNDARY_OR_CORRELATION
```

The bounded 7-by-7 grid selected:

| parameter | selected | bounds | bounds source |
|---|---:|---:|---|
| daytime stomatal resistance | 800 s/m | 200--800 s/m | formal default uncertainty specification |
| leaf characteristic length | 0.10 m | 0.02--0.10 m | formal default uncertainty specification |

Both selected values are at their upper bounds. Although the local
finite-difference Jacobian has full column rank and modest column
correlation, the calibration retains a -1.029 log10 mean bias and a 0.048
median predicted/observed ratio. The numerical rank is therefore not treated
as evidence of global or empirical identifiability.

The frozen parameter-result hash is
`51609eadd468b64d6aff9953b9c316f9ebbad53121ae6e8f50bda76b8ab57687`.
The late plant-body and pods points were not used to select parameters or
bounds.
