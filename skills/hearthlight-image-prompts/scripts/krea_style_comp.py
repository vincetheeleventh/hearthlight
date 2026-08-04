#!/usr/bin/env python3
"""Compile Krea Stage-A still prompts from the workbook's frame-one column only."""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE_SPEC = importlib.util.spec_from_file_location("image_pass", HERE / "image_pass.py")
base = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(base)

MODEL = "krea/krea-2/medium"
STILL_COLUMN = "Still (frame one)"
ACTION_COLUMN = "Action (motion — video only)"
FORBIDDEN_PROMPT_FRAGMENTS = (
    "STYLE AND COMPOSITION PASS",
    "Frozen action:",
    "Camera law:",
    "Continuity:",
    "Character construction:",
    "Hold silhouette/proportion:",
    "Moodboard and style settings are supplied",
)
TIMECODE = re.compile(r"\b\d+(?:\.\d+)?\s*[–-]\s*\d+(?:\.\d+)?s\s*:", re.IGNORECASE)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def newest_workbook(root: Path) -> Path:
    candidates = sorted(
        (root / "05-storyboard").glob("*shotlist*.xlsx"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise SystemExit("Shot-list workbook missing")
    return candidates[0]


def column_name(index: int) -> str:
    value = index + 1
    result = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(65 + remainder) + result
    return result


def normalize_prompt(value: object) -> str:
    return " ".join(str(value or "").split()).strip()


def workbook_rows(root: Path) -> tuple[Path, list[str], list[list[object]]]:
    source = newest_workbook(root)
    rows = base._xlsx_rows(source, "Shot List")
    if not rows:
        raise SystemExit("Shot List sheet empty")
    headers = [str(value or "").strip() for value in rows[0]]
    required = {"Shot", "Shot Title", STILL_COLUMN, ACTION_COLUMN}
    missing = sorted(required - set(headers))
    if missing:
        raise SystemExit(f"Current shot-list schema missing columns: {', '.join(missing)}")
    return source, headers, rows


def source_row(root: Path, shot_id: str) -> tuple[Path, list[str], dict, int]:
    source, headers, rows = workbook_rows(root)
    for excel_row, row in enumerate(rows[1:], start=2):
        record = {headers[index]: row[index] if index < len(row) else None for index in range(len(headers))}
        if str(record.get("Shot") or "").strip().upper() == shot_id.strip().upper():
            return source, headers, record, excel_row
    raise SystemExit(f"Shot not found in current workbook: {shot_id}")


def validate_prompt(prompt: str) -> None:
    if not prompt:
        raise SystemExit(f"{STILL_COLUMN} is blank")
    bad = [fragment for fragment in FORBIDDEN_PROMPT_FRAGMENTS if fragment.lower() in prompt.lower()]
    if TIMECODE.search(prompt):
        bad.append("motion timecode")
    if bad:
        raise SystemExit("Still prompt contains forbidden non-image material: " + ", ".join(bad))


def compile_packet(root: Path, shot_id: str) -> dict:
    source, headers, record, excel_row = source_row(root, shot_id)
    title = str(record.get("Shot Title") or "").strip()
    if title == "Twelve Years Later":
        raise SystemExit(f"Shot {shot_id} is source photography; Krea generation forbidden")
    prompt = normalize_prompt(record.get(STILL_COLUMN))
    validate_prompt(prompt)

    manifest = read_json(root / "03-bible" / "assets.json")
    moodboard = manifest.get("moodboard", {})
    if not moodboard.get("id"):
        raise SystemExit("Moodboard ID missing from 03-bible/assets.json")
    aspect_ratio = str(manifest.get("master_aspect_ratio") or "").strip()
    if not aspect_ratio:
        raise SystemExit("Master aspect ratio missing from 03-bible/assets.json")

    still_index = headers.index(STILL_COLUMN)
    action_index = headers.index(ACTION_COLUMN)
    packet = {
        "schema_version": 1,
        "created_at": now(),
        "project": root.name,
        "shot": str(record["Shot"]).strip(),
        "title": title,
        "workflow_stage": "style-composition",
        "model": MODEL,
        "aspect_ratio": aspect_ratio,
        "resolution": "1K",
        "prompt": prompt,
        "references": [
            {
                "type": "moodboard",
                "id": moodboard["id"],
                "strength": moodboard.get("strength", 0.35),
            }
        ],
        "source": {
            "workbook": base.relpath(source, root),
            "sheet": "Shot List",
            "prompt_column": STILL_COLUMN,
            "prompt_cell": f"{column_name(still_index)}{excel_row}",
            "excluded_action_column": ACTION_COLUMN,
            "excluded_action_cell": f"{column_name(action_index)}{excel_row}",
        },
    }
    return packet


def packet_path(root: Path, packet: dict) -> Path:
    safe_id = re.sub(r"[^0-9A-Za-z_-]+", "-", packet["shot"]).strip("-")
    workbook_stem = Path(packet["source"]["workbook"]).stem
    version = workbook_stem.rsplit("-", 1)[-1]
    return root / "04-images" / "prompt-packets" / f"frame-one-{version}" / f"shot-{safe_id}-style-composition.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--shot", required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    root = base.project_dir(args.project)
    packet = compile_packet(root, args.shot)
    if args.check_only:
        print(json.dumps(packet, indent=2, ensure_ascii=False))
        return 0
    out = packet_path(root, packet)
    write_json(out, packet)
    print(json.dumps({"packet": base.relpath(out, root), "shot": packet["shot"], "source_cell": packet["source"]["prompt_cell"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
