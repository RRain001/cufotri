# D3 external-data request package

```text
REQUEST_STATUS = DRAFT_READY_NOT_SENT
TARGET_CANDIDATE = D3C-001
AUTOMATIC_CONTACT = NOT_AUTHORIZED
```

## Purpose and scientific boundary

This package requests the source data needed to assess whether the IAEA/KAERI
soybean experiment can support a future, independently approved external-data
intake. The current public report is Tier C mechanism-support evidence; it is
not executable for the frozen D3 design and is not trusted-registry evidence.

Receiving files would not authorize calibration, model execution, H2/H3
selection, preregistration, trusted-registry modification, formal external
validation, or V3 physics. Those actions remain behind the approval sequence
defined in the search protocol.

## Requested source files

Highest priority:

1. `sbTbox.xls` -- full glove-box air-moisture HTO time series;
2. `sbTHS.xls` -- temperature, relative humidity and solar/light series;
3. `sbWR.xls` -- wind/mixing and precipitation/rain series.

If retained, also request:

- sample-level plant-body TFWT for SB1 and SB4;
- organ-level TFWT for stem, leaves, shell and seeds;
- exact exposure start/end timestamps and time zone;
- post-exposure background air-moisture HTO observations;
- plant/sample/replicate identifiers and composite-sample membership;
- sampling timestamps and their reference origin;
- fresh mass, dry mass and extracted tissue-water mass/volume;
- analytical results before rounding or normalization;
- detection and quantification limits;
- analytical uncertainty and its components;
- instrument, preparation and counting methods;
- calibration and blank-control records;
- a data dictionary with units and coordinate/time conventions;
- missing-value encodings and quality flags;
- licence, attribution and redistribution conditions.

## Preferred delivery

Preferred formats are the original workbooks plus a lossless CSV export for
each sheet. Files should be accompanied by a readme/data dictionary. Native
timestamps, precision, units, blank cells and quality flags should be
preserved; no interpolation, reconstruction or hidden filtering is requested.

The sender should identify:

- whether each file is original, corrected or derived;
- the version/date and any corrections relative to the 2008 final report;
- whether numeric cells contain formulas or fixed values;
- whether TFWT is on a tissue-water basis and the exact unit conversion;
- whether composite values can be traced to contributing plants;
- whether the recipient may store checksums and metadata in a public Git
  repository;
- whether the raw files or derived tables may be redistributed.

## Acceptance boundary

On receipt, files will first be stored read-only outside Git. A SHA-256
manifest, licence review and data-quality review will be performed without
calibration or H2/H3 execution. A separate approval branch and independent
registry review are mandatory before the evidence can enter the trusted
registry.

## Manual action required

A human must select the recipient, confirm the wording and send the message.
No email or other contact was sent by this workflow.
