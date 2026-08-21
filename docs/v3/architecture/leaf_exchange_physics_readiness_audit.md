# V3-P5.2 Leaf Exchange Physics Readiness Audit

Status: `PASS_ARCHITECTURE_READY`

This audit determines whether the isolated V3 Leaf Exchange framework can
receive a later UFOTRI physics migration. It is an architecture-readiness
review, not a physics implementation or validation result. P5.2 does not add
UFOTRI equations, numerical values, external evidence, or production defaults.

## Scope and boundary

The audited V3 path is the P1 `cteas_ufotri.leaf_exchange` package and its
P5.1 `ParameterDatabase` seam. The existing V2 plant path is a separate
compatibility path. In particular, `plant/leaf_exchange.py` contains legacy
manual/UFOTRI formula code and defaults, but P5.2 neither imports those values
into V3 nor changes that path.

The audit therefore evaluates migration seams, ownership, and failure modes.
It does not assert that the repository as a whole contains no legacy UFOTRI
formula. It asserts that the V3 P1-P5.1 migration layer remains physics-free.

## Current process map

```text
LeafExchangeForcing
        |
        v
LeafExchangePhysics.step(state, forcing, dt, parameters)
        |
        +--> TFWT inventory
        +--> OBT inventory
        +--> activity ledger and mass-balance closure
```

The current process can be summarized as:

```text
Atmospheric HTO -> LeafExchangePhysics.step() -> TFWT -> OBT
```

This is a framework map. The default implementation is fail-closed with
status `PHYSICS_PENDING_UFOTRI_MIGRATION`; deterministic exchange kernels are
explicitly test-only synthetic substitutes.

## Future UFOTRI migration map

The future physical process must make the following steps explicit:

```text
Air HTO
  -> boundary-layer resistance
  -> leaf surface
  -> stomatal and cuticular exchange pathways
  -> TFWT formation and transport
  -> biochemical conversion to OBT
  -> decay/turnover loss
```

The future map is a migration target only. No implementation is present in
P5.2, and no numerical relation is frozen by this document.

## Capability matrix

| Capability | Current V3 evidence | P5.2 disposition |
| --- | --- | --- |
| Immutable leaf state | `LeafExchangeState` contains HTO, TFWT, OBT, masses, and time-step bookkeeping | Ready as a state seam |
| Meteorological forcing | `LeafExchangeForcing` validates air HTO, temperature, and relative humidity | Ready for an upstream contract extension; current type is intentionally unchanged |
| Parameter interface | `LeafExchangeParameters` resolves names through `ParameterDatabase` and fails closed on placeholder or unit mismatch | Ready as the ownership seam |
| Activity ledger | `LeafExchangeMassBalance` checks initial inventory plus boundary input against final inventory and loss | Ready, subject to future pathway ownership rules |
| Replaceable physics | `LeafExchangePhysics.step()` is injected into `LeafExchangeModel` | Ready for P6 implementation |
| Leaf resistance decomposition | No V3 stomatal/cuticular/boundary resistance implementation | Missing |
| Exchange pathway decomposition | No separate stomatal and cuticular flux contract | Missing |
| Formation kinetics | No reviewed V3 TFWT-to-OBT formation relation or parameter set | Missing |
| UFOTRI numerical equivalence | No reference trajectory or equivalence case | Not claimed |

## Readiness decision

The V3 framework is architecturally ready because state, forcing, parameter
ownership, replaceable physics, and mass-balance seams already have explicit
contracts. It is not physically ready for production use until P6 freezes the
resistance pathway, exchange equations, formation/turnover kinetics, parameter
provenance, and reference-case tolerances.

P5.2 preserves all current interfaces. The proposed extension is recorded in
`ADR-009-leaf-exchange-extension.md`; it is not an implementation request for
this stage.
