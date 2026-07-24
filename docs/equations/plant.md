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

Direct leaf uptake is present but disabled, as requested. OBT formation defaults
to the manual's daily-average 0.06% h-1; turnover defaults to 0.3% h-1. Turnover
returns to TFWT so internal transfer conserves activity. Optional day/night
multipliers default to 1.5/0.5, preserving the configured average over equal
12-hour day/night periods. Root HTO uptake may be immediate or delayed by an
integral number of steps, including three hours. Dynamic phenology, edible
compartments, animals, and dose are outside this environmental core.
