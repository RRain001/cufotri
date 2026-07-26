# Monte Carlo classification

Each truth-model/design/noise cell uses 1000 mean-one lognormal replicates and minimum log10 RMSE to the two frozen predictions. No parameter is fitted and no latent pool is supplied.

| design | max delta dex | strong points | CV10 | CV20 | CV30 | minimum samples | status |
|---|---|---|---|---|---|---|---|
| D2_SECOND_PULSE_AFTER_72H | 0.3816 | 6 | 1.000 | 1.000 | 1.000 | 3: 48;72;120 | BASE_CRITERIA_PASS_ROBUSTNESS_NOT_EVALUATED |
| D3_SHORT_STEP_24H | 0.4645 | 7 | 1.000 | 1.000 | 1.000 | 3: 0.2;48;120 | DISCRIMINATING_DESIGN_SUPPORTED |
| D4_LONG_STEP_72H | 0.6748 | 7 | 1.000 | 1.000 | 1.000 | 8: 0.2;0.5;1;3;6;12;48;120 | SYNTHETIC_DESIGN_NOT_ROBUST |
| D5_PULSE_WASHOUT_REEXPOSURE | 0.6829 | 7 | 1.000 | 1.000 | 1.000 | 8: 0.2;0.5;1;3;6;12;24;120 | SYNTHETIC_DESIGN_NOT_ROBUST |
| D1_SECOND_PULSE_AFTER_24H | 0.2423 | 0 | 1.000 | 1.000 | 0.983 | 8: 0.2;0.5;1;48;120;168;336;768 | SYNTHETIC_DESIGN_NOT_ROBUST |
| D0_SINGLE_PULSE_BASELINE | 0.2416 | 0 | 1.000 | 0.999 | 0.978 | 8: 0.2;0.5;1;48;72;120;504;768 | SYNTHETIC_DESIGN_NOT_ROBUST |
