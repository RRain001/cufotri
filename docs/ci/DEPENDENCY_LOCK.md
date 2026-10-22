# Python dependency lock policy

The authoritative source of direct runtime/test requirements remains `pyproject.toml`.
The repository-level `uv.lock` is the **committed resolution** for the sole supported Python minor version (3.11) across applicable platforms. It was initially generated on a GitHub-hosted Ubuntu runner using uv **0.13.5**.

## Supported cloud environments

- GitHub-hosted Ubuntu x64 runs Docker **Python 3.11** verification images for Protected Integration Gate, Remediation and external evidence.
- GitHub-hosted Ubuntu x64 runs the same Docker **Python 3.11** verification stage for portable smoke/regression CI; no separate host Python testing environment is installed.
- `.python-version` is `3.11` and `pyproject.toml` restricts runtime to the Python 3.11 minor series (`>=3.11,<3.12`). This aligns with CTEAS-next's Python 3.11 Ubuntu-bootstrap and Docker runtime.
- A compatible non-Linux local environment may use the universal lock, but untested platform/runtime combinations are not implied to pass.

## Reproduce exact CI dependency resolution

```bash
python -m pip install uv==0.13.5
uv sync --locked --extra test --python "$(command -v python)"
.venv/bin/python -m pytest -q -m "not external_sb1_data and not external_sb4_data and not external_era5_data and not private_reblinding_secret and not historical_review_context"
```

The verification Docker build uses precisely `uv sync --locked --extra test`, while the runtime dependencies stage uses `uv sync --locked --no-dev --no-editable`, refusing to silently rewrite the resolved dependency graph. CI test commands execute in Docker, not in a second host-managed Python virtual environment. `uv.lock` contains package/version/source and package distribution hashes. This does not itself guarantee permanent external index availability, and it is not a scientific evidence dataset lock.

## Explicit dependency updates

Do not run `uv lock` silently as part of normal PR validation. Instead:

1. Open a dedicated dependency-maintenance PR.
2. Edit `pyproject.toml` only when direct requirements/compatibility change.
3. Using uv 0.13.5, run `uv lock --upgrade` (or targeted `uv lock --upgrade-package PACKAGE`), inspect the diff and commit updated `uv.lock`.
4. Run the Python 3.11 regression, Protected Integration Gate, Remediation CI and, if public model behavior could change, any relevant fixed numerical/regression fixtures.
5. Record old/new resolved versions, build provenance, security/licensing implications and any changed numerical results in the PR. Do not force acceptance by relaxing physics tolerances or marking external evidence available.

PyPI versions can be updated only with review. The installed-package manifest uploaded by the Python 3.11 CI is an independent **environment audit**, not an alternative authority that overrides `uv.lock`.

The container build instructions, non-root runtime contract and images' scientific boundaries are documented in [DOCKER_WORKFLOW.md](DOCKER_WORKFLOW.md).

CI uses a read-through Buildx/GitHub Actions dependency cache to avoid reinstalling
identical packages in every job. The cache does not replace `uv.lock` and is
populated only from the Docker `verification-deps` stage, before the complete
Git history and test evidence are copied into the verification image.

## Future improvements

Pin third-party GitHub Action dependencies to full commit SHAs in a separate security audit, and investigate self-hosted storage for publicly redistributable scientific input datasets after validating licenses and hashes. Avoid automatic security-upgrade PRs that bypass numerical equivalence testing.
