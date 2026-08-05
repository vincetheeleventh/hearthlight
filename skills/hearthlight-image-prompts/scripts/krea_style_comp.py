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


def compile_legacy_packet(root: Path, shot_id: str) -> dict:
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


def compile_legacy_batch(root: Path) -> tuple[dict, list[tuple[Path, dict]]]:
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
        packet = compile_legacy_packet(root, label)
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
                "source_cell": packet.get("source", {}).get("prompt_cell"),
            }
            for packet_file, packet in packets
        ],
        "shared_setups": aliases,
        "source_only": source_only,
    }
    return plan, packets


def legacy_batch_plan_path(root: Path, plan: dict) -> Path:
    version = Path(plan["source"]["workbook"]).stem.rsplit("-", 1)[-1]
    return root / "04-images" / "prompt-packets" / f"frame-one-{version}" / "batch-plan.json"


def vision_ledger(root: Path) -> Path:
    return root / "04-images" / "shot-vision.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    values = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid Shot Vision ledger line {line_number}: {exc}") from exc
        if isinstance(value, dict):
            values.append(value)
    return values


def approved_vision_packets(root: Path) -> dict[str, tuple[Path, dict]]:
    events = load_jsonl(vision_ledger(root))
    approvals = {
        str(event.get("batch_id") or ""): str(event.get("batch_sha256") or "")
        for event in events if event.get("event") == "prompt-batch-approved"
    }
    current_revision: dict[str, int] = {}
    for event in events:
        if event.get("event") in {"vision-migrated", "vision-updated", "vision-reverted", "vision-rant-applied"} and event.get("shot_id"):
            current_revision[str(event["shot_id"])] = int(event.get("revision") or 0)
    selected: dict[str, tuple[Path, dict]] = {}
    batch_files = sorted((root / "04-images" / "prompt-specs").glob("*/batch.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for batch_file in batch_files:
        batch = read_json(batch_file)
        batch_id = str(batch.get("batch_id") or "")
        if not batch_id or approvals.get(batch_id) != str(batch.get("batch_sha256") or ""):
            continue
        for entry in batch.get("shots", []):
            if not isinstance(entry, dict) or entry.get("blockers"):
                continue
            shot_id = str(entry.get("shot_id") or "")
            if not shot_id or shot_id in selected:
                continue
            if int(entry.get("vision_revision") or 0) != current_revision.get(shot_id, 0):
                continue
            packet_rel = str(entry.get("packet") or "")
            packet_file = (root / packet_rel).resolve()
            if root.resolve() not in packet_file.parents or not packet_file.is_file():
                raise SystemExit(f"Approved prompt packet missing or unsafe: {packet_rel}")
            packet = read_json(packet_file)
            if packet.get("prompt_sha256") != text_sha256(str(packet.get("prompt") or "")):
                raise SystemExit(f"Approved prompt packet hash mismatch: {packet_rel}")
            selected[shot_id] = (packet_file, packet)
    return selected


def compile_vision_packet(root: Path, shot_id: str) -> dict:
    source, _headers, record, _excel_row = source_row(root, shot_id)
    _registry, by_label, by_id = load_registry(root, source)
    label = normalize_shot(record.get("Shot"))
    registered = by_label.get(label)
    if not registered:
        raise SystemExit(f"Workbook shot has no stable registry identity: {label}")
    if (registered.get("image_direction") or {}).get("render_mode") == "source-photo":
        raise SystemExit(f"Shot {shot_id} is source photography; Krea generation forbidden")
    if registered.get("shared_setup_owner_shot_id"):
        owner = by_id.get(str(registered["shared_setup_owner_shot_id"]))
        raise SystemExit(f"Shot {label} reuses Shot {normalize_shot((owner or {}).get('display_number'))}; generate the owner only")
    selected = approved_vision_packets(root)
    found = selected.get(str(registered["shot_id"]))
    if not found:
        raise SystemExit(f"Shot {label} has no approved prompt for its current Shot Vision revision")
    packet = dict(found[1])
    packet["_packet_path"] = base.relpath(found[0], root)
    validate_prompt(str(packet.get("prompt") or ""))
    return packet


def compile_vision_batch(root: Path) -> tuple[dict, list[tuple[Path, dict]]]:
    source, headers, rows = workbook_rows(root)
    registry, by_label, by_id = load_registry(root, source)
    selected = approved_vision_packets(root)
    packets: list[tuple[Path, dict]] = []
    aliases: list[dict] = []
    source_only: list[dict] = []
    for registered in sorted(by_label.values(), key=lambda item: item.get("order", 0)):
        label = normalize_shot(registered["display_number"])
        direction = registered.get("image_direction") or {}
        if direction.get("render_mode") == "source-photo":
            source_only.append({"shot": label, "shot_id": registered["shot_id"], "source_asset": direction.get("source_asset")})
            continue
        owner_id = registered.get("shared_setup_owner_shot_id")
        if owner_id:
            owner = by_id.get(str(owner_id))
            if not owner:
                raise SystemExit(f"Shared setup owner missing for Shot {label}")
            aliases.append({"shot": label, "shot_id": registered["shot_id"], "owner_shot": normalize_shot(owner["display_number"]), "owner_shot_id": owner_id})
            continue
        found = selected.get(str(registered["shot_id"]))
        if not found:
            raise SystemExit(f"Shot {label} has no approved prompt for its current Shot Vision revision")
        validate_prompt(str(found[1].get("prompt") or ""))
        packets.append(found)
    manifest = read_json(root / "03-bible" / "assets.json")
    expected_aspect = str(manifest.get("master_aspect_ratio") or "").strip()
    if not expected_aspect or any(packet.get("aspect_ratio") != expected_aspect for _, packet in packets):
        raise SystemExit("Shot Vision batch conflicts with the Film Brief's master aspect ratio")
    plan = {
        "schema_version": 2, "created_at": now(), "project": root.name, "workflow_stage": "style-composition",
        "source": {"kind": "shot-vision", "vision_ledger_sha256": sha256(vision_ledger(root)), "workbook": base.relpath(source, root), "workbook_sha256": registry["source_revision_hash"], "registry_revision_id": registry.get("registry_revision_id")},
        "model": MODEL, "aspect_ratio": expected_aspect, "resolution": "1K",
        "generation_parameters": packets[0][1].get("generation_parameters") if packets else None,
        "prompt_contract": {"production_object": "visibility-aware-v1", "action_is_validation_context_only": True, "approved_prompt_required": True},
        "generation_count": len(packets),
        "packets": [{"shot": packet["shot"], "shot_id": packet["shot_id"], "title": packet["title"], "packet": base.relpath(path, root), "prompt_sha256": packet["prompt_sha256"], "request_sha256": packet["request_sha256"], "vision_revision": packet.get("vision_revision")} for path, packet in packets],
        "shared_setups": aliases, "source_only": source_only,
    }
    return plan, packets


def compile_packet(root: Path, shot_id: str) -> dict:
    return compile_vision_packet(root, shot_id) if vision_ledger(root).is_file() else compile_legacy_packet(root, shot_id)


def compile_batch(root: Path) -> tuple[dict, list[tuple[Path, dict]]]:
    return compile_vision_batch(root) if vision_ledger(root).is_file() else compile_legacy_batch(root)


def packet_path(root: Path, packet: dict) -> Path:
    if packet.get("_packet_path"):
        return root / str(packet["_packet_path"])
    safe_id = re.sub(r"[^0-9A-Za-z_-]+", "-", packet["shot"]).strip("-")
    workbook_stem = Path(packet["source"]["workbook"]).stem
    version = workbook_stem.rsplit("-", 1)[-1]
    return root / "04-images" / "prompt-packets" / f"frame-one-{version}" / f"shot-{safe_id}-style-composition.json"


def batch_plan_path(root: Path, plan: dict) -> Path:
    if (plan.get("source") or {}).get("kind") == "shot-vision":
        return root / "04-images" / "prompt-packets" / "approved-shot-vision" / "batch-plan.json"
    return legacy_batch_plan_path(root, plan)


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
        if (plan.get("source") or {}).get("kind") != "shot-vision":
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
    if not packet.get("_packet_path"):
        write_json(out, packet)
    print(json.dumps({"packet": base.relpath(out, root), "shot": packet["shot"], "source_cell": packet.get("source", {}).get("prompt_cell")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
