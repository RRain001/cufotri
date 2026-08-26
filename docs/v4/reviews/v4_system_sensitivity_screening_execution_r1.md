# Independent review — V4 system sensitivity screening execution R1

## Review scope

Review the successful PR #21 execution result and determine whether it supports a
software-screening closure and a next-stage design decision without being
misrepresented as physical validation.

## Evidence checked

- exact PR head: `6a4c87b4daeef672451e14d42a7935401e58c476`;
- Protected Integration Gate run `32947990894`, job `98112824987`;
- Actions checkout merge SHA `8ee97771618bc3952fd9d8fb947a252aecad0267`;
- portable suite: `1159 passed, 1 skipped, 57 deselected`;
- explicit frozen-boundary suite: `238 passed`;
- screening machine status: `PASS_SOFTWARE_SCREENING`;
- deterministic, restart, conservation, structural-zero and step-convergence
  gates all passed.

The earlier failing head `9bbed395...` and its synthetic-fixture conditioning
failure are retained in the result record. No production solver change was used
to obtain the pass.

## Review findings

1. The execution is reproducible enough for a **software local-screening**
   conclusion. It is not an empirical validation dataset and does not contain
   evidence-based uncertainty distributions.
2. The nearly opposite root-uptake coefficient and soil-water responses are
   structurally consistent with the current one-layer ratio form, so they must
   not be read as two independently validated parameters.
3. The large TFWT harvest-fraction response is endpoint-definition dependence
   inside a provisional food event model; it cannot be used to prioritize that
   parameter as a physically important transfer coefficient.
4. The large air-HTO/total-resistance responses confirm computational reach of
   the current leaf path, but the existing Leaf R4 evidence hold remains valid.
5. The short-horizon deposition response is affected by the frozen step-start
   soil read at the root boundary and cannot be extrapolated to long-term
   pathway importance.

## Verdict

`PASS_INDEPENDENT_REVIEW_WITH_INTERPRETATION_BOUNDARIES`

The next admissible stage is a control-plane-only
`V4_ROOT_SOIL_LAYERED_BOUNDARY_DECISION_R1`. No layered implementation, fixed
layer count, root parameter activation, full hydrology, leaf R5, global
uncertainty analysis, or real CTEAS-Atmos binding is authorized by this review.
