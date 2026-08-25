# V3 P7.8B-1 Equation Gap Analysis

## Scope

This report audits the difference between the frozen V3 equations and the
candidate equations recorded in
`docs/v3/physics/p7_8b1_redesign_specification.yaml`. Candidate equations are
dimensional design forms only. They are not source equations, validated
UFOTRI equations, calibration targets, or runtime defaults.

## Gap summary

| Subsystem | Frozen V3 representation | Missing mechanism | Candidate route | Disposition |
|---|---|---|---|---|
| OBT | First-order TFWT-to-OBT storage | Day/night normalization, activity/photosynthesis, pool scope, mass basis, temperature response | Two-pool precursor model; organ model remains research option | `REQUIRES_MORE_RESEARCH` except basis contract |
| Root | One-layer effective velocity | Layer, water flux, root activity, moisture, aggregation | Layered water-flux model with moisture closure | `REQUIRES_MORE_RESEARCH` |
| Soil | One-layer storage plus signed transport input | Hydraulic movement, diffusion, evaporation, layer/root interaction | Conservative finite-volume layer model | Deferred; `REQUIRES_MORE_RESEARCH` |
| Leaf | `r_a+r_b+r_c` and reciprocal conductance | Stage ontology and dynamic stomatal response | Stage metadata first; bounded response-function extension | `REQUIRES_MORE_RESEARCH` |
| TFWT | Fixed water-content activity storage | Water turnover, growth, dilution | Separate water-mass and activity balances | Deferred; `REQUIRES_MORE_RESEARCH` |
| Food OBT | Event harvest fraction | Continuous/event product state semantics | Continuous or hybrid product compartment | `REQUIRES_MORE_RESEARCH` |
| Food TFWT | Event TFWT fraction | Product-water state and water basis | Separate continuous/hybrid TFWT product state | `REQUIRES_MORE_RESEARCH` |

## Dimensional and conservation checks for candidate forms

| Candidate relation | Dimensional requirement | Required conservation boundary |
|---|---|---|
| `dB/dt = k_f T - k_r B` | `s^-1 * Bq m^-2 = Bq m^-2 s^-1` | TFWT-to-OBT formation and OBT turnover |
| `dP/dt`, `dB_x/dt`, `dB_n/dt` | Every source/loss term must be `Bq m^-2 s^-1` | `P + B_x + B_n` plus external inputs/losses |
| `J_root,i = q_w,i C_w,i` | `m s^-1 * Bq m^-3 water = Bq m^-2 s^-1` | Layer soil inventory decrease equals root transfer plus declared losses |
| `dM_i/dt = F_in - F_out + S_i - lambda M_i` | `Bq m^-2 s^-1` on both sides | Layer and global soil inventories, root and evaporation boundaries |
| `g_ex = 1/(r_a+r_b+r_c)` and `J=g_ex Delta C` | `1/(s m) = m s^-1`; `m s^-1 * Bq m^-3 = Bq m^-2 s^-1` | Signed air/leaf exchange at the leaf boundary |
| `dW/dt = I_W-O_W+G_W` | Water-mass flux basis must be explicit | Plant water mass, with activity carried/lost separately |
| `C_T=M_T/W` | `Bq m^-2 / kg water m^-2 = Bq kg^-1 water` | Activity and water inventories must not be conflated |
| `dM_food,x/dt = k_p M_plant,x-k_loss M_food,x` | `s^-1 * Bq = Bq s^-1` | Plant-product transfer, product loss, and harvest event ledger |

No conversion factor, layer depth, moisture fraction, rate, or response
coefficient is selected by this table.

## OBT options

### Option A — reduced first-order model

The current model is retained. This is the only compatibility profile and is
the correct choice when the data contain only TFWT and aggregate OBT or when
the biological pool scope is unresolved.

### Option B — precursor plus exchangeable/non-exchangeable pools

The candidate equations are:

\[
\frac{dP}{dt}=u_P(T,A,d,s,T_{leaf})-k_PP,
\]
\[
\frac{dB_x}{dt}=k_{PB}P-(k_x+k_{xn})B_x,
\qquad
\frac{dB_n}{dt}=k_{xn}B_x-k_nB_n.
\]

This option provides a place for day/night, activity, stage, and temperature
decisions, but it adds states and parameters that require matched biological
data. It is the preferred design candidate for future research, not an
approved implementation.

### Option C — organ-specific growth model

The generic candidate is

\[
\frac{dB_o}{dt}=u_o(T,A,s,T_{leaf})-k_oB_o.
\]

It remains a research option because organ-specific observations and growth
allocation are not yet available. It must not be introduced merely to create
more fitting degrees of freedom.

## Root options

### Option A — effective velocity

`J_root=v_r C` is algebraically compatible with the current V3 boundary. It
does not resolve layer distribution, water uptake, or moisture response and
therefore remains only the baseline.

### Option B — water-flux coupled layer model

\[
J_{root,i}=q_{w,i}C_{w,i},
\qquad
M_{s,i}=\theta_i\Delta z_iC_{w,i}.
\]

This is the preferred candidate because it exposes the storage and water-flux
bases. It still requires observations or a separately reviewed water-uptake
model for `q_w,i`.

### Option C — moisture response

\[
J_{root,i}=v_{r,i}f_\theta(\theta_i)C_{w,i}.
\]

`f_theta` is a dimensionless bounded closure candidate. It cannot replace
layer ownership, root distribution, or water-flux data. It may be evaluated
only inside Option B, not as a unit-conversion shortcut.

## Soil options

The baseline signed transport interface remains sufficient for the current
one-layer contract. A future layered conservative candidate is:

\[
\frac{dM_i}{dt}=F_{adv,i-1/2}+F_{diff,i-1/2}
 -F_{adv,i+1/2}-F_{diff,i+1/2}
 +S_i-\lambda M_i-J_{root,i}-J_{evap,i}.
\]

The candidate requires a defined water state, layer depths, interface fluxes,
root extraction, evaporation boundary, and sign convention. It is a numerical
state redesign, not an internal replacement for the signed input.

## Leaf options

The frozen chain remains:

\[
r_{tot}=r_a+r_b+r_c,
\qquad g_{ex}=1/r_{tot}.
\]

The candidate dynamic stomatal relation is:

\[
g_s=g_{s,max}F_{light}(L)F_{vpd}(VPD)
F_{temp}(T_{leaf})F_{stage}(s),
\qquad r_c=1/g_s.
\]

The response functions are deliberately unspecified. First test whether
stage metadata improves applicability stratification; only then consider a
dynamic response with matched component-resistance data. The likely impact is
an interface extension, not a numerical-coupling change.

## TFWT options

The frozen activity balance is:

\[
\frac{dM_T}{dt}=J_{leaf}+J_{root}-J_{loss}-J_{transformation}.
\]

The dynamic-water candidate is:

\[
\frac{dW}{dt}=I_W-O_W+G_W,
\qquad C_T=M_T/W,
\]
\[
\frac{dM_T}{dt}=J_{leaf}+J_{root}+J_{in,W}-C_TO_W-J_{transformation}.
\]

The distinction between an activity flux and a water-mass flux is mandatory.
The candidate requires a pipeline water-balance contract and is deferred.

## Food options

For OBT, the baseline event is `M_food,O^+ = h_O M_plant,O(t_h)`. For TFWT,
the baseline is `M_food,T^+ = h_T M_plant,T(t_h)`. A future continuous or
hybrid candidate uses:

\[
\frac{dM_{food,x}}{dt}=k_{p,x}M_{plant,x}-k_{loss,x}M_{food,x},
\quad x\in\{O,T\},
\]

plus a separately declared harvest operator when an event is retained.
OBT and TFWT product inventories must remain separate, and product water
mass must be explicit for TFWT concentration. This redesign necessarily
changes plant-product numerical coupling.

## Selection boundary

P7.8B-1 does not select Option B over Option A as production physics. It
selects only the next design questions and the evidence needed to answer
them. P7.8B2 must record a separate equation-selection decision before any
solver or coupling source can change.
