# D3 discriminating experiment commission package

```text
PACKAGE_STATUS = READY
TIER_A_EXECUTABLE_PUBLIC_DATA_COUNT = 0
EXPERIMENTAL_DATA_ALREADY_COLLECTED = FALSE
FORMAL_EXTERNAL_VALIDATION_AUTHORIZED = FALSE
```

## Objective

Commission a prospective soybean chamber experiment that can distinguish the
frozen H2 and H3 validation-only hypotheses without changing either model or
using the observations for fitting. This document specifies acquisition and
quality requirements only; it does not preregister or run formal validation.

## Minimum design

| Item | Required value |
|---|---|
| crop | soybean |
| exposure medium | air-moisture HTO |
| exposure concentration | 5270 Bq/mL water |
| exposure duration | 24 h |
| post-exposure follow-up | 120 h |
| total elapsed schedule | 144 h (approximately 6 days) |
| chamber temperature | 25 degrees C |
| relative humidity | 70% |
| wind/mixing | 0.5 m/s |
| precipitation | zero |
| post-exposure HTO background | measured, not assumed zero |
| minimum post-exposure samples | 0.2, 48 and 120 h |
| biological replication | at least 3 independent plants per destructive sampling time |
| primary endpoint | total plant-body TFWT |
| endpoint unit | Bq/L tissue water |
| target total uncertainty | <=20% |
| air HTO logging | 5 min or finer |
| temperature/RH/mixing logging | 5 min or finer |

`EXTENDED_120_DAY_FOLLOWUP=OPTIONAL`. A 120-day extension may improve
long-timescale characterization, but it is not part of the minimum experiment
and must not be substituted for the required 120-hour follow-up.

## Blinding and independence

Before any discriminating observations are opened:

1. freeze the real external-validation protocol;
2. bind the exact raw-file checksums and approved trusted-registry entry;
3. generate and checksum H2 and H3 predictions without refitting;
4. have an independent reviewer verify the prediction package;
5. then open only the prespecified discriminating observations.

Personnel who collect and quality-control samples may retain the natural
sample identities, but the modelling team must not receive the 0.2/48/120 h
TFWT values before the prediction freeze. Observation labels may be held by an
independent custodian.

## Chamber forcing requirements

Record at 5-minute resolution or finer from at least 30 minutes before
exposure through 120 h after exposure:

- timestamp with time zone and monotonic elapsed time;
- chamber and post-exposure air-moisture HTO;
- temperature, relative humidity and wind/mixing speed;
- light intensity or photosynthetically active radiation;
- precipitation (expected zero) and any chamber opening/event flag;
- instrument ID, calibration state, detection limit and quality flag.

Measure the post-exposure HTO background continuously or at sufficient
frequency to demonstrate the actual decay/background profile. Do not replace
it with zero.

## Sampling requirements

Use destructive, independent biological replicates. At minimum collect three
replicates at each of 0.2, 48 and 120 h after the 24 h exposure. A separate
exposure-end reference sample and additional points (for example 1, 6, 24 and
72 h) are recommended, provided the minimum set and replication are not
reduced.

For every sample record:

- unique sample, plant and replicate IDs;
- exact timestamp and calculated post-exposure time;
- plant-body definition and any separately retained organs;
- fresh mass, dry mass and extracted tissue-water volume/mass;
- TFWT result in Bq/L tissue water before rounding;
- detection/quantification limit, uncertainty and quality flag;
- preparation, extraction and counting method;
- blanks, duplicates, spikes or other laboratory controls.

The primary endpoint is measured total plant-body TFWT. If destructive
analysis requires separate leaves and stems, preserve their individual
measurements and masses so a mass-weighted total can be reconstructed without
an undocumented assumption.

## Replication and uncertainty

The minimum is three biological replicates per destructive sampling time, not
three analytical repeats of one plant. The laboratory should provide the
uncertainty budget and target total relative uncertainty at or below 20% for
the primary endpoint. Values below detection limits must be retained with
their flags and limits; they must not be silently replaced by zero.

## Required deliverables

- completed chamber-forcing CSV;
- completed TFWT sample CSV;
- completed biomass CSV;
- original instrument exports and laboratory worksheets;
- raw-file manifest with source, size, MIME type and SHA-256;
- completed quality-control checklist;
- data dictionary and protocol deviations;
- licence, attribution and redistribution statement.

The templates under
`validation/external_evidence_acquisition/d3/templates/` are the delivery
contract. Original raw files remain read-only and outside Git.

## Fail-closed acceptance

Missing air HTO, unmeasured post-exposure background, absent target samples,
unknown tissue-water basis, missing biological replicate identity, or absent
licence prevents trusted-registry approval. Synthetic or reconstructed data
cannot be relabelled as experimental observations.

Data arrival leads only to checksum, licence and data-quality review. Formal
H2/H3 execution remains prohibited until independent registry approval has
merged to `main`.
