# External dataset search and licence review

## Decision

The Phase 1 search found scientifically relevant experimental and field
evidence, but no experimental or field package that meets the minimum
reproducibility contract of the validation runner. No external experiment or
field case was executed, no threshold was relaxed, and no calibration was
performed.

```text
EXPERIMENTAL_DATA_STATUS = BLOCKED_EXTERNAL_DATA
FIELD_DATA_STATUS = BLOCKED_EXTERNAL_DATA
```

The authoritative machine-readable inventory is
`external_dataset_inventory.csv`. Search results are evidence of a documented
acquisition attempt, not evidence that the candidate has been empirically
validated.

## Search scope and sources

The search covered controlled plant HTO uptake/depuration, matched atmospheric
and terrestrial time series, soil transfer experiments, animal feeding studies,
and public intercomparison cases. Sources checked included:

- IAEA EMRAS Theme 1 Working Group 2 reports and the dedicated soybean
  scenario PDF;
- bibliographic and abstract records for controlled rice and maize exposure
  studies;
- the Copernicus Climate Data Store for forcing only. ERA5 closes the forcing
  coverage gap but is reanalysis, not a site HTO observation.

The downloaded IAEA report used for this review was kept outside the repository:

```text
local_review_copy = /tmp/cteas_ufotri_pdf_evidence/iaea_emras_tritium_c14.pdf
sha256 = 8112c5fb6c239222479585335e111bd71b81f5963c038ba52636963522b1ce2f
repository_status = NOT_COMMITTED
```

## Highest-priority candidate: IAEA EMRAS soybean scenario

The report describes six one-hour glove-box exposures (SB1-SB6). SB1 and SB4
include repeated plant sampling after exposure. It provides observation tables,
the SB1 exposure air series, temperature, relative humidity, radiation context,
and an approximately 10% tritium measurement uncertainty. This is closely
aligned with the candidate's leaf HTO and OBT pathway.

It is not executable under the Phase 1 minimum-input contract:

- outdoor post-exposure meteorology is said to be available from the organizers
  in two Excel files, but those files were not present in the retrieved public
  report package;
- complete glove-box air workbooks are likewise referenced but not retrieved;
- chamber wind or mixing is not specified well enough to map to a conductance
  boundary condition;
- a detection limit is not reported;
- repackaging the publication tables or any organizer workbooks is not
  authorized by a clear dataset licence.

The blocked case manifest records these exact requirements. Values from plots
or unrelated experiments were not digitized or spliced into a pseudo-complete
case.

## Field and other candidates

The Pickering and pine-tree scenarios provide valuable model-comparison
context, but the retrieved publication does not supply a complete,
machine-readable, same-location air-meteorology-soil-plant series with
uncertainty and detection limits. Rice and maize papers were discoverable at
abstract/bibliographic level, but no legally reusable raw time series package
was obtained.

The field manifest therefore remains blocked. It does not combine different
sites, crop species, or sampling periods.

## Licence decision

IAEA web content may be cited with attribution under the IAEA terms of use, but
scientific publications and third-party material can carry additional rights.
The repository therefore stores only project-authored metadata, checksums,
requirements, and citations. It does not store the downloaded PDF or copied raw
tables. Publisher-controlled journal content is cited by DOI only.

## Unblocking actions

1. Obtain the original EMRAS soybean supporting workbooks and written reuse
   terms from the IAEA/organizers.
2. Obtain a chamber mixing characterization or a documented mapping from the
   experiment to the model's boundary-layer parameter.
3. Obtain detection-limit metadata and complete uncertainty definitions.
4. For a field case, obtain one co-located and time-matched package containing
   air HTO, meteorology, soil-water or soil HTO, and TFWT or OBT.
5. Freeze checksum, unit mapping, exclusion rules, calibration/holdout split,
   metrics, and thresholds before the first execution.

Until those conditions are met:

```text
CALIBRATION_STATUS = NOT_RUN_BLOCKED_EXTERNAL_DATA
PARAMETER_IDENTIFIABILITY_STATUS = NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE
```
