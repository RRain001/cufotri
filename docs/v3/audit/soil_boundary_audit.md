# Soil Boundary Audit

Audit basis: actual files under `src/cteas_ufotri/soil/`, the current source
tree, and `git diff main...HEAD -- src`. No implementation-status label or
commit message was used.

## V3-P2 source findings

The V3 soil state/model provide a fixed three-layer state, externally supplied
deposition, a mass-balance ledger, and a read-only `RootZoneActivity` seam.
`SoilModel` reports `NOT_IMPLEMENTED` for root uptake and the default physics
kernel fails closed.

However, `soil/physics.py` also contains `SyntheticTransportKernel`. It
performs explicit first-order interlayer activity transfer and decay. The
source labels it `TEST_ONLY` and not UFOTRI, but this is numerical transport
behavior rather than a pure container/interface.

## Existing repository soil code

`soil/multibox.py`, `soil/hto_balance.py`, and `soil/water_balance.py` are
present in the current repository and are not introduced by the P5 additions
relative to `main`. `advance_three_box_soil()` contains an experimental
three-box water/HTO solver with:

- precipitation, evaporation, transpiration, drainage, and leakage;
- root-uptake rates and root HTO fluxes;
- interlayer advection and concentration-based diffusion;
- activity outflow limiting and water/HTO residuals.

This existing code is not the V3-P2 `SoilModel` path, and it is not evidence
of UFOTRI validation. It is nevertheless actual numerical soil behavior in
the repository's soil tree and must not be omitted from a repository-level
boundary audit.

## Classification

```text
V3_P2_DEFAULT_SOIL_PHYSICS = FAIL_CLOSED
V3_P2_ROOT_UPTAKE = NOT_IMPLEMENTED
TEST_ONLY_SYNTHETIC_SOIL_TRANSPORT = PRESENT
EXISTING_THREE_BOX_TRANSPORT_ROOT_DIFFUSION = PRESENT_IN_MAIN_BASELINE
```

The V3 interface seam itself remains isolated, but the whole source tree is
not interface-only. P6/roadmap documentation must distinguish V3 fail-closed
scaffolding, test-only numerical kernels, and pre-existing experimental soil
code.
