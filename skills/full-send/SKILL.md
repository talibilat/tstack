---
name: full-send
description: Takes a ticket, a bug or a request all the way to a merged PR in one go, with nobody watching. Runs blueprint, reproduce, ship, inspect, lane and babysit in order and stays on the PR until it is merged. Use when the user says "full send".
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# full-send

The user said "full send" because they are not watching this chat. You own the work from where it stands now until the PR is merged and Jira is up to date. Use it only when the user asked for it in clear words.

Read `~/.agents/skills/blueprint/references/conventions.md` first. Everything there applies.

## What "full send" allows

- Every hand-off between skills, with no card and no question.
- Every test method the proof needs: the browser, the user's computer and terminal, lanes, screenshots. A rule that says "ask before testing" is replaced by this request, for this task only.
- Every item on the "Never ask" list in the conventions file.

It does not allow the items on the "Ask first" list, a merge, or anything touching production.

## Steps

1. **Plan.** Run `blueprint` with everything the user wrote. It finds the task, claims it, renames the chat, reproduces the bug with `reproduce`, researches, and writes the plan.
   Done when `blueprint` step 9 has posted the plan and the simple explanation.
2. **Build and check.** Run `ship`. It builds in the worktree, calls `inspect`, fixes what `inspect` finds, and repeats until the gate passes.
   Done when the score is 100, the live run passed and the QA verdict is Done or Done with notes, all on one commit.
3. **Prove.** `ship` step 5 takes the after proof with `lane`, the same way the before proof was taken.
   Done when every before file has an after file.
4. **Open the PR and update Jira.** `ship` close-out.
   Done when the PR is open with the before and after table and the ticket carries the same proof.
5. **Babysit.** Run `babysit` on every PR. Fix CI, answer and resolve every comment, keep the branch up to date. After each push, run the live steps the fix touches and add the fresh proof.
   Done when CI is green, nothing is unresolved, and the ticket is in Code Review with a worklog.
6. **Stay until merged.** Keep the watch running. Come back for every new comment, failed check or conflict. Never merge the PR yourself, unless the user wrote "full send and merge" and the repo's rules allow it.
   Done when GitHub reports the PR as merged.
7. **Finish.** Post the last Jira update, stop the watch, and report in chat: the PR link, the merge commit, the before and after proof, the score, the hours logged, and each decision you made for the user.

## Staying alive

Ending the turn without a watcher or a running sub-agent stops the work, because nobody will prompt you again. While sub-agents run, end the turn and let their completion wake you. While the PR is open, wait with `watch_pull_request`, as `babysit` says. The chat stays open until step 7 is done.

Updates follow the schedule in the Progress board section of the conventions file: the table, what you just fixed and why, and what you are fixing now, in simple words. Jira follows the Jira updates section.

## When to ask

A question in a normal message goes unseen. Use `AskUserQuestion`, so the chat shows that it is waiting, and put all the context in the question. Ask only when you cannot continue alone:

- the bug will not reproduce, or the change cannot be proven
- a BA's words are missing or conflict, and the answer changes what gets built
- the next step is on the "Ask first" list
- the review loop is stuck, or the PR cannot pass and you cannot fix why
- another PR makes this one obsolete

Decide everything else yourself and list those decisions in the report. If the question tool gives no answer, leave the PR open and start your final message with the question.
