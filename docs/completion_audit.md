# Formal minimal baseline completion audit

Updated: 2026-07-24

The previous unconditional `COMPLETE` claim is replaced by the bounded
`FORMAL_MINIMAL_BASELINE_V1` assessment. The accepted conservation domain is
the surface soil/TFWT/OBT box. The atmosphere has a separate steady-state
source/sink ledger and is not claimed as a dynamic inventory.

| Audit condition | Resolution |
|---|---|
| Ambiguous whole-system mass balance | resolved by explicit surface-box naming and diagnostics |
| Rain HTO routed through runoff | resolved by precipitation/infiltration/runoff interfaces and tests |
| Calm/near-zero Gaussian singularity | resolved by explicit configurable policy and diagnostics |
| Deposition without plume depletion | dry segment-exponential project mode implemented and tested |
| One-step feedback delay | replaced by configurable 3600 s physical delay |
| Root fraction ambiguity | frozen as single-layer 1.0 project closure |
| Eq. (40) shading ambiguity | radiation-term-only mode is formal default |
| Feedback area duplication | rectangle-derived area validated against compatibility fields |
| Saved-artifact-only acceptance | `--recompute` runs five cases in a temporary directory with provenance |

Wet scavenging and advanced REEM/DIFF/ZT remain explicit limitations. The
formal recommendation is determined in
`docs/formal_minimal_baseline_v1_assessment.md`.
