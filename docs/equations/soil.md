# Soil equations

The top 5 cm is a single water bucket:

\[
\frac{dW_s}{dt}=P-E_s-T_p-L_s-R_o.
\]

Losses cannot remove water below the configured minimum. Storage above
\(W_{max}\) becomes deep drainage; optional infiltration-excess runoff is an
independent boundary provider.

HTO follows manual Eq. (2) in inventory form:

\[
\frac{dM_s}{dt}=v_dC_a-E_sC_s-U_sC_s-L_sC_s-\lambda_TM_s.
\]

Precipitation HTO enters through the optional rainwater concentration interface
\(P C_{rain}\), whose default is zero. Each outgoing flux is limited
proportionally if a step would exceed the available inventory.

The formal baseline splits \(P=P_{inf}+R_o\). Only
\(P_{inf}C_{rain}\) enters soil; \(R_oC_{rain}\) is a recorded bypass flux.

## V2 experimental three-box extension

`surface_root_deep_3box` provides a standalone conservative API for 0-5,
5-15, and 15-30 cm. Precipitation and atmospheric deposition enter only the
surface. Only the surface evaporates. Root uptake is distributed by configured
fractions; water and advected HTO move downward; optional concentration-gradient
diffusion is bidirectional; deep leakage is a boundary. Each donor's concurrent
HTO outflows are proportionally limited.

The layer depths and 20/40/40% nutrient-crop roots are manual anchors, but the
box hydraulics are a `PROJECT_EXTENSION`, not a solution of Richards Eq. (37).
The API is experimental and is not selected by the formal short-case coupler.
Selecting it in `run_short_case` raises an error; RC1 makes no formal
multi-layer performance claim. See
`docs/v2/multibox_integration_roadmap.md` for the deferred coupling contract.
