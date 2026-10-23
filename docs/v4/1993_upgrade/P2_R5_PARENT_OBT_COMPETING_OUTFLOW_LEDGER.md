# P2 R5 — source-pinned parent-OBT competing-outflow activity ledger

**Status:** conditional mathematical/source audit; **not** UFOTRI 4.0's
original coupled COMA/plant/animal kinetic integrator. Draft PR #159 and
P2 Issue #128 remain open; no independent scientific acceptance.

## Primary source and bounded selection

W. Raskob, *Description of the New Version 4.0 of the Tritium Model UFOTRI
Including User Guide*, KfK 5194 (1993), printed §5.5.2 pp.22–23 and
Tables 9–12 pp.86–89; official KIT PDF:
https://publikationen.bibliothek.kit.edu/270034158/3813483.
The original PDF checksum previously verified by P2 R2/R3 is
`9a75292bc7289969db7175e17003c3dd777de72a30b52993264662dbc5c62ff5`.
The source-table transcription is **pinned** by P2 R3 SHA256
`10607b7f2911bc23f9fae138dd153bf46f20baa4b7b6669bbe5f7f4c49bfc220`.

The R3 mapping, not guessed universal plant constants, supplies these
**daily COMA ingestion-graph** parent-OBT outgoing hazards:

| Source parent OBT | Printed destination(s) and rate(s), d⁻¹ | Total, d⁻¹ |
| --- | --- | ---: |
| Grass OBT | grass HTO .024; cow HTO .018; cow OBT .0029; milk OBT .0015 | .0464 |
| Leafy plant OBT | plant HTO .032 | .032 |
| Potato **parent plant** OBT | potato HTO .069 | .069 |
| Wheat **parent plant** OBT | wheat HTO .069 | .069 |

**Do not apply parent potato/wheat losses to edible tuber/seedling OBT.**
The printed p.23 rule prohibits OBT loss from these edible compartments.
R5 requires an *independent explicitly supplied* edible OBT activity
for those two crops and holds it unchanged in this isolated test.
It rejects a separate edible OBT input for grass/leafy plant.

## Conditional mathematical operator and exact activity ledger

This is a declared hypothesis:
`ISOLATED_PARENT_COMPETING_HAZARDS_NO_FEEDBACK`.
For a parent-OBT pool `B` in Bq/m² ground, a segment duration `dt`
in hours, and **daily** source hazards `k_i` in d⁻¹, let
`K=sum_i(k_i)`. The exact competing first-order outflow operator is:

```text
F_total = B * [-expm1(-K * dt/24)]       Bq/m²
F_i     = F_total * k_i/K               Bq/m²
B_next  = B - F_total                   Bq/m²
sink_i_next = sink_i + F_i              Bq/m²
edible_next = edible                    Bq/m² (potato/wheat only)
residual = B_next + sum_i(F_i) - B      Bq/m² (each step)
```

The end-to-end residual includes the initial/final independent edible
pool and cumulative *audit receiving buckets*. The destination names
are retained as printed for traceability, but a `cow HTO`, `milk OBT`
or `plant HTO` bucket is **not a simulated physical receiving state**.
In particular, no grass OBT→grass HTO return is fed back into the R4
HTO→OBT formation operator. No animal, milk, harvest or dose result is
computed. This mathematical ledger tests a conservative partition of
**activity** only; it does not validate the mass/dry-matter basis of
1993 Eq.(31)/(33).

For one 24h test interval with 1000 Bq/m² initial parent grass OBT,
`K=.0464 d⁻¹`, the analytic retained parent is
`1000*exp(-.0464)`; the loss is distributed among four sinks by
`k_i/.0464`. Segmentation into 12h, 6h, 1h or 0.5h must preserve
the same final parent and branch totals. The analogous checks are made
for the other three crop types and 7-day durations.

## Implementation and software qualification

- `src/cteas_ufotri/plant/kfk5194_1993_p2_r5_parent_outflow_budget.py`
  adds an opt-in typed source-checked, nonnegative analytical audit.
- `tests/unit/test_ufotri_1993_p2_r5_parent_outflow_budget.py`
  independently checks all source rates and sink partitions, 24h/7d
  timestep invariance, conservation, zero activity, potato/wheat edible
  separation, wrong 1990 profile, source tampering, invalid input and
  no default/production solver import.
- Exact-HEAD Ubuntu Docker targeted and full software tests, image ID,
  run IDs and scientific readiness must be recorded **after** a candidate
  commit is fixed. Prior R4 results cannot be reused for R5.

## Unresolved scientific obligations

P2 R2 Eq.(28) printed-versus-integrated mismatch, Eq.(29) mg/g unit
bridge and Eq.(30) implicit respiration convention remain unadjudicated.
Figure 11 phenology, Eq.(33) night semantics, Table 1 g versus g/m²,
original plant/soil/food coupling, full dynamic feedback and decay,
external experimental evidence, original 1993 executable parity and
independent scientific review remain **NOT_ESTABLISHED/NOT_RUN**.
This R5 is a bounded numerical accounting test, not the solution to
those gaps. Do not activate the 1993 production solver, mark P2
complete, attach `science-validated`/`merge-verified`, or merge Draft
PR #159 on this evidence.
