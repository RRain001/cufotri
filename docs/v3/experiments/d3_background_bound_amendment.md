# D3 post-exposure background-bound amendment

```text
AMENDMENT_ID = D3_BACKGROUND_BOUND_CORRECTION_V2
ORIGINAL_ASSUMPTION_SET = D3_PROSPECTIVE_ASSUMPTIONS_V1
CORRECTED_ASSUMPTION_SET = D3_PROSPECTIVE_ASSUMPTIONS_V2
ORIGINAL_CLASSIFICATION_COMMIT =
bf4ff0880b9b064e48dd8a1f02ef51f14c5b3c0a
REAL_EXTERNAL_EVIDENCE = FALSE
EMPIRICAL_VALIDATION_CLAIM = FALSE
```

## Reason

The source specification defines the desired post-exposure chamber
background as less than or equal to 0.5% of the exposure setpoint and the
maximum acceptable instantaneous background as 1%. V1 encoded 0.5% as an
exact mean maintained throughout the 120 h follow-up. This converted an upper
bound into a fixed forcing value and caused continuing HTO re-uptake to mask
the slow-mechanism difference.

The already unblinded V1 run remains immutable in Git history and retains its
failed positive-control verdict. V2 does not change the H2/H3 parameters,
classification times, 0.15/0.50 dex thresholds, biological-replicate count or
random seeds.

## Prospective correction

V2 freezes a synthetic operational background mean of 0.25% of the exposure
setpoint while retaining:

- target maximum mean: 0.5%;
- maximum acceptable instantaneous background: 1%;
- positive, measurable synthetic fluctuation;
- a separate strict-zero sensitivity scenario.

The 0.25% value is a project planning assumption, not a literature fact or a
claim about an existing chamber. It provides operational margin below the
specified upper bound. A real experiment must measure its own background and
must not substitute this synthetic value.

## Pre-rerun boundary

This amendment must be committed before V2 forcing or blinded datasets are
generated. A new classification protocol must bind the committed V2
assumptions hash. Classification must still occur before the local truth key
is opened.

The rerun remains synthetic, cannot enter the trusted registry, cannot select
formal V3 physics and cannot unblock:

```text
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```
