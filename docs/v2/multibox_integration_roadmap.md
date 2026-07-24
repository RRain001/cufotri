# Experimental three-box soil integration roadmap

RC1 status:

```text
MULTIBOX_SCOPE_STATUS = CLEAR_EXPERIMENTAL_STANDALONE
THREE_BOX_SOIL_STATUS = PASS_EXPERIMENTAL_STANDALONE
```

`soil.multibox.advance_three_box_soil` is a conservative, tested standalone
solver. It is not part of the formal `run_short_case` coupling path and RC1 does
not promote it. Selecting `soil.layer_model: surface_root_deep_3box` in a formal
short case raises an explicit error directing the caller to the standalone API.

Integration in a later release requires all of the following interfaces:

1. a formal coupled state carrying per-layer water and HTO inventories without
   changing the frozen single-layer state contract;
2. surface-only dry/wet deposition input and precipitation infiltration mapped
   into layer 1 exactly once;
3. layer-specific root uptake driven by the active crop root vector, with the
   summed uptake transferred into plant TFWT exactly once;
4. surface evaporation/re-emission and deep leakage exposed to the atmospheric
   feedback and activity boundary ledgers;
5. conservative inter-layer advective and diffusive transfers with donor
   limiting under the formal integrator time step;
6. layer-resolved output columns, units, configuration hashes, mode provenance,
   and a backward-compatible single-layer output projection;
7. analytic zero/one-way transfer checks, water and activity conservation,
   time-step convergence, single-layer limiting comparisons, and full
   end-to-end recomputation;
8. calibration or explicit uncertainty treatment for the current project-level
   drainage, leakage, diffusion, and moisture-profile assumptions.

Until these conditions pass an independent review, the three-box solver must
remain `PROJECT_EXTENSION_EXPERIMENTAL` and cannot be listed as a formal RC1
coupled capability.
