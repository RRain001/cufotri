# V4-2 Leaf Author-Data Acquisition R3B Review

## Decision

`READY_FOR_AUTHOR_CONTACT_NOT_SENT`

R3A closed with `HOLD_REQUIRED_FIELDS_MISSING`. The public evidence now shows a
stable asymmetry: some soybean datasets contain the absolute stomatal target but
not the row-aligned LI-COR drivers, while others contain strong row-aligned
VPD/PAR/Tleaf drivers but no stomatal target. R3B therefore does **not** lower
the empirical packet contract and does **not** authorize cross-dataset
composition.

The shortest evidence path is an author-held raw instrument export from an
experiment already shown to contain the required stomatal target.

## Priority 1 — Mostofa et al. 2025

R3A confirmed that the public workbook contains one absolute soybean `gsw`
time series (150 records at exact 5-second cadence) for Fig. 3d. The public file
does not contain VPD, Tleaf, PAR, humidity inputs, biological-replicate identity,
or a file-bound stage mapping.

R3B therefore requests the **original LI-6800/LI-680X export for the same Fig. 3d
measurement domain**, not a reconstructed spreadsheet. A useful raw export would
ideally retain `gsw`, VPDleaf/VpdL, Tleaf, PAR/Q, H2O fields, pressure, elapsed
time/timestamp, plant/leaf/run identity, treatment markers and stage context.

Article-level protocol values are not promoted to empirical rows merely because
they are scientifically plausible. If the author supplies only the same
published `gsw` values with no missing drivers or alignment metadata, the packet
remains HOLD.

## Priority 2 — Zandalinas et al. 2020

The paper describes simultaneous soybean gas-exchange measurements with two
LI-6800 systems and a light-step response experiment. The public discovery path
has not established the corresponding raw exports. R3B therefore defines a
second request for the original paired instrument files plus any existing
run-pairing/synchronization metadata.

This candidate remains secondary because the Mostofa public workbook already
proves the exact target series to be recovered from a raw instrument domain.

## File admission boundary

A received attachment is not evidence merely because it came from an author.
Before content analysis, R3B requires:

1. exact received bytes preserved;
2. original filename and byte size recorded;
3. SHA-256 calculated before editing or conversion;
4. sender/transfer context recorded;
5. article and experiment identity established;
6. revision/version relation recorded when more than one export exists;
7. raw files kept outside Git;
8. any decompressed, converted or cleaned copy treated as a separate derived artifact.

A file with ambiguous experiment identity, silent revision replacement, or
integrity mismatch fails closed.

## Data-semantic admission boundary

For a future complete packet candidate, target and drivers must coexist in the
same row domain or have an explicit source-supported alignment key. The following
are insufficient:

- same crop;
- same laboratory;
- same paper;
- similar timestamps from separate experiments;
- author-reported ranges substituted for row-level values;
- Tejera drivers joined to Mostofa `gsw`;
- manually reconstructed metadata.

If direct VPD is absent, derivation remains possible only from complete
row-aligned humidity, pressure and Tleaf inputs under an explicitly documented
equation. Midpoint substitution is forbidden.

## Communication boundary

This R3B branch prepares a request template only. No author has been contacted by
this stage, no message has been sent, and no response or data receipt may be
claimed. Contact identity must be verified separately from the relevant article
or institutional source before any external communication.

## Exit states

- No response / data unavailable: remain HOLD.
- Partial data: hash, audit and record incomplete evidence; remain HOLD if any
  blocking field is absent or ambiguous.
- Complete-looking raw export: mark `DATA_RECEIVED_COMPLETE_CANDIDATE`, then open
  a **separate file-level audit stage**. Do not authorize implementation directly.
- Author-data path exhausted: consider a separately reviewed prospective soybean
  experiment design or evidence-composition design. Neither is authorized here.

## Frozen implementation boundary

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
