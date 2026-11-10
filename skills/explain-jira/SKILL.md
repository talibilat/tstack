---
name: explain-jira
description: Reads a Jira ticket and its comments from a link or key and explains them in simple words. Says what the ticket is about, what each person is asking, and what to do next. Use when the user types explain-jira, or shares a Jira link and asks what the comments mean or what to do about them.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# explain-jira

Explain a ticket and its comments to someone who has not read them. Read only: this skill changes nothing in Jira.

Write as `~/.agents/skills/unslop/SKILL.md` says: everyday words, short sentences, and a real-life example where it helps. Use no analogy unless the user asks for one, as `plain-talk` does. Keep a technical term only when the user will need it, with a few words on what it means.

## Steps

1. **Rename the chat** to `JC <KEY>` (`t3_thread_update`, `rename`). Example: `JC ARPP-4372`.
2. **Read the ticket.** Take the key from the link. Fetch the summary, description, status, assignee, priority, parent and links, and every comment with its author and date. Jira results are large: follow "Jira results are large" in `~/.agents/skills/blueprint/references/conventions.md`. Open the screenshots and attachments the comments point to. Read the parent ticket's summary for context.
   Done when you have read every comment, oldest to newest.
3. **Explain, in this order:**
   1. **What this ticket is.** 3 to 5 sentences: what is wrong or wanted, who it affects, and where it stands now.
   2. **What they are asking.** One row per person or per request, newest last:

      | Who | When | What they said, in simple words | What they want from you |
      |---|---|---|---|

      Mark the BA's comments (the BAs are listed in `blueprint/references/setup.md`). Their words decide what the product must do, so quote the key sentence exactly. Say which requests are already answered and which are still open. Where two comments disagree, say so.
   3. **What you should do next.** A short numbered list, most urgent first. For each item, say who is waiting for it.
4. **Offer the next step**, in one line each:
   - a draft reply to post on the ticket (posted only after the user approves the text)
   - `blueprint <KEY>` to plan and fix what the comments ask for

Done when the user knows what the ticket is, what is being asked, and the first thing to do.

## Never

- Never post, edit or move anything in Jira from this skill without the user's yes.
- Never guess what a comment means. When one is unclear, say that it is unclear and what would settle it.
