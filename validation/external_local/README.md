# Local external validation data

This directory is for legally usable local experiment or field data. All raw
and derived data files are ignored by Git. Do not weaken the local
`.gitignore`.

For the soybean adapter, create an untracked `soybean_emras/manifest.yaml`
listing:

- licence and local-use decision;
- redistribution decision;
- organizer meteorology workbook;
- complete air HTO workbook/time series;
- observation workbook/time series;
- chamber mixing or ventilation metadata;
- uncertainty and detection-limit metadata;
- SHA-256 for every file.

Tracked templates and adapters contain no restricted numeric data.
