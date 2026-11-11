---
name: proof
description: Builds the annotated before and after picture for a bug fix or change. Captures the UI first (terminal output when there is no UI), puts before on the left, later fills the after on the right, circles and numbers every change, writes what is being looked at and what was asked, and checks the result against the requirements. Says "NOT COMPLETE" when it does not match. Called by reproduce (before half) and ship or inspect (after half). Use when the user says "proof", or when a before or after picture is needed.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

Be strict and vigilant. Do only what this skill says, in its order, and never step outside the system (see System rules in the conventions file).

# proof

One picture per step that a reviewer can read in ten seconds: the bug on the left, the fix on the right, every change circled and numbered, a line saying what is being looked at and what was asked, and a verdict. It is built in two halves, at two different times.

Read `~/.agents/skills/blueprint/references/conventions.md` first (Proof is mandatory, Live environment, Evidence). The tool is `~/.agents/skills/proof/scripts/pair.py`, called `pair.py` below, always run as `python3 -I`. Evidence lives in `.scratch/<KEY>-evidence/` (`before/`, `after/`, `compare/`) and the step list in `.scratch/<KEY>-proof.json`.

## To-do list

Before the first step, make a temporary to-do list for the mode you are in, so nothing is forgotten:

```
python3 -I ~/.agents/skills/guide/scripts/todo.py new proof --key <KEY> "Run pair.py init" "Write looking-at and asked for each step" "Capture the before pictures" "Render the left half" "Check the before half is COMPLETE"
python3 -I ~/.agents/skills/guide/scripts/todo.py new proof --key <KEY> "Sync with dev" "Capture the after pictures" "Find every change with diff" "Circle and number every change" "Judge each step against what was asked" "Render and look at every picture" "Check the proof is COMPLETE"
```

Use the first line for `before` mode and the second for `after` mode. Tick each item with its evidence (`todo.py tick proof --key <KEY> N --note "<proof>"`), mark a stuck one with `todo.py block`, and show the list with every update. When the last item is ticked, the list deletes itself. See "To-do lists" in the conventions file.

## The two modes

| Mode | Called by | When | What it does |
|---|---|---|---|
| `before` | `reproduce` | The bug has just happened | Captures the before pictures, writes the steps and what was asked, and builds the picture with only the left half filled |
| `after` | `ship` (after proof) and `inspect` (live run) | The fix is ready | Captures the same steps, fills the right half, circles every change, checks each step against the requirements, and returns COMPLETE or NOT COMPLETE |

The prompt a caller passes (fill in the brackets):

- Before: `proof before <KEY>. Steps are in .scratch/<KEY>-repro.md. Live environment: <lane or URL>. Method: visible Chrome. Capture the UI first, and terminal output only for a step with no UI. Fill the left half only.`
- After: `proof after <KEY>. Same steps, same place, same account and data. Requirements: .scratch/<KEY>-plan.md checklist and .scratch/<KEY>-decisions.md. Fill the right half, circle and number every change, judge each step against what was asked, and reply COMPLETE or NOT COMPLETE with the items.`

## Capture the UI first, the terminal second

For every step, take the picture where a person would look:

1. **UI.** Real Google Chrome with a visible window on the live environment (a `lane` for Aruva), as `reproduce` sets out. Wait for the page to settle, show the part that matters (scroll or zoom if needed), and save `before/NN-<what>.png` or `after/NN-<what>.png`. Use the same window size for before and after.
2. **Terminal, only when the step has no UI** (an API, worker, CLI or data step). Run the real command, save its full output as `before/NN-<what>.txt` (or `after/`), then turn it into a picture:

   ```
   python3 -I ~/.agents/skills/proof/scripts/pair.py textshot <KEY> <N> before|after --title "<the command>"
   ```

   That writes `NN-<what>.png` beside the text file. A step with a UI and a terminal side gets two steps.

## Mode: before

1. Run `pair.py init <KEY>`. It makes one step per numbered row of `<KEY>-repro.md`. The row's Action becomes "looking at", and its Expected column becomes "asked".
2. For each step, rewrite both so a reviewer who has not read the ticket understands them, with `pair.py item <KEY> N --looking-at "<the screen or call, in one line>" --asked "<what the requirement says should happen, with its source>"`. The source is a BA quote or a ticket key, as in the decision log.
3. Capture the before picture for each step (see above).
4. Optionally circle the bug on the before side: `pair.py mark <KEY> N --box x,y,w,h --label "<what is wrong here>" --sides before`. Boxes use the 900 pixel wide view that `pair.py diff` prints, not the raw screenshot size.
5. Run `pair.py render <KEY>`. Each picture now has the before on the left and a grey "AFTER fills in when the fix is ready" panel on the right.
6. Run `pair.py check <KEY> --stage before`. It must print `COMPLETE`.

Done when `check --stage before` prints COMPLETE and every step has a left half in `compare/`.

## Mode: after

1. Check that the fix is the code that is running, and sync with dev first, as `ship` step 5 says.
2. Capture the after picture for every step, the same way as the before: same steps, same window size, same account and data, same file names.
3. Find what changed: `pair.py diff <KEY> N`. It prints every changed region as a `--box`.
4. Circle and number each change, with a short label that says what changed and why it matters, in plain words:

   ```
   pair.py mark <KEY> N --box x,y,w,h --label "Chemistry now listed at once (was missing)"
   ```

   - Several changes in one picture get several marks, and the numbers run 1, 2, 3 in the order you add them. The legend under the picture lists them.
   - Use `--type look` (blue) for something the reviewer should check even though it did not change, such as a nearby flow that must still work.
   - Every changed region must be marked. A change that is only noise (a clock, a random id) is declared with `pair.py ignore <KEY> N --box ... --reason "..."`.
   - To start a step's marks again, use `pair.py mark <KEY> N --clear`.
5. **Match each step with what was asked.** Start one fresh, read-only sub-agent (Sonnet medium) so the judge is not the builder. Give it a short brief with paths: `.scratch/<KEY>-proof.json`, the `before/`, `after/` and `compare/` images (it must open them), the plan checklist and the decision log. Ask for one line per step: `match` or `no-match`, and the reason. It must quote the requirement it checked, and it must not edit anything. Then look at each picture yourself. Record the result: `pair.py verdict <KEY> N match|no-match --note "<one line: why>"`.
6. Run `pair.py render <KEY>`, then open every picture in `compare/` and look at it. The circles must sit on the real change, the labels must be readable, and the left and right must show the same screen. If one is wrong, fix the mark (`--clear` and mark again) or retake the picture, and render again.
7. Run `pair.py check <KEY>`.

Done when `check` prints `Proof: COMPLETE`.

## What the reply says

- **COMPLETE.** Every step is captured on both sides, every change is circled and labelled, and every step matches what was asked. Reply with `Proof: COMPLETE`, the folder `compare/`, and one line per step.
- **NOT COMPLETE.** Something does not match, a change is unmarked, or an image is missing. Reply with `Proof: NOT COMPLETE. The work is not finished yet.` and the list that `check` printed, with each failing step's reason. `ship` treats this as a failed round: it makes a phase 2 plan from the list, fixes the code, and calls `proof after` again. Never mark a step `match` to get past this.

## Never

- Never fill the right half before the fix is running, and never reuse a before picture as an after picture.
- Never mark a step `match` unless the picture shows what the requirement asks. When a requirement is unclear, say so and set the verdict to `no-match` with that reason, or ask the user.
- Never circle a place that did not change as though it did. `look` marks are blue and say what to check.
- Never skip the proof. Only the user can, by saying "skip proof" in the call.
- Never leave a browser window, tab or lane open.
