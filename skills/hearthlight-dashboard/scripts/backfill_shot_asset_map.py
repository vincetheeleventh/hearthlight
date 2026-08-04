#!/usr/bin/env python3
"""Build explicit legacy-event-to-shot mappings without rewriting history."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import uuid
from pathlib import Path


SCRIPT = Path(__file__).resolve()
STUDIO_ROOT = SCRIPT.parents[3]
INVALID_VALUES = {"", "-", "?", "none", "null", "n/a", "new"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def normalized(value: object) -> str:
    return str(value or "").strip().casefold()


def append_lookup(table: dict[str, list[str]], key: object, shot_id: str) -> None:
    value = normalized(key)
    if value not in INVALID_VALUES:
        table.setdefault(value, []).append(shot_id)


def read_jsonl(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    if not path.is_file():
        return records
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Malformed JSONL: {path}:{number}: {exc}") from exc
        if isinstance(value, dict):
            records.append(value)
    return records


def build_map(project: Path, confirmed_directories: list[tuple[str, str]] | None = None) -> dict[str, object]:
    registry_path = project / "05-storyboard" / "shots.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("status") != "ready":
        raise SystemExit("Shot registry must be ready before legacy assets can be mapped.")
    shots = [item for item in registry.get("shots", []) if isinstance(item, dict)]
    by_id = {str(item.get("shot_id")): item for item in shots if item.get("shot_id")}
    by_display: dict[str, list[str]] = {}
    by_legacy: dict[str, list[str]] = {}
    by_revision: dict[str, dict[str, list[str]]] = {}
    for shot in shots:
        shot_id = str(shot["shot_id"])
        append_lookup(by_display, shot.get("display_number"), shot_id)
        for legacy in shot.get("legacy_numbers", []):
            append_lookup(by_legacy, legacy, shot_id)
        for label in shot.get("legacy_labels", []):
            if isinstance(label, dict) and normalized(label.get("revision")):
                table = by_revision.setdefault(normalized(label.get("revision")), {})
                append_lookup(table, label.get("label"), shot_id)

    entries: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []
    ledger_paths = [project / "04-images" / "generations.jsonl", project / "06-video" / "ledger.jsonl"]
    for ledger in ledger_paths:
        for event in read_jsonl(ledger):
            event_id = str(event.get("event_id") or "").strip()
            asset_path = str(event.get("asset_path") or event.get("path") or "").strip()
            if not event_id and not asset_path:
                continue
            explicit = str(event.get("shot_id") or "").strip()
            candidates: list[str] = []
            mapped_by = ""
            if explicit and explicit in by_id:
                candidates = [explicit]
                mapped_by = "shot-id"
            if not candidates:
                legacy = normalized(event.get("legacy_shot_v3"))
                if legacy not in INVALID_VALUES:
                    lookup = by_revision.get("v3", by_legacy)
                    candidates = list(dict.fromkeys(lookup.get(legacy, [])))
                    mapped_by = "revision-label-v3" if "v3" in by_revision else "legacy-shot-v3"
            if not candidates:
                display = normalized(event.get("shot") or event.get("generation_owner"))
                if display not in INVALID_VALUES:
                    candidates = list(dict.fromkeys(by_display.get(display, [])))
                    mapped_by = "display-number"
            if len(candidates) != 1:
                unresolved.append({
                    "event_id": event_id or None,
                    "asset_path": asset_path or None,
                    "shot": event.get("shot"),
                    "legacy_shot_v3": event.get("legacy_shot_v3"),
                    "candidate_shot_ids": candidates,
                })
                continue
            entries.append({
                "mapping_id": str(uuid.uuid4()),
                "event_id": event_id or None,
                "asset_id": event.get("asset_id") or event_id or None,
                "asset_path": asset_path or None,
                "shot_id": candidates[0],
                "mapped_by": mapped_by,
                "source_shot_label": event.get("shot"),
            })

    confirmed_directories = confirmed_directories or []
    mapped_paths = {str(item.get("asset_path") or "") for item in entries}
    for identity_space, relative_directory in confirmed_directories:
        directory = (project / relative_directory).resolve()
        if project.resolve() not in directory.parents or not directory.is_dir():
            raise SystemExit(f"Confirmed mapping directory is missing or outside the project: {relative_directory}")
        lookup = by_legacy if identity_space == "legacy" else by_display
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif", ".mp4", ".mov", ".webm"}:
                continue
            match = re.search(r"shot[-_ ]*0*(\d+[A-Za-z]?)", path.stem, re.I)
            if not match:
                continue
            label = normalized(match.group(1))
            candidates = list(dict.fromkeys(lookup.get(label, [])))
            rel = path.relative_to(project).as_posix()
            if rel in mapped_paths:
                continue
            if len(candidates) != 1:
                unresolved.append({
                    "asset_path": rel,
                    "source_shot_label": match.group(1),
                    "identity_space": identity_space,
                    "candidate_shot_ids": candidates,
                })
                continue
            entries.append({
                "mapping_id": str(uuid.uuid4()),
                "event_id": None,
                "asset_id": None,
                "asset_path": rel,
                "shot_id": candidates[0],
                "mapped_by": f"confirmed-{identity_space}-directory",
                "source_shot_label": match.group(1),
            })
            mapped_paths.add(rel)

    return {
        "schema_version": 1,
        "project": project.name,
        "generated_at": utc_now(),
        "registry_revision_id": registry.get("registry_revision_id"),
        "source_revision_hash": registry.get("source_revision_hash"),
        "status": "needs_reconciliation" if unresolved else "ready",
        "entries": entries,
        "unresolved": unresolved,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Map legacy generation events to immutable Hearthlight shot IDs.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--write-unresolved", action="store_true")
    parser.add_argument("--map-current-display-directory", action="append", default=[], metavar="PROJECT_RELATIVE_PATH")
    parser.add_argument("--map-legacy-directory", action="append", default=[], metavar="PROJECT_RELATIVE_PATH")
    args = parser.parse_args()
    projects_root = (STUDIO_ROOT / "projects").resolve()
    project = (projects_root / args.project).resolve()
    if projects_root not in project.parents or not project.is_dir():
        raise SystemExit(f"Project not found: {args.project}")
    confirmed_directories = [
        *(("display", path) for path in args.map_current_display_directory),
        *(("legacy", path) for path in args.map_legacy_directory),
    ]
    payload = build_map(project, confirmed_directories)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if not args.apply:
        print(rendered, end="")
        return 0
    if payload["status"] != "ready" and not args.write_unresolved:
        raise SystemExit("Asset map needs reconciliation. Nothing written.")
    output = project / "05-storyboard" / "asset-shot-map.json"
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)
    print(f"Wrote {output} ({len(payload['entries'])} mappings, {payload['status']}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
