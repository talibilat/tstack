#!/usr/bin/env bash
# sync-dev.sh <worktree>...
# Bring each worktree up to date with the default branch of origin (dev, or main),
# so a local copy of the app is never behind. Run it before every local reproduce,
# live run and lane build.
#
#   up to date             nothing to do
#   behind, clean          rebases the worktree onto origin/<default>
#   behind, uncommitted    leaves it alone and says so (exit 1)
#   rebase conflict        aborts the rebase and says so (exit 1)
#
# DEFAULT_BRANCH=<name> overrides the branch. Never uses git stash.
set -u

status=0
for wt in "$@"; do
  top=$(git -C "$wt" rev-parse --show-toplevel 2>/dev/null) || { echo "not a git folder: $wt"; status=1; continue; }
  name=$(basename "$top")
  git -C "$wt" fetch -q origin || { echo "$name: fetch failed"; status=1; continue; }

  base=${DEFAULT_BRANCH:-}
  if [ -z "$base" ]; then
    base=$(git -C "$wt" symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
  fi
  for candidate in "$base" dev main; do
    [ -n "$candidate" ] && git -C "$wt" rev-parse -q --verify "refs/remotes/origin/$candidate" >/dev/null && { base=$candidate; break; }
  done
  git -C "$wt" rev-parse -q --verify "refs/remotes/origin/$base" >/dev/null || { echo "$name: no origin/dev or origin/main found"; status=1; continue; }

  behind=$(git -C "$wt" rev-list --count "HEAD..origin/$base")
  if [ "$behind" -eq 0 ]; then
    echo "$name: up to date with origin/$base at $(git -C "$wt" rev-parse --short HEAD)"
    continue
  fi
  if [ -n "$(git -C "$wt" status --porcelain)" ]; then
    echo "$name: $behind commits behind origin/$base, but it has uncommitted changes, so I did not touch it"
    status=1
    continue
  fi
  if git -C "$wt" rebase -q "origin/$base" >/dev/null 2>&1; then
    echo "$name: was $behind commits behind origin/$base, rebased, now at $(git -C "$wt" rev-parse --short HEAD)"
  else
    git -C "$wt" rebase --abort >/dev/null 2>&1
    echo "$name: $behind commits behind origin/$base, and the rebase has conflicts. Left as it was. Ask the user."
    status=1
  fi
done
exit $status
