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
