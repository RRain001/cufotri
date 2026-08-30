# UFOTRI cross-module fidelity qualification R1

## Candidate verdict

`CANDIDATE_PENDING_EXACT_HEAD_CI`

Target machine result: `PASS_CONTROLLED_CROSS_MODULE_FIDELITY_QUALIFICATION`.

This stage qualifies the already-reconstructed internal/manual-compatible mechanisms. It does not create a new production path and does not close the deferred real CTEAS-Atmos dependency.

## Qualification composition

The machine gate re-executes the frozen RC1 composition and the existing controlled end-to-end chain, then re-executes the numerical or contract gates required to cover the post-RC1 fidelity work: OBT conservation/numerics, coupled water/HTO hydrology, HT-derived HTO provenance, re-emission area-source compatibility, and the Canada/ITER benchmark contracts.

The controlled end-to-end chain supplies direct deterministic-repeat, restart-equivalence, soil→root `J=qC`, plant balance, coupled balance and food→intake→dose inventory checks. OBT and hydrology numerical gates supply explicit timestep-refinement evidence. E3/F1 gates preserve HT/HTO provenance and prevent double-counting or false HT-derived attribution.

## UFR-16 root-delay closure

The initial gap audit classified the approximately 3 h short-term root-uptake delay as a historical implementation not activated in RC1. The implementation remains present in the current historical `case.py` path.

For the existing advanced controlled case:

- configured delay = 10800 s;
- internal step = 600 s;
- queue length = 18 intervals;
- the first 18 root-uptake outputs must be zero because the history queue is initialized with zeros;
- every later root-uptake value must equal the plant-transpiration diagnostic from exactly 18 intervals earlier.

G3 checks this relationship by executing `run_short_case`. It also checks that the V4 root solver still contains no internal queue/hidden delay. UFR-16 is therefore reconciled as an existing optional compatibility mode; it is not promoted to the RC1 or root-v4 default.

## RC1 fallback versus fidelity paths

The two paths are intentionally different. G3 records the following axes rather than requiring numerical equality:

| Axis | RC1 fallback | UFOTRI fidelity scope |
|---|---|---|
| Leaf | baseline resistance chain | opt-in Eq. (7)–(31) path |
| OBT | reduced kf/kr baseline | recovered TFWT/exchangeable role + non-exchangeable OBT semantics |
| Soil hydrology | controlled three-layer/external flux boundary | opt-in Eq. (33)–(37) hydrology |
| Food chain | `KEEP_HARVEST_EVENT` endpoint | recovered continuous UFOTRI compartment paths |
| HT | absent from controlled RC1 baseline | opt-in HT deposition→soil HTO/provenance path |
| Re-emission | controlled legacy boundary | opt-in Eq. (4)–(6) area-source adapter |
| Root delay | inactive | historical 3 h option requalified, not defaulted |

This distinction preserves RC1 as fallback while allowing fidelity qualification to prove restored manual mechanisms.

## Gap-matrix disposition

G3 requires an exact 30/30 disposition against the original gap audit.

Internal A–F work closes the recoverable leaf, OBT, soil/hydrology, food/exposure, HT→HTO and re-emission mechanisms. UFR-16 is closed by existing-option requalification. Canada and ITER are closed only to the evidence level available from the manual; full empirical/atmospheric replay remains source-limited. UFR-01/03/04/05 remain external atmospheric dependencies. UFR-29/30 remain blocked by unavailable original software assets.

The stage does not convert any of those external/source limitations into a synthetic success.

## Hard boundaries

The following remain false after G3:

- production source/default changes;
- parameter activation or calibration;
- empirical validation;
- physical-accuracy or production-readiness claims;
- real CTEAS-Atmos HT/HTO binding claims;
- full Canada numerical/empirical replay;
- full ITER atmospheric numerical replay;
- original UFOTRI executable numerical equivalence;
- `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE`.

After exact-head CI and no-drift merge, the roadmap must be synchronized in a separate control-plane PR before the final G4 gate is entered.
