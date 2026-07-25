# Independent pathway reference equations

`REFERENCE_IMPLEMENTATION_INDEPENDENCE = NO_FORMAL_MODEL_IMPORTS`

The implementation in this directory parses the validation case directly. It
does not import plume, depletion, soil, plant, food, or dose code from
`src/cteas_ufotri`.

For the frozen centerline case:

\[
\sigma_y = \frac{a_y x}{\sqrt{1+10^{-4}x}},\qquad
\sigma_z = \frac{a_z x}{\sqrt{1+b_zx}}
\]

\[
C_a = \frac{Q_r}{2\pi u\sigma_y\sigma_z}
2\exp\left[-\frac{1}{2}\left(\frac{H}{\sigma_z}\right)^2\right]
\]

where the factor two is ground reflection and crosswind distance is zero.

Competing dry and wet removal use independent rates
\(k_d=v_d/H_m\) and \(k_w=\Lambda\):

\[
Q_r=Q_0e^{-(k_d+k_w)x/u}
\]

\[
L_d=(Q_0-Q_r)\frac{k_d}{k_d+k_w},\qquad
L_w=(Q_0-Q_r)\frac{k_w}{k_d+k_w}.
\]

The ecological surface flux is \((L_d+L_w)/A\). With water fluxes disabled in
this bounded case, the one-box soil update is

\[
M_s^{n+1}=M_s^n+\Delta t
\left(\frac{L_d+L_w}{A}-\lambda M_s^n\right).
\]

Fixed-conductance leaf uptake is \(F_\ell=v_\ell C_a\). The TFWT and OBT boxes
are advanced independently by

\[
M_f^{n+1}=M_f^n+\Delta t
\left(F_\ell+k_tM_o^n-k_fM_f^n-\lambda M_f^n\right),
\]

\[
M_o^{n+1}=M_o^n+\Delta t
\left(k_fM_f^n-k_tM_o^n-\lambda M_o^n\right).
\]

The inhalation and skin dose increment is

\[
\Delta E =
C_a B\frac{\Delta t}{86400}e_{\rm HTO}(1+f_{\rm skin}).
\]

The implementation also contains a non-zero food ingestion calculation
\((C_{\rm HTO}I e_{\rm HTO}+C_{\rm OBT}I e_{\rm OBT})\Delta t/86400\),
which is unit-tested separately. Food ingestion is zero in case 001 so the
end-to-end comparison isolates the atmospheric and environmental boxes.

Thresholds were frozen before execution:

- Gaussian and competing-depletion scalar components: relative error at most
  \(10^{-6}\);
- time-integrated soil/TFWT/OBT boxes: relative error at most 1%;
- simplified end-to-end pathway and dose: relative error at most 5%;
- activity residual: absolute value at most \(10^{-8}\) Bq m-2.
