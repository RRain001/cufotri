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
