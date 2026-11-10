---
name: reproduce
description: Reproduce a bug before any plan is written. Checks whether it was worked on before, replays it step by step on the current default branch (in the UI first, the terminal otherwise), saves the before screenshots and logs, turns it into a failing test and names the root cause. When it will not reproduce, says briefly why and how to get unblocked. Use when blueprint reaches its reproduce step, or when the user says to reproduce a bug, or that a bug is back, reopened or a repeat.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# reproduce

See the bug with your own eyes, and keep the proof. A bug that has not happened in front of you is not reproduced, and nothing gets planned on it. The before screenshots taken here are shown next to the after screenshots in the PR and in Jira, so both must come from the same steps.

Read `~/.agents/skills/blueprint/references/conventions.md` first. If `blueprint` called you, the ticket file, the worktrees and the baseline already exist. If the user called you alone, run `blueprint` steps 1 to 4 first, then continue here, and hand back to `blueprint` step 6 when you finish.

Update the `repro` row of the progress board after each step.

## 1. Write the repro steps

Read the ticket, its comments and attachments, and the chat. Write `.scratch/<KEY>-repro.md`. Its first line is the result, `Reproduced: not yet` for now. Steps 3 and 4 set it to `yes`, `no` or `already fixed`.

```
Reproduced: not yet
Live environment: <lane number and commits, or how the app was run>
Where: <lane URL, page or command>   Account and data: <role, fixture, file>
| # | Action | Expected (correct behavior, with its source) | What the report says happens | Proof file name |
```

Number the proof file names (`01-open-course.png`, `02-save-error.png`). The after proof reuses the same names. If the ticket shows UI screenshots, the steps go through the UI and the proof is UI screenshots of the same screens.

Done when a person could follow the steps without reading the ticket.

## 2. Check the history

Look for earlier work on this problem.

- Jira, in the main chat: issue links on the ticket (relates, clones, duplicates), tickets in the same epic or with a similar summary (`text ~ "<key words>"`) resolved in the last 12 months, and for each old ticket its description, comments, fix version and who worked on it.
- GitHub, git and local files, by one read-only sub-agent that writes `.scratch/<KEY>-history-repos.md` and replies in 40 lines or fewer: PRs that mention the old key, their changed files, review comments and failed checks, other PRs that changed the same files since, `git log --oneline` on those files since the old fix merged, and `<root>/archived-worktrees/<old key>/archive.md`.

Merge both into `.scratch/<KEY>-history.md`. With no earlier work, write "No earlier work found" and what you searched.

When earlier work exists, this is a repeat bug. Pick one verdict and give the evidence in 3 lines or fewer: old fix incomplete, a later change broke it, different root cause, or never really fixed. If the old and new tickets have no link, add "Relates" with `createIssueLink`. If the old PR is still open, reuse its branch and rebase only after asking. If it is merged or closed, keep the new branch.

Done when `<KEY>-history.md` exists.

## 3. Reproduce it live, step by step

Reproduce in the live environment only: a running copy of the app, started from the current default branch. For Aruva that is a `lane`. For other apps, run the app from the worktree. Follow `<KEY>-repro.md` one step at a time and check each step's result before taking the next. Write the environment on the second line of `<KEY>-repro.md`, for example `Live environment: lane 2 from uok-be abc1234, uok-fe def5678`.

- **UI first.** For Aruva use the `lane` skill: claim a lane built from the worktrees and drive the real UI. For other apps use the browser tools from the conventions file. You may use the user's computer and terminal freely for this.
- **Terminal otherwise.** When the bug has no screen (API, worker, CLI, data), reproduce it with real calls and commands against that same running app.
- If an old regression test exists, run it and say why it did not catch this case.

Try up to 3 different approaches or 30 minutes: another account or role, other data or file, another route to the same screen, a different browser, the exact commit the report names. Correct `<KEY>-repro.md` whenever the real steps differ from the report.

Only the live environment counts. The wrong behavior must happen in front of you in the running app. The ticket text, a reading of the code, a unit test, a mock and a static check never make it reproduced, and neither does production. If the live environment cannot be started (a lane will not come up, a key or service is missing), the result is `Reproduced: no` with that blocker as the reason. Never fall back to reading the code.

Done when `Reproduced: yes` is written because the wrong behavior happened in front of you on the current default branch, or the timebox ran out and you go to step 4.

## 4. If it will not reproduce

Set the first line of `<KEY>-repro.md` to `Reproduced: no`, or `Reproduced: already fixed` when the current code is fine and the history names the PR or commit that fixed it. Save what you tried under `before/` anyway (screenshots of the screen as it behaves now, logs), close every window and tab, and give the lane back.

Write a short report, 8 lines or fewer, in plain words. Post it in chat and save it at the end of `<KEY>-repro.md`:

```
Could not reproduce <KEY>

What I tried: <the steps, where (environment and commit), which account and data, and the approaches>
What happened: <what I saw instead, with the proof file or log>
Why I think it did not reproduce: <one reason from the list below, with the evidence>
How we can reproduce it: <the smallest thing that would unblock it, and who can give it>
```

Pick the most likely reason, and say plainly when you are not sure:

| Reason | How we can reproduce it |
|---|---|
| The report is missing steps or data (which screen, which account, which file) | The reporter gives exact steps, a screen recording or the file |
| It needs an account, role, file or data I do not have | Someone provides it, or I create the data if you say how |
| The environment differs: a setting, a feature flag, a version, or a service key that is not available locally (name it) | A working key or setting, or a run on the environment where it was seen |
| It depends on timing, load or order and happens only sometimes | A log or request id from a real failure, then a run that repeats the same order |
| It is already fixed on the current branch (name the PR or commit) | Confirm with the reporter, then close the ticket |
| I could not run the app here (name what blocked it) | Fix that blocker, then run it again |

Reply to the caller with `Reproduced: no` or `already fixed` and the report. Never guess a root cause, never invent steps that happened, and never write a plan.

## 5. Save the before proof

Save into `.scratch/<KEY>-evidence/before/`, using the file names from `<KEY>-repro.md`:

- A screenshot for every step. UI screenshots whenever the bug shows in the UI. A terminal screenshot or a saved transcript is extra proof, never a replacement for a UI screenshot.
- The logs for the failing action: backend and AI logs (`lane logs N <service>`), the browser console and the failed network request, saved as `.txt`.
- `commit.txt` with the commit of each repo the app was built from.

Strip tokens, secrets and personal data. Then close every browser window and tab you opened, and give the lane back with `lane down N`.

Done when every step in `<KEY>-repro.md` has its proof file and no window or lane is left open.

## 6. Turn it into a failing test

Use the `tdd` skill to write an automated test that fails for the same reason. Extend the old regression test where one exists. Commit it locally as `<KEY>: add failing test that reproduces the bug`. Never push it. If the repo has no test setup, save a script that reproduces the bug under `.scratch/<KEY>-reviews/`.

Done when the test or script goes red on the bug.

## 7. Name the root cause and report

Use the `diagnosing-bugs` skill to find the cause. Add to `<KEY>-repro.md`: the root cause with `file:line`, the failing test path, and for a repeat bug the verdict from step 2.

Set the first line of `<KEY>-repro.md` to `Reproduced: yes`. Reply to the caller with: `Reproduced: yes`, the root cause in 2 lines, the proof folder, and "This is a repeat of <old key>" when it is one. `blueprint` then fills the plan's Reproduction, Previous attempt and Why it came back sections from these files.

## Never

- Never report `Reproduced: yes` from the ticket text, the code or a unit test alone. It must have happened in the live environment.
- Never let the caller plan a bug that did not reproduce. Report `no` or `already fixed` with the reason.
- Never keep a terminal screenshot as the only proof of a UI bug.
- Never leave a browser window, tab or lane open.
- Never push in this skill.
