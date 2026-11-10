# Cards for blueprint

A card is one `AskUserQuestion` call with one question and 2 to 4 options. The tool adds a free-text "Other" box. Headers are 12 characters or fewer.

Cards appear only when `blueprint` is typed alone in an empty chat. Ask one card at a time, because each answer changes the counts on the next card. A ticket key typed into "Other" on any card ends the questions and starts that ticket.

Fetch the user's own To Do tickets once with the candidate query, drop the blocked ones, and keep the list in memory. Every count below is recalculated from the tickets still left after the answers so far.

## Card 1: how to pick

Single choice.

| Option | What happens |
|---|---|
| Random | Pick one ticket at random from the list. Ask nothing more. Say which ticket and why it was free to take, in one line. |
| Specific ticket | Narrow the list with cards 2 and 3, then choose on card 4. |

## Card 2: priority

Multi-select. One option per priority that has tickets, most urgent first, each with its count ("High (7)"). At most 3 priority options: merge "Low or Lowest" first, then "Medium or lower", until they fit. The last option is always "Skip (any priority)".

Before card 3, print one line with the new total and the count per epic for the chosen priorities.

## Card 3: epic

Multi-select. The 3 epics with the most tickets left, each as key, short summary and recalculated count. The last option is always "Skip (any epic)". Another epic key goes in "Other".

## Card 4: the ticket

Single choice. Shown only when more than one ticket is left. The top 3 by this ranking, the first marked "(Recommended)":

1. Priority, Highest first.
2. Size, smallest first. Size is story points when the project has that field (see the conventions file), otherwise the original estimate. Tickets with no size go last within their priority.
3. Nearest fix version release date, then Jira rank.

Label: `PROJ-123 (Bug, High, 2h)`. Description: the ticket summary. "Other" takes any ticket key.

## Only when a real decision is missing

- **Nothing matches.** Show the count per filter. Ask once: widen the filters, or include unassigned tickets. Never include unassigned tickets without this answer.
- **Repos unclear.** No repo clearly fits the ticket. Multi-select, best guess first and marked "(Recommended)".
- **Repro stuck.** After 30 minutes or 3 failed approaches. Options: "Keep trying for 30 more minutes", "Move ticket back to To Do and stop", "Post a Jira comment asking for repro details".
