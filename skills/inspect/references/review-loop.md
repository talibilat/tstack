# Review loop

The four code reviewers, the score, the QA validation child and the fix rounds. `inspect` runs the checks. `ship` makes the fixes between rounds.

## The four reviewers

| Reviewer | What the child reads and does (find each skill as the conventions file's Companion skills section says) |
|---|---|
| pstack interrogate | the `interrogate` skill from the pstack plugin. Adversarial review where every finding is proven by a command and its output. Review only. Do not fix. |
| postwork | the `postwork` skill. Reviews the change against `<KEY>-ticket.md`. Use the plain `postwork`, not `ticket-postwork-review`. |
| ponytail-review | the `ponytail-review` skill. Correctness, safety, load, tests, speed and lean code. |
| thermo-nuclear | the `thermo-nuclear-code-quality-review` skill. Strict maintainability review. |

## Start a round

Start the reviewers of the round together with `delegate_task`, role `review`, at the same moment as the live run. Round 1 runs all four. Later rounds run only the reviewers that still have open findings. When those pass, run one last pass with all four.

Target: Cursor `auto-smart` on `cost` first. A Cursor error or limit means run that reviewer again on Sonnet medium. See the conventions file.

Brief for every reviewer, with paths and no pasted text:

```
Review the change in <worktree path> against origin/<default branch>. Ticket: <path>. Plan: <path>. Decision log: <path>. Requirements and knowledge: <~/.agents/ticket-knowledge/<EPIC>.md>. Judge the change against the original requirements, not only the ticket.
Read <the reviewer's SKILL.md path, found as above> and follow it, with these overrides:
- Review only. Do not edit, stage, commit or push anything.
- Do not rename the chat. Do not ask the user questions.
- Do not start sub-agents. Read only the diff, the plan and the files the diff touches.
- Write your findings to <.scratch/<KEY>-reviews/<name>-r<N>.md> in this exact format, one row per finding:
  F<n> | Critical/High/Medium/Low | file:line | in-scope yes/no | claim | proof (command and output, or the exact lines) | smallest fix
- A finding with no concrete failing case or proof is not a finding. Leave it out.
- "in-scope yes" means the finding is on a changed line, or on code this change breaks.
- Reply with the file path, the number of findings, and one line for the verdict. Nothing else.
For postwork also include its score out of 100 and its PASS, PASS WITH MANUAL CHECKS or FAIL gate.
```

After the reviewers return, run `git -C <wt> status --porcelain` and compare it with the state before the round. A reviewer that edited anything is a failed reviewer. Revert its edits and run it again on Sonnet.

## Combine and score

1. Read each findings file. Merge duplicates (same file and line, or same claim) into one row and keep the strongest proof.
2. Check every merged finding yourself. Read the cited lines or re-run the proof command. Mark it verified or dropped (with the reason). Dropped findings do not cost points.
3. Findings with "in-scope no" go to a Follow-ups list. They go in the PR body, not into the fix plan, and do not cost points.
4. Score starts at 100. For each verified in-scope finding subtract 25 (Critical), 10 (High), 5 (Medium) or 2 (Low). Never go below 0.
5. 100 means no verified in-scope findings and postwork says PASS. PASS WITH MANUAL CHECKS counts as not passed until the manual checks are done and recorded. The live test is a gate, not points. Without a PASS in `<KEY>-live-test.md` for the current commit, the result is NOT PASSED, whatever the score.

Show this table in chat and append it to `.scratch/<KEY>-reviews.md`:

| Reviewer | Findings | Verified in scope | Dropped | Follow-ups | Gate |
|---|---|---|---|---|---|

Then: `Combined score: <n>/100`, the postwork score and gate on one line, and `Live test: PASS | FAIL | NOT RUN (commit <sha>)`.

## QA validation (after the code reviewers pass)

Start it only when the four code reviewers have no verified in-scope findings, postwork says PASS, and the live run passed on the current commit.

Start one `delegate_task` child (role `review`, Claude Sonnet medium). Do not send it to Cursor: it runs the app and creates test data. Brief, with paths and no pasted text:

```
Run the QA validation of the inspect skill in pipeline mode for <KEY>. Read ~/.agents/skills/inspect/SKILL.md and follow its sections 2 to 5 and its pipeline mode limits. Do not start the code reviewers or any other sub-agent.
Worktree: <path>. Ticket: <path>. Plan and its checklist: <path>. Decision log: <path>. Repro steps: <path>. Live run: <path>. Evidence folder: <path>.
Replay any repro step whose after proof is missing for this commit. Tick "verified" on each checklist line you proved, and list the lines you could not prove.
Write the full report to <.scratch/<KEY>-reviews/inspect-r<N>.md>. Reply with the TL;DR, the verdict and the failing items in 25 lines or fewer.
```

Afterward, run the same `git status --porcelain` check as for the code reviewers.

Handle the verdict:

- **Done, or Done with notes.** The QA validation passes. Notes and Low-only items go to the Follow-ups list. Add a `QA validation` row to the table with the verdict as its gate.
- **Stays open / back to dev.** Check each failing item yourself, like any finding. An AC marked Fail counts as High. A Partial AC counts as Medium. A drafted bug counts by its priority: Highest 25, High 10, Medium 5, Low 2. Verified items go into the phase 2 plan. This is a failed round. After the fix, `ship` runs its steps 2 and 3 again, then `inspect` runs the live run, the code reviewers that had findings, and the QA validation again.
- **Needs BA input.** Stop. Show the ambiguous or conflicting requirement and ask the user, even in autopilot.

Bug drafts for problems outside this ticket go to the Follow-ups list and the final message. Never file them in Jira from the loop. Offer to file them, and file only after the user confirms.

## Phase 2 plan (every round below 100)

Show a short plan in chat before touching code:

| Finding | Fix | Files | Owner subpart |
|---|---|---|---|

`ship` starts a fresh builder per independent group of findings (Sonnet medium). The brief is the finding rows plus the worktree path. Then it runs its steps 2 and 3 again (re-check the bug, baseline and scope), commits the fixes as `<KEY>: <what changed>`, and calls `inspect` for the next round, which starts with a fresh live run on the new commit.

## Round limits

Up to 5 rounds run without asking the user, as long as each round moves in the right direction. Moving in the right direction means the score goes up, or the open findings are new ones and fewer than before.

- Round 1 fails: phase 2 plan, fix, round 2.
- Round 2 fails: stop fixing. Write the diagnosis, then correct the plan.
  - Do the same findings come back, or new ones each time?
  - Is the plan wrong, is the ticket unclear, or is a fix aimed at a symptom?
  - Did the requirement documents say something the plan missed?
  - Is a reviewer demanding something outside the ticket?
  - Which single change removes the cause?

  Show the diagnosis in 6 lines or fewer, then run the next round with the corrected plan.
- Rounds 3 to 5: fix, re-run, and diagnose again after each failure.
- Stuck means any of these: the same finding comes back after two fixes, the score has not gone up for two rounds in a row, a fix breaks something an earlier round fixed, or round 5 fails. When stuck, stop and show the diagnosis and a card: "Re-plan", "Ship with follow-ups", "I'll take over". Wait for the answer.

Append each round's diagnosis and result to `<KEY>-reviews.md`.
