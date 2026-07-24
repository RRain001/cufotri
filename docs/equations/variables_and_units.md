# Variables and units

See `manual_scope_and_mapping.md` for the manual-symbol conflict, chemical
scope, state/diagnostic/input classification, and day/night logic.

| UFOTRI / model symbol | Code name | Meaning | SI unit | Kind |
|---|---|---|---|---|
| \(C_a=X_{HTO}\) | `air_hto_concentration` | ground-level air HTO | Bq m-3 | concentration |
| \(W_s\) | `soil_water_storage` | topsoil water depth | m | water inventory |
| \(M_s=C_{S,HTO}\) | `soil_hto_inventory` | topsoil HTO | Bq m-2 | activity inventory |
| \(C_s=M_s/W_s\) | `soil_hto_concentration` | soil-water HTO | Bq m-3 | concentration |
| \(W_p\) | `plant.water_storage_m` | plant free-water depth equivalent | m | water inventory |
| \(M_p=C_{P,HTO}\) | `plant_tfwt_inventory` | plant TFWT | Bq m-2 | activity inventory |
| \(C_p=M_p/W_p\) | `plant_tfwt_concentration` | plant-water HTO | Bq m-3 | concentration |
| \(M_{OBT}\) | `plant_obt_inventory` | non-exchangeable OBT | Bq m-2 | activity inventory |
| \(F_{as}\) | deposition | air-to-soil HTO | Bq m-2 s-1 | continuous flux |
| \(F_{re}\) | total re-emission | soil + plant to air | Bq m-2 s-1 | continuous flux |
| \(E_s,T_p,U_s,L_s\) | corresponding output columns | water fluxes | m s-1 | continuous flux |

Water mass is \(\rho_w W_s\) in kg m-2 and is never substituted for \(W_s\).
Rates in s-1 are multiplied by inventory to obtain Bq m-2 s-1.
