---
name: babysit-pr
description: Watches a pull request through CI and review until it is merged. Fixes failed checks, answers and resolves every review comment, and keeps the branch up to date. Use when the user says "babysit", asks to watch, monitor or check a PR, or when tts close-out reaches the PR watch.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# babysit-pr

Stay with a PR until it is merged. Review bots and people both leave useful comments, and both can be wrong, so check each one against the code before you change anything.

Input: a PR link or number. Read `~/.agents/skills/ttp/references/conventions.md` for the git identity, the Jira rules and the evidence rules.

## 1. Look at the PR now

```
python3 -I ~/.agents/skills/tts/scripts/pr-status.py <org>/<repo> <number> --state .scratch/<KEY>-pr-<repo>.json
```

It makes one call and prints about 1 KB of JSON: PR state, CI result, review decision, open threads, new comments since the last check, what to do next, and when to check again. Act on `next`. With several PRs, run it once per PR.

## 2. Wait without wasting tokens

One watcher per PR. Never write a `sleep` loop, a polling loop or `gh --watch`.

- In T3, handle what is already there, then call `watch_pull_request` and end the turn. It wakes the chat on a failed check, green checks, a review, a comment or a conflict. Only the chat that owns the PR watches it. A sub-agent never does.
- In another agent with a scheduler, schedule the status script at `check_again_in_minutes`: 10 while CI runs or anything is open, 60 once CI is green and nothing is open. With no scheduler, tell the user to say "check the PR".
- A wake where `next` starts with "wait" needs no chat message. End the turn.
- Open PR pages, full logs or comment threads only when `next` points to them.

## 3. Fix failed checks

Read only the failing job: `gh run view <id> --log-failed | tail -80`. Tell a real failure from a flaky runner. Fix real ones with the `fix-ci` skill, or by hand without it. Recreate the worktree from the branch if it is gone.

## 4. Answer every comment

For every item in `unresolved_threads` and `new_activity`, from a bot or a person, and only for comments newer than the last push:

1. Read the comment and the lines around it. Check the claim against the code.
2. Decide. Fix it when it is right. Answer with a reason when it is wrong or outside the ticket. Ask the user only when it asks for something outside the ticket, contradicts the plan, or needs a product decision. A product decision goes to the BA's words in Jira.
3. To fix: make the change, run the baseline commands, and run the live steps the change touches. Save fresh proof and add it to the evidence branch. Commit `<KEY>: address review comment (<short>)` and push. If the fix changes more than 50 lines or adds files, run `ttq` again.
4. Reply on the thread with the commit and what changed, or with the reason. Then resolve it:

   ```
   gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id=<thread_id>
   ```

   Plain PR comments and review bodies get a reply with `gh pr comment`.
5. Run the status script again.

Keep the PR the size the ticket needs. Review loops grow a PR one small fix at a time. Fix real bugs in the intended case. Decline extra tests, guards for cases that cannot happen and unrelated cleanups with a written reason, and list them as follow-ups.

Done when `unresolved_count` is 0 and nothing new is waiting.

## 5. Keep the branch up to date

When the status shows a conflict or a branch that is behind, rebase onto the fresh default branch, run the checks, and push with `--force-with-lease` against the head you saw before the rebase. This is the only force-push allowed. If another PR already solved the same problem, stop, tell the user, and ask before closing anything. For a PR that has sat for weeks, use the `modernize` skill first.

## 6. Stay until merged

The PR is good when CI passed, there are no conflicts, `unresolved_count` is 0 and no new comment is unhandled. Tell the caller (`tts` then moves the ticket to Code Review and logs work), and keep watching.

- A new comment, a failed check or a conflict: go back to the matching step.
- Approved but not merged: wait. Never merge the PR yourself, unless the user asked for the merge in clear words and the repo's rules allow it. Right before such a merge, fetch and check that the branch is up to date and green.
- `state` is MERGED: call `unwatch_pull_request`, post the Jira update, and tell the user.
- `state` is CLOSED without a merge: report it and ask what to do next.

When you stop for any other reason (blocked, or waiting on the user), call `unwatch_pull_request` first, so the chat shows that it needs attention.
