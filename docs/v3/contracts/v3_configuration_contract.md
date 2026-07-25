# V3 configuration contract

Status: `ARCHITECTURE_ONLY`

The root fields are `schema_version`, `model_version`,
`compatibility_mode`, `enabled_modules`, `parameter_package`,
`forcing_manifest`, `source_scenario`, and `validation_claim`.

The schema is fail-closed: unknown root fields are errors, units and enums are
versioned, and a physical mode is never guessed. In `v2_frozen` mode:

- `enabled_modules` is empty;
- `v2_compatibility` is required;
- the candidate anchor is immutable;
- `original_config` is the verbatim parsed V2 mapping;
- the SHA-256 is computed from the exact input bytes;
- no V3 default is merged into the original mapping.

Migration warnings and field mappings are written to a separate report.
`scripts/migrate_v2_config_to_v3.py` never overwrites its input and refuses an
existing output unless `--force` is explicitly supplied. `--force` remains
for generated outputs only and cannot target the input path.

Future `compatibility_mode: v3` configurations require a separate gate. The
presence of that enum in the schema is an interface reservation, not an
executable physics mode.
