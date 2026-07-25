# Soybean external-data request package

Status: `READY_TO_SEND_MANUALLY`

This repository does not send the request.

## Project and research purpose

CTEAS_UFOTRI is a reproducible, HTO-only research model. The requested soybean
data will be used locally to evaluate time-resolved leaf/plant HTO uptake and
depuration, preregister a bounded calibration/holdout comparison, and assess
parameter identifiability. The project will not use the package for regulatory
claims or relabel a numerical reference as empirical validation.

## Requested delivery files

The data owner may retain original filenames; the following requested names
make the desired contents explicit:

1. `soybean_organizer_meteorology.xlsx`
2. `soybean_air_hto_time_series.xlsx`
3. `soybean_plant_hto_obt_observations.xlsx`
4. `soybean_chamber_boundary_conditions.xlsx`
5. `soybean_analytical_uncertainty_detection_limits.xlsx`
6. `soybean_data_dictionary.xlsx`
7. `soybean_licence_or_local_use_statement.txt`

## Required fields

- UTC or an unambiguous experiment-relative time with exposure start/stop;
- temperature in K or degC with conversion metadata;
- relative humidity in percent or fraction with basis;
- air HTO concentration with explicit air-volume unit;
- chamber volume, ventilation/mixing rate, inlet/outlet replacement boundary,
  and wind/mixing description;
- plant-water HTO and, if measured, OBT with explicit plant-water or combustion
  water basis;
- sample and replicate identifiers;
- measurement uncertainty and detection limit for every observable/method;
- exclusion/quality flags and missing-value codes.

Continuous air and meteorology data should retain their original time
resolution; 5-minute resolution is preferred when that is the acquisition
resolution. Plant observations should retain exact sampling timestamps rather
than being resampled.

## Use, custody, and provenance

Files will be stored only in a Git-ignored local directory. The project will:

- compute a local SHA-256 for every received file;
- record a metadata-only manifest, field mapping, unit conversion, and dataset
  version;
- keep calibration and holdout identifiers separate;
- commit the preregistration before inspecting holdout performance;
- not OCR or digitize publication figures to replace missing files;
- not combine unrelated experiments into one case;
- not redistribute raw files unless the licence explicitly permits it.

## Requested permission statement

Please state whether local research use is permitted, whether derived metrics
and metadata/checksums may be published, whether raw values/files may be
redistributed, the required citation, and any expiry, access, confidentiality,
or attribution conditions.

## Contact placeholders

```text
DATA_OWNER_OR_ORGANIZER =
CONTACT_NAME =
CONTACT_EMAIL =
INSTITUTION =
REQUESTER_NAME =
REQUESTER_INSTITUTION =
REQUEST_DATE =
RESPONSE_DATE =
PERMISSION_REFERENCE =
```
