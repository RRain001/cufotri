# V2 benchmark cases

Run:

```bash
.venv/bin/python scripts/run_v2_benchmarks.py
```

The suite recomputes fifteen cases:

1. V1 regression;
2. no-rain dry deposition;
3. strong-rain wet scavenging;
4. daytime one-hour HTO release;
5. nighttime one-hour HTO release;
6. one-hour accident followed through 72 h of re-emission;
7. release during crop growth;
8. pre-harvest release;
9. pasture-to-milk pathway;
10. full adult research-screening dose;
11. zero source;
12. extremely low wind;
13. extremely dry soil;
14. saturated rain;
15. formal single-layer status plus experimental three-box comparison.

All cases require finite, non-negative physical outputs and a mass residual
below 1e-10. Additional invariants require exact zero-source air concentration,
lower air concentration with strong-rain washout than the dry case, positive
milk concentration in the pasture case, and positive dose in the full case.

No complete public UFOTRI numeric benchmark dataset was available in the
repository. Manual calibration anchors have separate unit tests; this suite
therefore establishes project regression, limiting-condition, monotonicity,
pathway, and conservation evidence rather than external field validation.
