# Where each agent loads skills

Checked on macOS on 6 November 2026 against Claude Code 2.1.318, the Codex app's bundled CLI and Cursor. The scanner (`scripts/skills.py`) reads these places and nothing else.

| Folder | Loaded by | How we know | Invoke name |
|---|---|---|---|
| `~/.claude/skills/<name>/` | Claude Code, personal | The Claude Code binary names `~/.claude/skills/<name>/SKILL.md` as the personal skill path | `<name>` |
| `~/.claude/skills/synced/<id>/<name>/` | Claude Code, skills synced from claude.ai | `manifest.json` in that folder; the `anthropic-skills:` prefix is hard-coded in the binary | `anthropic-skills:<name>` |
| `<installPath>/skills/<name>/` for each plugin in `~/.claude/plugins/installed_plugins.json` that is `true` in `~/.claude/settings.json` `enabledPlugins` | Claude Code plugins | Those two files | `<plugin.json name>:<name>`, e.g. `pstack:setup-pstack` |
| `~/.codex/skills/<name>/` (or `$CODEX_HOME/skills`) | Codex, personal | Codex binary text: "`$CODEX_HOME/skills` (defaults to `~/.codex/skills`)" | `<name>` |
| `~/.codex/skills/.system/<name>/` | Codex, built-in | Codex binary text about `skills/.system` | `<name>` |
| `~/.agents/skills/<name>/` | Codex, shared folder | Codex binary contains `.agents/skills` (`user-agent-skills`). Claude Code and Cursor reach these only through symlinks in their own folders. | `<name>` |
| `~/.codex/plugins/cache/<market>/<plugin>/<version>/skills/` for each `[plugins."<plugin>@<market>"] enabled = true` in `~/.codex/config.toml` | Codex plugins | `config.toml` | `<plugin>:<name>` |
| `~/.cursor/skills/<name>/` | Cursor, personal | Folder convention | `<name>` |
| `~/.cursor/skills-cursor/<name>/` | Cursor, built-in | Cursor state records use of these | `<name>` |
| `<repo>/.claude/skills`, `<repo>/.agents/skills`, `<repo>/.cursor/skills` | Project skills for Claude Code, Codex and Cursor | Folder convention; scanned only with `--project <repo>` | `<name>` |

## Not on disk

Claude Code's built-in skills (`code-review`, `simplify`, `loop`, `schedule`, `init`, `update-config`, `claude-api`, `keybindings-help`, `fewer-permission-prompts` and the artifact skills) exist only inside the app binary. The session's own skill list is the source for them.

## Skipped on purpose

These hold SKILL.md files but no agent loads them directly: the skills source repo (its skills reach agents through symlinks), `~/.claude/skills/.trash`, `.staging` folders, marketplace clones under `~/.claude/plugins/marketplaces`, `~/.cursor/plugins/marketplaces` and `~/.codex/.tmp`, `node_modules`, and git worktree copies of repos.

## Not yet verified

- Which copy wins when two locations hold different skills with the same name.
- Cursor plugin skills: Cursor stores installed plugins as numeric ids that do not map to names, so the scanner leaves them out.
- Codex `openai-curated-remote` plugins that are cached but absent from `config.toml`.
