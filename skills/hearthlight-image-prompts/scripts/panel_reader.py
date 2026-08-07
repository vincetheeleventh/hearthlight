#!/usr/bin/env python3
"""
Assemble the vision-pass packet: the hand-drawn panel plus everything needed to
read it correctly, and store the reading it produces.

The drawing is the densest statement of intent in the project and was invisible
to the prompt author. This makes it legible — as **tier 3 baseline evidence**,
never as a vote against the current Shot Vision. Contract:
`references/PANEL-READING.md`.

This script does not call a model. It prepares the packet, and records the
reading that comes back. The reading itself is an LLM job (D-020: prompt craft
belongs to a focused author; Python validates and appends nothing).

Commands
--------
    panel_reader.py packet  --project yugioh --shot 8 [--out FILE]
    panel_reader.py record  --project yugioh --shot 8 --reading FILE
    panel_reader.py status  --project yugioh

Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
STUDIO = HERE.parents[2]
CONTRACT = SKILL / "references" / "PANEL-READING.md"
PANEL_DIR = ("03-bible", "refs", "storyboard-panels")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}

# A vision model cannot read these directly; convert before sending.
NEEDS_CONVERSION = {".heic", ".heif"}


def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def load_shots(project: Path) -> list[dict]:
    p = project / "05-storyboard" / "shots.json"
    if not p.is_file():
        fail(f"no shot registry at {p}")
    doc = json.loads(p.read_text(encoding="utf-8"))
    return doc["shots"] if isinstance(doc, dict) and "shots" in doc else doc


def find_shot(shots: list[dict], ref: str) -> dict:
    for s in shots:
        if str(s.get("display_number")) == str(ref):
            return s
    for s in shots:
        if str(s.get("shot_id")) == str(ref):
            return s
    fail(f"no shot matching {ref!r}")


def resolve_panels(project: Path, shot: dict) -> tuple[list[dict], list[str]]:
    """Find this shot's drawing.

    Vince photographed the physical boards, chopped them up, and pasted each
    panel into the Storyboard column of the shot-list workbook. So the drawings
    live INSIDE the .xlsx, anchored to their shot's row — not as loose files.
    `extract` pulls them out to `shot-{nn}-board.png`; those are preferred here.
    The `board-panel-{nn}` convention is still honoured as a fallback.
    """
    root = project.joinpath(*PANEL_DIR)
    found, notes = [], []

    # 1. extracted-from-workbook, named by shot — the normal case
    display = str(shot.get("display_number") or "").strip()
    if display and root.is_dir():
        stem = f"shot-{int(display):02d}-board" if display.isdigit() else f"shot-{display}-board"
        for p in sorted(root.glob(f"{stem}.*")):
            if p.suffix.lower() in IMAGE_SUFFIXES:
                found.append({
                    "panel": display, "source": "workbook",
                    "path": str(p.relative_to(project)).replace("\\", "/"),
                    "needs_conversion": p.suffix.lower() in NEEDS_CONVERSION,
                    "bytes": p.stat().st_size,
                })
    if found:
        return found, notes

    # 2. fallback: loose board-panel-NN files
    numbers = [str(x).strip() for x in (shot.get("board_panels") or []) if str(x).strip()]
    if not numbers:
        notes.append(str(shot.get("storyboard_reference") or "") or "no board_panels recorded")
        return found, notes
    for n in numbers:
        stem = f"board-panel-{int(n):02d}" if n.isdigit() else f"board-panel-{n}"
        matches = [p for p in root.glob(f"{stem}.*") if p.suffix.lower() in IMAGE_SUFFIXES] \
            if root.is_dir() else []
        if not matches:
            notes.append(f"panel {n}: no file matching {stem}.* — the drawing is not on disk")
            continue
        for p in matches:
            found.append({
                "panel": n,
                "path": str(p.relative_to(project)).replace("\\", "/"),
                "needs_conversion": p.suffix.lower() in NEEDS_CONVERSION,
                "bytes": p.stat().st_size,
            })
    return found, notes


def latest_vision(project: Path, shot_id: str) -> dict:
    p = project / "04-images" / "shot-vision.jsonl"
    if not p.is_file():
        return {}
    best = {}
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(ev.get("shot_id")) != str(shot_id):
            continue
        if int(ev.get("revision") or 0) >= int(best.get("revision") or 0):
            best = ev
    return best


def neighbours(shots: list[dict], shot: dict) -> dict:
    """Adjacent shots — what makes 'adjacent-shot continuity' checkable rather than aspirational."""
    ordered = sorted(shots, key=lambda s: s.get("order") or s.get("display_number") or 0)
    idx = next((i for i, s in enumerate(ordered)
                if str(s.get("shot_id")) == str(shot.get("shot_id"))), None)
    if idx is None:
        return {}

    def brief(s: dict | None) -> dict | None:
        if not s:
            return None
        return {
            "shot": s.get("display_number"), "title": s.get("title"),
            "still": (s.get("prompt") or {}).get("still", "")[:600],
            "board_panels": s.get("board_panels"),
        }

    return {
        "previous": brief(ordered[idx - 1] if idx > 0 else None),
        "next": brief(ordered[idx + 1] if idx + 1 < len(ordered) else None),
    }


def readings_path(project: Path) -> Path:
    return project / "04-images" / "panel-readings.jsonl"



# ── extract the drawings out of the workbook ─────────────────────────────────

XDR = "{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}"
AMAIN = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def newest_workbook(project: Path) -> Path | None:
    books = sorted((project / "05-storyboard").glob("*shotlist*.xlsx"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return books[0] if books else None


def extract_panels(project: Path, workbook: Path, dry_run: bool = False) -> list[tuple[str, str]]:
    """Pull each anchored image out of the workbook and name it by its shot.

    Images are anchored to a row; that row's `Shot` cell names the shot. This is
    how a photographed board becomes a per-shot drawing the vision pass can read.
    """
    import xml.etree.ElementTree as ET
    import zipfile

    sys.path.insert(0, str(STUDIO / "skills" / "hearthlight-dashboard" / "scripts"))
    import shot_record as sr  # the workbook reader already in the repo

    rows = sr.xlsx_rows(workbook)
    if not rows:
        fail("workbook has no rows")
    headers = [h.strip() for h in rows[0]]
    if "Shot" not in headers:
        fail("workbook has no 'Shot' column")
    shot_col = headers.index("Shot")

    out_dir = project.joinpath(*PANEL_DIR)
    written: list[tuple[str, str]] = []
    with zipfile.ZipFile(workbook) as book:
        drawings = [n for n in book.namelist() if n.startswith("xl/drawings/drawing")
                    and n.endswith(".xml")]
        for drawing in drawings:
            rel_name = drawing.replace("drawings/", "drawings/_rels/") + ".rels"
            if rel_name not in book.namelist():
                continue
            rels = {r.get("Id"): r.get("Target")
                    for r in ET.fromstring(book.read(rel_name))}
            tree = ET.fromstring(book.read(drawing))
            for anchor in list(tree):
                frm = anchor.find(f"{XDR}from")
                blip = anchor.find(f".//{AMAIN}blip")
                if frm is None or blip is None:
                    continue
                excel_row = int(frm.find(f"{XDR}row").text) + 1
                target = rels.get(blip.get(f"{REL}embed"))
                if not target:
                    continue
                if excel_row - 1 >= len(rows):
                    continue
                row = rows[excel_row - 1]
                shot = (row[shot_col].strip()
                        if shot_col < len(row) else "")
                if not shot:
                    continue
                member = "xl/" + target.lstrip("./").replace("../", "")
                if member not in book.namelist():
                    continue
                suffix = Path(member).suffix or ".png"
                stem = f"shot-{int(shot):02d}-board" if shot.isdigit() else f"shot-{shot}-board"
                dest = out_dir / f"{stem}{suffix}"
                written.append((shot, str(dest.relative_to(project)).replace("\\", "/")))
                if dry_run:
                    continue
                out_dir.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(book.read(member))
    return written


def cmd_extract(a) -> int:
    project = STUDIO / "projects" / a.project
    if not project.is_dir():
        fail(f"no project at {project}")
    wb = Path(a.workbook) if a.workbook else newest_workbook(project)
    if wb and not wb.is_absolute():
        wb = project / a.workbook
    if not wb or not wb.is_file():
        fail("no shot-list workbook found")
    written = extract_panels(project, wb, dry_run=a.dry_run)
    print(f"{len(written)} drawing(s) anchored in {wb.name}")
    for shot, path in written:
        print(f"   shot {shot:>4}  ->  {path}")
    if a.dry_run:
        print("\n[dry-run] nothing written")
    else:
        print(f"\nwritten to {'/'.join(PANEL_DIR)}/")
        print("These are DERIVED from the workbook. Re-run after re-pasting panels.")
    return 0


def cmd_packet(a) -> int:
    project = STUDIO / "projects" / a.project
    if not project.is_dir():
        fail(f"no project at {project}")
    shots = load_shots(project)
    shot = find_shot(shots, a.shot)
    panels, notes = resolve_panels(project, shot)
    vision = latest_vision(project, str(shot.get("shot_id")))

    packet = {
        "schema_version": 1,
        "created_at": now(),
        "project": a.project,
        "shot": shot.get("display_number"),
        "shot_id": shot.get("shot_id"),
        "title": shot.get("title"),
        "contract": str(CONTRACT.relative_to(STUDIO)).replace("\\", "/"),
        "authority_reminder": (
            "The panel is TIER 3 baseline evidence. The latest Shot Vision governs. "
            "Report conflicts; never resolve them. Absence in the drawing is not an instruction."
        ),
        "panels": panels,
        "panel_notes": notes,
        "storyboard_reference": shot.get("storyboard_reference"),
        "shot_vision": {
            "text": vision.get("vision", ""),
            "revision": vision.get("revision"),
            "confirmed_by_user": vision.get("confirmed_by_user"),
        },
        "current_prompt": {
            "still": (shot.get("prompt") or {}).get("still", ""),
            "revision": (shot.get("prompt") or {}).get("revision"),
        },
        "storyboard_text": shot.get("text") or {},
        "adjacent": neighbours(shots, shot),
        "expected_output": "strict JSON per the contract — no prose outside it",
    }

    out = Path(a.out) if a.out else None
    text = json.dumps(packet, indent=2, ensure_ascii=False)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text)

    if not panels:
        print("\nNOTE: no panel image resolved — the author works from text alone.",
              file=sys.stderr)
        for n in notes:
            print(f"  · {n}", file=sys.stderr)
    else:
        conv = [p["path"] for p in panels if p["needs_conversion"]]
        if conv:
            print(f"\nNOTE: convert before sending to a vision model: {', '.join(conv)}",
                  file=sys.stderr)
    if vision and vision.get("confirmed_by_user") is False:
        print("\nNOTE: this Shot Vision has never been confirmed by Vince "
              "(confirmed_by_user: false).", file=sys.stderr)
    return 0


def cmd_record(a) -> int:
    project = STUDIO / "projects" / a.project
    shots = load_shots(project)
    shot = find_shot(shots, a.shot)
    reading = json.loads(Path(a.reading).read_text(encoding="utf-8"))

    required = {"framing", "confidence"}
    missing = sorted(required - set(reading))
    if missing:
        fail(f"reading is missing required keys: {', '.join(missing)}")
    conf = reading.get("confidence") or {}
    if isinstance(conf, dict) and conf and set(conf.values()) == {"high"}:
        print("WARNING: every observation is 'high' confidence. A rough board should not "
              "read that way — check the pass is being honest.", file=sys.stderr)

    event = {
        "schema_version": 1, "event": "panel-read", "event_id": str(uuid.uuid4()),
        "created_at": now(), "shot_id": shot.get("shot_id"),
        "shot": shot.get("display_number"), "reading": reading,
        "source": "panel_reader.py",
    }
    with readings_path(project).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    conflicts = reading.get("conflicts_with_vision") or []
    blockers = reading.get("blockers") or []
    print(f"recorded panel reading for shot {shot.get('display_number')}")
    if conflicts:
        print(f"\n{len(conflicts)} CONFLICT(S) WITH THE VISION — Vince's call:")
        for c in conflicts:
            print(f"  · panel: {c.get('panel_shows')}")
            print(f"    vision: {c.get('vision_states')}")
    if blockers:
        print(f"\n{len(blockers)} BLOCKER(S):")
        for b in blockers:
            print(f"  · {b}")
    return 0


def cmd_status(a) -> int:
    project = STUDIO / "projects" / a.project
    shots = load_shots(project)
    read_ids = set()
    p = readings_path(project)
    if p.is_file():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.strip():
                try:
                    read_ids.add(str(json.loads(line).get("shot_id")))
                except json.JSONDecodeError:
                    pass

    have = missing_file = no_panel = 0
    for s in shots:
        panels, _ = resolve_panels(project, s)
        mark = "read" if str(s.get("shot_id")) in read_ids else "    "
        if panels:
            have += 1
            state = f"{len(panels)} panel(s)"
        elif s.get("board_panels"):
            missing_file += 1
            state = "panels listed, FILE MISSING"
        else:
            no_panel += 1
            state = "no panel"
        print(f"  {mark}  shot {str(s.get('display_number')):>3}  {state}")
    print(f"\n{have} with a drawing on disk · {missing_file} listed but missing · "
          f"{no_panel} without a panel · {len(read_ids)} read")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Panel reading — the vision pass over the board")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("packet", help="build the vision-pass packet for a shot")
    p.add_argument("--project", required=True); p.add_argument("--shot", required=True)
    p.add_argument("--out"); p.set_defaults(func=cmd_packet)

    r = sub.add_parser("record", help="store a returned reading")
    r.add_argument("--project", required=True); r.add_argument("--shot", required=True)
    r.add_argument("--reading", required=True); r.set_defaults(func=cmd_record)

    e = sub.add_parser("extract", help="pull the drawings out of the shot-list workbook")
    e.add_argument("--project", required=True); e.add_argument("--workbook")
    e.add_argument("--dry-run", action="store_true"); e.set_defaults(func=cmd_extract)

    s = sub.add_parser("status", help="which shots have a drawing, and which are read")
    s.add_argument("--project", required=True); s.set_defaults(func=cmd_status)

    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
