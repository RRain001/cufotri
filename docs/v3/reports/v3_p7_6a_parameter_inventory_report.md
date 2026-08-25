# V3-P7.6A parameter inventory report

Status: `PASS_PARAMETER_EVIDENCE_PROVENANCE_FROZEN`

Branch baseline: `codex/v3-p7-5b-numerical-coupling-freeze`

The inventory is canonicalized in
`docs/v3/parameter_evidence/parameter_inventory.yaml`. It covers explicit
V3 P6/P7 model inputs, state-initialization inputs, atmospheric forcing,
pipeline controls, and synthetic values used by the P7.5/P7.5B tests. It does
not import or resolve any runtime parameter.

Scanned interface areas:

- `plant/leaf_exchange_resistance`
- `plant/tfwt_v3`
- `plant/obt_v3`
- `plant/soil_v3`
- `plant/root_v3`
- `plant/food_v3`
- `exposure/intake_v3`
- `exposure/dose_v3`
- `coupling/atmos_v3`
- `v3_pipeline`
- P7.5/P7.5B tests

## Inventory totals

| Primary class | Count |
|---|---:|
| `PHYSICAL_CONSTANT` | 1 |
| `EMPIRICAL_MODEL_PARAMETER` | 8 |
| `BIOLOGICAL_PARAMETER` | 4 |
| `CROP_PARAMETER` | 7 |
| `SOIL_PARAMETER` | 3 |
| `EXPOSURE_PARAMETER` | 2 |
| `DOSE_PARAMETER` | 1 |
| `SCENARIO_INPUT` | 28 |
| `NUMERICAL_CONTROL` | 2 |
| `TEST_ONLY_PARAMETER` | 20 |
| **Total** | **76** |

The registry sorts records by `parameter_id` and rejects duplicates. Derived
quantities such as total resistance, exchange velocity, concentrations,
storage balances, and dose results are not parameters and are therefore not
duplicated in the manifest.

No physical constant or provisional coefficient received a guessed value.
The physical half-life, resistance components, OBT rates, root coefficient,
harvest fractions, exposure inputs, and dose coefficient remain explicit
evidence gaps or caller-supplied inputs.
