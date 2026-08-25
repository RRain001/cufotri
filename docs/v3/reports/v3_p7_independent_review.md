# V3-P7 independent boundary review

Verdict: `PASS_P7_INTERFACE_ONLY`

Reviewed branch: `codex/v3-p7-atmos-coupling-interface`

Reviewed baseline: `0ff463336409e74814d7d676577178b2e3680adc`

## Scope and protected paths

- Source additions are isolated to `src/cteas_ufotri/coupling/atmos_v3/`.
- Existing V1/V2 plant, soil, foodchain, dose, atmosphere, case, config,
  and legacy coupling runtime files are unchanged.
- `configs/`, `parameters/`, and the trusted external-evidence registry are
  unchanged.
- Default leaf-exchange and direct-leaf-uptake activation remain off.

## Boundary review

The new record is immutable, requires explicit forcing values, validates UTC,
finite values, ranges, provenance, and exact unit tokens, and does not repair
or infer missing data. Metadata is a separate immutable record with model,
grid, temporal, source, creation-time, and quality fields.

The only downstream edges are the existing leaf-resistance forcing input and
the existing soil deposition forcing input. The atmospheric package has no
direct import of TFWT, OBT, root, foodchain, intake, dose, CALMET, CALPUFF,
ERA5/WRF readers, or file-format libraries. No production solver is called
and no UFOTRI parameter is loaded.

## Evidence

- P7 focused tests: 16 passed.
- Cross-stage compatibility tests: 157 passed.
- Architecture tests: 44 passed, including source-scope and protected-path
  checks.
- Compile, import smoke, and whitespace checks passed.

## Limitations and disposition

The interface is not a meteorological data exchange implementation and does
not provide atmospheric or plant physical validation. No CALMET/CALPUFF
equivalence, observational validation, calibration, regulatory, dose, or V3
physics-readiness claim is made. P8 may define a data-exchange contract and
source-specific adapters after independent review; it must preserve this
typed boundary and provenance/units requirements.
