# V4-2 Leaf Evidence Acquisition R3

## Status

`IN_PROGRESS_BROADENED_EMPIRICAL_SEARCH`

R2 ended with `HOLD_REQUIRED_FIELDS_MISSING`: neither Monnens 2023 nor Tomeo–Rosenthal 2018 provides a complete single-dataset matched dynamic stomatal-response packet. R3 broadens discovery without lowering the V4-2 admission contract.

## Search objective

The preferred evidence source remains one soybean experiment with row-aligned absolute `gsw`/`rc`, VPD or complete humidity derivation inputs, PAR/light, leaf temperature, developmental stage/context, crop identity, time semantics, independent-group identity, units, provenance and matched alignment. Unrelated datasets cannot be stitched together merely to fill missing fields.

## Priority 1 — Mostofa et al. 2025, cryptic isoprene emission of soybeans

Dataset DOI: `10.5061/dryad.51c59zwkh`.

The public Dryad record exposes `Raw_data_Mostofa_et_al._2025.xlsx`. The associated experiment used Williams 82 soybean at reproductive stage R1, LI-6800 gas exchange, and recorded stomatal conductance every 5 s. The article declares chamber PAR of 1000 µmol m-2 s-1, temperature of 30 °C, CO2 of 420 µmol mol-1 and water vapor of 22–26 mmol mol-1 for the gas-exchange/isoprene measurements.

This is currently the strongest public soybean candidate because target, developmental stage and forcing conditions originate in one experiment. It is not yet a packet: the workbook must prove the actual row structure, gsw columns, per-record Tleaf/VPD or sufficient humidity inputs, replicate/time alignment and the scope over which declared chamber constants apply.

Disposition: `PRIORITY_FILE_LEVEL_AUDIT_REQUIRED`.

## Priority 2 — Tejera-Nieves & Walker 2024 A/Ci soybean data

Dataset DOI: `10.5061/dryad.pk0p2ngst`.

The Dryad README explicitly includes soybean and row-level `RunID`, `Elapsed`, `Tleaf`, `PAR` and `VPDleaf` from LI-6800 measurements, with six biological replicates for non-tobacco species including soybean. This is unusually strong driver/context evidence.

However, the published dataset column list describes `A`, `Ci`, `Tleaf`, `CO2_r`, `PAR` and `VPDleaf` and does not list `gsw` or `rc`. The CSV therefore requires byte-level confirmation before being classified, but the current metadata suggest it is driver-rich component evidence rather than a complete stomatal-response packet.

Disposition: `DRIVER_RICH_COMPONENT_EVIDENCE_FILE_AUDIT_REQUIRED`.

## Priority 3 — Zandalinas et al. 2020 systemic stomatal response

Article DOI: `10.1104/pp.20.00511`.

The article reports two LI-6800 systems attached simultaneously to upper and lower soybean leaves, continuous monitoring of stomatal conductance, transpiration, photosynthesis and leaf temperature, and a 40→1500 µmol m-2 s-1 light step. Plants were four weeks old and the measured leaves were young fully expanded source leaves at the same developmental stage.

No public raw LI-6800 repository has yet been established, and the public supplement appears to contain methods/design rather than raw instrument logs. Raw-log or author-data discovery is required, especially to establish VPD/humidity and record/group identity.

Disposition: `PRIORITY_AUTHOR_OR_RAW_DATA_DISCOVERY`.

## Priority 4 — Helicoverpa zea saliva / soybean stomatal Dryad dataset

Dataset DOI: `10.5061/dryad.q573n5tgj`.

Dryad exposes multiple figure-level CSV files plus stomatal-conductance analysis scripts and states that the deposited material contains raw data associated with the paper. The dataset confirms soybean stomatal-conductance experiments, but public metadata do not prove matched VPD, PAR, Tleaf, stage or group fields.

Disposition: `FILE_LEVEL_TRIAGE_REQUIRED`.

## Component evidence — soybean waterlogging physiology

Recent soybean waterlogging work reports stomatal conductance and leaf temperature at explicit vegetative/reproductive stages. The reported instrument is LI-600 rather than LI-6800 and public raw driver alignment has not been established.

Disposition: component evidence only unless source files prove the missing packet fields.

## Methods benchmark — Rizzo & Bailey 2026

Dataset DOI: `10.5061/dryad.5x69p8djr`.

This public LI-6800 dataset contains variables including `gsw`, `VPDleaf`, `Tleaf`, PPFD/light and timestamps, making it a useful packet-parsing and response-domain benchmark. Its measured species are cowpea, redbud and walnut, not soybean, so it must not supply soybean parameters or soybean physical-validation claims.

## Decision boundary

R3 does not authorize implementation. File-level audit order is Mostofa 2025, Tejera-Nieves/Walker 2024, then the Helicoverpa soybean Dryad files, while Zandalinas raw-log discovery continues in parallel.

If no single public soybean source closes the packet, the next decision must explicitly choose among:

1. requesting author-held raw LI-COR files;
2. designing a prospective soybean experiment satisfying the packet by construction;
3. proposing an evidence-composition model and independently reviewing that changed inference model.

The third option is not a default shortcut.

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
