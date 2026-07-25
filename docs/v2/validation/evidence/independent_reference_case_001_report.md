# Independent reference case 001

`REFERENCE_MODEL_STATUS = PASS_INDEPENDENT_REFERENCE_CASE_001`

The formal V2 candidate and a separately coded reference model parsed the same
frozen case manifest. The reference implementation imports no
`cteas_ufotri` modules and does not read formal model output. Its code,
equations, output, and provenance are under
`validation/reference_models/independent_pathway_reference/`.

## Scope

The bounded six-hour case independently implements:

- rural Gaussian centerline ground concentration with ground reflection;
- competing dry and wet exponential source depletion;
- separate dry/wet surface activity allocation;
- a one-box soil HTO inventory;
- fixed-conductance leaf HTO uptake;
- first-order TFWT and OBT boxes;
- inhalation/skin dose; and
- a separately unit-tested non-zero HTO/OBT ingestion calculation.

The comparison deliberately disables re-emission, root uptake, edible
allocation, animal pathways, and complex meteorology-responsive leaf
resistance. Passing this case is not evidence for those omitted processes.

## Preregistered thresholds and results

| Observable | Metric | Threshold | Result |
|---|---|---:|---:|
| air HTO | normalized RMSE | <= 1e-6 | 1.795e-15 |
| dry depletion | normalized RMSE | <= 1e-6 | 2.488e-13 |
| wet depletion | normalized RMSE | <= 1e-6 | 2.488e-13 |
| soil HTO | normalized RMSE | <= 1% | 1.516e-13 |
| plant TFWT | normalized RMSE | <= 1% | 1.373e-15 |
| plant OBT | normalized RMSE | <= 1% | 1.782e-15 |
| inhalation dose | final relative error | <= 5% | 4.021e-16 |
| total effective dose | final relative error | <= 5% | 1.340e-16 |

The independent reference activity residual is at most
`5.823e-10 Bq m-2`, below the preregistered `1e-8 Bq m-2` threshold.

Execution:

```bash
.venv/bin/python \
  validation/reference_models/independent_pathway_reference/run_reference.py \
  --case validation/cases/independent_reference_case_001.yaml \
  --output validation/reference_models/independent_pathway_reference/reference_output.csv \
  --provenance validation/reference_models/independent_pathway_reference/reference_provenance.json

.venv/bin/python scripts/run_v2_validation_case.py \
  --case validation/cases/independent_reference_case_001.yaml \
  --output validation/reports/independent_reference_case_001
```

The result is strong agreement for the declared simplified equations only. It
is independent numerical evidence but not experimental or field validation.
