---
name: lane
description: Gives each agent its own small, isolated copy of Aruva (a lane) built from its worktree, so many agents can run the app at once, test it in the browser, over the API and in the terminal, and save before and after screenshots and logs. Use when the user types lane, or when reproduce, inspect or ship needs to reproduce, live test, demo or screenshot an Aruva change.
---

Be strict and vigilant. Do only what this skill says, in its order, and never step outside the system (see System rules in the conventions file).

# lane

A **lane** is one agent's private Aruva: its own database, Redis, Qdrant, Neo4j, backend, AI service and frontend, on its own ports. The heavy stateless services (document parser, content extractor, PII masking) are shared from the always-on base stack. Many agents can each hold a lane at once without touching each other's data, ports or containers.

The browser that `lane shot` and the flows open is real Google Chrome with a visible window. Set `HEADLESS=1` only when there is no other option, and write the reason on the `Method:` line of the repro file.

Everything goes through one command, `lane`, in this skill's `scripts/` folder. Below, `lane` means `~/.agents/skills/lane/scripts/lane`.

The pipeline uses a lane three times, and each use follows the steps below:

| Called by | Lane is built from | Proof goes to |
|---|---|---|
| `reproduce` (before proof) | The worktrees at the current default branch, before any fix | `.scratch/<KEY>-evidence/before/` |
| `inspect` (live run) | The worktrees at the commit under review | `.scratch/<KEY>-evidence/` and `after/` |
| `ship` step 5 (after proof) | The worktrees at the final commit | `.scratch/<KEY>-evidence/after/`, same file names as `before/` |

Before and after are taken the same way: follow `.scratch/<KEY>-repro.md` step by step, with the same account and data.

## To-do list

Before the first step, make a temporary to-do list from this skill's steps, so nothing is forgotten:

```
python3 -I ~/.agents/skills/guide/scripts/todo.py new lane --key <KEY> --from ~/.agents/skills/lane/SKILL.md
```

Leave out `--key` when the task has no key. Tick each item when its Done condition is met, with the evidence: `todo.py tick lane --key <KEY> N --note "<proof>"`. Mark a stuck item with `todo.py block`, and add a step you find later with `todo.py add`. Show the list with every update. When the last item is ticked, the list deletes itself. See "To-do lists" in the conventions file.

## Steps

1. **Check.** Run `lane doctor`. Every line must say `ok` (an `info` line about the shared network is fine). On a `FAIL`, follow `references/setup.md` and stop if you cannot fix it.
   Done when doctor prints no `FAIL`.

2. **Sync, then claim a lane.** First run `scripts/sync-dev.sh <worktree> ...` for every worktree, so the lane is never behind dev. If it reports a dirty worktree or a conflict, stop and ask. Then pass the worktree of every repo your change touches, from the task folder (`<root>/worktrees/<KEY>/be`, `.../ai`, `.../fe`). Repos you leave out run the base dev image.

   ```
   lane up <TICKET-KEY> --be <uok-be worktree> --ai <uok-ai worktree> --fe <uok-fe worktree> --owner "<agent or chat name>"
   ```

   It prints the lane number `N` and the URLs. Measured: about 1 minute with no builds; 14 minutes for a first backend plus frontend build; under 1 minute when Docker's build cache already holds those layers. Builds run one at a time across all lanes and wait for free memory, so `lane up` may say it is waiting. It refuses when Docker is short of memory or all lanes are taken; run `lane ls`, and free only lanes you own.
   Done when it prints `lane N is up` and the URL block.

3. **Test it live** on the commit you will ship. Use every mode that fits the change:

   | Change | How | Proof |
   |---|---|---|
   | Visible in the UI | `lane shot N <path> <file.png> --as <email>` for one page. For a journey, write a script with `scripts/browser.mjs` (`openLane`, `goto`) or run a ready flow: `lane flow N foundation --pdf <file>` | Numbered screenshots |
   | API | `TOKEN=$(lane login N <email>)` then `curl -H "authorization: Bearer $TOKEN" <api url>/...` | Request, status and body saved as `.txt` |
   | Worker, data or logs | `lane logs N api`, `lane exec N exec -T postgres psql -U postgres -d uok -c '...'` | The output saved as `.txt` |

   Flows: `foundation` (course, Course Foundation, upload, extraction, review, validate, approve, create the Smart Syllabus) is verified end to end. `generate` (upload a book asset to that syllabus, parse, Full AI Gen, publish) is verified up to the parse; generation needs a valid Gemini key, see troubleshooting.

   A flow writes `steps.log` and numbered screenshots. A `FINDING` line is a real product result on that PDF (for example a blocking validation issue), not a tool failure: report it. The flow waives a blocking issue once and stops if validation still blocks, because choosing which candidates to reject needs a person. Resume a run with `--course <id> --from <step>`.

   Accounts and seeded courses are in `references/accounts.md`. After you change code, or after `sync-dev.sh` moves a worktree, run `lane rebuild N be|ai|fe` and test again.
   Done when every step of the ticket's live test has a result and a proof file.

4. **Save proof** into the task's evidence folder, in the subfolder the table above names. UI screenshots are the proof for anything that shows in the UI. Save the logs for the same action beside them: `lane logs N api > <folder>/NN-api-log.txt`, and the same for the AI service when it is involved. `lane proof N <label>` gives a folder inside the lane if you need scratch space. Strip tokens, secrets and personal data from text proof.
   Done when the evidence folder holds every proof file the repro steps and the live test name, and the logs for each.

5. **Give the lane back.** Close every browser window and tab you opened. Run `lane down N` as soon as testing ends, also after a failure. It deletes the lane's containers, data, volumes and built images, and copies anything under the lane's `proof/` folder to `<LANES_HOME>/proofs/`.
   Done when `lane ls` no longer shows lane N.

## Rules

- Work only in your own lane. Never run `docker compose` against the base stack (`qa-dev`) or another lane, and never edit the base stack's files.
- Keep the lane while you test, and give it back as soon as you finish. Commands that use a lane reset its stale timer. `lane sweep` (dry run) and `lane sweep --yes` remove lanes untouched for `STALE_HOURS`.
- A lane's data starts from the e2e seed every time. Create what your test needs inside the lane.
- The live test result is valid only for the commit you built. Rebuild and retest after every code change.
- Lanes share some real outside services with dev: uploads land in the dev cloud storage bucket, AI calls use real model keys and cost money, and mail can really send. Use fixture accounts only and keep AI-heavy flows small (the small handbook PDFs).

## Test books

Need a book or document for a test? Use the files in `~/Documents/Projects/ARUVA/Data` (Nokia, Telecom, Maths, Chemistry, Psychologu, Biology.pdf, AI-Security). Pick the smallest one that works. Biology.pdf is 136 MB, so avoid it.

The ticket may attach the book that shows the bug. Download that same book from Jira and test with it. Keep the download in the scratchpad, never in a repo.

- Use them for testing only. Never attach them to a real course, ticket, PR or Jira comment.
- Check the lane first. If the book or course already exists there, or the upload would create a duplicate, use a different book or create a new course. Do not reuse or overwrite the existing one.
- Local Gemini embeddings use the Vertex AI JSON key whose path is in `blueprint/references/setup.md`. Local only. Never commit it or paste its contents.

## The annotated pair

The before and after pictures are built by the `proof` skill: before on the left, after on the right, every change circled and numbered, what is being looked at and what was asked written on the picture, and a verdict against the requirements. `reproduce` calls it in `before` mode (left half only) and `ship` and `inspect` call it in `after` mode. See `proof` for the tool and the prompts.

## Proof gate, no exceptions

No PR, no Jira comment, no Jira attachment and no ticket move until the before and after screenshots exist, are real, and show the fix. "Real" means:

1. Every step has a `before/` and an `after/` screenshot of the live app (UI whenever the bug shows in the UI). Logs, transcripts and text are extra, never a replacement.
2. `proof.py gate before` and `gate after` both print PASS. The gate fully decodes each image, rejects blank, tiny or corrupt files and files that are not PNG, JPEG or WebP.
3. Open every image yourself (Read it) and check it shows the right screen, the bug on the before side, and the fixed behavior on the after side. A page that only shows a login, an error page, a blank screen or the wrong course is not proof. Retake it.
4. After you upload to GitHub or Jira, download or open the uploaded image and check it renders. A broken image link or a corrupted upload counts as not published. Fix it, then re-check.
5. If you cannot produce the screenshots (lane will not start, key invalid, blocked), stop and tell the user why. Do not open the PR or comment on Jira without them. Only the user can waive this, by saying "skip proof" in the call.

## When something breaks

`scripts/isolation-check.sh` proves that no lane can reach another lane's services; run it if you suspect cross-talk. `lane repair N` re-attaches the shared services after the base stack was recreated. `references/troubleshooting.md` lists the failures seen while building this skill and the fix for each. Read it before you change `lane` itself.
