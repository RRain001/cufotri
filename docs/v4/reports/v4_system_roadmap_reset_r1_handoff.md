# V4 system roadmap reset R1 handoff

Branch: `codex/v4-system-roadmap-reset-r1`

Base: `d4bb2def0e81fe5a26b772a239e8c6de8f0d0dcc`

Purpose: freeze the system-level sequencing decision without changing solver physics.

Expected branch contents:

- ADR-026 system roadmap reset;
- machine-readable roadmap registry;
- governance boundary README;
- exact invariants test;
- integration-gate registration;
- review and handoff records.

Required independent checks before merge:

1. branch is based on the recorded main SHA and is ahead only by this roadmap-control change;
2. no files under production solver paths are modified;
3. `git diff --check` equivalent is clean;
4. exact-head CI passes;
5. PR diff preserves `ACTIVE_PARAMETERS = 0`, `CALIBRATION_STARTED = FALSE`, `V3_PHYSICS_READY = FALSE`;
6. merge uses expected head SHA;
7. post-merge parent and tree identity are checked for no drift.

After merge, the authorized next stage is `V4_SYSTEM_ATMOS_EXCHANGE_CONTRACT`. It must remain an interface/data-contract stage and must not reimplement CTEAS-Atmos inside this repository.
