# Long-term plan completion audit

Status values: `PASS` requires direct code/test/runtime evidence; `PARTIAL`
means a stated requirement still lacks complete evidence.

| Plan stage | Status | Current evidence / remaining proof |
|---|---|---|
| Repository and safety inventory | PASS | ignored credential/raw/output paths; actual ERA5 audit |
| Project structure and AGENTS.md | PASS | package/config/docs/tests/CLI and repository rules |
| Manual normalization | PASS_SCOPE | `manual_scope_and_mapping.md` plus six equation contracts |
| ERA5 and meteorological derivations | PASS_PROVISIONAL | CSV/NetCDF, UTC, accumulation/reset, RH/VPD/wind/radiation, PBL/stability routing |
| UFOTRI PET and fallback hydrology | PASS_PROVISIONAL | Eq. 38-43 route and explicit radiation fallback; aerodynamic coefficient remains documented assumption |
| Gaussian primary atmosphere | PASS | point/area sources, PG, ground/top reflection, fixed/simple Briggs, geographic receptors, stability modes |
| Soil water and HTO | PASS | bucket/runoff/drainage/rain HTO/deposition/re-emission/root/decay and conservation tests |
| Plant TFWT and OBT | PASS | direct-leaf interface, root/transpiration, day/night OBT and turnover tests |
| Re-emission and coupling | PASS_PROVISIONAL | basic mode plus optional reconstructed REEM/DIFF/ZT, area-source feedback and lag |
| Numerical integration | PASS | bounded explicit update, step refinement, SciPy continuous reference |
| Required unit/integration tests | PASS | 43 tests cover all enumerated plan invariants and interface failures |
| End-to-end case and artifacts | PASS | synthetic/ERA5 48 h plus advanced 24 h, required schema and nine artifacts each |
| Final documentation/status | PASS | README, equations, assumptions, numerical scheme, status and reports refreshed |

## Completion basis

Every row is now `PASS`, `PASS_SCOPE`, or `PASS_PROVISIONAL`. Provisional items
are precisely the missing-coefficient/default-assumption cases explicitly
permitted by the original plan. They are centralized and replaceable rather
than hidden in core balance equations.

The artifact-level completion check is reproducible with:

```bash
.venv/bin/python scripts/verify_acceptance.py
```
