# EMRAS soybean SB1 unit contract

Internal calculations use SI units. Source units remain alongside canonical
derived units.

## Chamber air HTO

The IAEA table reports activity per volume of air moisture:

```text
C_moisture = Bq/mL water
```

It is not `Bq/m3 air`. At every 5-minute point, the project saturation vapour
pressure function is reused:

```text
e_sat_Pa = saturation_vapour_pressure_pa(T_K)
rho_v_sat_kg_m3 = e_sat_Pa / (R_v * T_K)
rho_v_actual_g_m3 = RH_fraction * rho_v_sat_kg_m3 * 1000
C_air_Bq_m3 = C_moisture_Bq_ml_water * rho_v_actual_g_m3
```

with `R_v = 461.5 J kg-1 K-1` and the transparent approximation
`1 g liquid water = 1 mL water`. Dimensional check:

```text
(Bq/mL water) * (g water/m3 air) * (mL water/g water)
= Bq/m3 air
```

The saturation function is
`src/cteas_ufotri/meteorology/derived_variables.py::
saturation_vapour_pressure_pa`; the validation adapter does not introduce a
second vapour-pressure formula.

## Plant observations

Raw fields are retained:

```text
tfwt_bq_ml_water
obt_bq_ml_combustion_water
```

Canonical comparison fields are:

```text
tfwt_bq_l_water = 1000 * tfwt_bq_ml_water
obt_bq_l_combustion_water = 1000 * obt_bq_ml_combustion_water
```

Model output in `Bq/m3 plant water` is divided by 1000 before comparison with
the canonical `Bq/L plant water` field.

## ERA5

- `t2m`, `d2m`: K.
- `sp`: Pa.
- `u10`, `v10`: m/s.
- `tp`: metres of water accumulated over the interval ending at
  `valid_time`; derived millimetres equal `1000 * tp`.
- `ssrd`, `strd`: J/m2 accumulated over the interval ending at
  `valid_time`; derived W/m2 equals interval energy divided by interval
  seconds.
- `tcc`: fraction in `[0, 1]`.

Interval accumulations are not accumulated a second time.
