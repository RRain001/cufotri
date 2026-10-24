# CUFOTRI: simple model-development workflow

**Goal:** Reproduce documented UFOTRI atmospheric/soil/plant/dose equations and implement transparent box models/ODE couplings. Software correctness does not imply numerical equivalence with the unavailable original UFOTRI executable, field validation, or regulatory certification.

1. Read the relevant KfK 4605 (1990) or KfK 5194 (1993) equation. Record the source, selected model version, input/output units and any necessary explicit hypothesis.
2. Add or revise the minimum implementation in `src/cteas_ufotri/`; keep parameters in existing versioned configs and preserve the `cteas_ufotri` import API.
3. Add a few useful tests: one reference value, analytical ODE solution or conserved total, one edge/boundary, and one module interface case where applicable. No new audit stage or mass of document-only tests required.
4. Inside the existing Python 3.11 verification environment, run `make test-quick` (curated core physical cases) and the **changed module's** tests. `make test-model` covers unit and integration cases if shared physics changed.
5. Run `make run-example` or the relevant existing case runner; inspect mass/activity balance and output provenance. Merge normal manual-based research features following GitHub's lightweight PR checks.
6. Before a **release candidate** or a risky whole-system refactor, use `make test-full`, an exact-SHA Ubuntu Docker build/full, and report the excluded external tests. The optional comprehensive legacy integration workflow is run by explicit dispatch, not on every documentation or formula edit.

## Separate scope of scientific claims

Manual-based **reconstruction** requires formula, unit and physical-balance evidence; does **not** claim original executable parity. For a PR explicitly claiming historical numerical equivalence, empirical accuracy, formal evidence acceptance or publication-calibrated parameters, use the `scientific-claim` label and independently verify the corresponding evidence and reviewer at the same exact SHA. Claims to original-program parity require the original program and common inputs. External SB1, SB4, ERA5, private D3 and independent review remain NOT_RUN until actually obtained.

Avoid changing GitHub required checks to make a failed or unrun test appear passing. Frozen historical results and removed status ledgers remain recoverable from the pre-slim archive tag described in [HISTORY.md](HISTORY.md).

## Directory and test expectations

- Runtime library: `src/cteas_ufotri/`; do not remove distinct physical versions purely to shorten file counts.
- `tests/unit` and `tests/integration`: actual formula/ODE/conservation/interface behavior.
- `validation/`: active independent cases and input contracts, not a catch-all for old audit narrative.
- `docs/`: operator/developer guide, physical sources, and current scoped claims.
- `scripts/`: case runner and purposeful maintainable tools; legacy stage scripts are not a default development workflow.

GitHub's main Ruleset continues to require `repository-admission` and `scientific-admission`; checks now depend on claim scope, not every source file indiscriminately. Document-only or lightweight changes do not themselves manufacture scientific verification.

## Existing shared validators

Avoid reimplementing the same numeric boundary checks for each source-compatible adapter. The opt-in UFOTRI-native primary atmosphere in `atmosphere/ufotri_native_v4.py` owns `_finite`, `_nonnegative`, `_positive` and `_utc`; the trajectory and process modules reuse them with the original exception and unit semantics. Likewise, `plant/leaf_ufotri_v4/model.py` owns the existing TypeError/ValueError numeric checks already imported by the re-emission area-source adapter. These two validator families intentionally retain their different exception contracts and should **not** be combined without a separate compatibility reason. None of these helpers represents a new 1993 physical formula or original executable parity claim.

## Optional parameter studies (P5 streamlined entrypoint)

Use one `scripts/studies.py` CLI instead of separate historical standalone wrappers:

```bash
python scripts/studies.py wet-sensitivity --output /tmp/wet-grid.json
python scripts/studies.py v2-uncertainty --output /tmp/lhs-convergence.json
```

`wet-sensitivity` still invokes the original 4×3 wet-scavenging study and writes exactly the same sorted JSON bytes as the previous `scripts/run_wet_parameter_sensitivity.py`. `v2-uncertainty` still invokes the existing full-model LHS convergence function with unchanged fixed configuration and seeds, and preserves its JSON/status contract. The original two file-path entrypoints were archived, not their scientific computations. Other V2 benchmark and V3 synthetic runners remain unchanged because their original evidence registries or regeneration protocols reference those paths. No external validation is implied by either study.

## P6 test consolidation: current physical provenance instead of stage-by-stage approvals

The current `tests/v4/test_v4_production_source_policy_evergreen.py` tests the input-source facts that matter across the former R1–R4 governance revisions: full 49-input disposition coverage, the reviewed tritium half-life, FAO-56 reference conventions and pressure-derived psychrometric constant, the distinction between site elevation and receptor/stack height, explicit pressure/elevation source precedence, and the prohibition on silently promoting old Hefei/ERA5 test points into a production scenario. Keep `test_v4_production_case_input_source_resolution_r5.py` as the current fail-closed declaration-intake check. Prior revision test programs are historical Git records, not day-to-day test prerequisites.

`tests/architecture/test_v3_current_remediation_invariants.py` checks that the model runtime cannot import parameter-validation *or* physics-adoption control-plane code; its older P7.6D immutable past-commit tests are archived. This refactor does **not** remove the underlying frozen R1–R4 provenance YAMLs or change physics, benchmark thresholds, runtime parameters, external evidence requirements or research status. The normal `python scripts/test.py quick` / `model` flow is unchanged; all retained V3/V4/architecture checks remain available on demand.

## P7A small-source consolidation

The existing `exposure/intake_v3/validation.py` implements fail-closed identifier and UTC timestamp checks that are AST-identical to the former duplicate code in `exposure/dose_v3/validation.py`. The dose module now imports those existing helpers, still passing its own `DoseStateError` or `DoseParameterError` class as `error_type`, so intake and dose boundary exceptions remain distinct. The benchmark runner similarly reuses `validation_v3/benchmark_registry.py::_thaw` while keeping canonical JSON encoding unchanged. Only identical helpers were consolidated, not unit conversion, source provenance, physical transfer or dose algorithms. Ordinary developers should modify the shared helper rather than introduce a new duplicate.

The six retired fixed-commit historical P7.6 and V3.1 architecture tests are not required daily and can be recovered via `archive/cufotri-p7-base-20261024`. Current parameter candidate/readiness/import-isolation tests remain in `tests/architecture/test_v3_current_remediation_invariants.py`; physical behavior and conservation are tested by the maintained unit/integration suite.

## P7B active typed-path checks

The food, intake and dose modules share current interface checks in `tests/architecture/test_v3_current_food_intake_dose_boundaries.py`. The older three fixed-commit stage checks were archived. All executable numerical tests and input evidence contracts remain. Restore the historical tests or stage documents from `archive/cufotri-p7b-base-20261024` when needed.
