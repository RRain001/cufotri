# V4-2 Leaf Evidence File Audit R2 — Handoff

## Purpose

R2 is a read-only audit of actual public source files. It exists because R1
could identify strong public candidates but could not establish packet admission
from metadata alone.

Entry main:

`e1bd2460fe242fe93f13b3d3a2f74607c9448544`

Audit branch:

`codex/v4-2-leaf-evidence-file-audit-r2`

Machine-readable audit packet:

`docs/v4/leaf/v4_2_leaf_evidence_file_audit_r2.yaml`

## Why local file inspection is required

The repository gate requires exact evidence about columns, units, source-file
hashes, missingness, row/group alignment, growth-stage semantics and response-
domain support. Article abstracts, repository landing pages and indexed file
names cannot establish those properties.

The current ChatGPT web environment can read the Dryad/Zenodo landing metadata
but could not reliably retrieve the raw XLSX/CSV bytes. R2 must therefore run in
an environment with ordinary HTTPS file download and local tabular-file access.

This is not permission to modify solver code.

## Required downloads

### Candidate 1 — Monnens 2023

Dryad DOI: `10.5061/dryad.h18931zrh`

Required file:

`Monnens_et_al_All_data_Dryad.xlsx`

Do not infer workbook contents from the article. Record the downloaded file's
SHA-256, all sheet names, dimensions, headers and source/repository provenance.

### Candidate 2 — Tomeo & Rosenthal 2018

Dryad DOI: `10.5061/dryad.2gd3b`

Zenodo mirror record: `5022524`

Required files and published MD5 values:

```text
CE_GasExchangeParameters.csv
30b955a1b12b22bf4e80353f8aaa7315

Field_GasExchangeParameters.csv
e9f7043885e7097448d37efaf92f9733

README_for_CE_GasExchangeParameters.txt
68cbfb56e9f656e5573713f9a1fdd761

README_for_Field_GasExchangeParameters.txt
07ce6434d693d28fc756ec6649e3ed01
```

R2 must verify those MD5 values and also record SHA-256 locally.

## Audit methodology

For each source file:

1. preserve original bytes outside the Git repository;
2. compute cryptographic hashes;
3. record sheet/table dimensions and exact column headers;
4. use README/repository/article only to establish semantics and units that are
   actually traceable to the audited file;
5. classify every V4-2 required packet field as:
   `DIRECT_COLUMN`, `DECLARED_CONSTANT_WITH_PROVENANCE`,
   `EXPLICIT_DERIVATION_SUPPORTED`, `MISSING`, or `AMBIGUOUS`;
6. quantify missingness for required direct columns;
7. prove row alignment for target and forcings;
8. identify legitimate independent groups without using final holdout to define
   response domains;
9. instantiate a dataset-bound stage ontology only when the source provides a
   defensible row/group mapping;
10. report observed VPD/light/Tleaf support but do not fit a stomatal model.

## Important fail-closed rules

- Days after emergence are not automatically equivalent to soybean V/R stage.
- Article-level V4/V5, R2-R4 or R6 descriptions do not prove a row-level stage
  mapping unless the audited table can be linked to those groups.
- Chamber setpoints may be `DECLARED_CONSTANT_WITH_PROVENANCE` only if the
  source explicitly states they apply to the audited observations.
- RH-to-VPD conversion is not allowed unless all required inputs, units and the
  reviewed conversion relation are present.
- Two soybean datasets cannot be stitched into one packet merely to fill each
  other's missing fields.
- A dataset can be useful component evidence and still fail full-packet admission.

## Allowed result

R2 may conclude one of:

```text
PASS_ONE_COMPLETE_EMPIRICAL_PACKET_CANDIDATE
HOLD_COMPONENT_EVIDENCE_ONLY
HOLD_REQUIRED_FIELDS_MISSING
HOLD_ALIGNMENT_OR_PROVENANCE_AMBIGUOUS
```

Even the PASS result does **not** authorize production implementation. It only
allows construction of a concrete packet followed by independent item review.

## Repository outputs

Commit only audit metadata, matrices, tests and reports. Do not commit third-
party raw files unless a later explicit repository-data policy says otherwise.

Required outputs:

```text
docs/v4/leaf/v4_2_leaf_evidence_file_audit_r2_result.yaml
docs/v4/reports/v4_2_leaf_evidence_file_audit_r2_result.md
tests/v4/test_v4_2_leaf_evidence_file_audit_r2.py
```

Do not modify:

```text
src/
configs/
production solver code
active parameter values
```

## Frozen invariants

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
