# V4 OBT matched-evidence acquisition request package R1

Status: `PREREGISTERED_NOT_SENT`

This repository does not send the requests in this stage. This file freezes the requested content and evidence-use boundary before any raw packet is inspected for model fit.

## Common statement for every request

CTEAS_UFOTRI is evaluating whether a future OBT precursor/exchangeable/non-exchangeable candidate can be supported by matched experimental evidence. The requested files will be used first for metadata/schema intake and scientific suitability review. Receipt does not imply validation, parameter activation, calibration, redistribution permission, or acceptance of the future candidate model.

Please preserve original filenames and original numeric values. A data dictionary, units, analytical protocol, uncertainty/detection-limit information, experiment/run and biological-replicate identifiers, and licence/local-use terms are required wherever available.

## Priority A — VATO / IRSN-EDF

Purpose: determine whether the first-phase VATO grass programme contains a sample-level component-resolved packet suitable for future OBT model discrimination.

Requested material:

1. Original sample-level grass TFWT observations.
2. Original sample-level exchangeable OBT and non-exchangeable OBT observations, if directly measured; if only total OBT or another operational definition was measured, provide that original field and its analytical definition instead of reconstructing components.
3. Analytical exchange/de-exchange, drying, combustion and counting protocols; recovery or correction information where used.
4. Sample/cut IDs, biological/field replicate IDs, timestamps, sampling support and tissue/product scope.
5. Fresh/dry/water/hydrogen or other declared mass basis and any measured conversion quantities actually used by the programme.
6. Atmospheric HTO forcing and the light/radiation, air or leaf temperature, humidity and other environmental records aligned with the samples, at their original resolution where available.
7. Analytical uncertainty and detection/quantification limits; missing/quality flags.
8. Data dictionary, original filenames, dataset version and correction history.
9. Licence/local research-use, derived-metric publication and redistribution terms.
10. Contact or provenance record identifying the responsible data owner/curator.

Explicit clarification question:

> Were exchangeable OBT and non-exchangeable OBT directly determined for compatible first-phase VATO grass samples, with sample-level values recoverable together with TFWT and forcing metadata? If not, what OBT quantity was directly measured?

No fixed E-OBT fraction will be requested or inferred as a substitute for component measurements.

## Priority B1 — controlled MicroTom experiment

Publication identifier: Portuphy, Katayama and Faanu, SSRN 5059446 / DOI `10.2139/ssrn.5059446`.

Requested material:

1. Sample-level TFWT, E-OBT and NE-OBT measurements from the controlled 14-day experiment.
2. Total OBT measurements if separately assayed, with explicit relation to E/NE aliquots.
3. Tomato cultivar/plant/tissue and developmental-stage identifiers.
4. Exposure/source boundary conditions and timing.
5. Light/PAR or photosynthetic-activity records/proxies and their units.
6. Air and/or leaf temperature, humidity and other controlled-environment records.
7. Sample timestamps, biological replicate/run identifiers and sampling support.
8. Analytical methods, uncertainty, detection/quantification limits and quality flags.
9. Mass/area/water basis and any measured conversion quantities.
10. Original machine-readable tables, data dictionary, version, licence/local-use terms and provenance.

## Priority B2 — Renard ryegrass experiment

Publication identifier: Renard et al. (2017), DOI `10.1016/j.jenvrad.2017.06.026`.

Requested material:

1. Sample-level TFWT and OBT observations, including the original exchangeable-fraction/component measurements.
2. Total/E/NE component fields if available; do not derive a missing component on the provider's behalf unless that derivation is part of the documented original analytical method.
3. Organ/tissue and plant-age identifiers, dehydrated biomass and any measured water/mass quantities used for basis conversion.
4. Hydroponic HTO exposure history, chamber/air boundary and environmental conditions.
5. Sample timestamps, biological replicate/run identifiers and sampling support.
6. Analytical method, uncertainty/detection limits and quality flags.
7. Original machine-readable tables, data dictionary, version, licence/local-use terms and provenance.

The constant-exposure experiment is not assumed to identify day/night, activity or temperature response terms merely because component OBT was measured.

## Supporting requests — soybean/nocturnal physiology

These are optional supporting requests only. They may inform forcing design, developmental-stage response, reduced-baseline checks or a future prospective experiment. They are not substitutes for a same-case TFWT + E-OBT + NE-OBT packet.

For IAEA/KAERI soybean, request original attachments/observation tables and exact analytical definitions, while recording that exchangeable OBT removed during NE-OBT preparation cannot be reconstructed from NE-OBT alone.

For nocturnal physiology studies, request original light/photosynthesis/stomatal/starch/growth observations only if useful for prospective forcing design. These values must remain separate from OBT component calibration cases unless they originate from the same biological experiment.

## Provider response fields

Every request record in the future execution stage must fill:

```text
TARGET_ID =
DATA_OWNER_OR_CURATOR =
CONTACT_NAME =
CONTACT_EMAIL_OR_FORM =
INSTITUTION =
REQUEST_DATE =
RESPONSE_DATE =
RESPONSE_DISPOSITION = NOT_SENT | NO_RESPONSE | DECLINED | PARTIAL | DATA_OFFERED
PERMISSION_REFERENCE =
LOCAL_RESEARCH_USE_ALLOWED =
DERIVED_RESULTS_PUBLICATION_ALLOWED =
RAW_REDISTRIBUTION_ALLOWED =
REQUIRED_CITATION =
EXPIRY_OR_ACCESS_CONDITIONS =
```

These fields remain blank/not-sent in the preregistration stage.

## Raw-file custody after receipt

If files are received in a later authorized execution stage:

- store original bytes under Git-ignored local external-data storage;
- compute SHA-256 for every original file;
- never overwrite an original version;
- create metadata-only tracked manifests and field maps;
- do not copy raw quantitative values into tracked fixtures;
- do not inspect quantitative holdout values for tuning;
- do not digitize publication figures to fill missing tables;
- request remediation when a required component, basis or provenance field is genuinely missing.

## Acceptance is not validation

A received packet can end in any of these acquisition dispositions:

```text
ACCEPT_METADATA_INTAKE
PARTIAL_REQUEST_REMEDIATION
EXPLORATORY_ONLY
INSUFFICIENT_FOR_INDEPENDENT_HOLDOUT
REJECT_NONAUDITABLE
```

None of these states authorizes OBT multi-pool implementation or calibration. A later dataset-shape amendment and identifiability review remain mandatory before any fit.
