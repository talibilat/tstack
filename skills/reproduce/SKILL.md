---
name: reproduce
description: Reproduce a bug before any plan is written. Checks whether it was worked on before, replays it step by step on the current default branch (in the UI first, the terminal otherwise), saves the before screenshots and logs, turns it into a failing test and names the root cause. Use when blueprint reaches its reproduce step, or when the user says to reproduce a bug, or that a bug is back, reopened or a repeat.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# reproduce

See the bug with your own eyes, and keep the proof. The before screenshots taken here are shown next to the after screenshots in the PR and in Jira, so both must come from the same steps.

Read `~/.agents/skills/blueprint/references/conventions.md` first. If `blueprint` called you, the ticket file, the worktrees and the baseline already exist. If the user called you alone, run `blueprint` steps 1 to 4 first, then continue here, and hand back to `blueprint` step 6 when you finish.

Update the `repro` row of the progress board after each step.

## 1. Write the repro steps

Read the ticket, its comments and attachments, and the chat. Write `.scratch/<KEY>-repro.md`:

```
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

Run the app from the current default branch and follow `<KEY>-repro.md` one step at a time. Check each step's result before taking the next.

- **UI first.** For Aruva use the `lane` skill: claim a lane built from the worktrees and drive the real UI. For other apps use the browser tools from the conventions file. You may use the user's computer and terminal freely for this.
- **Terminal otherwise.** When the bug has no screen (API, worker, CLI, data), reproduce it with real calls and commands.
- If an old regression test exists, run it and say why it did not catch this case.

Timebox: 30 minutes or 3 different approaches, then show the "Repro stuck" card from the `blueprint` cards file. Correct `<KEY>-repro.md` whenever the real steps differ from the report.

Done when the wrong behavior happened in front of you, on the current default branch.

## 4. Save the before proof

Save into `.scratch/<KEY>-evidence/before/`, using the file names from `<KEY>-repro.md`:

- A screenshot for every step. UI screenshots whenever the bug shows in the UI. A terminal screenshot or a saved transcript is extra proof, never a replacement for a UI screenshot.
- The logs for the failing action: backend and AI logs (`lane logs N <service>`), the browser console and the failed network request, saved as `.txt`.
- `commit.txt` with the commit of each repo the app was built from.

Strip tokens, secrets and personal data. Then close every browser window and tab you opened, and give the lane back with `lane down N`.

Done when every step in `<KEY>-repro.md` has its proof file and no window or lane is left open.

## 5. Turn it into a failing test

Use the `tdd` skill to write an automated test that fails for the same reason. Extend the old regression test where one exists. Commit it locally as `<KEY>: add failing test that reproduces the bug`. Never push it. If the repo has no test setup, save a script that reproduces the bug under `.scratch/<KEY>-reviews/`.

Done when the test or script goes red on the bug.

## 6. Name the root cause and report

Use the `diagnosing-bugs` skill to find the cause. Add to `<KEY>-repro.md`: the root cause with `file:line`, the failing test path, and for a repeat bug the verdict from step 2.

Reply to the caller with: reproduced yes or no, the root cause in 2 lines, the proof folder, and "This is a repeat of <old key>" when it is one. `blueprint` then fills the plan's Reproduction, Previous attempt and Why it came back sections from these files.

## Never

- Never write a plan before the bug reproduces on the current default branch.
- Never keep a terminal screenshot as the only proof of a UI bug.
- Never leave a browser window, tab or lane open.
- Never push in this skill.
