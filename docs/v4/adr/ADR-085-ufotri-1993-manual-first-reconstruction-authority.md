# ADR-085 — UFOTRI 4.0 (1993) manual-first reconstruction authority

Status: `ACCEPTED_SCIENTIFIC_SCOPE_DECISION` (2026-10-22); implementation qualification remains separate.

Stage: `KFK5194_1993_MANUAL_BASED_RECONSTRUCTION_AUTHORITY`

## Context

The original UFOTRI 4.0 FORTRAN source, executable, original decks and golden outputs have **not been obtained**. CUFOTRI's current frozen, previously qualified historical software baseline primarily follows KfK 4605 (1990). The target is **W. Raskob, KfK 5194 (1993), _Description of the New Version 4.0 of the Tritium Model UFOTRI Including User Guide_**, official source: https://publikationen.bibliothek.kit.edu/270034158/3813483. The 1991 KfK 4853 guide is historical cross-edition evidence, not the 1993 specification. The repository root `ufotri_manual.md` transcribes **1990** and must not be mistaken for the 1993 manual.

The KfK5194 source audit R2–R9 documents many 1993 equations and historical defaults and several genuine ambiguities: Eq.(23) conductivity `K` mm/day versus Eq.(24) inter-layer flux `V_ab` mm/hour, Eq.(25) evaporative re-emission terms against the 1990 equation, `RELFA` percent convention, and contradictory printed `SOURCE K2.2` / `METEOZON K1.2` card descriptions and example rows. Waiting indefinitely for the original FORTRAN must **not** prevent an explicitly scoped **manual-based** 1993 reconstruction.

## Decision: normative documentation and allowed claim

1. **KfK 5194 (1993) is the normative physical and historical parameter reference for the opt-in UFOTRI 4.0 path**: printed equations, figures, tables, named inputs, units, defaults, option flags, and documented applicability. Cite exact printed section/equation/table/page and PDF zero-based index for each implementation.
2. **KfK 4853 (1991)** informs lineage or checks an ambiguity, but cannot override an explicitly stated 1993 formula, branch or default. **KfK 4605 (1990)** remains the frozen compatibility baseline and may not silently supply missing 1993 constants.
3. **Original FORTRAN source/executable is NOT a prerequisite to begin a source-anchored manual reconstruction.** It is a separate, currently unavailable evidence route required before claiming `ORIGINAL_UFOTRI_4_0_EXECUTABLE_NUMERIC_EQUIVALENCE`. Do not call manual-faithful calculations 'the original UFOTRI program'.
4. The 1993 path must be a clearly named **opt-in source-version profile** (e.g. `KFK5194_1993_V4`), distinct from the active 1990 defaults. The current repository does **not** yet implement or activate the complete 1993 profile.
5. When the 1993 manual itself is inconsistent, the implementation must **not invent the historical FORTRAN behavior**. Mark the precise branch `SOURCE_LIMITED`; prefer an explicit modern, versioned, user-facing scientific assumption or alternate named interpretation only if the assumed equation/units and consequences are transparent, independently reviewed, and tested. High-risk ambiguous legacy fixed-width cards may be rejected; a named-field configuration interface is permitted without promising bytewise compatibility.
6. Original-executable numeric parity, empirical/field validation, original input reader parity, and regulatory qualification are **four separate claims**, none established by the source audit or green synthetic tests. Retain the existing `NOT_ESTABLISHED` flags.

## Per-feature implementation acceptance while P0 audit continues

**Do not equate 'unavailable original code' with a global block on manual-first development.** A physical P1–P7 feature can proceed as a reviewable, opt-in implementation proposal once *its own* P0 source evidence and scientific review are satisfied, even if full P0-wide audit is still open. This does **not** waive P0 source-first review or permit marking P0 closed or the 1993 whole-model reconstruction ready:

- Identify the exact 1993 manual equation, default and branch, with units, domain, time basis and any missing quantities. Confirm scientific/independent review of **that feature** first.
- Maintain a machine-readable version-scoped parameter profile and **no legacy default or frozen-baseline drift**.
- For each new solver path, require dimension checking, conservation/positivity/boundary tests, deterministic numerical regressions, paired opt-in 1990/1993 tests when comparable, and exact-head Python 3.11/Docker/Protected Integration/Remediation CI. Independently check the original-PDF transcription.
- For ambiguous source elements, document a research assumption, run a sensitivity/bounding comparison, and do not describe it as the literal original execution algorithm.
- Full P0 audit remains `OPEN` until all required source matrix coverage and independent scientific sign-off. A whole-model 1993 fidelity claim requires a separate end-to-end scientific gate; original-executable/empirical claims each have their own external evidence requirements.

## Priority and implementation order

**P0 per-feature source sign-off → P1 named 1993 version profile and input contracts → P3/P2/P4/P5/P6 physical paths → P7 coupling and manual-fidelity qualification.** Do not require exact FORTRAN fixed-column parsing as a condition for a modern named-parameter 1993 model; pursue legacy cards and byte-level equivalence on a separate optional interoperability/validation track. Use the 1993 user-guide default `IWASH=0` three-class precipitation branch, not the optional `IWASH=1` power law, wherever the historical 1993 default is explicitly requested (existing R6b source evidence).

For all published or user-facing reports, use **'independent reconstruction based on the published 1993 UFOTRI 4.0 KfK5194 manual'** until stronger evidence is available.

## Boundaries and supersession

This ADR adjusts **source and qualification policy** only; it does not retroactively validate prior code, change physical formulas or defaults, close P0/#126, or assert original-executable accuracy. It refines the 'P0 blocking all work' language in Epic #125: **source review of each proposed feature is mandatory; global archival FORTRAN retrieval is not**. Any contrary implication in older R7–R9 'must obtain original reader before implementation' text applies only to claiming/recreating an **original fixed-width reader**, not to building a modern named-field model conforming to explicitly documented 1993 physics.
