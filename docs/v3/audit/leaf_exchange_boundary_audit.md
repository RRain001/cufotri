# Leaf Exchange Boundary Audit

Audit basis: actual files under `src/cteas_ufotri/leaf_exchange/` and
`git diff main...HEAD -- src`; no status document or commit message was used
as evidence.

## File classification

| File | Actual contents | Classification |
| --- | --- | --- |
| `state.py` | Immutable forcing/state records, units, finite/range validation, inventory properties | A: interface/skeleton |
| `model.py` | Injected kernel coordinator, state update, ledger closure, provenance | A: interface/skeleton; invokes a supplied kernel |
| `parameters.py` | ParameterDatabase lookup, exact-unit checks, provenance, placeholder fail-closed behavior | A: parameter seam |
| `balance.py` | Integrated inventory ledger and closure validation | A: contract/validation |
| `physics.py` | Protocol and fail-closed default, plus `ZeroExchangePhysics` and `SyntheticLinearLeafExchangePhysics` | A plus test-only numerical harness; not pure interface-only |

## Forbidden-physics scan

- No UFOTRI equation, resistance calculation, stomatal conductance, or
  reviewed HTO transfer coefficient is implemented in the V3 leaf package.
- `FrameworkOnlyPhysics` raises before any default arithmetic is selected.
- `SyntheticLinearLeafExchangePhysics` does perform explicit-Euler TFWT
  inventory evolution, first-order TFWT-to-OBT transfer, and OBT decay using
  supplied test parameters. Its source labels it `TEST_ONLY` and explicitly
  says it is not UFOTRI, but it is still numerical physics-shaped behavior.

The literal P5 boundary rule forbids TFWT numerical evolution in an
interface-only phase. Therefore this harness is recorded as:

```text
UFOTRI_PHYSICS_IMPLEMENTED = FALSE
TEST_ONLY_TFWT_NUMERICAL_EVOLUTION = PRESENT
PREMATURE_NUMERICAL_KERNEL = TRUE
```

This finding does not claim UFOTRI formula implementation. It does mean the
accumulated branch cannot be described as containing only interfaces and
validation placeholders.

## Boundary conclusion

The leaf state, model, parameter, and balance files are scaffolding. The
physics file contains a test-only numerical substitute in addition to the
interface. P6 must either explicitly reclassify this harness as a retained
framework test fixture or remove/separate it before claiming a strict
interface-only phase.
