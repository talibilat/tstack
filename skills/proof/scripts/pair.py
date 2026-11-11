#!/usr/bin/env python3
"""pair.py: one annotated before and after picture per step.

The left half (before) is filled when the bug is reproduced. The right half (after)
is filled when the fix is ready, then every change is circled and numbered, each
step is checked against what was asked, and the picture is rebuilt.

  pair.py init     <KEY>                         steps from <KEY>-repro.md
  pair.py item     <KEY> N [--looking-at T] [--asked T] [--allow-identical WHY]
  pair.py textshot <KEY> N before|after [--title "$ command"]
                                                 terminal output (.txt) as an image
  pair.py diff     <KEY> N                       list the changed regions
  pair.py mark     <KEY> N --box x,y,w,h --label T [--type change|look]
                          [--sides both|before|after] [--before-box x,y,w,h] | --clear
  pair.py ignore   <KEY> N --box x,y,w,h --reason T
  pair.py verdict  <KEY> N match|no-match --note T
  pair.py render   <KEY>                         build compare/<step>.png for every step
  pair.py check    <KEY> [--stage before|after]  COMPLETE or NOT COMPLETE (exit 0 or 1)

All options take --dir (default .scratch). Boxes use the 900 pixel wide view that
`diff` prints, not the raw screenshot size. Evidence lives in <dir>/<KEY>-evidence/
(before/, after/, compare/). The step list lives in <dir>/<KEY>-proof.json.
"""
import argparse
import json
import re
import sys
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

W = 900  # width of each half in the picture
GAP = 20
CELL = 12  # change detection grid
THRESH = 24  # colour difference that counts as a changed pixel
MIN_FRACTION = 0.02  # share of changed pixels that makes a grid cell changed
MIN_SIDE = 12  # ignore changed regions smaller than this
EXTS = (".png", ".jpg", ".jpeg", ".webp")
RED, GREEN, GREY, BLUE, ORANGE = (200, 40, 40), (30, 140, 60), (110, 110, 110), (28, 126, 214), (232, 89, 12)


# ---------- paths and manifest ----------
def ev(args):
    return Path(args.dir) / f"{args.key}-evidence"


def manifest_path(args):
    return Path(args.dir) / f"{args.key}-proof.json"


def load(args):
    p = manifest_path(args)
    if not p.exists():
        sys.exit(f"no {p}. Run: pair.py init {args.key} --dir {args.dir}")
    return json.loads(p.read_text())


def save(args, data, rendered=False):
    now = time.time()
    data["modified"] = now
    if rendered:
        data["rendered"] = now
    manifest_path(args).write_text(json.dumps(data, indent=2) + "\n")


def get_item(data, n):
    for item in data["items"]:
        if item["n"] == n:
            return item
    sys.exit(f"no step {n}. Steps: {', '.join(str(i['n']) for i in data['items'])}")


def find_image(folder, stem):
    for ext in EXTS:
        p = folder / (stem + ext)
        if p.exists():
            return p
    return None


# ---------- fonts and text ----------
def font(size, mono=False):
    names = ["/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Monaco.ttf"] if mono else ["/System/Library/Fonts/Helvetica.ttc"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap(draw, text, fnt, max_width):
    lines = []
    for paragraph in str(text).splitlines() or [""]:
        line = ""
        for word in paragraph.split():
            trial = (line + " " + word).strip()
            if draw.textlength(trial, font=fnt) <= max_width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        lines.append(line)
    return lines


# ---------- images, changes, marks ----------
def normalize(path):
    img = Image.open(path).convert("RGB")
    return img, img.resize((W, max(1, round(img.height * W / img.width))), Image.Resampling.LANCZOS)


def regions(before, after):
    """Changed regions as (x, y, w, h) in the 900 wide view."""
    h = min(before.height, after.height)
    r, g, b = ImageChops.difference(before.crop((0, 0, W, h)), after.crop((0, 0, W, h))).split()
    diff = ImageChops.lighter(ImageChops.lighter(r, g), b)  # the biggest change in any colour channel
    mask = diff.point(lambda v: 255 if v > THRESH else 0)
    sw, sh = max(1, W // CELL), max(1, h // CELL + 1)
    small = mask.resize((sw, sh), Image.Resampling.BOX)
    cells = {(x, y) for y in range(sh) for x in range(sw) if small.getpixel((x, y)) > 255 * MIN_FRACTION}
    found, seen = [], set()
    for start in sorted(cells):
        if start in seen:
            continue
        stack, group = [start], []
        seen.add(start)
        while stack:
            cx, cy = stack.pop()
            group.append((cx, cy))
            for dx in range(-1, 2):  # touching cells belong to the same change
                for dy in range(-1, 2):
                    nxt = (cx + dx, cy + dy)
                    if nxt in cells and nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
        xs, ys = [c[0] for c in group], [c[1] for c in group]
        x0, y0, x1, y1 = min(xs) * CELL, min(ys) * CELL, (max(xs) + 1) * CELL, (max(ys) + 1) * CELL
        x1, y1 = min(x1, W), min(y1, h)
        if x1 - x0 >= MIN_SIDE and y1 - y0 >= MIN_SIDE:
            found.append((x0, y0, x1 - x0, y1 - y0))
    if abs(before.height - after.height) > 6:  # one picture is taller: the extra rows changed too
        tall, short = (before, after) if before.height > after.height else (after, before)
        found.append((0, short.height, W, tall.height - short.height))
    return sorted(found, key=lambda r: (r[1], r[0]))


def covered(region, boxes):
    """True when the marks together cover at least 40% of the changed region."""
    if not boxes:
        return False
    rx, ry, rw, rh = region
    points = [(rx + (i + 0.5) * rw / 12, ry + (j + 0.5) * rh / 12) for i in range(12) for j in range(12)]
    inside = sum(1 for px, py in points if any(x - 10 <= px <= x + w + 10 and y - 10 <= py <= y + h + 10 for x, y, w, h in boxes))
    return inside / len(points) >= 0.4


def parse_box(text):
    try:
        x, y, w, h = (int(float(v)) for v in text.split(","))
    except (ValueError, OverflowError):
        sys.exit(f"box '{text}' must be x,y,w,h in whole numbers")
    if w < 10 or h < 10 or x < 0 or y < 0:
        sys.exit("a box needs x and y of 0 or more, and a width and height of at least 10")
    return [x, y, w, h]


def draw_marks(panel, marks, side):
    draw = ImageDraw.Draw(panel)
    badge = font(22)
    for m in marks:
        if m["sides"] not in ("both", side):
            continue
        x, y, w, h = m["before_box"] if side == "before" and m.get("before_box") else m["box"]
        colour = BLUE if m["type"] == "look" else ORANGE
        rx, ry = w / 2 * 1.2 + 8, h / 2 * 1.2 + 8
        cx, cy = x + w / 2, y + h / 2
        if w > 2.5 * h:  # a wide, flat change gets a rounded box, because an oval would swallow its neighbours
            draw.rounded_rectangle((x - 8, y - 8, x + w + 8, y + h + 8), radius=22, outline=colour, width=5)
            rx, ry = w / 2 + 8, h / 2 + 8
        else:
            draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=colour, width=5)
        bx = min(max(cx - rx + 4, 20), W - 20)
        by = min(max(cy - ry + 4, 20), panel.height - 20)
        draw.ellipse((bx - 17, by - 17, bx + 17, by + 17), fill=colour)
        label = str(m["n"])
        draw.text((bx - draw.textlength(label, font=badge) / 2, by - 13), label, fill="white", font=badge)


# ---------- terminal output as an image ----------
def cmd_textshot(args):
    data = load(args)
    item = get_item(data, args.n)
    folder = ev(args) / args.stage
    source = folder / (item["step"] + ".txt")
    if not source.exists():
        sys.exit(f"{source} is missing. Save the real command output there first")
    fnt = font(20, mono=True)
    lines = [f"$ {args.title}"] if args.title else []
    text = source.read_text(errors="replace")
    if not text.strip():
        sys.exit(f"{source} is empty. Save the real command output there first")
    for raw in text.splitlines():
        lines += textwrap.wrap(raw, 100, replace_whitespace=False, drop_whitespace=False) or [""]
    if len(lines) > 60:  # keep the start and the end, because the error is often last
        lines = lines[:30] + [f"... {len(lines) - 58} lines left out, see {source.name} ..."] + lines[-28:]
    line_h, pad = 28, 28
    img = Image.new("RGB", (1200, max(400, len(lines) * line_h + pad * 2)), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        colour = (120, 200, 255) if args.title and i == 0 else (225, 225, 225)
        draw.text((pad, pad + i * line_h), line, fill=colour, font=fnt)
    target = folder / (item["step"] + ".png")
    img.save(target)
    print(f"wrote {target}")


# ---------- commands that edit the step list ----------
def rows_from_repro(args):
    repro = Path(args.dir) / f"{args.key}-repro.md"
    if not repro.exists():
        sys.exit(f"{repro} is missing. Write the repro steps first (reproduce step 1)")
    items = []
    for line in repro.read_text().splitlines():
        row = re.match(r"^\|\s*(\d+)\s*\|(.+)\|\s*([^|]+?)\s*\|\s*$", line)
        if not row:
            continue
        cells = [c.strip() for c in row.group(2).split("|")]
        name = row.group(3).strip().strip("`")
        items.append({
            "n": int(row.group(1)),
            "step": Path(name).stem,
            "kind": "terminal" if name.endswith(".txt") else "ui",
            "looking_at": cells[0] if cells else "",
            "asked": cells[1] if len(cells) > 1 else "",
            "marks": [], "ignore": [], "verdict": "pending", "note": "", "allow_identical": "",
        })
    return items


def cmd_init(args):
    items = rows_from_repro(args)
    if not items:
        sys.exit("the repro file has no numbered step rows")
    if manifest_path(args).exists() and not args.force:
        data = load(args)
        have = {i["n"] for i in data["items"]}
        added = [i for i in items if i["n"] not in have]
        data["items"] = sorted(data["items"] + added, key=lambda i: i["n"])
        save(args, data)
        print(f"kept {manifest_path(args).name}; added step(s) {[i['n'] for i in added] or 'none'}. Use --force to start over")
        return
    save(args, {"key": args.key, "items": items})
    print(f"created {manifest_path(args)} with {len(items)} step(s). Fix 'looking at' and 'asked' with: pair.py item")


def cmd_item(args):
    data = load(args)
    item = get_item(data, args.n)
    if args.looking_at is not None:
        item["looking_at"] = args.looking_at
    if args.asked is not None:
        item["asked"] = args.asked
    if args.allow_identical is not None:
        item["allow_identical"] = args.allow_identical
    save(args, data)
    print(f"step {args.n}: looking at '{item['looking_at']}', asked '{item['asked']}'")


def sizes(args, item):
    b = find_image(ev(args) / "before", item["step"])
    a = find_image(ev(args) / "after", item["step"])
    bn = normalize(b)[1] if b else None
    an = normalize(a)[1] if a else None
    return b, a, bn, an


def cmd_mark(args):
    data = load(args)
    item = get_item(data, args.n)
    if args.clear:
        item["marks"] = []
        item["verdict"], item["note"] = "pending", ""
        save(args, data)
        print(f"step {args.n}: marks cleared")
        return
    if not args.box or not args.label:
        sys.exit("give --box x,y,w,h and --label \"what the reviewer should see\"")
    box = parse_box(args.box)
    _, _, bn, an = sizes(args, item)
    ref = an or bn
    if ref is not None and (box[0] + box[2] > W or box[1] + box[3] > ref.height):
        sys.exit(f"box is outside the {W}x{ref.height} view. Run: pair.py diff {args.key} {args.n}")
    mark = {"n": len(item["marks"]) + 1, "box": box, "label": args.label, "type": args.type, "sides": args.sides}
    if args.before_box:
        mark["before_box"] = parse_box(args.before_box)
        bx = mark["before_box"]
        if bn is not None and (bx[0] + bx[2] > W or bx[1] + bx[3] > bn.height):
            sys.exit(f"--before-box is outside the {W}x{bn.height} before view")
    item["marks"].append(mark)
    item["verdict"], item["note"] = "pending", ""  # a changed picture must be judged again
    save(args, data)
    print(f"step {args.n}: mark {mark['n']} added ({args.type}): {args.label}")


def cmd_ignore(args):
    data = load(args)
    item = get_item(data, args.n)
    item["ignore"].append({"box": parse_box(args.box), "reason": args.reason})
    save(args, data)
    print(f"step {args.n}: ignoring that box because: {args.reason}")


def cmd_verdict(args):
    data = load(args)
    item = get_item(data, args.n)
    if args.verdict == "no-match" and not args.note:
        sys.exit("say what does not match with --note")
    item["verdict"] = "match" if args.verdict == "match" else "no-match"
    item["note"] = args.note or ""
    save(args, data)
    print(f"step {args.n}: {item['verdict']}")


def cmd_diff(args):
    data = load(args)
    item = get_item(data, args.n)
    b, a, bn, an = sizes(args, item)
    if bn is None:
        sys.exit("no before image for this step")
    print(f"step {args.n} ({item['step']}): before view {W}x{bn.height}" + (f", after view {W}x{an.height}" if an else ", after not captured yet"))
    if an is None:
        return
    boxes = [m["box"] for m in item["marks"]] + [i["box"] for i in item["ignore"]]
    found = regions(bn, an)
    if not found:
        print("no changed region found. The two pictures look the same")
    for i, r in enumerate(found, 1):
        state = "marked" if covered(r, boxes) else "NOT MARKED"
        print(f"change {i}: --box {r[0]},{r[1]},{r[2]},{r[3]}   {state}")


# ---------- rendering ----------
def render_item(args, item):
    b = find_image(ev(args) / "before", item["step"])
    a = find_image(ev(args) / "after", item["step"])
    if b is None:
        return None, "no before image"
    _, bn = normalize(b)
    an = normalize(a)[1] if a else None
    height = max(bn.height, an.height if an else bn.height)
    total_w = W * 2 + GAP

    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    f_txt, f_bar, f_big = font(22), font(34), font(26)
    caption = wrap(probe, f"LOOKING AT   {item['looking_at']}", f_txt, total_w - 40) + wrap(probe, f"ASKED   {item['asked']}", f_txt, total_w - 40)
    legend = []
    for m in item["marks"]:
        legend += wrap(probe, f"{m['n']}   {m['label']}", f_txt, total_w - 80)
    if item["note"]:
        legend += wrap(probe, f"Result: {item['note']}", f_txt, total_w - 40)
    bar_h, cap_h, leg_h = 64, 20 + 30 * len(caption), (20 + 30 * len(legend)) if legend else 0
    canvas = Image.new("RGB", (total_w, bar_h + cap_h + height + leg_h), "white")
    d = ImageDraw.Draw(canvas)

    d.rectangle([0, 0, W, bar_h], fill=RED)
    d.text((20, 14), f"{item['n']}.  BEFORE", fill="white", font=f_bar)
    d.rectangle([W + GAP, 0, total_w, bar_h], fill=GREEN if an else GREY)
    d.text((W + GAP + 20, 14), "AFTER" if an else "AFTER  (fills in when the fix is ready)", fill="white", font=f_bar)
    verdict = {"match": ("MATCHES WHAT WAS ASKED", (255, 255, 255)), "no-match": ("DOES NOT MATCH", (255, 220, 220))}.get(item["verdict"])
    if verdict and an:
        d.text((total_w - 20 - d.textlength(verdict[0], font=f_txt), 20), verdict[0], fill=verdict[1], font=f_txt)

    d.rectangle([0, bar_h, total_w, bar_h + cap_h], fill=(240, 240, 240))
    for i, line in enumerate(caption):
        d.text((20, bar_h + 12 + i * 30), line, fill=(30, 30, 30), font=f_txt)

    top = bar_h + cap_h
    left = bn.copy()
    draw_marks(left, item["marks"], "before")
    canvas.paste(left, (0, top))
    if an:
        right = an.copy()
        draw_marks(right, item["marks"], "after")
        canvas.paste(right, (W + GAP, top))
    else:
        d.rectangle([W + GAP, top, total_w, top + height], fill=(235, 235, 235))
        for i, line in enumerate(["AFTER is not captured yet.", "Run the same steps after the fix", "and it fills in here."]):
            d.text((W + GAP + 60, top + 80 + i * 38), line, fill=GREY, font=f_big)

    ly = top + height
    y = ly + 14
    for m in item["marks"]:
        colour = BLUE if m["type"] == "look" else ORANGE
        d.ellipse((20, y - 2, 46, y + 24), fill=colour)
        d.text((27, y), str(m["n"]), fill="white", font=font(20))
        for line in wrap(d, m["label"], f_txt, total_w - 90):
            d.text((60, y), line, fill=(30, 30, 30), font=f_txt)
            y += 30
    if item["note"]:
        for line in wrap(d, f"Result: {item['note']}", f_txt, total_w - 40):
            d.text((20, y), line, fill=(30, 30, 30), font=f_txt)
            y += 30

    out = ev(args) / "compare"
    out.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".jpg"):
        stale = out / (item["step"] + ext)
        if stale.exists():
            stale.unlink()
    target = out / (item["step"] + ".png")
    canvas.save(target, optimize=True)
    if target.stat().st_size > 1_000_000:  # keep each image under 1 MB
        target.unlink()
        target = out / (item["step"] + ".jpg")
        canvas.save(target, quality=82, optimize=True)
    return target, "both halves" if an else "left half only (after pending)"


def cmd_render(args):
    data = load(args)
    rows, bad = [], 0
    for item in data["items"]:
        target, state = render_item(args, item)
        if target is None:
            print(f"FAIL  step {item['n']}: {state}")
            bad += 1
            continue
        print(f"ok    compare/{target.name}  ({state})")
        rows.append(f"| {item['n']} | {item['looking_at']} | {item['asked']} | {item['verdict']} | `compare/{target.name}` |")
    out = ev(args) / "compare"
    if rows:
        (out / "compare.md").write_text("| # | Looking at | Asked | Result | Picture |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    save(args, data, rendered=True)
    return 1 if bad else 0


# ---------- checks ----------
def problems_before(args):
    if not manifest_path(args).exists():
        return [f"no {manifest_path(args).name}. Run pair.py init {args.key}, then pair.py render {args.key}"]
    data = load(args)
    found = []
    have = {i["n"]: i for i in data["items"]}
    for row in rows_from_repro(args):
        if row["n"] not in have:
            found.append(f"step {row['n']} is in the repro file but not in the proof file. Run pair.py init {args.key} to add it")
        elif have[row["n"]]["step"] != row["step"]:
            found.append(f"step {row['n']}: the repro file names {row['step']} but the proof file has {have[row['n']]['step']}. Run pair.py init {args.key} --force")
    for item in data["items"]:
        n = item["n"]
        if not item["looking_at"].strip() or not item["asked"].strip():
            found.append(f"step {n}: 'looking at' and 'asked' must both be written (pair.py item)")
        if find_image(ev(args) / "before", item["step"]) is None:
            found.append(f"step {n}: before/{item['step']} has no image" + (" (terminal step: run pair.py textshot)" if item["kind"] == "terminal" else ""))
        elif find_image(ev(args) / "compare", item["step"]) is None:
            found.append(f"step {n}: no left half yet. Run pair.py render {args.key}")
    return found


def problems_after(args):
    found = problems_before(args)
    if not manifest_path(args).exists():
        return found
    data = load(args)
    for item in data["items"]:
        n = item["n"]
        b, a, bn, an = sizes(args, item)
        if b is None:
            continue
        if a is None:
            found.append(f"step {n}: after not captured yet. Take it with the same steps and run pair.py render {args.key}")
            continue
        bo, ao = Image.open(b), Image.open(a)
        if abs(bo.width - ao.width) > 0.02 * bo.width:
            found.append(f"step {n}: before is {bo.width} px wide and after is {ao.width}. Retake with the same window size")
            continue
        changes = regions(bn, an)
        boxes = [m["box"] for m in item["marks"]] + [i["box"] for i in item["ignore"]]
        if not changes and not item["allow_identical"]:
            found.append(f"step {n}: before and after look the same, so nothing shows the fix. Check the fix is running, retake the after picture, or record why with pair.py item --allow-identical")
        for i, r in enumerate(changes, 1):
            if not covered(r, boxes):
                found.append(f"step {n}: change {i} at {r[0]},{r[1]},{r[2]},{r[3]} is not marked. Run pair.py diff {args.key} {n}, then pair.py mark with a label")
        if not item["marks"]:
            found.append(f"step {n}: nothing is circled. Add at least one numbered mark with a label")
        if item["verdict"] == "pending":
            found.append(f"step {n}: not judged yet. Compare it with what was asked, then run pair.py verdict")
        elif item["verdict"] == "no-match":
            found.append(f"step {n}: DOES NOT MATCH what was asked. {item['note']}")
        shown = find_image(ev(args) / "compare", item["step"])
        if data.get("rendered", 0) < data.get("modified", 0) or (shown and shown.stat().st_mtime < max(b.stat().st_mtime, a.stat().st_mtime)):
            found.append(f"step {n}: the picture is out of date. Run pair.py render {args.key}")
    return list(dict.fromkeys(found))


def cmd_check(args):
    if args.stage == "before":
        found = problems_before(args)
        label = "Proof (before half)"
    else:
        found = problems_after(args)
        label = "Proof"
    if not found:
        print(f"{label}: COMPLETE")
        return 0
    print(f"{label}: NOT COMPLETE. The work is not finished yet.")
    for line in found:
        print(f"  - {line}")
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, n=False):
        sp = sub.add_parser(name)
        sp.add_argument("key")
        if n:
            sp.add_argument("n", type=int)
        sp.add_argument("--dir", default=".scratch")
        sp.set_defaults(fn=fn)
        return sp

    add("init", cmd_init).add_argument("--force", action="store_true")
    sp = add("item", cmd_item, True)
    sp.add_argument("--looking-at")
    sp.add_argument("--asked")
    sp.add_argument("--allow-identical")
    sp = add("textshot", cmd_textshot, True)
    sp.add_argument("stage", choices=["before", "after"])
    sp.add_argument("--title")
    add("diff", cmd_diff, True)
    sp = add("mark", cmd_mark, True)
    sp.add_argument("--box")
    sp.add_argument("--label")
    sp.add_argument("--type", choices=["change", "look"], default="change")
    sp.add_argument("--sides", choices=["both", "before", "after"], default="both")
    sp.add_argument("--before-box")
    sp.add_argument("--clear", action="store_true")
    sp = add("ignore", cmd_ignore, True)
    sp.add_argument("--box", required=True)
    sp.add_argument("--reason", required=True)
    sp = add("verdict", cmd_verdict, True)
    sp.add_argument("verdict", choices=["match", "no-match"])
    sp.add_argument("--note")
    add("render", cmd_render)
    add("check", cmd_check).add_argument("--stage", choices=["before", "after"], default="after")

    args = ap.parse_args()
    sys.exit(args.fn(args) or 0)


if __name__ == "__main__":
    main()
