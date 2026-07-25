# Local external validation data

This directory is for legally usable local experiment or field data. All raw
and derived data files are ignored by Git. Do not weaken the local
`.gitignore`.

For the soybean adapter, create an untracked
`soybean_emras/source_manifest.yaml` listing:

- licence and local-use decision;
- redistribution decision;
- exposure start/stop and expected time step;
- file roles for meteorology, complete air HTO, observations, mixing boundary,
  uncertainty, and detection limits;
- explicit units for every required field;
- disjoint calibration and holdout sample identifiers;
- confirmation that holdout was not inspected before preregistration;
- SHA-256 for every file.

The adapter computes checksums and creates a metadata-only intake manifest and
report. It rejects missing fields, unknown units, discontinuous forcing/air
series, missing mixing boundaries, absent detection limits, overlapping
calibration/holdout IDs, and premature holdout inspection.

The adapter never OCRs or digitizes publication figures and never splices
different experiments into a synthetic complete case. Tracked templates and
adapters contain no restricted numeric data.
