---
name: explain-pr
description: Reads a pull request and its review comments from a link and explains them in simple words. Says what the PR is for, what each reviewer is asking, and what to do next. Use when the user types explain-pr, or shares a PR link and asks what the comments mean or what to do about them.
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# explain-pr

Explain a pull request and its comments to someone who has not read them. Read only: this skill changes nothing on GitHub.

Write as `~/.agents/skills/unslop/SKILL.md` says: everyday words, short sentences, and a real-life example where it helps. Use no analogy unless the user asks for one, as `plain-talk` does. Keep a technical term only when the user will need it, with a few words on what it means.

Keep it short: a few sentences for what it is, a compact table for what they ask, and a short list for what to do next. Add detail only when the user asks.

## To-do list

Before the first step, make a temporary to-do list from this skill's steps, so nothing is forgotten:

```
python3 -I ~/.agents/skills/guide/scripts/todo.py new explain-pr --key <KEY> --from ~/.agents/skills/explain-pr/SKILL.md
```

Leave out `--key` when the task has no key. Tick each item when its Done condition is met, with the evidence: `todo.py tick explain-pr --key <KEY> N --note "<proof>"`. Mark a stuck item with `todo.py block`, and add a step you find later with `todo.py add`. Show the list with every update. When the last item is ticked, the list deletes itself. See "To-do lists" in the conventions file.

## Steps

1. **Read the PR.** From the link, take the repo and the number.

   ```
   gh pr view <number> -R <org>/<repo> --json title,body,state,author,headRefName,baseRefName,reviewDecision,statusCheckRollup,comments,reviews,files
   gh api repos/<org>/<repo>/pulls/<number>/comments --paginate
   ```

   Read the lines of code each review comment points to. Find the Jira key in the title or the branch name, and read that ticket's summary for context.
   Done when you have read every comment and review, oldest to newest.
2. **Rename the chat** to `GC <KEY> #<number>` (`t3_thread_update`, `rename`). Example: `GC ARPP-4372 #218`. With no Jira key, use `GC #<number>`.
3. **Explain, in this order:**
   1. **What this PR is for.** 3 to 5 sentences: the problem it solves, what it changes, and where it stands now (checks, approvals, conflicts).
   2. **What they are asking.** One row per comment thread, open ones first:

      | Who | Where (file and line) | What they said, in simple words | Open or resolved | Is it right? |
      |---|---|---|---|---|

      Say whether each comment comes from a person or a review bot. For "Is it right?", check the claim against the code and answer yes, no or partly, with one line of why. List failed checks in the same table.
   3. **What you should do next.** A short numbered list, most urgent first: what to fix, what to answer with a reason, and what needs a decision from someone else.
4. **Offer the next step**, in one line each:
   - `babysit <link>` to fix the checks, answer every comment and stay until the PR is merged
   - a draft reply for any single comment (posted only after the user approves the text)

Done when the user knows what the PR is for, what is being asked, and the first thing to do.

## Never

- Never post, resolve, push or merge anything from this skill without the user's yes.
- Never guess what a comment means. When one is unclear, say that it is unclear and what would settle it.
