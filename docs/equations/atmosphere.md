# Atmospheric equations

The v0.1 continuous point-source model uses a reflected Gaussian plume:

\[
C(x,y,0)=\frac{Q}{\pi u\sigma_y\sigma_z}
\exp[-y^2/(2\sigma_y^2)-H_e^2/(2\sigma_z^2)].
\]

This is consistent with the ground-level form of manual Eq. (6). Rural
Turner/Pasquill-Gifford approximations provide \(\sigma_y,\sigma_z\).
Upwind concentration and zero-source concentration are zero. The primary plume
uses rural power-law conversion from 10 m wind to effective stack height.
`fixed` rise is the default; `briggs_simple` provides a replaceable
distance-dependent buoyancy/momentum option. A finite reflecting mixing layer
uses image sources above and below its top.

The re-emitted flux is integrated over a rectangular ground source by midpoint
quadrature, directly approximating manual Eq. (4). Quadrature convergence and
linearity are tested. Receptors may be declared directly in wind coordinates,
as local east/north offsets, or as longitude/latitude; meteorological wind
direction rotates the latter two into plume coordinates.

Stability can be fixed A-F or diagnosed hourly by a simple rural Turner scheme
using wind, net radiation, and optional cloud cover. ERA5 boundary-layer height
overrides the configured mixing height when present.

## Formal minimal baseline v1 additions

Below 0.5 m s-1, the default records
\(u_{\mathrm{eff}}=\max(u,0.5\,\mathrm{m\,s^{-1}})\). `skip_gaussian` and
`error` are supported alternatives. Dry fallout depletion is a
`PROJECT_SIMPLIFICATION`:
\(Q_{j+1}=Q_j\exp[-(v_d/H_m)\Delta x/u_{\mathrm{eff}}]\).
This is not exact manual Eq. (6). Wet scavenging is `NOT_IMPLEMENTED`.
