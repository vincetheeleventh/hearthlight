#!/usr/bin/env python3
"""
Set (or replace) the chosen conditioning image for a shot.

The Studio UI resolves a shot's hero asset automatically and has no control for
overriding it. This does that override, using the mechanism the UI already
honours: a `selection` event with `purpose: hero` in the append-only
`04-images/generations.jsonl`.

Nothing is overwritten and nothing is deleted. The source image is copied to a
properly-versioned filename, a `generation` event registers it, and a
`selection` event makes it the hero. Reverting is another selection event.

Usage
-----
    python set_shot_image.py --project yugioh --shot 2 \\
        --image 04-images/omni-62f9fe6e-....png

    python set_shot_image.py --project yugioh --shot 2 --image <path> --dry-run
    python set_shot_image.py --project yugioh --shot 2 --show

Paths may be absolute or relative to the project root.

Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
import uuid
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[3]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def load_shots(project: Path) -> list[dict]:
    p = project / "05-storyboard" / "shots.json"
    if not p.is_file():
        fail(f"no shot registry at {p}")
    d = json.loads(p.read_text(encoding="utf-8"))
    shots = d["shots"] if isinstance(d, dict) and "shots" in d else d
    if not isinstance(shots, list):
        fail("shots.json is not a shot list")
    return shots


def find_shot(shots: list[dict], ref: str) -> dict:
    """Resolve by display number, shot_id, or a legacy label."""
    for s in shots:                                    # display number
        if str(s.get("display_number")) == str(ref):
            return s
    for s in shots:                                    # stable id
        if str(s.get("shot_id")) == str(ref):
            return s
    for s in shots:                                    # legacy label
        if str(ref) in [str(x) for x in (s.get("legacy_numbers") or [])]:
            return s
    fail(f"no shot matching {ref!r}. Use a display number, a shot_id, or a legacy label.")


def read_events(jsonl: Path) -> list[dict]:
    if not jsonl.is_file():
        return []
    out = []
    for line in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def current_hero(events: list[dict], shot_id: str) -> tuple[str | None, str | None]:
    """(asset_path, selected_at) of the most recent explicit hero selection."""
    best_at, best_id = "", None
    for e in events:
        if e.get("event") == "selection" and e.get("purpose") == "hero" \
                and str(e.get("shot_id")) == shot_id:
            at = str(e.get("created_at") or "")
            if at >= best_at:
                best_at, best_id = at, str(e.get("asset_id") or "")
    if not best_id:
        return None, None
    for e in events:
        if str(e.get("asset_id")) == best_id and e.get("asset_path"):
            return str(e["asset_path"]), best_at
    return best_id, best_at


def next_version(project: Path, display: int, events: list[dict]) -> int:
    n = 0
    for p in (project / "04-images").glob(f"shot-{display:02d}-v*.png"):
        try:
            n = max(n, int(p.stem.rsplit("v", 1)[-1]))
        except ValueError:
            pass
    for e in events:
        path = str(e.get("asset_path") or "")
        if f"shot-{display:02d}-v" in path:
            try:
                n = max(n, int(Path(path).stem.rsplit("v", 1)[-1]))
            except ValueError:
                pass
    return n + 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Set a shot's chosen conditioning image")
    ap.add_argument("--project", required=True)
    ap.add_argument("--shot", required=True, help="display number, shot_id, or legacy label")
    ap.add_argument("--image", help="source image (absolute, or relative to project)")
    ap.add_argument("--note", default="", help="why this image was chosen")
    ap.add_argument("--stage", default="final", help="workflow stage label (default: final)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--show", action="store_true", help="print the current choice and exit")
    a = ap.parse_args()

    project = STUDIO / "projects" / a.project
    if not project.is_dir():
        fail(f"no project at {project}")

    shots = load_shots(project)
    shot = find_shot(shots, a.shot)
    shot_id = str(shot["shot_id"])
    display = int(shot["display_number"])
    jsonl = project / "04-images" / "generations.jsonl"
    events = read_events(jsonl)

    print(f"shot {display} — {shot.get('title')}")
    print(f"  shot_id  {shot_id}")
    cur_path, cur_at = current_hero(events, shot_id)
    print(f"  current  {cur_path or '(auto-resolved — no explicit choice)'}"
          + (f"  [{cur_at}]" if cur_at else ""))

    if a.show:
        return 0
    if not a.image:
        fail("--image is required unless --show")

    src = Path(a.image)
    if not src.is_absolute():
        src = project / a.image
    if not src.is_file():
        fail(f"image not found: {src}")
    if src.suffix.casefold() not in IMAGE_SUFFIXES:
        fail(f"not an image: {src.suffix}")

    # Approved assets are immutable — the choice becomes a NEW version.
    ver = next_version(project, display, events)
    dest_rel = f"04-images/shot-{display:02d}-v{ver:02d}.png"
    dest = project / dest_rel
    if dest.exists():
        fail(f"{dest_rel} already exists — refusing to overwrite (immutability rule)")

    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    asset_id = str(uuid.uuid4())
    ts = now_iso()

    gen = {
        "schema_version": 3, "event": "generation", "event_id": asset_id,
        "asset_id": asset_id, "created_at": ts,
        "shot": display, "shot_id": shot_id, "version": ver,
        "workflow_stage": a.stage, "source": "set_shot_image.py",
        "asset_path": dest_rel, "sha256": sha,
        "review_status": "approved",
        "note": a.note or f"chosen by hand from {src.name}",
        "origin_path": str(src),
    }
    sel = {
        "schema_version": 3, "event": "selection", "event_id": str(uuid.uuid4()),
        "created_at": ts, "shot": display, "shot_id": shot_id,
        "asset_id": asset_id, "version": ver,
        "workflow_stage": a.stage, "purpose": "hero",
        "note": a.note or "manual override",
    }

    print(f"  → copy   {src}")
    print(f"           {dest_rel}")
    print(f"  → asset  {asset_id}")
    print(f"  → events generation + selection(purpose=hero) appended to generations.jsonl")

    if a.dry_run:
        print("\n[dry-run] nothing written")
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    with jsonl.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(gen) + "\n")
        fh.write(json.dumps(sel) + "\n")

    print("\ndone. Refresh the Studio UI — the shot's hero is now this image.")
    print("To revert: run again with the previous image, or append another hero selection.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
