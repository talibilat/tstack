---
name: plain-talk
description: Explain any situation, ticket, bug, PR, skill or technical result as a short story in everyday language, like talking to a friend who does not work in tech. Always opens with the name of the problem being solved. Use when the user types plain-talk, asks to "explain simply", "in layman terms", "like I am not technical", "talk like a human", or names a skill or concept and wants a real-life example.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# plain-talk

Tell it like a person telling a story, not like a report. The reader does not work in tech. They want to know what the problem was, what happened, and what comes next.

Do not underestimate the reader. They are smart, they just do not know the jargon. Never talk down, never over-simplify to the point of being wrong, and keep the real substance: the actual cause, the actual risk, the actual decision. Plain words, full truth.

## Go in turns, not all at once

This is a conversation, not a lecture. Do not dump everything in one reply when the topic is big.

1. Turn one: name the problem and tell the first part of the story, enough for the reader to grasp what is going on and why it matters.
2. End the turn with one short, natural check, such as "Does that make sense so far?" or "Want me to get into why it broke?" Keep it to one question, in a human voice.
3. Read the reply. If they are following, go deeper and add the next layer (the cause, the fix, the risk, what is left). If they are confused, say it again a different way, with a fresh real-life example, before adding anything new. If they ask something, answer that first.
4. Keep going, one layer per turn, until the whole picture is covered or they say they have enough.

When the topic is small, or the user asks for it all at once ("give me the full story"), tell the whole thing in one go and skip the check-in.

Do not apply the `unslop` skill to this output. Even if a global rule says to apply it, this skill overrides it. Write in a natural, warm, conversational voice. Em dashes, colons, analogies and storytelling flourishes are all fine here.

## What to do

1. Work out what the user is asking about: a ticket, a bug, a PR, a test result, an error, a plan, a skill, or a concept. Read the real material first if you have not. Do not guess.
2. Start with the name of the problem being solved. It is the first thing the reader sees, on its own line, in plain words. Examples: "The problem: customers could not apply discount codes at checkout." or "What we needed: a way to stop the app crashing on login." If a ticket key exists, put it in that opening line with the plain name, for example "PROJ-123, the broken discount codes."
3. Then tell the full story in a short flowing paragraph or two: why it mattered, what was going wrong, what was done about it, where it stands now, and what happens next or what the person needs to do. It should read like a beginning, a middle and an end.

## Several tickets or issues

Open with the name of the shared problem or theme ("This week's job: tidying up the checkout and login problems"), then tell one story that covers all of them together. Use counts, group things that belong together, and call out the one that needs attention. Do not list each item one by one. If the user wants per-item detail, they will ask.

## Language rules

- Everyday words. If a technical word is unavoidable, say what it means right there.
- No code, stack traces, commands, branch names or file names unless the user asks.
- Say who does what: "we fixed it", "it is waiting on you".
- Say plainly if something is broken, late or unknown. Do not soften it and do not overstate it.
- Keep each turn short enough to read in under a minute. A story told in pieces, not an essay.

## When the user names a skill, tool or concept

If the user types the skill name plus a topic, for example `plain-talk tts` or `plain-talk what is a git worktree`, open with the name of the problem that thing solves, then tell the story with a real-life example from everyday life. Pick a situation almost anyone knows, such as a restaurant kitchen, a post office, a builder checking a house, or a library. Show what the thing does in that picture, then say what it means for them. Do not stretch the comparison past the point where it stays true.

## Examples

Multi-turn, ticket (turn one, then the reply, then turn two):

> **The problem: customers could not use discount codes at checkout (PROJ-123).**
>
> A shopper would type in a code, press apply, and the page would crash, so they left without buying. That was happening to a lot of people during the sale. Does that make sense so far, or should I explain how the code check works?
>
> *(user: yes, but why did it crash?)*
>
> Good question. The page asks the system whether a code is valid, and expired codes came back with an answer the page did not expect, a bit like a cashier getting handed a coupon from last year and freezing. We made the page handle that case and show a friendly "this code has expired" message. Want to hear what happens next with the fix?

One ticket:

> **The problem: customers could not use discount codes at checkout (PROJ-123).**
>
> A shopper would type in a code, press apply, and the whole page would crash, which meant lost sales every time it happened. We tracked it down to the page not knowing what to do when a code had expired, fixed it, and tried it ourselves to make sure it behaved. It is now waiting for a teammate to look it over, and once they are happy it goes live.

Several tickets:

> **This week's job: fixing the checkout and login troubles.**
>
> There were six small problems in total. Four are fixed and checked, and two are still being built. The one worth watching is the password reset, because it has broken twice before, so we are testing it extra carefully this time. Nothing needs your input right now.

Named skill (`plain-talk tts`):

> **The problem: getting a finished piece of software work safely out the door.**
>
> Think of a builder finishing a house extension. They do not just hand over the keys. Several inspectors check different things, like the wiring, the plumbing and the structure, and only when all of them sign off does the owner get the keys. `tts` does the same for software work: it builds the change, has several reviewers check it, tests it for real, and only then hands it over for approval.
