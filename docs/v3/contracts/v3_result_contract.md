# V3 result contract

Status: `ARCHITECTURE_ONLY`

Every result envelope records:

```text
model_version
schema_version
module_versions
state_definitions
ledger
validation_status
candidate_anchor
git_commit
config_hash
input_checksums
```

State definitions make units and normalizations discoverable without reading
the calculation code. The standard ledger exposes external, internal,
boundary, decay, inventory, and residual terms separately. Input checksums use
stable manifest names as keys.

A V2 result wrapped for V3 retains its original fields separately; the
envelope cannot relabel a V2 run as V3 physics. Validation status is an
evidence claim, not an inference from test success. The machine contract is
`schemas/v3/result.schema.json`.
