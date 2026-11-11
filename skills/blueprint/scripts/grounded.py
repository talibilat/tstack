#!/usr/bin/env python3
"""grounded.py: checks that every decision in a plan rests on something written in Jira.

  grounded.py check <KEY> [--dir .scratch] [--stage decisions|grill|all]

Reads, under <dir>:
  <KEY>-decisions.md          | # | Decision | Kind | Backed by | Quote or evidence |
  <KEY>-reviews/grill.md      | Q | Question | Answer | Source | Quote | Decision | Plan agrees |
  <KEY>-plan.md               its "Blockers" section must list every answer that is NOT IN JIRA

Rules:
  requirement decision   Backed by names a Jira ticket key, a Confluence page or an attachment,
                         and the quote is the BA's own words (10 characters or more)
  build choice           the evidence is a file:line or a research or review file
  grill answer           has a source and a quote, or says NOT IN JIRA and is listed as a blocker
  every requirement decision is checked by at least one grill question

Exit code 0 means PASS.
"""
import argparse
import re
import sys
from pathlib import Path

KEY = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")
FILE_LINE = re.compile(r"[\w./@-]+\.\w+:\d+")
PLACEHOLDER = re.compile(r"<[^>]*>|^\s*(tbd|todo|\.\.\.|n/?a|-)\s*$", re.I)
NOT_FOUND = "not in jira"


def table(path, must_have):
    """Rows of the first markdown table whose header holds every word in must_have."""
    lines = [l.strip() for l in path.read_text().splitlines() if l.strip().startswith("|")]
    header, rows = None, []
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        low = [c.lower() for c in cells]
        if header is None:
            if all(any(w in c for c in low) for w in must_have):
                header = low
            continue
        if len(cells) >= len(header):
            rows.append(dict(zip(header, cells)))
    return header, rows


def col(row, *names):
    for key, value in row.items():
        if any(n in key for n in names):
            return value
    return ""


class Report:
    def __init__(self):
        self.failures = []

    def fail(self, text):
        self.failures.append(text)
        print(f"FAIL  {text}")

    def ok(self, text):
        print(f"ok    {text}")


def real(text, minimum=1):
    return len(text.strip()) >= minimum and not PLACEHOLDER.search(text)


def check_decisions(args, report):
    path = Path(args.dir) / f"{args.key}-decisions.md"
    if not path.exists():
        report.fail(f"{path.name} is missing. Every decision gets a row (see requirements.md)")
        return []
    header, rows = table(path, ["decision", "backed by"])
    rows = [r for r in rows if re.match(r"^d?\d+$", col(r, "#"), re.I)]
    if header is None or not rows:
        report.fail(f"{path.name} has no decision rows with the columns # | Decision | Kind | Backed by | Quote or evidence")
        return []
    requirement_numbers = []
    for r in rows:
        n = col(r, "#")
        kind, backed, proof = col(r, "kind").lower(), col(r, "backed by"), col(r, "quote", "evidence")
        if not real(col(r, "decision"), 5):
            report.fail(f"decision {n} is empty")
        if kind == "requirement":
            requirement_numbers.append(re.sub(r"\D", "", n))
            if not (KEY.search(backed) or re.search(r"confluence|attachment|page", backed, re.I)):
                report.fail(f"decision {n} is a requirement but 'Backed by' names no Jira ticket, Confluence page or attachment: '{backed[:50]}'")
            elif not real(proof, 10):
                report.fail(f"decision {n} is a requirement with no quote of the BA's words")
            else:
                report.ok(f"decision {n} (requirement) rests on {backed[:50]}")
        elif kind == "build choice":
            if not (FILE_LINE.search(proof + " " + backed) or re.search(r"-(research|reviews)/", proof + " " + backed)):
                report.fail(f"decision {n} is a build choice with no file:line or research file as evidence")
            else:
                report.ok(f"decision {n} (build choice) has code evidence")
        else:
            report.fail(f"decision {n} has kind '{kind}'. Use 'requirement' or 'build choice'")
    return requirement_numbers


def blockers_text(args):
    plan = Path(args.dir) / f"{args.key}-plan.md"
    if not plan.exists():
        return ""
    text = plan.read_text()
    match = re.search(r"##\s*Blockers[^\n]*\n(.*?)(?=\n##\s|\Z)", text, re.S | re.I)
    return match.group(1) if match else ""


def check_grill(args, report, requirement_numbers):
    path = Path(args.dir) / f"{args.key}-reviews" / "grill.md"
    if not path.exists():
        report.fail(f"{path.parent.name}/{path.name} is missing. Run the Jira-only grilling (blueprint step 8)")
        return
    header, rows = table(path, ["question", "answer", "source", "quote"])
    rows = [r for r in rows if re.match(r"^q?\d+$", col(r, "q", "#"), re.I) or col(r, "question")]
    if header is None or not rows:
        report.fail("grill.md has no rows with the columns Q | Question | Answer | Source | Quote | Decision | Plan agrees")
        return
    if len(rows) > 15:
        report.fail(f"the grilling has {len(rows)} questions. It is a small session: keep it to 15 or fewer")
    blockers = blockers_text(args)
    covered, found_nothing = set(), {}
    for r in rows:
        q = col(r, "q", "#") or "?"
        answer, source, quote = col(r, "answer"), col(r, "source"), col(r, "quote")
        agrees = col(r, "plan agrees").lower()
        numbers = re.findall(r"\d+", col(r, "decision"))
        has_answer = not answer.strip().lower().startswith(NOT_FOUND)
        for n in numbers:
            found_nothing.setdefault(n, []).append(has_answer)
            if has_answer:
                covered.add(n)
        if agrees not in ("yes", "changed", "blocker"):
            report.fail(f"{q}: 'Plan agrees' must be yes, changed or blocker, not '{agrees}'")
        if answer.strip().lower().startswith(NOT_FOUND):
            if not re.search(rf"\b{re.escape(q)}\b", blockers):
                report.fail(f"{q} is NOT IN JIRA but is not listed under Blockers in the plan")
            elif agrees != "blocker":
                report.fail(f"{q} is NOT IN JIRA, so 'Plan agrees' must be blocker")
            else:
                report.ok(f"{q} is NOT IN JIRA and is a blocker")
            continue
        if not real(answer, 3):
            report.fail(f"{q} has no answer")
        elif not (KEY.search(source) or re.search(r"confluence|attachment|page", source, re.I)):
            report.fail(f"{q}: the source '{source[:40]}' names no Jira ticket, Confluence page or attachment")
        elif not real(quote, 10):
            report.fail(f"{q}: the answer has no quote from the source")
        else:
            report.ok(f"{q} answered from {source[:50]}")
    for n in requirement_numbers:
        if n and n not in found_nothing:
            report.fail(f"requirement decision {n} was not checked by any grill question")
        elif n and n not in covered:
            report.fail(f"decision {n} is written as a requirement with a quote, but the grilling found nothing in Jira. Drop it as a requirement or fix its source")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("check")
    sp.add_argument("key")
    sp.add_argument("--dir", default=".scratch")
    sp.add_argument("--stage", choices=["decisions", "grill", "all"], default="all")
    args = ap.parse_args()

    report = Report()
    numbers = check_decisions(args, report)
    if args.stage in ("grill", "all"):
        check_grill(args, report, numbers)
    if report.failures:
        print(f"\ngrounded: FAIL ({len(report.failures)}). A decision without a Jira source is not made. Ground it, change it, or make it a blocker.")
        sys.exit(1)
    print("\ngrounded: PASS")


if __name__ == "__main__":
    main()
