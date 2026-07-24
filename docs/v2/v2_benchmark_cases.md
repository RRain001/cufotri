# V2 benchmark and scenario evidence

Run:

```bash
.venv/bin/python scripts/run_v2_benchmarks.py
```

The JSON output assigns every check exactly one of these evidence categories:

- `analytic_benchmark`: an implementation result compared with an independently
  evaluated closed-form or hand calculation;
- `manual_anchor`: a numeric UFOTRI-manual statement compared with the
  configured or implemented value;
- `literature_comparison`: a numeric value compared with an identified
  non-UFOTRI source;
- `physical_invariant`: a zero/extreme/conservation limit;
- `integration_scenario`: an executable pathway scenario without an
  independent target;
- `regression_case`: preservation of prior project behaviour.

Integration scenarios and regression cases are deliberately not called
reference or validation cases.

## Independent analytic benchmarks

There are ten analytic benchmarks, exceeding the acceptance minimum of six:

1. constant wet removal, \(Q=Q_0\exp(-\lambda t)\);
2. dry allocation under competing constant dry/wet hazards;
3. wet allocation under competing constant dry/wet hazards;
4. a fixed-conductance leaf exchange box approaching its analytic equilibrium;
5. re-emission depletion, \(M=M_0\exp(-kt)\);
6. a constant-input/first-order-output animal product box;
7. one-day public dose by hand arithmetic;
8. one-year public dose by hand arithmetic;
9. fresh-mass/water-depth TFWT conversion;
10. fresh-to-dry-mass OBT conversion.

The production functions are exercised to obtain the computed values. Targets
are calculated independently in `benchmarks/independent.py`; tolerances are
stored in each JSON record.

## Numeric manual and literature anchors

The suite checks five manual anchors and two literature comparisons:

- radiative soil re-emission: 10% per hour at the manual reference condition;
- diffusive soil re-emission: 1% per hour;
- combined daytime reference re-emission: 11% per hour;
- cow body-water half-time: 3.5 days (configured pathway gives about 3.46 d);
- cow organic-compartment half-time: approximately 40 days (configured pathway
  gives about 36.0 d and is checked with a 15% comparison tolerance);
- adult HTO coefficient: \(1.8\times10^{-11}\) Sv/Bq;
- adult OBT ingestion coefficient: \(4.2\times10^{-11}\) Sv/Bq.

The re-emission and animal anchors are from the UFOTRI manual. The dose
coefficient comparisons use the configured source label `HPA-CRCE-004 Table 1`;
they are literature comparisons, not UFOTRI validation.

## Executable scenarios and invariants

The original fifteen executable cases remain:

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

All executable cases require finite, non-negative physical outputs and a mass
residual below \(10^{-10}\). Additional invariants require exact zero-source air
concentration, lower air concentration with strong-rain washout than the dry
case, positive milk concentration in the pasture case, and positive dose in the
full case.

These checks establish analytic correctness, numeric source anchoring,
regression, limiting-condition, pathway, and conservation evidence. They do not
constitute external field validation or a complete public UFOTRI reproduction
dataset.
