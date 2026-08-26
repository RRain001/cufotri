# V4-2 Leaf Author-Data Acquisition R3B Review

## Decision

`CLOSED_AUTHOR_CONTACT_NOT_PURSUED`

R3A closed with `HOLD_REQUIRED_FIELDS_MISSING`. The public evidence shows a
stable asymmetry: some soybean datasets contain the absolute stomatal target but
not the row-aligned LI-COR drivers, while others contain strong row-aligned
VPD/PAR/Tleaf drivers but no stomatal target. R3B therefore did **not** lower
the empirical packet contract and did **not** authorize cross-dataset
composition.

R3B prepared a fail-closed author-held raw-data request path, but the project has
explicitly decided not to contact authors or pursue author-held raw data. No
message was sent, no response was received, and no author data were admitted.
The prepared request and integrity rules are retained only as provenance for the
closed path.

The next reviewed path is a **prospective soybean experiment design** that can
collect the complete dynamic stomatal-response packet in one experiment.

## Preserved author-data path rationale

The shortest external evidence path would have been an author-held raw instrument
export from an experiment already shown to contain the required stomatal target.
Two source-specific requests were prepared:

1. Mostofa et al. 2025 — original LI-6800/LI-680X export corresponding to public
   Fig. 3d, where R3A confirmed 150 absolute `gsw` records at exact 5-second
   cadence.
2. Zandalinas et al. 2020 — original paired LI-6800 exports for the simultaneous
   upper/lower soybean-leaf light-step experiment.

These requests were **not sent** and are no longer the active evidence path.

## Why the packet contract is unchanged

Closing the author-contact path does not justify relaxing any requirement. A
future complete packet must still bind, in one experiment or under an explicitly
reviewed alignment contract:

- absolute stomatal conductance or equivalent resistance;
- target unit and measurement basis;
- PAR/light;
- direct VPD or complete row-aligned humidity/pressure/Tleaf inputs;
- leaf temperature;
- crop and developmental-stage context;
- timestamp/interval semantics;
- biological replicate identity;
- variable-level provenance;
- matched record alignment.

Article-level ranges, chamber temperature used as Tleaf, midpoint humidity
substitution, or cross-dataset stitching remain prohibited.

## Preserved integrity boundary

If author data are ever reconsidered in a future project decision, the prepared
contract still requires exact received bytes, original filename/size, SHA-256,
transfer context, experiment identity, revision/version relation, raw files kept
outside Git, and any converted copy treated as a derived artifact. Nothing in
this closure admits or validates any external file.

## Next stage

Proceed to a separately reviewed prospective soybean experiment design. That
stage should specify the minimum instrument outputs, experimental factors,
replicate structure, timing, growth-stage ontology, response-domain coverage,
pre-registered metrics, holdout strategy, file/provenance schema and acceptance
criteria before any calibration or solver implementation.

Evidence-composition is not authorized as a substitute.

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
