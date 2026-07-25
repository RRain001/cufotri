# Local external validation data

This directory is for legally usable local experiment or field data. All raw
and derived data files are ignored by Git. Do not weaken the local
`.gitignore`.

For the soybean adapter, create an untracked
`soybean_emras/source_manifest.yaml`, validated against
`schemas/v3/external_raw_data_manifest.schema.json`, listing:

- dataset identifier/version, eligible or explicitly test-only evidence type,
  authoritative source, licence, and local-use decision;
- redistribution decision;
- exposure start/stop and expected time step;
- file entries for meteorology, complete air HTO, observations, mixing
  boundary, uncertainty, and detection limits, each with role, path, format,
  size, expected SHA-256, and locally calculated SHA-256;
- explicit units for every required field;
- disjoint calibration and holdout sample identifiers;
- confirmation that holdout was not inspected before preregistration;
- `SOURCE_CHECKSUM_UNAVAILABLE` only when the source supplied no checksum; the
  locally calculated SHA-256 remains mandatory.

The adapter recomputes every checksum, compares it with the manifest, parses
all required numeric columns, and creates a metadata-only intake manifest and
report. The generated intake is validated at runtime against
`schemas/v3/external_intake_manifest.schema.json`. It rejects missing fields,
empty/non-finite/negative values where prohibited, unknown or mismatched
units, discontinuous forcing/air series, incomplete exposure coverage,
nonpositive chamber/mixing values, absent or invalid detection limits,
overlapping calibration/holdout IDs, and premature holdout inspection.

The adapter never OCRs or digitizes publication figures and never splices
different experiments into a synthetic complete case. Tracked templates and
adapters contain no restricted numeric data.
