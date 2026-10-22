# CUFOTRI Docker + uv workflow

## Purpose and authority

The Docker environment uses the project's sole supported **Python 3.11**
minor, aligned with CTEAS-next's Docker/Ubuntu Python version. The existing
`uv.lock` is the sole Python-dependency resolution authority.
The container layout parallels CTEAS-next's separate verification and
runtime images, without introducing a new physics or evidence claim.

The Dockerfile has two public build targets and two internal dependency stages:

- `python-deps`: uv 0.13.5 resolves and installs runtime-only packages
  non-editably using `uv sync --locked --no-dev --no-editable`.
- `verification-deps`: adds `git` and locked `pytest` dependencies using `uv sync --locked --extra test` **before** the complete repository and Git history are copied. Only this non-sensitive dependency stage can be exported to the BuildKit GitHub Actions cache.
- `verification`: adds the full source tree and Git history to the cached dependency stage. Used for all scientific GitHub Actions and **not** a distribution image.
- `runtime`: starts from a new slim Python 3.11 base, copies only the
  preinstalled runtime environment and `configs/`, and runs as UID/GID 10001.
  It deliberately has no `uv`, `pytest`, `git`, `tests/`, project source
  checkout, historical reports or raw scientific inputs.

The official multi-platform `python:3.11-slim-bookworm` base is digest-pinned in `Dockerfile` (verified 2026-10-22). To update it, review an authoritative `docker buildx imagetools inspect` result, test the supported platforms and commit the changed digest through a dedicated PR. A package/SHA/image-ID record is uploaded by `docker-portable.yml`.

The verification image includes the Git object database because some frozen
audit tests require historical SHA lookups. GitHub Actions checks out with
`fetch-depth: 0` and `persist-credentials: false`. The repository's
`.dockerignore` excludes local passwords/ERA5/NetCDF/derived data. Do not
build verification images with an unreviewed private directory as context,
and **do not publish/export** the verification image.

## Reproduce with Docker

From a fresh source checkout with Git history:

```bash
docker build --target verification -t cufotri:verify .
docker run --rm cufotri:verify python -m pytest \
  -m "not external_sb1_data and not external_sb4_data and not external_era5_data and not private_reblinding_secret and not historical_review_context"
```

The Protected Integration Gate also executes its frozen V3/V4 boundary suite
and five explicit V4 machine composition runners, now **inside Docker**.
The remediation and Python 3.11 smoke CI jobs similarly build/run the same
verification image (job-local; no Docker image registry is required). Buildx
reads from the shared GitHub cache scope `cufotri-py311-deps-v1` in all four
scientific workflows. Only the Docker dual-stage workflow **writes** that scope,
from target `verification-deps`. Parallel first-time PR runs may have a cold
cache; subsequent runs reuse the pinned Python dependency layers. A cache hit
is a performance improvement, **not** a scientific acceptance criterion.

Build the data-free runtime:

```bash
docker build --target runtime --build-arg SOURCE_REVISION="$(git rev-parse HEAD)" -t cufotri:runtime .
docker run --rm --tmpfs /results:rw,uid=10001,gid=10001 cufotri:runtime
```

To keep generated files, mount a writable directory (UID 10001 needs write
access on Linux):

```bash
mkdir -p outputs/cufotri
docker run --rm -v "$(pwd)/outputs/cufotri:/results" cufotri:runtime
```

To change a case file, mount only approved **read-only** case inputs and pass
the in-container paths. The image entrypoint is
`python -m cteas_ufotri.cli`, so CLI flags may be appended after the image.
Its default case uses deterministic **synthetic** forcing, not real ERA5.

## Cloud policy

All four active workflows build the `verification` stage and run Python
scientific commands inside it. The new `docker-portable.yml` checks that
both images build, tests the runtime package/absence of test tooling, and runs
the default synthetic 48 h CLI with a writable tmpfs. Only this small,
standalone, data-free runtime stage may be considered for publication after
separate release authorization; the PR CI does not push any image.

`external-evidence.yml` remains manual-only. It builds the verification
image, generates metadata-only readiness audit, and `strict` runs marked
external tests with `--require-external-inputs`. Neither building the image
nor a green `audit` supplies missing SB1/SB4/ERA5/D3 data. For full strict
validation, approved source data must be securely mounted read-only or
provisioned to the runner with documented SHA-256, licenses, access controls
and non-synthetic claims. The stock public GitHub runner has no such data.

## Reproducibility boundaries

`uv.lock` freezes Python dependency selection but not the interpreter patch
version, Debian package revisions, CPU behavior, or source data. The multi-architecture base-image index is pinned by SHA-256 in the Dockerfile.
A full release SBOM, per-platform numerical parity and dependency vulnerability
scanning remain future supply-chain qualification tasks. Record `github.sha`
in the runtime OCI image label; the container CI records the image ID and
installed package list. Do not assert numerical bit identity across
AMD64/ARM64 or real-world physical validation from these build checks.
