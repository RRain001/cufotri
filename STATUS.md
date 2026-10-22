# CUFOTRI status and acceptance boundaries

Snapshot: 2026-10-22. This page is a concise entrypoint, not a replacement for the stage records.

## Current software and scientific claims

| Claim | Status | Evidence authority |
|---|---|---|
| V4 controlled synthetic/replay software development baseline | `COMPLETE` | `docs/v4/adr/ADR-057-v4-development-baseline-rc1.md` |
| H1-H6 manual-based UFOTRI-native atmosphere and downstream functional reconstruction | `COMPLETE` (manual-based scope) | `docs/v4/roadmap/UFOTRI_NATIVE_ATMOSPHERE_RECOVERY_PLAN.md` |
| Complete manual-based **replication** including the unresolved source-limited numerics | `FALSE` | Same recovery roadmap |
| Numerical equivalence to original UFOTRI executable | `NOT_ESTABLISHED` | Source/executable unavailable |
| Empirical / field physical-accuracy validation | `NOT_ESTABLISHED` | External data and independently qualified replay required |
| Site-specific calibration, regulatory qualification or operational production readiness | `NOT_ESTABLISHED` | No such authorization |
| Live CTEAS-Atmos backend integration | `NOT_ESTABLISHED` | Optional future backend, not part of standalone path |

The qualified manual-based reconstruction intentionally preserves boundaries concerning source-limited MUSEMET numerics, certain building-wake/plume-rise branches, washout details, and the original executable's parameter selection. Synthetic and conservation PASS results must not be described as original-executable equivalence or empirical validity.

## Source of truth

1. The **native-atmosphere correction** roadmap overrides older descriptions that placed all atmospheric physics outside this project.
2. The **master replication plan** retains the full A-G historical evidence and gates.
3. Stage-specific ADRs, test results and merge/no-drift checks document individual implementation decisions.
4. `docs/implementation_status.md` is a chronological historic ledger and may contain older status snapshots.

Do not mark a stage or physical claim complete solely because its code compiles or portable unit tests pass.

## GitHub Actions checks

For every scientific source PR:
- **V3 Protected Integration Gate:** all portable tests excluding *declared* external-input and frozen-context markers; frozen/current invariants; existing machine conservation/integration gates.
- **V3 Remediation CI:** historical boundary contracts and evergreen regression checks.
- **Python compatibility:** representative smoke and integration tests on Python 3.12 and 3.13.

The check result must correspond to the PR's exact head and compatible base. After merge, `main` CI must pass on the merged commit as an independent signal. CI failure is a blocker to merging unless its cause and waiver are explicitly documented; missing external evidence must not be represented as a successful external validation.

## External evidence readiness

Fresh public clones and stock GitHub-hosted runners do not include the SB1, SB4, ERA5 acceptance packet or private D3 true-reblinding secret. Their manifest contracts are in `validation/external_input_requirements.py`, and Python test marks distinguish software tests from external-data requirements.

Manual **External evidence audit** supports:
- `audit`: report missing/invalid/available dataset state without pretending to execute external scientific validation;
- `strict`: fail closed on missing/invalid data before running marked external tests.

Before any empirical readiness claim, record authoritative dataset version, license/redistribution decision, raw-byte checksum, observation quality, time alignment, independent calibration/holdout separation and numerical acceptance thresholds. Synthetic fallback must never replace missing observational inputs in strict qualification.

## Cloud-first operating policy

- Work on temporary PR branches, preserve `main`, never resurrect completed Git cleanup workflows.
- Do not commit raw ERA5 data, restricted articles, private keys, blind truth keys or other non-redistributable inputs.
- Keep historical independent-review hashes and `history/unmerged-branch-tips-20261022` Git tag for provenance, not production physics adoption.
- Preserve the Python package import/API name `cteas_ufotri` until a separately planned compatibility migration is approved.
- If a future development stage changes model equations, provide units, source equation anchors, a conservation or physical-invariant test, default-behavior impact, and separate empirical/non-empirical claims.
