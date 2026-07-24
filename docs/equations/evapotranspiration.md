# Evapotranspiration

Default PET follows manual Eq. (38), not FAO-56 Penman-Monteith. The radiation
and vapour-deficit terms are combined in SI and divided by latent heat and water
density to yield m s-1. Because the scanned manual does not supply a complete
unit conversion for its empirical aerodynamic term, the coefficient is a
central, provisional configuration parameter. Setting it to zero gives the
equilibrium form in Eq. (39).

Soil potential evaporation follows Eq. (40):
\(E_{0s}=E_0\exp(-0.398 LAI)\). The remainder is potential transpiration.
The soil-moisture factor follows Eq. (41),
\(\alpha=1.26[1-\exp(-10.56W_s/W_{max})]\), capped at one. Eq. (42)-(43)
then scale both fluxes. At or below wilting storage, transpiration and root
uptake are zero. v0.1 uses \(U_s=T_p\) without the manual's three-hour lag.
