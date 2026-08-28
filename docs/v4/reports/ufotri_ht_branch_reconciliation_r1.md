# UFOTRI HT Branch Reconciliation R1

Stage: `UFOTRI_HT_BRANCH_RECONCILIATION_R1`

Candidate status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

## 1. Result

E1 restores the missing typed gaseous-tritium boundary without implementing downstream HT chemistry. The candidate adds an isolated HT/T2 forcing contract, a soil-deposition handoff that remains chemically HT, an explicit manual benchmark evidence profile, and machine-readable ownership of E2/E3/E4 responsibilities.

## 2. Why the existing HTO interface cannot be reused

The existing V4 atmospheric exchange ADR states that its chemical identity is HTO only. HT, T2, total tritium and unspecified mixtures are forbidden substitutes without a separate reviewed conversion/model contract.

The retained `AtmosphericHTOForcing` likewise uses `air_hto_concentration` and an HTO deposition flux. Reusing that type for gaseous tritium would erase the distinction required by the manual and would make later HT→HTO mass provenance impossible to audit.

E1 therefore adds `AtmosphericHTForcing` as a separate type.

## 3. Manual chemical-state mapping

KfK 4605 describes two environmental chemical forms:

- gaseous tritium, explicitly HT/T2;
- tritiated water, HTO.

For E1 manual fidelity, the accepted gaseous species are explicit `HT` and `T2`. HTO, total tritium, unspecified mixtures and DT fail closed rather than being silently normalized.

The DT boundary is intentionally conservative: it is not a claim that DT cannot physically exist; it records that the reviewed manual evidence used for this replication contract explicitly names HT/T2.

## 4. Atmospheric input contract

Each E1 record contains:

- `[start_utc, end_utc)` with positive duration and explicit UTC;
- species `HT` or `T2`;
- `air_ht_concentration_bq_m3` in `Bq/m3`;
- `surface_ht_deposition_flux_bq_m2_s` in `Bq/m2/s`;
- concentration sampling height;
- spatial support;
- source identity;
- provenance identity;
- source kind.

Only synthetic and replay records are accepted in E1. Real CTEAS-Atmos HT forcing fails closed until E4 freezes a real producer contract.

## 5. Soil-facing boundary

E1 integrates HT surface deposition flux over the record interval to produce `deposited_ht_bq_m2`.

This is only an accounting transformation:

`HT surface flux × interval -> deposited HT areal inventory`

It is **not**:

`HT -> HTO`

The resulting `HTSoilDepositionBoundary` explicitly requires `converted_to_hto_bq_m2=0`.

E2 will own the microbial/soil conversion and its conservation ledger.

## 6. Manual process semantics

The manual states that HT deposition depends on soil type and soil moisture. Once deposited, HT is transformed quickly to HTO through microorganism activity, and only the transformed fraction remains in the soil.

Those statements are frozen in the E1 evidence profile and governance. They are not implemented as kinetics here.

This prevents E1 from collapsing two distinct questions:

1. how much HT reaches the soil boundary;
2. what fraction/rate subsequently becomes HTO.

## 7. Benchmark parameters: evidence, not defaults

The KfK benchmark parameter set exposes:

| Quantity | Manual benchmark |
|---|---:|
| HT dry deposition velocity | `0.05 cm/s` |
| HT dry deposition velocity, SI conversion | `5e-4 m/s` |
| atmospheric HT oxidation | `0.5 %/d = 0.005 d-1` |
| HT soil diffusion coefficient | `5e-2 cm2/s` |
| HT soil diffusion coefficient, SI conversion | `5e-6 m2/s` |
| HTO dry deposition comparison | `1.8 cm/s` |
| HTO soil diffusion comparison | `2e-5 cm2/s` |

E1 exposes these values so later stages can trace evidence. It does not activate any of them as a global or production parameter.

In particular, atmospheric oxidation belongs with real atmospheric transport semantics and is not applied inside the UFOTRI soil contract.

## 8. Qualification strategy

The machine gate verifies:

- explicit HT/T2 species;
- exact units;
- one-hour HT deposition amount;
- one-hour versus four 15-minute partition equivalence;
- no HTO creation;
- separate HT and HTO forcing types/field names;
- real Atmos fail-closed behavior;
- benchmark evidence visibility;
- benchmark non-activation;
- E1/E2/E3/E4 ownership;
- fail-closed invalid species, units, time and numeric inputs.

No empirical data fitting or physical benchmark comparison is performed in E1.

## 9. Source-change boundary

The candidate stage PR is intended to add exactly:

- `src/cteas_ufotri/coupling/ht_v4.py`;
- `scripts/v4/run_ufotri_ht_branch_reconciliation_r1.py`;
- `tests/v4/test_ufotri_ht_branch_reconciliation_r1.py`;
- `docs/v4/adr/ADR-071-ufotri-ht-branch-reconciliation-r1.md`;
- `docs/v4/governance/ufotri_ht_branch_reconciliation_r1.yaml`;
- this report.

No existing HTO source, V2/RC1 source, workflow or roadmap is modified.

## 10. Candidate claim and next stage

Only after exact-head CI, locked-head merge and post-merge no-drift may E1 claim:

`UFOTRI_HT_BRANCH_RECONCILIATION=COMPLETE`

That claim closes only the HT branch contract/manual mapping.

The next stage is:

`UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1`

E1 does not claim HT→HTO conversion, HT-derived HTO re-emission, real atmospheric HT transport/binding, calibration, empirical validation, physical accuracy, production readiness or original-executable equivalence.
