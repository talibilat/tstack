---
name: lane
description: Gives each agent its own small, isolated copy of Aruva (a lane) built from its worktree, so many agents can run the app at once, test it in the browser, over the API and in the terminal, and save before and after screenshots and logs. Use when the user types lane, or when reproduce, inspect or ship needs to reproduce, live test, demo or screenshot an Aruva change.
---

# lane

A **lane** is one agent's private Aruva: its own database, Redis, Qdrant, Neo4j, backend, AI service and frontend, on its own ports. The heavy stateless services (document parser, content extractor, PII masking) are shared from the always-on base stack. Many agents can each hold a lane at once without touching each other's data, ports or containers.

Everything goes through one command, `lane`, in this skill's `scripts/` folder. Below, `lane` means `~/.agents/skills/lane/scripts/lane`.

The pipeline uses a lane three times, and each use follows the steps below:

| Called by | Lane is built from | Proof goes to |
|---|---|---|
| `reproduce` (before proof) | The worktrees at the current default branch, before any fix | `.scratch/<KEY>-evidence/before/` |
| `inspect` (live run) | The worktrees at the commit under review | `.scratch/<KEY>-evidence/` and `after/` |
| `ship` step 5 (after proof) | The worktrees at the final commit | `.scratch/<KEY>-evidence/after/`, same file names as `before/` |

Before and after are taken the same way: follow `.scratch/<KEY>-repro.md` step by step, with the same account and data.

## Steps

1. **Check.** Run `lane doctor`. Every line must say `ok` (an `info` line about the shared network is fine). On a `FAIL`, follow `references/setup.md` and stop if you cannot fix it.
   Done when doctor prints no `FAIL`.

2. **Claim a lane.** Pass the worktree of every repo your change touches. Repos you leave out run the base dev image.

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

   Accounts and seeded courses are in `references/accounts.md`. After you change code, run `lane rebuild N be|ai|fe` and test again.
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

## When something breaks

`scripts/isolation-check.sh` proves that no lane can reach another lane's services; run it if you suspect cross-talk. `lane repair N` re-attaches the shared services after the base stack was recreated. `references/troubleshooting.md` lists the failures seen while building this skill and the fix for each. Read it before you change `lane` itself.
