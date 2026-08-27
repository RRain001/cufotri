# V4 OBT evidence acquisition execution R1 — exact-head certification report

## Result

`STATUS = PASS_EXECUTION_CONTROL_EXACT_HEAD_AWAITING_CLOSURE_GATE`

The PR #36 preregistration merge has been independently rechecked and is no-drift. The execution stage is therefore authorized, but only for external request execution and metadata-only intake.

The execution control plane deliberately records no external send. It freezes the execution event schema, audits current versus historical contact routes and prepares provider-specific messages from the already-frozen request package. It changes no production source, solver equation, runtime state, parameter value, calibration logic, observation operator, holdout rule or identifiability rule.

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

PR #36 closure Protected recorded `1303 passed, 1 skipped, 57 deselected` in the portable suite and `365 passed` in the frozen/current-boundary suite, while sensitivity, root operator split, soil-root-TFWT-OBT integration, replay orchestration and food-intake-dose endpoint machine gates remained PASS.

## First execution-control exact head

The valid first exact head is:

```text
FIRST_EXACT_HEAD = 15f3e4be9e03cf9ff49fe1a1fe1b0a516de628a5
FIRST_PROTECTED_RUN = 33045107295_SUCCESS
FIRST_REMEDIATION_RUN = 33045107285_SUCCESS
FIRST_CHECKOUT_MERGE_REF = d20da58ac9721d5703ade8bcc5807453596466c7
PORTABLE_SUITE = PASS_1311_WITH_1_SKIP_57_DESELECTED
FROZEN_BOUNDARY_SUITE = PASS_373
SENSITIVITY_SCREENING = PASS_SOFTWARE_SCREENING
ROOT_OPERATOR_SPLIT = PASS_SELECTION
SOIL_ROOT_TFWT_OBT_INTEGRATION = PASS_INTEGRATION
REPLAY_ORCHESTRATION = PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION
FOOD_INTAKE_DOSE_ENDPOINT = PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION
```

An earlier head, `f92b2e962acbc4c6cedfe4a1bd872b53cd084f9c`, is explicitly superseded and non-certifying. Its Remediation run succeeded, while Protected run `33044867209` failed exactly one newly added governance test because the assertion expected a more specific sentence wording than the report used. The portable result was `1310 passed, 1 failed, 1 skipped, 57 deselected`. The repair changed only that test assertion (`+1/-1` in one file). No production code, scientific model, parameter, numerical coupling or pre-existing regression failed.

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
OBT_MULTI_POOL_IMPLEMENTATION_AUTHORIZED = FALSE
OBT_PARAMETER_ACTIVATION_AUTHORIZED = FALSE
CURRENT_KF_KR_CALIBRATION_AUTHORIZED = FALSE
LEAF_R5_AUTHORIZED = FALSE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED = FALSE
FULL_HYDROLOGY_AUTHORIZED = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
```

The request text remains frozen in `docs/v4/gates/obt_evidence_request_messages_r1.md`. Its presence is not a send event and it is not modified by this closure.

## Raw-data boundary

Any future received file must remain outside Git, preserve original bytes, receive SHA-256 before content inspection and enter the repository only through metadata-only manifests. Tracked raw quantitative plant-tritium values remain forbidden. A later Layer-B dataset-shape amendment remains mandatory before any quantitative fitting or holdout inspection.

## Closure boundary

The certified first-head condition is satisfied. This governance closure still requires its own exact-head Protected + Remediation success and a no-drift `expected_head_sha` merge before PR #37 is treated as closed on `main`.

The closure does not modify the request message artifact, Protected workflow, preregistration contract, production source, solver, runtime, parameter layer or numerical coupling. No request is sent during closure.

After closure dual CI plus no-drift merge, request execution may proceed only through a currently verified route. A send does not authorize Option-B implementation, fitting, activation, current `kf/kr` calibration, Leaf R5, root `q_w`, full hydrology or real CTEAS-Atmos binding.
