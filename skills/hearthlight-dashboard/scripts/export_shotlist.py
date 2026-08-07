#!/usr/bin/env python3
"""
Export the canonical shot record to a spreadsheet you can open and read.

The record (`05-storyboard/shots.json`) is the source of truth. This writes a
**derived, read-only** view of it — the glanceable whole-film pass the workbook
used to give you, without the workbook being upstream of anything.

Edits made here go nowhere. Change a shot with:

    shot_record.py set --project yugioh --shot 2 --field still --value "..."

or in the Studio UI, which writes the same versioned event.

CSV rather than .xlsx on purpose: it is a derived artifact, so formatting is not
worth maintaining, and Excel, Numbers and Sheets all open it natively.

Usage
-----
    export_shotlist.py --project yugioh
    export_shotlist.py --project yugioh --out /some/where.csv
    export_shotlist.py --project yugioh --vision       # include Shot Vision

Stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3]

COLUMNS = [
    ("Shot", lambda s, v: s.get("display_number")),
    ("Title", lambda s, v: s.get("title")),
    ("Start", lambda s, v: s.get("start")),
    ("End", lambda s, v: s.get("end")),
    ("Duration (s)", lambda s, v: s.get("duration_seconds")),
    ("Still (frame one)", lambda s, v: (s.get("prompt") or {}).get("still")),
    ("Action (motion — video only)", lambda s, v: (s.get("prompt") or {}).get("action")),
    ("Dialogue", lambda s, v: (s.get("text") or {}).get("dialogue")),
    ("Audio", lambda s, v: (s.get("text") or {}).get("audio")),
    ("Camera Movement", lambda s, v: (s.get("text") or {}).get("camera_movement")),
    ("Notes", lambda s, v: (s.get("text") or {}).get("notes")),
    ("Board Panel", lambda s, v: ", ".join(str(x) for x in (s.get("board_panels") or []))),
    ("Prompt rev", lambda s, v: (s.get("prompt") or {}).get("revision")),
    ("Prompt updated by", lambda s, v: (s.get("prompt") or {}).get("updated_by")),
    ("Shot ID", lambda s, v: s.get("shot_id")),
]

VISION_COLUMN = ("Shot Vision", lambda s, v: v.get(str(s.get("shot_id")), ""))


def load_vision(project: Path) -> dict[str, str]:
    """Latest vision text per shot_id, resolved from the append-only log."""
    p = project / "04-images" / "shot-vision.jsonl"
    if not p.is_file():
        return {}
    best: dict[str, tuple[int, str]] = {}
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        sid = str(ev.get("shot_id") or "")
        rev = int(ev.get("revision") or 0)
        if sid and rev >= best.get(sid, (-1, ""))[0]:
            best[sid] = (rev, str(ev.get("vision") or ""))
    return {k: v[1] for k, v in best.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description="Export the shot record to CSV")
    ap.add_argument("--project", required=True)
    ap.add_argument("--out")
    ap.add_argument("--vision", action="store_true", help="include the Shot Vision column")
    a = ap.parse_args()

    project = STUDIO / "projects" / a.project
    reg = project / "05-storyboard" / "shots.json"
    if not reg.is_file():
        print(f"ERROR: no shot registry at {reg}", file=sys.stderr)
        return 1

    doc = json.loads(reg.read_text(encoding="utf-8"))
    shots = doc["shots"] if isinstance(doc, dict) and "shots" in doc else doc
    vision = load_vision(project) if a.vision else {}

    cols = list(COLUMNS)
    if a.vision:
        cols.insert(7, VISION_COLUMN)

    stamp = dt.date.today().isoformat()
    out = Path(a.out) if a.out else project / "05-storyboard" / f"shotlist-export-{stamp}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([c[0] for c in cols])
        for s in sorted(shots, key=lambda x: x.get("order") or x.get("display_number") or 0):
            w.writerow(["" if (val := fn(s, vision)) is None else val for _, fn in cols])

    missing = sum(1 for s in shots if not (s.get("prompt") or {}).get("still"))
    print(f"wrote {out}")
    print(f"  {len(shots)} shots · {len(cols)} columns"
          + (f" · ⚠ {missing} without a canonical prompt" if missing else ""))
    print("\nDERIVED VIEW — editing this file changes nothing.")
    print("Edit a shot:  shot_record.py set --project "
          f"{a.project} --shot N --field still --value \"...\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
