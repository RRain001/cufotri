# ADR-017: V3 baseline validation framework policy

Status: Accepted for P7.7A framework construction

## Context

P7.6D froze the current V3 model and identified both future validation targets
and representation redesign requirements. A validation interface is needed
before any future physical evidence can be reviewed, but the interface must
not become a parameter database, a calibration path, or a reason to bypass
the redesign gate.

## Decision

P7.7A adds an isolated `validation_v3` control plane with four contracts:

1. `ValidationCase` requires named forcing, initial state, parameter context,
   model outputs, reference data, metrics, acceptance criteria, and complete
   provenance.
2. Metrics operate only on caller-supplied values. Existing solver ledgers
   remain authoritative; the conservation adapter recomputes a residual for
   audit without mutating or replacing a ledger.
3. `ValidationResult` records the metric decision together with uncertainty,
   execution hash, solver version, and parameter snapshot. Its pass/fail flag
   must agree with its threshold rule.
4. `can_enter_validation()` admits only software, analytical, and synthetic
   baseline cases using explicit test-only parameters. It rejects active
   parameters, calibration, UFOTRI database import/activation, empirical
   validation classes, and V3 readiness.

Benchmark values live in YAML. The built-in five-case suite is an interface
fixture and is not executed by the loader.

## Consequences

The validation vocabulary and result provenance are stable enough for a later
independent runner and review package. Physical evidence, parameter
validation, calibration, activation, and any P7.6D redesign remain separate
decisions. The framework cannot by itself justify `VALIDATED_PARAMETERS` or
`V3_PHYSICS_READY` changes.

## Rejected alternatives

- Importing the existing parameter registry into runtime solvers would couple
  evidence governance to activation and violate the current V3 boundary.
- Generating expected values by calling the production solver would make a
  self-comparison rather than an independent benchmark.
- Storing case constants in Python would hide scenario provenance and violate
  the repository configuration contract.
