#!/usr/bin/env python3
"""Hearthlight two-pass still workflow: Krea composition, then GPT Image likeness."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_SPEC = importlib.util.spec_from_file_location("image_pass", HERE / "image_pass.py")
base = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(base)

ALL_SHOTS = tuple(range(1, 29))
STAGES = ("style-composition", "likeness")
SCHEMA_VERSION = 2
STYLE_MODEL = "krea/krea-2/medium"
LIKENESS_MODEL = "openai/gpt-image-2"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def append(root: Path, value: dict) -> None:
    base.append_event(root / "04-images" / "generations.jsonl", value)


def assets(root: Path) -> dict:
    return read(root / "03-bible" / "assets.json")


MASTER_RATIO_DEFAULT = "16:9"


def master_ratio(root: Path) -> str:
    return assets(root).get("master_aspect_ratio") or MASTER_RATIO_DEFAULT


def ratio_target(ratio_value: str) -> float:
    num, den = (float(part) for part in ratio_value.split(":"))
    return num / den


def shots(root: Path) -> dict:
    return read(root / "04-images" / "shot-specs.json")


def events(root: Path) -> list[dict]:
    return base.load_events(root)


def registry_shot(root: Path, shot: int) -> dict:
    path = root / "05-storyboard" / "shots.json"
    if not path.is_file():
        return {}
    payload = read(path)
    return next(
        (
            item
            for item in payload.get("shots", [])
            if str(item.get("display_number")) == str(shot)
            or str(shot) in {str(value) for value in item.get("legacy_numbers", [])}
        ),
        {},
    )


def contract_fields(root: Path, shot: int, asset_event: dict | None = None) -> dict:
    fields = {"shot_id": registry_shot(root, shot).get("shot_id")}
    if asset_event:
        fields["asset_id"] = asset_event.get("asset_id") or asset_event.get("event_id")
    return {key: value for key, value in fields.items() if value}


def asset_id(event: dict | None) -> str | None:
    if not event:
        return None
    return str(event.get("asset_id") or event.get("event_id") or "") or None


def generation_events(items: list[dict], stage: str | None = None) -> list[dict]:
    result = [item for item in items if item.get("event") == "generation"]
    if stage:
        result = [item for item in result if item.get("workflow_stage") == stage]
    return result


def owner(root: Path, shot: int) -> int:
    return int(shots(root)["shots"][shot - 1]["generation_owner"])


def latest_generation(root: Path, shot: int, stage: str) -> dict | None:
    own = owner(root, shot)
    found = [item for item in generation_events(events(root), stage) if item["shot"] == own]
    return max(found, key=lambda item: item["version"]) if found else None


def latest_review(root: Path, shot: int, stage: str) -> dict | None:
    found = [item for item in events(root) if item.get("event") == "review" and item.get("shot") == shot and item.get("review_stage") == stage]
    return found[-1] if found else None


def latest_selection(root: Path, shot: int, purpose: str) -> dict | None:
    found = [item for item in events(root) if item.get("event") == "selection" and item.get("shot") == shot and item.get("purpose") == purpose]
    return found[-1] if found else None


def character_assets(manifest: dict, shot: int) -> list[dict]:
    return [item for item in manifest["assets"] if item.get("kind") == "character-sheet" and shot in item.get("shots", [])]


def prop_assets(manifest: dict, shot: int) -> list[dict]:
    return [item for item in manifest["assets"] if item.get("kind") == "prop-reference" and shot in item.get("shots", [])]


def character_record(root: Path, asset: dict) -> dict:
    name = asset["id"].replace("character-", "")
    path = root / "03-bible" / "characters" / name / "character.json"
    if not path.exists():
        raise SystemExit(f"Character record missing: {path}")
    return read(path)


def is_canonical_card_shot(root: Path, shot: int) -> bool:
    return shots(root)["shots"][shot - 1]["title"] == "Warrior Returning Alive"


def likeness_required(root: Path, manifest: dict, shot: int) -> bool:
    return bool(character_assets(manifest, shot) or is_canonical_card_shot(root, shot))


def compile_live_specs(root: Path) -> dict:
    candidates = sorted((root / "05-storyboard").glob("*shotlist*.xlsx"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise SystemExit("Shot-list workbook missing")
    source = candidates[0]
    rows = base._xlsx_rows(source, "Shot List")
    headers = [str(value or "").strip() for value in rows[0]]
    compiled = []
    for row in rows[1:]:
        record = {headers[index]: row[index] if index < len(row) else None for index in range(len(headers))}
        if not record.get("Shot"):
            continue
        shot = int(record["Shot"])
        visual = str(record.get("Visual Description") or "").strip()
        action = str(record.get("Action Description") or "").strip()
        camera = str(record.get("Camera Movement") or "").strip()
        amendment = "No image-pass amendment; v3 spreadsheet row remains authoritative."
        if shot == 1:
            visual = (
                "A 16:9 extreme close-up from directly overhead: only a nine-year-old boy's active hands and forearms "
                "searching rapidly through overlapping Yu-Gi-Oh trading cards on a patterned rug. Warm morning sunlight "
                "sifts across the cards in broken bands as his hands push, flip, lift, inspect, and discard. " + base.STYLE_CLAUSE
            )
            amendment = "Hands stay active. End on a firm pulling hand shape for the match cut into Shot 2's bootlace pull."
        elif shot == 2:
            visual = (
                "A 16:9 close insert at boot height. Only the father's hands tying one high-laced tan desert boot, the boot "
                "and bloused desert-camouflage trouser cuff, and his wife's slippered lower legs are visible. Faces and upper "
                "bodies remain outside frame. After the knot is pulled tight, her hand lowers dog tags into the close-up and "
                "he takes them. Soft morning light from frame left. " + base.STYLE_CLAUSE
            )
            action = (
                "0.0–2.5s: His hands pull the bootlace tight and knot it. 2.5–4.5s: His wife's hand enters from above with "
                "the dog tags; he takes them. Camera: locked close at boot height; never rise to reveal faces."
            )
            camera = "static close insert"
            amendment = "Replaces v3 medium-wide/pedestal framing. Preserve dog-tag handoff. Match cut from Shot 1 hands."
        if shot == 4:
            amendment = "Reuse Shot 1's exact approved overhead composition. New action timing; no second conditioning still."
        title = str(record.get("Shot Title") or "").strip()
        is_source = title == "Twelve Years Later"
        owner_id = 1 if shot == 4 else shot
        compiled.append({
            "shot": shot, "title": title, "legacy_id": record.get("Legacy ID"),
            "board_panel": record.get("Board Panel"), "duration_seconds": record.get("Duration (s)"),
            "source_visual_description": record.get("Visual Description"), "source_action_description": record.get("Action Description"),
            "source_camera_movement": record.get("Camera Movement"), "source_notes": str(record.get("Notes") or "").strip(),
            "image_visual_description": visual, "image_action_description": action, "image_camera_movement": camera,
            "image_pass_note": amendment, "render_mode": "source-photo" if is_source else "generated",
            "generation_owner": owner_id, "shared_with_shot": 1 if shot == 4 else None,
            "source_asset": "03-bible/refs/props/prop-card-warrior-returning-alive-01.webp" if is_source else None,
        })
    expected = list(range(1, len(compiled) + 1))
    if [item["shot"] for item in compiled] != expected:
        raise SystemExit("Shot list must be consecutively numbered")
    payload = {
        "schema_version": SCHEMA_VERSION, "project": root.name, "source": base.relpath(source, root), "compiled_at": now(),
        "master_aspect_ratio": master_ratio(root), "default_model": STYLE_MODEL,
        "unique_generated_setups": len({item["generation_owner"] for item in compiled if item["render_mode"] == "generated"}),
        "shots": compiled,
    }
    write(root / "04-images" / "shot-specs.json", payload)
    lines = ["# Image-pass shot specifications — Warrior Returning Alive v3", "", f"> Source: `{payload['source']}` · {payload.get('master_aspect_ratio', MASTER_RATIO_DEFAULT)} · {len(compiled)} shots · {payload['unique_generated_setups']} unique illustrated setups", ""]
    for item in compiled:
        lines += [f"## Shot {item['shot']:02d} — {item['title']}", "", f"- Render: `{item['render_mode']}` · owner `{item['generation_owner']:02d}`", f"- Visual: {item['image_visual_description']}", f"- Action: {item['image_action_description']}", f"- Camera: {item['image_camera_movement']}", f"- Amendment: {item['image_pass_note']}", ""]
    (root / "04-images" / "shot-specs.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def configure(root: Path) -> dict:
    compile_live_specs(root)
    manifest_path = root / "03-bible" / "assets.json"
    manifest = read(manifest_path)
    manifest.setdefault("image_workflow", {})
    manifest["image_workflow"] = {
        "name": "style-composition-then-likeness",
        "style_composition": {
            "model": STYLE_MODEL,
            "aspect_ratio": master_ratio(root),
            "resolution": "1K",
            "moodboard_id": manifest["moodboard"].get("id"),
            "moodboard_strength": manifest["moodboard"].get("strength"),
            "priority": ["style", "composition", "body silhouette", "relative height", "pose", "action"],
            "character_sheet_images": "not attached",
        },
        "likeness": {
            "model": LIKENESS_MODEL,
            "aspect_ratio": master_ratio(root),
            "base": "approved style-composition image",
            "priority": ["character identity", "wardrobe", "canonical prop identity"],
            "preserve": ["composition", "camera", "crop", "pose", "action", "environment", "lighting", "palette", "style"],
        },
    }
    approvals = manifest.setdefault("cost_approvals", {})
    approvals.setdefault("style_composition", {"estimated_cu": None, "estimated_minutes": None, "status": "pending", "approved_at": None})
    approvals.setdefault("likeness", {"estimated_cu": None, "estimated_minutes": None, "status": "pending", "approved_at": None})

    known = {
        "character-father": ("03-bible/characters/father/father_char_sheet.png", "approved"),
        "character-boy": ("03-bible/characters/boy/boy_char_sheet.png", "generated"),
        "character-mother": ("03-bible/characters/mother/mother-sheet.png", "missing"),
    }
    for item in manifest["assets"]:
        if item["id"] in known:
            local, proposed = known[item["id"]]
            item["local_path"] = local
            item["status"] = proposed if (root / local).exists() else "missing"
            record = character_record(root, item)
            item["shots"] = [int(value) for value in record.get("shots", []) if isinstance(value, int) and value in ALL_SHOTS]
        elif item["id"] == "prop-warrior-card":
            item["shots"] = [21, 27, 28]
    write(manifest_path, manifest)

    spec = shots(root)
    packet = {
        "schema_version": SCHEMA_VERSION,
        "project": root.name,
        "created_at": now(),
        "master_aspect_ratio": master_ratio(root),
        "passes": manifest["image_workflow"],
        "shots": [],
    }
    for item in spec["shots"]:
        shot = int(item["shot"])
        chars = [entry["id"] for entry in character_assets(manifest, shot)]
        props = [entry["id"] for entry in prop_assets(manifest, shot)]
        packet["shots"].append({
            "shot": shot,
            "title": item["title"],
            "generation_owner": item["generation_owner"],
            "render_mode": item["render_mode"],
            "style_composition_model": None if item["render_mode"] == "source-photo" else STYLE_MODEL,
            "likeness_required": likeness_required(root, manifest, shot) and item["render_mode"] != "source-photo",
            "likeness_model": LIKENESS_MODEL if likeness_required(root, manifest, shot) and item["render_mode"] != "source-photo" else None,
            "character_assets": chars,
            "prop_assets": props,
            "final_source": "likeness" if likeness_required(root, manifest, shot) and item["render_mode"] != "source-photo" else ("source-photo" if item["render_mode"] == "source-photo" else "style-composition"),
        })
    write(root / "04-images" / "image-workflow.json", packet)
    rebuild_status(root)
    return packet


def approval_ready(manifest: dict, key: str) -> bool:
    value = manifest.get("cost_approvals", {}).get(key, {})
    return value.get("status") == "approved" and bool(value.get("approved_at"))


def preflight(root: Path, stage: str) -> dict:
    manifest = assets(root)
    blockers, warnings, ok = [], [], []
    required = [
        root / "project.json",
        root / "03-bible" / "mise-en-scene.md",
        root / "03-bible" / "assets.json",
        root / "04-images" / "shot-specs.json",
        root / "04-images" / "image-workflow.json",
    ]
    spec_source = shots(root).get("source")
    if spec_source:
        required.append(root / spec_source)
    for path in required:
        (ok if path.exists() else blockers).append(str(path.relative_to(root)))
    try:
        identity = json.loads((root / "project.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        identity = {}
    if not identity.get("client"):
        blockers.append("project client declaration open")
    if not identity.get("charged_register"):
        blockers.append("charged register declaration open")
    if not identity.get("master_aspect_ratio"):
        blockers.append("master aspect ratio declaration open")
    if not manifest.get("moodboard", {}).get("id"):
        blockers.append("moodboard ID missing")
    else:
        ok.append(f"moodboard: {manifest['moodboard'].get('name')} @ {manifest['moodboard'].get('strength')}")
    if not approval_ready(manifest, "style_composition" if stage == "style-composition" else "likeness"):
        blockers.append(f"cost approval pending: {'style_composition' if stage == 'style-composition' else 'likeness'}")

    if stage == "style-composition":
        for item in manifest["assets"]:
            if item.get("kind") == "character-sheet":
                try:
                    character_record(root, item)
                    ok.append(f"character description available: {item['id']}")
                except SystemExit as exc:
                    blockers.append(str(exc))
            if item.get("kind") == "setting-sheet" and item.get("status") != "approved":
                warnings.append(f"setting sheet absent; prompt-only environment: {item['id']}")
    else:
        workflow = read(root / "04-images" / "image-workflow.json")
        needed_ids = sorted({asset_id for item in workflow["shots"] if item["likeness_required"] for asset_id in item["character_assets"]})
        by_id = {item["id"]: item for item in manifest["assets"]}
        for asset_id in needed_ids:
            item = by_id[asset_id]
            local = root / item["local_path"]
            if item.get("status") == "approved" and local.exists():
                ok.append(f"approved local sheet: {asset_id}")
            else:
                blockers.append(f"likeness sheet missing or unapproved: {asset_id}")
        for item in workflow["shots"]:
            if item["render_mode"] == "source-photo" or item["generation_owner"] != item["shot"] or not item["likeness_required"]:
                continue
            gen = latest_generation(root, item["shot"], "style-composition")
            review = latest_review(root, item["shot"], "style-composition")
            selected = latest_selection(root, item["shot"], "composition-base")
            if not gen or not review or review.get("status") != "composition-approved" or not selected:
                blockers.append(f"composition base not approved/selected: shot-{item['shot']:02d}")
    warnings.extend(manifest.get("optional_warnings", []))
    return {"stage": stage, "ready": not blockers, "blockers": blockers, "warnings": warnings, "ok": ok}


def set_estimate(root: Path, stage: str, cu: float, minutes: float) -> dict:
    manifest = assets(root)
    key = "style_composition" if stage == "style-composition" else "likeness"
    entry = manifest.setdefault("cost_approvals", {}).setdefault(key, {})
    entry.update({"estimated_cu": cu, "estimated_minutes": minutes, "status": "pending", "approved_at": None})
    write(root / "03-bible" / "assets.json", manifest)
    return entry


def approve_cost(root: Path, stage: str, confirmed: bool) -> dict:
    if not confirmed:
        raise SystemExit("Cost approval requires --confirmed after Vince approves the shown estimate")
    manifest = assets(root)
    key = "style_composition" if stage == "style-composition" else "likeness"
    entry = manifest.setdefault("cost_approvals", {}).setdefault(key, {})
    if entry.get("estimated_cu") is None or entry.get("estimated_minutes") is None:
        raise SystemExit("Record live CU and time estimates before approval")
    entry.update({"status": "approved", "approved_at": now()})
    write(root / "03-bible" / "assets.json", manifest)
    return entry

def compact_must_hold(record: dict) -> str:
    values = record.get("must_hold", [])
    return "; ".join(values[:5])


def style_prompt(root: Path, shot: int) -> tuple[str, list[dict]]:
    manifest = assets(root)
    spec = shots(root)["shots"][shot - 1]
    chars = character_assets(manifest, shot)
    signatures = []
    for item in chars:
        rec = character_record(root, item)
        signatures.append(f"{rec['display_name']}: {rec['signature_string']}. Hold silhouette/proportion: {compact_must_hold(rec)}")
    scale = ""
    ids = {item["id"] for item in chars}
    if "character-father" in ids and "character-boy" in ids:
        scale = "Adult-child scale must read immediately: the nine-year-old is substantially shorter and smaller than his father; never equalize their height or mass."
    prompt = "\n\n".join(part for part in [
        "STYLE AND COMPOSITION PASS. Prioritize the approved ink-and-colour aesthetic, camera placement, frame geometry, pose, action, body silhouette, and relative height. Character facial likeness is provisional in this pass.",
        spec["image_visual_description"],
        f"Frozen action: {spec['image_action_description']}",
        f"Camera law: {spec['image_camera_movement']}. Continuity: {spec['image_pass_note']}",
        "Character construction: " + " ".join(signatures) if signatures else "No likeness-critical character in frame.",
        scale,
        f"Maintain {master_ratio(root)} composition. No extra people. No incidental text or labels. Preserve only explicitly required SONICS lettering and canonical card text. Moodboard and style settings are supplied as generation parameters, not reinterpreted here.",
    ] if part)
    references = [{"type": "moodboard", "id": manifest["moodboard"]["id"], "strength": manifest["moodboard"]["strength"]}]
    return prompt, references


def likeness_prompt(root: Path, shot: int, base_selection: dict) -> tuple[str, list[dict]]:
    manifest = assets(root)
    spec = shots(root)["shots"][shot - 1]
    chars = character_assets(manifest, shot)
    references = [{"type": "composition-base", "shot": shot, "version": base_selection["version"], "local_path": base_selection["asset_path"], "url": base_selection.get("krea_url")}]
    replacements = []
    for item in chars:
        rec = character_record(root, item)
        replacements.append(f"Replace the depicted {rec['display_name']} with the exact character from the attached {item['id']} sheet. Identity law: {rec['signature_string']}. Must hold: {compact_must_hold(rec)}")
        references.append({"type": "character-sheet", "id": item["id"], "local_path": item["local_path"], "url": item.get("krea_url")})
    if is_canonical_card_shot(root, shot):
        card = next(item for item in manifest["assets"] if item["id"] == "prop-warrior-card")
        replacements.append("Replace the generic card face with the exact attached Warrior Returning Alive card. Preserve its real artwork, border, title, wear, and orientation faithfully.")
        references.append({"type": "canonical-prop", "id": card["id"], "local_path": card["local_path"], "url": card.get("krea_url")})
    prompt = "\n\n".join([
        "LIKENESS REPLACEMENT PASS. Edit the attached approved composition base; do not create a new composition.",
        f"Preserve exactly: {master_ratio(root)} canvas, camera position, crop, perspective, figure placement, body scale, poses, hand positions, action, environment geometry, prop placement, lighting direction, value pattern, palette, line quality, colour washes, white-space boundaries, and overall Krea-derived style.",
        " ".join(replacements),
        f"Shot content remains: {spec['image_visual_description']}",
        "Change only character identity, required wardrobe details, and any explicitly referenced canonical prop. Do not add or remove people. Do not beautify, age-shift, restage, relight, recrop, or redesign the image. No new text or labels.",
    ])
    return prompt, references


def compile_prompts(root: Path, stage: str, selected_shot: int | None) -> list[str]:
    if stage == "style-composition":
        raise SystemExit(
            "Legacy Stage-A compiler disabled: it mixed motion/action columns into still prompts. "
            "Use scripts/krea_style_comp.py, which reads Still (frame one) only."
        )
    workflow = read(root / "04-images" / "image-workflow.json")
    made = []
    for item in workflow["shots"]:
        shot = item["shot"]
        if selected_shot and shot != selected_shot:
            continue
        if item["render_mode"] == "source-photo" or item["generation_owner"] != shot:
            continue
        if stage == "likeness" and not item["likeness_required"]:
            continue
        if stage == "style-composition":
            prompt, refs = style_prompt(root, shot)
            model = STYLE_MODEL
            parent = None
        else:
            selected = latest_selection(root, shot, "composition-base")
            if not selected:
                raise SystemExit(f"Composition base not selected: shot-{shot:02d}")
            prompt, refs = likeness_prompt(root, shot, selected)
            model = LIKENESS_MODEL
            parent = selected["version"]
        out = root / "04-images" / "prompt-packets" / f"shot-{shot:02d}-{stage}.json"
        write(out, {"schema_version": SCHEMA_VERSION, "created_at": now(), "shot": shot, "workflow_stage": stage, "model": model, "aspect_ratio": master_ratio(root), "resolution": "1K", "parent_version": parent, "prompt": prompt, "references": refs})
        made.append(str(out.relative_to(root)))
    return made


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def record(root: Path, args) -> dict:
    own = owner(root, args.shot)
    if own != args.shot:
        raise SystemExit(f"Shot {args.shot:02d} shares Shot {own:02d}; record owner only")
    source = Path(args.file).resolve()
    if not source.is_file():
        raise SystemExit(f"File missing: {source}")
    packet = read(Path(args.packet))
    if packet["shot"] != args.shot or packet["workflow_stage"] != args.stage:
        raise SystemExit("Prompt packet does not match shot/stage")
    current = events(root)
    if args.krea_job_id and any(item.get("krea_job_id") == args.krea_job_id for item in generation_events(current)):
        raise SystemExit(f"Krea job already recorded: {args.krea_job_id}")
    all_for_shot = [item for item in generation_events(current) if item["shot"] == args.shot]
    version = max((item["version"] for item in all_for_shot), default=0) + 1
    if args.stage == "likeness":
        selected = latest_selection(root, args.shot, "composition-base")
        if not selected or packet.get("parent_version") != selected["version"]:
            raise SystemExit("Likeness generation must descend from selected composition base")
    suffix = source.suffix.lower() or ".png"
    target = root / "04-images" / f"shot-{args.shot:02d}-v{version:02d}{suffix}"
    if target.exists():
        raise SystemExit(f"Refusing overwrite: {target}")
    shutil.copy2(source, target)
    dimensions = base._dimensions(target)
    if dimensions and abs(dimensions[0] / dimensions[1] - ratio_target(master_ratio(root))) > 0.03:
        target.unlink()
        raise SystemExit(f"Expected {master_ratio(root)}, got {dimensions[0]}x{dimensions[1]}")
    event_id = str(uuid.uuid4())
    parent = None
    if packet.get("parent_version") is not None:
        parent = next(
            (item for item in generation_events(current) if item.get("shot") == args.shot and item.get("version") == packet.get("parent_version")),
            None,
        )
    event = {
        "schema_version": SCHEMA_VERSION, "event": "generation", "event_id": event_id, "asset_id": event_id, "created_at": now(),
        **contract_fields(root, args.shot),
        "shot": args.shot, "version": version, "parent_version": packet.get("parent_version"), "workflow_stage": args.stage,
        "parent_asset_id": asset_id(parent),
        "source": "hearthlight-krea", "asset_path": base.relpath(target, root), "sha256": digest(target),
        "dimensions": list(dimensions) if dimensions else None, "aspect_ratio": master_ratio(root), "prompt": packet["prompt"],
        "prompt_known": True, "model": packet["model"], "krea_job_id": args.krea_job_id, "krea_url": args.krea_url,
        "references": packet["references"], "review_status": "pending-review", "selected_final": False,
    }
    append(root, event)
    rebuild_status(root)
    return event


def propose_review(root: Path, stage: str, input_path: Path, allow_incomplete: bool) -> dict:
    incoming = read(input_path)
    flagged, ambiguous = incoming.get("flagged", []), incoming.get("ambiguous", [])
    seen = set()
    for item in flagged:
        shot = int(item["shot"])
        if shot not in ALL_SHOTS or shot in seen or not str(item.get("feedback", "")).strip():
            raise SystemExit("Flagged shots require unique shot number and verbatim feedback")
        seen.add(shot)
    workflow = read(root / "04-images" / "image-workflow.json")
    available = []
    for item in workflow["shots"]:
        shot = item["shot"]
        if item["render_mode"] == "source-photo":
            continue
        if stage == "likeness" and not item["likeness_required"]:
            continue
        if latest_generation(root, shot, stage):
            available.append(shot)
    expected = [item["shot"] for item in workflow["shots"] if item["render_mode"] != "source-photo" and (stage == "style-composition" or item["likeness_required"])]
    if not allow_incomplete and sorted(set(available)) != sorted(set(expected)):
        raise SystemExit(f"Review batch incomplete; missing: {sorted(set(expected)-set(available))}")
    proposal_id = incoming.get("proposal_id") or f"{stage}-review-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    proposal = {"schema_version": SCHEMA_VERSION, "proposal_id": proposal_id, "created_at": now(), "review_stage": stage, "source_rant": incoming.get("source_rant"), "flagged": [{"shot": int(item["shot"]), "feedback": str(item["feedback"]).strip()} for item in flagged], "unflagged_proposed_approved": [shot for shot in sorted(set(available)) if shot not in seen], "ambiguous": ambiguous, "confirmed": False}
    out = root / "04-images" / "review-proposals" / f"{proposal_id}.json"
    write(out, proposal)
    return proposal


def apply_review(root: Path, proposal_path: Path, confirmed: bool) -> None:
    if not confirmed:
        raise SystemExit("Review changes require --confirmed")
    proposal = read(proposal_path)
    if proposal.get("ambiguous"):
        raise SystemExit("Resolve ambiguous review items first")
    stage = proposal["review_stage"]
    flagged = {int(item["shot"]): item["feedback"] for item in proposal["flagged"]}
    for shot in proposal["unflagged_proposed_approved"] + sorted(flagged):
        gen = latest_generation(root, shot, stage)
        if not gen:
            continue
        approved = shot not in flagged
        status = ("composition-approved" if stage == "style-composition" else "likeness-approved") if approved else f"{stage}-revision-requested"
        append(root, {"schema_version": SCHEMA_VERSION, "event": "review", "event_id": str(uuid.uuid4()), "created_at": now(), **contract_fields(root, shot, gen), "proposal_id": proposal["proposal_id"], "review_stage": stage, "shot": shot, "version": gen["version"], "status": status, "feedback": flagged.get(shot)})
        if approved and stage == "style-composition":
            append(root, {"schema_version": SCHEMA_VERSION, "event": "selection", "event_id": str(uuid.uuid4()), "created_at": now(), **contract_fields(root, shot, gen), "purpose": "composition-base", "shot": shot, "generation_owner": owner(root, shot), "version": gen["version"], "asset_path": gen["asset_path"], "krea_url": gen.get("krea_url")})
    proposal["confirmed"], proposal["confirmed_at"] = True, now()
    write(proposal_path, proposal)
    rebuild_status(root)


def select_final(root: Path, shot: int, version: int) -> None:
    workflow = read(root / "04-images" / "image-workflow.json")["shots"][shot - 1]
    own = owner(root, shot)
    match = next((item for item in generation_events(events(root)) if item["shot"] == own and item["version"] == version), None)
    if workflow["render_mode"] == "source-photo":
        raise SystemExit("Source-photo selection is registered separately")
    required_stage = "likeness" if workflow["likeness_required"] else "style-composition"
    if not match or match.get("workflow_stage") != required_stage:
        raise SystemExit(f"Final must use approved {required_stage} generation")
    review = latest_review(root, shot, required_stage)
    expected = "likeness-approved" if required_stage == "likeness" else "composition-approved"
    if not review or review.get("status") != expected or review.get("version") != version:
        raise SystemExit(f"Shot {shot:02d} version must be {expected}")
    append(root, {"schema_version": SCHEMA_VERSION, "event": "selection", "event_id": str(uuid.uuid4()), "created_at": now(), **contract_fields(root, shot, match), "purpose": "final", "shot": shot, "generation_owner": own, "version": version, "asset_path": match["asset_path"], "selected_final": True})
    rebuild_status(root)


def rebuild_status(root: Path) -> None:
    workflow_path = root / "04-images" / "image-workflow.json"
    if not workflow_path.exists():
        return
    workflow = read(workflow_path)
    lines = ["# Image review status — Warrior Returning Alive", "", "> Krea style/composition, then GPT Image 2 likeness replacement. Derived from `generations.jsonl`.", ""]
    for item in workflow["shots"]:
        shot = item["shot"]
        if item["render_mode"] == "source-photo":
            lines.append(f"- shot-{shot:02d}: source-photo")
            continue
        comp = latest_generation(root, shot, "style-composition")
        comp_review = latest_review(root, shot, "style-composition")
        base_sel = latest_selection(root, shot, "composition-base")
        like = latest_generation(root, shot, "likeness") if item["likeness_required"] else None
        like_review = latest_review(root, shot, "likeness") if item["likeness_required"] else None
        final = latest_selection(root, shot, "final")
        state = [f"composition={'v%02d' % comp['version'] if comp else 'pending'}"]
        if comp_review: state.append(comp_review["status"])
        if base_sel: state.append(f"base=v{base_sel['version']:02d}")
        if item["likeness_required"]:
            state.append(f"likeness={'v%02d' % like['version'] if like else 'pending'}")
            if like_review: state.append(like_review["status"])
        else:
            state.append("likeness=not-required")
        if final: state.append(f"final=v{final['version']:02d}")
        if item["generation_owner"] != shot: state.append(f"shares={item['generation_owner']:02d}")
        lines.append(f"- shot-{shot:02d}: " + " · ".join(state))
    (root / "04-images" / "status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    pre = sub.add_parser("preflight"); pre.add_argument("--stage", choices=STAGES, required=True)
    comp = sub.add_parser("compile-prompts"); comp.add_argument("--stage", choices=STAGES, required=True); comp.add_argument("--shot", type=int, choices=ALL_SHOTS)
    est = sub.add_parser("set-estimate"); est.add_argument("--stage", choices=STAGES, required=True); est.add_argument("--cu", type=float, required=True); est.add_argument("--minutes", type=float, required=True)
    approve = sub.add_parser("approve-cost"); approve.add_argument("--stage", choices=STAGES, required=True); approve.add_argument("--confirmed", action="store_true")
    rec = sub.add_parser("record"); rec.add_argument("--shot", type=int, choices=ALL_SHOTS, required=True); rec.add_argument("--stage", choices=STAGES, required=True); rec.add_argument("--file", required=True); rec.add_argument("--packet", required=True); rec.add_argument("--krea-job-id"); rec.add_argument("--krea-url")
    prop = sub.add_parser("propose-review"); prop.add_argument("--stage", choices=STAGES, required=True); prop.add_argument("--input", required=True); prop.add_argument("--allow-incomplete", action="store_true")
    app = sub.add_parser("apply-review"); app.add_argument("--proposal", required=True); app.add_argument("--confirmed", action="store_true")
    sel = sub.add_parser("select-final"); sel.add_argument("--shot", type=int, choices=ALL_SHOTS, required=True); sel.add_argument("--version", type=int, required=True)
    sub.add_parser("status")
    args = parser.parse_args()
    root = base.project_dir(args.project)
    if args.command == "init":
        result = configure(root); print(json.dumps({"shots": len(result["shots"]), "workflow": result["passes"]["name"]}))
    elif args.command == "preflight":
        result = preflight(root, args.stage); print(json.dumps(result, indent=2, ensure_ascii=False)); return 0 if result["ready"] else 2
    elif args.command == "compile-prompts": print(json.dumps(compile_prompts(root, args.stage, args.shot), indent=2))
    elif args.command == "set-estimate": print(json.dumps(set_estimate(root, args.stage, args.cu, args.minutes), indent=2))
    elif args.command == "approve-cost": print(json.dumps(approve_cost(root, args.stage, args.confirmed), indent=2))
    elif args.command == "record": print(json.dumps(record(root, args), indent=2, ensure_ascii=False))
    elif args.command == "propose-review": print(json.dumps(propose_review(root, args.stage, Path(args.input), args.allow_incomplete), indent=2, ensure_ascii=False))
    elif args.command == "apply-review": apply_review(root, Path(args.proposal), args.confirmed); print("REVIEW_APPLIED")
    elif args.command == "select-final": select_final(root, args.shot, args.version); print("FINAL_SELECTED")
    elif args.command == "status": rebuild_status(root); print("STATUS_REBUILT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
