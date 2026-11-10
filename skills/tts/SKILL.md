---
name: tts
description: Time to ship. Builds a planned task in its worktree with parallel sub-agents, calls ttq and loops on fixes until both are satisfied, captures the after proof with ttl, opens the PR and updates Jira with before and after screenshots, then watches the PR until it is merged. Use when the user types tts, when ttp hands off, or to build and ship a ticket or request. Plans first with ttp when no plan exists.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# tts (time to ship)

Turn a plan into a merged-quality PR. Work only inside the task's worktree. The user's message outranks everything here (see "Your message comes first" in the conventions file).

First read `~/.agents/skills/ttp/references/conventions.md`. Read `~/.agents/skills/ttq/SKILL.md` before step 4, and `references/closeout.md` before step 6. If you are not Claude Code inside T3, read the "Using these skills from another agent" table and swap the tools as it says.

Keep the user informed as the Progress board section of the conventions file says. Before each piece of work, record what you are fixing and why with `progress.py now`. Post an update (the table plus a few simple sentences: this part is fixed, this is why, now I am fixing that) whenever `progress.py due <KEY>` says "due".

## 0. Get ready

1. Take the key from the call or from the chat. No key and plain instructions means standalone mode.
2. Look for `.scratch/<KEY>-ticket.md`, `-plan.md`, `-decisions.md`, `-repro.md`, `-timeline.md`, the `before/` proof and the worktree.
   - All present: this ran after `ttp`. Reuse them.
   - Plan missing: read `~/.agents/skills/ttp/SKILL.md` and run it for this key up to the end of its step 8, then continue here.
   - Worktree archived: recreate it from the branch with `git worktree add <path> <branch>`.
3. Check the plan against the requirement documents and the knowledge file. A plan written before a requirement changed is replanned first.
4. Recap the plan in about 5 lines, then start building at once.

"just tts" means build only: stop after step 3 and say that QA, proof and the PR were skipped.

Done when the plan, the decision log, the before proof and the worktree are all in place.

## 1. Build

Every builder works in the same worktree, so the briefs keep them apart.

1. Read the plan's Subparts table. Order the subparts by dependency into batches. Subparts in one batch own separate files and run in parallel.
2. Start one builder per subpart, as the Agents section of the conventions file says. Each brief is clear and complete on its own:
   - the worktree path, the plan path and the decision log path
   - the subpart id, what it must do, the files it owns, and the test that must pass
   - the checklist lines it covers
   - the do-not-touch list
   - "Edit only your files. Do not commit or push. Do not run installs. If the plan is unclear or wrong, stop and say so instead of guessing. Report the files you changed and the test result in under 15 lines."
3. End the turn. The completions wake the chat.
4. After each batch, in the main chat:
   - `git -C <wt> status --porcelain`. Every changed file must belong to a subpart in this batch. Revert or ask about anything else.
   - Run the tests the subparts name.
   - Commit one subpart at a time with the identity from the conventions file. Message: `<KEY>: <what changed>`.
   - Tick "built" on the checklist lines that batch covers.
5. Check the overrun rule at every batch boundary. Replace a failed builder once, then ask.

Done when every subpart is committed and every checklist line is ticked "built".

## 2. Re-check the bug

For a bug, run the repro test or script again. It must now pass. If it still fails, the build is not done. Go back to the plan, not to a guess.

## 3. Prove nothing else broke

Run the baseline commands again. Every command must do at least as well as the baseline, with no new failures. Then check scope:

- `git -C <wt> diff --name-only origin/<default branch>...HEAD` lists only files the plan lists, plus the repro test.
- Any extra file needs a written reason in the plan or gets reverted.
- Lockfiles, dependency files, CI config and anything on the do-not-touch list stay unchanged unless a subpart lists them.

## 4. ttq, and the loop

Follow `~/.agents/skills/ttq/SKILL.md` in pipeline mode. It runs the four code reviewers, the live run and the QA validation, and returns a score, a verdict and the findings.

`tts` and `ttq` are both satisfied only when all of these hold on the current commit:

- combined score 100, with postwork PASS
- live run PASS with proof for every step
- QA verdict Done or Done with notes
- every checklist line ticked "verified"

Anything less is a failed round:

1. Write the phase 2 plan from the findings, as `ttq/references/review-loop.md` says, and show it in chat.
2. Start a fresh builder per independent group of findings.
3. Run steps 2 and 3 again, commit the fixes, and run `ttq` again on the new commit.

Round limits, the stuck rule and the diagnosis are in the same file. "Needs BA input" stops the work and shows the question.

Done when all four conditions hold on one commit.

## 5. After proof with ttl

Run this on the final commit, after the loop ends.

1. Follow `<KEY>-repro.md` exactly as `bug-reproduced` did, in the same place and with the same account and data. For Aruva use the `ttl` skill.
2. Save a proof file for every step into `.scratch/<KEY>-evidence/after/`, with the same file names as in `before/`. UI screenshots wherever the before proof is a UI screenshot. Save the logs for the same action, now clean.
3. Write `.scratch/<KEY>-evidence/before-after.md`: one row per step with the before image, the after image and a one-line caption.
4. Close every window and tab you opened, and give the lane back.

The after shots `ttq` saved during its live run count, when they were taken on this same commit and cover every step.

Done when every file in `before/` has a file of the same name in `after/`, and the table shows them side by side.

## 6. Close out

Follow `references/closeout.md`. It ends only when the PR is merged. In order: publish the proof, push, open the PR with the before and after table, comment in Jira with the same proof and attach the screenshots, archive and delete the worktree, hand the PR to `babysit-pr` (fix CI, resolve every comment), move the ticket to Code Review and log work, then stay until it merges. Keep Jira current at each milestone.

## Never

- Never skip the requirement documents. Re-check them when the loop is stuck.
- Never let a sub-agent commit or push.
- Never edit outside the plan's files without a written reason.
- Never run a bigger model without a card.
- Never call the work done below 100, or without a live run PASS on the current commit.
- Never open a PR or update Jira without before and after proof.
- Never merge the PR yourself.
- Never poll an agent. Watch PRs only the way `babysit-pr` says.
- Never end the chat's work before the PR is merged, unless the user stopped it.
