# V4 OBT evidence acquisition execution R1 — first-head report

## Result

`STATUS = REQUEST_EXECUTION_READY_CONTACT_ROUTES_AUDITED_NOT_SENT`

The PR #36 preregistration merge has been independently rechecked and is no-drift. The execution stage is therefore authorized, but only for external request execution and metadata-only intake.

This first execution head deliberately records no external send. It freezes the execution event schema, audits current versus historical contact routes and prepares provider-specific messages from the already-frozen request package. It changes no production source, solver equation, runtime state, parameter value, calibration logic, observation operator, holdout rule or identifiability rule.

## Authorization anchor

```text
SOURCE_PR = 36
SOURCE_MERGE = ca77d8abf4d7babe2669aa829f028e4ac45f653d
SOURCE_PARENT1 = d28695a13eae1fe4a7afb55a7a8a179d366de44c
SOURCE_PARENT2 = acfd0f087b3a05d414a55a1d3a480eee8223a83b
PR_HEAD_TREE = 2be97abe215c365bd496123719ac99863bccb210
MERGE_TREE = 2be97abe215c365bd496123719ac99863bccb210
HEAD_TO_MERGE_FILES = []
MAIN = ca77d8abf4d7babe2669aa829f028e4ac45f653d
MERGE_TREE_DRIFT = FALSE
```

The closure exact head had Protected and Remediation success. Protected recorded `1303 passed, 1 skipped, 57 deselected` in the portable suite and `365 passed` in the frozen/current-boundary suite, while sensitivity, root operator split, soil-root-TFWT-OBT integration, replay orchestration and food-intake-dose endpoint machine gates remained PASS.

## Contact-route result

- VATO: current ASNR VATO research route and contact name are public, but former `@irsn.fr` direct addresses are treated as historical until current delivery is reverified. `SEND_ELIGIBLE_NOW=FALSE`.
- MicroTom: current Kyushu laboratory route is independently supported; `katayama.kazunari.947@m.kyushu-u.ac.jp` is a current direct laboratory contact. `SEND_ELIGIBLE_NOW=TRUE`, but no message has yet been sent.
- Renard 2017: historical corresponding route `hugo.renard@irsn.fr` is documented, but no current direct corresponding route has yet been independently reverified. `SEND_ELIGIBLE_NOW=FALSE`.
- supporting soybean/nocturnal evidence: not audited in this first execution head.

This distinction prevents a historical contact address from being silently promoted to a current execution fact.

## Request-state truth

```text
REQUESTS_SENT = FALSE
RESPONSES_RECEIVED = FALSE
RAW_PACKET_RECEIVED = FALSE
QUANTITATIVE_MODEL_FIT_INSPECTION = FALSE
HOLDOUT_VALUES_INSPECTED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
```

The request text is prepared in `docs/v4/gates/obt_evidence_request_messages_r1.md`. Its presence is not a send event.

## Raw-data boundary

Any future received file must remain outside Git, preserve original bytes, receive SHA-256 before content inspection and enter the repository only through metadata-only manifests. Tracked raw quantitative plant-tritium values remain forbidden. A later Layer-B dataset-shape amendment remains mandatory before any quantitative fitting or holdout inspection.

## First-head exit rule

This execution-control head must pass Protected + Remediation CI before any request is recorded as sent. After dual CI, only a currently verified contact route may be used. A send does not authorize Option-B implementation, fitting, activation, current `kf/kr` calibration, Leaf R5, root `q_w`, full hydrology or real CTEAS-Atmos binding.
