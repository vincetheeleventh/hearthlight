#!/usr/bin/env python3
"""Compile Krea Stage-A still prompts from the workbook's frame-one column only."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_shot(value: object) -> str:
    text = str(value or "").strip()
    return text[:-2] if text.endswith(".0") and text[:-2].isdigit() else text.upper()



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
        if normalize_shot(record.get("Shot")) == normalize_shot(shot_id):
            return source, headers, record, excel_row
    raise SystemExit(f"Shot not found in current workbook: {shot_id}")


def load_registry(root: Path, source: Path) -> tuple[dict, dict[str, dict], dict[str, dict]]:
    path = root / "05-storyboard" / "shots.json"
    if not path.exists():
        raise SystemExit("Stable shot registry missing: 05-storyboard/shots.json")
    registry = read_json(path)
    if registry.get("status") != "ready":
        raise SystemExit("Shot registry needs reconciliation; generation blocked")
    if registry.get("source_revision_hash") != sha256(source):
        raise SystemExit("Shot registry does not match current workbook; reconcile before generation")
    by_label: dict[str, dict] = {}
    by_id: dict[str, dict] = {}
    for shot in registry.get("shots", []):
        label = normalize_shot(shot.get("display_number"))
        shot_uuid = str(shot.get("shot_id") or "").strip()
        if not label or not shot_uuid or shot.get("id_state") != "stable":
            raise SystemExit("Shot registry contains missing or unstable identity; generation blocked")
        if label in by_label or shot_uuid in by_id:
            raise SystemExit("Shot registry contains duplicate identity; generation blocked")
        by_label[label] = shot
        by_id[shot_uuid] = shot
    return registry, by_label, by_id


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
    registry, by_label, by_id = load_registry(root, source)
    label = normalize_shot(record.get("Shot"))
    registered = by_label.get(label)
    if not registered:
        raise SystemExit(f"Workbook shot has no stable registry identity: {label}")
    if normalize_prompt(registered.get("title")) != normalize_prompt(record.get("Shot Title")):
        raise SystemExit(f"Workbook/registry title mismatch for Shot {label}; reconcile before generation")
    owner_id = registered.get("shared_setup_owner_shot_id")
    if owner_id:
        owner = by_id.get(owner_id)
        if not owner:
            raise SystemExit(f"Shared setup owner missing for Shot {label}")
        raise SystemExit(
            f"Shot {label} reuses Shot {normalize_shot(owner['display_number'])}; "
            "generate the owner only"
        )

    title = str(record.get("Shot Title") or "").strip()
    render_mode = str((registered.get("image_direction") or {}).get("render_mode") or "").strip()
    if render_mode == "source-photo":
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
        "shot": label,
        "shot_id": registered["shot_id"],
        "title": title,
        "workflow_stage": "style-composition",
        "model": MODEL,
        "aspect_ratio": aspect_ratio,
        "resolution": "1K",
        "generation_parameters": {
            "creativity": "raw",
            "intensity": 0,
            "complexity": 0,
            "movement": 0,
        },
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
            "workbook_sha256": registry["source_revision_hash"],
            "registry_revision_id": registry.get("registry_revision_id"),
        },
    }
    packet["prompt_sha256"] = text_sha256(prompt)
    packet["request_sha256"] = text_sha256(json.dumps({
        "model": packet["model"],
        "aspect_ratio": packet["aspect_ratio"],
        "resolution": packet["resolution"],
        "generation_parameters": packet["generation_parameters"],
        "prompt": packet["prompt"],
        "references": packet["references"],
    }, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    return packet


def packet_path(root: Path, packet: dict) -> Path:
    safe_id = re.sub(r"[^0-9A-Za-z_-]+", "-", packet["shot"]).strip("-")
    workbook_stem = Path(packet["source"]["workbook"]).stem
    version = workbook_stem.rsplit("-", 1)[-1]
    return root / "04-images" / "prompt-packets" / f"frame-one-{version}" / f"shot-{safe_id}-style-composition.json"


def compile_batch(root: Path) -> tuple[dict, list[tuple[Path, dict]]]:
    source, headers, rows = workbook_rows(root)
    registry, by_label, by_id = load_registry(root, source)
    packets: list[tuple[Path, dict]] = []
    aliases: list[dict] = []
    source_only: list[dict] = []
    shot_index = headers.index("Shot")
    workbook_labels = {
        normalize_shot(row[shot_index])
        for row in rows[1:]
        if shot_index < len(row) and normalize_shot(row[shot_index])
    }
    if workbook_labels != set(by_label):
        missing = sorted(set(by_label) - workbook_labels)
        unknown = sorted(workbook_labels - set(by_label))
        raise SystemExit(
            "Workbook/registry shot set mismatch; generation blocked "
            f"(missing={missing}, unknown={unknown})"
        )
    for registered in sorted(by_label.values(), key=lambda item: item.get("order", 0)):
        label = normalize_shot(registered["display_number"])
        image_direction = registered.get("image_direction") or {}
        if image_direction.get("render_mode") == "source-photo":
            source_only.append({
                "shot": label,
                "shot_id": registered["shot_id"],
                "source_asset": image_direction.get("source_asset"),
            })
            continue
        owner_id = registered.get("shared_setup_owner_shot_id")
        if owner_id:
            owner = by_id.get(owner_id)
            if not owner:
                raise SystemExit(f"Shared setup owner missing for Shot {label}")
            aliases.append({
                "shot": label,
                "shot_id": registered["shot_id"],
                "owner_shot": normalize_shot(owner["display_number"]),
                "owner_shot_id": owner_id,
            })
            continue
        packet = compile_packet(root, label)
        packets.append((packet_path(root, packet), packet))
    plan = {
        "schema_version": 1,
        "created_at": now(),
        "project": root.name,
        "workflow_stage": "style-composition",
        "source": {
            "workbook": base.relpath(source, root),
            "workbook_sha256": registry["source_revision_hash"],
            "registry_revision_id": registry.get("registry_revision_id"),
        },
        "model": MODEL,
        "aspect_ratio": packets[0][1]["aspect_ratio"] if packets else None,
        "resolution": "1K",
        "generation_parameters": packets[0][1]["generation_parameters"] if packets else None,
        "prompt_contract": {
            "sole_source_column": STILL_COLUMN,
            "excluded_column": ACTION_COLUMN,
            "exact_cell_equality_required": True,
        },
        "generation_count": len(packets),
        "packets": [
            {
                "shot": packet["shot"],
                "shot_id": packet["shot_id"],
                "title": packet["title"],
                "packet": base.relpath(packet_file, root),
                "prompt_sha256": packet["prompt_sha256"],
                "request_sha256": packet["request_sha256"],
                "source_cell": packet["source"]["prompt_cell"],
            }
            for packet_file, packet in packets
        ],
        "shared_setups": aliases,
        "source_only": source_only,
    }
    return plan, packets


def batch_plan_path(root: Path, plan: dict) -> Path:
    version = Path(plan["source"]["workbook"]).stem.rsplit("-", 1)[-1]
    return root / "04-images" / "prompt-packets" / f"frame-one-{version}" / "batch-plan.json"

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--shot")
    selection.add_argument("--all", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    root = base.project_dir(args.project)
    if args.all:
        plan, packets = compile_batch(root)
        if args.check_only:
            print(json.dumps(plan, indent=2, ensure_ascii=False))
            return 0
        for packet_file, packet in packets:
            write_json(packet_file, packet)
        out = batch_plan_path(root, plan)
        write_json(out, plan)
        print(json.dumps({
            "batch_plan": base.relpath(out, root),
            "generation_count": plan["generation_count"],
            "shared_setups": len(plan["shared_setups"]),
            "source_only": len(plan["source_only"]),
        }, ensure_ascii=False))
        return 0
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
