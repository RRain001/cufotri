# ADR-056: V4 development completeness review R1

## Status

Accepted as a control-plane completeness decision, subject to exact-head CI and no-drift merge closure.

## Question

After explicitly deferring real production-input binding and real CTEAS-Atmos binding, does the selected controlled V4 architecture still contain any mandatory internal software or selected-physics blocker that must be implemented before a development-baseline RC can be frozen?

## Evidence reviewed

The review uses the normalized current-state authority plus existing certified V4 evidence for:

- data/time/unit/provenance fail-closed contracts;
- three-layer 0–30 cm soil state, signed transport, balance ledgers and restart;
- root identity `J_root,i = q_w,i C_w,i`;
- UFOTRI Eq.39 total root-water construction and 20/40/40 layer profile;
- baseline leaf-resistance exchange path;
- soil-root-TFWT-OBT integration with `PRESERVE_V3_POST_OBT_ROOT_GAIN`;
- replay/synthetic orchestration and coupled conservation;
- reduced UFOTRI OBT baseline;
- `KEEP_HARVEST_EVENT` food/intake/dose endpoint;
- controlled full-chain numerical integration, determinism and restart equivalence;
- frozen V3-default isolation.

## Decision

`PASS_NO_MANDATORY_INTERNAL_BLOCKERS`

No mandatory internal software or selected-baseline physics implementation is missing for the current V4 development target.

This decision is deliberately narrower than production or scientific validation. The V4 baseline can enter a final development RC because its selected internal software chain and controlled physics are implemented and connected. Real project inputs, real Atmos binding, calibration, empirical validation, physical-accuracy qualification and production readiness remain later phases.

## Optional/held physics

The following are not promoted into mandatory blockers:

- Leaf R5 dynamic stomatal response: remains evidence-driven and currently `HOLD_EMPIRICAL_EVIDENCE_REQUIRED`;
- full Richards/Darcy hydrology: not required by the selected simplified UFOTRI baseline;
- multi-pool OBT: evidence-driven optional extension;
- UFOTRI short-term ~3 h delay: optional extension;
- Penman Eq.38 aerodynamic term: not part of the selected Eq.39 controlled baseline.

A future evidence package may reopen any of these through a separate decision. Their absence does not block the current development RC.

## Residual risks that are not internal-development blockers

The RC must continue to state explicitly that:

- synthetic/replay forcing is software evidence, not empirical validation;
- no real CTEAS-Atmos binding is active;
- no real production input packet is ready;
- no calibration or production parameter activation is authorized;
- no physical-accuracy or production-readiness claim is made.

## Authorization

The only mandatory next internal stage is:

`V4_DEVELOPMENT_BASELINE_RC1`

RC1 may perform combined regression, controlled end-to-end execution, deterministic/restart/conservation/fail-closed checks, V3 isolation checks and baseline freeze metadata.

RC1 may not add a new physics subsystem, bind real Atmos, project a production manifest, activate production parameters, calibrate, or claim empirical/physical validation.
