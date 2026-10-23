# CUFOTRI

Open-source, research-oriented reconstruction of tritium transport and environmental pathways from the available UFOTRI/KfK 4605 manual. The Python package and CLI retain the historical name `cteas_ufotri`; this is deliberate API compatibility, not a second repository.

**The codebase is a manual-based functional reconstruction, not a numerically verified clone of the original UFOTRI executable.** The original executable/source and full original regression fixtures are not available. Reproducible software tests do not constitute site, regulatory, empirical, or physical-accuracy validation.

## Current status

See [STATUS.md](STATUS.md) for the current claim boundary and CI requirements, and [the scientific documentation index](docs/INDEX.md) to navigate versioned methods, evidence and historical ADRs. Detailed traceability and stage evidence remain in:

- [UFOTRI replication master plan](docs/v4/roadmap/UFOTRI_REPLICATION_MASTER_PLAN.md)
- [Native atmosphere recovery correction](docs/v4/roadmap/UFOTRI_NATIVE_ATMOSPHERE_RECOVERY_PLAN.md), which supersedes older atmospheric status descriptions
- [V4 development baseline RC1](docs/v4/adr/ADR-057-v4-development-baseline-rc1.md)
- [H6 final manual-reconstruction gate R2](docs/v4/adr/ADR-084-ufotri-manual-based-functional-reconstruction-final-gate-r2.md)
- [Historic V1/V2 README](docs/reference/legacy-readme-v2-20261022.md)

The model includes the UFOTRI-native HTO/HT atmospheric route, deposition and soil HT conversion, water/HTO transport, plant TFWT/OBT, re-emission, food-chain and public-exposure interfaces. The frozen V4 RC1 baseline is retained alongside opt-in manual-fidelity paths. CTEAS-Atmos remains an optional future external backend.

## Repository map

| Path | Responsibility |
|---|---|
| `src/cteas_ufotri/` | Versioned research solvers, physical interfaces, and coupling |
| `configs/` | Case inputs and configuration defaults |
| `schemas/` | Machine-readable scientific input/output contracts |
| `tests/` | Unit, integration, numerical-conservation and governance checks |
| `validation/` | Independent benchmark protocols, data provenance, adapters and external evidence contracts |
| `scripts/v4/` | Auditable V4 stage runners and machine validation gates |
| `docs/v4/` | ADRs, status, source-fidelity decisions and stage evidence |
| `.github/workflows/` | Required PR admission and scoped integration/Python checks; dispatchable Docker, remediation and external scientific reproducibility jobs |

The large historical `docs/implementation_status.md` remains a legacy stage ledger, **not** the current top-level release authority. Its dated stage entries should not override the two V4 roadmaps or [STATUS.md](STATUS.md).

## Ubuntu-first development and GitHub PR delivery

Develop in a dedicated, clean Ubuntu task worktree and a short-lived GitHub PR branch. The managed Ubuntu Docker environment runs build, smoke, full software suite and permitted science evidence at the **exact PR HEAD**. GitHub automatically runs mandatory admission, V3 Protected Integration Gate and Python 3.11 compatibility checks on applicable PR changes. Docker dual-stage and Remediation jobs remain available via agent-driven `workflow_dispatch`; independent science acceptance is separate.

The main workflows are:

- **V3 Protected Integration Gate** — comprehensive portable tests, current/frozen invariants and V4 machine gates;
- **V3 Remediation CI** — dispatchable historical-boundary and evergreen regression checks when applicable;
- **Python 3.11 regression** — one Docker-contained interpreter for installation, imports and representative scientific tests;
- **Docker dual-stage verification** — agent-dispatchable verification/runtime image contract, not an automatic rebuild on every PR;
- **External evidence audit** — manual-only review of unavailable restricted/large input requirements; strict mode fails rather than silently substituting fake data.

Check the latest run status for the particular PR; historical green badges alone do not establish that the current commit passed.


## Managed Ubuntu development and merge gates (2026-10-23)

For the shared development host, first read `/home/lhy/dev/AGENTS.md`, `/home/lhy/dev/README.md` and this repository's `AGENTS.md`. Work from the actual GitHub PR HEAD in a clean isolated branch/worktree. Ubuntu Docker runs the primary software tests and exact-SHA numerical checks; GitHub provides the mandatory lightweight `repository-admission` / `scientific-admission` PR checks and selected additional CI. This host operates **Mihomo at `127.0.0.1:7897`**, with no MacBook proxy forwarding. These `/home/lhy/dev` commands are host-specific rather than prerequisites for independent clones.

```bash
/home/lhy/dev/bin/local-ci-build cufotri
/home/lhy/dev/bin/local-ci smoke cufotri --wait
/home/lhy/dev/bin/local-ci full cufotri --wait
/home/lhy/dev/bin/local-ci scientific cufotri --wait
```

The `local-ci` entry points currently require the repository's fixed `/home/lhy/dev/cufotri/worktrees/local-docker-dev` checkout to contain the intended clean HEAD, and image/inputs/results must refer to that SHA. `full` is only the selected **software** suite; `scientific` can legitimately report `PARTIAL`/`NOT_RUN`. A source/test PR needs a verified `ubuntu-docker-full` commit status for its live SHA; the project also retains any applicable original-model, analytical, scientific or independent-review gates.

The `main` Ruleset requires PR review through `repository-admission` and `scientific-admission`. When every applicable check passes and any required independent scientific acceptance is documented, the agent adds `merge-verified` and GitHub's event-driven native auto-merge processes the PR. Draft, failed, pending, missing-data, stale-SHA or scientifically unaccepted changes remain blocked. Heavy scientific workflows can be agent-dispatched without manual GitHub UI interaction; they are **not** automatically PASS when skipped.

## Docker verification and runtime

Ubuntu Docker builds and executes the primary Python 3.11 + `uv.lock` verification image at the reviewed SHA. Scoped GitHub integration/Python Actions and optional dispatched reproducibility tests use the same locked verification contract; optional dual-stage verification also checks the separate non-root runtime image without pytest, uv or Git history. See [Docker workflow](docs/ci/DOCKER_WORKFLOW.md) for image and security contracts.

```bash
docker build --target verification -t cufotri:verify .
docker run --rm cufotri:verify python -m pytest -m "not external_sb1_data and not external_sb4_data and not external_era5_data and not private_reblinding_secret and not historical_review_context"
docker build --target runtime -t cufotri:runtime .
docker run --rm --tmpfs /results:rw,uid=10001,gid=10001 cufotri:runtime
```

## Optional non-Docker local reproduction

Requires Python 3.11 (single supported interpreter minor; see `.python-version` and `pyproject.toml`). This is a developer convenience, **not** a second CI environment:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest -m "not external_sb1_data and not external_sb4_data and not external_era5_data and not private_reblinding_secret and not historical_review_context"
.venv/bin/python -m cteas_ufotri.cli --case configs/test_case.yaml
```

For the full internal V4 RC1 software composition gate:

```bash
.venv/bin/python scripts/v4/run_development_baseline_rc1.py --output /tmp/cufotri-v4-development-baseline.json
```

Software, deterministic synthetic/replay and conservation tests are **not** experimental-field validation. Run external strict verification only after acquiring and verifying the separately declared input datasets.

## External evidence

ERA5, experimental SB1/SB4 reference packets and private D3 reblinding secrets are not bundled with a fresh public clone. The inputs are declared in `validation/external_input_requirements.py`. Local environments historically use `CTEAS_EXTERNAL_EVIDENCE_ROOT` and `CTEAS_ERA5_INPUT_ROOT`; setting these variable names alone does not supply the files in an ephemeral GitHub runner.

Do not commit credentials, private datasets, unlicensed literature, or blind/unblinding secrets. If external data is missing, explicitly report missing/skipped or strict-failed status. The historic worktree/review-context tests must not be reclassified as contemporary scientific acceptance.

See [validation/README.md](validation/README.md) for data provenance, checksums, licensing and independent validation requirements.
