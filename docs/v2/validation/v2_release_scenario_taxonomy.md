# V2 release-scenario taxonomy

```text
LIMITATION = M_RELEASE_DURATION
SCENARIO_TAXONOMY_STATUS = READY
SCHEMA = validation/schemas/release_scenario.schema.json
```

Every validation case must declare exactly these fields:

```text
release_scenario_type
release_start
release_end
source_rate_basis
post_release_duration
```

| Type | Meaning | Required source-rate interpretation |
|---|---|---|
| `CONTINUOUS_ROUTINE` | routine release continuing through the modelled interval | constant or time-resolved rate with an explicit averaging basis |
| `FINITE_ROUTINE_WINDOW` | routine operation bounded by explicit start/end | rate is zero outside the declared window |
| `ACCIDENT_PULSE` | short release represented as an integrated pulse or bounded short window | total Bq and pulse-to-rate conversion must be explicit |
| `ACCIDENT_TIME_SERIES` | accident source varying in time | timestamped Bq s-1 series, interpolation and interval semantics explicit |
| `POST_RELEASE_FOLLOWUP` | environmental evolution after a preceding release | preceding release provenance and zero/new source behavior explicit |

`release_start` and `release_end` are timezone-aware ISO-8601 timestamps with
end later than start. `source_rate_basis` states whether input is an
instantaneous rate, interval mean, integrated pulse conversion, or timestamped
series. `post_release_duration` is an explicit ISO-8601 duration and may be
`PT0H`; omission is not interpreted as zero.

The case runner validates this contract before model execution. This removes
ambiguous duration semantics but does not establish the correct duration for a
specific facility or accident; that requires independently supplied site/event
evidence.
