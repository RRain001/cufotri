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
| `.github/workflows/` | Docker-based PR/main scientific CI, runtime image verification and manual external-evidence audit |

The large historical `docs/implementation_status.md` remains a legacy stage ledger, **not** the current top-level release authority. Its dated stage entries should not override the two V4 roadmaps or [STATUS.md](STATUS.md).

## GitHub-first development

Development takes place through a short-lived GitHub branch and pull request; a permanent local clone is not required. The GitHub-hosted Actions runner builds a **Python 3.11 Docker verification image** and executes the scientific tests inside that image. Review the exact PR head, both existing scientific CI workflows and compatibility checks before merging to `main`.

The main workflows are:

- **V3 Protected Integration Gate** — comprehensive portable tests, current/frozen invariants and V4 machine gates;
- **V3 Remediation CI** — historical-boundary and evergreen regression checks;
- **Python 3.11 regression** — one Docker-contained interpreter for installation, imports and representative scientific tests;
- **Docker dual-stage verification** — build and test the isolated verification image and non-root runtime image;
- **External evidence audit** — manual-only review of unavailable restricted/large input requirements; strict mode fails rather than silently substituting fake data.

Check the latest run status for the particular PR; historical green badges alone do not establish that the current commit passed.

## Docker verification and runtime

GitHub Actions uses the Docker verification image (Python 3.11 + `uv.lock`) for all scientific Python tests. It also checks a separate non-root runtime image with no pytest, uv, or Git history. See [Docker workflow](docs/ci/DOCKER_WORKFLOW.md) for security boundaries, commands and configuration.

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
