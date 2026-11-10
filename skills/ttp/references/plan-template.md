# Plan template and the simple explanation

The plan lives in `.scratch/<KEY>-plan.md`. The same text is shown in chat. Blockers go first, before everything else. The decision log lives beside it in `.scratch/<KEY>-decisions.md`, with the layout in `requirements.md`.

## Plan

```
# <KEY> plan: <ticket summary>

Repeat bug: no            (yes when bug-reproduced found earlier work. Then fill in the two sections below)
Budget: <estimate or 4h>   Plan estimate: <hours>   Jira estimate: <hours or none>
Repos: <repo list>

Requirements used: <document, version and date, one line each. Knowledge file path.>
Decision log: <path>   Research: <folder>   Before proof: <folder>

## Blockers and open questions
<None, or a numbered list. Each item says who can unblock it.>

## Problem
<2 to 4 sentences in plain words.>

## Acceptance criteria
1. <each one written so a test or a command can check it. End each line with its Jira source: ticket key, Confluence page and version, or attachment name. No source means it is not a requirement and does not belong here.>

## Reproduction (bugs only)
<From <KEY>-repro.md: the steps, the before proof files, the failing test path, the failing output and the root cause with file:line.>

## Previous attempt          (repeat bugs only: old ticket, PR, files changed, what the fix did, how it was tested)
## Why it came back          (repeat bugs only: one of "old fix incomplete", "later change broke it", "different root cause", "never really fixed")

## Approach
<What changes and why. Name the files. Point to the decision log row behind each choice.>

## Related and future tickets
<Each linked, open or future ticket that touches this area: its key, what it expects, and how this plan stays clear of it.>

## Subparts
| Id | What | Files it owns | Depends on | Test |
|---|---|---|---|---|
No two subparts own the same file. Independent subparts run in parallel.

## Do not touch
<Files and behaviors that must stay the same. Always includes lockfiles, CI config and dependency files unless a subpart lists them.>

## Baseline (before any change)
| Repo | Test | Lint | Typecheck | Build |
|---|---|---|---|---|
<pass/fail and counts. Pre-existing failures are listed by name so they are not blamed later.>

## Test plan
<New tests, the repro test, and the commands that must pass.>

## Checklist
| # | Asked for (ticket, chat or user, with source) | Subpart | Proved by | Planned | Built | Verified |
|---|---|---|---|---|---|---|
<One line for every single thing that was asked. ttp ticks Planned, tts ticks Built, ttq ticks Verified.>

## Live test
<Starts with the steps in <KEY>-repro.md, replayed the same way for the after proof. Mode: agent browser, agent run, or user run, and why. Setup commands and data. Numbered steps, each with the action and the expected result. Include the bug's failing action and one nearby flow that must still work. Never production. For each step, say what proof to capture: a UI screenshot, a screenshot of the browser inspector or response, or an API call transcript. UI screenshots whenever the change shows in the UI or the ticket carries UI screenshots. Name the logs to save.>

## Risks
<From blast-radius: what the change could break, with callers checked.>
```

## Plan check

Before showing the plan, run one Sonnet child (medium effort) that reads the `ticket-prework-review` skill and the pstack `blast-radius` skill (see Companion skills in the conventions file), then reviews `<KEY>-ticket.md` and `<KEY>-plan.md`. Tell it:

- Do not rename the chat.
- Do not ask questions.
- Do not edit any file except to write its report to `.scratch/<KEY>-reviews/plan-check.md`.
- Check that every acceptance criterion has a Jira source (ticket, parent, Confluence page or attachment) and flag any requirement that looks invented.
- Check that every decision log row has its backing, and that every point in the ticket file has a checklist line.
- Return at most 40 lines: a score out of 100, the gaps, and the risks.

Fix every gap that is a plan problem. List the rest under Blockers.

## What I understood (the simple explanation)

Show it in chat right after the plan, before any building starts. It is for a reader who does not write code. Use everyday words, as `plain-talk` does, and keep a technical term only when it is the point, with a few words on what it means. Brief, and complete enough that the reader could explain the problem to someone else.

1. **What exactly is wrong.** What a person sees, where, and how it differs from what should happen. Point to the before screenshot.
2. **Why it happens.** The cause in plain words, one step at a time: what the app does, where it goes wrong, and why that produces what the person sees. One everyday comparison.
3. **How I plan to fix it.** Each part of the fix as one line: what changes, and what that part is for.
4. **What you will notice afterwards.** The visible result once it ships.
5. **What could still go wrong.** One or two honest lines.

Example for a caching bug:

> **What is wrong.** New chats are saved, but the chat list shows them empty (see `01-empty-chat.png`). They should show their messages straight away.
> **Why.** The app keeps a saved copy of each chat so it does not have to fetch it every time (a cache). When a chat is saved, the app updates the database but forgets to refresh that copy. The screen reads the old copy, so it looks empty. It is like a restaurant menu board nobody updated: the kitchen has the new dishes, but customers read the old board.
> **The fix.** Part 1 refreshes the saved copy whenever a chat is saved, so the screen always reads the latest version. Part 2 adds a test that saves a chat and checks the list, so this cannot come back unnoticed.
> **What you will notice.** A new chat shows its messages at once.
> **What could go wrong.** Two other screens read the same copy, so each one is checked in the live run.

When the explanation and the plan disagree, fix the plan.
