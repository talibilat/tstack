#!/usr/bin/env python3
"""Print one compact JSON summary of a pull request. Read-only.

Usage: python3 -I pr-status.py <owner/repo> <number> [--state FILE]

One GraphQL call through the `gh` CLI. With --state, the file remembers when the
PR was last checked, so "new_activity" only lists comments and reviews posted
since then by someone other than the signed-in user.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone

QUERY = """
query($o:String!,$r:String!,$n:Int!){
  viewer{login}
  repository(owner:$o,name:$r){pullRequest(number:$n){
    state isDraft mergeable reviewDecision mergedAt url
    commits(last:1){nodes{commit{oid statusCheckRollup{state contexts(first:100){nodes{
      __typename
      ... on CheckRun{name status conclusion}
      ... on StatusContext{context state}
    }}}}}}
    reviewThreads(first:100){nodes{id isResolved isOutdated path line
      comments(last:3){nodes{author{login __typename} body url createdAt}}}}
    comments(last:50){nodes{author{login __typename} body url createdAt}}
    reviews(last:50){nodes{author{login __typename} state body url submittedAt}}
  }}
}
"""

PASS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
FAIL = {"FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE", "ERROR"}


def short(text, n=240):
    return " ".join((text or "").split())[:n]


def who(author):
    a = author or {}
    return {"login": a.get("login", "ghost"), "bot": a.get("__typename") == "Bot"}


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    repo, number = args[0], int(args[1])
    state_file = args[args.index("--state") + 1] if "--state" in args else None
    owner, name = repo.split("/", 1)

    out = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"o={owner}", "-f", f"r={name}", "-F", f"n={number}"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit("gh failed: " + short(out.stderr, 400))
    data = json.loads(out.stdout)["data"]
    me = data["viewer"]["login"]
    pr = data["repository"]["pullRequest"]

    since = None
    if state_file:
        try:
            since = json.load(open(state_file)).get("checked_at")
        except (OSError, ValueError):
            pass

    commit = (pr["commits"]["nodes"] or [{}])[0].get("commit", {})
    rollup = commit.get("statusCheckRollup") or {}
    passed, pending, failed = 0, 0, []
    for c in (rollup.get("contexts") or {}).get("nodes", []):
        if c["__typename"] == "CheckRun":
            label, status, concl = c["name"], c["status"], c["conclusion"]
            if status != "COMPLETED":
                pending += 1
            elif concl in PASS:
                passed += 1
            else:
                failed.append(label)
        else:
            label, st = c["context"], c["state"]
            if st in PASS:
                passed += 1
            elif st in FAIL:
                failed.append(label)
            else:
                pending += 1

    threads = []
    for t in pr["reviewThreads"]["nodes"]:
        if t["isResolved"]:
            continue
        last = (t["comments"]["nodes"] or [{}])[-1]
        threads.append({
            "thread_id": t["id"], "where": f'{t["path"]}:{t["line"]}', "outdated": t["isOutdated"],
            "by": who(last.get("author")), "text": short(last.get("body")), "url": last.get("url"),
        })

    def newer(ts):
        return ts and (since is None or ts > since)

    new = []
    for c in pr["comments"]["nodes"]:
        if newer(c["createdAt"]) and who(c["author"])["login"] != me:
            new.append({"type": "comment", "by": who(c["author"]), "text": short(c["body"]), "url": c["url"], "at": c["createdAt"]})
    for r in pr["reviews"]["nodes"]:
        if newer(r["submittedAt"]) and who(r["author"])["login"] != me and (r["body"] or r["state"] != "COMMENTED"):
            new.append({"type": "review:" + r["state"], "by": who(r["author"]), "text": short(r["body"]), "url": r["url"], "at": r["submittedAt"]})
    new.sort(key=lambda x: x["at"])

    ci = "none" if not (passed or pending or failed) else "failed" if failed else "pending" if pending else "passed"
    if pr["state"] == "MERGED":
        nxt, minutes = "merged: stop watching and report", None
    elif pr["state"] == "CLOSED":
        nxt, minutes = "closed without merge: stop and report", None
    elif pr["mergeable"] == "CONFLICTING":
        nxt, minutes = "fix merge conflicts", 10
    elif ci == "failed":
        nxt, minutes = "fix failed checks", 10
    elif threads or new:
        nxt, minutes = "resolve every comment and thread", 10
    elif ci in ("pending", "none"):
        nxt, minutes = "wait for CI", 10
    elif pr["reviewDecision"] == "CHANGES_REQUESTED":
        nxt, minutes = "changes requested but no open thread: read the review", 10
    else:
        nxt, minutes = "CI green and nothing open: wait for approval or merge", 60

    summary = {
        "state": pr["state"], "draft": pr["isDraft"], "mergeable": pr["mergeable"], "review": pr["reviewDecision"],
        "head": (commit.get("oid") or "")[:7],
        "ci": {"status": ci, "passed": passed, "pending": pending, "failed": failed},
        "unresolved_threads": threads[:20], "unresolved_count": len(threads),
        "new_activity": new[:20], "new_count": len(new),
        "next": nxt, "check_again_in_minutes": minutes, "url": pr["url"],
    }
    print(json.dumps(summary, separators=(",", ":")))

    if state_file:
        with open(state_file, "w") as f:
            json.dump({"checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, f)


if __name__ == "__main__":
    main()
