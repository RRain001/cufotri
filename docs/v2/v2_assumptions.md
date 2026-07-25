# V2 assumptions and decision log

This file extends, and does not rewrite, `docs/assumptions.md`.

Current release status is
`FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE`, based on the accepted RC2
independent re-audit. This status is bounded by the machine-readable limits in
`docs/v2/v2_candidate_limitations.yaml` and does not mean site calibration,
regulatory validation, or complete UFOTRI equivalence.

| ID | Decision | Classification | Limitation / resolution |
|---|---|---|---|
| V2-A01 | HTO-only chemistry | project scope | HT deposition, oxidation, and HT-specific C2 are excluded |
| V2-A02 | Wet removal is allocated once between dry and wet loss by competing exponential rates | `PROJECT_EXTENSION` | prevents double counting; tested as a ledger |
| V2-A03 | Power-law washout uses named, replaceable YAML parameter sets | `LITERATURE_COMPARISON_NOT_UFOTRI` research default plus project uncertainty bounds | default Japanet comparison is not relabelled as UFOTRI; low/central/high and the declared 4 x 3 grid bracket uncertainty |
| V2-A04 | Leaf exchange uses one net bidirectional flux and meteorology-responsive resistances | `MANUAL_DERIVED` plus `LITERATURE_PARAMETERIZATION` | avoids simultaneous deposition/reverse exchange; Pasquill-to-Monin and flat-plate boundary closures are not site-calibrated UFOTRI parameters |
| V2-A05 | Eq. (32) is not used literally as printed | source ambiguity | its OCR dimensions are inconsistent; resistance equations govern |
| V2-A06 | Basic `Es*Cs + Tp*Cp` remains the conservation reference | `MANUAL_DERIVED` | empirical Eq. (44) is a selectable comparison mode |
| V2-A07 | Crop categories and edible-part growth are configurable | `PROJECT_EXTENSION` | manual explicitly lacks adequate grain/root compartments |
| V2-A08 | Animal paths use minimal inventories; beef uses explicit continuous herd turnover and product storage | `PROJECT_EXTENSION` | turnover and edible mass are replaceable assumptions; dose consumes only available produced activity |
| V2-A09 | Dose is research screening only | project scope | no regulatory or site-validation claim |
| V2-A10 | Three-box soil uses manual layer depths/root fractions but a conservative box solver, not Richards Eq. (37) | `PROJECT_EXTENSION` | full PDE and soil-specific hydraulic inversion deferred |
| V2-A11 | Uncertainty distributions and seeds are configuration | `PROJECT_EXTENSION` | deterministic core remains independently testable |
| V2-A12 | Dry and wet plume losses are authoritative independent activity components; the ecological box uses a separate reference area | `PHYSICAL_INVARIANT` plus `PROJECT_EXTENSION` geometry | \(M_d=F_dA_d\), \(M_w=F_wA_w\), and downstream \(M_d+M_w\) close for unequal footprints; all three areas are replaceable and `v_d C_a` is diagnostic |
| V2-A13 | Pasture uses `perennial_dormant_season`, minimum LAI 0.25, DOY 150/220/290 cuts, 50% shoot removal, and a provisional root activity fraction of 0.30 | `PROJECT_EXTENSION` | roots and shoots are explicit and root activity survives cuts; dates, LAI, biomass, cut fraction, and root fraction are not site calibrated |
| V2-A14 | Full-model uncertainty samples only parameters active under the selected modes | `PROJECT_EXTENSION` | n=256 stabilizes quantiles; weak-parameter Spearman order remains `LIMITED_WITH_EVIDENCE` |

When a literature value is introduced, its citation, version/date, unit
conversion, applicability, and classification must be added here or in a
dedicated parameter provenance table before it is used as a default.

## Leaf-resistance parameterization sources and limits

The canopy resistance follows UFOTRI manual Eqs. (12)-(14), (18), and
(22)-(27). Pasquill class is converted to Monin-Obukhov length with
\(1/L=a+b\log_{10}(z_0)\) and the Golder coefficients reproduced by the
[NSW EPA Approved Methods (2022), Section 4.3.4 and Table 5](https://www.epa.nsw.gov.au/sites/default/files/22p3963-approved-methods-for-modelling-and-assessment-of-air-pollutants.pdf).
That mapping is labelled `LITERATURE_PARAMETERIZATION`, not an original
UFOTRI parameter set.

Leaf boundary resistance uses the average laminar flat-plate mass-transfer
correlation \(Sh=0.664Re^{1/2}Sc^{1/3}\), as tabulated in
[Perry's Chemical Engineers' Handbook, Section 5](https://schneider.cheme.cmu.edu/Files/Perry%27s%20Chemical%20Engineers%27%20Handbook%207th%20Edition/5.%20Heat%20and%20Mass%20Transfer.pdf).
The implementation rejects \(Re>5\times10^5\). Default leaf length, air
viscosity, and water-vapour diffusivity are replaceable research parameters;
they are not crop- or site-calibrated. LAI is applied once through
\(r_c=r_{ST}/LAI\), with no additional LAI multiplier on the resulting flux.
UFOTRI Eq. (27) uses \(\rho_{v,\mathrm{sat}}\); RH affects VPD resistance but
does not multiply the equilibrium concentration.

## Wet-scavenging parameter source and uncertainty

The research default `iaea_emras_japanet_comparison` uses
\(a=5.0\times10^{-5}\), \(b=0.8\), and precipitation in mm h-1 from the
[IAEA EMRAS Tritium Working Group final report, Japanet Eq. II.8.7](https://www-ns.iaea.org/downloads/rw/projects/emras/draft-final-reports/emras-tritium-wg.pdf).
It is explicitly `LITERATURE_COMPARISON_NOT_UFOTRI`: the report's UFOTRI
comparison used a different time-dependent resistance treatment.

For \(\Lambda=aP^b\), \(\Lambda\) is s-1 and \(a\) has compound units
\(\mathrm{s^{-1}(mm\,h^{-1})^{-b}}\). Project low/central/high bounds are
configuration-level research assumptions, not calibrated site values. The
formal sensitivity grid evaluates \(a=\{10^{-5},2\times10^{-5},
5\times10^{-5},10^{-4}\}\) and \(b=\{0.6,0.8,1.0\}\) through wet plume loss,
surface input, soil, TFWT, OBT, food concentration, and ingestion dose.
