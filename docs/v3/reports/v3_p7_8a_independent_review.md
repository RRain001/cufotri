# V3 P7.8A Independent Review

Review type: control-plane completeness, prioritization, coupling, and
runtime-boundary review
Review status: `PASS_PHYSICS_REDESIGN_PRIORITIZATION`
Review boundary: documentation and test artifacts only; no empirical or
implementation claim

## Review checklist

| # | Review question | Verdict | Evidence |
|---:|---|---|---|
| 1 | Are all P7.6D redesign blockers represented? | PASS | The registry contains exactly the nine P7.6D `REDESIGN_REQUIRED` parameter IDs |
| 2 | Is every item ranked with the requested criteria? | PASS | Each item records scientific importance, dose relevance, uncertainty impact, validation availability, and implementation complexity |
| 3 | Does every item have a rationale, roadmap stage, and validation requirement? | PASS | Registry fields `rationale`, `recommended_stage`, `required_validation_data`, and `expected_exit_evidence` are mandatory in the test contract |
| 4 | Are KEEP/EXTEND/REDESIGN subsystem decisions explicit? | PASS | The registry separates current baseline decisions from redesign item decisions for leaf, TFWT, OBT, soil, root, food, consumption, and dose |
| 5 | Are the four coupling states frozen and applied consistently? | PASS | The coupling matrix covers every governed item and uses only the four declared states |
| 6 | Are root and food coupling consequences distinguished from interface-only work? | PASS | Root and food product boundaries are `NUMERICAL_COUPLING_REDESIGN_REQUIRED`; OBT/leaf interface work remains non-coupled at this stage |
| 7 | Are deferred questions distinguished from blockers? | PASS | TFWT dynamic water balance and soil hydrology are explicit `DEFERRED` records, not hidden implementation tasks |
| 8 | Are prohibited shortcuts recorded as permanent rejections? | PASS | Unreviewed import, root rate scaling, food rate scaling, and dose-driven physics redesign are `REJECTED` with `NEVER` roadmap stages |
| 9 | Can a redesign enter validation or become active directly? | PASS | Registry admission gate forbids direct `REDESIGN_REQUIRED`/`DEFERRED` transitions to `VALIDATED` or `ACTIVE` |
| 10 | Does P7.8A preserve the P7.6D/P7.7B status boundary? | PASS | Active parameters remain zero, calibration and UFOTRI database remain false, and `V3_PHYSICS_READY` remains false |
| 11 | Does the coupling matrix reopen P7.5/P7.5B? | PASS | Matrix flags are false; future root/food changes require a later explicit coupling review |
| 12 | Are runtime owners isolated? | PASS | No plant, soil, exposure, coupling, pipeline, or parameter-runtime source is part of the P7.8A artifact set |

## Findings

The highest-priority scientific work is the OBT formation package and the
layered root representation. The OBT package has high dose-pathway relevance
but requires matched biological data and a state/equation decision. Root
uptake is a direct soil-to-plant bridge and is the first redesign that clearly
requires numerical-coupling redesign. Food OBT/TFWT transfer is a separate
high-dose boundary and cannot be reduced to a time-scaled event fraction.

Leaf stage and OBT mass-basis work can be prepared as smaller contracts, but
they remain redesign-controlled. TFWT water turnover and soil hydrology are
deferred because their required water-balance evidence and ownership
contracts are not complete.

## Review limitations

This review does not validate any equation, parameter, crop response,
hydrologic process, food-transfer rate, or dose coefficient. It does not
replace an independent scientific review of a future V3.1/V3.2/V4 design.
P7.7B synthetic benchmark evidence is treated only as software evidence.

## Executed verification

The registry, matrix, status document, and review artifacts were checked with:

```text
PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/v3/test_p7_8a_physics_redesign_governance.py \
  tests/unit/test_p7_6d_physics_adoption.py \
  tests/v3/test_p7_7a_validation_framework.py \
  tests/v3/test_p7_7b_synthetic_benchmarks.py
```

The executed compatibility scope was 32 tests, and it completed with
`32 passed`. The P7.8A test also checked the branch diff against the
P7.7B baseline and found no runtime-owner or parameter-runtime source change.
`git diff --check` passed.
