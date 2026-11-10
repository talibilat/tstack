#!/usr/bin/env python3
"""List every agent skill installed on this machine, read from the SKILL.md files themselves.

Usage: skills.py [--json] [--agent claude|codex|cursor|all] [--project DIR] [--find WORD]

Each skill is reported once per real file (symlinks are followed and de-duplicated), with the agents that
load it, the name you type, whether only a human can invoke it, and the first sentence of its description.
Locations come from how each agent loads skills on this machine; see references/locations.md.
"""
import argparse, json, os, re, sys
from pathlib import Path

HOME = Path.home()


def frontmatter(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return None
    meta, key = {}, None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if km:
            key, val = km.group(1), km.group(2).strip()
            if val in (">", "|", ">-", "|-"):
                val = ""
            meta[key] = val.strip("'\"")
        elif key and line.startswith((" ", "\t")):
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta


def first_sentence(text, limit=160):
    text = re.sub(r"\s+", " ", text or "").strip()
    # Take sentences until the summary says something (a bare "Time to help." is not enough).
    sentences = re.findall(r".+?[.!?](?=\s|$)", text) or [text]
    s = ""
    for sentence in sentences:
        s = (s + " " + sentence.strip()).strip()
        if len(s) >= 40:
            break
    return s if len(s) <= limit else s[: limit - 1] + "…"


def skill_dirs(root, recursive=False):
    """Folders under root that hold a SKILL.md (one level, or nested for plugin layouts)."""
    root = Path(root)
    if not root.is_dir():
        return []
    found = []
    pattern = "**/SKILL.md" if recursive else "*/SKILL.md"
    for f in root.glob(pattern):
        parts = set(f.parts)
        if parts & {".trash", ".staging", "node_modules", ".git"}:
            continue
        found.append(f.parent)
    return sorted(found)


def plugin_name(plugin_root):
    for rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json", "plugin.json"):
        p = Path(plugin_root) / rel
        if p.is_file():
            try:
                return json.loads(p.read_text()).get("name")
            except Exception:
                pass
    return None


def locations(projects):
    """Yield (agent, scope, prefix, folder) for every place an agent loads skills from."""
    # Claude Code: user skills, synced claude.ai skills, enabled plugins.
    yield ("claude", "user", "", HOME / ".claude/skills")
    synced = HOME / ".claude/skills/synced"
    for d in sorted(synced.glob("*")) if synced.is_dir() else []:
        yield ("claude", "claude.ai", "anthropic-skills:", d)
    inst = HOME / ".claude/plugins/installed_plugins.json"
    settings = HOME / ".claude/settings.json"
    enabled = {}
    try:
        enabled = json.loads(settings.read_text()).get("enabledPlugins", {}) or {}
    except Exception:
        pass
    try:
        data = json.loads(inst.read_text())
        plugins = data.get("plugins", data)
        for key, entries in plugins.items():
            if not enabled.get(key):
                continue
            for e in entries if isinstance(entries, list) else [entries]:
                path = Path(e.get("installPath", ""))
                name = plugin_name(path) or key.split("@")[0]
                yield ("claude", f"plugin {key}", f"{name}:", path / "skills")
    except Exception:
        pass
    # Codex: home skills, system skills, shared ~/.agents, enabled plugins.
    codex_home = Path(os.environ.get("CODEX_HOME", HOME / ".codex"))
    yield ("codex", "user", "", codex_home / "skills")
    yield ("codex", "system", "", codex_home / "skills/.system")
    yield ("codex", "shared", "", HOME / ".agents/skills")
    cfg = codex_home / "config.toml"
    if cfg.is_file():
        text = cfg.read_text()
        for m in re.finditer(r'^\[plugins\."([^"]+)"\]\s*\n(?:[^\[]*?)enabled\s*=\s*true', text, re.M):
            key = m.group(1)
            plugin, _, market = key.partition("@")
            base = codex_home / "plugins/cache" / market / plugin
            versions = sorted([p for p in base.glob("*") if p.is_dir() and p.name != "latest"], key=lambda p: p.stat().st_mtime) if base.is_dir() else []
            if versions:
                yield ("codex", f"plugin {key}", f"{plugin}:", versions[-1] / "skills")
    # Cursor: user skills and built-ins.
    yield ("cursor", "user", "", HOME / ".cursor/skills")
    yield ("cursor", "built-in", "", HOME / ".cursor/skills-cursor")
    # Project skills for the given project folders.
    for proj in projects:
        p = Path(proj).expanduser().resolve()
        yield ("claude", f"project {p.name}", "", p / ".claude/skills")
        yield ("codex", f"project {p.name}", "", p / ".agents/skills")
        yield ("cursor", f"project {p.name}", "", p / ".cursor/skills")


def collect(projects, agent_filter):
    skills = {}  # realpath -> record
    for agent, scope, prefix, folder in locations(projects):
        if agent_filter != "all" and agent != agent_filter:
            continue
        recursive = scope.startswith("plugin")
        for d in skill_dirs(folder, recursive=recursive):
            if scope == "user" and agent == "codex" and d.parent.name == ".system":
                continue
            real = d.resolve()
            meta = frontmatter(real / "SKILL.md")
            rec = skills.setdefault(str(real), {
                "name": (meta or {}).get("name") or d.name,
                "invoke": set(),
                "agents": set(),
                "scopes": set(),
                "user_only": (meta or {}).get("disable-model-invocation", "").lower() == "true",
                "description": first_sentence((meta or {}).get("description", "")),
                "path": str(real),
                "valid": bool(meta and meta.get("name") and meta.get("description")),
            })
            rec["invoke"].add(prefix + rec["name"])
            rec["agents"].add(agent)
            rec["scopes"].add(f"{agent}:{scope}")
    out = []
    for r in skills.values():
        for k in ("invoke", "agents", "scopes"):
            r[k] = sorted(r[k])
        out.append(r)
    return sorted(out, key=lambda r: (r["invoke"][0].lower()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--agent", default="all", choices=["all", "claude", "codex", "cursor"])
    ap.add_argument("--project", action="append", default=[], help="also scan this project's .claude/.agents/.cursor skills")
    ap.add_argument("--find", help="only skills whose name or description contains this word")
    a = ap.parse_args()
    rows = collect(a.project, a.agent)
    if a.find:
        w = a.find.lower()
        rows = [r for r in rows if w in " ".join(r["invoke"]).lower() or w in r["description"].lower()]
    if a.json:
        json.dump(rows, sys.stdout, indent=2)
        print()
        return
    by_group = {}
    for r in rows:
        key = "plugin" if any(":plugin" in s or "claude.ai" in s for s in r["scopes"]) else "personal"
        by_group.setdefault(key, []).append(r)
    total = len(rows)
    print(f"{total} distinct skills (same file reached through several folders counts once)\n")
    for group in ("personal", "plugin"):
        items = by_group.get(group, [])
        if not items:
            continue
        print(f"## {'Your skills' if group == 'personal' else 'Plugin and claude.ai skills'} ({len(items)})\n")
        print("| Type this | Agents | Who can start it | What it does |")
        print("|---|---|---|---|")
        for r in items:
            who = "you only" if r["user_only"] else "you or the agent"
            flag = "" if r["valid"] else " (broken frontmatter)"
            print(f"| {' / '.join('`' + i + '`' for i in r['invoke'])} | {', '.join(r['agents'])} | {who} | {r['description'].replace('|', '/')}{flag} |")
        print()


if __name__ == "__main__":
    main()
