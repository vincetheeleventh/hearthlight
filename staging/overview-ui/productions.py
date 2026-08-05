"""Hearthlight production projection for Hearthlight Studio.

Canonical production files stay inside Story Studio. This adapter normalizes
old and new project layouts for the UI without silently migrating or repairing them.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import uuid
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic", ".heif"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
MEDIA_SUFFIXES = IMAGE_SUFFIXES | VIDEO_SUFFIXES
APPROVED_WORDS = {"approved", "done", "selected", "final", "composition-approved", "likeness-approved"}
NAMESPACE = uuid.UUID("78784992-9873-4c66-965e-a0a04f21eff6")
STATUS_VALUES = {"missing", "incomplete", "upcoming", "ready for approval", "approved", "warning", "not applicable"}
INVALID_IDENTITY_LABELS = {"", "-", "?", "none", "null", "n/a", "new"}


class ProductionDataError(ValueError):
    pass


def read_json(path: Path, default: object = None) -> object:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionDataError(f"Malformed JSON: {path}") from exc


def read_jsonl(path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    records: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []
    if not path.is_file():
        return records, findings
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [{"code": "unreadable-file", "severity": "warning", "path": str(path), "detail": str(exc)}]
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            findings.append({"code": "malformed-jsonl", "severity": "warning", "path": str(path), "line": number, "detail": str(exc)})
            continue
        if isinstance(value, dict):
            records.append(value)
    return records, findings


def safe_child(root: Path, relative: str | Path, *, must_exist: bool = False) -> Path:
    base = root.resolve()
    raw = Path(str(relative).replace("\\", "/"))
    if raw.is_absolute():
        candidate = raw.resolve()
    else:
        candidate = (base / raw).resolve()
    if candidate != base and base not in candidate.parents:
        raise ProductionDataError("Path escapes the production root")
    if must_exist and not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def iso_mtime(path: Path) -> str:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).replace(microsecond=0).isoformat()
    except OSError:
        return ""


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def as_number(value: object) -> int | float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def display_name(slug: str) -> str:
    return re.sub(r"[-_]+", " ", slug).strip().title() or slug


def stable_id(*parts: object) -> str:
    return str(uuid.uuid5(NAMESPACE, "|".join(str(part) for part in parts)))


def valid_identity_label(value: object) -> str | None:
    text = str(value or "").strip()
    return None if text.casefold() in INVALID_IDENTITY_LABELS else text


def parse_distribution(path: Path) -> dict[str, object]:
    result: dict[str, object] = {"format": "", "client": "", "chargedRegister": "", "source": ""}
    if not path.is_file():
        return result
    text = path.read_text(encoding="utf-8")
    for source, target in [("format", "format"), ("client", "client"), ("charged_register", "chargedRegister")]:
        match = re.search(rf"(?im)^\s*[-*]?\s*{re.escape(source)}\s*:\s*([^\r\n]+)", text)
        if match:
            result[target] = match.group(1).strip().strip("`*")
    source = re.search(r"(?im)^\s*Source:\s*`([^`]+)`", text)
    if source:
        result["source"] = source.group(1).strip()
    aspect = re.search(r"(?im)^\s*[-*]\s*((?:\d+:\d+)[^\r\n]*)", text)
    if aspect:
        result["aspectRatio"] = aspect.group(1).split()[0].rstrip(".,")
    return result


def parse_ledger(path: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    if not path.is_file():
        return result
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        match = re.match(r"(approved|pending|unconfirmed|n/a|done)\s*(.*)", value, re.I)
        if match:
            result[key] = {"state": match.group(1).casefold(), "date": match.group(2).strip()}
    return result


def _xlsx_rows(path: Path, sheet_name: str) -> list[list[object]]:
    ns = {
        "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "p": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    with zipfile.ZipFile(path) as book:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in book.namelist():
            tree = ET.fromstring(book.read("xl/sharedStrings.xml"))
            shared = ["".join(node.text or "" for node in item.findall(".//m:t", ns)) for item in tree.findall("m:si", ns)]
        workbook = ET.fromstring(book.read("xl/workbook.xml"))
        rel_id = next((sheet.attrib.get(f"{{{ns['r']}}}id") for sheet in workbook.findall("m:sheets/m:sheet", ns) if sheet.attrib.get("name") == sheet_name), None)
        if not rel_id:
            raise ProductionDataError(f"Worksheet not found: {sheet_name}")
        rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        target = next((rel.attrib.get("Target") for rel in rels.findall("p:Relationship", ns) if rel.attrib.get("Id") == rel_id), None)
        if not target:
            raise ProductionDataError(f"Worksheet relationship missing: {sheet_name}")
        sheet = ET.fromstring(book.read("xl/" + str(target).lstrip("/").removeprefix("xl/")))
        values: dict[tuple[int, int], object] = {}
        max_row = max_col = 0
        for cell in sheet.findall(".//m:sheetData/m:row/m:c", ns):
            match = re.match(r"([A-Z]+)(\d+)", cell.attrib.get("r", ""))
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
                value: object = "".join(node.text or "" for node in cell.findall(".//m:t", ns))
            elif value_node is None:
                value = None
            elif kind == "s":
                value = shared[int(value_node.text or 0)]
            elif kind in {"str", "e"}:
                value = value_node.text
            else:
                value = as_number(value_node.text)
                if value is None:
                    value = value_node.text
            values[(row, col)] = value
            max_row, max_col = max(max_row, row), max(max_col, col)
        return [[values.get((row, col)) for col in range(1, max_col + 1)] for row in range(1, max_row + 1)]


def normalize_shot(item: dict[str, object], slug: str, source: str, inferred: bool) -> dict[str, object]:
    display = item.get("display_number", item.get("shot"))
    legacy = item.get("legacy_numbers")
    if not isinstance(legacy, list):
        legacy = [item.get("legacy_id") if item.get("legacy_id") not in (None, "") else display]
    text = item.get("text") if isinstance(item.get("text"), dict) else {}
    image = item.get("image_direction") if isinstance(item.get("image_direction"), dict) else {}
    if not image:
        image = {
            "visual_description": item.get("image_visual_description") or "",
            "action_description": item.get("image_action_description") or "",
            "camera_movement": item.get("image_camera_movement") or "",
            "continuity_note": item.get("image_pass_note") or "",
            "render_mode": item.get("render_mode") or "",
            "source_asset": item.get("source_asset"),
        }
    order_value = as_number(item.get("order"))
    order = int(order_value) if order_value is not None else 0
    return {
        "shotId": str(item.get("shot_id") or f"inferred-{stable_id(slug, source, display, item.get('title'))}"),
        "displayNumber": display,
        "order": order,
        "legacyNumbers": [label for value in legacy if (label := valid_identity_label(value))],
        "legacyLabels": [dict(value) for value in item.get("legacy_labels", []) if isinstance(value, dict)],
        "title": str(item.get("title") or item.get("shot_title") or f"Shot {display}"),
        "start": str(item.get("start") or ""),
        "end": str(item.get("end") or ""),
        "durationSeconds": as_number(item.get("duration_seconds")),
        "boardPanels": item.get("board_panels") if isinstance(item.get("board_panels"), list) else [str(item.get("board_panel"))] if item.get("board_panel") not in (None, "", "—", "-") else [],
        "storyboardReference": str(item.get("storyboard_reference") or ""),
        "sharedSetupOwnerShotId": item.get("shared_setup_owner_shot_id"),
        "sharedSetupOwnerNumber": item.get("generation_owner") if item.get("generation_owner") != display else None,
        "registrySource": source,
        "inferred": inferred,
        "reconciliationStatus": item.get("id_state") or ("inferred" if inferred else "stable"),
        "story": {
            "visualDescription": str(text.get("visual_description") or item.get("source_visual_description") or ""),
            "dialogue": str(text.get("dialogue") or ""),
            "audio": str(text.get("audio") or ""),
            "notes": str(text.get("notes") or item.get("source_notes") or ""),
        },
        "imageDirection": {
            "visualDescription": str(image.get("visual_description") or ""),
            "actionDescription": str(image.get("action_description") or ""),
            "cameraMovement": str(image.get("camera_movement") or ""),
            "continuityNote": str(image.get("continuity_note") or ""),
            "renderMode": str(image.get("render_mode") or ""),
            "sourceAsset": image.get("source_asset"),
        },
        "videoMotion": {
            "actionDescription": str(text.get("action_description") or item.get("source_action_description") or image.get("action_description") or ""),
            "cameraMovement": str(text.get("camera_movement") or item.get("source_camera_movement") or image.get("camera_movement") or ""),
        },
    }


def load_narrative(project: Path, findings: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Read the rebuild-proof narrative sidecar, keyed by immutable shot_id."""
    path = project / "05-storyboard" / "shot-narrative.json"
    try:
        payload = read_json(path, {})
        entries = payload.get("shots", {}) if isinstance(payload, dict) else {}
        if not isinstance(entries, dict):
            return {}
        return {str(key): value for key, value in entries.items() if isinstance(value, dict)}
    except ProductionDataError as exc:
        findings.append({"code": "shot-narrative-unreadable", "severity": "warning", "path": "05-storyboard/shot-narrative.json", "detail": str(exc)})
        return {}


def narrative_vision(entry: dict[str, object]) -> str:
    """Render the legacy narrative object as an editable human-facing Shot Vision draft."""
    lines: list[str] = []
    for label, key in [
        ("Vision", "one_liner"), ("Meaning", "expanded"), ("Why this shot", "why_this_shot"),
        ("Beat", "beat"), ("Emotional charge", "charge"),
    ]:
        value = str(entry.get(key) or "").strip()
        if value:
            lines.append(f"{label}: {value}")
    for label, key in [("Motifs", "motifs"), ("Never", "never"), ("Open questions", "open_loops")]:
        values = entry.get(key)
        if isinstance(values, list):
            value = "; ".join(str(item).strip() for item in values if str(item or "").strip())
            if value:
                lines.append(f"{label}: {value}")
    staging = entry.get("staging") if isinstance(entry.get("staging"), dict) else {}
    staging_values: list[str] = []
    for group in (staging.get("surfaced"), staging.get("ambient")):
        if isinstance(group, dict):
            staging_values.extend(str(value).strip() for value in group.values() if str(value or "").strip())
    if staging_values:
        lines.append("Staging ideas: " + "; ".join(staging_values))
    return "\n".join(lines)


def load_vision_events(project: Path, findings: list[dict[str, object]]) -> list[dict[str, object]]:
    events, event_findings = read_jsonl(project / "04-images" / "shot-vision.jsonl")
    findings.extend(event_findings)
    return events


def attach_vision(
    shots: list[dict[str, object]],
    narrative_entries: dict[str, dict[str, object]],
    events: list[dict[str, object]],
) -> None:
    by_shot: dict[str, list[dict[str, object]]] = {}
    for event in events:
        if event.get("event") in {"vision-migrated", "vision-updated", "vision-reverted", "vision-rant-applied"}:
            by_shot.setdefault(str(event.get("shot_id") or ""), []).append(event)
    for shot in shots:
        shot_id = str(shot.get("shotId") or "")
        seed = narrative_vision(narrative_entries.get(shot_id, {}))
        history = sorted(by_shot.get(shot_id, []), key=lambda item: (int(item.get("revision") or 0), str(item.get("created_at") or "")))
        latest = history[-1] if history else None
        shot["shotVision"] = {
            "text": str((latest or {}).get("vision") or seed),
            "revision": int((latest or {}).get("revision") or 0),
            "eventId": (latest or {}).get("event_id"),
            "batchId": (latest or {}).get("batch_id"),
            "source": (latest or {}).get("source") or ("shot-narrative.json draft" if seed else "blank"),
            "updatedAt": (latest or {}).get("created_at"),
            "seededDraft": not history and bool(seed),
            "history": [
                {
                    "eventId": item.get("event_id"), "batchId": item.get("batch_id"),
                    "revision": int(item.get("revision") or 0), "text": str(item.get("vision") or ""),
                    "previousText": str(item.get("previous_vision") or ""),
                    "source": item.get("source"), "createdAt": item.get("created_at"),
                    "event": item.get("event"),
                }
                for item in reversed(history)
            ],
        }


def load_prompt_batches(project: Path, events: list[dict[str, object]], findings: list[dict[str, object]]) -> list[dict[str, object]]:
    approvals = {
        str(event.get("batch_id") or ""): event
        for event in events if event.get("event") == "prompt-batch-approved" and event.get("batch_id")
    }
    batches: list[dict[str, object]] = []
    root = project / "04-images" / "prompt-specs"
    for path in root.glob("*/batch.json") if root.is_dir() else []:
        try:
            batch = read_json(path, None)
        except ProductionDataError as exc:
            findings.append({"code": "prompt-batch-unreadable", "severity": "warning", "path": path.relative_to(project).as_posix(), "detail": str(exc)})
            continue
        if not isinstance(batch, dict) or not batch.get("batch_id"):
            continue
        value = dict(batch)
        approval = approvals.get(str(value["batch_id"]))
        value["approved"] = bool(approval and approval.get("batch_sha256") == value.get("batch_sha256"))
        value["approvedAt"] = (approval or {}).get("created_at")
        value["path"] = path.relative_to(project).as_posix()
        batches.append(value)
    return sorted(batches, key=lambda item: str(item.get("created_at") or ""), reverse=True)


def attach_narrative(shots: list[dict[str, object]], entries: dict[str, dict[str, object]]) -> None:
    """Join narrative sidecar entries onto normalized shots. Missing entry = not yet authored."""
    for shot in shots:
        entry = entries.get(str(shot.get("shotId")), {})
        staging = entry.get("staging") if isinstance(entry.get("staging"), dict) else {}
        surfaced = staging.get("surfaced") if isinstance(staging.get("surfaced"), dict) else {}
        ambient = staging.get("ambient") if isinstance(staging.get("ambient"), dict) else {}
        loops = entry.get("open_loops")
        shot["narrative"] = {
            "authored": bool(entry),
            "oneLiner": str(entry.get("one_liner") or ""),
            "expanded": str(entry.get("expanded") or ""),
            "openLoops": [str(loop) for loop in loops if str(loop or "").strip()] if isinstance(loops, list) else [],
            "whyThisShot": str(entry.get("why_this_shot") or ""),
            "staging": {
                "surfaced": {
                    "shotType": str(surfaced.get("shot_type") or ""),
                    "cameraMove": str(surfaced.get("camera_move") or ""),
                    "characterActions": str(surfaced.get("character_actions") or ""),
                    "setting": str(surfaced.get("setting") or ""),
                },
                "ambient": {
                    "props": str(ambient.get("props") or ""),
                    "lighting": str(ambient.get("lighting") or ""),
                    "sound": str(ambient.get("sound") or ""),
                },
            },
        }


def load_shots(project: Path, findings: list[dict[str, object]]) -> tuple[list[dict[str, object]], str, dict[str, object]]:
    slug = project.name
    registry_path = project / "05-storyboard" / "shots.json"
    if registry_path.is_file():
        try:
            payload = read_json(registry_path, {})
            assert isinstance(payload, dict)
            shots = [normalize_shot(item, slug, "shots.json", False) for item in payload.get("shots", []) if isinstance(item, dict)]
            findings.extend(payload.get("validation_findings", []))
            return sorted(shots, key=lambda item: item["order"]), "shots.json", payload
        except (ProductionDataError, AssertionError) as exc:
            findings.append({"code": "shot-registry-unreadable", "severity": "warning", "path": "05-storyboard/shots.json", "detail": str(exc)})

    specs_path = project / "04-images" / "shot-specs.json"
    if specs_path.is_file():
        try:
            payload = read_json(specs_path, {})
            assert isinstance(payload, dict)
            shots = [normalize_shot(item, slug, "shot-specs.json", True) for item in payload.get("shots", []) if isinstance(item, dict)]
            by_number = {str(item["displayNumber"]): item for item in shots}
            for shot in shots:
                owner = shot.pop("sharedSetupOwnerNumber", None)
                if owner is not None:
                    shot["sharedSetupOwnerShotId"] = by_number.get(str(owner), {}).get("shotId")
            return sorted(shots, key=lambda item: item["order"]), "shot-specs.json", payload
        except (ProductionDataError, AssertionError) as exc:
            findings.append({"code": "shot-specs-unreadable", "severity": "warning", "path": "04-images/shot-specs.json", "detail": str(exc)})

    storyboard = project / "05-storyboard" / "storyboard.md"
    if storyboard.is_file():
        rows = []
        for index, match in enumerate(re.finditer(r"(?im)^##\s*Shot\s+([^—\-\r\n]+)\s*(?:[—-]\s*(.*))?$", storyboard.read_text(encoding="utf-8")), start=1):
            number = match.group(1).strip()
            rows.append(normalize_shot({"shot": number, "title": (match.group(2) or "").strip(), "order": index}, slug, "storyboard.md", True))
        if rows:
            return rows, "storyboard.md", {}

    workbooks = sorted((project / "05-storyboard").glob("*.xlsx"), key=lambda path: path.stat().st_mtime, reverse=True)
    for workbook in workbooks:
        try:
            rows = _xlsx_rows(workbook, "Shot List")
            headers = [str(value or "").strip() for value in rows[0]]
            shots = []
            for order, row in enumerate(rows[1:], start=1):
                record = {headers[index]: row[index] if index < len(row) else None for index in range(len(headers))}
                if record.get("Shot") in (None, ""):
                    continue
                visual = record.get("Visual Description") or record.get("Still (frame one)")
                action = record.get("Action Description") or record.get("Action (motion — video only)")
                item = {
                    "shot": record["Shot"], "order": order, "title": record.get("Shot Title"), "legacy_id": record.get("Legacy ID"),
                    "board_panel": record.get("Board Panel"), "duration_seconds": record.get("Duration (s)"), "start": record.get("Start"), "end": record.get("End"),
                    "source_visual_description": visual, "source_action_description": action, "source_camera_movement": record.get("Camera Movement"), "source_notes": record.get("Notes"),
                    "text": {"dialogue": record.get("Dialogue"), "audio": record.get("Audio")},
                }
                shots.append(normalize_shot(item, slug, workbook.name, True))
            if shots:
                return shots, workbook.name, {}
        except (OSError, ProductionDataError, zipfile.BadZipFile) as exc:
            findings.append({"code": "shot-list-unreadable", "severity": "warning", "path": workbook.name, "detail": str(exc)})

    inferred: dict[str, Path] = {}
    for directory in [project / "04-images", project / "06-video", project / "03-bible" / "refs" / "storyboard-panels"]:
        for path in directory.glob("*.*") if directory.is_dir() else []:
            match = re.search(r"(?:shot|panel)[-_ ]*0*(\d+)", path.stem, re.I)
            if path.suffix.casefold() in MEDIA_SUFFIXES and match:
                inferred.setdefault(match.group(1), path)
    shots = [normalize_shot({"shot": int(number), "title": f"Shot {number}", "order": int(number)}, slug, "filenames", True) for number in sorted(inferred, key=int)]
    return shots, "filenames", {}


def event_time(event: dict[str, object], path: Path | None = None) -> str:
    return str(event.get("created_at") or event.get("timestamp") or (iso_mtime(path) if path else ""))


def is_approved(value: object) -> bool:
    text = str(value or "").casefold().replace("_", "-")
    return any(word in text for word in APPROVED_WORDS)


def media_url(slug: str, asset_id: str, *, preview: bool = False, poster: bool = False) -> str:
    url = f"/production-media/{quote(slug, safe='')}/{quote(asset_id, safe='')}"
    if preview:
        return url + "?preview=1"
    if poster:
        return url + "?poster=1"
    return url


@dataclass(frozen=True)
class MediaTarget:
    path: Path
    content_type: str
    generated: bool = False


class ProductionAdapter:
    def __init__(self, hearthlight_root: Path, cache_dir: Path):
        self.root = hearthlight_root.resolve()
        self.projects_root = (self.root / "projects").resolve()
        self.cache_dir = cache_dir.resolve()

    def _project(self, slug: str) -> Path:
        if not slug or Path(slug).name != slug:
            raise ProductionDataError("Invalid production slug")
        project = (self.projects_root / slug).resolve()
        if self.projects_root not in project.parents or not project.is_dir():
            raise FileNotFoundError(slug)
        return project

    def _pipeline(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        pipeline = read_json(self.root / "skills" / "hearthlight-dashboard" / "pipeline.json", {})
        requirements = read_json(self.root / "skills" / "hearthlight-dashboard" / "requirements.json", {})
        stages = pipeline.get("stages", []) if isinstance(pipeline, dict) else []
        rules = requirements.get("requirements", []) if isinstance(requirements, dict) else []
        return [item for item in stages if isinstance(item, dict)], [item for item in rules if isinstance(item, dict)]

    def list_productions(self) -> dict[str, object]:
        productions = []
        if self.projects_root.is_dir():
            for project in sorted((item for item in self.projects_root.iterdir() if item.is_dir() and not item.name.startswith(".")), key=lambda item: item.name.casefold()):
                try:
                    full = self.get_production(project.name)
                except Exception as exc:
                    productions.append({"slug": project.name, "name": display_name(project.name), "error": str(exc), "shotCount": 0, "blockerCount": 0, "pendingReviewCount": 0})
                    continue
                productions.append({key: full.get(key) for key in ["slug", "name", "format", "client", "runtimeSeconds", "shotCount", "uniqueIllustratedSetups", "gateProgress", "blockerCount", "pendingReviewCount", "lastActivity", "coverAsset", "nextAction", "validationCount"]})
        return {"productions": productions, "root": str(self.root)}

    def _requirements(self, project: Path, stages: list[dict[str, object]], rules: list[dict[str, object]], ledger: dict[str, dict[str, str]], assets_manifest: dict[str, object], findings: list[dict[str, object]]) -> tuple[list[dict[str, object]], int]:
        index = {str(stage.get("id")): position for position, stage in enumerate(stages)}
        approved_positions = [index[key] for key, value in ledger.items() if key in index and value.get("state") in {"approved", "done"}]
        active_position = max(approved_positions, default=-1) + 1
        result: list[dict[str, object]] = []

        def urgency(stage_id: object) -> str:
            position = index.get(str(stage_id), len(stages))
            return "now" if position <= active_position else "later"

        def add(rule: dict[str, object], status: str, evidence: list[str], *, suffix: str = "", label: str | None = None, detail: str = "") -> None:
            if status not in STATUS_VALUES:
                status = "warning"
            stage_id = rule.get("stage_dependency")
            result.append({
                "id": str(rule.get("id")) + suffix,
                "label": label or str(rule.get("label") or rule.get("id")),
                "scope": str(rule.get("scope") or "project"),
                "status": status,
                "urgency": urgency(stage_id) if status not in {"approved", "not applicable"} else "resolved",
                "stageDependency": stage_id,
                "gateDependency": rule.get("gate_dependency"),
                "evidence": evidence,
                "expectedPath": rule.get("expected_path"),
                "detail": detail,
            })

        registry_assets = [item for item in assets_manifest.get("assets", []) if isinstance(item, dict)]
        handled = {"character-dossier", "character-record", "character-sheet", "environment-sheet", "timing", "image-prompt", "approved-still", "storyboard-panel", "approved-current-video"}
        for rule in rules:
            if rule.get("id") in handled or rule.get("scope") == "shot":
                continue
            evidence_rule = rule.get("evidence") if isinstance(rule.get("evidence"), dict) else {}
            expected = str(rule.get("expected_path") or "")
            matches = list(project.glob(expected)) if evidence_rule.get("type") == "glob" else [project / expected]
            present = sum(1 for path in matches if path.exists()) >= int(evidence_rule.get("minimum") or 1)
            gate_state = ledger.get(str(rule.get("gate_dependency")), {}).get("state")
            status = "approved" if present and gate_state in {"approved", "done"} else "ready for approval" if present else "missing" if urgency(rule.get("stage_dependency")) == "now" else "upcoming"
            add(rule, status, [str(path.relative_to(project)).replace("\\", "/") for path in matches if path.exists()])

        character_rules = {str(rule.get("id")): rule for rule in rules if str(rule.get("id")).startswith("character-")}
        for asset in [item for item in registry_assets if item.get("kind") == "character-sheet"]:
            character = str(asset.get("id") or "character").removeprefix("character-")
            folder = project / "03-bible" / "characters" / character
            record_path = folder / "character.json"
            dossier_path = folder / "CHARACTER.md"
            record = read_json(record_path, {}) if record_path.is_file() else {}
            record = record if isinstance(record, dict) else {}
            sheet_rel = str(record.get("sheet") or asset.get("local_path") or "")
            try:
                sheet_path = safe_child(project, sheet_rel) if sheet_rel else folder / f"{character}-sheet.png"
            except ProductionDataError:
                sheet_path = folder / f"{character}-sheet.png"
                findings.append({"code": "unsafe-character-sheet-path", "severity": "warning", "character": character, "path": sheet_rel})
            for key, path in [("character-dossier", dossier_path), ("character-record", record_path)]:
                rule = character_rules.get(key, {"id": key, "label": key, "scope": "project", "stage_dependency": "characters", "gate_dependency": "gate2_mise_en_scene", "expected_path": str(path.relative_to(project))})
                add(rule, "ready for approval" if path.is_file() else "missing", [str(path.relative_to(project)).replace("\\", "/")] if path.is_file() else [], suffix=f":{character}", label=f"{display_name(character)} {str(rule.get('label')).casefold()}")
            rule = character_rules.get("character-sheet", {"id": "character-sheet", "label": "Approved character sheet", "scope": "project", "stage_dependency": "characters", "gate_dependency": "gate3_images", "expected_path": sheet_rel})
            states = [str(asset.get("status") or "").casefold(), str(record.get("status") or "").casefold(), str(record.get("sheet_status") or "").casefold()]
            semantic_states = {
                "approved" if is_approved(state)
                else "missing" if any(word in state for word in {"missing", "absent", "not found"})
                else "pending"
                for state in states if state
            }
            approved = bool(states) and all(is_approved(state) for state in states if state) and sheet_path.is_file()
            if not sheet_path.is_file():
                status = "missing"
            elif "missing" in semantic_states:
                status = "warning"
                findings.append({"code": "conflicting-character-status", "severity": "warning", "character": character, "states": states})
            else:
                status = "approved" if approved else "ready for approval"
            add(rule, status, [str(sheet_path.relative_to(project)).replace("\\", "/")] if sheet_path.is_file() else [], suffix=f":{character}", label=f"{display_name(character)} character sheet", detail=" / ".join(state for state in states if state))

        environment_rule = next((rule for rule in rules if rule.get("id") == "environment-sheet"), {"id": "environment-sheet", "label": "Environment sheet", "scope": "project", "stage_dependency": "gate2_mise_en_scene", "gate_dependency": "gate3_images"})
        for asset in [item for item in registry_assets if item.get("kind") == "setting-sheet"]:
            rel = str(asset.get("local_path") or "")
            path = safe_child(project, rel) if rel else project / "missing"
            status = "approved" if path.is_file() and is_approved(asset.get("status")) else "incomplete" if path.is_file() else "missing"
            add(environment_rule, status, [rel] if path.is_file() else [], suffix=f":{asset.get('id')}", label=str(asset.get("id") or "Environment").removeprefix("setting-").replace("-", " ").title(), detail=str(asset.get("status") or ""))

        blocker_count = sum(1 for item in result if item["urgency"] == "now" and item["status"] in {"missing", "incomplete"})
        return result, blocker_count

    def _assets(
        self,
        project: Path,
        slug: str,
        shots: list[dict[str, object]],
        ledger: dict[str, dict[str, str]],
        findings: list[dict[str, object]],
        retired_shots: list[dict[str, object]] | None = None,
    ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        retired_shots = retired_shots or []
        all_shots = shots + retired_shots
        retired_ids = {str(shot["shotId"]) for shot in retired_shots}
        by_id = {str(shot["shotId"]): shot for shot in all_shots}
        number_candidates: dict[str, list[dict[str, object]]] = {}
        legacy_candidates: dict[str, list[dict[str, object]]] = {}
        revision_candidates: dict[str, dict[str, list[dict[str, object]]]] = {}
        for shot in all_shots:
            number_candidates.setdefault(str(shot["displayNumber"]).casefold(), []).append(shot)
            for legacy in shot["legacyNumbers"]:
                legacy_candidates.setdefault(str(legacy).casefold(), []).append(shot)
            for label in shot.get("legacyLabels", []):
                revision = str(label.get("revision") or "").casefold()
                value = valid_identity_label(label.get("label"))
                if revision and value:
                    revision_candidates.setdefault(revision, {}).setdefault(value.casefold(), []).append(shot)
        by_number = {key: values[0] for key, values in number_candidates.items() if len(values) == 1}
        by_legacy = {key: values[0] for key, values in legacy_candidates.items() if len(values) == 1}
        panel_candidates: dict[str, list[dict[str, object]]] = {}
        by_revision = {revision: {key: values[0] for key, values in labels.items() if len(values) == 1} for revision, labels in revision_candidates.items()}
        for shot in all_shots:
            for panel in shot.get("boardPanels", []):
                panel_candidates.setdefault(str(panel).casefold(), []).append(shot)
        by_panel = {key: values[0] for key, values in panel_candidates.items() if len(values) == 1}
        strict_identity = bool(shots) and all(
            not shot.get("inferred") and shot.get("reconciliationStatus") in {"stable", "new"}
            for shot in shots
        )

        mapping_payload = read_json(project / "05-storyboard" / "asset-shot-map.json", {})
        mapping_payload = mapping_payload if isinstance(mapping_payload, dict) else {}
        mapping_entries = [item for item in mapping_payload.get("entries", []) if isinstance(item, dict)]
        mapping_by_event = {str(item.get("event_id")): item for item in mapping_entries if item.get("event_id")}
        mapping_by_asset = {str(item.get("asset_id")): item for item in mapping_entries if item.get("asset_id")}
        mapping_by_path = {str(item.get("asset_path")): item for item in mapping_entries if item.get("asset_path")}

        image_events, image_findings = read_jsonl(project / "04-images" / "generations.jsonl")
        video_events, video_findings = read_jsonl(project / "06-video" / "ledger.jsonl")
        findings.extend(image_findings + video_findings)
        assets_manifest = read_json(project / "03-bible" / "assets.json", {})
        assets_manifest = assets_manifest if isinstance(assets_manifest, dict) else {}
        registered_references = {str(item.get("id")): item for item in assets_manifest.get("assets", []) if isinstance(item, dict)}
        moodboard = assets_manifest.get("moodboard") if isinstance(assets_manifest.get("moodboard"), dict) else {}
        assets: list[dict[str, object]] = []
        asset_by_key: dict[tuple[str, str, str], dict[str, object]] = {}
        referenced: set[Path] = set()

        def event_shot(event: dict[str, object]) -> dict[str, object] | None:
            explicit = str(event.get("shot_id") or "")
            if explicit in by_id:
                event["_mapped_by"] = "shot-id"
                return by_id[explicit]
            mapping = (
                mapping_by_event.get(str(event.get("event_id") or ""))
                or mapping_by_asset.get(str(event.get("asset_id") or ""))
                or mapping_by_path.get(str(event.get("asset_path") or event.get("path") or ""))
            )
            mapped_id = str((mapping or {}).get("shot_id") or "")
            if mapped_id in by_id:
                event["_mapped_by"] = str((mapping or {}).get("mapped_by") or "asset-shot-map")
                return by_id[mapped_id]
            legacy = valid_identity_label(event.get("legacy_shot_v3"))
            legacy_lookup = by_revision.get("v3", by_legacy)
            if legacy and legacy.casefold() in legacy_lookup:
                event["_mapped_by"] = "revision-label-v3" if "v3" in by_revision else "legacy-shot-v3"
                return legacy_lookup[legacy.casefold()]
            display = valid_identity_label(event.get("shot") or event.get("generation_owner"))
            if display and display.casefold() in by_number:
                event["_mapped_by"] = "display-number"
                return by_number[display.casefold()]
            return None

        def event_references(event: dict[str, object]) -> list[dict[str, object]]:
            result: list[dict[str, object]] = []
            for raw in event.get("references", []) if isinstance(event.get("references"), list) else []:
                if not isinstance(raw, dict):
                    continue
                reference = dict(raw)
                reference_id = str(reference.get("id") or "")
                manifest_reference = registered_references.get(reference_id, {})
                if reference.get("type") == "moodboard" and reference_id == str(moodboard.get("id") or ""):
                    reference.setdefault("name", moodboard.get("name"))
                    reference.setdefault("status", moodboard.get("status"))
                    reference.setdefault("strength", moodboard.get("strength"))
                else:
                    reference.setdefault("name", manifest_reference.get("id"))
                    reference.setdefault("status", manifest_reference.get("status"))
                rel = str(reference.get("local_path") or manifest_reference.get("local_path") or "")
                if rel:
                    try:
                        path = safe_child(project, rel, must_exist=True)
                    except (ProductionDataError, FileNotFoundError):
                        path = None
                    if path:
                        ref_asset_id = f"reference-{stable_id(slug, rel)}"
                        reference.update({"path": rel, "assetId": ref_asset_id, "mediaUrl": media_url(slug, ref_asset_id), "thumbnailUrl": media_url(slug, ref_asset_id, preview=path.suffix.casefold() in {".heic", ".heif"})})
                result.append(reference)
            return result

        for event in image_events + video_events:
            if event.get("event") in {"review", "selection", "prompt-edit"}:
                continue
            if event.get("event") not in {"generation", "video", "clip", "render", "output"} and not event.get("asset_path") and not event.get("path"):
                continue
            shot = event_shot(event)
            if not shot:
                findings.append({"code": "unresolved-legacy-asset", "severity": "warning", "eventId": event.get("event_id"), "shot": event.get("shot")})
                continue
            rel = str(event.get("asset_path") or event.get("path") or "")
            if str(shot["shotId"]) in retired_ids:
                try:
                    referenced.add(safe_child(project, rel, must_exist=True).resolve())
                except (ProductionDataError, FileNotFoundError):
                    pass
                continue
            try:
                path = safe_child(project, rel, must_exist=True)
            except (ProductionDataError, FileNotFoundError) as exc:
                findings.append({"code": "missing-or-unsafe-asset", "severity": "warning", "shotId": shot["shotId"], "path": rel, "detail": str(exc)})
                continue
            referenced.add(path)
            kind = "video" if path.suffix.casefold() in VIDEO_SUFFIXES else "image"
            stage = str(event.get("workflow_stage") or event.get("stage") or ("video" if kind == "video" else "image"))
            aid = str(event.get("asset_id") or event.get("event_id") or f"legacy-{stable_id(slug, rel, event.get('shot'), event.get('version'))}")
            asset = {
                "assetId": aid, "shotId": shot["shotId"], "kind": kind, "stage": stage, "path": rel,
                "mediaUrl": media_url(slug, aid), "thumbnailUrl": media_url(slug, aid, preview=path.suffix.casefold() in {".heic", ".heif"}, poster=kind == "video"),
                "createdAt": event_time(event, path), "provider": event.get("source") or event.get("provider"), "model": event.get("model"),
                "reviewState": str(event.get("review_status") or event.get("status") or "pending-review"), "selectionState": "selected-final" if event.get("selected_final") else "",
                "version": event.get("version"), "prompt": event.get("prompt"), "settings": {key: event.get(key) for key in ["dimensions", "aspect_ratio", "resolution", "references", "krea_job_id", "krea_url"] if event.get(key) is not None},
                "sha256": event.get("sha256"), "parentAssetId": event.get("parent_asset_id") or event.get("conditioning_asset_id"), "feedback": event.get("feedback"),
                "inferred": not bool(event.get("asset_id") or event.get("shot_id")), "stale": False,
                "references": event_references(event), "selectionPurposes": ["final"] if event.get("selected_final") else [], "heroSelectedAt": "", "mappedBy": event.get("_mapped_by"),
            }
            dimensions = event.get("dimensions")
            aspect = str(event.get("aspect_ratio") or "")
            aspect_match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)\s*", aspect)
            if isinstance(dimensions, list) and len(dimensions) == 2 and aspect_match:
                try:
                    actual_ratio = float(dimensions[0]) / float(dimensions[1])
                    declared_ratio = float(aspect_match.group(1)) / float(aspect_match.group(2))
                except (TypeError, ValueError, ZeroDivisionError):
                    actual_ratio = declared_ratio = 0
                if actual_ratio and abs(actual_ratio - declared_ratio) > 0.04:
                    findings.append({"code": "aspect-metadata-mismatch", "severity": "warning", "shotId": shot["shotId"], "assetId": aid, "dimensions": dimensions, "declaredAspectRatio": aspect})
            assets.append(asset)
            asset_by_key[(str(shot["shotId"]), str(event.get("version")), stage)] = asset

        for event in image_events + video_events:
            if event.get("event") not in {"review", "selection"}:
                continue
            shot = event_shot(event)
            if not shot:
                continue
            if str(shot["shotId"]) in retired_ids:
                continue
            stage = str(event.get("review_stage") or event.get("workflow_stage") or "image")
            target = next((asset for asset in reversed(assets) if asset["shotId"] == shot["shotId"] and (event.get("asset_id") == asset["assetId"] or (str(asset.get("version")) == str(event.get("version")) and (stage == "image" or asset["stage"] == stage)))), None)
            if not target:
                continue
            if event.get("event") == "review":
                target["reviewState"] = str(event.get("status") or target["reviewState"])
                target["feedback"] = event.get("feedback")
            else:
                purpose = str(event.get("purpose") or ("final" if event.get("selected_final") else ""))
                if purpose and purpose not in target["selectionPurposes"]:
                    target["selectionPurposes"].append(purpose)
                if purpose == "final":
                    target["selectionState"] = "selected-final"
                elif purpose == "composition-base" and target["selectionState"] != "selected-final":
                    target["selectionState"] = "composition-base"
                elif purpose == "hero":
                    target["heroSelectedAt"] = str(event.get("created_at") or "")

        panel_root = project / "03-bible" / "refs" / "storyboard-panels"
        if panel_root.is_dir():
            for path in panel_root.rglob("*.*"):
                if path.suffix.casefold() not in IMAGE_SUFFIXES:
                    continue
                match = re.search(r"(?:shot|panel)[-_ ]*0*(\d+[A-Za-z]?)", path.stem, re.I)
                shot = by_panel.get(match.group(1).casefold()) if match else None
                if not shot:
                    continue
                rel = path.relative_to(project).as_posix()
                aid = f"board-{stable_id(slug, rel)}"
                assets.append({"assetId": aid, "shotId": shot["shotId"], "kind": "image", "stage": "storyboard", "path": rel, "mediaUrl": media_url(slug, aid), "thumbnailUrl": media_url(slug, aid, preview=path.suffix.casefold() in {".heic", ".heif"}), "createdAt": iso_mtime(path), "provider": "hand-drawn", "model": None, "reviewState": "approved" if ledger.get("gate4_storyboard", {}).get("state") in {"approved", "done"} else "mapped", "selectionState": "mapped", "version": None, "prompt": None, "settings": {}, "sha256": None, "parentAssetId": None, "feedback": None, "inferred": True, "stale": False, "references": [], "selectionPurposes": [], "heroSelectedAt": ""})
                referenced.add(path.resolve())

        unmapped: list[dict[str, object]] = []
        for directory in [project / "04-images", project / "06-video", panel_root]:
            if not directory.is_dir():
                continue
            for path in directory.rglob("*.*"):
                if path.suffix.casefold() not in MEDIA_SUFFIXES or path.resolve() in referenced:
                    continue
                rel = path.relative_to(project).as_posix()
                mapping = mapping_by_path.get(rel)
                shot = by_id.get(str((mapping or {}).get("shot_id") or ""))
                mapped_by = str((mapping or {}).get("mapped_by") or "")
                if not shot:
                    stable_match = re.search(r"-([0-9a-f]{8})-v\d+$", path.stem, re.I)
                    prefix_matches = [
                        candidate for shot_id, candidate in by_id.items()
                        if stable_match and shot_id.casefold().startswith(stable_match.group(1).casefold())
                    ]
                    if len(prefix_matches) == 1:
                        shot = prefix_matches[0]
                        mapped_by = "stable-id-filename"
                if not shot and not strict_identity:
                    match = re.search(r"shot[-_ ]*0*(\d+[A-Za-z]?)", path.stem, re.I)
                    shot = by_number.get(match.group(1).casefold()) if match else None
                    mapped_by = "display-number-fallback" if shot else ""
                if not shot:
                    reason = (
                        "Numeric filename is not revision-safe; register this path to a stable shot ID"
                        if strict_identity else "No unambiguous shot number"
                    )
                    unmapped.append({"path": rel, "reason": reason, "inferred": True})
                    continue
                if str(shot["shotId"]) in retired_ids:
                    referenced.add(path.resolve())
                    continue
                aid = f"inferred-{stable_id(slug, rel)}"
                kind = "video" if path.suffix.casefold() in VIDEO_SUFFIXES else "image"
                assets.append({"assetId": aid, "shotId": shot["shotId"], "kind": kind, "stage": "video" if kind == "video" else "image", "path": rel, "mediaUrl": media_url(slug, aid), "thumbnailUrl": media_url(slug, aid, poster=kind == "video", preview=path.suffix.casefold() in {".heic", ".heif"}), "createdAt": iso_mtime(path), "provider": "filesystem", "model": None, "reviewState": "pending-review", "selectionState": "", "version": None, "prompt": None, "settings": {}, "sha256": None, "parentAssetId": None, "feedback": None, "inferred": True, "stale": False, "references": [], "selectionPurposes": [], "heroSelectedAt": "", "mappedBy": mapped_by})
        return assets, unmapped

    @staticmethod
    def _resolve_heroes(shots: list[dict[str, object]], assets: list[dict[str, object]]) -> None:
        for shot in shots:
            history = sorted([asset for asset in assets if asset["shotId"] == shot["shotId"]], key=lambda asset: str(asset.get("createdAt") or ""), reverse=True)
            approved_stills = [asset for asset in history if asset["kind"] == "image" and asset["stage"] != "storyboard" and (asset["selectionState"] == "selected-final" or ("final" in str(asset["stage"]).casefold() and is_approved(asset["reviewState"]))) ]
            current_still = approved_stills[0] if approved_stills else None
            for asset in history:
                if asset["kind"] != "video" or not current_still:
                    continue
                parent = asset.get("parentAssetId")
                if not parent or str(parent) != str(current_still["assetId"]):
                    asset["stale"] = True
            approved_video = next((asset for asset in history if asset["kind"] == "video" and is_approved(asset["reviewState"]) and not asset["stale"]), None)
            selected_hero = max((asset for asset in history if asset.get("heroSelectedAt") and not asset["stale"]), key=lambda asset: str(asset.get("heroSelectedAt") or ""), default=None)
            composition_base = next((asset for asset in history if asset["kind"] == "image" and asset.get("selectionState") == "composition-base"), None)
            board = next((asset for asset in history if asset["stage"] == "storyboard" and asset["reviewState"] in {"approved", "mapped"}), None)
            approved = approved_video or selected_hero or current_still or composition_base or board
            pending = next((asset for asset in history if not is_approved(asset["reviewState"]) and not asset["stale"]), None)
            hero = approved or pending
            shot["assetHistory"] = history
            shot["heroAsset"] = hero
            shot["newerPendingAsset"] = pending if approved and pending and pending is not approved and str(pending.get("createdAt") or "") > str(approved.get("createdAt") or "") else None
            shot["badges"] = [
                *(["pending review"] if pending else []),
                *(["shared setup"] if shot.get("sharedSetupOwnerShotId") else []),
                *(["stale output"] if any(asset["stale"] for asset in history) else []),
                *(["unresolved mapping"] if shot.get("reconciliationStatus") == "needs_reconciliation" else []),
                *(["inferred"] if shot.get("inferred") else []),
            ]

        by_shot_id = {str(shot["shotId"]): shot for shot in shots}
        for shot in shots:
            owner_id = str(shot.get("sharedSetupOwnerShotId") or "")
            owner = by_shot_id.get(owner_id)
            if shot.get("heroAsset") is None and owner and owner.get("heroAsset"):
                inherited = dict(owner["heroAsset"])
                inherited["inheritedFromShotId"] = owner_id
                shot["heroAsset"] = inherited
    def get_production(self, slug: str) -> dict[str, object]:
        project = self._project(slug)
        findings: list[dict[str, object]] = []
        distribution = parse_distribution(project / "distribution-spec.md")
        ledger = parse_ledger(project / "status.yml")
        stages, rules = self._pipeline()
        stage_ids = [str(stage.get("id")) for stage in stages]
        gates = []
        seen_unapproved = False
        for stage in stages:
            if stage.get("kind") != "gate":
                continue
            stage_id = str(stage.get("id"))
            state = ledger.get(stage_id, {}).get("state", "unconfirmed")
            approved = state in {"approved", "done"}
            if approved and seen_unapproved:
                findings.append({"code": "gate-history-inconsistency", "severity": "warning", "stage": stage_id, "detail": "A later gate is approved while an earlier gate remains pending."})
            if not approved and state != "n/a":
                seen_unapproved = True
            gates.append({"id": stage_id, "label": stage.get("label"), "gate": stage.get("gate"), "state": state, "date": ledger.get(stage_id, {}).get("date", "")})

        shots, registry_source, registry_payload = load_shots(project, findings)
        narrative_entries = load_narrative(project, findings)
        attach_narrative(shots, narrative_entries)
        vision_events = load_vision_events(project, findings)
        attach_vision(shots, narrative_entries, vision_events)
        prompt_batches = load_prompt_batches(project, vision_events, findings)
        latest_prompt_batch = prompt_batches[0] if prompt_batches else None
        retired_shots = []
        for item in registry_payload.get("retired_shots", []) if isinstance(registry_payload, dict) else []:
            if not isinstance(item, dict):
                continue
            retired = normalize_shot(item, slug, "shots.json", False)
            retired.update({"retiredAt": item.get("retired_at"), "retiredReason": item.get("retired_reason")})
            retired_shots.append(retired)
        attach_narrative(retired_shots, narrative_entries)
        attach_vision(retired_shots, narrative_entries, vision_events)
        latest_workbook = max((project / "05-storyboard").glob("*.xlsx"), key=lambda path: path.stat().st_mtime, default=None)
        registry_source_path = str(registry_payload.get("source") or "")
        registered_workbook = None
        if registry_source_path:
            try:
                candidate = safe_child(project, registry_source_path)
                if candidate.is_file() and candidate.suffix.casefold() in {".xlsx", ".xlsm"}:
                    registered_workbook = candidate
            except ProductionDataError:
                registered_workbook = None
        shot_list_path = registered_workbook or latest_workbook
        shot_list_document = None
        if shot_list_path:
            shot_list_document = {
                "name": shot_list_path.name,
                "path": shot_list_path.relative_to(project).as_posix(),
                "source": "registered" if registered_workbook else "latest available",
                "modifiedAt": iso_mtime(shot_list_path),
            }
        newer_source = bool(
            latest_workbook
            and registry_source_path
            and latest_workbook.resolve() != (project / registry_source_path).resolve()
        )
        if newer_source:
            findings.append({"code": "newer-shot-source", "severity": "warning", "registered": registry_source_path, "newest": latest_workbook.relative_to(project).as_posix(), "detail": "A newer shot-list workbook exists. Reconcile it explicitly before rebuilding the registry."})
        assets_manifest = read_json(project / "03-bible" / "assets.json", {})
        assets_manifest = assets_manifest if isinstance(assets_manifest, dict) else {}
        project_requirements, blocker_count = self._requirements(project, stages, rules, ledger, assets_manifest, findings)
        assets, unmapped = self._assets(project, slug, shots, ledger, findings, retired_shots)
        self._resolve_heroes(shots, assets)

        registry_assets = [item for item in assets_manifest.get("assets", []) if isinstance(item, dict)]
        workflow = assets_manifest.get("image_workflow") if isinstance(assets_manifest.get("image_workflow"), dict) else {}
        style_settings = workflow.get("style_composition") if isinstance(workflow.get("style_composition"), dict) else {}
        likeness_settings = workflow.get("likeness") if isinstance(workflow.get("likeness"), dict) else {}
        image_events, _event_findings = read_jsonl(project / "04-images" / "generations.jsonl")
        prompt_edits = [item for item in image_events if item.get("event") == "prompt-edit"]
        jobs: list[dict[str, object]] = []
        job_dir = project / "04-images" / "studio-generation-jobs"
        if job_dir.is_dir():
            for path in job_dir.glob("*.json"):
                try:
                    value = read_json(path, None)
                except ProductionDataError:
                    continue
                if isinstance(value, dict):
                    jobs.append(value)

        def reference_descriptor(item: dict[str, object], *, reference_type: str | None = None, strength: object = None) -> dict[str, object]:
            reference_id = str(item.get("id") or stable_id(item.get("local_path"), item.get("name")))
            rel = str(item.get("local_path") or item.get("path") or "")
            descriptor: dict[str, object] = {
                "id": reference_id,
                "type": reference_type or item.get("kind") or "reference",
                "name": item.get("name") or display_name(reference_id.removeprefix("character-").removeprefix("setting-").removeprefix("prop-")),
                "status": item.get("status"),
                "strength": strength,
                "path": rel or None,
            }
            if rel:
                try:
                    path = safe_child(project, rel, must_exist=True)
                except (ProductionDataError, FileNotFoundError):
                    path = None
                if path:
                    media_id = f"reference-{stable_id(slug, rel)}"
                    descriptor.update({"assetId": media_id, "mediaUrl": media_url(slug, media_id), "thumbnailUrl": media_url(slug, media_id, preview=path.suffix.casefold() in {".heic", ".heif"})})
            return descriptor

        def required_asset_label(asset: dict[str, object]) -> str:
            identifier = str(asset.get("id") or "asset")
            kind = str(asset.get("kind") or "asset")
            base = display_name(identifier.removeprefix("character-").removeprefix("setting-").removeprefix("prop-"))
            suffix = {"character-sheet": "character sheet", "setting-sheet": "setting sheet", "prop-reference": "prop reference"}.get(kind, display_name(kind))
            return f"{base} {suffix}"

        def required_asset_status(asset: dict[str, object]) -> str:
            identifier = str(asset.get("id") or "")
            kind = str(asset.get("kind") or "")
            rel = str(asset.get("local_path") or "")
            try:
                path = safe_child(project, rel) if rel else project / "missing"
            except ProductionDataError:
                return "warning"
            if not path.is_file():
                return "missing"
            if kind == "character-sheet":
                character = identifier.removeprefix("character-")
                requirement = next((item for item in project_requirements if item.get("id") == f"character-sheet:{character}"), None)
                if requirement:
                    return str(requirement.get("status") or "ready for approval")
            return "approved" if is_approved(asset.get("status")) else "ready for approval"

        for shot in shots:
            required = [
                {"id": asset.get("id"), "kind": asset.get("kind"), "status": required_asset_status(asset), "path": asset.get("local_path")}
                for asset in registry_assets
                if any(str(number) in {str(shot["displayNumber"]), *shot["legacyNumbers"]} for number in asset.get("shots", []))
            ]
            shot["requiredAssets"] = required
            shot["requirements"] = [
                {"id": "timing", "label": "Shot timing", "scope": "shot", "status": "approved" if shot.get("durationSeconds") is not None else "missing", "evidence": [registry_source], "expectedPath": "05-storyboard/shots.json"},
                {"id": "image-prompt", "label": "Image direction", "scope": "shot", "status": "ready for approval" if shot["imageDirection"].get("visualDescription") else "missing", "evidence": ["04-images/shot-specs.json"] if shot["imageDirection"].get("visualDescription") else [], "expectedPath": "04-images/shot-specs.json"},
                *[{"id": str(asset["id"]), "label": required_asset_label(asset), "scope": "shot", "status": "approved" if is_approved(asset.get("status")) else "missing" if str(asset.get("status")) == "missing" else "incomplete", "evidence": [str(asset.get("path") or "")], "expectedPath": asset.get("path")} for asset in required],
            ]
            moodboard_record = assets_manifest.get("moodboard") if isinstance(assets_manifest.get("moodboard"), dict) else {}
            style_references = [reference_descriptor(moodboard_record, reference_type="moodboard", strength=moodboard_record.get("strength"))] if moodboard_record else []
            composition_base = next((item for item in shot.get("assetHistory", []) if item.get("selectionState") == "composition-base"), None)
            likeness_references: list[dict[str, object]] = []
            if composition_base:
                likeness_references.append({
                    "id": composition_base["assetId"], "assetId": composition_base["assetId"], "type": "composition-base",
                    "name": f"Composition base v{composition_base.get('version')}", "status": composition_base.get("reviewState"),
                    "path": composition_base.get("path"), "mediaUrl": composition_base.get("mediaUrl"), "thumbnailUrl": composition_base.get("thumbnailUrl"),
                })
            likeness_references.extend(reference_descriptor(item) for item in required if item.get("kind") in {"character-sheet", "prop-reference"})
            likeness_blockers = [item["name"] for item in likeness_references if item.get("type") != "composition-base" and not is_approved(item.get("status"))]
            if not composition_base:
                likeness_blockers.insert(0, "approved composition base")
            shot["generationStages"] = {
                "style-composition": {
                    "label": "Style + composition", "model": style_settings.get("model") or assets_manifest.get("default_model"),
                    "aspectRatio": style_settings.get("aspect_ratio") or assets_manifest.get("master_aspect_ratio"),
                    "resolution": style_settings.get("resolution"), "references": style_references,
                    "status": "ready" if str((assets_manifest.get("cost_approvals") or {}).get("style_composition_v4" if vision_events else "style_composition", {}).get("status") or "").casefold() == "approved" else "cost approval required",
                },
                "likeness": {
                    "label": "Likeness", "model": likeness_settings.get("model"),
                    "aspectRatio": likeness_settings.get("aspect_ratio") or assets_manifest.get("master_aspect_ratio"),
                    "resolution": likeness_settings.get("resolution"), "references": likeness_references,
                    "status": "blocked" if likeness_blockers else "ready", "blockers": likeness_blockers,
                },
            }
            prompt_asset = next((item for item in shot.get("assetHistory", []) if item.get("kind") == "image" and item.get("stage") in {"style-composition", "likeness"}), None)
            prompt_stage = str(prompt_asset.get("stage") if prompt_asset else "style-composition")
            compiled_entry = next(
                (
                    entry
                    for batch in prompt_batches
                    for entry in batch.get("shots", [])
                    if isinstance(entry, dict) and str(entry.get("shot_id") or "") == str(shot["shotId"])
                ),
                None,
            )
            shot["promptCompilation"] = {
                **(dict(compiled_entry) if isinstance(compiled_entry, dict) else {}),
                "batchId": next(
                    (
                        batch.get("batch_id")
                        for batch in prompt_batches
                        if any(isinstance(entry, dict) and str(entry.get("shot_id") or "") == str(shot["shotId"]) for entry in batch.get("shots", []))
                    ),
                    None,
                ),
            }
            matching_edits = [
                event for event in prompt_edits
                if str(event.get("workflow_stage") or "") == prompt_stage
                and (str(event.get("shot_id") or "") == str(shot["shotId"]) or str(event.get("shot") or "") in {str(shot["displayNumber"]), *shot["legacyNumbers"]})
            ]
            latest_edit = max(matching_edits, key=lambda event: str(event.get("created_at") or ""), default=None)
            configured_stage = shot["generationStages"].get(prompt_stage, shot["generationStages"]["style-composition"])
            prompt_text = str(
                (compiled_entry or {}).get("prompt")
                or (latest_edit or {}).get("prompt")
                or (prompt_asset or {}).get("prompt")
                or shot["imageDirection"].get("visualDescription")
                or ""
            )
            shot["currentPrompt"] = {
                "prompt": prompt_text,
                "usedPrompt": str((prompt_asset or {}).get("prompt") or ""),
                "stage": prompt_stage,
                "stageLabel": configured_stage.get("label"),
                "model": configured_stage.get("model") or (prompt_asset or {}).get("model"),
                "assetId": (prompt_asset or {}).get("assetId"),
                "assetVersion": (prompt_asset or {}).get("version"),
                "references": (prompt_asset or {}).get("references") or configured_stage.get("references") or [],
                "source": "compiled Shot Vision" if compiled_entry and compiled_entry.get("prompt") else "edited draft" if latest_edit else "latest generation" if prompt_asset and prompt_asset.get("prompt") else "image direction",
                "promptBatchId": shot.get("promptCompilation", {}).get("batchId"),
                "visionRevision": (compiled_entry or {}).get("vision_revision"),
                "promptSha256": (compiled_entry or {}).get("prompt_sha256"),
                "editedAt": (latest_edit or {}).get("created_at"),
            }
            missing_dependencies = [req for req in shot["requirements"] if req["status"] == "missing"]
            approval_dependencies = [req for req in shot["requirements"] if req["status"] in {"incomplete", "ready for approval", "warning"}]
            shot["missingDependencies"] = missing_dependencies
            shot["approvalDependencies"] = approval_dependencies
            if missing_dependencies:
                names = ", ".join(str(item["label"]) for item in missing_dependencies[:2])
                remainder = len(missing_dependencies) - 2
                shot["badges"].append(f"{len(missing_dependencies)} missing: {names}{f' +{remainder}' if remainder else ''}")
            if approval_dependencies:
                names = ", ".join(str(item["label"]) for item in approval_dependencies[:2])
                remainder = len(approval_dependencies) - 2
                shot["badges"].append(f"{len(approval_dependencies)} need approval: {names}{f' +{remainder}' if remainder else ''}")
            owner_id = str(shot.get("sharedSetupOwnerShotId") or shot["shotId"])
            shot_jobs = [item for item in jobs if str(item.get("shotId") or item.get("ownerShotId") or "") in {str(shot["shotId"]), owner_id}]
            shot["generationJob"] = max(shot_jobs, key=lambda item: str(item.get("createdAt") or ""), default=None)

        pending_count = sum(1 for asset in assets if not is_approved(asset.get("reviewState")) and asset.get("stage") != "storyboard")
        gate_approved = sum(1 for gate in gates if gate["state"] in {"approved", "done"})
        structure_blocker = ""
        if registry_source != "shots.json":
            structure_blocker = "Build a stable shots.json registry before editing shot structure."
        elif registry_payload.get("status") != "ready":
            structure_blocker = "Resolve shot identity findings before editing shot structure."
        elif newer_source:
            structure_blocker = "A newer shot-list workbook must be reconciled first."
        elif any(shot.get("inferred") or shot.get("reconciliationStatus") not in {"stable", "new"} for shot in shots):
            structure_blocker = "Every shot needs a stable Shot ID before editing shot structure."
        structure_editable = not structure_blocker

        next_gate = next((gate for gate in gates if gate["state"] not in {"approved", "done", "n/a"}), None)
        missing_now = [item for item in project_requirements if item["urgency"] == "now" and item["status"] in {"missing", "incomplete", "warning"}]
        missing_later = [item for item in project_requirements if item["urgency"] == "later" and item["status"] in {"missing", "incomplete", "upcoming", "warning"}]
        runtime = sum(float(shot.get("durationSeconds") or 0) for shot in shots)
        unique_setups = len({shot["sharedSetupOwnerShotId"] or shot["shotId"] for shot in shots if shot["imageDirection"].get("renderMode") != "source-photo"})
        activity_paths = [path for path in project.rglob("*") if path.is_file()]
        last_activity = max((iso_mtime(path) for path in activity_paths), default="")
        cover = next((shot.get("newerPendingAsset") or shot.get("heroAsset") for shot in shots if shot.get("newerPendingAsset") or shot.get("heroAsset")), None)
        return {
            "slug": slug, "name": display_name(slug), "format": distribution.get("format") or "Unspecified", "client": distribution.get("client") or "none", "chargedRegister": distribution.get("chargedRegister") or "",
            "runtimeSeconds": round(runtime, 3), "shotCount": len(shots), "uniqueIllustratedSetups": unique_setups,
            "registrySource": registry_source, "registryStatus": registry_payload.get("status") or ("inferred" if registry_source != "shots.json" else "ready"),
            "gateProgress": {"approved": gate_approved, "total": len(gates)}, "gates": gates,
            "nextAction": {"label": f"Resolve {missing_now[0]['label']}" if missing_now else f"Review {next_gate['label']}" if next_gate else "All declared gates are complete", "stage": missing_now[0].get("stageDependency") if missing_now else next_gate.get("id") if next_gate else None},
            "registryRevisionId": registry_payload.get("registry_revision_id"),
            "shotListDocument": shot_list_document,
            "structureEditable": structure_editable, "structureBlocker": structure_blocker,
            "retiredShots": retired_shots, "retiredShotCount": len(retired_shots),
            "blockerCount": blocker_count, "pendingReviewCount": pending_count, "lastActivity": last_activity,
            "coverAsset": cover, "requirements": project_requirements, "missingNow": missing_now, "missingLater": missing_later,
            "shots": shots, "unmappedAssets": unmapped, "validationFindings": findings, "validationCount": len(findings),
            "promptBatches": prompt_batches, "latestPromptBatch": latest_prompt_batch,
        }

    def get_shot(self, slug: str, shot_id: str) -> dict[str, object]:
        production = self.get_production(slug)
        shots = production["shots"]
        for index, shot in enumerate(shots):
            if shot["shotId"] == shot_id:
                return {
                    "production": {
                        key: production[key]
                        for key in [
                            "slug", "name", "format", "runtimeSeconds", "gateProgress",
                            "structureEditable", "structureBlocker", "registryRevisionId",
                        ]
                    },
                    "shot": shot,
                    "previousShotId": shots[index - 1]["shotId"] if index else None,
                    "nextShotId": shots[index + 1]["shotId"] if index + 1 < len(shots) else None,
                    "validationFindings": [
                        item for item in production["validationFindings"]
                        if item.get("shotId") in {None, shot_id}
                    ],
                }
        raise FileNotFoundError(shot_id)

    def _registered_media(self, slug: str) -> dict[str, Path]:
        project = self._project(slug)
        production = self.get_production(slug)
        registry: dict[str, Path] = {}
        for shot in production["shots"]:
            for asset in shot.get("assetHistory", []):
                try:
                    registry[str(asset["assetId"])] = safe_child(project, str(asset["path"]), must_exist=True)
                except (ProductionDataError, FileNotFoundError):
                    continue
            for generation_stage in shot.get("generationStages", {}).values():
                for reference in generation_stage.get("references", []):
                    if not reference.get("assetId") or not reference.get("path"):
                        continue
                    try:
                        registry[str(reference["assetId"])] = safe_child(project, str(reference["path"]), must_exist=True)
                    except (ProductionDataError, FileNotFoundError):
                        continue
        return registry

    def resolve_media(self, slug: str, asset_id: str, *, preview: bool = False, poster: bool = False) -> MediaTarget:
        source = self._registered_media(slug).get(asset_id)
        if source is None:
            raise FileNotFoundError(asset_id)
        if preview and source.suffix.casefold() in {".heic", ".heif"}:
            target = self.cache_dir / "previews" / slug / f"{stable_id(asset_id, source.stat().st_mtime_ns)}.jpg"
            if not target.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                converted = False
                try:
                    from PIL import Image
                    with Image.open(source) as image:
                        image.convert("RGB").thumbnail((1600, 1600))
                        image.convert("RGB").save(target, "JPEG", quality=88)
                    converted = True
                except Exception:
                    magick = shutil.which("magick")
                    if magick:
                        converted = subprocess.run([magick, str(source), "-auto-orient", "-resize", "1600x1600>", str(target)], capture_output=True, check=False).returncode == 0
                    if not converted:
                        powershell = shutil.which("powershell") or shutil.which("powershell.exe")
                        if powershell:
                            script = (
                                "Add-Type -AssemblyName PresentationCore; "
                                "$input=[IO.File]::OpenRead($env:HEARTHLIGHT_HEIC_SOURCE); "
                                "try {$decoder=[Windows.Media.Imaging.BitmapDecoder]::Create($input,"
                                "[Windows.Media.Imaging.BitmapCreateOptions]::PreservePixelFormat,"
                                "[Windows.Media.Imaging.BitmapCacheOption]::OnLoad); "
                                "$encoder=New-Object Windows.Media.Imaging.JpegBitmapEncoder; "
                                "$encoder.QualityLevel=88; $encoder.Frames.Add($decoder.Frames[0]); "
                                "$output=[IO.File]::Create($env:HEARTHLIGHT_HEIC_TARGET); "
                                "try {$encoder.Save($output)} finally {$output.Dispose()}} "
                                "finally {$input.Dispose()}"
                            )
                            environment = os.environ.copy()
                            environment["HEARTHLIGHT_HEIC_SOURCE"] = str(source)
                            environment["HEARTHLIGHT_HEIC_TARGET"] = str(target)
                            converted = subprocess.run(
                                [powershell, "-NoProfile", "-NonInteractive", "-Command", script],
                                capture_output=True,
                                check=False,
                                env=environment,
                            ).returncode == 0
                    if not converted:
                        ffmpeg = shutil.which("ffmpeg")
                        if ffmpeg:
                            converted = subprocess.run([ffmpeg, "-y", "-i", str(source), "-frames:v", "1", "-vf", "scale='min(1600,iw)':-2", str(target)], capture_output=True, check=False).returncode == 0
                if not converted or not target.is_file():
                    raise ProductionDataError("HEIC preview conversion is unavailable")
            return MediaTarget(target, "image/jpeg", True)
        if poster and source.suffix.casefold() in VIDEO_SUFFIXES:
            target = self.cache_dir / "posters" / slug / f"{stable_id(asset_id, source.stat().st_mtime_ns)}.jpg"
            if not target.is_file():
                ffmpeg = shutil.which("ffmpeg")
                if not ffmpeg:
                    raise ProductionDataError("Video poster extraction is unavailable")
                target.parent.mkdir(parents=True, exist_ok=True)
                result = subprocess.run([ffmpeg, "-y", "-ss", "0.05", "-i", str(source), "-frames:v", "1", "-vf", "scale='min(1280,iw)':-2", str(target)], capture_output=True, check=False)
                if result.returncode or not target.is_file():
                    raise ProductionDataError("Could not extract video poster")
            return MediaTarget(target, "image/jpeg", True)
        return MediaTarget(source, mimetypes.guess_type(source.name)[0] or "application/octet-stream")
