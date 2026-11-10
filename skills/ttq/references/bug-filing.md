# Filing a new bug

## Before filing

- Search the bug project in `setup.md` for duplicates and related bugs. If one exists, report it instead of creating a new one.
- Identify the parent chain of the ticket being validated (Epic, Story, Task).

## Jira rules

- Work only inside the project key in `setup.md`.
- Reading issues needs no confirmation.
- Creating, editing or transitioning an issue always needs explicit confirmation first. Show the full draft (fields, parent epic, "Relates to" links) and wait for approval before executing. In pipeline mode, never file. Leave drafts.

## Mandatory fields

- **Parent or epic.** Always set the parent epic of the ticket being validated.
- **Links.** Always add a "Relates to" link for every requirement ticket the bug touches: the validated ticket, its parent tasks, stories, and any governing requirement tickets. Do not link only the nearest one.
- **Priority**, with a reason for High or Highest.

## Priority guide

- **Highest:** data loss or corruption, a security hole, a system or core flow that is unusable.
- **High:** a core AC is broken and there is no workaround.
- **Medium:** an AC is partly broken, or a workaround exists.
- **Low:** cosmetic or a minor inconvenience.

## Description structure

Title, Description, Steps to Reproduce, Actual Result, Expected Result, Root Cause Analysis (Backend bug, Frontend bug), Test Case (action and expected result).

In Actual Result and Root Cause Analysis, attach the relevant log excerpts, console errors, or failed request details (endpoint, status code, response body) as evidence.

## Environment block (on every bug report)

- Browser: Chrome, Firefox or Edge, with versions.
- Platform URL (from `setup.md`).
- API docs URL (from `setup.md`).
