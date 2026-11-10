---
name: council
description: Gets an independent opinion from three models from three providers (Grok, Claude Opus, GPT) on a plan, a change or a decision, and loops until they agree. Use when the user says "council".
---

Never assume a requirement. Check Jira for the latest requirements before acting. If a requirement is unclear or cannot be verified, ask the user in plain language before proceeding with work that depends on it.

# council

Three models that were trained by different companies make different mistakes. Where all three agree, the answer is probably right. Where they disagree, look closer.

## The members

All three run at medium effort. If the user names other members or another effort, use those.

| Member | `delegate_task` target |
|---|---|
| Grok 4.7 | `{"providerInstanceId":"cursor","model":"grok-4.7","options":{"reasoning_effort":"medium"}}` |
| Claude Opus 5.5 | `{"providerInstanceId":"claudeAgent","model":"claude-opus-5-5","options":{"effort":"medium"}}` |
| GPT Sol | `{"providerInstanceId":"codex","model":"gpt-6.1-sol","options":{"reasoningEffort":"medium"}}` |

GPT Terra (`gpt-6.1-terra`) takes the GPT seat when Sol is unavailable. Call `orchestrator_capabilities` once to confirm the three models exist. If a member cannot be reached, say which one and run with the others. Never swap in a different model without saying so.

## Steps

1. **Get the work ready.** Fix the problems you already know about and run the relevant checks first. The council judges your best version.
2. **Brief all three at once**, one sub-agent each, with the same brief: the question, the paths to read (plan, decision log, diff, ticket file), and the rules. The rules: read only, no edits, no questions to the user, every claim backed by a `file:line` or a quote, a score out of 10, and a reply of 40 lines or fewer written to `.scratch/<KEY>-reviews/council-<member>-r<N>.md`. End the turn while they run.
3. **Compare.** Put the answers side by side: where all three agree, where they differ, and what each one alone noticed. Check every finding yourself against the code or the ticket before you act on it.
4. **Act.** Make the changes you agree with. For each one you decline, write the reason. A product question the council raises goes to the BA's words in Jira, never to a vote.
5. **Ask again** after changes, with a fresh round. Stop when every member scores 9 or more, or when a round brings no new verified finding. At most 3 rounds.

Keep the scope where the user's goal put it. A council round tends to grow the work one small suggestion at a time. Decline what the task does not need and list it as a follow-up.

## Report

Show this in chat. If the work has a PR, add it to the PR description too.

```
## Council review

Rounds: 2

| Member | Round 1 | Round 2 |
|---|---|---|
| Grok 4.7 | 7/10 | 9/10 |
| Claude Opus 5.5 | 8/10 | 10/10 |
| GPT Sol | 7/10 | 9/10 |
```

Then three short lists: what they agreed on, where they disagreed and what you decided, and the follow-ups you declined. A member that gave no score shows as "no score".
