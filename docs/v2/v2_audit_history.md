# V2 audit history

This index preserves the independent evidence chain for the formal V2 research
candidate. Historical reports are immutable evidence; later acceptance does
not rewrite an earlier rejection.

| Stage | Audited commit | Verdict | Decisive issue | Subsequent result |
|---|---|---|---|---|
| Initial V2 | `0075708b35baeb6f8b3b5574d5b735316d959097` | `REJECT_CURRENT_V2_PARAMETERIZATION` | B-01 dry-deposition cross-module activity mismatch | RC1 repaired the activity interface and other HIGH findings |
| RC1 | `aa6256a12a74dc8913773b0df3e8f30a6e7c7f06` | `REJECT_RC1_REMEDIATION` | unequal dry/wet footprints and UFOTRI Eq. (27) vapour-density basis | RC2 repaired both HIGH findings plus benchmark/root/calendar gaps |
| RC2 | `e74f96b01840b00f9d775d60d0e4a37012dbc105` | `ACCEPT_RC2_WITH_MINOR_CORRECTIONS` | no BLOCKER/HIGH; release metadata and provenance LOW findings only | release finalization expands provenance and current-status metadata |

## Evidence files

- Initial V2 independent audit:
  `docs/v2/independent_physics_parameter_audit.md`
- RC1 remediation self-assessment:
  `docs/v2/v2_physics_remediation_rc1_assessment.md`
- RC1 independent re-audit:
  `docs/v2/v2_rc1_independent_reaudit.md`
- RC2 remediation status:
  `docs/v2/v2_physics_remediation_rc2_status.md`
- RC2 independent re-audit:
  `docs/v2/v2_rc2_independent_reaudit.md`

```text
CURRENT_FORMAL_PHYSICS_ACCEPTANCE_BASIS =
RC2_INDEPENDENT_REAUDIT_ACCEPTED_WITH_MINOR_CORRECTIONS
```

The candidate remains HTO-only, research-grade, not site-calibrated, not
regulatory validated, and not complete UFOTRI equivalence.
