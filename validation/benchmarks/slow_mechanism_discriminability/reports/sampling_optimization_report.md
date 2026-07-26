# Sampling optimization

The deterministic greedy search starts at maximum H2-H3 log10 separation, uses only the 14 preregistered candidate times, and selects 3-8 samples by worst-noise accuracy. Tie breaks choose the earlier time.

| design | status | count | hours |
|---|---|---|---|
| D0_SINGLE_PULSE_BASELINE | NO_3_TO_8_POINT_SET_MEETS_FROZEN_CRITERIA | 8 | 0.2;0.5;1;48;72;120;504;768 |
| D1_SECOND_PULSE_AFTER_24H | NO_3_TO_8_POINT_SET_MEETS_FROZEN_CRITERIA | 8 | 0.2;0.5;1;48;120;168;336;768 |
| D2_SECOND_PULSE_AFTER_72H | MINIMUM_SAMPLING_CRITERIA_PASS | 3 | 48;72;120 |
| D3_SHORT_STEP_24H | MINIMUM_SAMPLING_CRITERIA_PASS | 3 | 0.2;48;120 |
| D4_LONG_STEP_72H | MINIMUM_SAMPLING_CRITERIA_PASS | 8 | 0.2;0.5;1;3;6;12;48;120 |
| D5_PULSE_WASHOUT_REEXPOSURE | NO_3_TO_8_POINT_SET_MEETS_FROZEN_CRITERIA | 8 | 0.2;0.5;1;3;6;12;24;120 |
