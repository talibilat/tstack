# Setup for the ticket skills

Copy this file to `setup.md` in the same folder and fill it in. If `setup.md` is missing, the skill fills what it can from your Jira and git tools and asks you for the rest. `setup.md` is private and git-ignored.

## Jira

| Item | Value |
|---|---|
| Site | `https://<your-site>.atlassian.net` |
| cloudId | from the Jira tool `getAccessibleAtlassianResources` |
| My accountId | from the Jira tool `atlassianUserInfo` |
| Projects | `KEY1` (name), `KEY2` (name) |
| Status names | `To Do`, `In Progress`, `Code Review`. Rename to match your workflow. |
| Transitions | Ids can differ by project. Always match by status name. |
| Planning | Fix versions? Estimates? Sprints? |
| BAs | Names and account ids of the business analysts whose written words decide requirements. Empty means the authors of epics and requirement tickets. |
| Story points | Field id, or `none`. Looked up on the first run and recorded here. |
| Candidate query | `project in (KEY1, KEY2) AND status = "To Do" AND assignee = currentUser() ORDER BY Rank ASC` |

## Repos

Root: `~/code/<workspace>`. GitHub org or user: `<org>`. Default branch: `main`. PRs target that branch.

| Repo | Install | Test | Lint | Typecheck | Build |
|---|---|---|---|---|---|
| `<repo>` | `npm ci` | `npm test` | `npm run lint` | `npx tsc --noEmit` | `npm run build` |

A repo missing from this table: the skill reads its README and scripts, asks you once, and adds a row.

## Identity

- Git author name and email for commits. Use your GitHub noreply address if you keep your email private.
- GitHub account for pushes and PRs.
