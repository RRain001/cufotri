# syntax=docker/dockerfile:1
# Python 3.11 matches CTEAS-next; verify with uv.lock, ship no CI dependencies.
ARG PYTHON_BASE=python:3.11-slim-bookworm

FROM ${PYTHON_BASE} AS python-deps
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_NO_PROGRESS=1 \
    MPLBACKEND=Agg \
    UV_PROJECT_ENVIRONMENT=/opt/cufotri/.venv
WORKDIR /opt/cufotri
RUN python -m pip install --no-cache-dir uv==0.13.5
COPY .python-version pyproject.toml uv.lock ./
COPY src/ ./src/
# A non-editable install is required: the production image will not carry src/.
RUN uv sync --locked --no-dev --no-editable --python /usr/local/bin/python

# Verification: all tests, governance records and Git object history are present
# only here. Never publish this stage; checkout must have fetch-depth: 0 and
# persist-credentials: false for historical provenance tests.
FROM python-deps AS verification
RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY . .
RUN uv sync --locked --extra test --python /usr/local/bin/python
ENV PATH=/opt/cufotri/.venv/bin:${PATH}
CMD ["python", "-m", "pytest", "-m", "not external_sb1_data and not external_sb4_data and not external_era5_data and not private_reblinding_secret and not historical_review_context"]

# Production: independent slim base, no git, no uv, no pytest, no tests,
# no Git history, no historical reports, no credentials, no research inputs.
FROM ${PYTHON_BASE} AS runtime
ARG SOURCE_REVISION=unknown
LABEL org.opencontainers.image.title="CUFOTRI Python 3.11 research runtime" \
      org.opencontainers.image.revision="${SOURCE_REVISION}"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    PATH=/opt/cufotri/.venv/bin:${PATH}
WORKDIR /opt/cufotri
RUN groupadd --gid 10001 cufotri \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin cufotri \
    && mkdir -p /results \
    && chown 10001:10001 /results
COPY --from=python-deps /opt/cufotri/.venv ./.venv
COPY configs/ ./configs/
USER 10001:10001
ENTRYPOINT ["python", "-m", "cteas_ufotri.cli"]
CMD ["--output-directory", "/results"]
