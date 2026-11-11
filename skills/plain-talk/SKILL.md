---
name: plain-talk
description: Explains any situation, ticket, bug, PR, skill or technical result in everyday language, with real-life examples, for a reader who does not work in tech. Short by default, full detail on request, and a brief mode other skills call. Names the problem first, then explains what happened, why and what comes next. Gives no analogy unless asked. Explains each point separately when the user lists points and asks for that. Use when the user types plain-talk, asks to "explain simply", "in layman terms", "like I am not technical", "talk like a human", or names a skill or concept and wants it explained.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# plain-talk

Explain it the way a clear-headed colleague would explain it to a smart friend who does not work in tech. The reader wants to understand the real thing: what the problem is, why it happens, what was done about it, and what comes next.

Do not underestimate the reader. They are smart, they just do not know the jargon. Never talk down, never simplify to the point of being wrong, and keep the real substance: the actual cause, the actual risk, the actual decision, the real numbers and names (in plain words). Plain words, full truth, enough detail to act on.

Write as `~/.agents/skills/unslop/SKILL.md` says: layman language, plain words, short sentences, active voice, no em dashes, no filler, and an example when one is required. Use no analogy unless asked (see below).

## To-do list

When the answer has several parts, make a temporary to-do list first, so no point is skipped. One item per point the user asked about, plus these:

```
python3 -I ~/.agents/skills/guide/scripts/todo.py new plain-talk "Read the real material" "Name the problem first" "<one item per point the user listed>" "Check the sections match the points"
```

Tick each item as you write its section. It deletes itself when the last item is ticked. For a one-point answer, skip the list. See "To-do lists" in the conventions file.

## Real-life examples, not analogies

A real-life example is a real situation of the same kind that people actually meet. An analogy says "X is like Y" and borrows a different situation to stand in for the real one.

- Use real-life examples. They show the same thing happening somewhere familiar: "The same happens in a banking app that still shows yesterday's balance after a transfer. The money moved, but the screen shows a stored number."
- Give no analogy ("it is like a restaurant kitchen") until the user asks for one ("give me an analogy", "compare it to something"). When asked, give it, and say where it stops being true.
- Pick an example that is true to the problem, specific, and one the reader has likely seen. Say what it shows. Do not decorate.

## Short by default

Keep answers short. Give the most important points first, in a few sentences, and stop. Go into full detail only when the user asks for it ("tell me more", "explain in detail", "the full story").

**Brief mode** is for when another skill calls this one for a quick explanation, such as the one after a plan. Write about 150 words at most: the problem named in a line, then one or two sentences for each part asked for. Keep the substance (the real cause, the real fix) and drop everything else. No tables, no multi-turn check-ins.

## Give the full picture (when asked for detail)

Cover what is needed, then stop. A ticket usually needs most of these, and a small question needs only one or two:

- what the problem is and who it affects, with how often or how many when known
- what a person sees when it goes wrong, step by step
- why it happens, one cause at a time, in the order things occur
- what was done, and why that fixes the cause and not only the symptom
- what could still go wrong, and what was checked
- where it stands now, and what happens next or what the reader must do

Read the real material first (the ticket, the PR, the logs, the result). Never guess. Say plainly what is unknown or unconfirmed.

## Name the problem first

The first thing the reader sees names the problem being solved. Put the ticket key in it when there is one. Shape it however fits: a bold line, a plain sentence, a question, a heading. Examples: "The problem: customers could not apply discount codes at checkout (PROJ-123)." or "What was going wrong: saved chats showed up empty."

## Change the shape every time

Do not reply in the same format each time. Choose the shape that makes this answer clearest, and vary it from one reply to the next:

- plain flowing paragraphs, like a person telling it
- a short walk-through of what happens, step by step
- a before and after table
- a timeline of what happened and when
- question and answer, when the user asked several questions
- one section per point, when the user listed points (see below)
- a short summary first, then the detail underneath

Do not reuse the same opening, headings or closing line. Use a table, a list or a Mermaid diagram only when it makes the answer easier to follow than a sentence would.

## Points the user listed

When the user gives several points, questions, tickets or items, and asks for them separately ("explain each one", "one by one", "separately", "each point"), explain every point on its own:

1. Give each point its own section, in the order the user listed them. Label it with the user's own words or number.
2. In each section, cover that point fully: what it is, why it matters or why it happens, a real-life example, and what it means for the reader. Do not merge points or let one point's explanation stand in for another.
3. Do not skip any. Before sending, count the points the user gave and the sections you wrote. The two numbers must match.

When the user lists several items and does not ask for them separately, group the ones that belong together and tell one story. Call out the one that needs attention, and give counts. If they then ask for detail on one, go deep on that one.

## Turns

For a big topic, go one layer at a time and end with one short, natural question ("Want me to go into why it broke?"). Read the reply. If they follow, add the next layer. If they are confused, say it again with a different real-life example before adding anything new. When the topic is small, or the user wants it all at once, give it all in one go and skip the question. Length follows the request: short by default, and as long as it needs to be when the user asks for detail.

## Language

- Everyday words. When a technical word is unavoidable, say what it means right there.
- No code, stack traces, commands, branch names or file names unless the user asks.
- Say who does what: "we fixed it", "it is waiting on you".
- Say plainly if something is broken, late or unknown. Do not soften it and do not overstate it.

## When the user names a skill, tool or concept

For `plain-talk ship` or `plain-talk what is a git worktree`, open by naming the problem the thing solves. Then explain what it does, step by step, using a real example of it being used, with real names and numbers where they help. End with what it means for the reader and what to type or expect. Give a comparison only if they ask.

## Examples

A ticket, as flowing prose:

> **The problem: customers could not use discount codes at checkout (PROJ-123).**
>
> During the sale, a shopper would type a code, press apply, and the whole page would crash, so they left without buying. It happened every time a code had expired, and the sale had many expired codes still in circulation from last month's email. The page asks the system whether a code is valid. For an expired code the system answers with a message the page was never built to read, so it gives up and shows an error screen. We changed the page to understand that message and show "This code has expired" instead, and we tried an expired code, a valid one and a mistyped one ourselves to make sure each behaves. It is waiting for a teammate to look it over. Once they agree, it goes live.

Several tickets, as a table (the user did not ask for them separately):

> **This week's job: the checkout and login problems.**
>
> | Ticket | What was wrong | Where it stands |
> |---|---|---|
> | PROJ-123 | Expired discount codes crashed checkout | Fixed, checked, waiting for review |
> | PROJ-131 | Password reset email arrived twice | Fixed, being checked |
> | PROJ-140 | Login page slow on phones | Still being built |
>
> The one to watch is PROJ-131, because the reset flow has broken twice before, so it is getting extra testing. Nothing needs your input right now.

Points asked for separately:

> *(user: explain these separately: 1. the cache, 2. why the list was empty, 3. the fix)*
>
> **1. The cache.** The app stores a copy of data it uses often, so it does not have to fetch it again each time. A banking app does this with your balance, so the home screen opens fast. The cost is that the copy can go out of date if nothing refreshes it.
>
> **2. Why the list was empty.** When a chat was saved, the app updated the database but never refreshed the stored copy. The chat list reads the copy, so it still showed the old version from before the chat existed. The same happens when a banking app shows yesterday's balance after you send money: the transfer happened, the screen shows a stored number.
>
> **3. The fix.** Every time a chat is saved, the app now refreshes the stored copy too. We also added a test that saves a chat and checks the list, so this cannot return unnoticed.
