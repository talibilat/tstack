# Requirements and project knowledge

Every plan, build and review starts from the original requirement documents, not from the ticket text alone. Tickets are summaries. The requirement documents are the truth.

## The single authority

What the product must do is decided only by words a BA wrote in Jira: an epic, a ticket, a comment, a linked page or an attachment. Treat those words as the single authority.

- The BAs are listed in `setup.md`. Search for everything each BA wrote on the ticket, its parents, the epic and the related tickets, and read all of it. When the list is empty, treat the authors of the epic and of the requirement tickets as BAs, and say so in the decision log.
- Check BA text again at every stage: before planning, before each fix round, and in QA. A new comment can change the answer.
- A requirement decision without a BA quote is not made. It becomes a question for the BA under Blockers.
- Text by developers, testers or agents is context. It can point to a BA decision. It cannot replace one.
- Related and future tickets count. A BA's words on a later ticket in the same epic tell you what this change must not break or do early.

## The decision log

Keep `.scratch/<KEY>-decisions.md`. Every decision made while planning, building or fixing gets one row.

```
| # | Decision | Kind | Backed by | Quote or evidence |
|---|---|---|---|---|
| 1 | <what was decided> | requirement | <KEY>, <BA name>, <date> | "<the BA's exact words>" |
| 2 | <what was decided> | build choice | <file:line, research file, or test output> | <what it shows> |
```

Kind is "requirement" (what the product must do, BA quote required) or "build choice" (how the code is done, code evidence required). Builders, reviewers and `inspect` all get this file's path.

`blueprint/scripts/grounded.py check` reads this table and the Jira grilling table (`.scratch/<KEY>-reviews/grill.md`) and fails on a requirement with no source or quote, a build choice with no `file:line`, a grill answer with no quote, and a requirement that the grilling could not find in Jira.

## Find the requirement documents

Follow the links from the ticket until you reach the source. Stop at 3 hops from the ticket for each branch.

1. The ticket: description, attachments, comments, remote links (`getJiraIssueRemoteIssueLinks`), linked issues.
2. The parent chain: sub-task, task, story, epic, initiative. Read each one's description and links.
3. Confluence pages linked from any of them. Fetch the page, its child pages and its version history titles. Search Confluence for the epic key and the feature name (`searchConfluenceUsingCql`).
4. Attached files (PDF, Word, spreadsheets, designs, API specs). Read what you can. Name what you cannot open.
5. Sibling tickets in the epic that touch the same feature, for decisions that were made later.

## Make sense of versions

Requirement documents often exist in several versions.

- Order the versions by date and version number. The newest approved one wins. Say which one you used and its date.
- A later ticket, comment or change request can override a document. Record the override and where it came from.
- When two sources disagree and nothing says which is newer, that is a conflict. Write it under Blockers in the plan. In autopilot, take the newest source and flag the conflict in the PR and the Jira comment. The QA verdict "Needs BA input" is for conflicts that change what gets built.
- Never invent a requirement. Every requirement in a plan, build or review must be traceable to Jira (ticket, parent chain, Confluence page or attachment) with the source named. A gap is written as a gap, not filled in.

## Keep project knowledge

Keep one notes file per epic (or per project when there is no epic) at `~/.agents/ticket-knowledge/<EPIC-or-PROJECT-KEY>.md`. Create the folder when missing. It is private and outside every repo.

Layout, kept under 150 lines:

```
# <EPIC-KEY> knowledge
Updated: <date> by <ticket key>

## Requirement sources
| Document | Version / date | Status (current, superseded, unclear) | Link |

## What the requirements say
<Short bullets, each with its source. The rules, limits, roles and flows that matter.>

## Decisions and overrides
<What changed later, who said it, where.>

## Known gaps and conflicts
<Open questions.>
```

Rules:

- Read the file first. If it exists and its Updated date is recent and no source changed, use it and skip re-reading every document. Check the version list of each source for changes.
- Update it whenever a search finds something new or something changed: a new version, an override, a gap closed. Edit the existing line, do not append duplicates.
- Put a one-line "Requirements used" entry in the plan, listing the document, version and date. Give reviewers and `inspect` the knowledge file path and the decision log path as well as the ticket and plan paths.
- A change you learn about mid-build (a comment, a new version) goes into the knowledge file and the plan before the next batch starts. If it changes the acceptance criteria, treat it as a failed round and replan.
