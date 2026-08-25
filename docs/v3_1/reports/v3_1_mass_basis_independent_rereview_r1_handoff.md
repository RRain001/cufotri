# V3.1 Mass-Basis Contract — Independent Rereview R1 Handoff

## Frozen target

```text
IMPLEMENTATION_PR = 3
PRIOR_REVIEW_PR = 4
FROZEN_TARGET = e28fd18033984e9fda252aa87b81b399b60ece1e
BASE_MAIN = d24aa03b00dcb586a2d93e678f42cb7853b7c078
REREVIEW_BRANCH = codex/v3-1-mass-basis-independent-rereview-r1
```

This is a new rereview after the first reviewer-independent review found a
blocking Python/JSON-Schema mismatch. The failed review is retained as evidence
and is not rewritten into a PASS.

## Prior blocker

GitHub Copilot code review `PRR_kwDOTiMPdM8AAAABKupe9g` reviewed the prior
frozen target `4664e4c09f20bbfd48c5d1c750efafeb6d6e9643` and recommended changes.
The blocking issue was that JSON Schema `minLength: 1` admitted whitespace-only
strings that Python `_require_text()` strips and rejects.

The affected serialized text boundary includes `subject_id`, string tissue and
area identifiers, provenance strings, and declared conversion evidence IDs.

## Remediation

The schema now requires at least one non-whitespace character for every
serialized text field governed by `_require_text()`. New negative tests exercise
whitespace-only subject IDs, provenance fields, tissue/area identifiers, and
evidence IDs. The whitespace test module is included explicitly in the
protected integration gate.

Schema-remediation code head:

`6926ebf405b976ef58c66e17f6bfc0aacca551dd`

Evidence:

```text
V3_REMEDIATION_CI_32809809259 = PASS
V3_PROTECTED_INTEGRATION_GATE_32809809310 = PASS
PORTABLE_SUITE = 994 passed / 1 skipped / 57 deselected
EXPLICIT_INVARIANTS = 73 passed
```

The final documentation-complete target `e28fd180...` also passed exact-head
V3 Remediation CI `32810070891` and V3 Protected Integration Gate `32810070923`.

## Rereview checks

The reviewer should treat every item below as blocking unless explicitly stated
otherwise:

1. Reproduce the prior whitespace finding and confirm the new schema rejects it.
2. Check all `_require_text()`-governed serialized MassBasisContract fields for
   schema/Python parity, not only the originally surfaced examples.
3. Confirm no numerical fresh/dry/water/hydrogen conversion exists.
4. Confirm evidence uses explicit source/target pair records and rejects
   self-pairs, duplicate pair IDs, and measurement reuse across pairs.
5. Confirm evidence is bound to matching tissue scope and area basis.
6. Confirm declared conversion evidence IDs cannot conflict with supplied
   evidence records.
7. Confirm `BasisConversionEvidence`/`PairedMeasurement` persistence remains
   explicitly out of V3.1 schema scope rather than silently diverging.
8. Confirm frozen V3 runtime paths remain unchanged and do not import V3.1.
9. Confirm P7.8B-2 scope remains intact: no V4 physics, calibration, parameter
   activation, or physical-validation claim.

## Required verdict

A PASS may be recorded only against exact target
`e28fd18033984e9fda252aa87b81b399b60ece1e` and only if no blocking finding
remains. The prior implementation-author rereview is supporting evidence, not
an independent verdict.

```ini
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
V4_IMPLEMENTATION_AUTHORIZED = FALSE
```
