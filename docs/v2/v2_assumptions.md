# V2 assumptions and decision log

This file extends, and does not rewrite, `docs/assumptions.md`.

| ID | Decision | Classification | Limitation / resolution |
|---|---|---|---|
| V2-A01 | HTO-only chemistry | project scope | HT deposition, oxidation, and HT-specific C2 are excluded |
| V2-A02 | Wet removal is allocated once between dry and wet loss by competing exponential rates | `PROJECT_EXTENSION` | prevents double counting; tested as a ledger |
| V2-A03 | Power-law washout parameters are replaceable YAML values | `PROVISIONAL` until sourced | manual reports sparse data and two weakly rain-dependent classes |
| V2-A04 | Leaf exchange uses one net bidirectional flux | `MANUAL_DERIVED` | avoids simultaneous deposition and reverse exchange |
| V2-A05 | Eq. (32) is not used literally as printed | source ambiguity | its OCR dimensions are inconsistent; resistance equations govern |
| V2-A06 | Basic `Es*Cs + Tp*Cp` remains the conservation reference | `MANUAL_DERIVED` | empirical Eq. (44) is a selectable comparison mode |
| V2-A07 | Crop categories and edible-part growth are configurable | `PROJECT_EXTENSION` | manual explicitly lacks adequate grain/root compartments |
| V2-A08 | Animal paths are minimal inventory models | `PROJECT_EXTENSION` | not all historical UFOTRI animal detail is claimed |
| V2-A09 | Dose is research screening only | project scope | no regulatory or site-validation claim |
| V2-A10 | Three-box soil uses manual layer depths/root fractions but a conservative box solver, not Richards Eq. (37) | `PROJECT_EXTENSION` | full PDE and soil-specific hydraulic inversion deferred |
| V2-A11 | Uncertainty distributions and seeds are configuration | `PROJECT_EXTENSION` | deterministic core remains independently testable |
| V2-A12 | Dry and wet plume losses are the authoritative surface-input ledgers | `PHYSICAL_INVARIANT` | separate explicit uniform footprints rescale local flux only; `v_d C_a` is diagnostic |

When a literature value is introduced, its citation, version/date, unit
conversion, applicability, and classification must be added here or in a
dedicated parameter provenance table before it is used as a default.
