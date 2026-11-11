#!/usr/bin/env python3
"""todo.py: a temporary to-do list for one skill run, so no step is forgotten.

  todo.py new     <skill> [--key KEY] [--from <SKILL.md>] [item ...]   make the list
  todo.py add     <skill> [--key KEY] "item"                           a step found later
  todo.py tick    <skill> [--key KEY] N [N ...] [--note TEXT]          done, with the evidence
  todo.py block   <skill> [--key KEY] N "why it is stuck"
  todo.py unblock <skill> [--key KEY] N
  todo.py show    <skill> [--key KEY]                                  table, what is left, blockers

--from reads the numbered steps ("## 1. Title") or the numbered list under "## Steps" of a
SKILL.md, so the list always matches the skill. The list is a file, <dir>/todo-<skill>[-<KEY>].json
(--dir defaults to .scratch). When the last item is ticked, the file is deleted.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def path_for(args):
    tag = f"{args.skill}-{args.key}" if args.key else args.skill
    return Path(args.dir) / f"todo-{tag}.json"


def load(args):
    p = path_for(args)
    if not p.exists():
        sys.exit(f"no to-do list for {args.skill}. Make it first: todo.py new {args.skill} ...")
    return json.loads(p.read_text())


def save(args, data):
    p = path_for(args)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n")


def steps_from_skill(path):
    text = Path(path).read_text()
    items = [m.group(1).strip() for m in re.finditer(r"^##\s+(?:Step\s+)?\d+\.\s+(.+)$", text, re.M)]
    if not items:
        section = re.search(r"^##\s+Steps\s*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
        if section:
            for m in re.finditer(r"^\d+\.\s+(.+)$", section.group(1), re.M):
                first = re.sub(r"[*`]", "", m.group(1)).split(". ")[0].strip(" .")
                items.append(first)
    return [i[:90] for i in items]


def render(data):
    items = data["items"]
    done = sum(1 for i in items if i["done"])
    pct = round(100 * done / len(items)) if items else 0
    nxt = next((i["n"] for i in items if not i["done"] and not i["blocked"]), None)
    title = data["skill"] + (f" ({data['key']})" if data.get("key") else "")
    out = [f"To-do: {title}. {done} of {len(items)} done ({pct}%).", ""]
    out += ["| # | Step | Status | Note |", "|---|---|---|---|"]
    for i in items:
        status = "done" if i["done"] else "BLOCKED" if i["blocked"] else "next" if i["n"] == nxt else "to do"
        note = i["blocked"] if i["blocked"] and not i["done"] else i["note"]
        out.append(f"| {i['n']} | {i['text']} | {status} | {note} |")
    left = [i for i in items if not i["done"]]
    if left:
        out += ["", "Still to do:"] + [f"- [ ] {i['n']}. {i['text']}" for i in left]
    blocked = [i for i in left if i["blocked"]]
    if blocked:
        out += ["", "Blockers:"] + [f"- {i['n']}. {i['text']}: {i['blocked']}" for i in blocked]
    return "\n".join(out)


def finish_if_done(args, data):
    if data["items"] and all(i["done"] for i in data["items"]):
        print(render(data))
        path_for(args).unlink()
        print(f"\nAll ticked. The to-do list for {args.skill} is deleted.")
        return True
    return False


def cmd_new(args):
    if path_for(args).exists():
        print(f"kept the existing list ({path_for(args).name}). Use 'show' to see it")
        return
    items = list(args.items)
    if args.source:
        items = steps_from_skill(args.source) + items
    if not items:
        sys.exit("no steps found. Give the items after the skill name, for example: todo.py new guide \"read the chat\" \"answer\"")
    data = {"skill": args.skill, "key": args.key,
            "items": [{"n": n, "text": t, "done": False, "blocked": "", "note": ""} for n, t in enumerate(items, 1)]}
    save(args, data)
    print(render(data))


def cmd_add(args):
    data = load(args)
    data["items"].append({"n": len(data["items"]) + 1, "text": args.text, "done": False, "blocked": "", "note": ""})
    save(args, data)
    print(f"added step {len(data['items'])}: {args.text}")


def item(data, n):
    for i in data["items"]:
        if i["n"] == n:
            return i
    sys.exit(f"no step {n}. Steps are 1 to {len(data['items'])}")


def cmd_tick(args):
    data = load(args)
    for n in args.numbers:
        i = item(data, n)
        i["done"], i["blocked"] = True, ""
        if args.note:
            i["note"] = args.note
    if finish_if_done(args, data):
        return
    save(args, data)
    print(render(data))


def cmd_block(args):
    data = load(args)
    item(data, args.n)["blocked"] = args.why
    save(args, data)
    print(render(data))


def cmd_unblock(args):
    data = load(args)
    item(data, args.n)["blocked"] = ""
    save(args, data)
    print(render(data))


def cmd_show(args):
    print(render(load(args)))


def reorder(argv):
    """Let options come before or after the items: move them to the end, after the positional items."""
    options, rest, skip = [], [], False
    for i, token in enumerate(argv):
        if skip:
            skip = False
        elif token in ("--key", "--dir", "--from", "--note") and i + 1 < len(argv):
            options += [token, argv[i + 1]]
            skip = True
        else:
            rest.append(token)
    return rest + options


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn):
        sp = sub.add_parser(name)
        sp.add_argument("skill")
        sp.add_argument("--key")
        sp.add_argument("--dir", default=".scratch")
        sp.set_defaults(fn=fn)
        return sp

    sp = add("new", cmd_new)
    sp.add_argument("--from", dest="source")
    sp.add_argument("items", nargs="*")
    add("add", cmd_add).add_argument("text")
    sp = add("tick", cmd_tick)
    sp.add_argument("numbers", nargs="+", type=int)
    sp.add_argument("--note")
    sp = add("block", cmd_block)
    sp.add_argument("n", type=int)
    sp.add_argument("why")
    add("unblock", cmd_unblock).add_argument("n", type=int)
    add("show", cmd_show)
    args = ap.parse_args(reorder(sys.argv[1:]))
    args.fn(args)


if __name__ == "__main__":
    main()
