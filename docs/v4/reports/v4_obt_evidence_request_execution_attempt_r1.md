# V4 OBT evidence request execution attempt R1

## Result

`STATUS = SEND_ATTEMPT_BLOCKED_BY_UNAUTHORIZED_CHANNEL`

The post-merge main lock for PR #37 was rechecked before execution:

```text
MAIN = 90ed5534758cca55749339b9004b3060362b746a
MERGE_TREE = b58b538336faeab2ea941ae5f8400329f49fe6cb
CLOSURE_HEAD_TREE = b58b538336faeab2ea941ae5f8400329f49fe6cb
MERGE_TREE_DRIFT = FALSE
```

The first authorized execution target remained `MICRO_TOM_2024` using the current verified laboratory route:

```text
RECIPIENT = katayama.kazunari.947@m.kyushu-u.ac.jp
SUBJECT = Request for sample-level tritium plant data from the MicroTom experiment
MESSAGE_SOURCE = docs/v4/gates/obt_evidence_request_messages_r1.md
```

An external send was attempted through the connected Gmail action after the no-drift gate was satisfied. The Gmail action returned an authorization/login denial and no message was sent. The action was not retried and no alternate route was used.

Therefore the authoritative request-state truth remains:

```text
REQUESTS_SENT = FALSE
MICRO_TOM_2024_REQUEST_STATE = REQUEST_PREPARED_NOT_SENT
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

This report records only an execution-channel failure. It is not evidence of scientific insufficiency, provider non-response, delivery failure, or rejection. No request timestamp, sent event, response event, or dataset event exists.

## Next transition

The next authorized transition remains `SEND_ONLY_ON_CURRENTLY_VERIFIED_ROUTE` once an explicitly authorized external mail channel is available. Until a successful send event is recorded with recipient route, channel, exact message identity, and UTC timestamp, the project must remain in `REQUEST_PREPARED_NOT_SENT` state.
