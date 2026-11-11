---
name: ship
description: Builds a planned task in its worktree with parallel sub-agents, calls inspect and loops on fixes until both are satisfied, captures the after proof with lane, opens the PR and updates Jira with before and after screenshots, then watches the PR until it is merged. Use when the user types ship, when blueprint hands off, or to build and ship a ticket or request. Plans first with blueprint when no plan exists.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

Be strict and vigilant. Do only what this skill says, in its order, and never step outside the system (see System rules in the conventions file).

# ship

Turn a plan into a merged-quality PR. Work only inside the task's worktree. The user's message outranks everything here (see "Your message comes first" in the conventions file).

First read `~/.agents/skills/blueprint/references/conventions.md`. Read `~/.agents/skills/inspect/SKILL.md` before step 4, and `references/closeout.md` before step 6. If you are not Claude Code inside T3, read the "Using these skills from another agent" table and swap the tools as it says.

Keep the user informed as the Progress board section of the conventions file says. Before each piece of work, record what you are fixing and why with `progress.py now`. Post an update (the table plus a few simple sentences: this part is fixed, this is why, now I am fixing that) whenever `progress.py due <KEY>` says "due".

## 0. Get ready

1. Take the key from the call or from the chat. No key and plain instructions means standalone mode.
2. Look for `.scratch/<KEY>-ticket.md`, `-plan.md`, `-decisions.md`, `-repro.md`, `-timeline.md`, the `before/` proof and the worktree.
   - All present: this ran after `blueprint`. Reuse them.
   - Plan missing: read `~/.agents/skills/blueprint/SKILL.md` and run it for this key up to the end of its step 8, then continue here.
   - The task folder `<root>/worktrees/<KEY>/` and its worktrees are what `blueprint` made. Use exactly those. Run `~/.agents/skills/blueprint/scripts/worktree.sh list <root> <KEY>`: it must show a worktree for every repo in the plan's Task folder table. Never create a worktree or a branch of your own. A repo is missing: add it with `~/.agents/skills/blueprint/scripts/worktree.sh add`, install, and run its baseline. The folder was archived: move its worktrees back with the commands in its `archive.md`.
3. For a bug, open `<KEY>-repro.md`. Its first line must be `Reproduced: yes`, its second line must name the live environment, and `before/` must hold the proof. Otherwise do not build: run `blueprint` for this key, which stops with a could-not-reproduce report when the bug will not reproduce.
4. Check the plan against the requirement documents and the knowledge file. A plan written before a requirement changed is replanned first.
5. Recap the plan in about 5 lines, then start building at once.

"build only" means build only: stop after step 3 and say that QA, proof and the PR were skipped.

Done when the plan, the decision log, the before proof and the worktree are all in place.

## 1. Build

Every builder works in the same worktree, so the briefs keep them apart.

1. Read the plan's Subparts table. Order the subparts by dependency into batches. Subparts in one batch own separate files and run in parallel.
2. Start one builder per subpart, as the Agents section of the conventions file says. Each brief is clear and complete on its own:
   - the worktree path (`<root>/worktrees/<KEY>/<short>`), the plan path and the decision log path
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

## 4. inspect, and the loop

Follow `~/.agents/skills/inspect/SKILL.md` in pipeline mode. It runs the four code reviewers, the live run and the QA validation, and returns a score, a verdict and the findings.

`ship` and `inspect` are both satisfied only when all of these hold on the current commit:

- combined score 100, with postwork PASS
- live run PASS with proof for every step
- QA verdict Done or Done with notes
- every checklist line ticked "verified"

Anything less is a failed round:

1. Write the phase 2 plan from the findings, as `inspect/references/review-loop.md` says, and show it in chat.
2. Start a fresh builder per independent group of findings.
3. Run steps 2 and 3 again, commit the fixes, and run `inspect` again on the new commit.

Round limits, the stuck rule and the diagnosis are in the same file. "Needs BA input" stops the work and shows the question.

Done when all four conditions hold on one commit.

## 5. After proof, and the comparison

Run this on the final commit, after the loop ends. The before half from `reproduce` is already on the left of each picture, so keep `before/` untouched.

1. Sync every repo with dev (`~/.agents/skills/lane/scripts/sync-dev.sh <worktree> ...`). If a worktree moved, rebuild the lane and run the baseline again.
2. Call the `proof` skill in `after` mode. It captures the same steps in the same place, with the same account, data and method, fills the right half, circles and numbers every change, writes what is being looked at and what was asked, and checks each step against the requirements. Pass it:

   > `proof after <KEY>. Same steps, same place, same account and data. Requirements: .scratch/<KEY>-plan.md checklist and .scratch/<KEY>-decisions.md. Fill the right half, circle and number every change, judge each step against what was asked, and reply COMPLETE or NOT COMPLETE with the items.`

3. Read its reply.
   - `Proof: COMPLETE`: go on.
   - `Proof: NOT COMPLETE`: the work is not finished. Treat it as a failed round. Write the phase 2 plan from the items it lists (a step that does not match is a High finding), fix the code, run steps 2 and 3 of this skill again, then call `proof after` again. Never edit a verdict to get past it.
4. Close every window and tab you opened, and give the lane back.
5. Run the after gate. It re-checks the before side, rejects an after image identical to its before image, and runs the `proof` check:

   ```
   python3 -I ~/.agents/skills/blueprint/scripts/proof.py gate after <KEY>
   ```

6. Open every picture in `compare/` and look at it: the circles sit on the real changes, the labels are readable, and the left and right show the same screen. `python3 -I ~/.agents/skills/blueprint/scripts/proof.py compare <KEY>` rebuilds them.

The after shots `inspect` saved during its live run count, when they were taken on this same commit and cover every step. `proof` still builds and checks the pictures.

Done when `gate after` prints `after gate: PASS` and every picture has been looked at.

## 6. Close out

Follow `references/closeout.md`. It ends only when the PR is merged. In order: publish the proof, push, open the PR with the before and after table, comment in Jira with the same proof and attach the screenshots, archive and delete the worktree, hand the PR to `babysit` (fix CI, resolve every comment), move the ticket to Code Review and log work, then stay until it merges. Keep Jira current at each milestone.

## The annotated pair

The before and after pictures are built by the `proof` skill: before on the left, after on the right, every change circled and numbered, what is being looked at and what was asked written on the picture, and a verdict against the requirements. `reproduce` calls it in `before` mode (left half only) and `ship` and `inspect` call it in `after` mode. See `proof` for the tool and the prompts.

## Proof gate, no exceptions

No PR, no Jira comment, no Jira attachment and no ticket move until the before and after screenshots exist, are real, and show the fix. "Real" means:

1. Every step has a `before/` and an `after/` screenshot of the live app (UI whenever the bug shows in the UI). Logs, transcripts and text are extra, never a replacement.
2. `proof.py gate before` and `gate after` both print PASS. The gate fully decodes each image, rejects blank, tiny or corrupt files and files that are not PNG, JPEG or WebP.
3. Open every image yourself (Read it) and check it shows the right screen, the bug on the before side, and the fixed behavior on the after side. A page that only shows a login, an error page, a blank screen or the wrong course is not proof. Retake it.
4. After you upload to GitHub or Jira, download or open the uploaded image and check it renders. A broken image link or a corrupted upload counts as not published. Fix it, then re-check.
5. If you cannot produce the screenshots (lane will not start, key invalid, blocked), stop and tell the user why. Do not open the PR or comment on Jira without them. Only the user can waive this, by saying "skip proof" in the call.

## Never

- Never skip the requirement documents. Re-check them when the loop is stuck.
- Never create a worktree or a branch. Work only in the task folder `blueprint` made.
- Never let a sub-agent commit or push.
- Never edit outside the plan's files without a written reason.
- Never run a bigger model without a card.
- Never call the work done below 100, or without a live run PASS on the current commit.
- Never open a PR or update Jira without the before and after comparison. Only the user can waive it, by saying "skip proof" in the call.
- Never merge the PR yourself.
- Never poll an agent. Watch PRs only the way `babysit` says.
- Never end the chat's work before the PR is merged, unless the user stopped it.
