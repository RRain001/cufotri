# Plant equations

\[
C_p=M_p/W_p
\]

\[
\frac{dM_p}{dt}=U_sC_s+F_{leaf}+k_{turn}M_{OBT}
-T_pC_p-k_{OBT}M_p-\lambda_TM_p
\]

\[
\frac{dM_{OBT}}{dt}=k_{OBT}M_p-k_{turn}M_{OBT}-\lambda_TM_{OBT}.
\]

The V1 direct leaf uptake interface remains available and disabled by default.
V2 adds `off`, `deposition_only`, and `bidirectional_resistance` modes. The
bidirectional net flux is

\[
F_{ap}=g_c(C_a-C_{p,eq}),\qquad
g_c=(r_a+r_b+r_c)^{-1}.
\]

Here \(C_{p,eq}\) converts TFWT activity to equilibrium air activity using
actual water-vapour density, water density, and the configured liquid/vapour
fractionation. Canopy resistance uses LAI, day/night stomatal resistance, and
a VPD multiplier. LAI=0 gives zero exchange. Positive flux enters TFWT;
negative flux is the same limited plant-to-air boundary flux and participates
in re-emission feedback. This closure is `MANUAL_DERIVED_PROVISIONAL`.

OBT formation defaults
to the manual's daily-average 0.06% h-1; turnover defaults to 0.3% h-1. Turnover
returns to TFWT so internal transfer conserves activity. Optional day/night
multipliers default to 1.5/0.5, preserving the configured average over equal
12-hour day/night periods. Root HTO uptake may be immediate or delayed by an
integral number of steps, including three hours. Dynamic phenology, edible
compartments, animals, and dose are outside this environmental core.

## V2 edible compartments

The vegetative whole-plant source pools transfer activity once into separate
edible TFWT and OBT inventories. This avoids treating total plant concentration
as edible concentration and avoids counting an edible inventory both inside and
outside the conserved system. Biomass growth changes the fresh, dry, and water
denominators and therefore dilutes concentration without destroying activity.
At harvest, edible activity is split into harvested product and harvest loss;
remaining vegetative activity is an explicit crop-reset boundary.
