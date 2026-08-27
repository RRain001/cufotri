# V4 production-case input source resolution R1 report

## Verdict

```text
V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R1 = SOURCE_RESOLUTION_AUDIT_COMPLETE_AWAITING_EXACT_HEAD_GATE
MANIFEST_INPUTS = 49
REQUIRED_INPUTS = 48
OPTIONAL_INPUTS = 1
NEW_SOURCE_RESOLVED_RECORDS = 1
PRODUCTION_INPUT_PACKET_READY = FALSE
FULL_MODEL_PRODUCTION_READY = FALSE
ACTIVE_PARAMETERS = 0
REAL_CTEAS_ATMOS_BINDING = FALSE
```

This stage is source-evidence control plane only. No production solver file, numerical coupling, workflow, calibration state, or runtime parameter import is changed.

## Exhaustive R1 disposition

Every quantity in `docs/v4/contracts/v4_production_case_input_manifest_r1.yaml` is assigned exactly one source-resolution disposition:

| Disposition | Count |
|---|---:|
| `SOURCE_RESOLVED_NOT_ACTIVATED` | 1 |
| `ALREADY_CONTROLLED` | 1 |
| `BLOCKED_EXTERNAL` | 2 |
| `LIVE_CASE_BINDING_REQUIRED` | 5 |
| `DERIVED_DEPENDENCY_NOT_READY` | 3 |
| `CASE_SOURCE_REQUIRED` | 12 |
| `CONDITION_DEPENDENT_PHYSICAL_PROPERTY_SOURCE_REQUIRED` | 3 |
| `PROCESS_SOURCE_OR_EXPLICIT_ZERO_POLICY_REQUIRED` | 11 |
| `PROVISIONAL_EVIDENCE_REQUIRED` | 11 |
| **Total** | **49** |

The authoritative machine-readable partition is `docs/v4/governance/v4_production_case_input_source_resolution_r1.yaml`.

## Newly resolved source: H-3 nuclear half-life

`soil_three_layer.tritium_half_life` maps to the independently reviewed V3 evidence parameter `soil.tritium_half_life`.

The existing physical-constant validation registry records:

- stage status: `PASS_PHYSICAL_CONSTANT_VALIDATION`;
- selected evidence: `evidence.ddep.tritium_half_life.2006`;
- validated quantity: universal H-3 nuclear half-life;
- selected value: `388540800 s`;
- selected uncertainty: `777600 s`;
- review status: independent reviewed;
- active parameters after validation: `0`.

R1 therefore resolves the source identity and provenance only. The evidence remains isolated from runtime. `production_use_authorized=false` and `runtime_import_authorized=false` are frozen.

No environmental residence, soil-retention, biological-elimination, or OBT-turnover interpretation is permitted.

## Eq.39 physical properties remain unresolved for production

Three Eq.39 conversion inputs are deliberately not promoted from test values:

### `root_eq39.latent_heat`

FAO-56 states that latent heat varies with temperature. Its `2.45 MJ kg^-1` value is a simplification used for the FAO Penman-Monteith equation and corresponds to an air temperature of about 20 degC. R1 therefore does not freeze `2.45e6 J kg^-1` as a universal physical constant.

### `root_eq39.water_density`

IAPWS-95 provides water thermodynamic properties as functions of state. The convenient `1000 kg m^-3` value is not treated as an invariant universal property. R1 does not select a production value.

### `root_eq39.psychrometric_constant`

FAO-56 derives the psychrometric constant from atmospheric pressure, latent heat, specific heat, and molecular-weight ratio. A fixed `66 Pa K^-1` test value therefore cannot be promoted without an explicit model/source decision.

All three remain `CONDITION_DEPENDENT_PHYSICAL_PROPERTY_SOURCE_REQUIRED`.

## Real Atmos boundary remains blocked

The following remain blocked:

- `atmosphere.surface_deposition_flux`;
- `soil_three_layer.surface_deposition_flux`.

Frozen token:

```text
BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED
```

No accumulated deposition quantity, synthetic replay field, inferred precipitation product, or explicit zero can replace the required real surface flux without a later explicit evidence decision.

## Other unresolved source classes

R1 does not select case values for meteorological forcing, LAI, soil-water states, initial HTO/plant inventories, crop/growth identity, food/intake scenario fields, or dose coefficients.

Process slots such as inter-layer water/HTO fluxes, lower-boundary losses, surface water input/loss, re-emission, and TFWT loss/transformation remain fail-closed until either a real source or a separately evidenced explicit-zero policy exists.

Leaf resistance evidence remains provisional. R1 does not authorize Leaf R5.

## Frozen non-decisions

```text
PRODUCTION_INPUT_PACKET_READY=FALSE
FULL_MODEL_PRODUCTION_READY=FALSE
ACTIVE_PARAMETERS=0
CALIBRATION_STARTED=FALSE
OBT_MULTI_POOL_IMPLEMENTATION_AUTHORIZED=FALSE
OBT_PARAMETER_ACTIVATION_AUTHORIZED=FALSE
CURRENT_KF_KR_CALIBRATION_AUTHORIZED=FALSE
LEAF_R5_AUTHORIZED=FALSE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=FALSE
FULL_HYDROLOGY_AUTHORIZED=FALSE
REAL_CTEAS_ATMOS_BINDING=FALSE
EMPIRICAL_VALIDATION=FALSE
PHYSICAL_ACCURACY_CLAIM=FALSE
```

## Next stage

After exact-head dual-green CI and clean no-drift merge, proceed only to:

```text
V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R2
FOCUS=EQ39_PHYSICAL_PROPERTY_SOURCE_DECISION_ONLY
```

R2 may decide how latent heat, water density, and psychrometric constant obtain production provenance. It must not activate Eq.38, add full hydrology, implement Leaf R5, redesign OBT, calibrate parameters, or bind real CTEAS-Atmos data.
