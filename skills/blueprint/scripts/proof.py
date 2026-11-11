#!/usr/bin/env python3
"""Proof gate: checks the before and after proof, builds the comparison images,
and checks they reached Jira and GitHub. Proof cannot be skipped unless the user
says so, and then the skip is written down in SKIPPED-BY-USER.txt.

  proof.py gate before  <KEY> [--dir .scratch]
  proof.py gate after   <KEY> [--dir .scratch] [--allow-identical NAME ...]
  proof.py compare      <KEY> [--dir .scratch]
  proof.py attach       <KEY> [--dir .scratch]      upload the comparison images and logs to the Jira ticket
  proof.py verify       <KEY> --pr <org/repo#number> [--pr ...] [--dir .scratch]

Layout, under <dir>/<KEY>-evidence/:
  before/   screenshots and logs taken while the bug happens (never overwritten)
  after/    the same steps, same file names, after the fix
  compare/  one side-by-side image per step, plus compare.md

Exit code 0 means PASS. Any FAIL line means the work does not move on.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
LOG_EXT = {".txt", ".log"}
MIN_IMAGE_BYTES = 5_000
SIGNATURES = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"RIFF")


def evidence_dir(args):
    return Path(args.dir) / f"{args.key}-evidence"


def repro_file(args):
    return Path(args.dir) / f"{args.key}-repro.md"


class Report:
    def __init__(self):
        self.failures = []

    def ok(self, text):
        print(f"ok    {text}")

    def fail(self, text):
        self.failures.append(text)
        print(f"FAIL  {text}")

    def finish(self, label):
        if self.failures:
            print(f"\n{label}: FAIL ({len(self.failures)} problem{'s' if len(self.failures) != 1 else ''}). Do not move on. Fix these first.")
            return 1
        print(f"\n{label}: PASS")
        return 0


def skipped_by_user(args):
    note = evidence_dir(args) / "SKIPPED-BY-USER.txt"
    return note.exists() and note.read_text().strip()


def images_in(folder):
    return sorted(p for p in folder.glob("*") if p.suffix.lower() in IMAGE_EXT) if folder.is_dir() else []


def logs_in(folder):
    return sorted(p for p in folder.glob("*") if p.suffix.lower() in LOG_EXT) if folder.is_dir() else []


def check_image(path, report):
    data = path.read_bytes()
    if len(data) < MIN_IMAGE_BYTES:
        report.fail(f"{path.name} is only {len(data)} bytes, too small to be a real screenshot")
        return False
    if not data.startswith(SIGNATURES):
        report.fail(f"{path.name} is not a PNG, JPEG or WebP image")
        return False
    try:
        from PIL import Image

        with Image.open(path) as img:
            img.load()  # fully decode, so a truncated or corrupt file fails here
            if img.width < 600 or img.height < 300:
                report.fail(f"{path.name} is {img.width}x{img.height}, too small to be a real screenshot")
                return False
            low, high = img.convert("L").getextrema()
            if low == high:
                report.fail(f"{path.name} is one flat colour (blank screenshot)")
                return False
    except ImportError:
        pass
    except Exception as err:  # unreadable image
        report.fail(f"{path.name} cannot be opened: {err}")
        return False
    return True


def parse_repro(args, report):
    """Returns (result, method_ok, step_files) from <KEY>-repro.md."""
    path = repro_file(args)
    if not path.exists():
        report.fail(f"{path} is missing. Write the repro steps first (reproduce step 1)")
        return None, [], []
    lines = path.read_text().splitlines()
    first = lines[0].strip() if lines else ""
    match = re.match(r"Reproduced:\s*(.+)", first)
    result = match.group(1).strip().lower() if match else None
    head = "\n".join(lines[:10])
    env = re.search(r"^Live environment:\s*(.+)$", head, re.M)
    if not env or "<" in env.group(1):
        report.fail("the repro file has no 'Live environment:' line naming the lane, Docker stack or dev environment")
    else:
        report.ok(f"live environment: {env.group(1).strip()[:90]}")
    method = re.search(r"^Method:\s*(.+)$", head, re.M)
    if not method or "<" in method.group(1):
        report.fail("the repro file has no 'Method:' line (visible Chrome, Docker lane, or a script with the reason)")
    elif re.search(r"headless|script|background", method.group(1), re.I) and "because" not in method.group(1).lower():
        report.fail("Method says a script or headless run but gives no reason. Use visible Chrome or Docker, or write 'because ...'")
    else:
        report.ok(f"method: {method.group(1).strip()[:90]}")
    steps = []
    for line in lines:
        row = re.match(r"^\|\s*(\d+)\s*\|.*\|\s*([^|]+?)\s*\|\s*$", line)
        if row:
            steps.append(row.group(2).strip().strip("`"))
    return result, method, steps


def gate_before(args):
    report = Report()
    if skipped_by_user(args):
        print("Proof was skipped at the user's request:", (evidence_dir(args) / "SKIPPED-BY-USER.txt").read_text().strip())
        return 0
    result, _, steps = parse_repro(args, report)
    if result is None:
        report.fail("the first line of the repro file must be 'Reproduced: yes' (or 'not a bug')")
    elif result in ("yes", "not a bug"):
        report.ok(f"Reproduced: {result}")
    else:
        report.fail(f"Reproduced: {result}. The bug has not happened in the live environment, so nothing moves forward. Say what blocks it and resolve that")
    before = evidence_dir(args) / "before"
    if not steps:
        report.fail("the repro file has no numbered step rows with a proof file name in the last column")
    for name in steps:
        target = before / name
        if not target.exists():
            report.fail(f"before/{name} is missing")
        elif target.suffix.lower() in IMAGE_EXT and check_image(target, report):
            report.ok(f"before/{name}")
    if result == "yes" and not logs_in(before):
        report.fail("before/ has no log file (.txt or .log) for the failing action")
    elif result == "yes":
        report.ok(f"{len(logs_in(before))} log file(s) in before/")
    for problem in load_pair().problems_before(pair_args(args, "before")):
        report.fail(problem)
    return report.finish("before gate")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate_after(args):
    report = Report()
    if skipped_by_user(args):
        print("Proof was skipped at the user's request:", (evidence_dir(args) / "SKIPPED-BY-USER.txt").read_text().strip())
        return 0
    print("-- the before side")
    if gate_before(args) != 0:
        report.fail("the before gate does not pass, so there is nothing to compare against")
        return report.finish("after gate")
    print("-- the after side")
    before, after = evidence_dir(args) / "before", evidence_dir(args) / "after"
    allowed = set(args.allow_identical or [])
    for shot in images_in(before):
        twin = next((after / (shot.stem + ext) for ext in IMAGE_EXT if (after / (shot.stem + ext)).exists()), None)
        if twin is None:
            report.fail(f"after/{shot.stem}.* is missing. Take it with the same steps and the same file name")
            continue
        if not check_image(twin, report):
            continue
        if digest(shot) == digest(twin) and shot.name not in allowed:
            report.fail(f"after/{shot.name} is identical to the before image, so it proves nothing. Check the fix is running, or pass --allow-identical {shot.name}")
        else:
            report.ok(f"after/{shot.name}")
    if not logs_in(after):
        report.fail("after/ has no log file (.txt or .log) for the same action")
    for problem in load_pair().problems_after(pair_args(args)):
        report.fail(problem)
    return report.finish("after gate")


def load_pair():
    """Load pair.py from the proof skill, which sits next to this skill."""
    for base in (Path(__file__), Path(__file__).resolve()):
        path = base.parents[2] / "proof" / "scripts" / "pair.py"
        if path.exists():
            spec = importlib.util.spec_from_file_location("pair", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    sys.exit("the proof skill is not installed next to this one (skills/proof/scripts/pair.py)")


def pair_args(args, stage="after"):
    return argparse.Namespace(key=args.key, dir=args.dir, stage=stage)


def compare(args):
    """Builds the annotated before and after pictures with the proof skill's pair.py."""
    return load_pair().cmd_render(pair_args(args))


def load_jira():
    path = Path(__file__).with_name("jira-attach.py")
    spec = importlib.util.spec_from_file_location("jira_attach", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def attach(args):
    report = Report()
    root_dir = evidence_dir(args)
    uploads = [(p, p.name) for p in images_in(root_dir / "compare")]
    for stage in ("before", "after"):
        uploads += [(p, f"{stage}-{p.name}") for p in logs_in(root_dir / stage)]
    if not uploads:
        report.fail("nothing to attach. Run: proof.py compare " + args.key)
        return report.finish("attach")
    jira = load_jira()
    cfg = jira.settings()
    data = jira.call(cfg, f"/rest/api/3/issue/{args.key}?fields=attachment")
    have = {a["filename"] for a in data["fields"].get("attachment", [])}
    for path, name in uploads:
        if name in have:
            report.ok(f"{name} already on {args.key}")
            continue
        jira.attach(cfg, args.key, path, name=name)
        report.ok(f"attached {name}")
    return report.finish("attach")


def verify(args):
    report = Report()
    if skipped_by_user(args):
        print("Proof was skipped at the user's request:", (evidence_dir(args) / "SKIPPED-BY-USER.txt").read_text().strip())
        return 0
    names = sorted(p.name for p in images_in(evidence_dir(args) / "compare"))
    if not names:
        report.fail("compare/ has no images. Run: proof.py compare " + args.key)
        return report.finish("publish check")
    print("-- Jira")
    jira = load_jira()
    cfg = jira.settings()
    data = jira.call(cfg, f"/rest/api/3/issue/{args.key}?fields=attachment")
    attached = {a["filename"] for a in data["fields"].get("attachment", [])}
    for name in names:
        report.ok(f"Jira has {name}") if name in attached else report.fail(f"{name} is not attached to {args.key}. Run: jira-attach.py {args.key} <file>")
    print("-- GitHub")
    if not args.pr:
        report.fail("no --pr given. Check every PR: --pr <org/repo#number>")
    for ref in args.pr or []:
        repo, _, number = ref.partition("#")
        body = subprocess.run(
            ["gh", "pr", "view", number, "-R", repo, "--json", "body", "-q", ".body"],
            capture_output=True, text=True,
        )
        if body.returncode != 0:
            report.fail(f"could not read {ref}: {body.stderr.strip()[:100]}")
            continue
        for name in names:
            report.ok(f"{ref} shows {name}") if name in body.stdout else report.fail(f"{ref} does not show {name} in its description")
    return report.finish("publish check")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    gate = sub.add_parser("gate")
    gate.add_argument("stage", choices=["before", "after"])
    gate.add_argument("key")
    gate.add_argument("--dir", default=".scratch")
    gate.add_argument("--allow-identical", nargs="*")
    for name in ("compare", "attach", "verify"):
        sp = sub.add_parser(name)
        sp.add_argument("key")
        sp.add_argument("--dir", default=".scratch")
        if name == "verify":
            sp.add_argument("--pr", action="append")
    args = ap.parse_args()
    if args.cmd == "gate":
        code = gate_before(args) if args.stage == "before" else gate_after(args)
    else:
        code = {"compare": compare, "attach": attach, "verify": verify}[args.cmd](args)
    sys.exit(code)


if __name__ == "__main__":
    main()
