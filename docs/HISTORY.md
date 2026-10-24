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
