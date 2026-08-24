# V3 P7.7A Baseline Benchmark Plan

This is a definition plan, not an execution report. The five cases are
declared in `configs/v3/validation/p7_7a_baseline_benchmarks.yaml`. Their
numbers are explicit software-fixture inputs and do not represent UFOTRI
parameter values or empirical observations.

| Case | Interface under test | Independent reference contract | Deliberate exclusion |
| --- | --- | --- | --- |
| `v3-p7-7a-radioactive-decay` | Inventory time evolution | Analytic decay expression | Half-life truth or soil retention validation |
| `v3-p7-7a-leaf-exchange` | Explicit leaf flux into TFWT | Flux integral | Leaf resistance parameter validation |
| `v3-p7-7a-tfwt-obt` | TFWT to OBT state propagation | Analytic linear storage expression | `kf`/`kr` physical validity |
| `v3-p7-7a-soil-root` | Soil inventory to root flux | Explicit coefficient flux expression | Root-coefficient physical validity and redesign |
| `v3-p7-7a-end-to-end-pathway` | Atmosphere → leaf → TFWT → OBT → soil → root → food → dose state wiring | Independent synthetic state/endpoint table contract | Full UFOTRI validation, calibration, and regulatory/dose claims |

## Future execution contract

When a separately authorized harness executes a case, it must:

1. pass the case through `can_enter_validation()`;
2. obtain model outputs from the caller-owned solver or pathway interface;
3. obtain reference values from the declared independent reference method or
   artifact, never by reusing production arithmetic;
4. compute a named metric with aligned units and time basis;
5. emit a `ValidationResult` with an execution hash, solver version,
   uncertainty convention, and immutable parameter snapshot;
6. retain the result as software/semantic evidence unless a later stage
   separately admits physical evidence.

The end-to-end case names the required checks for state propagation,
conservation, and restart equivalence in its acceptance criteria. P7.7A does
not implement those pathway calculations or claim that they pass.
