# V3-P2 Soil Layer Framework

Status: `FRAMEWORK_COMPLETE`

UFOTRI soil physics: `NOT_IMPLEMENTED`

Validated soil parameters: `NOT_IMPORTED`

UFOTRI numerical equivalence: `NOT_CLAIMED`

## Responsibility and boundary

The P2 module establishes a fixed three-layer HTO soil-media contract:

```text
atmospheric HTO forcing
        |
        v
surface soil layer
        |
        v
root-zone coupling seam
        |
        v
plant uptake interface (reserved, no uptake)
```

It owns explicit layer state, supplied atmospheric deposition, parameter
provenance, a replaceable transport seam, deterministic test kernels, and a
soil activity ledger. It does not migrate UFOTRI equations, import UFOTRI
soil values, calculate root uptake, couple crops or food, calculate dose, or
claim field validation.

The P2 package is isolated from the existing V2 `soil.multibox` and
configuration-driven pathways. Adding this framework does not enable or
replace the V2 one-box default.

## State representation

`SoilState` requires exactly three ordered `SoilLayer` records with IDs 1, 2,
and 3. Layer geometry is explicit; array position has no undocumented
meaning.

| Field | Contract |
|---|---|
| `layer_id` | integer 1, 2, or 3 |
| `depth_top`, `depth_bottom` | m, with `0 <= top < bottom` |
| `water_inventory` | water storage in m (`m3 m-2`) |
| `hto_activity` | HTO inventory in `Bq m-2` |
| `hto_inventory` | explicit property alias for `hto_activity` |
| `hto_concentration` | derived `Bq m-3 water` |
| `water_content` | derived dimensionless ratio `water_inventory / thickness` |

Positive HTO water inventory requires positive water storage. All numeric
values are finite and non-negative where applicable. `SoilState` is immutable
and has no global state or shared leaf state.

## Atmospheric input interface

`SoilForcing` carries `hto_air_concentration` in `Bq m-3 air` and a supplied
`deposition_flux` in `Bq m-2 s-1`. `apply_atmospheric_input(state, forcing, dt)`
integrates only the supplied deposition flux and adds it to layer 1:

```text
atmospheric_input = deposition_flux * dt
```

The P2 framework does not infer deposition velocity, scavenging, or another
air-to-soil equation from air concentration.

## Physics seam

The canonical numerical call is:

```python
new_state, balance = model.advance(soil_state, forcing, dt)
```

The coordinator invokes
`SoilPhysics.step(state, forcing, dt, parameters)` after atmospheric input.
`FrameworkOnlyPhysics` fails closed until a reviewed UFOTRI soil kernel is
available. `ZeroTransportKernel` and `SyntheticTransportKernel` are explicitly
`TEST_ONLY`; they validate state movement, determinism, positivity, and
conservation only.

The synthetic kernel uses an inventory-difference transfer harness and
first-order decay solely for numerical tests. Its equations are not UFOTRI
equations and do not constitute physical validation.

## Root-zone coupling seam

`get_root_zone_activity(state, layer_id=2)` returns a read-only
`RootZoneActivity` record containing root-zone inventory and water
concentration. It does not remove activity, mutate plant state, or report an
uptake flux. P2 `output_to_plants` is therefore zero in the test kernels.

## Parameter database and provenance

`SoilParameters.from_database()` resolves all executable values through
`ParameterDatabase.get_entry()` in the `soil.*` namespace:

```text
soil.interlayer_transport_rate
soil.decay_rate
```

Placeholder, missing, non-finite, negative, or unit-incompatible entries fail
closed. No soil parameter database values are added to or substituted into
V3-P0. Tests use an explicitly synthetic `TEST_ONLY` database and retain its
package SHA-256 plus entry-level provenance.

## Mass-balance contract

All ledger values are integrated activity in `Bq m-2`:

```text
closure_error =
    initial_inventory
  + atmospheric_input
  - output_to_plants
  - decay_loss
  - final_inventory
```

`internal_transfer` is reported as a positive magnitude and reconciled as an
equal source/destination movement. It has no net contribution to the global
inventory identity. The model rejects non-finite or negative terms and fails
closed when the ledger does not close within the declared tolerance.

## Validation status

P2 tests cover three-layer initialization, explicit geometry, invalid depth,
negative activity, placeholder and invalid parameter rejection, atmospheric
input conservation, zero transport, deterministic synthetic transport,
root-zone read-only coupling, positivity protection, provenance, and ledger
closure. These are software-contract and conservation tests only.

```yaml
Framework: COMPLETE
UFOTRI_soil_physics: NOT_IMPLEMENTED
Validated_parameters: NOT_IMPORTED
Field_validation: NOT_PERFORMED
UFOTRI_numerical_equivalence: NOT_CLAIMED
```
