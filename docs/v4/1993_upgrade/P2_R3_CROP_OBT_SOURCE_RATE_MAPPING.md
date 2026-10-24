# P2 R3 — KfK5194 (1993) crop-specific HTO→OBT source-rate mapping

**Research diagnostic only; not a source-certified production OBT integrator.**

Primary authority: KfK 5194, §5.5.2, **printed pp.22–23 / PDF0 pp.31–32** (official PDF https://publikationen.bibliothek.kit.edu/270034158/3813483), and **printed Table 1 p.17 / PDF0 p.26**, Tables 9–12 **pp.86–89 / PDF0 pp.95–98**. Original PDF SHA256 verified on Ubuntu: `9a75292bc7289969db7175e17003c3dd777de72a30b52993264662dbc5c62ff5`. Printed p.22 was visually inspected, not inferred from garbled text extraction. Printed transfer-edge/source transcription is the pre-existing checked `primary_source_transfer_tables_r3.yaml` with SHA256 `10607b7f2911bc23f9fae138dd153bf46f20baa4b7b6669bbe5f7f4c49bfc220` (pinned by the new research adapter).

## Four Eq.(32)/(33) mean transfer rate edges

The p.22 uniform formation coefficient `T_m` explicitly references a *different* table edge for each crop. The historical source calls it a **daily** `1/d` rate and Eq.(32) uses the corresponding **hourly** `1/h` rate (`daily/24`). Source data in Tables 9–12 are COMA long-term ingestion calculated rates with standard model inputs; mapping alone **does not** demonstrate original hourly FORTRAN branch selection or the Eq.(28)→(33) numerical coupling.

| Crop / target OBT | Printed p.22 formation edge | Checked table, row | Daily 1/d | Hourly 1/h |
|---|---|---|---:|---:|
| Grass OBT | T5,6 | Table 10 `t5,6`: grass HTO→grass OBT | 0.0081 | 0.0003375 |
| Whole leafy-vegetable OBT | T14,15 | Table 9 `t14,15`: plant HTO→plant OBT | 0.0025 | 0.0001041666667 |
| Potato *tuber OBT* | T_p5,p8 | Table 11 `tp5,p8`: potato hto→tuber OBT | 0.0026 | 0.0001083333333 |
| Wheat *seedling OBT*, using historical p.22 label | T_w5,w8 | Table 12 *as transcribed* `tp5,p8`: wheat HTO→seedling OBT | 0.0041 | 0.0001708333333 |

**Important:** potato plant OBT (`tp5,p6`, 0.0053/d) and wheat plant OBT (`tp5,p6`, 0.012/d) **are not the same compartments** as tuber/seedling OBT. Likewise Table 12 reuses the printed potato-style `tp5,p8` while p.22 calls wheat `T_w5,w8`. Neither spelling is silently corrected; the model carries a `SOURCE_LIMITED` identifier discrepancy tag.

## Eq.(33) uniform dry-matter source calculations — area units NOT qualified

Printed p.22 specifies **12 daylight hours per growth day**, grass 30 days, leafy vegetable 45 days, tubers 90 days, wheat seedlings 60 days. With the separately printed Table 1 dry masses in **g**:

| Production basis as printed | Dry mass g | Growth days | Source-unit dry-matter rate g / daylight h |
|---|---:|---:|---:|
| Grass whole plant | 170 | 30 | 170 / 360 = 0.472222… |
| Leafy vegetable whole plant | 160 | 45 | 160 / 540 = 0.296296… |
| Potato tuber edible part | 660 | 90 | 660 / 1080 = 0.611111… |
| Wheat seedling edible part | 519 | 60 | 519 / 720 = 0.720833… |

These are conditional arithmetic values **per original source crop unit**, NOT a validated `g dry matter / m² ground / h` mass flux suitable for automatic insertion into the R1 Eq.(31)/(33) ground-area-normalized adapter. KfK5194 Table 1 header prints `g` without a verified ground-area basis. Although the input NAMELIST has separately documented g/m² masses, one cannot silently treat the Table 1 numeric cells as a spatial density. Independently the printed Table 1 values have potato tuber dry mass 660g **greater** than total potato plant dry mass 600g; wheat seedling dry mass 519g **greater** than total wheat plant dry mass 500g. These are source inconsistency flags, not grounds to invent reconciled inventories.

## Distinct OBT turnover and edible-compartment non-loss rule

KfK5194 printed p.23 explicitly disallows OBT loss from **edible potato tubers** and **edible wheat seedlings**. It does **not** disallow loss from the corresponding *parent plant OBT*.

- Table 10 **grass OBT** exits to grass HTO (0.024/d), cow HTO (0.018/d), cow OBT (0.0029/d), milk OBT (0.0015/d). Total 0.0464/d, isolated retention half-time `ln(2)/0.0464 ≈ 14.94 d`. Using only `grass OBT → grass HTO` would incorrectly produce a 28.88 d source-pool half-time.
- Table 9 **leafy plant OBT** → plant HTO 0.032/d; isolated half-time ≈ 21.66 d.
- Table 11 **potato parent-plant OBT** → potato HTO 0.069/d; Table 12 **wheat parent-plant OBT** → wheat HTO 0.069/d. These are **not** edible tuber/seedling OBT losses.
- The research adapter reports edible tuber/seedling OBT-loss coefficient **zero under the explicit printed p.23 historical model rule**, while keeping a separate parent OBT coefficient. It never reinterprets the parent's exponential loss as edible material loss.

The isolated parent-OBT `exp(-sum(k_out)*t)` survival diagnostic is only a one-compartment source arithmetic oracle. It is not a coupled animal/food/harvest model and does not subtract a complete mass/activity ledger.

## Implemented, guarded, and remaining

- Opt-in `src/cteas_ufotri/plant/kfk5194_1993_p2_crop_rate_source.py` selects exactly one p.22 formation edge and the distinct parent-OBT exit network from a **pinned original-source transcription**. The printed table labels, annual/daily/hourly provenance, and unresolved wheat p22/Table 12 mismatch are surfaced explicitly. There is no production default/CLI activation.
- `tests/unit/test_ufotri_1993_p2_r3_crop_rate_source.py` independently checks four source values, daily-to-hour conversion, 12-hour grow-day masses, four grass exit branches/half-time, edible-vs-parent loss isolation, source SHA tamper rejection, incompatible 1990 profile, invalid crop/type/time inputs and legacy-code non-import. It includes controlled standalone R1 Eq.(32) test calls only, with explicit provenance; it does not turn on a full solver.
- The R1 Eq.(33) interface expects *ground-area-normalized* `P_act/P_mean`; R3 has intentionally **not** connected unnormalised printed `g/h` source values to it.
- **Still blocked for a production 1993 OBT model:** P2 R2 Eq.(28) original-code discrepancy, Eq.(29) mg→g conversion, Eq.(30) coupled respiration order, source-limited Eq.(33) night branch, crop-area mass normalization, daily Figure 11 actual curve, crop edible HT/OBT two-way budgets, full soil/leaf/P3/P4/P5/P6 coupling, original FORTRAN numeric parity and independent science review.

**Decision:** P2 #128 OPEN; P0 #126 OPEN; PR #159 Draft/unmerged. Experimental source diagnostics cannot earn independent scientific admission merely through passing Docker unit/full tests.
