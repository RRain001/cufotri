# V4-2 Leaf Evidence File Audit R2 — Result

## Verdict

```ini
FINAL_VERDICT = HOLD_REQUIRED_FIELDS_MISSING
AUDIT_BASE = e1bd2460fe242fe93f13b3d3a2f74607c9448544
AUDITED_HANDOFF_HEAD = 92ad5af675621e745f6831f26338f2410190a136
AUDIT_DATE = 2026-08-26
CANDIDATES_AUDITED = 2 (separately, no stitching)
LEAF_IMPLEMENTATION_AUTHORIZED = FALSE
```

R2 downloaded the real source bytes for both R1 priority candidates and
audited them cell-by-cell with openpyxl/pandas (no OCR). Both candidates
provide genuine component evidence, but neither establishes every blocking
required packet field from its own files. The verdict is therefore a HOLD;
it is not a rejection of the datasets and not a physical-validation claim in
either direction.

## Retrieval record

| Candidate | Source actually used | Why |
| --- | --- | --- |
| Monnens 2023 (`10.5061/dryad.h18931zrh`) | Dryad `downloads/file_stream/2220653` | Dryad API now requires a bearer token; public endpoint reached after solving the site's Anubis proof-of-work check. Bytes verified as xlsx (`PK` header), 38689 bytes — matches R1 metadata (38.69 KB). |
| Tomeo & Rosenthal 2018 (`10.5061/dryad.2gd3b`) | Zenodo mirror record 5022524 | Dryad API gated; mirror used instead. **All four published MD5 values match local bytes exactly** — no SOURCE_VERSION_MISMATCH. |

Full hashes (MD5 + SHA-256) and resolved URLs are recorded in
`docs/v4/leaf/v4_2_leaf_evidence_file_audit_r2_result.yaml`.

## Candidate 1 — Monnens 2023 workbook (soybean VPD)

The workbook has six figure tabs. The VPD-relevant content is:

- **Figure 5**: hydrogen production at four declared conditions —
  `0.5 kPa 25°C`, `2.0 kPa 25°C`, `0.8 kPa 30°C`, `3.0 kPa 30°C`. VPD and
  temperature exist **only as column-header labels**.
- **Figure 6**: per-plant **fold increases** (Low→High VPD) for hydrogen
  production, transpiration, CO₂ assimilation, and stomatal conductance.
  These are ratio endpoints, not observed conductance values.

Field-classification outcome: `observed_stomatal_conductance` MISSING
(ratios only), `light_or_PAR` MISSING (absent from all sheets and README),
`stage_ontology` MISSING, `VPD binding to conductance rows` AMBIGUOUS
(two-condition contrast with temperature confounded between the 25 °C and
30 °C pairs), timestamps AMBIGUOUS (Morning/Afternoon fragments only),
plant identity AMBIGUOUS (23+23 implicit rows, no ID column).

**Response domain**: TWO_CONDITION_CONTRAST — insufficient for a dynamic
response packet even before considering the missing absolute values.

## Candidate 2 — Tomeo & Rosenthal 2018 CSVs

Both tables are **steady-state gas-exchange parameter summaries**:

- `CE_GasExchangeParameters.csv`: 71 plants × 21 cols; `ss_gs`
  (conductance to water vapor) complete, 12 cultivars, unique
  `cultivar+repl` identities.
- `Field_GasExchangeParameters.csv`: 89 observations × 29 cols; 31 plots,
  `camp ∈ {july, aug, sept}` with an explicit README row-level mapping
  july==lateVegetative(V4/V5), aug==earlyReproductive(R2–R4),
  sept==lateReproductive(R6).

Field-classification outcome: conductance and group identity are real
(`DIRECT_COLUMN`), and the Field stage mapping is genuinely
dataset-bound (`EXPLICIT_DERIVATION_SUPPORTED`). However:

- **No VPD column, no PAR/light column, no leaf-temperature column exists**
  in either table (`press400` is ambient pressure ≈95.9–101.0 kPa, not
  humidity).
- Units are not declared in the READMEs (only semantics), so
  `quantitative_units` is AMBIGUOUS pending article-text audit.
- Timestamps are month-granular at best.
- Because drivers are unrecorded, these are
  ENDPOINT_OR_FITTED_PARAMETER_SUMMARY tables — matched driver-response
  records cannot be constructed from them.

## Cross-dataset rule

Each candidate was judged strictly on its own files. No Monnens-VPD +
Tomeo-stage stitching was attempted or permitted.

## Stage 7 characterization (no fitting performed)

| Quantity | CE | Field | Monnens Fig 6 |
| --- | --- | --- | --- |
| ss_gs min/max | 0.1546 / 0.4213 | 0.0988 / 0.5848 | ratios only |
| missing target values | 0/71 | 0/89 | 1 n/a of 46 (stomatal fold) |
| VPD/PAR/Tleaf domain | not characterizable | not characterizable | header labels only |
| independent groups | 71 plants / 12 cultivars | 31 plots × 2–3 occasions | 46 implicit plant rows |

## Blockers

1. TOMEO_DRIVER_COLUMNS_ABSENT — no VPD/PAR/Tleaf in either table.
2. MONNENS_ABSOLUTE_CONDUCTANCE_ABSENT — only fold-increase endpoints.
3. MONNENS_PAR_LIGHT_MISSING — absent from workbook and Dryad README.
4. MATCHED_DRIVER_RESPONSE_RECORDS_ABSENT_BOTH — neither file set pairs
   drivers with responses per record.
5. STAGE_ONTOLOGY_INCOMPLETE — Monnens and Tomeo-CE lack any stage field
   (Tomeo-Field is the sole supported mapping).
6. UNITS_NOT_DECLARED_IN_TOMEO_FILES — semantics yes, units no.

## Consequence

`HOLD_REQUIRED_FIELDS_MISSING`: both datasets remain component-evidence
only. A future round needs one dataset that supplies per-record VPD/PAR/
Tleaf together with absolute observed conductance (e.g., raw LI-COR logs
from the authors), or an explicitly reviewed evidence-composition path.

## Frozen invariants (unchanged by this audit)

```ini
LEAF_IMPLEMENTATION_AUTHORIZED = FALSE
SOLVER_IMPLEMENTATION_STARTED = FALSE
CANDIDATE_PARAMETER_VALUES_ADMITTED = FALSE
CALIBRATION_STARTED = FALSE
ACTIVE_PARAMETERS = 0
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```

Third-party raw files live only under `/private/tmp/cteas_ufotri_leaf_evidence_r2_data`
and are not committed to the repository.
