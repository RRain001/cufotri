# V3 Physics Roadmap

Status: `P5.6_RECONCILED_AND_FROZEN`

P5.6 is a documentation and architecture-state stage. It does not import
validated values, implement UFOTRI equations, modify formal configuration, or
open the V3 physics path.

## Ordered work packages

```text
P5.6 Architecture reconciliation
        |
        v
P6.1 UFOTRI parameter database import
        |
        v
P6.2 Leaf exchange physics implementation
        |
        v
P6.3 Root uptake + multilayer soil coupling
        |
        v
P6.4 Food chain
        |
        v
P6.5 Dose assessment
        |
        v
P7 CTEAS-Atmos dynamic coupling
```

## Entry and exit gates

| Stage | Required entry evidence | Required exit evidence |
|---|---|---|
| P5.6 | Repository reality audit complete; no active validated UFOTRI DB | Unified terminology, protected-path check, and independent review |
| P6.1 | Reviewed source mapping and parameter schema decision | Non-placeholder values with citation, uncertainty, applicability, lifecycle, and independent review |
| P6.2 | P6.1 accepted; leaf equations frozen | UFOTRI leaf-exchange implementation plus dimensional, conservation, and independent benchmark evidence |
| P6.3 | Leaf boundary accepted; soil/root contracts frozen | Reviewed root uptake and multilayer coupling with conservation and benchmark evidence |
| P6.4 | Plant/soil activity contracts accepted | Reviewed transfer pathway and independent food-chain benchmark evidence |
| P6.5 | Food-chain pathway accepted; regulatory basis selected | Dose coefficients, age-group assumptions, committed-dose method, and independent review |
| P7 | P6 pathway evidence accepted | Explicit atmospheric-to-plant dynamic coupling and separate system-level validation |

No stage may promote a synthetic kernel, placeholder parameter, or passing
architecture test into validated UFOTRI physics. Every stage must preserve the
V2 compatibility path and fail closed when its reviewed physics inputs are
missing.

## Current disposition

```yaml
P5_STATUS: COMPLETE_WITH_RECLASSIFICATION
UFOTRI_PHYSICS_IMPLEMENTED: false
UFOTRI_PARAMETER_IMPORTED: false
FRAMEWORK_READY: true
PHYSICS_READY: false
NEXT_PHASE: UFOTRI_PARAMETER_AND_PHYSICS_IMPLEMENTATION
```
