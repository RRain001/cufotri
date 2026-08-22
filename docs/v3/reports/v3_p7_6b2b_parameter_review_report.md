# V3-P7.6B-2B parameter applicability review report

## Matrix result

The one-to-one matrix still covers all 76 P7.6A inventory records. The
targeted recovery changes one record from unresolved to a direct applicability
match and leaves all other model-parameter reviews fail-closed:

```text
DIRECT_MATCH       1
PARTIAL_MATCH      0
TRANSFER_REQUIRED  0
UNKNOWN           25
NOT_APPLICABLE    50
```

`soil.tritium_half_life` is mapped to the universal H-3 radioactive-decay
property and the existing V3 decay equation. The matrix explicitly excludes
soil transport and water-content interpretation from that mapping.

## Tier-1 review ledger

| parameter group | matrix disposition | candidate disposition | review boundary |
| --- | --- | --- | --- |
| `root.k_root` | `UNKNOWN` | deferred | no recovered `m s^-1` effective transfer velocity for the current flux equation |
| `obt.kf` | `UNKNOWN` | deferred | no complete current first-order equation plus compatible, bounded source coefficient |
| `obt.kr` | `UNKNOWN` | deferred | loss timescale evidence lacks a closed V3 OBT definition/equation mapping |
| `leaf.r_a`, `leaf.r_b`, `leaf.r_c` | `UNKNOWN` | deferred | no closed resistance-chain mapping with environmental and crop scope |
| `soil.transport_flux` | `UNKNOWN` | deferred | signed interface flux is not a transport coefficient |
| `soil.layer_depth`, `soil.water_content` | `UNKNOWN` | deferred | geometry/state inputs are not promoted to empirical evidence |
| `soil.tritium_half_life` | `DIRECT_MATCH` | `VALIDATION_CANDIDATE` | radioactive decay only; explicit `d` to `s` conversion |

The reviewed OBT literature is retained as a screening rationale in the
evidence-recovery report, not silently promoted to V3 coefficients. In
particular, a TFWT-to-OBT ratio or a standalone loss half-life cannot satisfy
the current candidate equation gate.

## Review integrity

Every matrix row retains a source context, model component, equation-match
token, unit-match token, uncertainty flag, review notes, and required action.
The candidate record links the deterministic applicability ID and the matrix
candidate flag. No matrix row starts calibration or changes a solver input.
