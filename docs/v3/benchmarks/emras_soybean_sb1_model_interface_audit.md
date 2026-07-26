# EMRAS soybean SB1 model interface audit

```text
MODEL_INTERFACE_STATUS = RUNNABLE_WITH_VALIDATION_ADAPTER_ONLY
AUDIT_CLASS = B
FORMAL_PHYSICS_CHANGE_REQUIRED = FALSE
```

| required_input | current_input | unit | time_resolution | mapping_status | code_location | limitation |
|---|---|---|---|---|---|---|
| air HTO | `advance(... air_concentration_bq_m3)` | Bq m-3 air | arbitrary step | DIRECT_IN_KERNEL_ADAPTER_REQUIRED_IN_RUNNER | `src/cteas_ufotri/coupling/integrator.py` | `run_short_case` normally computes air HTO from a Gaussian source and has no direct-air time-series column |
| temperature | `air_temperature_k` | K | arbitrary step | DIRECT | `coupling/integrator.py` | chamber value is measured; outdoor value is ERA5 |
| relative humidity | temperature plus `dewpoint_temperature_k` | K/K yielding fraction | arbitrary step | DERIVED_WITH_PROJECT_MAGNUS_RELATION | `meteorology/derived_variables.py` | chamber dewpoint is derived from published T/RH |
| wind | `wind_speed_m_s` | m s-1 | arbitrary step | DIRECT_WITH_BOUNDARY_LIMITATION | `plant/leaf_exchange.py` | chamber fan circulation is reported but its rate is missing; adapter passes zero and exposes the formal 0.05 m/s clamp |
| radiation | net radiation in Penman terms | W m-2 | arbitrary step | VALIDATION_MAPPING | `meteorology/fallback_fluxes.py` | chamber klux uses the report midpoint 4.75 W m-2 klux-1; outdoor net radiation uses the existing absorbed-shortwave-minus-fixed-longwave fallback |
| precipitation | `precipitation_m_s` | m s-1 | arbitrary step | DIRECT | `coupling/integrator.py` | chamber precipitation is zero |
| plant-body TFWT | plant TFWT inventory / water storage | Bq m-3 water | model step | DIRECT_CANONICAL_CONVERSION | `plant/tfwt.py` | fixed measured exposure water storage does not represent later biomass dilution |
| dynamic depuration | transpiration plus bidirectional leaf release | Bq m-2 s-1 | model step | DIRECT | `coupling/integrator.py`, `plant/leaf_exchange.py` | no chamber mixing observation; no dynamic measured plant-water storage |
| background air HTO | direct air boundary | Bq m-3 air | model step | DIRECT | validation adapter | monthly ranges are assumptions, not hourly measurements |
| pods TFWT | edible TFWT inventory | Bq m-3 water | model step | PROVISIONAL_STRUCTURAL_MAPPING | `plant/edible.py` | generic edible allocation is not soybean-pod calibrated |
| stem/leaf/shell/seed OBT | plant and edible OBT inventories | Bq m-2 | model step | AVERAGES_ONLY | `plant/obt.py`, `plant/edible.py` | current model cannot resolve the four measured organs separately |

## Adapter boundary

The validation adapter may splice the IAEA chamber interval into ERA5,
resample to five minutes, convert units, call the existing calculation kernel,
and map model inventories to the published comparison units. It does not
change any model equation, add a hidden exchange process, tune a clearance
rate, or alter formal configuration files.

The following assumptions remain visible and replaceable:

- institutional-area rather than exact-plot coordinate;
- ERA5 instead of the organizer tower files;
- zero-at-start chamber HTO boundary;
- unreported chamber fan rate represented by the existing minimum-wind clamp;
- generic published soybean LAI curve, explicitly not measured for SB1;
- fixed exposure plant-water storage for the primary plant-body comparison;
- generic existing edible allocation for a provisional pods structural check.

Because the primary target is plant-body TFWT uptake and depuration and that
path is executable without a formal equation change, the overall result is B,
not C. Pods and organ-resolved OBT results cannot be promoted beyond
structural diagnostics.
