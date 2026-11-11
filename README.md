# tstack

The agent skills I use every day to take a Jira ticket from To Do to a merged
pull request, with before and after proof. They work in Claude Code, Codex and
Cursor. Some use [T3 Code](https://github.com/pingdotgg/t3code) features when
they are available and fall back to native tools when they are not.

The idea and the layout of this repo come from
[t3dotgg/tstack](https://github.com/t3dotgg/tstack). The skills are my own.

## Skills

| Skill | Say | What it does |
|---|---|---|
| `full-send` | "full send PROJ-123" | Does everything below in one go with nobody watching, and stays on the PR until it is merged. |
| `blueprint` | "blueprint" | Picks or takes a ticket, reproduces the bug, researches with many sub-agents, and writes a checked plan. Then explains in simple words what is wrong, why, and how it will be fixed. |
| `reproduce` | (automatic) | Replays a bug step by step, saves the before screenshots and logs, writes a failing test and names the cause. No plan is made until the bug reproduces. If it will not, it says briefly why and how to get unblocked. |
| `proof` | "proof" | Builds one annotated before and after picture per step: before on the left, after on the right, every change circled and numbered, what was asked written on it. Says NOT COMPLETE when the fix does not match the requirements. |
| `ship` | "ship" | Builds the plan with parallel sub-agents in one worktree, loops with `inspect` until it passes, opens the PR and updates Jira. |
| `inspect` | "inspect" | Four code reviewers, a live run and a senior QA check of every acceptance criterion. Scores out of 100. |
| `lane` | "lane" | A private running copy of the app per agent, for screenshots, API calls and logs. Aruva-specific. |
| `babysit` | "babysit" | Watches a PR through CI and review, fixes real findings, resolves every comment, stays until merged. |
| `council` | "council" | Gets a review from Grok, Claude Opus and GPT at medium effort, and loops until they agree. |
| `modernize` | "modernize" | Rebases an old PR and decides if it should still exist. |
| `explain-jira` | "explain-jira" + Jira link | Explains the ticket, what each person is asking, and what to do next. |
| `explain-pr` | "explain-pr" + PR link | Explains the PR, what each reviewer is asking, and what to do next. |
| `guide` | "guide" | Says how each skill works and, mid-chat, where the work stands and what to type next. |
| `plain-talk` | "plain-talk" | Explains any ticket, bug or result in everyday words with real-life examples, no analogy unless asked. |
| `unslop` | (automatic) | The writing style for every reply, plan, commit, PR and Jira comment. |
| `postwork` | (automatic) | Reviewer: checks finished work against its ticket. |
| `ticket-prework-review` | (automatic) | Reviewer: checks a ticket and plan before building starts. |

## How they fit together

The pipeline, in order. `full-send` runs the whole chain.

```mermaid
flowchart LR
  P[blueprint<br>plan] --> R[reproduce<br>before proof] --> P
  R --> F1[proof<br>before half]
  P --> S[ship<br>build]
  S --> Q[inspect<br>4 reviewers + live QA]
  Q -- findings --> S
  Q -- score 100 --> L[lane<br>after proof]
  L --> F2[proof<br>after half + check]
  F2 -- NOT COMPLETE --> S
  F2 --> C[ship close-out<br>PR + Jira]
  C --> B[babysit<br>until merged]
```

- `blueprint` uses `reproduce`, `ticket-prework-review` and `lane`.
- `reproduce` and `ship` use `proof`. `proof` uses `lane`.
- `inspect` uses `postwork` and `lane`.
- Everything uses `unslop`.

## What each skill can touch

A solid arrow means the skill changes that system. A dotted arrow means it only reads.

```mermaid
flowchart LR
  subgraph Skills
    blueprint
    br[reproduce]
    proof
    ship
    inspect
    lane
    bp[babysit]
    mod[modernize]
    cou[council]
    explain-jira
    explain-pr
    guide
  end
  subgraph Systems
    J[(Jira)]
    G[(GitHub)]
    C[(Code worktree)]
    A[(Running app and browser)]
    M[(Other AI models)]
  end
  blueprint -->|claim, status, comment| J
  blueprint -.->|search PRs| G
  blueprint -->|make worktree, failing test| C
  br -.->|read history, add link| J
  br -.-> G
  br -->|failing test, local only| C
  br -->|run, screenshot| A
  proof -->|capture, circle changes, judge| A
  proof -.->|read plan and requirements| C
  ship -->|comment, screenshots, status, worklog| J
  ship -->|push branch, open PR| G
  ship -->|build and commit| C
  inspect -.->|read requirements| J
  inspect -.->|read only| C
  inspect -->|live run| A
  lane -->|start, test, delete a private copy| A
  bp -->|push fixes, reply, resolve| G
  bp -->|fix code| C
  bp -->|update comment| J
  mod -->|rebase and update the PR branch| G
  mod -.-> J
  cou -.->|read only| C
  cou -->|ask three models| M
  explain-jira -.->|read only| J
  explain-pr -.->|read only| G
  guide -.->|read only| C
```

| Skill | Jira | GitHub | Code | Running app | Never does |
|---|---|---|---|---|---|
| `blueprint` | Assigns the ticket to you, moves it to In Progress, posts the plan comment | Reads PRs | Makes the worktree, commits one failing test locally | Through `reproduce` and `lane` | Push, or change product code |
| `reproduce` | Reads tickets, links a repeat bug to the old one | Reads PRs and history | Commits a failing test locally | Runs it, takes before screenshots and logs | Push |
| `proof` | Nothing | Nothing | Reads the plan and the diff | Drives a visible Chrome, takes the before and after pictures | Edit code, mark a step as matching without evidence |
| `ship` | Comments, uploads screenshots, moves to Code Review, logs time | Pushes the branch and the proof, opens the PR | Builds and commits inside the worktree | Through `inspect` and `lane` | Merge, force-push, touch production |
| `inspect` | Reads. Drafts bugs, files them only with your yes | Reads the diff | Reads only | Runs every scenario live | Edit code |
| `lane` | Nothing | Nothing | Reads the worktree to build from | Starts and deletes its own private copy | Touch another agent's copy or the shared stack |
| `babysit` | Posts the review-fix and merge updates | Pushes fixes, replies, resolves threads | Fixes what CI and reviewers found | Reruns the live steps a fix touches | Merge, unless you asked in clear words |
| `modernize` | Reads the ticket | Updates the PR's own branch after a rebase | Rebases | Reruns checks | Merge, close, widen the scope |
| `council` | Nothing | Nothing | Reads only | Nothing | Edit anything |
| `explain-jira` | Reads only | Nothing | Nothing | Nothing | Post without your yes |
| `explain-pr` | Reads the ticket summary | Reads only | Nothing | Nothing | Post, resolve or push without your yes |
| `guide` | Nothing | Nothing | Reads the task files | Nothing | Change anything |

Every skill stops and asks before these: a force-push or history rewrite, a database migration, anything on shared, staging or production systems, secrets, dependency upgrades, CI changes, and deleting tests.

## What the pipeline promises

- Requirements come only from words the BA wrote in Jira. Every decision is logged with its source, and a sub-agent that may answer only from Jira grills the plan. A script fails any decision that is not grounded.
- Nothing passes without a live run. UI changes are proven with UI screenshots.
- A bug is reproduced first, in Docker or a lane, in a visible Chrome window. If it will not reproduce, the agent works on the blocker for up to 3 rounds, then reports it and stops. No plan is made.
- The before and after proof is mandatory. A script checks it at each stage, builds one annotated before and after picture per step (changes circled and numbered, what was asked written on it), and checks the images are on the Jira ticket and in every PR. Only you can skip it, by saying "skip proof".
- You get updates in simple words: a progress table, what was just fixed and why, and what is being fixed now. Every 10 minutes by day, every hour in the evening, none overnight.
- One folder per task, `worktrees/ARPP-1234/fe`, `be` and `ai`, all made by `blueprint`, used by every later skill, and moved to `archived-worktrees/` by `babysit` once the PRs are merged.
- The system is strict. Skills follow their steps in order, and the progress board refuses to skip a stage.
- The chat is named after the ticket: `PROJ-123` for the pipeline, `JC PROJ-123` for Jira comments, `GC PROJ-123 #45` for GitHub comments.

## Install

```bash
npx skills@latest add talibilat/tstack -g
```

Or by hand:

```bash
git clone https://github.com/talibilat/tstack
cp -R tstack/skills/* ~/.claude/skills/   # Claude Code
cp -R tstack/skills/* ~/.codex/skills/    # Codex
```

## Setup

There is nothing to fill in before the first run. The skills ask for what they need, once:

- **Jira and repos.** On first run, `blueprint` writes `skills/blueprint/references/setup.md` from your Jira and git tools and asks for the rest. Add your BA's name there.
- **Jira API token.** Needed only to upload screenshots to tickets. The skill asks for it once and saves it in `~/.config/tstack/jira.env`, outside the repo.

## Requirements

- An Atlassian Jira connector in your agent.
- An authenticated [GitHub CLI](https://cli.github.com) (`gh`), and git.
- `python3` for the progress board, the PR status script and the Jira upload.
- `council` needs sub-agents on other providers' models. T3 Code does this with `delegate_task`.
- `lane` needs the local Aruva setup in `skills/lane/references/setup.md`.

`postwork` also reads Matt Pocock's `code-review` skill. That file is not in this repo. Copy it to `skills/postwork/references/matt-code-review.md`.

Optional reviewers, used when installed: `interrogate` and `blast-radius` (pstack), `ponytail-review`, `thermo-nuclear-code-quality-review`, `grilling`, `diagnosing-bugs`, `tdd`. A missing reviewer shows as NOT RUN.

## Make them yours

These are starting points. Edit them. Whatever you type after a skill name outranks the skill's own rules, so "blueprint PROJ-123, plan only" or "updates every 30 minutes" just works.

## License

[MIT](LICENSE)
