# D3 discriminating experiment commission package

```text
PACKAGE_STATUS = READY_FOR_LAB_FEASIBILITY_REVIEW
COMMISSIONING_STATUS =
HOLD_CLASSIFICATION_POWER_TARGET_NOT_MET
TIER_A_EXECUTABLE_PUBLIC_DATA_COUNT = 0
EXPERIMENTAL_DATA_ALREADY_COLLECTED = FALSE
FORMAL_EXTERNAL_VALIDATION_AUTHORIZED = FALSE
```

## Objective

Prepare a prospective soybean chamber experiment for laboratory feasibility
and radiation-safety review. The intended endpoint is discrimination between
the frozen H2 and H3 validation-only hypotheses without parameter fitting.
The synthetic dry run showed that the current 0.15 dex fail-closed threshold
with 3--6 replicates does not meet the preregistered positive-control
classification target. This document therefore specifies the operational and
data-quality package but does not claim that the current sample size is
statistically sufficient or authorize commissioning as a decisive experiment.

## Dry-run decision boundary

```text
H2_TRUTH_CLASSIFICATION = FAIL_DATA_INCONCLUSIVE
H3_TRUTH_CLASSIFICATION = FAIL_DATA_INCONCLUSIVE
OUT_OF_MODEL_CHALLENGE = PASS_DATA_INCONCLUSIVE
CV20_PASSING_REPLICATE_COUNTS_3_TO_6 = NONE
FORMAL_H2_H3_SELECTION = NOT_AUTHORIZED
```

The laboratory may review feasibility, safety, detection limits, schedule and
plant availability now. Before a real discriminating experiment is
commissioned, a new preregistered design or power analysis must resolve the
positive-control failure without tuning a rule after seeing real observations.

## Minimum formal experiment

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
| biological replication | 5 independent plants per destructive sampling time as the operational default |
| primary endpoint | total plant-body TFWT |
| endpoint unit | Bq/L tissue water |
| target total uncertainty | <=20% |
| air HTO logging | 5 min or finer |
| temperature/RH/mixing logging | 5 min or finer |

`EXTENDED_120_DAY_FOLLOWUP=OPTIONAL`. A 120-day extension may improve
long-timescale characterization, but it is not part of the minimum experiment
and must not be substituted for the required 120-hour follow-up.

The minimum formal sampling set is 0.2, 48 and 120 h with five biological
replicates at each time. This is 15 exposed plants. Add five pre-exposure
baseline plants, five zero-HTO controls and a 20% reserve:

```text
MINIMUM_PACKAGE_PLANTS = ceil((15 + 5 + 5) * 1.20) = 30
```

This count is a project planning assumption, not a formal power result.

## Recommended diagnostic experiment

The recommended destructive sampling times are 0.2, 1, 6, 24, 48, 72 and
120 h, with five exposed plants per time. With five pre-exposure baseline
plants, seven zero-HTO controls and a 20% reserve:

```text
EXTENDED_PACKAGE_PLANTS = ceil((35 + 5 + 7) * 1.20) = 57
```

The experimental laboratory must revise 30/57 plants for expected survival,
destructive-sampling losses, chamber capacity and its own quality-control plan.
The diagnostic 1/6/24/72 h samples must not be used to refit H2/H3 or replace
the preregistered primary classification times.

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

Use destructive, independent biological replicates. The current operational
default is five replicates at each of 0.2, 48 and 120 h after the 24 h
exposure. Additional diagnostic points are 1, 6, 24 and 72 h, provided the
minimum set and replication are not reduced.

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

Five biological replicates per destructive sampling time are the current
operational default, not five analytical repeats of one plant. In the dry-run
Monte Carlo at total CV 20%, 3--6 replicates yielded only 18.3%--30.7%
positive-control classification accuracy under the frozen 0.15 dex
inconclusive threshold. Five replicates are retained for sample-loss and
outlier resistance, but this is not a statistical power proof.

The laboratory should provide the uncertainty budget and confirm whether total
relative uncertainty at or below 20% is feasible. The planning detection limit
of 250 Bq/L and fresh/dry mass resolution of 0.01 g are project assumptions;
the laboratory must replace them with instrument-specific capabilities.
Values below detection limits must be retained with their flags and limits;
they must not be silently replaced by zero or LOD/2.

## Radiation-safety and feasibility hold points

The operability of 5270 Bq/mL water in chamber air moisture requires an
independent radiation-safety review covering source inventory, containment,
worker dose, exhaust treatment, waste and emergency response. Temperature
25 +/- 1 degrees C, RH 70 +/- 5%, mixing 0.5 +/- 0.1 m/s and a measured
post-exposure background are planning targets, not claims about an existing
facility. The laboratory must confirm achievable control bands and detection
limits before schedule or cost is accepted.

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
merged to `main`. The present synthetic dry run cannot enter that registry,
cannot clear the production gate and cannot be used to choose V3 physics.
