#!/usr/bin/env python3
"""Versioned Hearthlight image-pass tooling.

The Krea MCP remains the generation surface. This script owns the durable local
contract around it: shot specs, asset/cost preflight, immutable generation
history, confirmed review application, final selection, and contact sheets.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT = Path(__file__).resolve()
STUDIO = SCRIPT.parents[3]
STYLE_CLAUSE = (
    "Rendered in ink-and-colour illustration style: confident dark ink linework, "
    "soft flat colour washes, minimal detail, cozy warm palette, background "
    "dissolving to clean white at the edges of frame."
)
SCHEMA_VERSION = 1
GENERATED_SHOTS = tuple(range(1, 23))
ALL_SHOTS = tuple(range(1, 24))


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def project_dir(slug: str) -> Path:
    root = (STUDIO / "projects" / slug).resolve()
    if not root.is_dir():
        raise SystemExit(f"Project not found: {root}")
    return root


def relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise SystemExit(f"Path escapes project: {resolved}") from exc
    return resolved


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def append_event(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def load_events(root: Path) -> list[dict]:
    path = root / "04-images" / "generations.jsonl"
    if not path.exists():
        return []
    events = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid generations.jsonl line {number}: {exc}") from exc
    return events


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _xlsx_rows(path: Path, sheet_name: str) -> list[list]:
    """Read values from one xlsx worksheet using only the Python stdlib."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
          "p": "http://schemas.openxmlformats.org/package/2006/relationships"}
    with zipfile.ZipFile(path) as book:
        shared = []
        if "xl/sharedStrings.xml" in book.namelist():
            tree = ET.fromstring(book.read("xl/sharedStrings.xml"))
            for item in tree.findall("m:si", ns):
                shared.append("".join(node.text or "" for node in item.findall(".//m:t", ns)))

        workbook = ET.fromstring(book.read("xl/workbook.xml"))
        rel_id = None
        for sheet in workbook.findall("m:sheets/m:sheet", ns):
            if sheet.attrib.get("name") == sheet_name:
                rel_id = sheet.attrib[f"{{{ns['r']}}}id"]
                break
        if not rel_id:
            raise SystemExit(f"Worksheet not found: {sheet_name}")

        rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        target = None
        for rel in rels.findall("p:Relationship", ns):
            if rel.attrib.get("Id") == rel_id:
                target = rel.attrib["Target"]
                break
        if not target:
            raise SystemExit(f"Worksheet relationship missing: {sheet_name}")
        sheet_path = "xl/" + target.lstrip("/").replace("xl/", "", 1)
        sheet = ET.fromstring(book.read(sheet_path))

        values: dict[tuple[int, int], object] = {}
        max_row = max_col = 0
        for cell in sheet.findall(".//m:sheetData/m:row/m:c", ns):
            ref = cell.attrib["r"]
            match = re.match(r"([A-Z]+)(\d+)", ref)
            if not match:
                continue
            letters, row_text = match.groups()
            col = 0
            for char in letters:
                col = col * 26 + ord(char) - 64
            row = int(row_text)
            kind = cell.attrib.get("t")
            value_node = cell.find("m:v", ns)
            if kind == "inlineStr":
                value = "".join(node.text or "" for node in cell.findall(".//m:t", ns))
            elif value_node is None:
                value = None
            elif kind == "s":
                value = shared[int(value_node.text)]
            elif kind in {"str", "e"}:
                value = value_node.text
            else:
                raw = value_node.text or ""
                try:
                    number = float(raw)
                    value = int(number) if number.is_integer() else number
                except ValueError:
                    value = raw
            values[(row, col)] = value
            max_row, max_col = max(max_row, row), max(max_col, col)
        return [[values.get((row, col)) for col in range(1, max_col + 1)]
                for row in range(1, max_row + 1)]


def _spec_markdown(payload: dict) -> str:
    out = [
        "# Image-pass shot specifications — Warrior Returning Alive",
        "",
        "> Derived from the approved spreadsheet without modifying it. Image-pass amendments are",
        "> explicit below. Final selected images reconcile back into the storyboard before video.",
        "",
        f"Master: **{payload['master_aspect_ratio']}** · model: **{payload['default_model']}** · "
        f"unique generated setups: **{payload['unique_generated_setups']}**",
        "",
    ]
    for spec in payload["shots"]:
        out.extend([
            f"## Shot {spec['shot']:02d} — {spec['title']}",
            "",
            f"- Render: `{spec['render_mode']}` · generation owner: `{spec['generation_owner']:02d}`",
            f"- Visual: {spec['image_visual_description']}",
            f"- Action: {spec['image_action_description']}",
            f"- Camera: {spec['image_camera_movement']}",
            f"- Continuity: {spec['image_pass_note']}",
            "",
        ])
    return "\n".join(out)


def compile_specs(root: Path, source: Path) -> dict:
    rows = _xlsx_rows(source, "Shot List")
    headers = [str(value or "").strip() for value in rows[0]]
    shots = []
    for row in rows[1:]:
        record = {headers[index]: row[index] if index < len(row) else None
                  for index in range(len(headers))}
        if not record.get("Shot"):
            continue
        shot = int(record["Shot"])
        visual = str(record.get("Visual Description") or "").strip()
        action = str(record.get("Action Description") or "").strip()
        camera = str(record.get("Camera Movement") or "").strip()
        note = str(record.get("Notes") or "").strip()
        amendment = "No image-pass amendment; spreadsheet row remains authoritative."
        if shot == 1:
            visual = (
                "A 16:9 extreme close-up from directly overhead: only a small boy's active hands "
                "and forearms searching rapidly through overlapping Yu-Gi-Oh trading cards on a "
                "patterned rug. Warm morning sunlight sifts across the cards in broken bands, "
                "catching their faces as his hands push, flip, lift, inspect, and discard. " + STYLE_CLAUSE
            )
            action = (
                "0.0–3.0s: The boy's hands search with purpose, pushing cards aside, flipping "
                "several, lifting one to inspect, then dropping it back. Sunlight travels subtly "
                "across the moving cards. Camera: locked-off static overhead."
            )
            amendment = (
                "Hands stay active in frame one. End on a firm lace-pulling hand shape that can "
                "match cut to the father's hands in Shot 2."
            )
        elif shot == 2:
            visual = (
                "A 16:9 close insert at boot height. Only a lean father's hands tying one dark "
                "leather military boot, the boot and trouser cuff, and his wife's still lower legs "
                "beside him are visible. Their faces and upper bodies remain outside frame. After "
                "the knot is pulled tight, her hand lowers a pair of dog tags into the close-up and "
                "he takes them without looking up. Soft morning light from frame left. " + STYLE_CLAUSE
            )
            action = (
                "0.0–2.5s: His hands pull the bootlace tight and knot it. 2.5–4.5s: His wife's hand "
                "enters from above with the dog tags; he takes them without either body moving "
                "closer. Camera: locked close at boot height; never rise to reveal faces."
            )
            camera = "static close insert"
            amendment = (
                "Replaces the medium-wide/pedestal composition. Match cut from Shot 1's searching "
                "hands to the father's lace-pulling hands; retain the dog-tag handoff from the "
                "spreadsheet Action Description."
            )
        if shot == 17:
            amendment = (
                "Live Krea schema exposes only generic image-to-image for Krea 2 Medium, not a "
                "dedicated faithful content-reference control. Use openai/gpt-image-2 at 16:9 with "
                "the uploaded real card in image_urls; exact card art and title outrank model uniformity."
            )
        render_mode = "source-photo" if shot == 23 else "generated"
        owner = 1 if shot == 4 else shot
        if shot == 4:
            amendment = (
                "Reuse Shot 1's exact approved overhead drawing. Escalation belongs to animation "
                "and hand action, not a second conditioning still."
            )
        shots.append({
            "shot": shot,
            "title": record.get("Shot Title"),
            "board_panel": record.get("Board Panel"),
            "duration_seconds": record.get("Duration (s)"),
            "source_visual_description": record.get("Visual Description"),
            "source_action_description": record.get("Action Description"),
            "source_camera_movement": record.get("Camera Movement"),
            "source_notes": note,
            "image_visual_description": visual,
            "image_action_description": action,
            "image_camera_movement": camera,
            "image_pass_note": amendment,
            "render_mode": render_mode,
            "generation_owner": owner,
            "model_override": "openai/gpt-image-2" if shot == 17 else None,
            "required_reference_assets": ["prop-warrior-card"] if shot == 17 else [],
            "shared_with_shot": 1 if shot == 4 else None,
            "source_asset": "03-bible/refs/warrior_returning_alive_card.webp" if shot == 23 else None,
        })
    if [item["shot"] for item in shots] != list(ALL_SHOTS):
        raise SystemExit("Shot source must contain exactly shots 1–23 in order")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "project": root.name,
        "source": relpath(source, root),
        "compiled_at": utc_now(),
        "master_aspect_ratio": "16:9",
        "default_model": "krea/krea-2/medium",
        "unique_generated_setups": 21,
        "shots": shots,
    }
    out = root / "04-images"
    write_json(out / "shot-specs.json", payload)
    (out / "shot-specs.md").write_text(_spec_markdown(payload) + "\n", encoding="utf-8")
    return payload


def default_assets(root: Path) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "project": root.name,
        "master_aspect_ratio": "16:9",
        "default_model": "krea/krea-2/medium",
        "moodboard": {"id": None, "name": None, "strength": 0.35, "status": "missing"},
        "assets": [
            {"id": "character-father", "kind": "character-sheet", "local_path": "03-bible/characters/father/father-sheet.png", "krea_url": None, "status": "missing", "shots": [2, 3, 5, 6, 7, 8, 10, 11, 13, 14, 16, 18, 19, 20, 22]},
            {"id": "character-boy", "kind": "character-sheet", "local_path": "03-bible/characters/boy/boy-sheet.png", "krea_url": None, "status": "missing", "shots": [1, 4, 6, 7, 8, 9, 10, 11, 14, 15, 19, 20, 21]},
            {"id": "character-mother", "kind": "character-sheet", "local_path": "03-bible/characters/mother/mother-sheet.png", "krea_url": None, "status": "missing", "shots": [2, 5]},
            {"id": "setting-parents-bedroom", "kind": "setting-sheet", "local_path": "03-bible/refs/environments/parents-bedroom-sheet.png", "krea_url": None, "status": "missing", "shots": [2, 3, 5]},
            {"id": "setting-boy-bedroom", "kind": "setting-sheet", "local_path": "03-bible/refs/environments/boy-bedroom-sheet.png", "krea_url": None, "status": "missing", "shots": [1, 4, 6, 7, 8, 9, 10, 11, 21]},
            {"id": "setting-doorway-driveway", "kind": "setting-sheet", "local_path": "03-bible/refs/environments/doorway-driveway-taxi-sheet.png", "krea_url": None, "status": "missing", "shots": [12, 13, 14, 15, 16, 17, 18, 19, 20]},
            {"id": "prop-warrior-card", "kind": "prop-reference", "local_path": "03-bible/refs/warrior_returning_alive_card.webp", "krea_url": None, "status": "local-only", "shots": [1, 4, 6, 7, 8, 9, 15, 16, 17, 21, 22, 23]},
        ],
        "cost_approvals": {
            "calibration": {"estimated_cu": None, "estimated_minutes": None, "status": "pending", "approved_at": None, "note": None},
            "reference_batch": {"estimated_cu": None, "estimated_minutes": None, "status": "pending", "approved_at": None},
            "first_pass": {"estimated_cu": None, "estimated_minutes": None, "status": "pending", "approved_at": None},
        },
        "optional_warnings": [
            "Distribution platform and caption policy remain open; 16:9 master is authoritative.",
            "Mother remains absent from shots 14–20.",
            "Shot 23 final text line is still undrafted.",
        ],
    }


def default_import_queue(root: Path) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "project": root.name,
        "status": "awaiting-selection",
        "items": [],
        "note": "Add selected playground files or Krea URLs, record each generation, then mark complete.",
    }


def mark_imports_complete(root: Path) -> None:
    path = root / "04-images" / "imports" / "manifest.json"
    data = read_json(path)
    events = generation_events(load_events(root))
    imported_paths = {event["asset_path"] for event in events if event.get("source") == "playground-import"}
    unresolved = [item for item in data.get("items", []) if item.get("required", True) and item.get("asset_path") not in imported_paths]
    if unresolved:
        raise SystemExit("Cannot complete imports: selected playground items are not all recorded")
    data["status"] = "complete"
    data["completed_at"] = utc_now()
    write_json(path, data)


def init_project(root: Path, source: Path) -> None:
    for directory in [
        root / "04-images" / "imports",
        root / "04-images" / "review-proposals",
        root / "03-bible" / "characters" / "father",
        root / "03-bible" / "characters" / "boy",
        root / "03-bible" / "characters" / "mother",
        root / "03-bible" / "refs" / "environments",
    ]:
        directory.mkdir(parents=True, exist_ok=True)
    assets_path = root / "03-bible" / "assets.json"
    if not assets_path.exists():
        write_json(assets_path, default_assets(root))
    imports_manifest = root / "04-images" / "imports" / "manifest.json"
    if not imports_manifest.exists():
        write_json(imports_manifest, default_import_queue(root))
    history = root / "04-images" / "generations.jsonl"
    history.touch(exist_ok=True)
    compile_specs(root, source)
    rebuild_views(root)


def generation_events(events: list[dict]) -> list[dict]:
    return [event for event in events if event.get("event") == "generation"]


def latest_generation(events: list[dict], shot: int, specs: dict | None = None) -> dict | None:
    owner = shot
    if specs:
        owner = specs["shots"][shot - 1]["generation_owner"]
    candidates = [event for event in generation_events(events) if event["shot"] == owner]
    return max(candidates, key=lambda item: item["version"]) if candidates else None


def latest_review(events: list[dict], shot: int) -> dict | None:
    candidates = [event for event in events if event.get("event") == "review" and event["shot"] == shot]
    return candidates[-1] if candidates else None


def latest_selection(events: list[dict], shot: int) -> dict | None:
    candidates = [event for event in events if event.get("event") == "selection" and event["shot"] == shot]
    return candidates[-1] if candidates else None


def rebuild_views(root: Path) -> None:
    specs_path = root / "04-images" / "shot-specs.json"
    specs = read_json(specs_path) if specs_path.exists() else None
    events = load_events(root)
    prompt_lines = [
        "# Image generation history — Warrior Returning Alive",
        "",
        "> Human-readable view rebuilt from `generations.jsonl`. Do not edit history here.",
        "",
    ]
    for event in generation_events(events):
        prompt_lines.extend([
            f"## Shot {event['shot']:02d} · v{event['version']:02d}",
            "",
            f"- Source: `{event['source']}`",
            f"- Model: `{event.get('model') or 'unknown'}`",
            f"- File: `{event['asset_path']}`",
            f"- Krea job: `{event.get('krea_job_id') or 'unknown'}`",
            f"- References: `{json.dumps(event.get('references', []), ensure_ascii=False)}`",
            "",
            event.get("prompt") or "*[Prompt unavailable from imported generation]*",
            "",
        ])
    (root / "04-images" / "prompts.md").write_text("\n".join(prompt_lines) + "\n", encoding="utf-8")

    status_lines = [
        "# Image review status — Warrior Returning Alive",
        "",
        "> Derived from append-only `generations.jsonl`. Gate 3 still requires Vince's explicit ✅.",
        "",
    ]
    if specs:
        for shot in ALL_SHOTS:
            gen = latest_generation(events, shot, specs)
            review = latest_review(events, shot)
            selection = latest_selection(events, shot)
            state = review["status"] if review else ("generated-pending-review" if gen else "pending")
            version = selection["version"] if selection else (gen["version"] if gen else None)
            extra = f" v{version:02d}" if version else ""
            if selection:
                extra += " · final-selected"
            if shot == 4:
                extra += " · shares Shot 01 still"
            if shot == 23:
                extra += " · source photograph"
            status_lines.append(f"- shot-{shot:02d}: {state}{extra}")
    (root / "04-images" / "status.md").write_text("\n".join(status_lines) + "\n", encoding="utf-8")


def preflight(root: Path, phase: str) -> dict:
    blockers, warnings, ok = [], [], []
    assets_path = root / "03-bible" / "assets.json"
    specs_path = root / "04-images" / "shot-specs.json"
    for label, path in [
        ("distribution spec", root / "distribution-spec.md"),
        ("approved shot source", root / "05-storyboard" / "warrior_returning_alive_shotlist.xlsx"),
        ("compiled image shot specs", specs_path),
        ("asset manifest", assets_path),
    ]:
        (ok if path.exists() else blockers).append(f"{label}: {path.name}")
    if not assets_path.exists():
        return {"phase": phase, "ready": False, "blockers": blockers, "warnings": warnings, "ok": ok}
    manifest = read_json(assets_path)
    moodboard = manifest["moodboard"]
    if moodboard.get("id") and moodboard.get("status") in {"selected", "approved"}:
        ok.append(f"moodboard selected: {moodboard.get('name') or moodboard['id']}")
    else:
        blockers.append("moodboard missing: select one personal Krea moodboard ID")
    card = next(item for item in manifest["assets"] if item["id"] == "prop-warrior-card")
    card_path = root / card["local_path"]
    if card_path.exists() and card.get("krea_url"):
        ok.append("canonical card reference uploaded to Krea")
    else:
        blockers.append("canonical card reference must exist locally and have a Krea asset URL")
    cost_key = {"calibration": "calibration", "foundation": "reference_batch", "first-pass": "first_pass"}[phase]
    approval = manifest["cost_approvals"][cost_key]
    if approval.get("status") == "approved" and approval.get("approved_at"):
        ok.append(f"cost approved: {cost_key}")
    else:
        blockers.append(f"cost approval pending: {cost_key}")
    if phase == "first-pass":
        imports_path = root / "04-images" / "imports" / "manifest.json"
        if imports_path.exists() and read_json(imports_path).get("status") == "complete":
            ok.append("selected playground import step complete")
        else:
            blockers.append("selected playground outputs must be imported or explicitly marked complete")
        for asset in manifest["assets"]:
            if asset["id"] == "prop-warrior-card":
                continue
            path = root / asset["local_path"]
            if asset.get("status") == "approved" and path.exists() and asset.get("krea_url"):
                ok.append(f"asset approved: {asset['id']}")
            else:
                blockers.append(f"asset missing/unapproved: {asset['id']}")
    warnings.extend(manifest.get("optional_warnings", []))
    return {"phase": phase, "ready": not blockers, "blockers": blockers, "warnings": warnings, "ok": ok}


def set_moodboard(root: Path, moodboard_id: str, name: str | None, strength: float) -> None:
    path = root / "03-bible" / "assets.json"
    data = read_json(path)
    data["moodboard"] = {"id": moodboard_id, "name": name, "strength": strength, "status": "selected"}
    write_json(path, data)


def set_asset(root: Path, asset_id: str, local_path: str | None, krea_url: str | None, status: str) -> None:
    path = root / "03-bible" / "assets.json"
    data = read_json(path)
    asset = next((item for item in data["assets"] if item["id"] == asset_id), None)
    if not asset:
        raise SystemExit(f"Unknown asset id: {asset_id}")
    if local_path:
        candidate = inside(root / local_path, root)
        asset["local_path"] = relpath(candidate, root)
    if krea_url:
        asset["krea_url"] = krea_url
    asset["status"] = status
    write_json(path, data)


def approve_cost(root: Path, batch: str, cu: float | None, minutes: float | None, note: str | None) -> None:
    path = root / "03-bible" / "assets.json"
    data = read_json(path)
    data["cost_approvals"][batch] = {
        "estimated_cu": cu,
        "estimated_minutes": minutes,
        "status": "approved",
        "approved_at": utc_now(),
        "note": note,
    }
    write_json(path, data)


def _dimensions(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None


def record_generation(root: Path, args) -> dict:
    specs = read_json(root / "04-images" / "shot-specs.json")
    spec = specs["shots"][args.shot - 1]
    if spec["generation_owner"] != args.shot:
        raise SystemExit(f"Shot {args.shot:02d} shares Shot {spec['generation_owner']:02d}; record the owner only")
    source = Path(args.file).resolve()
    if not source.is_file():
        raise SystemExit(f"Generation file missing: {source}")
    events = load_events(root)
    if args.krea_job_id and any(event.get("krea_job_id") == args.krea_job_id for event in generation_events(events)):
        raise SystemExit(f"Krea job already recorded: {args.krea_job_id}")
    prior = [event for event in generation_events(events) if event["shot"] == args.shot]
    version = max((item["version"] for item in prior), default=0) + 1
    suffix = source.suffix.lower() or ".png"
    destination = root / "04-images" / f"shot-{args.shot:02d}-v{version:02d}{suffix}"
    if destination.exists():
        raise SystemExit(f"Refusing to overwrite: {destination}")
    shutil.copy2(source, destination)
    dimensions = _dimensions(destination)
    if dimensions and args.source != "playground-import" and spec["render_mode"] == "generated":
        ratio = dimensions[0] / dimensions[1]
        if abs(ratio - 4 / 3) > 0.03:
            destination.unlink()
            raise SystemExit(f"Expected 16:9 image, got {dimensions[0]}x{dimensions[1]}")
    prompt = None
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    references = read_json(Path(args.references_json)) if args.references_json else []
    event = {
        "schema_version": SCHEMA_VERSION,
        "event": "generation",
        "event_id": str(uuid.uuid4()),
        "created_at": args.created_at or utc_now(),
        "shot": args.shot,
        "version": version,
        "parent_version": args.parent_version,
        "source": args.source,
        "asset_path": relpath(destination, root),
        "sha256": sha256(destination),
        "dimensions": list(dimensions) if dimensions else None,
        "aspect_ratio": "16:9" if dimensions and abs(dimensions[0] / dimensions[1] - 16 / 9) <= 0.03 else "unknown",
        "prompt": prompt,
        "prompt_known": prompt is not None,
        "model": args.model,
        "krea_job_id": args.krea_job_id,
        "krea_url": args.krea_url,
        "references": references,
        "review_status": "pending-review",
        "selected_final": False,
    }
    append_event(root / "04-images" / "generations.jsonl", event)
    rebuild_views(root)
    return event


def create_review_proposal(root: Path, input_path: Path, allow_incomplete: bool) -> dict:
    incoming = read_json(input_path)
    flagged = incoming.get("flagged", [])
    ambiguous = incoming.get("ambiguous", [])
    seen = set()
    for item in flagged:
        shot = int(item["shot"])
        if shot not in ALL_SHOTS or shot in seen or not str(item.get("feedback", "")).strip():
            raise SystemExit("Each flagged shot must be unique, numbered 1–23, with verbatim feedback")
        seen.add(shot)
    specs = read_json(root / "04-images" / "shot-specs.json")
    events = load_events(root)
    available = [shot for shot in ALL_SHOTS if latest_generation(events, shot, specs) or shot == 23]
    if not allow_incomplete and available != list(ALL_SHOTS):
        missing = sorted(set(ALL_SHOTS) - set(available))
        raise SystemExit(f"Review batch incomplete; missing shots: {missing}")
    proposal_id = incoming.get("proposal_id") or f"review-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    proposal = {
        "schema_version": SCHEMA_VERSION,
        "proposal_id": proposal_id,
        "created_at": utc_now(),
        "source_rant": incoming.get("source_rant"),
        "flagged": [{"shot": int(item["shot"]), "feedback": str(item["feedback"]).strip()} for item in flagged],
        "unflagged_proposed_approved": [shot for shot in available if shot not in seen],
        "ambiguous": ambiguous,
        "confirmed": False,
    }
    out = root / "04-images" / "review-proposals"
    write_json(out / f"{proposal_id}.json", proposal)
    lines = [f"# Review proposal — {proposal_id}", "", "## Flagged"]
    lines.extend([f"- Shot {item['shot']:02d}: {item['feedback']}" for item in proposal["flagged"]] or ["- None"])
    lines.extend(["", "## Proposed approved (unflagged)", "", ", ".join(f"{shot:02d}" for shot in proposal["unflagged_proposed_approved"]) or "None", "", "## Ambiguous", ""])
    lines.extend([f"- {item}" for item in ambiguous] or ["- None"])
    (out / f"{proposal_id}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return proposal


def apply_review(root: Path, proposal_path: Path, confirmed: bool) -> None:
    if not confirmed:
        raise SystemExit("Review state changes require --confirmed after Vince approves the summary")
    proposal = read_json(proposal_path)
    if proposal.get("ambiguous"):
        raise SystemExit("Resolve ambiguous review items before applying")
    events = load_events(root)
    specs = read_json(root / "04-images" / "shot-specs.json")
    flagged = {item["shot"]: item["feedback"] for item in proposal["flagged"]}
    for shot in proposal["unflagged_proposed_approved"] + sorted(flagged):
        gen = latest_generation(events, shot, specs)
        version = gen["version"] if gen else None
        append_event(root / "04-images" / "generations.jsonl", {
            "schema_version": SCHEMA_VERSION,
            "event": "review",
            "event_id": str(uuid.uuid4()),
            "created_at": utc_now(),
            "proposal_id": proposal["proposal_id"],
            "shot": shot,
            "version": version,
            "status": "revision-requested" if shot in flagged else "approved",
            "feedback": flagged.get(shot),
        })
    proposal["confirmed"] = True
    proposal["confirmed_at"] = utc_now()
    write_json(proposal_path, proposal)
    rebuild_views(root)


def select_final(root: Path, shot: int, version: int) -> None:
    events = load_events(root)
    specs = read_json(root / "04-images" / "shot-specs.json")
    owner = specs["shots"][shot - 1]["generation_owner"]
    match = next((event for event in generation_events(events)
                  if event["shot"] == owner and event["version"] == version), None)
    if not match:
        raise SystemExit(f"Generation not found: shot {owner:02d} v{version:02d}")
    review = latest_review(events, shot)
    if not review or review["status"] != "approved":
        raise SystemExit(f"Shot {shot:02d} must be approved before final selection")
    append_event(root / "04-images" / "generations.jsonl", {
        "schema_version": SCHEMA_VERSION,
        "event": "selection",
        "event_id": str(uuid.uuid4()),
        "created_at": utc_now(),
        "shot": shot,
        "generation_owner": owner,
        "version": version,
        "asset_path": match["asset_path"],
        "selected_final": True,
    })
    rebuild_views(root)


def contact_sheet(root: Path, output: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SystemExit("Pillow is required to build the contact sheet") from exc
    specs = read_json(root / "04-images" / "shot-specs.json")
    events = load_events(root)
    tile_w, tile_h, label_h, cols = 360, 270, 48, 4
    rows = 6
    canvas = Image.new("RGB", (cols * tile_w, rows * (tile_h + label_h)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for index, spec in enumerate(specs["shots"]):
        shot = spec["shot"]
        gen = latest_generation(events, shot, specs)
        source = root / gen["asset_path"] if gen else None
        if shot == 23 and not source:
            source = root / spec["source_asset"]
        if not source or not source.exists():
            continue
        with Image.open(source) as image:
            image = image.convert("RGB")
            image.thumbnail((tile_w - 12, tile_h - 12))
            x = (index % cols) * tile_w + (tile_w - image.width) // 2
            y = (index // cols) * (tile_h + label_h) + (tile_h - image.height) // 2
            canvas.paste(image, (x, y))
        lx = (index % cols) * tile_w + 8
        ly = (index // cols) * (tile_h + label_h) + tile_h + 5
        draw.text((lx, ly), f"{shot:02d}  {spec['title']}", fill="black", font=font)
    output = inside(output, root)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, "PNG")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    sub = ap.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--source", default="05-storyboard/warrior_returning_alive_shotlist.xlsx")
    compile_cmd = sub.add_parser("compile-specs")
    compile_cmd.add_argument("--source", default="05-storyboard/warrior_returning_alive_shotlist.xlsx")
    pre = sub.add_parser("preflight")
    pre.add_argument("--phase", choices=["calibration", "foundation", "first-pass"], required=True)
    mood = sub.add_parser("set-moodboard")
    mood.add_argument("--id", required=True)
    mood.add_argument("--name")
    mood.add_argument("--strength", type=float, default=0.35)
    asset = sub.add_parser("set-asset")
    asset.add_argument("--id", required=True)
    asset.add_argument("--local-path")
    asset.add_argument("--krea-url")
    asset.add_argument("--status", choices=["missing", "local-only", "generated", "approved"], required=True)
    sub.add_parser("complete-imports")
    cost = sub.add_parser("approve-cost")
    cost.add_argument("--batch", choices=["calibration", "reference_batch", "first_pass"], required=True)
    cost.add_argument("--cu", type=float)
    cost.add_argument("--minutes", type=float)
    cost.add_argument("--note")
    record = sub.add_parser("record")
    record.add_argument("--shot", type=int, choices=ALL_SHOTS, required=True)
    record.add_argument("--file", required=True)
    record.add_argument("--source", choices=["hearthlight-krea", "playground-import", "source-photo"], required=True)
    record.add_argument("--prompt-file")
    record.add_argument("--model")
    record.add_argument("--krea-job-id")
    record.add_argument("--krea-url")
    record.add_argument("--references-json")
    record.add_argument("--created-at")
    record.add_argument("--parent-version", type=int)
    propose = sub.add_parser("propose-review")
    propose.add_argument("--input", required=True)
    propose.add_argument("--allow-incomplete", action="store_true")
    apply_cmd = sub.add_parser("apply-review")
    apply_cmd.add_argument("--proposal", required=True)
    apply_cmd.add_argument("--confirmed", action="store_true")
    select = sub.add_parser("select")
    select.add_argument("--shot", type=int, choices=ALL_SHOTS, required=True)
    select.add_argument("--version", type=int, required=True)
    sheet = sub.add_parser("contact-sheet")
    sheet.add_argument("--output", default="04-images/contact-sheet-review.png")
    sub.add_parser("rebuild")
    return ap


def main() -> int:
    args = parser().parse_args()
    root = project_dir(args.project)
    if args.command == "init":
        init_project(root, inside(root / args.source, root))
        print("INIT_OK")
    elif args.command == "compile-specs":
        payload = compile_specs(root, inside(root / args.source, root))
        print(f"COMPILED {len(payload['shots'])} shots; {payload['unique_generated_setups']} unique generations")
    elif args.command == "preflight":
        result = preflight(root, args.phase)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["ready"] else 2
    elif args.command == "set-moodboard":
        if not 0 <= args.strength <= 1:
            raise SystemExit("Moodboard strength must be between 0 and 1")
        set_moodboard(root, args.id, args.name, args.strength)
        print("MOODBOARD_SET")
    elif args.command == "set-asset":
        set_asset(root, args.id, args.local_path, args.krea_url, args.status)
        print("ASSET_SET")
    elif args.command == "complete-imports":
        mark_imports_complete(root)
        print("IMPORTS_COMPLETE")
    elif args.command == "approve-cost":
        approve_cost(root, args.batch, args.cu, args.minutes, args.note)
        print("COST_APPROVED")
    elif args.command == "record":
        event = record_generation(root, args)
        print(json.dumps({"shot": event["shot"], "version": event["version"], "asset": event["asset_path"]}))
    elif args.command == "propose-review":
        proposal = create_review_proposal(root, Path(args.input), args.allow_incomplete)
        print(json.dumps(proposal, indent=2, ensure_ascii=False))
    elif args.command == "apply-review":
        apply_review(root, inside(root / args.proposal, root), args.confirmed)
        print("REVIEW_APPLIED")
    elif args.command == "select":
        select_final(root, args.shot, args.version)
        print("FINAL_SELECTED")
    elif args.command == "contact-sheet":
        contact_sheet(root, root / args.output)
        print(args.output)
    elif args.command == "rebuild":
        rebuild_views(root)
        print("VIEWS_REBUILT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
