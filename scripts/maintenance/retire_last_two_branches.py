#!/usr/bin/env python3
"""Retire two CUFOTRI historical branches only after verified durable tags.

The archive branch contains 37 original name/SHA identities and 34 distinct
non-main tip commits in its ancestry. No historic changes are merged to main.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPOSITORY = "RRain001/cufotri"
ARCHIVE_BRANCH = "archive/unmerged-20261022"
BACKUP_BRANCH = "backup/local-v3-d3-external-evidence-acquisition-20260826"
ARCHIVE_SHA = "d604e9f426dc084ec94eed63f6a28b658b833c51"
BACKUP_SHA = "e0d6f89a34e75b939ec9fe64411d18f23866d76e"
ARCHIVE_TAG = "history/unmerged-branch-tips-20261022"
BACKUP_TAG = "history/local-v3-d3-acquisition-20260826"
MANIFEST = Path("scripts/maintenance/unmerged-branches-20261022.json")
REPORT = Path(os.getenv("REPORT_PATH", "final-branch-retirement-report.json"))


def git(*args, check=True):
    return subprocess.run(["git", *args], check=check, text=True, capture_output=True)


def sha_of_remote_branch(name):
    result = git("ls-remote", "origin", "refs/heads/" + name).stdout.strip()
    return result.split()[0] if result else None


def remote_tag_sha(name):
    output = git("ls-remote", "--tags", "origin", "refs/tags/" + name,
                 "refs/tags/" + name + "^{}").stdout.splitlines()
    if not output:
        return None
    peeled = [line.split()[0] for line in output
              if line.endswith("refs/tags/" + name + "^{}")]
    if len(peeled) != 1:
        raise RuntimeError("Historical tag is not annotated: " + name)
    return peeled[0]


def ancestor(older, newer):
    result = git("merge-base", "--is-ancestor", older, newer, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError("Unable to check commit ancestry")
    return result.returncode == 0


def save(report):
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


def verify_archive_manifest():
    manifest = json.loads(MANIFEST.read_text())
    entries = manifest["branches"]
    if manifest["repository"] != REPOSITORY or len(entries) != 37:
        raise RuntimeError("Unexpected historic evidence manifest")
    if len({x["name"] for x in entries}) != 37:
        raise RuntimeError("Duplicate history manifest entries")
    if len({x["sha"] for x in entries}) != 34:
        raise RuntimeError("Unexpected number of unique evidence tips")

    message = git("show", "-s", "--format=%B", ARCHIVE_SHA).stdout
    parents = git("show", "-s", "--format=%P", ARCHIVE_SHA).stdout.split()
    if len(parents) != 35 or "EXACT_BRANCH_TIP_MANIFEST_BEGIN" not in message:
        raise RuntimeError("History archive commit was modified")
    if "EXACT_BRANCH_TIP_MANIFEST_END" not in message:
        raise RuntimeError("History archive identity list is incomplete")
    for row in entries:
        name, sha = row["name"], row["sha"]
        if f"{name} {sha}" not in message or not ancestor(sha, ARCHIVE_SHA):
            raise RuntimeError("Lost or mismatched original evidence: " + name)
    archive_tree = git("rev-parse", f"{ARCHIVE_SHA}^{{tree}}").stdout.strip()
    base_tree = git("rev-parse", f"{parents[0]}^{{tree}}").stdout.strip()
    if archive_tree != base_tree:
        raise RuntimeError("Archive includes code changes; expected history-only commit")
    return parents[0]


def ensure_tag(name, sha, description):
    remote_sha = remote_tag_sha(name)
    if remote_sha:
        if remote_sha != sha:
            raise RuntimeError(f"Existing tag points to unexpected commit: {name}")
        return "already_exists"

    if git("show-ref", "--verify", "--quiet", "refs/tags/" + name,
           check=False).returncode == 0:
        raise RuntimeError("Conflicting local tag: " + name)
    git("tag", "-a", name, sha, "-m", description)
    push = git("push", "--porcelain", "origin",
               "refs/tags/" + name + ":refs/tags/" + name, check=False)
    if push.returncode:
        raise RuntimeError("Tag publish failed: " + (push.stderr or push.stdout))
    if remote_tag_sha(name) != sha:
        raise RuntimeError("Cannot verify published annotated tag: " + name)
    return "published"


def main():
    repo = os.getenv("GITHUB_REPOSITORY")
    if repo != REPOSITORY or os.getenv("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("This must run on CUFOTRI default main branch")
    event = os.getenv("GITHUB_EVENT_NAME")
    if event == "push":
        if "[retire-cufotri-branches-20261022]" not in os.getenv("TRIGGER_COMMIT_MESSAGE", ""):
            raise RuntimeError("Missing explicit retirement trigger in merge commit")
    elif event == "workflow_dispatch":
        if os.getenv("RETIRE_CONFIRMATION") != "RETAIN_TAGS_DELETE_TWO_BRANCHES":
            raise RuntimeError("Manual run requires exact confirmation")
    else:
        raise RuntimeError("Only explicitly authorized push or dispatch allowed")

    main_sha = sha_of_remote_branch("main")
    if main_sha != os.getenv("GITHUB_SHA"):
        raise RuntimeError("Main branch changed during job preparation")

    report = {"repo": REPOSITORY, "main": main_sha, "tags": {},
              "deleted": [], "failed": [], "remaining_branches": []}
    save(report)

    first_parent = verify_archive_manifest()
    if not ancestor(first_parent, main_sha):
        raise RuntimeError("Archive source main commit not in current main history")
    if not ancestor(BACKUP_SHA, main_sha):
        raise RuntimeError("Old backup commit not retained by main")
    history = [(ARCHIVE_BRANCH, ARCHIVE_SHA, ARCHIVE_TAG,
                "CUFOTRI historical unmerged branch tips and 37-name SHA manifest"),
               (BACKUP_BRANCH, BACKUP_SHA, BACKUP_TAG,
                "CUFOTRI frozen original V3 D3 external evidence acquisition checkpoint")]

    for old_ref, sha, tag, description in history:
        live = sha_of_remote_branch(old_ref)
        if live not in (None, sha):
            raise RuntimeError(f"Branch moved after historic audit: {old_ref}")
        report["tags"][tag] = {"sha": sha, "state": ensure_tag(tag, sha, description)}
        save(report)

    # Both annotated tags must survive fetching from GitHub before ANY deletion.
    git("fetch", "--no-tags", "origin",
        "refs/tags/" + ARCHIVE_TAG + ":refs/tags/verify-history-archive",
        "refs/tags/" + BACKUP_TAG + ":refs/tags/verify-history-backup")
    if (git("rev-parse", "refs/tags/verify-history-archive^{commit}").stdout.strip()
            != ARCHIVE_SHA or
        git("rev-parse", "refs/tags/verify-history-backup^{commit}").stdout.strip()
            != BACKUP_SHA):
        raise RuntimeError("Re-fetched tag targets do not match audited commits")
    if sha_of_remote_branch("main") != main_sha:
        raise RuntimeError("Main advanced; aborting branch deletion")

    for old_ref, expected_sha, tag, _ in history:
        if remote_tag_sha(tag) != expected_sha:
            raise RuntimeError("Tag lost before branch deletion")
        live = sha_of_remote_branch(old_ref)
        if live is None:
            continue
        if live != expected_sha:
            raise RuntimeError("Branch advanced; keeping: " + old_ref)
        result = git(
            "push", "--porcelain",
            f"--force-with-lease=refs/heads/{old_ref}:{expected_sha}",
            "origin", ":refs/heads/" + old_ref, check=False,
        )
        if result.returncode:
            report["failed"].append({
                "branch": old_ref, "error": (result.stderr or result.stdout)[-1500:]
            })
            save(report)
            raise RuntimeError("Failed to delete " + old_ref)
        report["deleted"].append(old_ref)
        save(report)

    # The pull-request branch should be auto-deleted by GitHub on merge.
    refs = git("ls-remote", "--heads", "origin").stdout.splitlines()
    remaining = sorted(x.split()[1].removeprefix("refs/heads/") for x in refs)
    report["remaining_branches"] = remaining
    save(report)
    if remaining != ["main"]:
        raise RuntimeError("Other branches remain: " + ", ".join(remaining))
    if remote_tag_sha(ARCHIVE_TAG) != ARCHIVE_SHA or remote_tag_sha(BACKUP_TAG) != BACKUP_SHA:
        raise RuntimeError("Permanent Git history tags missing")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("RETIREMENT_ERROR:", e, file=sys.stderr)
        raise
