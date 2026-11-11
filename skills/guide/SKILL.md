---
name: guide
description: The guide to the tstack skills (full-send, blueprint, reproduce, proof, ship, inspect, lane, babysit, council, modernize, explain-jira, explain-pr, unslop). Says when and how to use each one, and from the middle of any chat says where the work stands and what to do next. Also lists every skill installed on this machine. Use when the user types guide, asks what to do next, which skill fits, how a skill works, or which skills exist.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# guide

Give directions, and keep the answer short. Answer from the chat, the files on disk and the skill files, never from memory. Change nothing: this skill only reads and explains.

Pick the branch that fits what the user asked. A bare `guide` in a chat with work in it means "Where am I". A bare `guide` in an empty chat means "How the pipeline works".

## Where am I, and what next

1. Read the chat above: the task, the last skill that ran, the last thing that finished or failed.
2. Run `python3 -I ~/.agents/skills/guide/scripts/progress.py list` from the chat's project folder, then `progress.py show <KEY>` for the task in this chat. With no board, look at which `.scratch/<KEY>-*` files exist and place the work in the table below.
3. Answer in this order: the task in one line, the board table, the stage the work is in and what is blocking it, and the exact thing to type next.

| What exists | The work is at | Type next |
|---|---|---|
| Nothing, empty chat | The start | `full send PROJ-123` to do everything in one go. Or `blueprint`, `blueprint PROJ-123`, or `blueprint` followed by the problem in your own words |
| A problem or error in the chat, no files | The start, with the task already described | `blueprint` (it takes the problem above as the task) |
| `-ticket.md`, no `-repro.md`, and it is a bug | `blueprint` before the reproduce step | `blueprint <KEY>` to resume |
| `-repro.md` says `Reproduced: no` or `already fixed` | Stopped at the reproduce gate, no plan on purpose | Read the could-not-reproduce report, give the missing detail, then `blueprint <KEY>` |
| `-repro.md` says `Reproduced: yes` and `before/` proof, no `-plan.md` | `blueprint` research and planning | `blueprint <KEY>` to resume |
| `-plan.md`, no build commits in the worktree | Planned, ready to build | `ship <KEY>` |
| Build commits, no `-reviews.md` | Built, not checked | `ship <KEY>` (it calls `inspect`) |
| `-reviews.md` below 100, or a live run FAIL | In the fix loop | `ship <KEY>` to run the next round |
| Score 100 and QA Done, `after/` incomplete | After proof missing | `ship <KEY>` (step 5, with `lane`) |
| PR open | The PR watch | `babysit <PR link>`, or "check the PR" |
| An old PR that fell behind | Needs a decision | `modernize <PR link>` |
| Comments you do not follow | Needs explaining | `explain-jira <Jira link>` or `explain-pr <PR link>` |
| `pair.py` says NOT COMPLETE | The after picture does not match what was asked, so the work is not finished | `ship KEY` fixes the items it lists and tries again |
| `proof.py` prints FAIL | A proof gate is stopping the work on purpose | Fix the line it names. Never skip it. Only you can, by saying "skip proof" |
| A card or question waiting | Blocked on the user | Answer the question shown |

Done when the user knows the stage and has one thing to type.

## How the pipeline works

Show this table, then one line on how the stages follow each other. The order and the rules live in `~/.agents/skills/blueprint/references/conventions.md`. Read the skill's own `SKILL.md` before explaining one in detail.

| Skill | When to use it | How to use it | What you get |
|---|---|---|---|
| `full-send` | You want the whole job done while you are away | `full send PROJ-123`, or `full send` under a problem in the chat | Every stage below in order, with no questions, and the chat stays on the PR until it is merged |
| `blueprint` | Always first. A new ticket, a bug, an error in the chat, or any request | `blueprint` alone in an empty chat asks 1 to 4 short questions (random or specific ticket, then priority, epic, ticket). `blueprint PROJ-123` asks nothing. `blueprint` under a problem in the chat plans that problem. `just blueprint` stops after the plan | A claimed ticket, a worktree, before proof, research from many sub-agents, a decision log backed by BA words, a checked plan with a checklist |
| `reproduce` | `blueprint` calls it for every bug. Type it yourself to reproduce a bug or check one that came back | `reproduce PROJ-123` | Step by step repro on the current code, before screenshots and logs, a failing test, the root cause, and the history when it is a repeat. When it will not reproduce, a short report of why and how to get unblocked, and no plan |
| `proof` | A bug needs a before and after picture. `reproduce` calls it for the left half, `ship` and `inspect` for the right half. Type it to check one yourself | `proof before KEY` or `proof after KEY` | One annotated picture per step: before left, after right, changes circled and numbered, what was asked written on it, and COMPLETE or NOT COMPLETE |
| `ship` | After the plan. `blueprint` starts it by itself | `ship PROJ-123`. With no plan it runs `blueprint` first. adding "build only" builds without QA or a PR | Parallel builders in one worktree, the `inspect` loop until the score is 100, after proof, a PR and a Jira comment with before and after screenshots, then the PR watch until merge |
| `inspect` | `ship` calls it after the build. Type it yourself to check any ticket, branch or PR | `inspect PROJ-123` | Four code reviewers, a live run, every acceptance criterion checked, a score out of 100 and a verdict |
| `lane` | Whenever the app must run for real: before proof, live run, after proof. The other skills call it | `lane`, or let the pipeline call it | A private copy of Aruva per agent, UI screenshots, API transcripts and logs |
| `babysit` | A PR is open and must reach merge. `ship` calls it | `babysit <PR link>` | Failed checks fixed, every comment answered and resolved, the branch kept up to date, until merged |
| `council` | A plan, a change or a decision deserves a second, third and fourth opinion | `council`, with the thing to review | Grok 4.7, Claude Opus 5.5 and GPT Sol at medium effort, scored out of 10, repeated until they agree |
| `modernize` | An old PR has fallen behind | `modernize <PR link>` | A verdict (MODERNIZE, REWORK or CLOSE) and a rebased branch when it should live |
| `explain-jira` | Someone commented on a ticket and you want it explained | `explain-jira <Jira link>` | What the ticket is, what each person asks, what to do next. Chat named `JC <KEY>` |
| `explain-pr` | A PR has review comments you want explained | `explain-pr <PR link>` | What the PR is for, what each reviewer asks and whether they are right, what to do next. Chat named `GC <KEY> #<PR>` |
| `unslop` | Always on. Every reply, plan, commit, PR and Jira comment goes through it | Nothing to type | Plain, short writing |
| `plain-talk` | When a ticket, a result or a skill needs explaining in everyday words | `plain-talk PROJ-123`, `plain-talk ship` | A short story with a real-life example |

The flow: `blueprint` plans and calls `reproduce` on the way. `ship` builds and calls `inspect`. The two loop until both are satisfied. `lane` runs the app for every live step. `ship` then opens the PR and updates Jira with the before and after proof, and `babysit` stays with the PR until it is merged. Updates (the progress table plus what was just fixed and why, in simple words) come every 10 minutes from 07:00 to 18:00, every hour until midnight, and not at all from midnight to 07:00, unless the user names another interval.

## Which skill for this

For a task the pipeline covers, name the skill from the table above and the exact text to type. For anything else, run the scanner with `--find <word>`, read the `SKILL.md` of the two or three best matches, and recommend one with the exact name to type.

## What does this skill do

Read its `SKILL.md` and explain it in a few plain sentences, with an everyday example, when to use it and what to type.

## Which skills do I have

1. Run the scanner:

   ```
   python3 -I ~/.agents/skills/guide/scripts/skills.py
   ```

   Add `--project <repo path>` for each repo the user is working in. Add `--agent claude|codex|cursor` to show one agent, or `--find <word>` to search. `--json` gives the raw records.
2. Add the built-ins. Claude Code ships some skills inside the app (for example `code-review`, `simplify`, `loop`, `schedule`, `init`), with no file on disk. Compare this session's own skill list with the scanner output and add each skill the scan missed as a row marked "built-in (from this session)".
3. Show the tables grouped as the scanner groups them, then one line with the totals per agent.

Rules for the listing:

- Count a skill once even when several folders link to the same file. The scanner does this by following symlinks.
- Name collisions are real: `code-review` in `~/.agents/skills` differs from Claude Code's built-in `code-review`, and plugin skills carry a prefix (`pstack:tdd` is not `tdd`). Show the prefix.
- A skill marked "you only" has `disable-model-invocation: true`. Only a person typing its name can start it.
- If the scanner fails or a location is missing, say which one and why.

Where each agent loads skills from is in `references/locations.md`. Read it when a count looks wrong or a new agent is added.
