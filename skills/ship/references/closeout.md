# Close out

Start only when the combined score is 100, `<KEY>-live-test.md` shows PASS for the current commit with an evidence file for every step, the `inspect` verdict is Done or Done with notes, and `.scratch/<KEY>-evidence/compare/` holds one comparison image per step (`gate after` printed PASS and `compare` was run).

Update the `ship-close` and `ship-merge` rows of the progress board as the steps finish.

Each step below is on the conventions file's "Never ask" list, so none of them needs a card.

## 0. Publish the evidence

Evidence is in `.scratch/<KEY>-evidence/`: `before/`, `after/` under the same file names, `compare/` with the side-by-side images, and the logs. Run `python3 -I ~/.agents/skills/blueprint/scripts/proof.py gate after <KEY>` again on the final commit. If it does not print PASS, go back to step 5 of the skill. Never open a PR without the comparison.

Publish the images on an evidence branch. It shares no history with the code, so it can never be merged by accident.

1. `git -C <repo> worktree add --orphan -b evidence/<KEY> <root>/<repo>-worktrees/evidence-<KEY>`
2. In that folder: `mkdir -p <KEY>/before <KEY>/after <KEY>/compare`, copy the images in, then `git add -A` and commit with the identity from `setup.md`.
3. `git push -u origin evidence/<KEY>`, then `git worktree remove` the folder.
4. Image links look like `https://github.com/<org>/<repo>/blob/evidence/<KEY>/<KEY>/compare/<file>?raw=true`, and the same under `before/` and `after/`.

If the push is rejected, keep the images in `.scratch/<KEY>-evidence/` and tell the user which folder holds them. The comparison still goes to the PR and Jira some other way: ask the user, and do not carry on without it. Remove secrets, tokens, emails and personal data from every image before it leaves the machine.

## 1. Push and open the PR

1. `gh auth status`. Switch to the GitHub account in `setup.md` if needed.
2. `git -C <wt> push -u origin <branch>`. Never force.
3. Write the PR body to `.scratch/<KEY>-pr.md`, then `gh pr create -R <org>/<repo> --base <default branch> --head <branch> --title "[<KEY>]: <lowercase imperative summary>" --body-file .scratch/<KEY>-pr.md`. The PR is ready for review, not a draft. One PR per repo.
4. Call `link_pull_request` with the full URL.
5. Write `pr-opened` to the timeline.

PR body headings:

```
## What this fixes
<2 to 4 plain sentences. Start with the Jira link: <jira site>/browse/<KEY>>

## What changed
<One bullet per subpart.>

## Before and after
| Step | Before and after, side by side |
|---|---|
<One row per repro step: the step in a few words, and the comparison image from `compare/` as `![](<evidence link>)`. UI screenshots wherever the change shows in the UI, or the ticket itself shows UI screenshots.>

## More proof it works locally
<One image or transcript for each other live run step, each with a one-line caption. A screenshot of the browser inspector or response for things only visible there, a request and response transcript for APIs, and the log excerpt that shows the error is gone.>

## Checked
<Baseline against result. The live test table from <KEY>-live-test.md. Review scores from <KEY>-reviews.md. The inspect verdict and TL;DR from <KEY>-reviews/inspect-r<N>.md.>

## Known limits
<Risks, the Follow-ups list from the reviewers, and any bug drafts from inspect that are outside this ticket. Note that the evidence branch evidence/<KEY> can be deleted after merge.>

## Earlier work              (reproduce tickets only)
<Old ticket key, old PR number, and why it came back.>
```

If the repo has a `.github/pull_request_template.md`, fill that instead and keep the Jira link, the proof section and the review scores.

## 2. Comment in Jira

Post one comment with `addCommentToJiraIssue` (markdown), right after the PR opens. Four plain lines, a fifth for repeat bugs, then the before and after table:

```
Fixed: <one sentence on what was wrong and what changed>
PR: <link for each repo>
Tested: <one line that starts with the live test result>
Proof: before and after comparison below and attached to this ticket, logs attached
Earlier work: <old key>, PR #<number>

| Step | Before and after |
|---|---|
| <step> | ![](<evidence link>) |
```

Then attach the files to the ticket itself. This is required:

```
python3 -I ~/.agents/skills/blueprint/scripts/proof.py attach <KEY>
```

It uploads every comparison image, and the logs as `before-<name>` and `after-<name>`, and skips what is already there. It uses the Jira token saved on this machine. If the token file is missing, ask for the token once as the Jira token section of the conventions file says, then run it again. Without a token, copy `compare/`, `before/` and `after/` to `~/Desktop/<KEY>/` and tell the user the folder is ready to drag in. Treat the step as not done until the user confirms.

If the ticket's own report used UI screenshots, the comment's images are UI screenshots of the same screens.

## 3. Archive, then delete the worktree

1. Create `<root>/archived-worktrees/<KEY>/`.
2. Write `archive.md` there with: the repos, branches and PR links, the last commit SHA per repo, the commands to recreate each checkout (`git worktree add <path> <branch>`), the repro test path, the review scores, active hours and the Jira estimate.
3. Copy `<KEY>-ticket.md`, `-plan.md`, `-reviews.md`, `-timeline.md`, `-live-test.md`, `-history.md` (if it exists), `<KEY>-reviews/` and `<KEY>-evidence/` into the archive folder.
4. `git -C <repo> worktree remove <path>`. If it refuses, run `git -C <path> status --short`. Use `--force` only when the output lists nothing but ignored files such as `node_modules`.
5. Keep the branch. Never delete a remote branch.

## 4. Babysit the PR

Follow the `babysit` skill for every PR: look at it now, wait with one watcher, fix failed checks, answer and resolve every comment, and keep the branch up to date. Come back here when it says the PR is good.

## 5. Code Review and worklog

The PR is good when CI passed, there are no conflicts, `unresolved_count` is 0 and no new comment is unhandled. Human approval is not required for this step.

Before the ticket moves, run the publish check. It reads Jira and every PR and fails when the comparison images are not on the ticket or not shown in a PR description:

```
python3 -I ~/.agents/skills/blueprint/scripts/proof.py verify <KEY> --pr <org>/<repo>#<number>
```

It must print `publish check: PASS`. Fix what it names, then run it again. Do not move the ticket to Code Review before it passes.

1. Write `done` to the timeline and compute active hours.
2. Look up the issue's transitions and move it to "Code Review" by name.
3. Log work with `addWorklogToJiraIssue`:
   - `timeSpent` is the larger of active time and the Jira original estimate. Round active time up to the next 15 minutes. With no estimate, use active time.
   - `started` is the `claim` timestamp.
   - `commentBody` is 2 to 4 lines: what changed, the PR links and how it was tested.
4. Post the Jira update for this milestone (see Jira updates in the conventions file).
5. Tell the user in chat: ticket key, PR links, combined score, hours logged and the archive path. Keep watching.

## 6. Stay until merged

Keep following `babysit` step 6 until GitHub reports the PR as merged. Time spent on review fixes after step 5 is logged as a second worklog when it adds up to more than 15 minutes. After the merge, post the last Jira update and set the `ship-merge` row to done. The chat is finished only then.

## Failure notes

- If a Jira call fails, say which one failed and what is left to do by hand. Do not retry in a loop.
- If the PR cannot be opened, leave the worktree in place and tell the user why.
