# V3.1 Mass-Basis Contract — Luna R1 Remediation

## Status

```ini
LUNA_R1_REVIEW = HOLD_REMEDIATION_REQUIRED
LUNA_R1_REVIEWED_SHA = e28fd18033984e9fda252aa87b81b399b60ece1e
LUNA_R1_REVIEW_BRANCH_HEAD = d2014f584a3fa6fc373bf32a6477e950ace01b5a
REMEDIATED_CODE_HEAD = cc5aabe0c331664a005ac3ec0579c993e1397757
TECHNICAL_REMEDIATION = PASS
FORMAL_INDEPENDENT_REREVIEW_R2 = PENDING
IMPLEMENTATION_PR_MERGE_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```

## Independent R1 finding

The local GPT-5.6 Luna reviewer reproduced a blocking bypass in
`validate_conversion_proposal()`. The frozen implementation returned
`ConversionStatus.IDENTITY_ONLY` immediately when source and target had the
same mass basis. That return preceded the contract-level
`EVIDENCE_DECLARED`/`conversion_evidence_id` checks.

Consequently a same-basis proposal could silently ignore a declared evidence
state, including a missing supplied evidence object or a conflicting supplied
evidence ID. This was a governance-state defect; no numerical basis conversion
was performed.

The independent review remains preserved on
`codex/v3-1-mass-basis-independent-rereview-r1` at
`d2014f584a3fa6fc373bf32a6477e950ace01b5a` and is not rewritten into PASS.

## Remediation decision

V3.1 has two distinct operations:

- `require_direct_comparison()` performs direct same-basis comparison and does
  not consume cross-basis conversion evidence metadata.
- `validate_conversion_proposal()` governs a proposed basis relation.

For a same-basis call to `validate_conversion_proposal()`, identity is now
admitted only when no `BasisConversionEvidence` object is supplied and neither
contract declares `ConversionStatus.EVIDENCE_DECLARED`.

If a same-basis proposal supplies cross-basis evidence, or either contract
carries `EVIDENCE_DECLARED`, the conversion-proposal gate fails closed and
instructs callers to use direct comparison for a true same-basis comparison.

This avoids inventing a same-basis `BasisConversionEvidence`: that object is
intentionally restricted to different source and target mass bases.

## Regression coverage

New regression module:

`tests/v3_1/test_mass_basis_identity_evidence_gate.py`

It verifies:

1. clean same-basis proposal -> `IDENTITY_ONLY`;
2. source-side `EVIDENCE_DECLARED` cannot bypass the gate;
3. target-side `EVIDENCE_DECLARED` cannot bypass the gate;
4. supplied cross-basis evidence is rejected on a same-basis proposal;
5. even matching declared evidence remains inapplicable to a same-basis
   conversion proposal;
6. `require_direct_comparison()` remains available for direct same-basis
   comparison without consuming conversion evidence state.

The regression module is explicitly included in
`.github/workflows/v3-integration-gate.yml` in addition to normal pytest
discovery.

## Exact code-head verification

Verified code/test/workflow head:

`cc5aabe0c331664a005ac3ec0579c993e1397757`

GitHub Actions:

```text
V3 Remediation CI
run 32916837652
PASS

V3 Protected Integration Gate
run 32916837645
PASS

portable current suite
1000 passed / 1 skipped / 57 deselected / 1 warning

explicit current/frozen/V3.1 invariants
79 passed
```

Compile/import smoke, linear ancestry, and `git diff --check` passed.

The warning remains the pre-existing NumPy/netCDF binary-compatibility warning
in `tests/unit/test_era5_reader.py::test_netcdf_mapping`.

## Isolation

Relative to the Luna R1 reviewed target `e28fd180...`, the code remediation
before governance documentation changed only:

- `src/cteas_ufotri/plant/mass_basis_v3_1/contract.py`;
- `tests/v3_1/test_mass_basis_identity_evidence_gate.py`;
- `.github/workflows/v3-integration-gate.yml`.

No pre-existing V3 solver, state, exposure, parameter, or pipeline source was
modified. No numerical fresh/dry/water/hydrogen conversion was introduced.

```ini
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
P7_5_SEMANTICS_CHANGED = FALSE
P7_5B_SEMANTICS_CHANGED = FALSE
EXISTING_STATE_SERIALIZATION_CHANGED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

## P7.7B local-review note

The Luna R1 macOS review worktree reported one failure in
`test_checked_in_result_registry_matches_a_fresh_execution` for P7.7B. The
V3.1 baseline-to-target diff did not modify that benchmark test, validation
module, or checked-in registry. The same test passes in the Ubuntu GitHub
Actions integration gate, including on remediation head `cc5aabe0...`.

This is therefore recorded as a separate cross-platform reproducibility
technical debt item, not evidence of a V3.1 regression. It does not convert the
synthetic benchmark into physical validation evidence.

## Next gate

After the documentation-complete implementation head itself passes exact-head
CI, create a fresh independent rereview R2 branch from that SHA. The reviewer
must independently re-test the R1 evidence-ID bypass and all previous V3.1
blocking checks.

No merge and no V4 implementation are authorized by this remediation.
