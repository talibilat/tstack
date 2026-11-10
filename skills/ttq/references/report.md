# Report structure

Use this for the final test result. Plain words, one line per scenario, details only for a Fail.

0. **TL;DR.** One line. Example: "Verdict: stays open. 8/10 AC pass, 2 bugs raised."

1. **SCOPE**
   - Ticket key, title, type (Task, Bug, Story).
   - The full parent chain (Epic, Story, Task) and any directly governing requirement tickets.
   - Layers tested.
   - Environment, build, commit and branch, date and time.
   - Test data used (accounts, roles, files).
   - One line on what was validated and why.

2. **REQUIREMENT / AC MAPPING**
   - Every requirement and AC on its own line, grouped by source ticket (this ticket, parent task, story, epic).
   - A result for each: Pass, Fail or Partial.
   - The evidence type for each: live-tested, code-reviewed, log-reviewed, or any mix.

3. **SCENARIOS VALIDATED.** One table for positive, negative and edge cases together.

   | # | Scenario | Type (Positive/Negative/Edge) | Result | Evidence (Live/Code/Logs) | Regression candidate (P1/P2/P3/P4/-) |
   |---|---|---|---|---|---|

   - P1: critical regression candidate. Data integrity, security, or an issue that has already come back. Include it in every regression run.
   - P2: important regression candidate. A secondary symptom, a side effect of a shared mechanism, or a rarer edge case.
   - P3: moderate regression candidate. A standard functional scenario with limited impact or an existing workaround. Cover it in full regression runs.
   - P4: low regression candidate. Minor, cosmetic or rarely used. Cover it in extended regression or when time allows.
   - "-": not worth regression testing.
   - Give each scenario exactly one rank, based on how bad a failure would be, not on whether it passed.
   - For P1 and P2 items, add a short note on which other modules the change may affect.

4. **BUGS RAISED**
   - Ticket key and a one-line summary for each new bug. In pipeline mode these are drafts.
   - Priority, with a reason if High or Highest.
   - Parent epic and "Relates to" links (see `bug-filing.md`).
   - Root cause labeled Backend bug, Frontend bug, or both.

5. **OBSERVATIONS.** Improvement ideas, UX remarks and out-of-scope findings. These are not bugs and are not filed as bugs.

6. **NOT TESTED.** Every scenario that could not be validated, one line each, with the reason: no test data, no access to logs, needs a two-session or concurrency repro, out of scope for the layers, account blocked by 2FA, needs a BA decision first, and so on. Nothing is silently left out.

7. **VERDICT.** One clear recommendation with a short reason:
   - **Done.** All ACs pass and there are no open Medium or higher bugs from this validation.
   - **Done with notes.** All ACs pass. Only Low-priority bugs or observations remain. List them.
   - **Stays open / back to dev.** Any AC fails, or a new bug blocks an AC.
   - **Needs BA input.** Requirements are ambiguous or conflict.
