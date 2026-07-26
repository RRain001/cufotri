# SB4 transfer mass-balance report

All 42 combinations of three mechanisms, two chamber profiles and seven
forcing scenarios are finite, nonnegative and pass the frozen conservation
criteria.

| quantity | maximum | frozen tolerance |
|---|---:|---:|
| formal mass-closure residual | 3.725290e-9 Bq m-2 | 1.0e-6 Bq m-2 |
| paired internal-transfer ledger residual | 0 Bq m-2 | 1.0e-9 Bq m-2 |
| disclosed internal state-sum roundoff | 2.146407e-9 Bq m-2 | diagnostic only |

The H2/H3 paired flux audit uses `math.fsum` over equal-and-opposite capture
and release entries. It does not change state updates, parameters, forcing or
the frozen `1.0e-9 Bq m-2` internal-transfer tolerance. The larger state-sum
diagnostic is retained separately because subtracting two large total states
can lose low-order floating-point bits; it is not substituted for the paired
activity ledger.

```text
MASS_BALANCE_STATUS = PASS_42_OF_42
FINITE_NONNEGATIVE_STATUS = PASS_42_OF_42
INTERNAL_TRANSFER_CONSERVATION = PASS_H2_AND_H3
TOLERANCE_RELAXATION_COUNT = 0
```
