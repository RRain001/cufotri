# UFOTRI OBT compartment conservation and numerical integration R1

## Candidate result

`UFOTRI_OBT_COMPARTMENT_CONSERVATION_NUMERICAL_INTEGRATION_R1 = CANDIDATE_PENDING_EXACT_HEAD_CI`

B2 is a numerical-qualification stage for the B1 OBT state-role reconstruction. It adds no new OBT physics and changes no frozen solver, integrator, operator split, or RC1/V3 default.

## Qualification profiles

Two manual-supported numerical contexts are intentionally kept separate.

### Profile A — Section 2.2.6 daily-average controlled baseline

```text
identifier = SECTION_2_2_6_DAILY_AVERAGE_CONTROLLED_BASELINE
kf = 0.0006 h^-1
kr = 0.003 h^-1
day multiplier = 1.0
night multiplier = 1.0
```

This profile is required to be exactly identical to the existing controlled `ufotri_obt_baseline_parameters()` values. The `1/1` multipliers preserve the daily-average rate and are not claimed to recover the missing UFOTRI day/night split.

### Profile B — Eq. (65)-(66)-derived comparison

Using the manual values:

```text
t15,14 = ln(2)/10 d
M_OBT = 0.1 kg m^-2
M_HTO = 0.4 kg m^-2
water H divisor = 9
organic H divisor = 13
```

Eq. (66) gives:

```text
kf ≈ 0.0119967781 d^-1
   ≈ 0.0004998657552 h^-1
```

Eq. (65) gives:

```text
kr ≈ 0.0693147181 d^-1
   ≈ 0.0028881132523 h^-1
```

For B2 only, this profile is converted to `s^-1` and run through the same frozen `OBTSolver` and V4 integrator. It is a controlled profile-comparison input, not a new default and not a recovered original-executable parameter selection.

## Controlled coupled-chain test

Both profiles use the same synthetic 24 h chain inherited from the previously qualified OBT baseline numerical integration:

- three soil layers with initial HTO inventories `10/20/30 Bq m^-2`;
- initial TFWT `2 Bq m^-2`;
- initial non-exchangeable OBT `0 Bq m^-2`;
- explicit root-water fluxes `(1e-8, 2e-8, 1e-8) m s^-1`;
- selected operator split `PRESERVE_V3_POST_OBT_ROOT_GAIN`;
- tritium decay enabled in the soil solver;
- synthetic provenance only.

For each profile, B2 checks:

- soil-root identity residual;
- plant residual;
- coupled residual;
- soil HTO residual;
- deterministic repeat;
- midpoint serialization/restart equivalence;
- timestep refinement `3600 -> 1800 -> 900 -> 450 s` against a `225 s` reference;
- nonzero OBT formation.

## Independent OBT analytic oracle

The B2 harness does not use the coupled integrator as its own oracle. It separately evaluates the constant-coefficient solution:

```text
S = kf * M_TFWT
M_eq = S / kr
M(t) = M_eq + (M0 - M_eq) exp(-kr t)
```

For a 24 h interval with constant `M_TFWT = 2 Bq m^-2`, `M0 = 0`:

### Section 2.2.6 profile

```text
M_eq = 0.4 Bq m^-2
M(24 h) ≈ 0.0277876416755 Bq m^-2
integrated formation = 0.0288 Bq m^-2
integrated other loss ≈ 0.00101235832448 Bq m^-2
```

### Eq. (65)-(66) profile

```text
M_eq = 0.346153846154 Bq m^-2
M(24 h) ≈ 0.0231808875450 Bq m^-2
integrated formation ≈ 0.0239935562502 Bq m^-2
integrated other loss ≈ 0.000812668705201 Bq m^-2
```

The machine gate requires `OBTSolver` to reproduce the independently calculated state and ledger within numerical tolerance for both profiles.

## Zero-TFWT limit

B2 also isolates the loss branch by setting TFWT inventory to zero and initial OBT to `1 Bq m^-2` for 24 h. The expected solution is:

```text
M(t) = exp(-kr t)
```

and reported formation must be exactly zero.

## Reduced RC1/V3 compatibility

B2 explicitly constructs a reference chain using `ufotri_obt_baseline_parameters()` and compares its numerical state against the Section-2.2.6 qualification profile. The two must have:

- identical `OBTParameters`;
- exactly zero numerical delta for soil HTO, TFWT, OBT, total plant inventory and all recorded residuals.

This gate prevents B2 from silently changing the frozen controlled baseline while adding the Eq. (65)-(66) comparison.

## Profile-difference interpretation

B1 already established that Section 2.2.6 and Eq. (65)-(66) are not numerically identical. B2 therefore requires the resulting controlled OBT state difference to be nonzero.

This difference is interpreted only as:

`MANUAL_RATE_PROFILE_NUMERICAL_CONSEQUENCE`

It is not interpreted as:

- uncertainty distribution;
- model error estimate;
- evidence that one profile is physically superior;
- evidence of which values the unavailable original executable selected.

## State-role boundary

B1 remains authoritative:

```text
free plant HTO + exchangeable OBT role -> TFWTState
non-exchangeable OBT                  -> OBTState
separate exchangeable OBT inventory  -> FALSE
```

B2 adds no third plant activity pool and performs no exchangeable-OBT double counting.

## Candidate source changes

New files only:

- `scripts/v4/run_ufotri_obt_compartment_conservation_numerical_integration_r1.py`;
- `tests/v4/test_ufotri_obt_compartment_conservation_numerical_integration_r1.py`;
- `docs/v4/adr/ADR-063-ufotri-obt-compartment-conservation-numerical-integration-r1.md`;
- `docs/v4/governance/ufotri_obt_compartment_conservation_numerical_integration_r1.yaml`;
- this report.

No existing production/frozen source file is modified.

## Hard boundaries

A passing B2 result does not make any of the following true:

```text
CALIBRATION = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
PRODUCTION_PARAMETER_ACTIVATION = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
GENERIC_MULTI_POOL_OBT = FALSE
ORIGINAL_EXECUTABLE_PARAMETER_SELECTION_RECOVERED = FALSE
NORMALIZED_DAY_NIGHT_MULTIPLIER_RECOVERED = FALSE
FROZEN_V3_RC1_DEFAULT_CHANGED = FALSE
```

## Completion decision

This report remains a candidate until exact-head Remediation and Protected CI pass and the PR is merged with a verified no-drift audit.

If those gates pass, B2 closes the recoverable Phase B OBT fidelity scope and the next authorized stage is:

`UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1`.
