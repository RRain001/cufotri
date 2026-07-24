# V2 full-model uncertainty convergence

Recompute with:

```bash
.venv/bin/python scripts/run_v2_uncertainty_convergence.py \
  --output /tmp/v2_uncertainty_convergence.json
```

This audit starts from `v2_full_adult_dose` and retains its deposition, crop,
animal-product, and adult-dose modes. To make repeated convergence runs
practical, it uses a declared 24 h audit horizon and 3600 s step. This is an
uncertainty-method acceptance case, not the formal 14 d dose result.

## Mode-aware parameters

The audited case samples nine active parameters:

```text
deposition_velocity
pasture_max_lai
initial_soil_water
maximum_soil_water
obt_formation_rate
feed_intake
beef_turnover
adult_hto_dose_coefficient
adult_obt_dose_coefficient
```

Seven parameters are recorded as `inactive_by_mode`: wet-scavenging `a,b`
because wet scavenging is off; generic-crop LAI because pasture is active;
advanced re-emission because `basic_mass_flux` is active; two leaf-resistance
parameters because leaf exchange is off; and adult leafy intake because the
active crop is pasture. These parameters are excluded, not reported as having
zero sensitivity.

## Sample-size and seed evidence

Primary seed `20260724` gives:

| LHS n | median (Sv) | P5 (Sv) | P95 (Sv) | mean (Sv) | std (Sv) |
|---:|---:|---:|---:|---:|---:|
| 64 | 1.063556e-6 | 9.603677e-7 | 1.169683e-6 | 1.064444e-6 | 6.883285e-8 |
| 128 | 1.064500e-6 | 9.581111e-7 | 1.169726e-6 | 1.064389e-6 | 6.855520e-8 |
| 256 | 1.064083e-6 | 9.582832e-7 | 1.170620e-6 | 1.064406e-6 | 6.841301e-8 |

The largest relative change from n=128 to n=256 across median, P5, P95, mean,
and standard deviation is 0.208%. Therefore the formal minimum is n=256 and
`SAMPLE_SIZE_CONVERGENCE_STATUS = PASS`.

At n=256, seeds `20260724`, `20260725`, `20260726`, and `20260727` all produce
ordered positive quantiles and non-zero variance. The adult HTO dose
coefficient is the dominant Spearman parameter for every seed. The full
nine-parameter order is not stable: minimum pairwise Spearman is 0.15 because
the remaining effects are weak and exchange rank between seeds. It is reported
as:

```text
RANK_STABILITY_STATUS = LIMITED_WITH_EVIDENCE
```

This is not promoted to a stronger ranking claim. Same-seed outputs are exactly
reproducible. The audit performs 1280 actual full-model reruns, verifies that
every active sampled parameter spans a non-zero range, and records the active
and inactive lists in JSON.
