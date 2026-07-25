# Long observed-forcing workflow architecture

Status: `ARCHITECTURE_ONLY`

## Manifest contract

Every forcing package declares dataset/product, licence, spatial coordinates
and coordinate reference, UTC coverage, interval, variables, units,
accumulation semantics, local path, SHA-256, and per-row provenance status.
Allowed status values are:

- `observed`: direct point/station observation;
- `reanalysis`: externally retrieved data-assimilating product such as ERA5;
- `interpolated`: bounded interpolation between external values;
- `extended`: deterministic or climatological extension.

ERA5 is always `reanalysis`, never point-station `observed`.

Accumulated precipitation and energy variables name the interval ending at
`valid_time`. ERA5 total precipitation remains metres before an explicit
derived `mm h-1`; accumulated energy remains `J m-2` before an explicit
derived `W m-2`. The original and derived fields cannot share a unit label.

## Gap policy

Gaps fail closed unless the manifest preregisters a maximum gap, interpolation
method, boundary policy, and provenance status. Extension cannot be relabelled
as external forcing. Coordinates, time zones, units, or accumulation windows
cannot be inferred from filenames.

## Case ladder

| Case | Purpose | Minimum evidence |
|---|---|---|
| 72 h | compatibility anchor | 72 consecutive hours, no silent gaps |
| 14 d | synoptic transition | checksum-complete external package |
| 30 d | repeated wet/dry cycles | explicit gap and accumulation audit |
| seasonal | phenology-scale forcing | observed/reanalysis fractions reported |

The frozen V2 48 h plus deterministic extension and the completed 72 h ERA5
reanalysis comparison remain unchanged. Future cases are opt-in manifests and
cannot overwrite either input.

`schemas/v3/forcing_manifest.schema.json` defines the tracked metadata. Raw and
derived forcing stay under Git-ignored data paths.
