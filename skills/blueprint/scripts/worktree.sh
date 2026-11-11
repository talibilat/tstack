#!/usr/bin/env bash
# worktree.sh: one folder per task, one worktree per repo inside it.
#
#   <root>/worktrees/<KEY>/fe   <root>/worktrees/<KEY>/be   <root>/worktrees/<KEY>/ai ...
#
#   worktree.sh add     <root> <KEY> <short> <repo-path> <branch> [<base-branch>]
#       make <root>/worktrees/<KEY>/<short> on <branch> (new from origin/<base>, or the existing branch)
#   worktree.sh list    <root> <KEY>
#       show every worktree of the task: branch, clean or dirty, commits not pushed
#   worktree.sh archive <root> <KEY> [--merged] [--scratch <dir>]
#       move the whole task folder to <root>/archived-worktrees/<KEY>. Refuses when a worktree
#       has uncommitted changes or unpushed commits. --merged means the PR is merged, so the
#       pushed check is skipped (the branch may be deleted on origin). --scratch copies the
#       task files (<dir>/<KEY>-*) into the archive.
#
# Never uses git stash, rm or a force flag. Each worktree is moved with `git worktree move`, so git
# keeps tracking it.
set -u

die() { echo "$*" >&2; exit 1; }

default_branch() {
  local b
  b=$(git -C "$1" symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
  for c in "$b" dev main; do
    [ -n "$c" ] && git -C "$1" rev-parse -q --verify "refs/remotes/origin/$c" >/dev/null && { echo "$c"; return; }
  done
}

main_repo() {
  local common
  common=$(git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  dirname "$common"
}

is_worktree() { [ -e "$1/.git" ]; }

cmd=${1:-help}
[ $# -gt 0 ] && shift
case "$cmd" in
  add)
    [ $# -ge 5 ] || die "usage: worktree.sh add <root> <KEY> <short> <repo-path> <branch> [<base-branch>]"
    root=$1 key=$2 short=$3 repo=$4 branch=$5
    dest="$root/worktrees/$key/$short"
    if [ -e "$dest" ]; then
      echo "already there: $dest (branch $(git -C "$dest" branch --show-current 2>/dev/null))"
      exit 0
    fi
    git -C "$repo" rev-parse --git-dir >/dev/null 2>&1 || die "not a git repo: $repo"
    git -C "$repo" fetch -q origin || die "fetch failed in $repo"
    base=${6:-$(default_branch "$repo")}
    [ -n "$base" ] || die "no origin/dev or origin/main in $repo"
    mkdir -p "$root/worktrees/$key"
    if git -C "$repo" show-ref -q --verify "refs/heads/$branch"; then
      git -C "$repo" worktree add -q "$dest" "$branch" || die "could not add $dest on $branch"
    else
      git -C "$repo" worktree add -q -b "$branch" "$dest" "origin/$base" || die "could not add $dest from origin/$base"
    fi
    echo "created $dest on $branch from origin/$base"
    ;;

  list)
    [ $# -ge 2 ] || die "usage: worktree.sh list <root> <KEY>"
    folder="$1/worktrees/$2"
    [ -d "$folder" ] || die "no task folder at $folder"
    found=0
    for wt in "$folder"/*/; do
      wt=${wt%/}
      is_worktree "$wt" || continue
      found=1
      branch=$(git -C "$wt" branch --show-current)
      state=clean; [ -n "$(git -C "$wt" status --porcelain)" ] && state=dirty
      unpushed="no remote branch"
      git -C "$wt" rev-parse -q --verify "refs/remotes/origin/$branch" >/dev/null && unpushed="$(git -C "$wt" rev-list --count "origin/$branch..HEAD") unpushed"
      echo "$(basename "$wt")  $branch  $state  $unpushed  $(git -C "$wt" rev-parse --short HEAD)"
    done
    [ "$found" -eq 1 ] || echo "no worktrees in $folder yet"
    ;;

  archive)
    [ $# -ge 2 ] || die "usage: worktree.sh archive <root> <KEY> [--merged] [--scratch <dir>]"
    root=$1 key=$2
    shift 2
    merged=0 scratch=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --merged) merged=1 ;;
        --scratch) scratch=${2:-}; shift ;;
        *) die "unknown option: $1" ;;
      esac
      shift
    done
    folder="$root/worktrees/$key"
    [ -d "$folder" ] || die "no task folder at $folder"
    problems=0
    for wt in "$folder"/*/; do
      wt=${wt%/}
      is_worktree "$wt" || continue
      case "$(basename "$wt")" in _*) continue ;; esac
      name=$(basename "$wt")
      git -C "$wt" fetch -q origin --prune 2>/dev/null
      if [ -n "$(git -C "$wt" status --porcelain)" ]; then
        echo "$name: has uncommitted changes. Commit or ask the user first"
        problems=1
      fi
      if [ "$merged" -eq 0 ]; then
        branch=$(git -C "$wt" branch --show-current)
        if ! git -C "$wt" rev-parse -q --verify "refs/remotes/origin/$branch" >/dev/null; then
          echo "$name: branch $branch is not on origin"
          problems=1
        elif [ "$(git -C "$wt" rev-list --count "origin/$branch..HEAD")" -gt 0 ]; then
          echo "$name: has commits that are not pushed"
          problems=1
        fi
      fi
    done
    [ "$problems" -eq 0 ] || die "nothing was moved. Fix the lines above, then run archive again"

    dest="$root/archived-worktrees/$key"
    [ -e "$dest" ] && dest="$dest-$(date +%Y%m%d%H%M%S)"
    mkdir -p "$dest"
    notes="$dest/archive.md"
    { echo "# $key archive"; echo; echo "Archived: $(date -u +%FT%TZ). To work on it again, move a worktree back with the command on its line."; echo; } > "$notes"
    moved=0
    for wt in "$folder"/*/; do
      wt=${wt%/}
      is_worktree "$wt" || continue
      case "$(basename "$wt")" in _*) continue ;; esac
      name=$(basename "$wt")
      main=$(main_repo "$wt") || die "cannot find the repo of $wt"
      branch=$(git -C "$wt" branch --show-current)
      sha=$(git -C "$wt" rev-parse --short HEAD)
      git -C "$main" worktree move "$wt" "$dest/$name" || die "could not move $wt (the ones already moved are in $dest)"
      echo "- $name: repo $main, branch $branch, last commit $sha. Move back: git -C $main worktree move $dest/$name $folder/$name" >> "$notes"
      moved=$((moved + 1))
    done
    if [ -n "$scratch" ] && [ -d "$scratch" ]; then
      mkdir -p "$dest/scratch"
      for f in "$scratch/$key"-*; do [ -e "$f" ] && cp -R "$f" "$dest/scratch/"; done
      echo "- task files copied to $dest/scratch" >> "$notes"
    fi
    rmdir "$folder" 2>/dev/null || echo "left $folder in place, it still holds other files"
    echo "archived $moved worktree(s) to $dest"
    ;;

  *)
    sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'
    [ "$cmd" = help ] || exit 2
    ;;
esac
