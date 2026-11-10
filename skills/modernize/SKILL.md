---
name: modernize
description: Brings an old pull request up to date and decides whether it should still exist. Rebases it onto the current default branch, checks what changed around it and what the ticket now says, and recommends MODERNIZE, REWORK or CLOSE. Use when the user says "modernize" or asks to rebase or revive an old PR.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# modernize

A clean rebase proves only that git is satisfied. This skill asks the bigger question first: does the product still need this PR?

Input: a PR link or number. This skill may rebase and update the PR's own branch. It never merges, closes, changes the base branch or widens the scope.

## 1. Understand what the PR was for

Read the PR: title, body, commits, the whole diff, review threads, checks, and its Jira ticket (the key is in the title or the branch name). State the smallest goal the PR was trying to reach, in 2 lines. Record the PR's head commit.

Done when you can say the goal without describing the code.

## 2. See what changed since

Fetch the latest default branch and the PR head. Work in a spare worktree when the current one has changes.

- Read the commits that landed on the default branch since the PR split off, in the files and features the PR touches.
- Search merged and open PRs for the same problem.
- Read the ticket again: its status, new comments, and anything the BA wrote since. Read the linked and newer tickets in the same epic.

Ask: Is the problem already solved? Did the APIs, types or data the PR relies on change? Was the code it edits moved, deleted or simplified on purpose? Would merging it bring back old behavior, or leave two ways to do one thing? Does the BA still want this?

Done when each question has an answer with a commit, a PR or a ticket quote behind it.

## 3. Choose before you push

| Verdict | When | What you do |
|---|---|---|
| MODERNIZE | The goal still matters and the approach still fits | Rebase, fix conflicts, test, update the branch |
| REWORK | The goal still matters, but the approach no longer fits the code | Describe the smallest rewrite. Stop, unless the user also asked for the rework |
| CLOSE | Solved elsewhere, no longer wanted, or not worth its upkeep | Give the evidence and stop. Close nothing without the user's yes |

Age alone is no reason to close, and effort already spent is no reason to keep.

## 4. Rebase (MODERNIZE only)

1. Start a branch or spare worktree at the recorded PR head.
2. Rebase onto the fresh default branch.
3. Resolve each conflict to keep what the PR intends and what the newer code requires. If a conflict shows a product disagreement, stop and go back to step 3.
4. Compare the commits before and after with `git range-diff`, and read the final diff. Nothing the PR intended has vanished, and nothing already merged has come back.
5. Run the repo's checks for the touched area. For a UI change, run the live steps and take fresh screenshots.
6. Push with `--force-with-lease` against the head you recorded. If the lease fails, someone pushed in between: fetch and look again.

## 5. Report

Lead with the verdict and the reason. Then: what changed on the default branch that matters, any conflict of ideas (or that there was none), the rebase and push result, the checks you ran, and what is left to decide, with the PR link. Keep what you saw apart from what you judge, and say what you could not check.

Hand over to `babysit` when the user wants the PR taken to merge.
