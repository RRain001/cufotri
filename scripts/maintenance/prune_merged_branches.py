#!/usr/bin/env python3
"""Safely preview or prune remote branches whose exact tip is in main history.

Designed for the manually dispatched CUFOTRI GitHub Actions workflow.
This script never changes main, tags, protected branches, backup refs, or
branches with unmerged commits. A remote SHA lease guards every deletion.
"""
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def git(*args, check=True):
    return subprocess.run(
        ["git", *args], text=True, capture_output=True, check=check
    )


def api_get(path):
    token = os.environ["GH_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "cufotri-maintenance",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def paged(path):
    values = []
    for page in range(1, 101):
        items = api_get(path + ("&" if "?" in path else "?")
                        + f"per_page=100&page={page}")
        if not isinstance(items, list):
            raise RuntimeError(f"Unexpected GitHub response for {path}")
        values.extend(items)
        if len(items) < 100:
            return values
    raise RuntimeError(f"Pagination limit reached for {path}")


def save(report, path):
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


def summary(report):
    lines = [
        "## CUFOTRI branch cleanup",
        f"- Mode: {report['mode']}",
        f"- Baseline main: \`{report['main_sha']}\`",
        f"- Branches inspected: {report['total_branches']}",
        f"- Candidates already in main: {len(report['candidates'])}",
        f"- Unmerged branches retained: {len(report['unmerged'])}",
        f"- Special/protected/open-PR branches retained: {len(report['excluded'])}",
        f"- Successfully deleted: {len(report['deleted'])}",
        f"- Failed deletions: {len(report['failed'])}",
        "",
        "Full branch names and their exact SHAs are in the uploaded JSON report.",
    ]
    output = "\n".join(lines) + "\n"
    print(output)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(output)


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    mode = os.environ.get("CLEANUP_MODE", "preview")
    confirmation = os.environ.get("CLEANUP_CONFIRMATION", "")
    report_path = Path(os.environ.get("REPORT_PATH", "branch-cleanup-report.json"))
    if repo != "RRain001/cufotri":
        raise RuntimeError("Only RRain001/cufotri is authorized")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("Dispatch must run on main")
    if os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
        raise RuntimeError("Only manual workflow_dispatch is allowed")
    if mode not in ("preview", "delete"):
        raise RuntimeError("Invalid cleanup mode")
    if mode == "delete" and confirmation != "DELETE_MERGED_CUFOTRI_BRANCHES":
        raise RuntimeError("Deletion requires exact explicit confirmation")

    repo_info = api_get(f"/repos/{repo}")
    if repo_info.get("default_branch") != "main":
        raise RuntimeError("The default branch changed; aborting")

    main_sha = git("rev-parse", "refs/remotes/origin/main").stdout.strip()
    remote_sha = git("ls-remote", "origin", "refs/heads/main").stdout.split()[0]
    if main_sha != remote_sha:
        raise RuntimeError("main changed since fetch; aborting")

    live = paged(f"/repos/{repo}/branches")
    opened = paged(f"/repos/{repo}/pulls?state=open")
    open_pr_heads = {p["head"]["ref"] for p in opened}
    local = {}
    for line in git(
        "for-each-ref", "--format=%(refname:strip=3)\t%(objectname)",
        "refs/remotes/origin",
    ).stdout.splitlines():
        name, sha = line.split("\t", 1)
        if name != "HEAD":
            local[name] = sha

    remote = {b["name"]: b for b in live}
    if len(remote) != len(live) or set(local) != set(remote):
        raise RuntimeError("Fetched branches differ from live GitHub branches")
    for name, branch in remote.items():
        if local[name] != branch["commit"]["sha"]:
            raise RuntimeError(f"Remote branch changed since fetch: {name}")

    report = {
        "repository": repo,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "main_sha": main_sha,
        "total_branches": len(remote),
        "candidates": [],
        "unmerged": [],
        "excluded": [],
        "deleted": [],
        "failed": [],
    }
    for name, branch in sorted(remote.items()):
        sha = branch["commit"]["sha"]
        entry = {"name": name, "sha": sha}
        if name == "main" or name.startswith(("backup/", "archive/", "release/")):
            report["excluded"].append({**entry, "reason": "preserved_ref"})
        elif name in ("gh-pages",) or branch.get("protected"):
            report["excluded"].append({**entry, "reason": "protected"})
        elif name in open_pr_heads:
            report["excluded"].append({**entry, "reason": "open_pull_request"})
        else:
            result = git("merge-base", "--is-ancestor", sha, main_sha, check=False)
            if result.returncode == 0:
                report["candidates"].append(entry)
            elif result.returncode == 1:
                report["unmerged"].append(entry)
            else:
                raise RuntimeError("Ancestry check failed: " + name)

    save(report, report_path)
    if len(report["candidates"]) > 150:
        raise RuntimeError("More than 150 deletion candidates; manual re-audit required")

    if mode == "delete":
        # Stop rather than proceed with a stale snapshot.
        latest_main = git("ls-remote", "origin", "refs/heads/main").stdout.split()[0]
        if latest_main != main_sha:
            raise RuntimeError("main changed during planning; no branches deleted")
        for entry in report["candidates"]:
            name, sha = entry["name"], entry["sha"]
            operation = git(
                "push", "--porcelain",
                f"--force-with-lease=refs/heads/{name}:{sha}",
                "origin", f":refs/heads/{name}", check=False,
            )
            if operation.returncode == 0:
                report["deleted"].append(entry)
            else:
                report["failed"].append({
                    **entry,
                    "error": (operation.stderr or operation.stdout)[-1200:],
                })
            save(report, report_path)
            if operation.returncode:
                break

    summary(report)
    save(report, report_path)
    if report["failed"]:
        raise RuntimeError("Stopped after failed or stale branch deletion")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"BRANCH_CLEANUP_ERROR: {exc}", file=sys.stderr)
        raise
