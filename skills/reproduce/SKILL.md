---
name: reproduce
description: Reproduce a bug before any plan is written. Checks whether it was worked on before, replays it step by step on the current default branch (in the UI first, the terminal otherwise), saves the before screenshots and logs, turns it into a failing test and names the root cause. When it will not reproduce, says briefly why and how to get unblocked. Use when blueprint reaches its reproduce step, or when the user says to reproduce a bug, or that a bug is back, reopened or a repeat.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# reproduce

See the bug with your own eyes, and keep the proof. A bug that has not happened in front of you is not reproduced, and nothing gets planned on it. The before proof you save here is half of the before and after comparison that goes to Jira and GitHub, so it is the most important output of this skill. The before screenshots taken here are shown next to the after screenshots in the PR and in Jira, so both must come from the same steps.

Read `~/.agents/skills/blueprint/references/conventions.md` first. If `blueprint` called you, the ticket file, the worktrees and the baseline already exist. If the user called you alone, run `blueprint` steps 1 to 4 first, then continue here, and hand back to `blueprint` step 6 when you finish.

Update the `repro` row of the progress board after each step.

## 1. Write the repro steps

Read the ticket, its comments and attachments, and the chat. Write `.scratch/<KEY>-repro.md`. Its first line is the result, `Reproduced: not yet` for now. Steps 3 and 4 set it to `yes`, `no` or `already fixed`.

```
Reproduced: not yet
Live environment: <lane number and commits, or how the app was run>
Method: <visible Chrome on the lane, Docker lane, or a script because <reason>>
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

Reproduce in the live environment only: a running copy of the app. Before you start a local copy, sync every repo with dev: `~/.agents/skills/lane/scripts/sync-dev.sh <worktree> ...`. A local copy is never behind dev. A local one counts: Docker, and for Aruva a `lane` (a private Docker copy) built from the current default branch. For other apps, start the app from the worktree with its own Docker or run command. A deployed dev environment also counts when the report was made there. Follow `<KEY>-repro.md` one step at a time and check each step's result before taking the next. Write the environment on the second line of `<KEY>-repro.md`, for example `Live environment: lane 2 from uok-be abc1234, uok-fe def5678`.

**Use the real thing, where you can watch it.** Run the app in Docker (a `lane` for Aruva) and drive it in real Google Chrome on this computer, with a visible window, one step at a time, taking each screenshot as the behavior happens. `lane shot` and the flows open a visible Chrome window by default. Do not use a background or headless script or a recorded flow, unless there is no other option. In that case write the reason on the `Method:` line (`Method: headless script because <reason>`). The proof gate rejects a script method with no reason.

- **UI first.** For Aruva use the `lane` skill: claim a lane built from the worktrees and drive the real UI. For other apps use the browser tools from the conventions file. You may use the user's computer and terminal freely for this.
- **Terminal otherwise.** When the bug has no screen (API, worker, CLI, data), reproduce it with real calls and commands against that same running app.
- If an old regression test exists, run it and say why it did not catch this case.

Try up to 3 different approaches or 30 minutes: another account or role, other data or file, another route to the same screen, a different browser, the exact commit the report names. Correct `<KEY>-repro.md` whenever the real steps differ from the report.

Only the live environment counts. The wrong behavior must happen in front of you in the running app. The ticket text, a reading of the code, a unit test, a mock and a static check never make it reproduced, and neither does production (never reproduce a bug on production). If the live environment cannot be started (Docker or a lane will not come up, a key or service is missing), the result is `Reproduced: no` with that blocker as the reason. Never fall back to reading the code.

Done when `Reproduced: yes` is written because the wrong behavior happened in front of you on the current default branch, or the timebox ran out and you go to step 4.

## 4. If it will not reproduce: name the blocker, then fix it

Nothing moves forward until the bug reproduces. Do not stop at the first failure, and do not report yet. Find out what blocks you and clear it yourself. Up to 3 rounds, each one a new attempt:

1. Name the blocker in one line, from the table.
2. Do what the table says.
3. Run the steps again, in the live environment.

| Blocker | You do |
|---|---|
| Docker or the lane will not start | Start Docker (`open -a Docker`), free memory, run `lane doctor`, follow `lane/references/troubleshooting.md`, start again |
| The local copy is behind dev or on the wrong commit | Run `sync-dev.sh`, rebuild, and check out the commit the report names |
| Missing data, account or file | Create it in the live copy with the shape the report names (fixture accounts are in `lane/references/accounts.md`). For a book, first download the one attached to the Jira ticket, otherwise use the smallest file in `~/Documents/Projects/ARUVA/Data` (Nokia, Telecom, Maths and others), for testing only. If that book or course already exists in the lane, use another book or create a new course. See the Test books section in `lane` |
| The environment differs (a setting, a feature flag, a service key) | Read the settings of the environment where it was seen, copy the relevant one into the lane, or reproduce on the deployed dev environment when the report was made there |
| The steps are missing or unclear | Read every comment, attachment and video on the ticket and its parents again, search similar tickets, and try each reasonable reading of the steps |
| It happens only sometimes (timing, load, order) | Repeat the steps 10 times, change the order, double-click, slow the network, and read the backend log of the failing request |
| It needs something only the user has (a valid key, a real account, a real file) | Ask for exactly that with `request_secret` or one `AskUserQuestion`, then carry on |
| It is already fixed on current dev | Find the PR or commit (`git log -S`, search PRs) and save the evidence. Then go to the report |

When a round makes it reproduce, go on to step 5. When 3 rounds fail, or the blocker needs the user:

1. Set the first line of `<KEY>-repro.md` to `Reproduced: no` (or `already fixed`). Save what you tried under `before/`, close every window and tab, and give the lane back.
2. Post a short report in chat, 8 lines or fewer, in plain words, and save it at the end of `<KEY>-repro.md`:

   ```
   Could not reproduce <KEY>

   What I tried: <steps, environment and commit, account and data, the rounds>
   What happened: <what I saw instead, with the proof file or log>
   What is blocking it: <the blocker from the table, with the evidence>
   How we resolve it: <the smallest thing that unblocks it, and who gives it>
   ```

3. Reply to the caller with `Reproduced: no` and the report. Never guess a root cause, never invent steps that happened, and never write a plan.

## 5. Save the before proof

Save into `.scratch/<KEY>-evidence/before/`, using the file names from `<KEY>-repro.md`:

- A screenshot for every step. UI screenshots whenever the bug shows in the UI. A terminal screenshot or a saved transcript is extra proof, never a replacement for a UI screenshot.
- The logs for the failing action: backend and AI logs (`lane logs N <service>`), the browser console and the failed network request, saved as `.txt`.
- `commit.txt` with the commit of each repo the app was built from.

Save each screenshot at the moment the bug shows. Never overwrite `before/` later, because the after proof is compared against it. It lives in `.scratch/<KEY>-evidence/before/`, and stays there until the PR is merged and is then archived.

Then call the `proof` skill in `before` mode. It captures the UI first (terminal output only for a step with no UI), writes what is being looked at and what was asked for each step, and builds the picture with the before on the left and the after still empty. Pass it:

> `proof before <KEY>. Steps are in .scratch/<KEY>-repro.md. Live environment: <lane or URL>. Method: visible Chrome. Capture the UI first, and terminal output only for a step with no UI. Fill the left half only.`

Strip tokens, secrets and personal data. Close every browser window and tab you opened, and give the lane back with `lane down N`. Then run the before gate:

```
python3 -I ~/.agents/skills/blueprint/scripts/proof.py gate before <KEY>
```

It checks the result, the live environment and method lines, that every step has a real screenshot, and that the logs exist. Paste its last line in chat.

Done when the gate prints `before gate: PASS` (it includes the `proof` before check), and no window or lane is left open.

## 6. Turn it into a failing test

Use the `tdd` skill to write an automated test that fails for the same reason. Extend the old regression test where one exists. Commit it locally as `<KEY>: add failing test that reproduces the bug`. Never push it. If the repo has no test setup, save a script that reproduces the bug under `.scratch/<KEY>-reviews/`.

Done when the test or script goes red on the bug.

## 7. Name the root cause and report

Use the `diagnosing-bugs` skill to find the cause. Add to `<KEY>-repro.md`: the root cause with `file:line`, the failing test path, and for a repeat bug the verdict from step 2.

Set the first line of `<KEY>-repro.md` to `Reproduced: yes`. Reply to the caller with: `Reproduced: yes`, the root cause in 2 lines, the proof folder, and "This is a repeat of <old key>" when it is one. `blueprint` then fills the plan's Reproduction, Previous attempt and Why it came back sections from these files.

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

- Never report `Reproduced: yes` from the ticket text, the code or a unit test alone. It must have happened in the live environment.
- Never let the caller plan a bug that did not reproduce. Report `no` or `already fixed` with the reason.
- Never report `Reproduced: yes`, or move on, before `gate before` prints PASS.
- Never use a background or headless script when visible Chrome or Docker works.
- Never keep a terminal screenshot as the only proof of a UI bug.
- Never leave a browser window, tab or lane open.
- Never push in this skill.
