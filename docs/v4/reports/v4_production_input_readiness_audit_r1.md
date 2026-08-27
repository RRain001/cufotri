# V4 production input readiness audit R1

Status: `AUDIT_COMPLETE_AWAITING_EXACT_HEAD_GATE`

Base main: `7800176751050c678ccfe24b04c5c263ec6c27bb`

## Verdict

```ini
V4_PRODUCTION_INPUT_READINESS_AUDIT_R1 = AUDIT_COMPLETE_AWAITING_EXACT_HEAD_GATE
SOFTWARE_CHAIN_CONNECTED_WITH_CONTROLLED_UFOTRI_PROFILES = TRUE
PRODUCTION_INPUT_PACKET_READY = FALSE
FULL_MODEL_PRODUCTION_READY = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
LEAF_R5 = FALSE
FULL_HYDROLOGY = FALSE
MULTI_POOL_OBT = FALSE
CALIBRATION_STARTED = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
NEXT_STAGE = V4_PRODUCTION_CASE_INPUT_MANIFEST_R1
```

This is an input-readiness result, not a physics-readiness or validation result.

## Clean base

The audit is based on the clean PR #44 merge `7800176751050c678ccfe24b04c5c263ec6c27bb` with tree `76db5ceec943e568cd1c0be3d4ae2a2ee7808fc6`, parent1 `589d23a81fb27509fb8591dac8695971dc14905f`, and parent2 `e854092cfa2e8cf696e434e2b8b86b72c89ed856`. The certified-head tree equals the merge tree and head-to-merge contains no changed files, so `MERGE_TREE_DRIFT=FALSE`.

## What is actually ready

The following selected control decisions are ready to be referenced by a production case manifest:

- reduced UFOTRI OBT daily-average baseline: formation `0.0006 h^-1`, loss `0.003 h^-1`, with both day/night multipliers kept at `1.0` because no unambiguous split was recovered;
- Eq.39 equilibrium-radiation total root-water uptake equation, with Eq.38 aerodynamic production term still inactive;
- UFOTRI 20/40/40 root-layer distribution;
- `PRESERVE_V3_POST_OBT_ROOT_GAIN` operator split;
- `KEEP_HARVEST_EVENT` environmental/food endpoint boundary.

These decisions define equations/profiles. They do not provide the real meteorology, soil state, crop state, endpoint parameters or live Atmos producer needed for a production run.

## Production-input gaps by subsystem

### Atmosphere

`AtmosphericHTOForcing` requires a complete packet of air HTO concentration, surface deposition flux, temperature, relative humidity, wind speed, precipitation, timestamp/location and provenance.

The frozen exchange contract already defines the required quantity/time/spatial semantics. Air-concentration semantics are compatible with the reviewed CTEAS-Atmos receptor product, but no real producer binding is active. More importantly, a true `Bq m^-2 s^-1` surface-deposition-flux product remains unconfirmed. Puff deposition ledger amounts, accumulated activity, inferred area-normalized rates and silent zero are forbidden substitutes.

Result: atmosphere contract ready; production packet not ready; real binding remains externally blocked.

### Eq.39 root boundary

The controlled equation is implemented, but its caller still must provide independently provenanced temperature, net radiation, LAI, current soil-water state, maximum water, wilting water, latent heat, water density and psychrometric constant.

Temperature can be mapped from a production-ready atmospheric packet. Current soil water can be derived from a production-ready three-layer soil state. Net radiation, LAI and water thresholds have no production source frozen in the selected chain. The three physical conversion constants are explicit inputs and still need reviewed provenance in the production manifest.

Result: root equation/profile ready; production caller packet not ready.

### Three-layer soil

The core intentionally owns storage/conservation only. It requires explicit surface water input/loss, signed L1-L2 and L2-L3 water/HTO fluxes, lower-boundary water/HTO losses, surface HTO re-emission, plus initial layer water/HTO inventories. Root extraction is supplied separately by the controlled root path.

All of these hydrological/transport fields have Python zero defaults, but the source code explicitly states that no hidden hydrology is inferred. Therefore the audit treats each default-zero field as `SOURCE_OR_EXPLICIT_ZERO_POLICY_REQUIRED`. A production case may use zero only when the manifest records that zero as an explicit model/scenario decision with provenance; the default itself is not evidence.

Result: soil architecture ready; dynamic production forcing packet not ready. `FULL_HYDROLOGY=FALSE` remains and is not changed by this finding.

### Leaf exchange

The leaf equation requires `r_a + r_b + r_c` and an equilibrium atmospheric-equivalent concentration. The existing parameter-database hook deliberately uses `production=False`, rejects `ACTIVE` values and provides no fallback. P7.6A also records all three resistance components as provisional with unresolved sources.

The synthetic sensitivity screen gave total resistance a local dose elasticity of `-0.559056`, confirming that the current leaf seam has strong computational reach. This is software propagation evidence only, not a physical uncertainty rank.

Result: leaf pathway connected; production resistance source not ready. This does not authorize Leaf R5.

### TFWT and OBT state basis

TFWT requires plant water content and an initial inventory. Its optional water-loss and transformation fluxes are external terms whose zero defaults are not production evidence. OBT uses the controlled UFOTRI `kf/kr` profile, but initial OBT inventory, plant fresh-mass basis, crop, stage, area basis and provenance remain case inputs.

Result: OBT rate profile controlled; plant-state production packet not ready.

### Food, intake and dose

`HarvestParameters`, `ConsumptionParameters` and `DoseParameters` all default to `parameter_status="provisional"`. Required case quantities include harvest fraction and area, optional TFWT harvest fraction if that transfer is represented, food-product mass, annual consumption amount, consumer/age group identity and dose coefficient with matching radionuclide/pathway identity.

The prior synthetic screen showed local elasticity `+0.844289` for `food.tfwt_harvest_fraction`, the largest value in that software fixture. This is not empirical importance, but it is sufficient to rule out treating provisional endpoint quantities as harmless implementation details.

Result: endpoint equations connected; production parameter/source packet not ready.

## Cross-cutting completeness requirements

A production case must declare, for every required input:

- scenario identity;
- canonical quantity and unit;
- source artifact/dataset and revision/checksum;
- UTC timestamp and time support;
- spatial support, height and/or area basis;
- crop/growth-stage/food/age-group identity where applicable;
- transformation/reconciliation log;
- missing-data policy;
- explicit-zero policy for fields intentionally set to zero;
- readiness state.

No silent unit conversion, local-time assumption, nearest-time substitution, zero fill, forward fill, synthetic-fixture substitution or hidden area conversion is permitted.

## Why the next stage is a case manifest rather than a new solver

The audit found unresolved sources across several already-connected modules. Solving one subsystem first would not prove that a complete production case exists. A case-level manifest provides a single completeness gate and makes the remaining blockers visible without admitting new physics.

Therefore the next stage is:

`V4_PRODUCTION_CASE_INPUT_MANIFEST_R1`

Scope: `CONTROL_PLANE_SCHEMA_AND_FAIL_CLOSED_COMPLETENESS_GATE_ONLY`.

It must not activate production values, fit parameters, bind CTEAS-Atmos, implement Leaf R5, implement full hydrology, or implement multi-pool OBT.

## Remaining blocker ordering

1. `V4_PRODUCTION_CASE_INPUT_MANIFEST_R1` — advance.
2. `REAL_CTEAS_ATMOS_BINDING` — external hold until true surface deposition flux is confirmed.
3. `LEAF_RESISTANCE_PRODUCTION_SOURCE_DECISION` — hold until the case manifest identifies the required crop/stage profile; do not substitute Leaf R5.
4. `THREE_LAYER_SOIL_DYNAMIC_FORCING_SOURCE_DECISION` — hold until the case manifest exposes which water/HTO fluxes need external sources or explicit zero policies; do not infer full hydrology authority.
5. `ENDPOINT_AND_PLANT_STATE_SOURCE_PACKET` — hold for manifest population with reviewed case-specific sources.

No empirical or physical importance ordering is claimed between items 2–5.
