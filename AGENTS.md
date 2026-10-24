# CUFOTRI development agent rules (simplified 2026-10-24)

**Owner decision:** Prioritize implementation of manual-based tritium box/ODE modules and small functional examples over serial literature-audit stages and full-suite repetition. This repo's workflow replaces its previous per-PR obligatory software Full and original-executable independent-science gates **for ordinary manual-based formula development**. Formal historical or empirical claims still require matching evidence.

## Before editing

1. On the authorized Ubuntu host read `/home/lhy/dev/AGENTS.md` and `/home/lhy/dev/README.md` for computer access, proxy, Docker and shared-repo safety. This file governs CUFOTRI-specific day-to-day model scope where old shared policy differs.
2. Fetch remote refs without resetting/cleaning, examine the actual PR HEAD and existing worktrees. Use a **new isolated worktree/branch** from current `origin/main` for new tasks or from the specific PR HEAD when continuing one. Never write directly to `main`, force push or alter another repo's running jobs.
3. Read [STATUS.md](STATUS.md), the relevant physical equation and [DEVELOPMENT.md](docs/DEVELOPMENT.md). Distinguish the frozen **KfK 4605 (1990)** baseline from opt-in **KfK 5194 (1993)** manuals.

## Implement science rather than paperwork

- Change only necessary `src/cteas_ufotri/` physics, parameters and contracts; retain the public `cteas_ufotri` name. Record the original manual equation, units, tissue/ground area and assumptions in a concise module docstring or one relevant document.
- Each new algebraic/box/ODE feature normally needs **a few** tests for representative values, non-negativity where physically justified, analytical/step-size result, conserved activity and interface contract. A source ambiguity becomes an explicit selectable hypothesis or a local TODO; don't falsely call it historical parity.
- Normal development: `python scripts/test.py quick` and affected module tests; use `python scripts/test.py model` for cross-module changes. Don't run 2000+ full cases per audit or tiny edit. Test inside the existing pinned Python 3.11 Ubuntu Docker verification environment when practical.
- Formal release/high-risk cross-module changes: run one exact-SHA Docker Build, Smoke and Full and record actual failures/skips/input hashes. Historical comprehensive GitHub Actions remain available **on-demand**, not automatically on each PR.

## Claims, review and merging

- Software PASS means runnable formulas and tested cases only; **not** numeric equivalence with the original UFOTRI executable, verified field model or regulatory approval. Do not claim original parity without the original executable and same-input comparison.
- A PR asserting actual historical-equivalence/empirical-science outcomes must be visibly labeled `scientific-claim`, `original-parity-claim`, or `empirical-validation-claim`, retain external SB1/SB4/ERA5/private D3 requirements as applicable, and obtain independent non-bot same-SHA scientific approval before a `science-validated` label. Scientific evidence that is absent is **NOT_RUN**.
- GitHub `repository-admission` / `scientific-admission` remain required; a `release-candidate` requires actual exact-SHA Ubuntu Full. Never forge a required status or bypass safeguards for a formal scientific claim.
- Before merging a non-Draft PR, verify current SHA, matching applicable automatic checks, no conflicts, and whether a formal claim/release gate applies. Only then use the existing `merge-verified` event-driven auto-merge workflow; never relabel blocked science PRs simply to merge them.
- Existing P2 PR #159 and P3 PR #152 remain Draft and must not be overwritten or merged as a side effect of repository cleanup.

## History and restricted data

Historical governance tests and past stage reports may be removed from the **current tree**, but remain recoverable from the pre-slim frozen Git tags/commits listed in [HISTORY.md](docs/HISTORY.md). Preserve current equations, meaningful budgets, active input schemas and reference evidence. Don't commit original restricted software, user-provided papers, blind keys, private datasets, tokens, or giant raw model outputs.
