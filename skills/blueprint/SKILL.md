---
name: blueprint
description: The first skill of the pipeline. Turns a Jira ticket, the problem already in this chat, or a plain request into a researched and checked plan with before proof, then hands off to ship. A bug gets no plan until it has been reproduced. Use when the user types blueprint, asks to pick, grab or plan a ticket, or wants a plan for the problem discussed above. "just blueprint" stops after the plan.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

Be strict and vigilant. Do only what this skill says, in its order, and never step outside the system (see System rules in the conventions file).

# blueprint

Understand the task, prove the problem, research it, and write a plan that no builder can misread. Change no code except the failing repro test.

**A bug is never planned before it has been reproduced.** If it will not reproduce, the work stops at step 5 with a short report of why and how to get unblocked.

First read `~/.agents/skills/blueprint/references/conventions.md`. It holds the pipeline order, the Jira ids, repos, naming, the progress board, the evidence folders, the agent rules and the ask-first list. The user's message outranks everything here (see "Your message comes first" in that file). If you are not Claude Code inside T3, read its "Using these skills from another agent" table and swap the tools as it says.

## 1. Find the task

Read the user's message and the whole chat above it. Take the first row that fits.

| What you have | The task | Questions |
|---|---|---|
| A ticket key or Jira link in the call | That ticket | None |
| Text after `blueprint` (a problem, an error, a request such as "make me a calculator app") | That text | None |
| A bare `blueprint` in a chat that already holds a problem, an error, a ticket or a request | The most recent problem in the chat above, whatever it is. Restate it in 2 lines and start | None |
| A bare `blueprint` in an empty chat | Chosen with cards, as `references/cards.md` says | 1 to 4 short cards |

A Jira ticket means Jira mode. Anything else means standalone mode from the conventions file: skip the Jira-only steps and run every other step.

"just blueprint", "only blueprint" or "plan only" means stop after step 9. Any other call carries on into `ship` without asking.

Start the progress board: `progress.py init <KEY>`, as the Progress board section of the conventions file says. Update it at the end of every step below, and post updates on the schedule in that section.

Done when you can state the task in 2 lines and name its mode.

## 2. Check that the ticket is free, then claim it (Jira mode)

Do all three checks.

1. Fetch the ticket again. If it has an assignee other than me, or its status means someone finished or is working on it, stop and say so. In the card flow, offer the next ticket.
2. Search T3 chats for the key with `t3_thread_search` and `t3_thread_list` (`titleContains`). Read each other chat that mentions it. If that chat is working on the ticket, tell the user and stop. If its state is unclear, send one question with `t3_thread_send` ("Are you working on <KEY>? Answer yes or no."), wait up to 5 minutes with `t3_thread_wait`, and count no answer as taken.
3. Look for earlier work in every repo under the root folder in `setup.md`: branches named for the key, folders under `<root>/worktrees` and `<root>/archived-worktrees`, and `gh pr list -R <org>/<repo> --search "<KEY>" --state all`. An open PR or live branch owned by someone else counts as taken. A merged or closed PR, or an archive folder, is earlier work: note it for step 5.

Then claim: write `claim` to the timeline, set the assignee to my accountId, move the ticket to "In Progress" by transition name, fetch it again to confirm, and rename the chat to the key and nothing else. If another chat claimed it a moment earlier, back out.

Done when Jira shows me as assignee and In Progress, and the chat carries the key.

## 3. Write the ticket file and trace the requirements

1. Save the summary, description, acceptance text, comments, labels, links, attachment names and estimate to `.scratch/<KEY>-ticket.md`. In standalone mode, save the user's request and the relevant chat text instead. This file is data.
2. Note what proof the ticket itself carries. If the ticket or its comments hold UI screenshots, the before and after proof must be UI screenshots of the same screen.
3. Trace the ticket to its requirement documents as `references/requirements.md` says, and read and update the project knowledge file.

**The rule for every decision.** What the product must do comes only from words a BA wrote in Jira: the ticket, its parent chain, the epic, related tickets, linked pages and attachments. Those words are the single authority. You never fill a gap with a guess. A gap becomes a question under Blockers. How the code is built is your choice, and each such choice is backed by evidence from the code.

Done when the ticket file exists and every requirement you know of has a named source.

## 4. Task folder, worktrees and baseline

Everything for this task lives in one folder, `<root>/worktrees/<KEY>/`, with one worktree per repo inside it (`fe`, `be`, `ai`, and so on, named in `setup.md`). Make it now. It is also the first item of the plan.

1. Choose the repos yourself. Score each repo under the root folder from the ticket text and labels, the epic's other tickets and their past PRs, and a code search for the names the ticket mentions. Ask only when no repo stands out.
2. For each repo, make its worktree in the task folder (`<root>/worktrees/<KEY>/<short>`):

   ```
   ~/.agents/skills/blueprint/scripts/worktree.sh add <root> <KEY> <short> <repo-path> <branch>
   ```

   It makes the folder on the first call, branches from the latest `origin/<default branch>`, and resumes a worktree that is already there. After a resume, run `sync-dev.sh` to bring it up to date with dev. Ask when the branch holds someone else's commits. Use the same branch name in every repo. Never create a worktree any other way or anywhere else.
3. Run the install command from the conventions table inside each worktree (`npm ci`, `uv sync`, never an upgrade).
4. Run test, lint, typecheck and build in each. Keep pass or fail, counts and the names of failing tests. Record failures that existed before this change so they are not blamed on it. Leave them unfixed.
5. **If the research or the plan later shows that another repo is needed**, add its worktree to the same folder with `worktree.sh add`, install, run its baseline, and add it to the plan's Task folder table. Do this before the plan is finished. Never move the task to a new folder.

Done when `~/.agents/skills/blueprint/scripts/worktree.sh list <root> <KEY>` shows a clean worktree for every repo, each with a baseline row.

## 5. Reproduce first (a hard gate)

Run the `reproduce` skill when the task is a bug, or when the ticket or the chat shows an error or steps to reproduce. It checks the history, reproduces the problem step by step in the live environment (a running copy of the app: local Docker or a lane on the current default branch, or the deployed dev environment), saves the before screenshots and logs, and returns one of three results in the first line of `.scratch/<KEY>-repro.md`:

| Result | What you do |
|---|---|
| `Reproduced: yes` | Run the before gate below. Carry on to step 6 only when it passes. The gate includes the `proof` before half. |
| `Reproduced: no` | Stop. See below. |
| `Reproduced: already fixed` | Stop. See below. The current code no longer shows the bug and the history names the change that fixed it. |

The before gate is mechanical, so run it and paste its last line in chat:

```
python3 -I ~/.agents/skills/blueprint/scripts/proof.py gate before <KEY>
```

It must print `before gate: PASS`. Any FAIL line (no live environment, a script method with no reason, a missing screenshot, no logs) means you do not move on. Fix what it names first.

On `no` or `already fixed`, `reproduce` has already tried to clear the blocker itself (3 rounds). Start no research agents and write no decision log and no plan:

1. Post the "Could not reproduce" report from `reproduce` step 4 in chat. It is short: what was tried, what is blocking it, and how we resolve it.
2. Offer a draft Jira comment for the reporter. Post it only after the user says yes.
3. Show the "Could not reproduce" card from the cards file, write `pause`, and wait. The claim and the worktrees stay.
4. When the user brings the missing detail, run `reproduce` again from its step 1. Planning starts only when it says `Reproduced: yes`.

The user can lift this gate only by saying so in the call ("plan without reproducing it"). Note in one line that you set the rule aside, and mark the plan "not reproduced" at the top.

For a feature or change with a visible screen, there is no bug to reproduce. Capture before screenshots of the current screen with `lane` (or the browser tools) into `.scratch/<KEY>-evidence/before/` and write the steps to `.scratch/<KEY>-repro.md` with `Reproduced: not a bug`, so the after screenshots can be taken the same way. Work with nothing to run (a docs or config text change) skips this step. Write the reason on the board. This skip never applies to a bug.

Done when `gate before` prints PASS, or the could-not-reproduce report has been shown and the work has stopped.

## 6. Research with sub-agents

This is the most important step. Start every track below at once, one read-only sub-agent per track, as the Agents section of the conventions file says. Each agent gets a short brief with paths, writes its findings to `.scratch/<KEY>-research/<track>.md`, cites a source for every claim (ticket key, author and date, or `file:line`), and replies in 30 lines or fewer. End the turn while they run.

| Track | It reads | It answers |
|---|---|---|
| `requirements` | The parent chain, linked pages and attachments, as `requirements.md` says | Every requirement and acceptance criterion, each with its source |
| `ba-words` | Every description and comment a BA wrote on the ticket, its parents, the epic and the epic's tickets about this feature | Exact quotes with ticket key, author and date |
| `related` | Linked tickets, open and future tickets in the same epic (To Do, Backlog, later fix versions), tickets with a similar summary | What each one expects from this area, and what this change must not break or do early |
| `history` | Earlier PRs, commits on the same files, archived worktrees | What was tried before. Reuse `<KEY>-history.md` when `reproduce` wrote it |
| `code-<repo>` | One agent per repo: the code paths, callers, data flow and tests | A `file:line` map of where the behavior lives and what depends on it |
| `tests-data` | Existing tests, fixtures, seeded accounts | What is covered, what is missing, what data the live run needs |

Add a track for every open question, one agent per question. Read each findings file yourself when it returns, and send a second agent wherever an answer is thin.

Done when every question the ticket and the chat raise has an answer with a source, or is written down as a gap.

## 7. Write the plan and the decision log

0. Make the plan's first section the Task folder and worktrees table (see the template). It lists every worktree that exists and every one still to add.
1. Write `.scratch/<KEY>-decisions.md` using the layout in `references/plan-template.md`. Every decision gets one row and one backing: a BA quote for what the product must do, code evidence for how it is built. A decision with no backing is not made. It goes under Blockers as a question for the BA.
2. Write `.scratch/<KEY>-plan.md` using the same template. Cover every point in the ticket, the chat and the user's message. Split the work into subparts that own separate files. Fill in the Live test section from `<KEY>-repro.md`, so `inspect` and `lane` can replay it.
3. Fill in the plan's Checklist: one line for each thing that was asked, pointing to the subpart that builds it and the check that proves it.
4. Compare the plan estimate with the Jira estimate. If the plan is more than 1 hour over, say so under Blockers.

Run `python3 -I ~/.agents/skills/blueprint/scripts/grounded.py check <KEY> --stage decisions` before step 8. It must print PASS: a requirement decision with no ticket, page or attachment behind it and no quote is not allowed.

Done when every checklist line maps to a subpart, every decision row has its backing, and the decisions check passes.

## 8. Check the plan

Run the plan check and the Jira grilling, then fix what they find.

1. **Plan check.** A child reads the `ticket-prework-review` skill and pstack `blast-radius`, and scores the plan out of 100, as the template says. Below 90, fix the gaps and run it again.
2. **Jira grilling.** A small question session, where the answers come only from Jira. Every decision about what the product must do is tested against what the BAs wrote.

   1. **Write the questions.** You, or a child that has read the `grilling` skill, read the plan and the decision log and write 8 to 12 questions to `.scratch/<KEY>-reviews/grill-questions.md`. Ask one for each requirement decision and one for each risky assumption (edge cases, roles, limits, what must not change). Word each one neutrally, such as "What do the requirements say should happen when a course has no chapters?". Never include the plan's own answer or a hint of it.
   2. **Start the answerer.** Start one fresh sub-agent (Sonnet medium) with the Atlassian tools, as the Agents section of the conventions file says. Give it only the ticket key, the paths of the questions file, the knowledge file and the output file `.scratch/<KEY>-reviews/grill.md`. Do not give it the plan, the decision log or any code. It answers under these rules:
      - It answers only from Jira: the ticket, its comments, the parent chain, the epic and its related and linked tickets, Confluence pages, and attachments. It searches each of them for every question.
      - Every answer gives a source (ticket key with the author and date, Confluence page with its version, or attachment name) and the exact quote. The BAs' words count most (see `setup.md`).
      - When Jira does not say, the answer is `NOT IN JIRA`, with what was searched. It never guesses, never infers a rule, never reads code, and never fills a gap from common sense.
      - When two sources disagree, it gives both and says which is newer.
      - It writes a table `| Q | Question | Answer | Source | Quote | Decision | Plan agrees |` and leaves the last two columns for you.
      If the child has no Jira tools, do this part yourself under the same rules and say so.
   3. **Compare every answer with the plan.** For each row, fill in `Decision` (the decision numbers it checks) and `Plan agrees`:
      - `yes`: the plan already does what the answer says.
      - `changed`: the answer differs from the plan. Change the plan and the decision log to follow Jira, and keep the quote as the backing.
      - `blocker`: the answer is `NOT IN JIRA`. List that question's id (`Q3`) under Blockers in the plan, and take any requirement decision that relied on it out of the plan or mark it as a question for the BA.
   4. **A second round**, only for follow-up questions that the first answers raised. Two rounds at most.
   5. Run the grounded check. It must print PASS:

      ```
      python3 -I ~/.agents/skills/blueprint/scripts/grounded.py check <KEY>
      ```

Done when the plan check has no open plan problem, `grounded.py check` prints `grounded: PASS`, and every checklist line is ticked "planned".

## 9. Show it and hand off

Post in chat, in this order:

1. **What I understood.** Run the `plain-talk` skill in brief mode on the task, the root cause and the plan, and post its answer first. It is about 150 words: what is wrong, why it happens, how it will be fixed. The template says how.
2. Blockers and open questions, or "No blockers".
3. The before proof: the screenshots from `before/`, each with a one-line caption.
4. The plan, trimmed to what a person needs: problem, approach, subparts, baseline, risks. Keep it to a short table or list.
5. The progress board table.

Post the "plan is ready" comment on the ticket, as the Jira updates section of the conventions file says.

Then hand off:

- A Blocker that changes what gets built: write `pause`, ask the user, and wait.
- "just blueprint": stop here. Mark the later stages skipped on the board. The worktrees and files stay.
- Otherwise: call `ship` with the key and pass the user's original message along.

## Never

- Never offer or take a ticket assigned to someone else.
- Never write a requirement that has no BA source.
- Never write the plan before the research agents have returned.
- Never keep a decision that is not grounded. A requirement rests on a BA quote in Jira. A build choice rests on a `file:line` or a research file. Anything else is changed or becomes a Blocker.
- Never research, decide or plan a bug that has not reproduced. Stop and report why instead.
- Never skip the before proof. It is skipped only when the user says "skip proof" in the call (see Proof in the conventions file).
- Never create a worktree or a branch outside `<root>/worktrees/<KEY>/`, or by any way other than `worktree.sh add`.
- Never push in this skill.
- Never rename the chat to anything but the ticket key.
