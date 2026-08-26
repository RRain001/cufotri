# V4-2 Leaf Evidence File Audit R3A — handoff

## Purpose

R2 proved that Monnens 2023 and Tomeo–Rosenthal 2018 do not provide a complete matched soybean dynamic stomatal-response packet. R3 broadened discovery and identified three public sources for direct byte-level audit. R3A is a read-only evidence audit. It is not solver implementation or calibration.

## Frozen base

```text
BASE_MAIN = 3e7ec58b19752da9eef018a80875d0a90bd6164f
BRANCH = codex/v4-2-leaf-evidence-file-audit-r3a
STATUS = PENDING_LOCAL_FILE_LEVEL_AUDIT
```

The governing machine-readable request is:

`docs/v4/leaf/v4_2_leaf_evidence_file_audit_r3a.yaml`.

## Audit order

### 1. Mostofa et al. 2025

Dryad DOI: `10.5061/dryad.51c59zwkh`.

Audit the actual bytes of:

- `Raw_data_Mostofa_et_al._2025.xlsx`
- `README.md`

This is the highest-priority candidate because the same experiment provides soybean Williams 82, reproductive stage R1, LI-6800 measurements, source-reported five-second stomatal-conductance logging, and explicit chamber conditions. The audit must determine whether those useful article-level facts are actually bindable to the workbook records.

Do not treat chamber temperature as leaf temperature without evidence. Do not turn the reported 22–26 mmol mol-1 water-vapor range into a fabricated row-level humidity value. If exact VPD cannot be observed or derived from complete aligned inputs, classify the VPD requirement accordingly.

### 2. Tejera-Nieves & Walker 2024

Dryad DOI: `10.5061/dryad.pk0p2ngst`.

Audit:

- `ACiMethod_4.0_RepositoryData.csv`
- `README.md`

The public README already reports soybean, RunID, Elapsed, Tleaf, PAR and VPDleaf. The key adversarial question is whether the actual file contains `gsw`, `rc`, or any legitimate absolute stomatal target omitted from the public summary. If it does not, this source is driver-rich component evidence, not a complete packet.

### 3. Lin et al. 2021 / Helicoverpa zea saliva

Dryad DOI: `10.5061/dryad.q573n5tgj`.

Audit first:

- `Fig1e.data.csv`
- `README.txt`
- `Stomatal_conductance.R`

The article identifies Fig. 1e as soybean stomatal conductance measured with an SC-1 porometer at multiple post-treatment times. Optional `FigS3ab.data.csv` and `FigS3cd.data.csv` may be inspected only to determine whether separate LI-6800 experiments contain relevant soybean-aligned drivers. Do not assume that the LI-6800 records and Fig. 1e porometer records are the same observations.

## Required field classification

Every candidate must receive a row for all 12 packet requirements using only:

```text
DIRECT_COLUMN
DECLARED_CONSTANT_WITH_PROVENANCE
EXPLICIT_DERIVATION_SUPPORTED
MISSING
AMBIGUOUS
```

A complete matrix must state source file/sheet/table, exact header or constant, unit, measurement basis, row/group alignment, missingness and provenance.

## Hash and provenance requirements

Keep downloaded data outside the repository. Record for each audited file:

- resolved URL;
- source DOI/version;
- download date;
- byte count;
- MD5 if source publishes one;
- SHA-256.

Do not commit third-party XLSX/CSV/R files.

## No evidence stitching

Mostofa target + Tejera drivers, or any analogous combination, does not form a packet. Separate experiments have no automatic row, plant, temporal or treatment alignment. Evidence composition is outside R3A.

## Allowed verdicts

Exactly one:

```text
PASS_ONE_COMPLETE_EMPIRICAL_PACKET_CANDIDATE
HOLD_COMPONENT_EVIDENCE_ONLY
HOLD_REQUIRED_FIELDS_MISSING
HOLD_ALIGNMENT_OR_PROVENANCE_AMBIGUOUS
```

PASS requires one individual candidate to close the complete packet. Even then:

```ini
LEAF_IMPLEMENTATION_AUTHORIZED = FALSE
```

The next gate would be concrete packet construction followed by independent leaf item review.

## Hard boundaries

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

## Result changes allowed

After the local audit, commit only audit governance artifacts:

- update the R3A request status/verdict;
- add `v4_2_leaf_evidence_file_audit_r3a_result.yaml`;
- add `v4_2_leaf_evidence_file_audit_r3a_result.md`;
- add result tests;
- update the handoff test and explicit CI list if needed.

No `src/` changes, no raw data and no model fitting.
