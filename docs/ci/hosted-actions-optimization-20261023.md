# Actions execution policy — cufotri (2026-10-23)

GitHub still automatically runs `repository-admission` and `scientific-admission` on every PR, with the Ruleset enforcing these checks. The Ubuntu Docker full verified at exact PR SHA is required for source/test PRs. `workflow_dispatch` remains available for the original official/scientific reproducibility workflows; their jobs and tests were not removed.

To reduce duplicate hosted Docker builds, `docker-portable.yml` (45-minute timeout) and `v3-remediation-ci.yml` (20-minute timeout) are dispatch-only. `v3-integration-gate.yml` and `python-compatibility.yml` retain PR checks, but no longer repeat on post-merge pushes to main. Integration and Python jobs keep original checks. All dispatch jobs operate on their chosen GitHub ref; their actual run `head_sha` must be recorded, and never treated as equivalent to different PR HEAD. External evidence remains independently required.
