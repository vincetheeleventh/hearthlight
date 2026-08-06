#!/usr/bin/env python3
"""Compile versioned Shot Vision into visibility-aware Krea Stage-A prompt packets."""
from __future__ import annotations

import argparse
import concurrent.futures
import functools
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Callable


HERE = Path(__file__).resolve().parent
BASE_SPEC = importlib.util.spec_from_file_location("image_pass", HERE / "image_pass.py")
base = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(base)

MODEL = "krea/krea-2/medium"
STYLE_FALLBACK = (
    "Rendered in ink-and-colour illustration style: confident dark ink linework, "
    "soft flat colour washes, minimal detail, cozy warm palette, background dissolving "
    "to clean white at the edges of frame."
)
MOTION_PATTERN = re.compile(
    r"\b(?:\d+(?:\.\d+)?\s*[–-]\s*\d+(?:\.\d+)?s\s*:|after|then|once|next|meanwhile|"
    r"begins?\s+to|starts?\s+to|about\s+to|enters?\s+frame|comes?\s+down|pedestals?|"
    r"camera\s+(?:moves|rises|pans|tilts|tracks|pedestals))\b",
    re.IGNORECASE,
)
OPTICAL_COLLISIONS = re.compile(r"\b(?:bokeh|shallow depth of field|rack focus|motion blur|glossy 3d)\b", re.I)
GENERIC_QUALITY = re.compile(r"\b(?:masterpiece|award[- ]winning|stunning|gorgeous|beautiful|best quality|highly detailed)\b", re.I)
CONTROL_LEAK = re.compile(r"\b(?:krea(?:\s*2)?|moodboard|style strength|creativity|intensity|complexity|movement|\d+k resolution)\b", re.I)
PROMPT_SCAFFOLD_LEAK = re.compile(r"\b(?:aspect ratio|illustrated narrative frame|rendered in|illustration style|ink(?:ed)? linework|colou?r washes?|watercolou?r|gouache|paper texture|clean white at the edges?|background (?:dissolves|thins|fades) to (?:clean )?white)\b|\b\d+(?:\.\d+)?:\d+(?:\.\d+)?\b", re.I)
VISIBILITY_VALUES = {"clear", "partial", "silhouette", "out-of-focus", "distant"}
AUTHOR_GUIDE = HERE.parent / "references" / "PROMPT-AUTHOR.md"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, default: object = None) -> object:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    events: list[dict] = []
    if not path.is_file():
        return events
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSONL at {path.name}:{number}: {exc.msg}") from exc
        if isinstance(value, dict):
            events.append(value)
    return events


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def normalize_shot(value: object) -> str:
    text = str(value or "").strip()
    return text[:-2] if text.endswith(".0") and text[:-2].isdigit() else text.upper()


def newest_workbook(root: Path) -> Path:
    candidates = sorted((root / "05-storyboard").glob("*shotlist*.xlsx"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        raise ValueError("Shot-list workbook missing")
    return candidates[0]


def workbook_records(root: Path) -> tuple[Path, dict[str, dict], list[str]]:
    source = newest_workbook(root)
    rows = base._xlsx_rows(source, "Shot List")
    if not rows:
        raise ValueError("Shot List sheet empty")
    headers = [str(value or "").strip() for value in rows[0]]
    required = {"Shot", "Shot Title", "Still (frame one)", "Action (motion — video only)", "Camera Movement", "Notes"}
    missing = sorted(required - set(headers))
    if missing:
        raise ValueError("Current shot-list schema missing columns: " + ", ".join(missing))
    records: dict[str, dict] = {}
    for excel_row, row in enumerate(rows[1:], start=2):
        record = {headers[index]: row[index] if index < len(row) else None for index in range(len(headers))}
        label = normalize_shot(record.get("Shot"))
        if label:
            record["_excel_row"] = excel_row
            records[label] = record
    return source, records, headers


def registry_records(root: Path) -> tuple[dict, dict[str, dict], dict[str, dict]]:
    registry = read_json(root / "05-storyboard" / "shots.json", {})
    if not isinstance(registry, dict) or registry.get("status") != "ready":
        raise ValueError("Stable ready shot registry required")
    by_id: dict[str, dict] = {}
    by_label: dict[str, dict] = {}
    for item in registry.get("shots", []):
        if not isinstance(item, dict):
            continue
        shot_id = str(item.get("shot_id") or "")
        label = normalize_shot(item.get("display_number"))
        if not shot_id or not label or item.get("id_state") not in {None, "stable", "new"}:
            raise ValueError("Registry contains missing or unstable Shot ID")
        by_id[shot_id] = item
        by_label[label] = item
    return registry, by_id, by_label


def film_brief(root: Path) -> str:
    path = root / "02-outline" / "FILM-BRIEF.md"
    if not path.is_file():
        raise ValueError("Authoritative FILM-BRIEF.md missing")
    return path.read_text(encoding="utf-8")


def authoritative_aspect_ratio(root: Path) -> str:
    brief = film_brief(root)
    match = re.search(r"\*\*Master aspect\*\*\s*\|\s*\*\*([^*]+)\*\*", brief, re.I)
    if not match:
        raise ValueError("Film Brief does not declare Master aspect")
    ratio = re.search(r"\b\d+\s*:\s*\d+\b", match.group(1))
    if not ratio:
        raise ValueError("Film Brief Master aspect has no numeric ratio")
    return ratio.group(0).replace(" ", "")


def locked_style(root: Path) -> str:
    path = root / "03-bible" / "mise-en-scene.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    match = re.search(r"Rendered in ink-and-colour illustration style:[^\r\n]+", text)
    return match.group(0).strip() if match else STYLE_FALLBACK


def brief_laws(root: Path) -> str:
    text = film_brief(root)
    match = re.search(r"(?ms)^## 5\. What must never happen\s*(.*?)(?=^## )", text)
    return match.group(1).strip() if match else ""


def format_narrative(entry: dict) -> str:
    lines: list[str] = []
    mappings = [
        ("Vision", entry.get("one_liner")),
        ("Meaning", entry.get("expanded")),
        ("Why this shot", entry.get("why_this_shot")),
        ("Beat", entry.get("beat")),
        ("Emotional charge", entry.get("charge")),
    ]
    for label, value in mappings:
        if str(value or "").strip():
            lines.append(f"{label}: {str(value).strip()}")
    for label, key in (("Motifs", "motifs"), ("Never", "never"), ("Open questions", "open_loops")):
        values = entry.get(key)
        if isinstance(values, list) and values:
            lines.append(f"{label}: " + "; ".join(str(value).strip() for value in values if str(value).strip()))
    staging = entry.get("staging") if isinstance(entry.get("staging"), dict) else {}
    surfaced = staging.get("surfaced") if isinstance(staging.get("surfaced"), dict) else {}
    ambient = staging.get("ambient") if isinstance(staging.get("ambient"), dict) else {}
    staging_values = [str(value).strip() for value in [*surfaced.values(), *ambient.values()] if str(value or "").strip()]
    if staging_values:
        lines.append("Staging ideas: " + "; ".join(staging_values))
    return "\n".join(lines).strip()


def seed_visions(root: Path) -> dict[str, dict]:
    payload = read_json(root / "05-storyboard" / "shot-narrative.json", {})
    entries = payload.get("shots", {}) if isinstance(payload, dict) and isinstance(payload.get("shots"), dict) else {}
    return {str(shot_id): {"vision": format_narrative(entry), "source": "shot-narrative.json", "revision": 0} for shot_id, entry in entries.items() if isinstance(entry, dict)}


def current_visions(root: Path) -> dict[str, dict]:
    current = seed_visions(root)
    for event in read_jsonl(root / "04-images" / "shot-vision.jsonl"):
        if event.get("event") not in {"vision-migrated", "vision-updated", "vision-reverted", "vision-rant-applied"}:
            continue
        shot_id = str(event.get("shot_id") or "")
        if shot_id:
            current[shot_id] = {
                "vision": str(event.get("vision") or ""),
                "revision": int(event.get("revision") or 0),
                "event_id": event.get("event_id"),
                "batch_id": event.get("batch_id"),
                "source": event.get("source"),
                "created_at": event.get("created_at"),
                "confirmed_by_user": bool(event.get("confirmed_by_user")),
            }
    return current


def character_records(root: Path) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for path in (root / "03-bible" / "characters").glob("*/character.json"):
        value = read_json(path, {})
        if isinstance(value, dict) and value.get("id"):
            result[str(value["id"])] = value
    return result


def relevant_characters(manifest: dict, shot: dict) -> list[str]:
    labels = {normalize_shot(shot.get("display_number")), *(normalize_shot(value) for value in shot.get("legacy_numbers", []))}
    result: list[str] = []
    for asset in manifest.get("assets", []) if isinstance(manifest.get("assets"), list) else []:
        if not isinstance(asset, dict) or asset.get("kind") != "character-sheet":
            continue
        if any(normalize_shot(value) in labels for value in asset.get("shots", [])):
            result.append(str(asset.get("id") or "").removeprefix("character-"))
    return result


def relevant_assets(manifest: dict, shot: dict) -> list[dict]:
    labels = {normalize_shot(shot.get("display_number")), *(normalize_shot(value) for value in shot.get("legacy_numbers", []))}
    selected: list[dict] = []
    for asset in manifest.get("assets", []) if isinstance(manifest.get("assets"), list) else []:
        if not isinstance(asset, dict) or not any(normalize_shot(value) in labels for value in asset.get("shots", [])):
            continue
        selected.append({
            "id": asset.get("id"), "kind": asset.get("kind"), "status": asset.get("status"),
            "local_path": asset.get("local_path"), "krea_url": asset.get("krea_url"),
        })
    return selected


def narrative_records(root: Path) -> dict[str, dict]:
    value = read_json(root / "05-storyboard" / "shot-narrative.json", {})
    shots = value.get("shots", {}) if isinstance(value, dict) else {}
    return {str(key): item for key, item in shots.items() if isinstance(item, dict)} if isinstance(shots, dict) else {}


def author_guide() -> str:
    if not AUTHOR_GUIDE.is_file():
        raise ValueError("Focused Shot Prompt Author guide is missing")
    return AUTHOR_GUIDE.read_text(encoding="utf-8").strip()


def between(text: str, start: str, end: str | None = None, limit: int = 8000) -> str:
    folded = text.casefold()
    begin = folded.find(start.casefold())
    if begin < 0:
        return ""
    finish = folded.find(end.casefold(), begin + len(start)) if end else -1
    value = text[begin:finish if finish >= 0 else None].strip()
    return value[:limit]


def visual_system_context(root: Path) -> dict[str, str]:
    path = root / "03-bible" / "mise-en-scene.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return {
        "visual_thesis": between(text, "## OVERVIEW", "## THE DRIVEWAY LIGHT LAW", 6000),
        "locked_style_context": between(text, "## TIER 1", "## TIER 1 — CHARACTERS", 5000),
        "driveway_light_law": between(text, "## THE DRIVEWAY LIGHT LAW", "## GATE 4", 7000),
    }


def source_bundle(root: Path, shot_ids: list[str]) -> tuple[dict, dict[str, dict], Path, dict]:
    registry, by_id, _by_label = registry_records(root)
    registry_source = root / "05-storyboard" / "shots.json"
    visions = current_visions(root)
    narratives = narrative_records(root)
    manifest = read_json(root / "03-bible" / "assets.json", {})
    manifest = manifest if isinstance(manifest, dict) else {}
    aspect = authoritative_aspect_ratio(root)
    declared = str(manifest.get("master_aspect_ratio") or "")
    stage = (manifest.get("image_workflow") or {}).get("style_composition", {}) if isinstance(manifest.get("image_workflow"), dict) else {}
    stage_ratio = str(stage.get("aspect_ratio") or "") if isinstance(stage, dict) else ""
    if declared != aspect or stage_ratio != aspect:
        raise ValueError(f"Aspect-ratio conflict: Film Brief={aspect}, assets={declared or 'missing'}, Stage A={stage_ratio or 'missing'}")
    characters = character_records(root)
    ordered = [item for item in registry.get("shots", []) if isinstance(item, dict) and item.get("shot_id")]
    ordered_index = {str(item["shot_id"]): index for index, item in enumerate(ordered)}

    def neighbor_context(shot_id: str) -> list[dict]:
        index = ordered_index.get(shot_id)
        if index is None:
            return []
        context: list[dict] = []
        for relation, position in (("previous", index - 1), ("next", index + 1)):
            if position < 0 or position >= len(ordered):
                continue
            neighbor = ordered[position]
            neighbor_id = str(neighbor.get("shot_id") or "")
            label = normalize_shot(neighbor.get("display_number"))
            neighbor_text = neighbor.get("text") if isinstance(neighbor.get("text"), dict) else {}
            narrative = narratives.get(neighbor_id, {})
            context.append({
                "relation": relation, "shot_id": neighbor_id, "shot": label,
                "still_frame_one": " ".join(str(neighbor_text.get("visual_description") or "").split()),
                "notes": " ".join(str(neighbor_text.get("notes") or "").split()),
                "narrative_one_liner": narrative.get("one_liner"),
                "current_vision": (visions.get(neighbor_id) or {}).get("vision"),
            })
        return context

    visual_system = visual_system_context(root)
    shots: list[dict] = []
    for shot_id in shot_ids:
        shot = by_id.get(shot_id)
        if not shot:
            raise ValueError(f"Unknown Shot ID: {shot_id}")
        label = normalize_shot(shot.get("display_number"))
        row = shot.get("text") if isinstance(shot.get("text"), dict) else {}
        related = relevant_characters(manifest, shot)
        vision = visions.get(shot_id, {"vision": "", "revision": 0})
        shot_text = " ".join([
            str(vision.get("vision") or ""), str(row.get("visual_description") or ""),
            str(row.get("notes") or ""), str(shot.get("title") or ""),
        ])
        special_laws = visual_system["driveway_light_law"] if re.search(r"\b(?:driveway|yard|sun|shadow|pickup|pavement|front door)\b", shot_text, re.I) else ""
        shots.append({
            "shot_id": shot_id,
            "shot": label,
            "title": shot.get("title"),
            "vision": vision,
            "authority_resolution": {
                "creative_authority": "vision.vision",
                "vision_revision": vision.get("revision", 0),
                "vision_confirmed_by_user": bool(vision.get("confirmed_by_user")),
                "storyboard_role": "supersedable technical baseline only",
                "rule": "If Vision and storyboard conflict, follow Vision and record the displaced storyboard fact in supersedes.",
            },
            "storyboard": {
                "still_frame_one": " ".join(str(row.get("visual_description") or "").split()),
                "action_video_only": " ".join(str(row.get("action_description") or "").split()),
                "camera_movement": str(row.get("camera_movement") or "").strip(),
                "notes": " ".join(str(row.get("notes") or "").split()),
                "duration_seconds": shot.get("duration_seconds"),
                "record": f"shots.json:{shot_id}",
            },
            "narrative": narratives.get(shot_id, {}),
            "adjacent_continuity": neighbor_context(shot_id),
            "characters": {name: characters[name] for name in related if name in characters},
            "assets": relevant_assets(manifest, shot),
            "special_visual_laws": special_laws,
            "shared_setup_owner_shot_id": shot.get("shared_setup_owner_shot_id"),
            "render_mode": (shot.get("image_direction") or {}).get("render_mode"),
        })
    bundle = {
        "schema_version": 2,
        "project": root.name,
        "target": {
            "model": MODEL, "aspect_ratio": aspect, "stage": "style-composition",
            "provider_profile": {
                "purpose": "style and composition; facial likeness provisional",
                "style_reference": "moodboard parameter",
                "prompt_expansion": "configuration-dependent",
                "negative_prompt_channel": "not exposed by current Krea packet",
                "controls_are_parameters": True,
            },
        },
        "film_laws": brief_laws(root),
        "locked_style": locked_style(root),
        "visual_system": {
            "visual_thesis": visual_system["visual_thesis"],
            "locked_style_context": visual_system["locked_style_context"],
        },
        "shots": shots,
    }
    semantic_assets = {key: value for key, value in manifest.items() if key != "cost_approvals"}
    source_hashes = {
        "shot_registry": sha256_file(registry_source),
        "film_brief": sha256_file(root / "02-outline" / "FILM-BRIEF.md"),
        "mise_en_scene": sha256_file(root / "03-bible" / "mise-en-scene.md"),
        "assets": sha256_text(json.dumps(semantic_assets, sort_keys=True, ensure_ascii=False, separators=(",", ":"))),
        "author_guide": sha256_file(AUTHOR_GUIDE),
        "vision_ledger": sha256_file(root / "04-images" / "shot-vision.jsonl") if (root / "04-images" / "shot-vision.jsonl").is_file() else None,
    }
    return bundle, by_id, registry_source, source_hashes


def worker_instructions(bundle: dict, repair: dict | None = None) -> str:
    schema = {
        "shots": [{
            "shot_id": "stable ID",
            "frozen_instant": "one present-tense visible tableau",
            "composition": {"shot_size": "", "viewpoint": "", "crop": "", "staging": "", "depth": "", "negative_space": ""},
            "subjects": [{"id": "character id or descriptive id", "role": "", "screen_position": "", "visibility": "clear|partial|silhouette|out-of-focus|distant", "visible_regions": [], "visible_traits": [], "pose": "", "gaze": "", "expression": "", "interaction": ""}],
            "props": [{"name": "", "owner": "", "count": 1, "position": "", "legibility": ""}],
            "environment": "", "lighting": "", "observable_intent": "",
            "required_elements": [], "forbidden_elements": [], "supersedes": [],
            "continuity_choices": [{"fact": "", "source": ""}],
            "prompt_body": "final coherent Krea prompt; visible shot description only; no aspect ratio, style block, headings, or repeated acceptance checklist",
            "prose_plan": {"whole_tableau": "one relational opening sentence", "subject_clauses": [], "light_and_visual_relationship": "one closing relationship; no repetition"},
            "quality_checks": {"single_instant": True, "visibility_grounded": True, "ownership_clear": True, "continuity_grounded": True, "illustration_native": True, "controls_outside_prose": True, "relationally_coherent": True, "non_redundant": True, "concise": True},
            "warnings": [], "blockers": [],
        }]
    }
    repair_text = ""
    if repair:
        repair_text = "\nREPAIR CONTEXT — correct the cited defects without changing Shot Vision:\n" + json.dumps(repair, ensure_ascii=False)
    return (
        "You are Hearthlight's Shot Prompt Author. You have one job: translate each validated source bundle into one intelligent, concise Krea image prompt specification. "
        "Use the focused contract below as active reasoning guidance, not decorative documentation. "
        "LATEST SHOT VISION IS CREATIVE AUTHORITY. Storyboard fields are supersedable baseline evidence. Before writing, compare them, follow Vision in every conflict, and record each displaced baseline fact in supersedes. "
        "For character visible_traits, copy visual_traits[].text exactly; a shot-specific trait is allowed only when copied verbatim from current Vision. Leave gaze and expression blank when the face or eyes are not visible. "
        "Do not copy a stale storyboard composition merely because it is concrete. Build a relational prose plan before the prompt: whole tableau first, atomic subject clauses second, light and the shot-specific visual relationship last. State each fact once. Never substitute global style language for missing staging. Return JSON only; never call tools.\n\n"
        "FOCUSED AUTHOR CONTRACT:\n" + author_guide()
        + "\n\nOUTPUT SCHEMA — match exactly:\n" + json.dumps(schema, ensure_ascii=False)
        + repair_text + "\n\nSOURCE BUNDLE:\n" + json.dumps(bundle, ensure_ascii=False)
    )


def reviewer_instructions(source: dict, spec: dict, prompt: str, bundle: dict) -> str:
    payload = {
        "film_laws": bundle.get("film_laws"), "locked_style": bundle.get("locked_style"),
        "visual_system": bundle.get("visual_system"), "target": bundle.get("target"),
        "shot_source": source, "production_object": spec, "rendered_prompt": prompt,
    }
    schema = {
        "shot_id": source["shot_id"], "verdict": "pass|block",
        "issues": [{"code": "", "detail": "", "source": ""}],
        "warnings": [],
    }
    return (
        "You are Hearthlight's independent Shot Prompt Reviewer. Do not rewrite the prompt and do not add creative direction. "
        "Judge whether the prompt is coherent, source-grounded, visually intelligent, visibility-aware, continuity-safe, illustration-native, concise, and likely to produce the intended Krea Stage-A frame. "
        "LATEST SHOT VISION IS CREATIVE AUTHORITY; storyboard is supersedable baseline only. First compare prompt and production object directly against every Vision Composition, Screen geography, Visible tableau, Must hold, and Never clause. Block any stale storyboard framing, subject, setup, or geography that the Vision replaced. "
        "Block material ambiguity, invented facts, conflicting geography/light/counts, invisible identity overload, abstract emotion without visible evidence, attribute-binding risk, medium collision, needless semantic density, checklist-like fragments, repeated acceptance conditions, or prose that lists parts without first establishing their shared spatial relationship. "
        "The rendered prompt must read as one coherent visible-frame description. Aspect ratio, locked style, moodboard, model controls, and structured Must show checks stay outside prompt prose. "
        "Do not block harmless wording preference. Return strict JSON only.\n\nREVIEW GUIDELINE:\n"
        + author_guide() + "\n\nOUTPUT SCHEMA:\n" + json.dumps(schema, ensure_ascii=False)
        + "\n\nREVIEW PAYLOAD:\n" + json.dumps(payload, ensure_ascii=False)
    )
def parse_worker_json(text: str) -> dict:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.I | re.S).strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Prompt worker returned no JSON object")
        value = json.loads(candidate[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("Prompt worker response must be a JSON object")
    return value


@functools.lru_cache(maxsize=1)
def hermes_model_config() -> tuple[str, str]:
    result = subprocess.run(
        ["hermes", "config", "get", "model"], cwd=HERE, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=30, check=False,
    )
    if result.returncode:
        raise ValueError("Hermes inference profile is unavailable")
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    model, provider = values.get("default", ""), values.get("provider", "")
    if not model or not provider:
        raise ValueError("Hermes model.default or model.provider is missing")
    return model, provider


def run_hermes(prompt: str, timeout: int = 300) -> dict:
    model, provider = hermes_model_config()
    hermes_command = shutil.which("hermes")
    if not hermes_command:
        raise ValueError("Hermes executable is unavailable")
    bridge_python = Path(hermes_command).with_name("python.exe")
    if not bridge_python.is_file():
        raise ValueError("Hermes Python runtime is unavailable")
    bridge_code = (
        "import json,sys; from pathlib import Path; "
        "d=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')); "
        "sys.argv=['hermes','--safe-mode','--model',d['model'],'--provider',d['provider'],'--oneshot',d['prompt']]; "
        "from hermes_cli.main import main; main()"
    )
    with tempfile.TemporaryDirectory(prefix="hearthlight-hermes-") as temporary:
        payload_path = Path(temporary) / "prompt.json"
        payload_path.write_text(
            json.dumps({"model": model, "provider": provider, "prompt": prompt}, ensure_ascii=False),
            encoding="utf-8",
        )
        result = subprocess.run(
            [str(bridge_python), "-c", bridge_code, str(payload_path)],
            cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout, check=False,
        )
    if result.returncode:
        detail = (result.stderr or result.stdout or "Hermes inference worker failed").strip().splitlines()[-1]
        raise ValueError(detail[:500])
    return parse_worker_json(result.stdout)


def invoke_hermes(bundle: dict, timeout: int = 300, repair: dict | None = None) -> dict:
    return run_hermes(worker_instructions(bundle, repair), timeout)


def invoke_reviewer(source: dict, spec: dict, prompt: str, bundle: dict, timeout: int = 300) -> dict:
    instructions = reviewer_instructions(source, spec, prompt, bundle)
    try:
        return run_hermes(instructions, timeout)
    except ValueError:
        return run_hermes(
            instructions + "\n\nRETRY: Your previous response was malformed JSON. Return one syntactically valid JSON object only; preserve the same review judgment.",
            timeout,
        )
def clean(value: object) -> str:
    return " ".join(str(value or "").split()).strip()


def clean_paragraphs(value: object) -> str:
    paragraphs = [" ".join(part.split()) for part in re.split(r"\n\s*\n", str(value or "").strip())]
    return "\n\n".join(part for part in paragraphs if part)


def validate_spec(spec: dict, source: dict, characters: dict[str, dict], aspect_ratio: str) -> list[str]:
    blockers = [clean(value) for value in spec.get("blockers", []) if clean(value)] if isinstance(spec.get("blockers"), list) else []
    if str(spec.get("shot_id") or "") != str(source["shot_id"]):
        blockers.append("Worker Shot ID does not match source")
    instant = clean(spec.get("frozen_instant"))
    body = clean_paragraphs(spec.get("prompt_body"))
    if not instant:
        blockers.append("Frozen instant is blank")
    if not body:
        blockers.append("Prompt body is blank")
    combined = "\n".join([instant, body])
    if MOTION_PATTERN.search(combined):
        blockers.append("Prompt contains motion or multiple temporal states")
    if OPTICAL_COLLISIONS.search(combined):
        blockers.append("Prompt contains unresolved photographic/optical language")
    if GENERIC_QUALITY.search(body):
        blockers.append("Prompt contains generic quality adjectives instead of visible construction")
    if CONTROL_LEAK.search(body):
        blockers.append("Krea request controls leaked into prompt prose")
    if PROMPT_SCAFFOLD_LEAK.search(body):
        blockers.append("Aspect ratio, deliverable, or rendering-style scaffolding leaked into Krea prompt prose")
    if len(body.split()) > 350:
        blockers.append("Prompt body exceeds 350 words and risks semantic overload")
    style = clean(source.get("locked_style"))
    if style and style.casefold() in body.casefold():
        blockers.append("Prompt body duplicates the locked style sentence")

    selected_by_character: dict[str, set[str]] = {}
    for subject in spec.get("subjects", []) if isinstance(spec.get("subjects"), list) else []:
        if not isinstance(subject, dict):
            blockers.append("Subject entry is not an object")
            continue
        identity = str(subject.get("id") or "")
        if not identity:
            blockers.append("Subject has no stable ID or descriptive ID")
        visibility = clean(subject.get("visibility")).casefold()
        if visibility not in VISIBILITY_VALUES:
            blockers.append(f"Subject {identity or '?'} has invalid visibility: {visibility or 'blank'}")
        character = characters.get(identity, {})
        region_aliases = {"hand": "hands", "forearm": "arms", "sleeve cuff": "arms", "cardigan sleeve": "arms", "lower leg": "legs", "lower legs": "legs", "boot": "feet", "boots": "feet", "shoulder": "torso"}
        visible = {region_aliases.get(clean(region).casefold(), clean(region).casefold()) for region in subject.get("visible_regions", []) if clean(region)} if isinstance(subject.get("visible_regions"), list) else set()
        if not visible:
            blockers.append(f"Subject {identity or '?'} has no visible body regions")
        if visibility in {"partial", "silhouette", "out-of-focus", "distant"} and not ({"face", "eyes"} & visible):
            if clean(subject.get("gaze")) or clean(subject.get("expression")):
                blockers.append(f"Invisible gaze or expression assigned to {identity or '?'}")
        allowed: dict[str, set[str]] = {}
        for trait in character.get("visual_traits", []) if isinstance(character.get("visual_traits"), list) else []:
            if isinstance(trait, dict):
                allowed[clean(trait.get("text"))] = {clean(region).casefold() for region in trait.get("regions", []) if clean(region)}
        selected = {clean(trait) for trait in subject.get("visible_traits", []) if clean(trait)} if isinstance(subject.get("visible_traits"), list) else set()
        selected_by_character[identity] = selected
        for trait_text in selected:
            regions = allowed.get(trait_text)
            vision_text = clean((source.get("vision") or {}).get("vision"))
            vision_grounded = bool(trait_text and trait_text.casefold() in vision_text.casefold())
            if character and trait_text not in allowed and not vision_grounded:
                blockers.append(f"Unknown or paraphrased trait selected for {identity}: {trait_text}")
            elif regions and not (regions & visible):
                blockers.append(f"Invisible trait selected for {identity}: {trait_text}")
        signature = clean(character.get("signature_string"))
        if signature and signature.casefold() in combined.casefold():
            blockers.append(f"Full character signature pasted into Stage A for {identity}")

    for prop in spec.get("props", []) if isinstance(spec.get("props"), list) else []:
        if not isinstance(prop, dict):
            blockers.append("Prop entry is not an object")
            continue
        name, owner, position = clean(prop.get("name")), clean(prop.get("owner")), clean(prop.get("position"))
        if not name:
            blockers.append("Prop has no name")
        if not owner:
            blockers.append(f"Prop {name or '?'} has no owner")
        if not position:
            blockers.append(f"Prop {name or '?'} has no screen position")
        count = prop.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            blockers.append(f"Prop {name or '?'} has invalid count")

    for forbidden in spec.get("forbidden_elements", []) if isinstance(spec.get("forbidden_elements"), list) else []:
        phrase = clean(forbidden)
        if len(phrase) >= 4 and phrase.casefold() in body.casefold():
            blockers.append(f"Forbidden element leaked into positive prompt: {phrase}")
    checks = spec.get("quality_checks") if isinstance(spec.get("quality_checks"), dict) else {}
    expected_checks = {"single_instant", "visibility_grounded", "ownership_clear", "continuity_grounded", "illustration_native", "controls_outside_prose", "relationally_coherent", "non_redundant", "concise"}
    failed_checks = [key for key in expected_checks if checks.get(key) is not True]
    if failed_checks:
        blockers.append("Author self-audit failed: " + ", ".join(sorted(failed_checks)))
    return list(dict.fromkeys(blockers))


def render_prompt(spec: dict, style: str = "", aspect_ratio: str = "") -> str:
    """Return only author prose; style, aspect, and acceptance checks are request metadata."""
    return clean_paragraphs(spec.get("prompt_body"))
def compile_batch(
    root: Path,
    batch_id: str,
    shot_ids: list[str],
    worker: Callable[[dict], dict] | None = None,
    reviewer: Callable[[dict, dict, str, dict], dict] | None = None,
) -> dict:
    bundle, registry_by_id, registry_source, source_hashes = source_bundle(root, shot_ids)
    manifest = read_json(root / "03-bible" / "assets.json", {})
    manifest = manifest if isinstance(manifest, dict) else {}
    moodboard = manifest.get("moodboard") if isinstance(manifest.get("moodboard"), dict) else {}
    if not moodboard or not moodboard.get("id") or str(moodboard.get("status") or "").casefold() not in {"selected", "approved"}:
        raise ValueError("Selected moodboard missing or unapproved")

    if worker:
        worker_result = worker(bundle)
    else:
        def author_one(source: dict) -> dict:
            one_bundle = {**bundle, "shots": [source]}
            try:
                result = invoke_hermes(one_bundle)
            except ValueError:
                result = invoke_hermes(one_bundle, repair={
                    "validation_errors": ["Previous author response was malformed JSON."],
                    "instruction": "Return one syntactically valid JSON object only. Preserve source facts and the same creative judgment.",
                })
            result_items = result.get("shots") if isinstance(result, dict) else None
            if not isinstance(result_items, list) or len(result_items) != 1:
                raise ValueError(f"Prompt author returned an invalid result for {source['shot_id']}")
            return result_items[0]

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(bundle["shots"]))) as executor:
            worker_result = {"shots": list(executor.map(author_one, bundle["shots"]))}
    result_shots = worker_result.get("shots") if isinstance(worker_result, dict) else None
    if not isinstance(result_shots, list):
        raise ValueError("Prompt author response has no shots array")
    by_result = {str(item.get("shot_id") or ""): item for item in result_shots if isinstance(item, dict)}
    expected = {str(item["shot_id"]) for item in bundle["shots"]}
    if set(by_result) != expected:
        raise ValueError(f"Prompt author Shot IDs differ from request: expected={sorted(expected)}, received={sorted(by_result)}")

    aspect = bundle["target"]["aspect_ratio"]
    style = bundle["locked_style"]
    semantic_reviewer = reviewer or (invoke_reviewer if worker is None else None)

    def prepare(source: dict, raw_spec: dict) -> dict:
        spec = dict(raw_spec)
        validation_source = {**source, "project": root.name, "locked_style": style}
        blockers = validate_spec(spec, validation_source, source.get("characters", {}), aspect)
        prompt = render_prompt(spec, style, aspect) if not blockers else ""
        if prompt and MOTION_PATTERN.search(prompt):
            blockers.append("Rendered prompt contains motion or multiple temporal states")
            prompt = ""
        return {"spec": spec, "blockers": list(dict.fromkeys(blockers)), "prompt": prompt}

    def normalize_review(value: dict, shot_id: str) -> dict:
        if not isinstance(value, dict):
            return {"shot_id": shot_id, "verdict": "block", "issues": [{"code": "invalid-review", "detail": "Reviewer returned no JSON object", "source": "reviewer"}], "warnings": []}
        issues = value.get("issues") if isinstance(value.get("issues"), list) else []
        normalized_issues = [
            {"code": clean(item.get("code")) or "semantic-review", "detail": clean(item.get("detail")), "source": clean(item.get("source"))}
            for item in issues if isinstance(item, dict) and clean(item.get("detail"))
        ]
        verdict = clean(value.get("verdict")).casefold()
        if str(value.get("shot_id") or "") != shot_id:
            normalized_issues.append({"code": "shot-id-mismatch", "detail": "Reviewer Shot ID does not match source", "source": "reviewer"})
            verdict = "block"
        if verdict not in {"pass", "block"}:
            normalized_issues.append({"code": "invalid-verdict", "detail": "Reviewer verdict must be pass or block", "source": "reviewer"})
            verdict = "block"
        return {
            "shot_id": shot_id, "verdict": verdict, "issues": normalized_issues,
            "warnings": [clean(item.get("detail") if isinstance(item, dict) else item) for item in value.get("warnings", []) if clean(item.get("detail") if isinstance(item, dict) else item)] if isinstance(value.get("warnings"), list) else [],
        }

    def polish_one(source: dict) -> dict:
        shot_id = str(source["shot_id"])
        draft = prepare(source, by_result[shot_id])
        attempts = 1
        review: dict = {"shot_id": shot_id, "verdict": "not-run", "issues": [], "warnings": []}

        if draft["blockers"] and worker is None:
            repair_bundle = {**bundle, "shots": [source]}
            repaired = invoke_hermes(repair_bundle, repair={
                "previous_production_object": draft["spec"],
                "deterministic_blockers": draft["blockers"],
            })
            items = repaired.get("shots") if isinstance(repaired, dict) else None
            if isinstance(items, list) and len(items) == 1:
                draft = prepare(source, items[0])
                attempts += 1

        if not draft["blockers"] and semantic_reviewer:
            review = normalize_review(semantic_reviewer(source, draft["spec"], draft["prompt"], bundle), shot_id)
            if review["verdict"] == "block" and worker is None and attempts < 2:
                repair_bundle = {**bundle, "shots": [source]}
                repaired = invoke_hermes(repair_bundle, repair={
                    "previous_production_object": draft["spec"], "semantic_review": review,
                })
                items = repaired.get("shots") if isinstance(repaired, dict) else None
                if isinstance(items, list) and len(items) == 1:
                    draft = prepare(source, items[0])
                    attempts += 1
                    if not draft["blockers"]:
                        review = normalize_review(semantic_reviewer(source, draft["spec"], draft["prompt"], bundle), shot_id)
            if review["verdict"] == "block":
                for issue in review["issues"]:
                    draft["blockers"].append(f"Semantic review [{issue['code']}]: {issue['detail']}")
                draft["prompt"] = ""
        elif not semantic_reviewer and not draft["blockers"]:
            review = {"shot_id": shot_id, "verdict": "not-run", "issues": [], "warnings": ["Semantic reviewer bypassed by injected test worker"]}

        draft["blockers"] = list(dict.fromkeys(draft["blockers"]))
        draft["review"] = review
        draft["author_attempts"] = attempts
        return {"shot_id": shot_id, **draft}

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(bundle["shots"]))) as executor:
        polished = list(executor.map(polish_one, bundle["shots"]))
    final_by_id = {item["shot_id"]: item for item in polished}

    output_dir = root / "04-images" / "prompt-specs" / batch_id
    packet_dir = root / "04-images" / "prompt-packets" / f"vision-{batch_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    packet_dir.mkdir(parents=True, exist_ok=True)
    compiled: list[dict] = []
    for source in bundle["shots"]:
        shot_id = str(source["shot_id"])
        final = final_by_id[shot_id]
        spec = dict(final["spec"])
        blockers = final["blockers"]
        prompt = final["prompt"] if not blockers else ""
        review = final["review"]
        warnings = [clean(value) for value in spec.get("warnings", []) if clean(value)] if isinstance(spec.get("warnings"), list) else []
        warnings.extend(review.get("warnings", []))
        spec.update({
            "schema_version": 2,
            "project": root.name,
            "shot": source["shot"],
            "title": source["title"],
            "vision_revision": source["vision"].get("revision", 0),
            "aspect_ratio": aspect,
            "model": MODEL,
            "locked_style": style,
            "source": {"authority": "shot-registry", "shot_registry": relpath(registry_source, root), "record": source["storyboard"]["record"], "archived_board_source": (read_json(registry_source, {}) or {}).get("source"), "hashes": source_hashes},
            "semantic_review": review,
            "author_attempts": final["author_attempts"],
            "blockers": blockers,
            "warnings": list(dict.fromkeys(warnings)),
        })
        safe_label = re.sub(r"[^0-9A-Za-z_-]+", "-", source["shot"]).strip("-").casefold()
        spec_path = output_dir / f"shot-{safe_label}.json"
        atomic_json(spec_path, spec)
        registered = registry_by_id[shot_id]
        packet = {
            "schema_version": 3,
            "created_at": now(),
            "project": root.name,
            "shot": source["shot"],
            "shot_id": shot_id,
            "title": source["title"],
            "workflow_stage": "style-composition",
            "model": MODEL,
            "aspect_ratio": aspect,
            "resolution": "1K",
            "generation_parameters": {"creativity": "raw", "intensity": 0, "complexity": 0, "movement": 0},
            "prompt": prompt,
            "references": [{"type": "moodboard", "id": moodboard["id"], "strength": moodboard.get("strength", 0.35)}],
            "vision_batch_id": batch_id,
            "vision_revision": source["vision"].get("revision", 0),
            "prompt_spec": relpath(spec_path, root),
            "source": spec["source"],
            "semantic_review": review,
            "author_attempts": final["author_attempts"],
            "blockers": blockers,
            "warnings": spec["warnings"],
            "shared_setup_owner_shot_id": registered.get("shared_setup_owner_shot_id"),
        }
        packet["prompt_sha256"] = sha256_text(prompt) if prompt else None
        request_payload = {key: packet[key] for key in ("model", "aspect_ratio", "resolution", "generation_parameters", "prompt", "references")}
        packet["request_sha256"] = sha256_text(json.dumps(request_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))) if prompt else None
        packet_path = packet_dir / f"shot-{safe_label}-style-composition.json"
        atomic_json(packet_path, packet)
        compiled.append({
            "shot": source["shot"], "shot_id": shot_id, "title": source["title"],
            "vision_revision": source["vision"].get("revision", 0), "prompt": prompt,
            "prompt_sha256": packet["prompt_sha256"], "request_sha256": packet["request_sha256"],
            "prompt_spec": relpath(spec_path, root), "packet": relpath(packet_path, root),
            "warnings": packet["warnings"], "blockers": blockers,
            "semantic_review": review, "author_attempts": final["author_attempts"],
            "supersedes": spec.get("supersedes", []),
        })
    estimate = ((manifest.get("cost_approvals") or {}).get("style_composition_v4") or {}) if isinstance(manifest.get("cost_approvals"), dict) else {}
    batch = {
        "schema_version": 2,
        "batch_id": batch_id,
        "project": root.name,
        "created_at": now(),
        "status": "blocked" if any(item["blockers"] for item in compiled) else "ready-for-approval",
        "model": MODEL,
        "aspect_ratio": aspect,
        "moodboard": {"id": moodboard["id"], "name": moodboard.get("name"), "strength": moodboard.get("strength", 0.35)},
        "source_hashes": source_hashes,
        "job_count": sum(1 for item in compiled if not item["blockers"]),
        "estimated_cu": estimate.get("estimated_cu"),
        "estimated_minutes": estimate.get("estimated_minutes"),
        "shots": compiled,
    }
    batch["batch_sha256"] = sha256_text(json.dumps({key: batch[key] for key in ("model", "aspect_ratio", "moodboard", "source_hashes", "shots")}, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    atomic_json(output_dir / "batch.json", batch)
    return batch

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--shots", nargs="+", required=True)
    args = parser.parse_args()
    try:
        batch = compile_batch(args.project_root.resolve(), args.batch_id, args.shots)
    except Exception as exc:
        print(json.dumps({"compiled": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"compiled": True, "batch": batch}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
