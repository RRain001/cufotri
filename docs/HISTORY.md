# Historical records and recovery

On 2026-10-24, CUFOTRI began simplifying the working repository for manual-based box-model/ODE development. **Historical source records, scientific uncertainty and provenance are not erased.** They remain in earlier Git commits and an independently verified local Git bundle. Archival removes files from the current working tree, not their prior Git history.

| Frozen item | Immutable commit |
|---|---|
| Pre-slim GitHub `main` | `872b397b7b4d36b7decf475da3bb043b3621b182` |
| UFOTRI 1993 P2 PR #159 before simplification | `b84a98123251b53d83fd27845b668296db6a482a` |

Local annotated tags: `archive/cufotri-preslim-20261024-main` and `archive/cufotri-preslim-20261024-p2`. A private, SHA256-verified `archived-refs.bundle` and per-file checksum manifests reside in `/home/lhy/dev/cufotri/reports/repo-slim-20261024/` on the authorized Ubuntu host. Do not publish those snapshots or any restricted raw data without checking their license and confidentiality.

To restore a single historical document without changing branches:

```bash
git show 872b397b7b4d36b7decf475da3bb043b3621b182:docs/v3/reports/FILE.md
```

To inspect the full original working tree without touching present source:

```bash
git worktree add --detach /tmp/cufotri-archive-view 872b397b7b4d36b7decf475da3bb043b3621b182
```

The repository still distinguishes **KfK 4605 (1990)** from **KfK 5194 (1993)**, with manual-based reconstruction separate from original executable parity, empirical validation or regulatory use. The original UFOTRI executable is not available. Staged science work on PR #159 and PR #152 remains in those respective Git branches and is not modified by this cleanup.

What was removed from the current tree: unreferenced historical reports and development-governance snapshots, with already-frozen test expectations for those snapshots. Active source modules, documented equation assumptions, original-license restrictions, external-data contracts and actual conservation/integration tests are retained. For ongoing work see [DEVELOPMENT.md](DEVELOPMENT.md).

## Second safe archival batch — 2026-10-24

After [PR #160](https://github.com/RRain001/cufotri/pull/160), a second dependency scan separated machine-referenced scientific sources from superseded standalone review documents. The frozen pre-second-batch `main` is `bccad376df44a6107de3aa02c7d4eb2ebb07ed51`, published under the annotated Git tag `archive/cufotri-phase2-base-20261024`. Only **47 old, currently unreferenced Markdown stage records** were archived in this batch: V2/V3 process and acceptance reports, historical V4 governance ADRs and associated handoffs. Their exact paths and SHA-256 checksums are preserved locally in `/home/lhy/dev/cufotri/reports/repo-slim-phase2-20261024/archived_documents_sha256.tsv`.

Physical equation methods, V3/V4 parameter and mass-basis definitions, 1990/1993 source editions, HTO/OBT soil/root process ADRs with unique methodology, machine-readable registries, runtime code, tests, existing scientific benchmarks and external input contracts were deliberately **not** archived. No original FORTRAN parity or missing field data was declared passed.

For example, restore a second-batch archived ADR without changing your current branch:

```bash
git show bccad376df44a6107de3aa02c7d4eb2ebb07ed51:docs/v4/adr/ADR-035-v4-system-post-orchestration-review.md
```

Retaining the immutable historical record does not mean obsolete stage approvals are current scientific validation.

The historical `V3 Remediation CI` manual workflow and four **document-only** stage-governance test modules were also retired from the active tree, while current numerical/conservation suites, `tests/architecture/test_v3_current_remediation_invariants.py` and `tests/integration/test_v3_pipeline_composite_conservation.py` remain. Their original files and stage expectations are recoverable from the same frozen phase-two tag; removing the old workflow does **not** change the protected `repository-admission` / `scientific-admission` checks, which remain active. Independent historical or empirical validation remains separate.

## Fourth batch: retire superseded G4/H6 stage-final gates — 2026-10-24

The pre-fourth-batch main commit is `ea87f2524917238dd279a24b95f61d24fe73ed2c`, preserved by the published annotated Git tag `archive/cufotri-phase4-base-20261024`. This batch archives exactly two historical final-qualification lifecycle scripts and their dedicated document-only test modules:

- `scripts/v4/check_ufotri_manual_based_functional_reconstruction_final_gate_r1.py` (G4 first lifecycle)
- `scripts/v4/check_ufotri_manual_based_functional_reconstruction_final_gate_r2.py` (H6 corrected lifecycle)
- `tests/v4/test_ufotri_manual_based_functional_reconstruction_final_gate_r1.py`
- `tests/v4/test_ufotri_manual_based_functional_reconstruction_final_gate_r2.py`

These 880 lines concern *past PR candidate-to-merge stage claims* and the historical roadmap. Static references from current source, remaining tests, other scripts, configuration, CI and validation data were checked before archival; **only the two frozen historical governance YAML records still mention the retired script paths**. Those YAML documents remain verbatim as historical records; their script paths are archival provenance, not active executable entrypoints. Exact SHA-256 per file is retained privately on Ubuntu at `/home/lhy/dev/cufotri/reports/repo-slim-phase4-20261024/archived_gate_sha256.tsv`.

For recovery (the current branch is not changed):

```bash
git show ea87f2524917238dd279a24b95f61d24fe73ed2c:scripts/v4/check_ufotri_manual_based_functional_reconstruction_final_gate_r2.py
```

**Not retired:** `scripts/v4/check_ufotri_cross_module_fidelity_qualification_r1.py` (G3), which performs real root-delay simulations, gap checks and module-level numerical probes; all associated conservation/integration tests; `STATUS.md` scientific claims; KfK 4605/5194 source definitions; or independent external scientific validation requirements. Archiving obsolete CI-era lifecycle checks **does not certify historical executable equivalence, physical accuracy or empirical field validation**.

## P5 runner consolidation and historic stage archival — 2026-10-24

The full starting `main` is commit `70af1d8a7b301da3a396a67f9947d8a7e1a8117d`, preserved as the published annotated `archive/cufotri-p5-base-20261024` tag. This P5 batch removes 17 superseded V3 governance/independent-review stage documents, G4/H6 historical lifecycle YAML and one post-endpoint historical state record from the *working tree*. Unique equation-gap, physical coupling and validation-dependency documents, active 1990/1993 manuals, the ADR-021 machine-referenced policy, and all scientific benchmark inputs remain available as current files.

Two small historical runner wrappers, `scripts/run_v2_uncertainty_convergence.py` and `scripts/run_wet_parameter_sensitivity.py`, were superseded by `scripts/studies.py` subcommands `v2-uncertainty` and `wet-sensitivity`. The numerical functions/parameters are unchanged. The 12-row wet study JSON was checked byte-for-byte before/after with SHA256 `5a5480fa3b37a93ab14165fb2576cfee2a777603d2b1c2a7bbdff7ec9dcf8c04`; the expensive full LHS study was checked at its dispatch/CLI contract but not rerun for this administrative migration. Historic scripts and stages can be read with `git show 70af1d8a7b301da3a396a67f9947d8a7e1a8117d:<path>`.

Path lists, machine-reference decisions and SHA-256 checksums for all archived documents and wrappers are held privately on Ubuntu under `/home/lhy/dev/cufotri/reports/repo-slim-p5-20261024/`. Existing science status and historical UFOTRI executable equivalence/field evidence remain `NOT_ESTABLISHED`/`NOT_RUN`.
