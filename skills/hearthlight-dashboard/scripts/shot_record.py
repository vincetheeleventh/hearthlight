#!/usr/bin/env python3
"""
The canonical shot record.

`05-storyboard/shots.json` is the single source of truth for what a shot is.
The spreadsheet is no longer upstream of it — it becomes an export
(`export_shotlist.py`).

Why: the workbook was read by two consumers that used different columns, and
nothing kept them agreeing. A spreadsheet cell also carries no revision, no
author and no reason. Shot 2's still prompt drifted from its Shot Vision that
way and cost a paid generation.

What this adds to each shot:

    "prompt": {
      "still":   "<frame-one prompt — the ONLY source for image generation>",
      "action":  "<motion text — video only>",
      "revision": 1,
      "updated_at": "...", "updated_by": "...", "source": "..."
    }

Every change is appended to `05-storyboard/shot-edits.jsonl` — append-only,
attributable, and diffable, the way `shot-vision.jsonl` already works.

Commands
--------
    shot_record.py show    --project yugioh [--shot 2]
    shot_record.py migrate --project yugioh --workbook 05-storyboard/x.xlsx [--dry-run]
    shot_record.py set     --project yugioh --shot 2 --field still \\
                           --value "..." --by vince --reason "..."
    shot_record.py verify  --project yugioh --workbook 05-storyboard/x.xlsx
    shot_record.py history --project yugioh --shot 2

Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import uuid
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3]
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
FIELDS = {"still": "Still (frame one)", "action": "Action (motion — video only)"}
AUTHORS = ["vince", "cowork", "hermes", "chatgpt"]


def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def project_dir(slug: str) -> Path:
    p = STUDIO / "projects" / slug
    if not p.is_dir():
        fail(f"no project at {p}")
    return p


def registry_path(project: Path) -> Path:
    p = project / "05-storyboard" / "shots.json"
    if not p.is_file():
        fail(f"no shot registry at {p}")
    return p


def load_registry(project: Path) -> tuple[dict, list]:
    doc = json.loads(registry_path(project).read_text(encoding="utf-8"))
    shots = doc["shots"] if isinstance(doc, dict) and "shots" in doc else doc
    return doc, shots


def save_registry(project: Path, doc: dict) -> None:
    registry_path(project).write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def find_shot(shots: list, ref: str) -> dict:
    for s in shots:
        if str(s.get("display_number")) == str(ref):
            return s
    for s in shots:
        if str(s.get("shot_id")) == str(ref):
            return s
    for s in shots:
        if str(ref) in [str(x) for x in (s.get("legacy_numbers") or [])]:
            return s
    fail(f"no shot matching {ref!r}")


# ── workbook reading (migration + verification only) ─────────────────────────

def xlsx_rows(path: Path, sheet: str = "Shot List") -> list[list[str]]:
    """Minimal .xlsx reader — same approach as build_shot_registry.py."""
    with zipfile.ZipFile(path) as book:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in book.namelist():
            root = ET.fromstring(book.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        wb = ET.fromstring(book.read("xl/workbook.xml"))
        rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        rel_map = {r.get("Id"): r.get("Target") for r in rels}
        target = None
        for s in wb.findall("m:sheets/m:sheet", NS):
            if s.get("name") == sheet:
                rid = s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
                target = rel_map.get(rid)
        if not target:
            fail(f"sheet {sheet!r} not found in {path.name}")
        name = "xl/" + target.lstrip("/").replace("worksheets/", "worksheets/")
        if name not in book.namelist():
            name = "xl/" + target.lstrip("/")
        sheet_xml = ET.fromstring(book.read(name))
        out: list[list[str]] = []
        for row in sheet_xml.findall(".//m:sheetData/m:row", NS):
            cells: dict[int, str] = {}
            for c in row.findall("m:c", NS):
                ref = c.get("r") or ""
                col = 0
                for ch in re.match(r"[A-Z]*", ref).group(0):
                    col = col * 26 + (ord(ch) - 64)
                col -= 1
                v = c.find("m:v", NS)
                is_el = c.find("m:is", NS)
                if c.get("t") == "s" and v is not None:
                    text = shared[int(v.text)] if v.text and int(v.text) < len(shared) else ""
                elif is_el is not None:
                    text = "".join(t.text or "" for t in is_el.iter(f"{{{NS['m']}}}t"))
                else:
                    text = (v.text or "") if v is not None else ""
                cells[col] = text
            out.append([cells.get(i, "") for i in range(max(cells) + 1)] if cells else [])
        return out


STYLE_SENTENCE = re.compile(
    r"\s*Rendered in ink-and-colour illustration style:.*?(?:edges of frame\.|$)",
    re.IGNORECASE | re.DOTALL)


def strip_style_block(text: str) -> tuple[str, bool]:
    """Remove the locked style block from prompt prose.

    Style is a **moodboard parameter**, never prompt text — the Krea compiler
    rejects a prompt containing it. The workbook conflated the two: every
    `Still (frame one)` cell ends with the style sentence. The canonical record
    holds clean prompt text and lets the parameter carry style.
    """
    cleaned = STYLE_SENTENCE.sub("", text or "").strip()
    return cleaned, cleaned != (text or "").strip()


def workbook_prompts(path: Path) -> dict[str, dict[str, str]]:
    """{display_number: {still, action}} straight from the sheet."""
    rows = xlsx_rows(path)
    if not rows:
        fail("workbook has no rows")
    headers = [h.strip() for h in rows[0]]
    idx = {h: i for i, h in enumerate(headers)}
    shot_col = idx.get("Shot")
    if shot_col is None:
        fail(f"no 'Shot' column. Found: {headers}")
    out: dict[str, dict[str, str]] = {}
    for row in rows[1:]:
        def cell(name: str) -> str:
            i = idx.get(name)
            return (row[i].strip() if i is not None and i < len(row) else "")
        display = cell("Shot")
        if not display:
            continue
        still, _ = strip_style_block(cell(FIELDS["still"]) or cell("Visual Description"))
        action = cell(FIELDS["action"]) or cell("Action Description")
        out[display] = {"still": still, "action": action}
    return out


# ── edit log ─────────────────────────────────────────────────────────────────

def edits_path(project: Path) -> Path:
    return project / "05-storyboard" / "shot-edits.jsonl"


def append_edit(project: Path, shot: dict, field: str, old: str, new: str,
                by: str, reason: str, source: str, revision: int | None = None) -> dict:
    """Log an edit. `revision` MUST be the value already written to the record —
    recomputing it here drifts the log out of step with the thing it describes."""
    ev = {
        "schema_version": 1, "event": "shot-edited", "event_id": str(uuid.uuid4()),
        "created_at": now(), "shot_id": shot.get("shot_id"),
        "shot": shot.get("display_number"), "field": field,
        "previous": old, "value": new,
        "revision": int(revision if revision is not None
                        else ((shot.get("prompt") or {}).get("revision") or 0)),
        "updated_by": by, "reason": reason, "source": source,
    }
    with edits_path(project).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_show(a) -> int:
    project = project_dir(a.project)
    _, shots = load_registry(project)
    targets = [find_shot(shots, a.shot)] if a.shot else shots
    for s in targets:
        p = s.get("prompt") or {}
        state = "canonical" if p.get("still") else "NOT MIGRATED (still empty)"
        print(f"\nshot {s.get('display_number')} — {s.get('title')}   [{state}]")
        print(f"  shot_id  {s.get('shot_id')}")
        if p:
            print(f"  rev {p.get('revision')}  by {p.get('updated_by')}  {p.get('updated_at')}")
            print(f"  still :  {(p.get('still') or '')[:150]}")
            print(f"  action:  {(p.get('action') or '')[:150]}")
        if not a.shot and len(targets) > 6:
            pass
    if not a.shot:
        migrated = sum(1 for s in shots if (s.get("prompt") or {}).get("still"))
        print(f"\n{migrated}/{len(shots)} shots have a canonical prompt")
    return 0


def cmd_migrate(a) -> int:
    project = project_dir(a.project)
    wb = Path(a.workbook)
    if not wb.is_absolute():
        wb = project / a.workbook
    if not wb.is_file():
        fail(f"workbook not found: {wb}")

    doc, shots = load_registry(project)
    src = workbook_prompts(wb)
    ts, changed, skipped, missing = now(), [], [], []

    for s in shots:
        display = str(s.get("display_number"))
        cells = src.get(display)
        if not cells or not cells["still"]:
            missing.append(display)
            continue
        existing = s.get("prompt") or {}
        if existing.get("still"):
            skipped.append(display)
            continue
        s["prompt"] = {
            "still": cells["still"], "action": cells["action"],
            "revision": 1, "updated_at": ts, "updated_by": "migration",
            "source": f"migrated verbatim from {wb.name}",
        }
        changed.append(display)

    print(f"migrate — {len(changed)} to write · {len(skipped)} already canonical · "
          f"{len(missing)} absent from the workbook")
    if missing:
        print(f"  absent: {', '.join(missing[:12])}{' …' if len(missing) > 12 else ''}")
    if a.dry_run:
        print("\n[dry-run] nothing written")
        return 0
    if not changed:
        print("nothing to do")
        return 0

    save_registry(project, doc)
    for s in shots:
        if str(s.get("display_number")) in changed:
            append_edit(project, s, "still", "", s["prompt"]["still"],
                        "migration", "workbook → canonical record", wb.name,
                        revision=s["prompt"]["revision"])
    print(f"\nwrote {len(changed)} prompts into shots.json")
    print(f"logged to {edits_path(project).name}")
    print("\nVerify:  shot_record.py verify --project "
          f"{a.project} --workbook {a.workbook}")
    return 0


def cmd_repair(a) -> int:
    """Strip the locked style block out of prompts already in the record."""
    project = project_dir(a.project)
    doc, shots = load_registry(project)
    fixed = []
    for s in shots:
        p = s.get("prompt") or {}
        cleaned, changed = strip_style_block(p.get("still") or "")
        if not changed:
            continue
        p["still"] = cleaned
        p["revision"] = int(p.get("revision") or 0) + 1
        p["updated_at"] = now()
        p["updated_by"] = "repair"
        p["source"] = "style block removed — style is a moodboard parameter, not prompt text"
        fixed.append((s, p["revision"]))
    print(f"repair — {len(fixed)} prompt(s) carry the style block")
    if a.dry_run or not fixed:
        if a.dry_run:
            print("\n[dry-run] nothing written")
        return 0
    save_registry(project, doc)
    for s, rev in fixed:
        append_edit(project, s, "still", "", s["prompt"]["still"], "repair",
                    "style block removed from prompt prose", "repair", revision=rev)
    print(f"cleaned {len(fixed)} prompts and logged each edit")
    return 0


def cmd_verify(a) -> int:
    """Cell-for-cell equality between the record and the workbook."""
    project = project_dir(a.project)
    wb = Path(a.workbook)
    if not wb.is_absolute():
        wb = project / a.workbook
    _, shots = load_registry(project)
    src = workbook_prompts(wb)

    same = diff = absent = 0
    for s in shots:
        display = str(s.get("display_number"))
        rec = (s.get("prompt") or {}).get("still") or ""
        cell = (src.get(display) or {}).get("still") or ""
        if not cell:
            absent += 1
            continue
        if rec.strip() == cell.strip():
            same += 1
        else:
            diff += 1
            print(f"\nshot {display} DIFFERS")
            print(f"  record   : {rec[:160]}")
            print(f"  workbook : {cell[:160]}")
    print(f"\n{same} identical · {diff} differ · {absent} absent from the workbook")
    if diff:
        print("\nA difference is not automatically wrong — the record is canonical now,")
        print("so a later edit SHOULD differ from the frozen workbook. Check the edit log.")
    return 1 if diff and a.strict else 0


def cmd_set(a) -> int:
    project = project_dir(a.project)
    doc, shots = load_registry(project)
    s = find_shot(shots, a.shot)
    if a.field not in FIELDS:
        fail(f"--field must be one of {list(FIELDS)}")
    prompt = s.setdefault("prompt", {"still": "", "action": "", "revision": 0})
    old = prompt.get(a.field) or ""
    if old.strip() == a.value.strip():
        print("value unchanged — nothing written")
        return 0
    prompt[a.field] = a.value
    prompt["revision"] = int(prompt.get("revision") or 0) + 1
    prompt["updated_at"] = now()
    prompt["updated_by"] = a.by
    prompt["source"] = a.reason or "manual edit"

    print(f"shot {s.get('display_number')} · {a.field} · rev {prompt['revision']}")
    print(f"  was: {old[:120]}")
    print(f"  now: {a.value[:120]}")
    if a.dry_run:
        print("\n[dry-run] nothing written")
        return 0
    save_registry(project, doc)
    append_edit(project, s, a.field, old, a.value, a.by, a.reason or "", "manual",
                revision=prompt["revision"])
    print("\nwritten. History:  shot_record.py history --project "
          f"{a.project} --shot {a.shot}")
    return 0


def cmd_history(a) -> int:
    project = project_dir(a.project)
    _, shots = load_registry(project)
    s = find_shot(shots, a.shot)
    p = edits_path(project)
    if not p.is_file():
        print("no edit history yet")
        return 0
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(ev.get("shot_id")) == str(s.get("shot_id")):
            rows.append(ev)
    print(f"shot {s.get('display_number')} — {len(rows)} edit(s)\n")
    for ev in rows:
        print(f"rev {ev.get('revision')} · {ev.get('field')} · {ev.get('updated_by')} "
              f"· {ev.get('created_at')}")
        if ev.get("reason"):
            print(f"  reason: {ev['reason']}")
        print(f"  → {(ev.get('value') or '')[:140]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Canonical shot record")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("show"); s.add_argument("--project", required=True)
    s.add_argument("--shot"); s.set_defaults(func=cmd_show)

    m = sub.add_parser("migrate"); m.add_argument("--project", required=True)
    m.add_argument("--workbook", required=True); m.add_argument("--dry-run", action="store_true")
    m.set_defaults(func=cmd_migrate)

    rp = sub.add_parser("repair", help="strip the style block from stored prompts")
    rp.add_argument("--project", required=True); rp.add_argument("--dry-run", action="store_true")
    rp.set_defaults(func=cmd_repair)

    v = sub.add_parser("verify"); v.add_argument("--project", required=True)
    v.add_argument("--workbook", required=True); v.add_argument("--strict", action="store_true")
    v.set_defaults(func=cmd_verify)

    e = sub.add_parser("set"); e.add_argument("--project", required=True)
    e.add_argument("--shot", required=True); e.add_argument("--field", required=True)
    e.add_argument("--value", required=True); e.add_argument("--by", default="vince", choices=AUTHORS)
    e.add_argument("--reason", default=""); e.add_argument("--dry-run", action="store_true")
    e.set_defaults(func=cmd_set)

    h = sub.add_parser("history"); h.add_argument("--project", required=True)
    h.add_argument("--shot", required=True); h.set_defaults(func=cmd_history)

    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
