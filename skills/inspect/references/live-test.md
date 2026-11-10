# Live run

Nothing passes without one. Unit tests, lint and builds do not count. A live run exercises the changed behavior for real and checks what a user or caller would see.

## Pick the mode

1. **The agent runs it (preferred).**
   - Aruva: use the `lane` skill. It starts a private copy of the app (a lane) from the worktree, so parallel agents never share ports or data, and it has commands for login, screenshots, API calls and logs. Give the lane back with `lane down` when the run ends.
   - Web UI: open the running app in a browser the agent controls and click through the steps. In T3, use the preview tools (`preview_open`, `preview_navigate`, `preview_act`, `preview_snapshot`), loaded with `ToolSearch`. In other agents, use the agent's own browser tool.
   - API, worker or CLI: start the service from the worktree with the command in its README, against local or test data. Call it with `curl` or the real client. Save status codes and response bodies.
   - Docs or config change: follow the written steps literally and check the result.
2. **The user runs it.** Use this when the agent cannot run the change: it needs credentials, a real account, a device, shared or staging data, or a third-party service. Give numbered steps and the exact result to expect at each step. Wait for the answer. The user's "pass" or "fail", with their notes, is the result.

Never test against production. Shared or staging systems need the user's OK first.

## Steps

1. Start with `.scratch/<KEY>-repro.md`. Replay its steps exactly as the before proof was taken: same place, same account, same data. Save each step's proof into `.scratch/<KEY>-evidence/after/` under the same file name as in `before/`.
2. Then run the plan's Live test section: the other numbered steps, each with its action and expected result. If it is thin, write it now. Always include one nearby flow that must still work.
3. Sync every repo with dev first (`~/.agents/skills/lane/scripts/sync-dev.sh <worktree> ...`), so a local copy is never behind. If a worktree moved, rebuild and run the baseline again. Run on the final commit. Record `git -C <wt> rev-parse HEAD`. Start services in the background. Stop them afterward and check that the ports are free.
4. Compare each step with its expected result. Take a screenshot or save the output for each step. Save the logs for the changed action: backend and AI logs, the browser console and the network request.
5. Write `.scratch/<KEY>-live-test.md`:

   ```
   Commit: <sha>   Mode: agent browser | agent run | user run   Date: <UTC>
   Setup: <commands, data used>
   | Step | Expected | Actual | Result | Evidence file |
   Verdict: PASS | FAIL   Decided by: agent | user
   ```

6. The verdict is PASS only if every step matches and every step has an evidence file. Any mismatch or missing proof is FAIL.
7. Close every browser window and tab you opened.

A FAIL is handled like a verified Critical finding. It goes into the phase 2 plan, it counts as a failed round, and the round limits in `review-loop.md` apply.

## User-run handoff

Post this in chat, then write `pause` to the timeline:

```
Live run for <KEY>
Where: <worktree path>   Start it with: <command>
1. <action>. Expect: <result>
2. <action>. Expect: <result>
```

Then show a card: "Passed", "Failed (I'll describe what I saw)", "I can't run it". "I can't run it" keeps the ticket blocked. Stop and ask what to do. Write `resume` after the answer.

## Evidence (required)

Proof that the change works locally is required for every task. The folder layout and the before and after rule are in the Evidence section of the conventions file.

| The change is | Proof |
|---|---|
| Visible in the UI, or the ticket shows UI screenshots | A UI screenshot of each step's result in the running app. A terminal screenshot or transcript is extra, never a replacement. |
| Not visible, but can be inspected in a browser (a network call, the console, storage, response JSON, a rendered file) | A screenshot of the browser inspector panel or the file or response itself. |
| Backend, API, worker, CLI or data | A real call with `curl` or the real client. Save the full request, the status and the response body as text, and a screenshot of the output. |

Rules:

- Name files `<step>-<what>.png` or `.txt`. Each image under 1 MB.
- Remove secrets, tokens, emails and personal data before saving. Crop or redact.
- Proof must show the real changed behavior on the final commit. Unit test output does not count.
- If a proof tool is missing, install it outside the repo and carry on. Examples: `npx playwright install chromium` for a browser, `brew install httpie` for HTTP calls. `screencapture -x` is built into macOS. Never add a tool to the repo's dependencies or lockfile. Tell the user in one line what you installed.

## Staleness

A verdict is valid for one commit. Any later commit that changes code makes it stale, so run the full steps again on the new commit.
