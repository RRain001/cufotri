# P2 R6 — conditional triangular HTO→parent OBT→audit-sink ledger

**Scope:** stand-alone opt-in mathematical audit, not the UFOTRI 4.0
plant/COMA integrator. P2 Issue #128 and Draft PR #159 remain
scientifically blocked. No default 1990 solver change.

## Authority and explicitly bounded hypothesis

Primary source: W. Raskob, KfK 5194 (1993), printed §5.5.2 pp.22–23,
Eq.(32), and COMA Tables 9–12 pp.86–89, official KIT PDF:
https://publikationen.bibliothek.kit.edu/270034158/3813483.
The source-table transcription remains pinned by P2 R3 SHA256
`10607b7f2911bc23f9fae138dd153bf46f20baa4b7b6669bbe5f7f4c49bfc220`.
The Eq.(32) empirical `fact2` values are 1.75 (day), 0.25 (night),
with a source-described 12 h day / 12 h night reference and a
caller-supplied, **not reconstructed**, Figure 11 `fact1`.

R6 declares the *research-only* hypothesis
`ISOLATED_TRIANGULAR_NO_SINK_FEEDBACK`. It connects the already
source-pinned R4 conditional HTO→OBT coefficient and R5 competing
parent-OBT outflow rates **only where both refer to the same OBT
compartment**:

| Crop | HTO→parent OBT rate, d⁻¹ | Parent OBT→sinks total, d⁻¹ | R6 |
| --- | ---: | ---: | --- |
| Grass whole | 0.0081 | 0.0464 (four edges) | admitted |
| Leafy plant whole | 0.0025 | 0.032 (one edge) | admitted |
| Potato tuber | 0.0026 to **tuber OBT** | 0.069 from **parent potato OBT** | rejected |
| Wheat seedling | 0.0041 to **seedling OBT** | 0.069 from **parent wheat OBT** | rejected |

Potato/wheat **cannot** be placed into the same two-pool operator:
the printed edible OBT compartment has no OBT loss, while the parent
plant has a separate outflow network. The operator rejects them rather
than silently misassigning the parent hazard to edible OBT.

## Exact conditional operator and dimensional contract

All initial states and audit receiving buckets are Bq/m² ground.
For one piecewise-constant interval `dt` in hours, let `a` be the
R4 Eq.(32) coefficient in h⁻¹ and `b=sum(k_i)/24` the R5 parent
outflow hazard in h⁻¹, where source `k_i` are in d⁻¹.

```text
dH/dt = -a H
dB/dt = +a H - b B
dS_i/dt = (k_i/24) B

H' = H exp(-a dt)
B' = B exp(-b dt) + a H [exp(-a dt)-exp(-b dt)]/(b-a)
S_i' - S_i = (k_i/sum(k)) * [(H+B)-(H'+B')]
```

At `a=b`, the convolution contribution to `B'` is
`a H dt exp(-a dt)`. The implementation uses an `expm1` form
for the near-degenerate rates, avoiding subtractive cancellation.
Each interval and the complete day enforce nonnegative pools and
closed **activity** `H+B+sum(S_i)`, not biomass/dry-matter mass.
Splitting a fixed-rate day/night interval must leave the exact
result unchanged. Swapping day and night order changes B and sinks
even when total HTO survival is unchanged; this is an intended
coupling sensitivity, not proof of historic UFOTRI solve order.

Receiving bucket names (including `grass HTO`, `cow HTO` and
`milk OBT`) are documentary labels, **not physical receiving
states**. In particular, the grass HTO-labelled sink never feeds
the HTO→OBT source back. No original program timestep, compartment
basis or feedback mechanism is inferred from this calculation.

## Tests, provenance and acceptance

- `src/cteas_ufotri/plant/kfk5194_1993_p2_r6_triangular_budget.py`
  uses the R4 source-checked Eq.(32) rates and R3/R5 source-checked
  parent outflow edges. The module is not imported by the production
  solver or the frozen 1990 default.
- `tests/unit/test_ufotri_1993_p2_r6_triangular_budget.py`
  uses an independently written matrix-exponential analytic oracle
  for both admitted crops, 12h→0.5h timestep refinement, source sink
  partitioning, time-order sensitivity, zero HTO/OBT/phenology,
  non-12/12 rejection, edition/hash tampering and edible/parent
  mismatch rejection.
- This source change needs a fixed full Git SHA, Ubuntu Python 3.11
  Docker image and targeted/full regression evidence before
  `PASS_SCOPED` may be claimed. Tests against a previous image with
  a read-only new-file mount are *development* tests only.
- Independent scientific review, source Eq.(28)/(29)/(30) adjudication,
  Eq.(33) night physiology, Figure 11 phenology, crop mass-area
  conversion, feedback/respiration, plant/soil/animal/dose coupling,
  radioactive decay, original-executable parity and field evidence
  remain **NOT_ESTABLISHED/NOT_RUN**. Do not merge Draft PR #159 or
  add `science-validated` / `merge-verified` on R6 software tests.
