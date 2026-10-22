# P1 R1 — KfK 5194 (1993) explicit historical input metadata contract

This is the first **non-executable, opt-in, version-scoped** P1 input contract, following [ADR-085](../adr/ADR-085-ufotri-1993-manual-first-reconstruction-authority.md). It advances [P1 Issue #127](https://github.com/RRain001/cufotri/issues/127), not the full P0 sign-off.

The pinned machine-readable profile is [`configs/ufotri_1993_manual_source_profile.yaml`](../../../configs/ufotri_1993_manual_source_profile.yaml), and the standalone Python loader is `cteas_ufotri.versioned_inputs_1993.load_1993_source_profile`. **This loader is not imported by the standard CLI, `load_configuration`, or the physical solver; the existing 1990 route remains the default.** An explicit `selected_profile="KFK5194_1993_V4"` and an explicit file path are mandatory.

## Primary-source-supported contract

- **Eight documented branch defaults:** `IMODEL`, `ICOVER`, `IPHOTO`, `IMONT`, `IFLAGS`, `IFLAGR` (KfK5194 p.54/PDF0 63); `IDEPHT`, `IBODEX` (p.55/PDF0 64) all printed as 1. These are historical *metadata*, not active physics.
- **Historical ISOPAR:** nuclides HT before HTO, dry velocities `0.0005/0.005 m/s`; **`IWASH=0`** 3-class default with rainfall boundaries `1/3 mm/h`, HTO coefficients `6e-5/1e-4/4e-4 s^-1`, precipitation duration factors `0.50/0.75/0.72` (KfK5194 pp.46–47, PDF0 55–56). Power law `IWASH=1` is a distinct optional branch, **not activated** in this profile.
- **Historical METPAR:** `METIN=0`, `NOSHFT=2`; printed `IWNDG=500` in `0.01 m/s` units equals `5 m/s`, `IREGN=0` in `0.01 mm/h` units (KfK5194 p.48/PDF0 57). SI and encoded input values are explicitly separated.
- **`RELFA` source ambiguity:** KfK5194 p.66/PDF0 75 prints 0.5 with label percent; the normalized value is deliberately `null` and `SOURCE_LIMITED`. The loader *rejects* any silent choice of 0.5% or 50%.

The documented constants are cross-checked with independent P0 primary-PDF transcription registries `primary_source_formula_audit_r2.yaml` and `primary_source_input_washout_r6.yaml`; tests reject unknown profiles, malformed data, hidden extra inputs, swapped nuclide ordering, wrong rain class scaling, invented resolved humidity, or changed source defaults.

This intentionally **does not reconstruct** original FORTRAN `READ/FORMAT` behavior, a historical binary file, 1993 Gaussian/soil/plant/OBT integration or executable numerical equivalence. It is a typed, immutable, serializable **historical-defaults metadata snapshot**, not a fully qualified scientific parameterization or operational config. Any scientific opt-in physics requires independent per-feature source review and physical tests; P0 remains OPEN.

Usage for metadata inspection only:

```python
from cteas_ufotri.versioned_inputs_1993 import load_1993_source_profile
record = load_1993_source_profile(
    "configs/ufotri_1993_manual_source_profile.yaml",
    selected_profile="KFK5194_1993_V4",
)
assert record.provenance()["runtime_activation"] is False
```
