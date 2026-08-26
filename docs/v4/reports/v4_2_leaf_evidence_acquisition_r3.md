# V4-2 Leaf Evidence Acquisition R3

## Status

`IN_PROGRESS_BROADENED_EMPIRICAL_SEARCH`

R2 ended with `HOLD_REQUIRED_FIELDS_MISSING`: neither Monnens 2023 nor Tomeo–Rosenthal 2018 provides a complete single-dataset matched dynamic stomatal-response packet. R3 therefore broadens discovery without lowering the V4-2 admission contract.

## Search objective

The preferred evidence source remains one soybean experiment with row-aligned:

- absolute observed `gsw` or equivalent leaf/surface resistance;
- VPD, or all humidity/temperature inputs required for an explicitly reviewed derivation;
- PAR/light;
- leaf temperature;
- dataset-bound growth/developmental stage or a source-declared single-stage experimental scope;
- crop/cultivar identity;
- timestamp/interval semantics;
- plant/replicate/independent-group identity;
- units and variable-level provenance.

No combination of unrelated datasets is accepted merely to fill missing fields.

## Candidate 1 — Zandalinas et al. 2020 soybean systemic stomatal response

Article DOI: `10.1104/pp.20.00511`.

The public article reports two LI-6800 systems attached simultaneously to upper and lower leaves of the same soybean plant, continuous monitoring of stomatal conductance, transpiration, photosynthesis and leaf temperature, and a chamber-light step from 40 to 1500 µmol m-2 s-1. Plants were four weeks old and selected leaves were described as young, fully expanded source leaves at the same relative position and developmental stage.

This makes the experiment structurally stronger than the R2 candidates for dynamic response work. However, public article-level evidence is not enough for packet admission. R3 must still establish whether raw LI-6800 records are obtainable and whether those records contain VPD or sufficient humidity variables, light, timestamps and independent-group identifiers. Until then this candidate is `PRIORITY_AUTHOR_OR_RAW_DATA_DISCOVERY`.

## Candidate 2 — Helicoverpa zea saliva / soybean stomatal Dryad dataset

Dataset DOI: `10.5061/dryad.q573n5tgj`.

The public Dryad record contains soybean stomatal-conductance analysis material and multiple CSV/R objects. It is worth a file-level triage, but no claim is made yet that it contains VPD, PAR, Tleaf or matched dynamic LI-COR records.

Disposition: `FILE_LEVEL_TRIAGE_REQUIRED`.

## Candidate 3 — soybean waterlogging physiology component evidence

Recent soybean waterlogging work reports stomatal conductance and leaf temperature at explicit vegetative/reproductive stages. The reported instrument is LI-600 rather than LI-6800, and public raw driver alignment has not yet been established.

Disposition: component evidence only unless source files prove the missing packet fields.

## Methods benchmark — Rizzo & Bailey 2026

Dataset DOI: `10.5061/dryad.5x69p8djr`.

The public Dryad dataset exposes LI-6800 records with variables including `gsw`, `VPDleaf`, `Tleaf`, light/PPFD and timestamps. This is highly useful for testing evidence-packet parsing, unit/provenance conventions and response-domain tooling. Its measured species are cowpea, redbud and walnut, not soybean.

Therefore it may validate tooling and methodology but must not be used as a soybean parameter source or as proof that the soybean V4-2 candidate is physically validated.

## Decision boundary

R3 does not authorize implementation. If no single public soybean source closes the packet, the next decision must explicitly choose among:

1. requesting author-held raw LI-COR files;
2. designing a prospective soybean experiment that satisfies the packet by construction;
3. proposing an evidence-composition model and subjecting that composition model to its own review.

The third option is not a default shortcut. Cross-dataset composition changes the inference model and therefore requires explicit review.

Current invariants:

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
