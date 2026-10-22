# CUFOTRI agent and research-development rules

## Scientific correctness

1. Source editions are version-scoped: repository-root `ufotri_manual.md` is **KfK 4605 (1990)** for the frozen baseline, while official **KfK 5194 (1993)** is the normative manual for opt-in UFOTRI 4.0 reconstruction ([ADR-085](docs/v4/adr/ADR-085-ufotri-1993-manual-first-reconstruction-authority.md)). Do not require unavailable original code to start reviewed manual-first physics; do not claim original-executable numerical equivalence without original UFOTRI source/executable comparison.
2. Every equation change must cite its source equation, use SI units, pass dimensional checks, and include conservation or appropriate numerical regression checks.
3. Keep case-specific values in YAML or versioned data contracts, never hidden in numerical code.
4. The frozen V4 RC1 baseline and opt-in manual-fidelity paths must remain distinguishable. Do not silently change established defaults, claim empirical validation based on synthetic tests, or interpret an old stage gate as a current full-model approval.
5. Read [STATUS.md](STATUS.md) and both `docs/v4/roadmap/` authority documents before scheduling new H-stage development. The native-atmosphere recovery correction supersedes the older assumption that CTEAS-Atmos is mandatory for UFOTRI-native standalone reproduction.

## GitHub-first execution

6. Use a short-lived GitHub branch and PR for code, workflow and documentation changes. No persistent local worktree is required. Never push directly to `main`; do not rewrite main/tags or resurrect historical cleanup branches.
7. Check the exact PR head and GitHub Actions run statuses before merging. The Protected Integration Gate and Remediation CI remain required scientific checks. Record any skipped/deselected test groups and explicitly distinguish software qualification from external evidence.
8. GitHub-hosted runners are ephemeral. Raw data, credentials, private D3 keys, unlicensed literature and generated simulation outputs must not be committed or logged. Sources are read-only. Follow input checksum and licensing contracts under `validation/`.
9. Missing external inputs: synthetic deterministic defaults may be used **only for documented synthetic development/examples**, not as substitutes for experiments in formal scientific acceptance. Strict external gates must fail closed; never weaken marks or tests just to obtain a green run.
10. Keep Python package/module entrypoint name `cteas_ufotri` until an explicit API migration is approved. Run the Python 3.11 locked-dependency regression **inside the Docker verification image** when changing public interfaces; do not introduce another Python minor version or host-only scientific CI without a dedicated compatibility decision.
11. Prefer small reviewable PRs. Update `STATUS.md` only when top-level claims or acceptance boundaries actually change; add stage-specific evidence/ADRs for physics changes rather than endlessly appending status snapshots to the root README.
12. For interrupted work, report exact commit, PR, successful and failed commands, remaining blockers and next reproducible step. Do not claim completion before the appropriate exact-head CI and merge/no-drift checks.
13. See `docs/ci/DOCKER_WORKFLOW.md`: GitHub Actions must build/run scientific tests in the Python 3.11 `verification` stage; the separate non-root `runtime` stage contains no Git history, raw data, or pytest/uv tooling. Never publish the verification image; never weaken externally marked strict tests.
