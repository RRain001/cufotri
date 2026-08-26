# V4-2 Leaf Evidence File Audit R3A — Result

## Verdict

```ini
FINAL_VERDICT = HOLD_REQUIRED_FIELDS_MISSING
R3A_BASE = 3e7ec58b19752da9eef018a80875d0a90bd6164f
AUDITED_HANDOFF_HEAD = c154b93d1165f1df675526409dcd35fc01625f3f
AUDIT_DATE = 2026-08-26
CANDIDATES_AUDITED = 3 (strictly separately, zero stitching)
LEAF_IMPLEMENTATION_AUTHORIZED = FALSE
```

All three R3 priority candidates were downloaded as real bytes from Dryad and
audited at cell/column level (openpyxl + pandas + static reading of the R
script). No candidate closes all 12 blocking packet fields alone, so the round
ends in HOLD. The HOLD is precise about what each dataset contributes and what
is missing.

## Retrieval record

Dryad now gates file downloads behind a bearer-token API plus an Anubis
proof-of-work browser challenge. All files were retrieved through the public
`downloads/file_stream` endpoint after solving the PoW challenge; the 1.9 MB
Tejera CSV required one range-resume request and its final size matches the
Dryad-declared byte count exactly. No repository publishes checksums for these
datasets via the API (recorded as NOT_PUBLISHED); local MD5+SHA-256 are logged
in `docs/v4/leaf/v4_2_leaf_evidence_file_audit_r3a_result.yaml`.

## Candidate 1 — Mostofa 2025 (PRIORITY 1)

**What is real:** sheet `Fig 3d` contains a genuine absolute stomatal
conductance record — `gsw (mol m-2 s-1)`, 150 rows, complete, single series,
with `Time(min)` at an exact uniform **0.083333-minute (5-second)** step over
12.42 minutes (gsw 0.0308–0.1284). This satisfies the target and time fields
as DIRECT_COLUMN.

**Why it fails:**
- No VPD/humidity column anywhere; the article's 22–26 mmol/mol water-vapor
  span is not per-row data and midpoint substitution is forbidden → VPD MISSING.
- No Tleaf column; the 30 °C chamber temperature is neither recorded per row
  nor declared as actual leaf temperature in any audited file → MISSING.
- No PAR column or applicable declared constant in audited files → MISSING.
- Exactly one trace with no plant/leaf/replicate identifier → independent
  groups MISSING (n=1 cannot define groups).
- Stage R1 and cultivar Williams 82 are article context, not file-bound → AMBIGUOUS.
- Response domain: this is a wound-response time series, not a driver-response domain.

Article-level constants were **not** granted DECLARED_CONSTANT_WITH_PROVENANCE:
they appear nowhere in the audited files, so their applicability to these rows
cannot be proven under the constant-admission rule.

## Candidate 2 — Tejera-Nieves & Walker 2024

**What is real:** an exceptionally clean driver set with explicit units —
`Tleaf` (thermocouple °C, 26.33–30.22), `PAR` (μmol photon m⁻² s⁻¹, soybean
rows effectively constant 1499.7–1500.3), `VPDleaf` (kPa, 1.14–1.66), `Elapsed`
(s), `RunID` (= species+treatment+replicate; 23 soybean runs across four CO₂
protocols), zero missingness, soybean = 3282 of 19601 rows.

**Why it fails:** exhaustive spelling search confirms **no conductance or
resistance column exists** (`A`, `Ci`, `CO2_r` only). Published LI-6800
capability does not mean the published table preserved gsw. Without the target,
this is component evidence only — exactly as the R3A packet anticipated.

## Candidate 3 — Helicoverpa zea saliva / Lin 2021

**Findings:**
- `Fig1e.data.csv`: 30 plants × {GOX, Control, Buffer} × times {1,3,5,7,24,48}
  with Plant ID groups — but the `Mean` values (115.6–402.1) carry **no unit,
  quantity, or species declaration in any audited file**. The magnitude is
  compatible with either porometer conductance (mmol m⁻² s⁻¹) or microscope
  aperture (µm); the README-listed analysis script `Stomatal_conductance.R`
  **does not exist in the repository**, so the processing chain cannot be
  verified. Target classification: AMBIGUOUS.
- No PAR/VPD/Tleaf columns exist in EXPERIMENT_A.
- Optional EXPERIMENT_B files (`FigS3ab/cd`) do contain united conductance
  (mol m⁻² s⁻¹) but have a different trial structure, no time axis, and no
  alignment contract to Fig1e — the instrument-boundary rule forbids merging
  them into matched records.
- Provenance gap recorded: README lists 8 files (incl. `Stomatal_conductance.R`,
  VOC scripts/CSVs) that are absent from the actual Dryad deposit.

## Cross-dataset rule

Zero stitching attempts: Mostofa-gsw + Tejera-drivers, Helicoverpa-gs +
Mostofa-conditions, and every analogous combination remain forbidden and were
not evaluated as packets.

## Blockers summary

1. Mostofa: no row-level (or file-bound constant) VPD / Tleaf / PAR; single
   trace without group identity; stage not file-bound.
2. Tejera: no conductance/resistance column (drivers complete).
3. Helicoverpa: Fig1e quantity/units/species undeclared; analysis script
   missing; no drivers anywhere.

## Consequence

`HOLD_REQUIRED_FIELDS_MISSING`. The most valuable concrete lead remains
obtaining author raw LI-680X logs for the Mostofa wound-response experiment,
which would carry per-row gsw together with Tleaf/Vpd/PAR in one instrument
file. Even a future PASS would only authorize CONCRETE_EMPIRICAL_PACKET_
CONSTRUCTION plus independent item review — never immediate implementation.

## Frozen invariants (unchanged)

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

Third-party raw files live only under `/private/tmp/cteas_ufotri_leaf_evidence_r3a_data`
and are not committed to Git.
