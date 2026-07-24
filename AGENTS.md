# CTEAS_UFOTRI repository rules

1. `ufotri_manual.md` is the primary physical source. The curated equations in
   `docs/equations/` are the implementation contract; a reviewed manual
   equation overrides an inferred implementation.
2. Internal calculations use SI units. Every new equation needs a dimensional
   check, and every inventory equation needs a conservation test.
3. Case values belong in YAML configuration, never in calculation code.
4. ERA5 credentials, raw weather data, and large generated outputs must not be
   committed or overwritten. Readers treat raw inputs as read-only.
5. Missing inputs may use replaceable defaults, documented in
   `docs/assumptions.md`; missing data is not a reason to stop development.
6. Uncertain UFOTRI relations retain an interface and the label `provisional`.
   They must not be represented as validated.
7. After each stage, run relevant tests and update
   `docs/implementation_status.md`. Continue after a passing stage.
8. Do not run long production simulations or develop a GUI until the
   calculation kernel is stable.
9. If a session/tool limit interrupts work, preserve code and update the status
   document with completed stages, failed commands, remaining tasks, and the
   exact next command. Do not mark the overall project complete.
