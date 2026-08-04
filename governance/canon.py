#!/usr/bin/env python3
"""Canon document hygiene — front matter validation, history-pattern scan, archiving.

The canon documents state the current state and nothing else. History lives in archive/.
Rules: governance/CANON-RULES.md (D-017).

    python governance/canon.py check
    python governance/canon.py check --doc ROADMAP
    python governance/canon.py archive ROADMAP --section "Open questions" --why "answered"
    python governance/canon.py fm ROADMAP            # print parsed front matter

Standard library only, same as checkpoint.py.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCHIVE = REPO / "archive"

# doc stem -> owner. Canon is a closed set; adding to it is a deliberate act.
CANON = {
    "GOALS": "vince",
    "PRODUCT_SPEC": "agents",
    "ROADMAP": "agents",
    "SKILL-INVENTORY": "agents",
    "DECISIONS": "agents",
    "PROPOSALS": "agents",
    "AGENTS": "agents",
    "README": "agents",
    "USER-GUIDE": "agents",
}

REQUIRED_KEYS = ["doc", "role", "authority", "owner", "updated", "answers"]
ROLES = {"north-star", "current-state", "current-work", "inventory",
         "law", "backlog", "index", "guide"}
AUTHORITIES = {"canon", "derived", "archive"}

# Patterns that mean "this sentence is about the past". Each is (regex, human name).
HISTORY_PATTERNS = [
    (r"~~[^~]+~~", "strikethrough"),
    (r"\((?:Resolved|Fixed|Answered|Closed)\s+\d{4}-\d{2}-\d{2}\.?\)", "resolved-stamp"),
    (r"(?:✅|\*\*)\s*(?:EFFECTIVELY\s+)?ANSWERED\s+\d{4}-\d{2}-\d{2}", "answered-stamp"),
    (r"\bReclassified\b[^.\n]*→", "reclassification note"),
    (r"\b(?:the\s+)?(?:revised|rewritten|updated|new)\s+`?(?:GOALS|PRODUCT_SPEC|ROADMAP)", "doc-revision narration"),
    (r"\bno longer (?:exists|just stale|only)\b", "no-longer narration"),
    (r"\b(?:used to be|previously was|formerly known as)\b", "past-tense narration"),
    (r"\bVerified (?:against[^.\n]*)?\d{4}-\d{2}-\d{2}", "verification stamp"),
    (r"\bas of \d{4}-\d{2}-\d{2}\b", "as-of stamp"),
]

# Lines that legitimately mention history because they ARE the rule about history.
EXEMPT_LINE = re.compile(
    r"(?:CANON-RULES|archive/|governance/canon\.py|banned|Banned|Instead|\| Pattern \|)",
)


def split_front_matter(text: str) -> tuple[dict, str, int]:
    """Return (front matter dict, body, body_start_line). Naive YAML — flat keys, lists, maps."""
    if not text.startswith("---\n"):
        return {}, text, 1
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text, 1
    raw = text[4:end]
    body = text[end + 5:]
    fm: dict = {}
    key = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if not isinstance(fm.get(key), list):
                fm[key] = []
            fm[key].append(line[4:].strip())
        elif line.startswith("  ") and ":" in line:
            sub_k, sub_v = line.strip().split(":", 1)
            if not isinstance(fm.get(key), dict):
                fm[key] = {}
            fm[key][sub_k.strip()] = sub_v.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            key, value = key.strip(), value.strip()
            fm[key] = value if value else None
    return fm, body, raw.count("\n") + 3


def canon_path(stem: str) -> Path:
    return REPO / f"{stem}.md"


def check_doc(stem: str) -> list[str]:
    path = canon_path(stem)
    if not path.exists():
        return [f"{stem}.md: missing"]
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body, offset = split_front_matter(text)
    problems: list[str] = []

    if not fm:
        return [f"{stem}.md: no YAML front matter (see governance/CANON-RULES.md)"]

    for key in REQUIRED_KEYS:
        if key not in fm or fm[key] in (None, "", [], {}):
            problems.append(f"{stem}.md: front matter missing `{key}`")

    if fm.get("doc") != stem:
        problems.append(f"{stem}.md: front matter `doc: {fm.get('doc')}` does not match filename")
    if fm.get("role") not in ROLES:
        problems.append(f"{stem}.md: role `{fm.get('role')}` not one of {sorted(ROLES)}")
    if fm.get("authority") not in AUTHORITIES:
        problems.append(f"{stem}.md: authority `{fm.get('authority')}` not one of {sorted(AUTHORITIES)}")
    if fm.get("owner") != CANON[stem]:
        problems.append(f"{stem}.md: owner should be `{CANON[stem]}`")
    try:
        dt.date.fromisoformat(str(fm.get("updated")))
    except (TypeError, ValueError):
        problems.append(f"{stem}.md: `updated` is not an ISO date")
    answers = fm.get("answers") or []
    if isinstance(answers, list):
        if not 2 <= len(answers) <= 5:
            problems.append(f"{stem}.md: `answers` has {len(answers)} entries; want 2–5")
        for a in answers:
            if a.endswith("?") or a[:1].isupper():
                problems.append(f"{stem}.md: answer should be lowercase and unpunctuated — {a!r}")

    # DECISIONS keeps laws only; its arguments live in archive/decisions/.
    for i, line in enumerate(body.splitlines(), start=offset):
        if EXEMPT_LINE.search(line):
            continue
        for pattern, name in HISTORY_PATTERNS:
            if re.search(pattern, line):
                problems.append(f"{stem}.md:{i}: {name} — history belongs in {fm.get('archive', 'archive/')}")
                break
    return problems


def cmd_check(args) -> int:
    stems = [args.doc] if args.doc else sorted(CANON)
    problems: list[str] = []
    for stem in stems:
        if stem not in CANON:
            print(f"[canon] {stem} is not a canon document", file=sys.stderr)
            return 2
        problems += check_doc(stem)
    if problems:
        print(f"[canon] {len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print(f"[canon] {len(stems)} document(s) clean")
    return 0


def cmd_archive(args) -> int:
    """Move a whole ## section out of a canon doc into its archive file."""
    stem = args.doc
    if stem not in CANON:
        print(f"[canon] {stem} is not a canon document", file=sys.stderr)
        return 2
    path = canon_path(stem)
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, _, _ = split_front_matter(text)
    target = REPO / (fm.get("archive") or f"archive/{stem.lower()}.md")

    pattern = re.compile(
        rf"^##\s+{re.escape(args.section)}\s*$.*?(?=^##\s|\Z)",
        re.M | re.S,
    )
    match = pattern.search(text)
    if not match:
        print(f"[canon] section '{args.section}' not found in {stem}.md", file=sys.stderr)
        return 1
    block = match.group(0).rstrip() + "\n"

    today = dt.date.today().isoformat()
    entry = (f"\n## {today} · from {stem}.md § {args.section}\n"
             f"**Why:** {args.why}\n\n" + block + "\n---\n")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text(
            f"# Archive — {stem}.md\n\n"
            "*Append-only. Removed from canon, kept for the trail. Not read by default.*\n\n---\n",
            encoding="utf-8")
    with target.open("a", encoding="utf-8") as fh:
        fh.write(entry)

    path.write_text(text[:match.start()] + text[match.end():], encoding="utf-8")
    print(f"[canon] moved {stem}.md § {args.section} → {target.relative_to(REPO)}")
    return 0


def cmd_fm(args) -> int:
    fm, _, _ = split_front_matter(canon_path(args.doc).read_text(encoding="utf-8", errors="replace"))
    for k, v in fm.items():
        print(f"{k}: {v}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Canon document hygiene.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="validate front matter and scan for history patterns")
    c.add_argument("--doc", help="one canon doc stem, e.g. ROADMAP")
    c.set_defaults(func=cmd_check)

    a = sub.add_parser("archive", help="move a section out of canon into its archive file")
    a.add_argument("doc")
    a.add_argument("--section", required=True, help="exact ## heading text")
    a.add_argument("--why", required=True, help="one line: why it left canon")
    a.set_defaults(func=cmd_archive)

    f = sub.add_parser("fm", help="print a doc's parsed front matter")
    f.add_argument("doc")
    f.set_defaults(func=cmd_fm)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
