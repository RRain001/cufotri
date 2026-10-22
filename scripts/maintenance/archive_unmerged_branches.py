#!/usr/bin/env python3
"""Preserve exact unmerged CUFOTRI branch tips in ONE durable archive ref.

Archive commit has main as its first parent and all 34 distinct historic
branch tips as additional parents. Its tree equals main's tree, so no historic
code is integrated into main. Commit message carries the full name->SHA
manifest. Deletions happen only after remote archive verification.
"""
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

MANIFEST = Path(__file__).with_name("unmerged-branches-20261022.json")
REPORT = Path(os.getenv("REPORT_PATH", "archive-unmerged-report.json"))
MARKER = "[run-unmerged-archive-20261022]"


def git(*args, check=True, env=None):
    return subprocess.run(
        ["git", *args], text=True, capture_output=True, check=check,
        env={**os.environ, **(env or {})},
    )


def ls_remote(ref):
    response = git("ls-remote", "origin", f"refs/heads/{ref}").stdout.strip()
    return response.split()[0] if response else None


def get_json(path):
    request = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + os.environ["GH_TOKEN"],
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "cufotri-history-archive",
        },
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)


def get_all(path):
    result = []
    for page in range(1, 20):
        delimiter = "&" if "?" in path else "?"
        items = get_json(f"{path}{delimiter}per_page=100&page={page}")
        if not isinstance(items, list):
            raise RuntimeError("Unexpected API pagination result")
        result.extend(items)
        if len(items) < 100:
            return result
    raise RuntimeError("Unexpected pagination limit")


def is_ancestor(parent, child):
    result = git("merge-base", "--is-ancestor", parent, child, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"Ancestry check failed for {parent}")
    return result.returncode == 0


def save(report):
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


def archive_message(manifest):
    lines = [
        "Archive historical unmerged CUFOTRI branch tips (2026-10-22)",
        "",
        "RESEARCH HISTORY ONLY. Do not merge this archive into main.",
        "This commit uses main's tree and records old branch tips as parents.",
        "Ancestry preserves original failure/independent-review commits.",
        "",
        "EXACT_BRANCH_TIP_MANIFEST_BEGIN",
    ]
    lines.extend(f"{b['name']} {b['sha']}" for b in manifest["branches"])
    lines.append("EXACT_BRANCH_TIP_MANIFEST_END")
    return "\n".join(lines) + "\n"


def check_archive(archive_sha, manifest):
    actual = git("show", "-s", "--format=%B", archive_sha).stdout
    if "EXACT_BRANCH_TIP_MANIFEST_BEGIN" not in actual:
        raise RuntimeError("Unexpected archive commit message")
    for branch in manifest["branches"]:
        if f"{branch['name']} {branch['sha']}" not in actual:
            raise RuntimeError("Archive commit lacks exact branch manifest: " + branch["name"])
        if not is_ancestor(branch["sha"], archive_sha):
            raise RuntimeError("Archive does not retain commit: " + branch["name"])


def main():
    manifest = json.loads(MANIFEST.read_text())
    repo = "RRain001/cufotri"
    if os.environ.get("GITHUB_REPOSITORY") != repo:
        raise RuntimeError("Unexpected GitHub repository")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("Workflow must run on main")
    mode = os.environ.get("ARCHIVE_MODE", "preview")
    event = os.environ.get("GITHUB_EVENT_NAME")
    if mode not in ("preview", "archive_delete"):
        raise RuntimeError("Unrecognized archive mode")
    if mode == "archive_delete":
        if event == "push":
            if MARKER not in os.environ.get("TRIGGER_COMMIT_TITLE", ""):
                raise RuntimeError("Archive push trigger marker missing")
            if os.environ.get("GITHUB_SHA") != ls_remote("main"):
                raise RuntimeError("Main changed since push trigger")
        elif event == "workflow_dispatch":
            if os.environ.get("ARCHIVE_CONFIRMATION") != "ARCHIVE_AND_DELETE_37_CUFOTRI":
                raise RuntimeError("Explicit confirmation required")
        else:
            raise RuntimeError("Invalid destructive trigger")
    elif event != "workflow_dispatch":
        raise RuntimeError("Preview requires manual dispatch")

    if manifest["repository"] != repo or len(manifest["branches"]) != 37:
        raise RuntimeError("Expected exact audited 37-branch manifest")
    archive_ref = manifest["archive_ref"]
    if archive_ref != "archive/unmerged-20261022":
        raise RuntimeError("Unexpected archive ref")
    branches = manifest["branches"]
    if len({b["name"] for b in branches}) != 37 or any(
        not b["name"].startswith("codex/") or len(b["sha"]) != 40
        for b in branches
    ):
        raise RuntimeError("Malformed or duplicate manifest entries")

    repo_info = get_json(f"/repos/{repo}")
    if repo_info["default_branch"] != "main":
        raise RuntimeError("Default branch changed")
    main_sha = git("rev-parse", "refs/remotes/origin/main").stdout.strip()
    if main_sha != ls_remote("main"):
        raise RuntimeError("Fetched main and live main disagree")
    if not is_ancestor(manifest["baseline_main_sha"], main_sha):
        raise RuntimeError("Audited baseline no longer an ancestor of main")

    live = {b["name"]: b for b in get_all(f"/repos/{repo}/branches")}
    open_prs = get_all(f"/repos/{repo}/pulls?state=open")
    open_heads = {p["head"]["ref"] for p in open_prs}
    report = {
        "repository": repo, "main_sha": main_sha,
        "mode": mode, "archive_ref": archive_ref,
        "planned": branches, "deleted": [], "already_removed": [],
        "failed": [], "archive_sha": None,
    }
    save(report)
    if len(live) != len(set(live)):
        raise RuntimeError("Duplicate branches from API")
    old_archive_sha = ls_remote(archive_ref)
    if old_archive_sha:
        git("fetch", "--no-tags", "origin",
            f"+refs/heads/{archive_ref}:refs/remotes/origin/{archive_ref}")
        check_archive(old_archive_sha, manifest)

    for entry in branches:
        name, sha = entry["name"], entry["sha"]
        branch = live.get(name)
        if branch is None:
            if old_archive_sha:
                report["already_removed"].append(entry)
            else:
                raise RuntimeError("Missing unarchived branch: " + name)
            continue
        if branch["commit"]["sha"] != sha:
            raise RuntimeError("Unexpected branch SHA: " + name)
        if branch.get("protected") or name in open_heads:
            raise RuntimeError("Protected or active PR branch: " + name)
        local_sha = git("rev-parse", f"refs/remotes/origin/{name}").stdout.strip()
        if local_sha != sha:
            raise RuntimeError("Fetched ref differs from live GitHub: " + name)
        if not is_ancestor(manifest["baseline_main_sha"], main_sha):
            raise RuntimeError("Baseline check changed")
        if git("cat-file", "-t", sha).stdout.strip() != "commit":
            raise RuntimeError("Ref is not a commit: " + name)

    if mode == "preview":
        print(f"Preview: {len(branches)} approved names, "
              f"{len({x['sha'] for x in branches})} unique commit tips; "
              f"archive exists={bool(old_archive_sha)}.")
        return

    if old_archive_sha:
        archive_sha = old_archive_sha
    else:
        # Construct one history-only archival commit. Its tree is exactly main's.
        distinct_tips = sorted({entry["sha"] for entry in branches})
        parents = []
        for tip in [main_sha, *distinct_tips]:
            if tip not in parents:
                parents.extend(["-p", tip])
        message = archive_message(manifest)
        if commit.returncode != 0:
            raise RuntimeError("Cannot build archival commit: " + commit.stderr)
        commit = git(
            "commit-tree", git("rev-parse", f"{main_sha}^{{tree}}").stdout.strip(),
            *parents, "-m", message,
            env={
                "GIT_AUTHOR_NAME": "CUFOTRI History Archive",
                "GIT_AUTHOR_EMAIL": "92715132+RRain001@users.noreply.github.com",
                "GIT_COMMITTER_NAME": "CUFOTRI History Archive",
                "GIT_COMMITTER_EMAIL": "92715132+RRain001@users.noreply.github.com",
            },
        )
        archive_sha = commit.stdout.strip()
        check_archive(archive_sha, manifest)
        created = git(
            "push", "--porcelain",
            f"--force-with-lease=refs/heads/{archive_ref}:",
            "origin", f"{archive_sha}:refs/heads/{archive_ref}",
            check=False,
        )
        if created.returncode != 0:
            raise RuntimeError("Cannot push archival ref: " + created.stderr)
        if ls_remote(archive_ref) != archive_sha:
            raise RuntimeError("Archive SHA mismatched after push")
        git("fetch", "--no-tags", "origin",
            f"+refs/heads/{archive_ref}:refs/remotes/origin/{archive_ref}")
        check_archive(archive_sha, manifest)

    report["archive_sha"] = archive_sha
    save(report)
    print("Verified durable archive:", archive_ref, archive_sha)
    if ls_remote("main") != main_sha:
        raise RuntimeError("main advanced, aborting deletion")

    for entry in branches:
        if entry in report["already_removed"]:
            continue
        name, expected_sha = entry["name"], entry["sha"]
        if not is_ancestor(expected_sha, archive_sha):
            raise RuntimeError("History no longer retained in archive")
        result = git(
            "push", "--porcelain",
            f"--force-with-lease=refs/heads/{name}:{expected_sha}",
            "origin", f":refs/heads/{name}", check=False,
        )
        if result.returncode == 0:
            report["deleted"].append(entry)
        else:
            report["failed"].append({
                **entry, "error": (result.stderr or result.stdout)[-1500:]
            })
            save(report)
            break
        save(report)

    remaining = {b["name"] for b in get_all(f"/repos/{repo}/branches")}
    report["remaining_branches"] = sorted(remaining)
    save(report)
    print("Deleted:", len(report["deleted"]))
    print("Already removed:", len(report["already_removed"]))
    print("Remaining:", ", ".join(sorted(remaining)))
    if report["failed"] or any(x["name"] in remaining for x in branches):
        raise RuntimeError("Some original branches remain; see JSON report")
    if archive_ref not in remaining or "main" not in remaining:
        raise RuntimeError("Main or archive disappeared unexpectedly")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ARCHIVE_ERROR:", exc, file=sys.stderr)
        raise
