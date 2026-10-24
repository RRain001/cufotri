# CUFOTRI

Manual-based research reconstruction of UFOTRI tritium pathways: atmospheric HT/HTO, dry/wet deposition, soil/water boxes, plant TFWT/OBT, food transfer and dose. The Python package and CLI remain named `cteas_ufotri` for backward compatibility.

**Scope:** A reproducible implementation of available manual equations, not a numerically verified copy of the original UFOTRI executable, validated field model or regulatory tool. KfK 4605 (1990) remains the frozen baseline; KfK 5194 (1993) is authoritative for explicitly opt-in 1993 pathways. Original program parity and external empirical validation are separate research questions.

## Quick start

Use the project-pinned **Python 3.11** environment (the standard Ubuntu verification Docker image already provides it):

```bash
python scripts/test.py quick            # curated equations and box/ODE conservation
python scripts/test.py model            # all currently maintained unit/integration tests
python scripts/test.py full             # optional comprehensive software regression
python -m cteas_ufotri.cli --case configs/test_case.yaml
```

On a developer machine with `make`, equivalent commands are `make test-quick`, `make test-model`, `make test-full` and `make run-example`. Install dependencies from `uv.lock` using Python 3.11; see [development guide](docs/DEVELOPMENT.md). Do not run full for every documented formula or minor edit.

## Source layout

| Path | Content |
|---|---|
| `src/cteas_ufotri/` | Atmospheric, soil, water, plant, TFWT/OBT, re-emission, food chain, dose, coupled ODE/budgets |
| `configs/` and `schemas/` | Reproducible model inputs and units |
| `tests/unit/`, `tests/integration/` | Mathematical behavior, analytical bounds, conservation and interfaces |
| `scripts/test.py` | Single quick / model / full software test entrypoint |
| `validation/` | Independently versioned reference data, provenance and external-data contracts |
| `docs/DEVELOPMENT.md` | Formula-first implementation and test workflow |
| `docs/INDEX.md` | Current method/source-fidelity navigation |
| `docs/HISTORY.md` | Pre-slim historical evidence, archive and restoration |

For active research status see [STATUS.md](STATUS.md). Selected source-edition decisions and scientific limitations remain under `docs/v4/adr/` and `docs/v4/1993_upgrade/`.

## GitHub / Ubuntu policy

Ordinary model-formula changes get focused physical tests. The fast Python 3.11 PR check runs only for source/test/dependency changes; the formerly repeated V3/V4 comprehensive gate is **manually dispatched** for releases or high-risk integration changes. A version release uses one exact-SHA Ubuntu Docker Full, not a Full for each subtask.

The repository's `repository-admission` and `scientific-admission` remain required by GitHub Ruleset. Manual-based equations are not the same as claims of original-program numeric equivalence or experimental validity: formal claims require actual independent evidence, an appropriate reviewer and explicit validation status. No missing SB1/SB4/ERA5/private D3 evidence is fabricated or silently reclassified as PASS.

Unmerged research PRs #152 and #159 are independent and remain Draft until explicitly resolved; this repository slimming must not alter or merge them. Archive details and reproducible recovery are in [HISTORY.md](docs/HISTORY.md).
