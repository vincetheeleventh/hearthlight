#!/usr/bin/env python3
"""Build Hearthlight's stable cross-stage shot registry.

The command is explicit by design. Reading a project never creates or rewrites
``05-storyboard/shots.json``. Re-running this command preserves established shot
IDs where a match is unambiguous and records reconciliation findings otherwise.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT = Path(__file__).resolve()
STUDIO_ROOT = SCRIPT.parents[3]
SHOT_NAMESPACE = uuid.UUID("d3116098-393b-46fd-98e3-e6626282fb55")
INVALID_LEGACY_VALUES = {"", "-", "?", "none", "null", "n/a", "new"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()

def valid_legacy(value: object) -> str | None:
    text = str(value or "").strip()
    return None if text.casefold() in INVALID_LEGACY_VALUES else text



def xlsx_rows(path: Path, sheet_name: str) -> list[list[object]]:
    """Read a worksheet using the standard library only."""
    ns = {
        "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "p": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    with zipfile.ZipFile(path) as book:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in book.namelist():
            tree = ET.fromstring(book.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.findall(".//m:t", ns))
                for item in tree.findall("m:si", ns)
            ]

        workbook = ET.fromstring(book.read("xl/workbook.xml"))
        rel_id = next(
            (
                sheet.attrib.get(f"{{{ns['r']}}}id")
                for sheet in workbook.findall("m:sheets/m:sheet", ns)
                if sheet.attrib.get("name") == sheet_name
            ),
            None,
        )
        if not rel_id:
            raise ValueError(f"Worksheet not found: {sheet_name}")
        rels = ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        target = next(
            (
                rel.attrib.get("Target")
                for rel in rels.findall("p:Relationship", ns)
                if rel.attrib.get("Id") == rel_id
            ),
            None,
        )
        if not target:
            raise ValueError(f"Worksheet relationship missing: {sheet_name}")
        sheet_path = "xl/" + str(target).lstrip("/").removeprefix("xl/")
        sheet = ET.fromstring(book.read(sheet_path))

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
                raw = value_node.text or ""
                try:
                    number = float(raw)
                    value = int(number) if number.is_integer() else number
                except ValueError:
                    value = raw
            values[(row, col)] = value
            max_row, max_col = max(max_row, row), max(max_col, col)
        return [
            [values.get((row, col)) for col in range(1, max_col + 1)]
            for row in range(1, max_row + 1)
        ]


def split_panels(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text or text in {"-", "—", "None"}:
        return []
    return [part.strip() for part in re.split(r"[,;]", text) if part.strip()]


def read_xlsx_shots(source: Path) -> list[dict[str, object]]:
    rows = xlsx_rows(source, "Shot List")
    if not rows:
        return []
    headers = [str(value or "").strip() for value in rows[0]]
    records: list[dict[str, object]] = []
    for order, row in enumerate(rows[1:], start=1):
        source_row = {
            headers[index]: row[index] if index < len(row) else None
            for index in range(len(headers))
        }
        if source_row.get("Shot") in (None, ""):
            continue
        display = source_row["Shot"]
        legacy = valid_legacy(source_row.get("Legacy ID"))
        if legacy is None and source_row.get("Legacy ID") in (None, ""):
            legacy = valid_legacy(display)
        visual = source_row.get("Visual Description")
        if visual in (None, ""):
            visual = source_row.get("Still (frame one)")
        action = source_row.get("Action Description")
        if action in (None, ""):
            action = source_row.get("Action (motion — video only)")
        records.append(
            {
                "display_number": display,
                "order": order,
                "legacy_numbers": [legacy] if legacy else [],
                "title": str(source_row.get("Shot Title") or f"Shot {display}").strip(),
                "start": str(source_row.get("Start") or "").strip(),
                "end": str(source_row.get("End") or "").strip(),
                "duration_seconds": source_row.get("Duration (s)"),
                "board_panels": split_panels(source_row.get("Board Panel")),
                "storyboard_reference": str(source_row.get("Storyboard") or "").strip(),
                "text": {
                    "visual_description": str(visual or "").strip(),
                    "action_description": str(action or "").strip(),
                    "dialogue": str(source_row.get("Dialogue") or "").strip(),
                    "audio": str(source_row.get("Audio") or "").strip(),
                    "camera_movement": str(source_row.get("Camera Movement") or "").strip(),
                    "notes": str(source_row.get("Notes") or "").strip(),
                },
            }
        )
        explicit_id = str(source_row.get("Shot ID") or "").strip()
        if explicit_id:
            records[-1]["shot_id"] = explicit_id
        still = str(source_row.get("Still (frame one)") or "").strip()
        if still:
            records[-1]["image_direction"] = {
                "visual_description": still,
                "action_description": "",
                "camera_movement": str(source_row.get("Camera Movement") or "").strip(),
                "continuity_note": str(source_row.get("Notes") or "").strip(),
                "render_mode": "",
                "source_asset": None,
            }
    return records


def merge_image_direction(project_root: Path, shots: list[dict[str, object]]) -> list[dict[str, object]]:
    """Merge older image specs through stable/legacy identity, never display order."""
    path = project_root / "04-images" / "shot-specs.json"
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    specs = [item for item in payload.get("shots", []) if isinstance(item, dict)]
    by_id = {str(item.get("shot_id")): item for item in specs if item.get("shot_id")}
    by_legacy: dict[str, list[dict[str, object]]] = {}
    by_source_number = {str(item.get("shot")): item for item in specs if item.get("shot") not in (None, "")}
    for spec in specs:
        legacy = valid_legacy(spec.get("legacy_id"))
        if legacy:
            by_legacy.setdefault(normalized(legacy), []).append(spec)
    findings: list[dict[str, object]] = []
    for shot in shots:
        spec = by_id.get(str(shot.get("shot_id") or ""))
        if not spec:
            for legacy in shot.get("legacy_numbers", []):
                candidates = by_legacy.get(normalized(legacy), [])
                if len(candidates) == 1:
                    spec = candidates[0]
                    break
                if len(candidates) > 1:
                    findings.append({
                        "code": "ambiguous-image-direction-match",
                        "status": "needs_reconciliation",
                        "display_number": shot.get("display_number"),
                        "shot_id": shot.get("shot_id"),
                        "legacy_number": legacy,
                        "candidate_legacy_ids": sorted(
                            str(item.get("shot_id") or item.get("legacy_id") or item.get("shot"))
                            for item in candidates
                        ),
                    })
                    break
        if not spec:
            continue
        spec_direction = {
            "visual_description": str(spec.get("image_visual_description") or "").strip(),
            "action_description": str(spec.get("image_action_description") or "").strip(),
            "camera_movement": str(spec.get("image_camera_movement") or "").strip(),
            "continuity_note": str(spec.get("image_pass_note") or "").strip(),
            "render_mode": str(spec.get("render_mode") or "").strip(),
            "source_asset": spec.get("source_asset"),
        }
        merged_direction = dict(shot.get("image_direction") or {})
        for key, value in spec_direction.items():
            if merged_direction.get(key) in (None, ""):
                merged_direction[key] = value
        shot["image_direction"] = merged_direction
        owner = spec.get("generation_owner")
        if owner not in (None, "", spec.get("shot")):
            owner_spec = by_source_number.get(str(owner))
            owner_legacy = valid_legacy((owner_spec or {}).get("legacy_id"))
            if owner_legacy:
                shot["shared_setup_owner_legacy"] = owner_legacy
            elif (owner_spec or {}).get("shot_id"):
                shot["shared_setup_owner_shot_id"] = owner_spec["shot_id"]
            else:
                findings.append({
                    "code": "missing-shared-setup-owner",
                    "status": "needs_reconciliation",
                    "shot_id": shot.get("shot_id"),
                    "owner_source_number": owner,
                })
    return findings




def record_revision_label(shot: dict[str, object], label: object, source_name: str) -> None:
    valid = valid_legacy(label)
    if valid is None:
        return
    match = re.search(r"(?:^|[-_])v(\d+)(?:\.|[-_]|$)", Path(source_name).name, re.I)
    revision = f"v{match.group(1)}" if match else None
    labels = [item for item in shot.get("legacy_labels", []) if isinstance(item, dict)]
    identity = (normalized(valid), normalized(source_name))
    if identity not in {
        (normalized(item.get("label")), normalized(item.get("source")))
        for item in labels
    }:
        labels.append({"label": valid, "source": source_name, "revision": revision})
    shot["legacy_labels"] = labels


def carry_legacy_labels(shot: dict[str, object], previous: dict[str, object]) -> None:
    """Keep every prior human label while the immutable ID stays unchanged."""
    values = list(shot.get("legacy_numbers", []))
    candidates = [*previous.get("legacy_numbers", [])]
    if normalized(previous.get("display_number")) != normalized(shot.get("display_number")):
        candidates.append(previous.get("display_number"))
    seen = {normalized(value) for value in values}
    for candidate in candidates:
        valid = valid_legacy(candidate)
        key = normalized(valid)
        if valid is not None and key not in seen:
            values.append(valid)
            seen.add(key)
    shot["legacy_numbers"] = values
    labels = [item for item in shot.get("legacy_labels", []) if isinstance(item, dict)]
    known = {
        (normalized(item.get("label")), normalized(item.get("source")))
        for item in labels
    }
    for item in previous.get("legacy_labels", []):
        if not isinstance(item, dict):
            continue
        identity = (normalized(item.get("label")), normalized(item.get("source")))
        if identity not in known:
            labels.append(dict(item))
            known.add(identity)
    if labels:
        shot["legacy_labels"] = labels


def merge_legacy_source_labels(
    shots: list[dict[str, object]],
    previous_shots: list[dict[str, object]],
    source_name: str,
) -> list[dict[str, object]]:
    """Import historical display labels from a declared older revision."""
    current_by_title: dict[str, list[dict[str, object]]] = {}
    for shot in shots:
        current_by_title.setdefault(normalized(shot.get("title")), []).append(shot)
    findings: list[dict[str, object]] = []
    for previous in previous_shots:
        title = normalized(previous.get("title"))
        candidates = current_by_title.get(title, []) if title else []
        if len(candidates) == 1:
            carry_legacy_labels(candidates[0], previous)
            record_revision_label(candidates[0], previous.get("display_number"), source_name)
        elif candidates:
            findings.append({
                "code": "ambiguous-legacy-source-label",
                "status": "needs_reconciliation",
                "source": source_name,
                "title": previous.get("title"),
                "candidate_shot_ids": [item.get("shot_id") for item in candidates],
            })
    return findings
def _candidate_keys(shot: dict[str, object]) -> tuple[str, str]:
    title = normalized(shot.get("title"))
    panels = "|".join(normalized(item) for item in shot.get("board_panels", []) if item)
    return title, f"{title}|{panels}" if title else ""


def reconcile_shots(
    project_slug: str,
    incoming: list[dict[str, object]],
    existing: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    """Preserve IDs only where identity is unambiguous.

    Unique title/panel identity wins over display numbering, so reorder and
    insertion do not churn IDs. Conflicting candidates are made explicit.
    """
    title_map: dict[str, list[dict[str, object]]] = {}
    identity_map: dict[str, list[dict[str, object]]] = {}
    legacy_map: dict[str, list[dict[str, object]]] = {}
    for old in existing:
        title, identity = _candidate_keys(old)
        if title:
            title_map.setdefault(title, []).append(old)
        if identity:
            identity_map.setdefault(identity, []).append(old)
        for legacy in old.get("legacy_numbers", []):
            legacy_map.setdefault(normalized(legacy), []).append(old)

    used: set[str] = set()
    findings: list[dict[str, object]] = []
    result: list[dict[str, object]] = []
    for item in incoming:
        shot = dict(item)
        explicit_id = str(shot.get("shot_id") or "").strip()
        if explicit_id:
            if explicit_id in used:
                seed = f"duplicate|{project_slug}|{explicit_id}|{shot.get('order')}"
                shot["shot_id"] = f"unresolved-{uuid.uuid5(SHOT_NAMESPACE, seed)}"
                shot["id_state"] = "needs_reconciliation"
                findings.append({
                    "code": "duplicate-shot-id",
                    "status": "needs_reconciliation",
                    "display_number": shot.get("display_number"),
                    "shot_id": explicit_id,
                })
            else:
                previous = next((old for old in existing if str(old.get("shot_id")) == explicit_id), None)
                shot["shot_id"] = explicit_id
                shot["id_state"] = "stable" if previous else "new"
                shot["matched_by"] = "explicit-shot-id"
                if previous:
                    carry_legacy_labels(shot, previous)
                used.add(explicit_id)
            result.append(shot)
            continue
        title, identity = _candidate_keys(shot)
        candidates: dict[str, tuple[dict[str, object], str]] = {}
        for old in identity_map.get(identity, []) if identity else []:
            candidates[str(old.get("shot_id"))] = (old, "title-and-board")
        if not candidates and title:
            for old in title_map.get(title, []):
                candidates[str(old.get("shot_id"))] = (old, "unique-title")
        if not candidates:
            for legacy in shot.get("legacy_numbers", []):
                for old in legacy_map.get(normalized(legacy), []):
                    old_title = normalized(old.get("title"))
                    if not old_title or not title or old_title == title:
                        candidates[str(old.get("shot_id"))] = (old, "legacy-number")
        candidates = {key: value for key, value in candidates.items() if key and key not in used}
        if len(candidates) == 1:
            shot_id, (previous, matched_by) = next(iter(candidates.items()))
            shot["shot_id"] = shot_id
            shot["id_state"] = "stable"
            shot["matched_by"] = matched_by
            carry_legacy_labels(shot, previous)
            used.add(shot_id)
        elif not candidates:
            seed = "|".join(
                [project_slug, title, str(shot.get("display_number")), *(str(x) for x in shot.get("legacy_numbers", []))]
            )
            shot["shot_id"] = str(uuid.uuid5(SHOT_NAMESPACE, seed))
            shot["id_state"] = "stable" if not existing else "new"
            used.add(str(shot["shot_id"]))
        else:
            seed = f"unresolved|{project_slug}|{shot.get('order')}|{title}"
            shot["shot_id"] = f"unresolved-{uuid.uuid5(SHOT_NAMESPACE, seed)}"
            shot["id_state"] = "needs_reconciliation"
            findings.append(
                {
                    "code": "ambiguous-shot-match",
                    "status": "needs_reconciliation",
                    "display_number": shot.get("display_number"),
                    "title": shot.get("title"),
                    "candidate_shot_ids": sorted(candidates),
                }
            )
        result.append(shot)

    retired = [
        str(old.get("shot_id"))
        for old in existing
        if old.get("shot_id") and str(old.get("shot_id")) not in used
    ]
    return result, findings, retired


def current_registry_source(project_root: Path) -> Path | None:
    registry = project_root / "05-storyboard" / "shots.json"
    if not registry.is_file():
        return None
    try:
        source = json.loads(registry.read_text(encoding="utf-8")).get("source")
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(source, str) or not source.lower().endswith(".xlsx"):
        return None
    candidate = (project_root / source).resolve()
    return candidate if candidate.is_file() and project_root.resolve() in candidate.parents else None


def apply_registry_overrides(
    project_root: Path,
    shots: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Apply explicit stable-ID relationships that a source format cannot carry."""
    path = project_root / "05-storyboard" / "shot-registry-overrides.json"
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [{
            "code": "invalid-shot-registry-overrides",
            "status": "needs_reconciliation",
            "detail": str(exc),
        }]
    entries = payload.get("shots", payload.get("overrides", []))
    if not isinstance(entries, list):
        return [{
            "code": "invalid-shot-registry-overrides",
            "status": "needs_reconciliation",
            "detail": "Expected a shots or overrides array.",
        }]
    by_id = {str(item.get("shot_id")): item for item in shots if item.get("shot_id")}
    findings: list[dict[str, object]] = []
    for override in entries:
        if not isinstance(override, dict):
            continue
        shot_id = str(override.get("shot_id") or "")
        owner_id = str(override.get("shared_setup_owner_shot_id") or "")
        if shot_id not in by_id or (owner_id and owner_id not in by_id) or shot_id == owner_id:
            findings.append({
                "code": "invalid-shot-registry-override",
                "status": "needs_reconciliation",
                "shot_id": shot_id or None,
                "shared_setup_owner_shot_id": owner_id or None,
            })
            continue
        if "shared_setup_owner_shot_id" in override:
            by_id[shot_id]["shared_setup_owner_shot_id"] = owner_id or None
    return findings


def build_registry(
    project_root: Path,
    source: Path,
    existing_path: Path | None = None,
    *,
    accept_retirements: bool = False,
    legacy_sources: list[Path] | None = None,
) -> dict[str, object]:
    incoming = read_xlsx_shots(source)
    existing_payload: dict[str, object] = {}
    if existing_path and existing_path.is_file():
        existing_payload = json.loads(existing_path.read_text(encoding="utf-8"))
    existing_active = [item for item in existing_payload.get("shots", []) if isinstance(item, dict)]
    shots, findings, proposed_retired = reconcile_shots(project_root.name, incoming, existing_active)
    for legacy_source in legacy_sources or []:
        findings.extend(merge_legacy_source_labels(
            shots, read_xlsx_shots(legacy_source),
            legacy_source.resolve().relative_to(project_root.resolve()).as_posix(),
        ))
    findings.extend(merge_image_direction(project_root, shots))

    by_legacy: dict[str, list[str]] = {}
    for item in shots:
        for legacy in item.get("legacy_numbers", []):
            by_legacy.setdefault(normalized(legacy), []).append(str(item.get("shot_id")))
    for shot in shots:
        owner_legacy = shot.pop("shared_setup_owner_legacy", None)
        owner_candidates = by_legacy.get(normalized(owner_legacy), []) if owner_legacy else []
        shot.setdefault("shared_setup_owner_shot_id", owner_candidates[0] if len(owner_candidates) == 1 else None)
        if owner_legacy is not None and len(owner_candidates) != 1:
            findings.append({
                "code": "missing-shared-setup-owner",
                "status": "needs_reconciliation",
                "shot_id": shot["shot_id"],
                "owner_legacy_number": owner_legacy,
            })

    findings.extend(apply_registry_overrides(project_root, shots))
    existing_retired = [item for item in existing_payload.get("retired_shots", []) if isinstance(item, dict)]
    existing_by_id = {str(item.get("shot_id")): item for item in existing_active if item.get("shot_id")}
    retired_shots = list(existing_retired)
    if proposed_retired and accept_retirements:
        retired_at = utc_now()
        for shot_id in proposed_retired:
            snapshot = dict(existing_by_id.get(shot_id, {"shot_id": shot_id}))
            snapshot.update({"retired_at": retired_at, "retired_reason": "Removed from explicitly reconciled source"})
            retired_shots.append(snapshot)
    elif proposed_retired:
        for shot_id in proposed_retired:
            previous = existing_by_id.get(shot_id, {})
            findings.append({
                "code": "missing-source-shot",
                "status": "needs_reconciliation",
                "shot_id": shot_id,
                "display_number": previous.get("display_number"),
                "title": previous.get("title"),
                "detail": "Existing shot is absent from the new source. Retire it explicitly or restore it to the source.",
            })

    revision = sha256(source)
    return {
        "schema_version": 2,
        "project": project_root.name,
        "source": source.resolve().relative_to(project_root.resolve()).as_posix(),
        "source_revision_hash": revision,
        "source_sync_state": "source-aligned",
        "registry_revision": int(existing_payload.get("registry_revision") or 0) + 1,
        "registry_revision_id": str(uuid.uuid4()),
        "generated_at": utc_now(),
        "status": "needs_reconciliation" if findings else "ready",
        "shots": shots,
        "retired_shots": retired_shots,
        "retired_shot_ids": [str(item.get("shot_id")) for item in retired_shots if item.get("shot_id")],
        "proposed_retired_shot_ids": [] if accept_retirements else proposed_retired,
        "validation_findings": findings,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or refresh a Hearthlight shots.json registry.")
    parser.add_argument("--project", required=True, help="Project slug under Story Studio/projects")
    parser.add_argument("--source", help="Project-relative shot-list XLSX. Defaults to the current shots.json source.")
    parser.add_argument("--legacy-source", action="append", default=[], help="Older project-relative XLSX whose human labels must remain aliases.")
    parser.add_argument("--dry-run", action="store_true", help="Print the registry without writing it.")
    parser.add_argument("--accept-retirements", action="store_true", help="Explicitly retire existing shots absent from the new source.")
    parser.add_argument("--write-unresolved", action="store_true", help="Write a needs_reconciliation registry for manual repair.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    projects_root = (STUDIO_ROOT / "projects").resolve()
    project_root = (projects_root / args.project).resolve()
    if projects_root not in project_root.parents or not project_root.is_dir():
        raise SystemExit(f"Project not found: {args.project}")
    source = (project_root / args.source).resolve() if args.source else current_registry_source(project_root)
    if source is None:
        candidates = sorted((project_root / "05-storyboard").glob("*.xlsx"), key=lambda path: path.stat().st_mtime)
        source = candidates[-1].resolve() if candidates else None
    if source is None or not source.is_file() or project_root not in source.parents:
        raise SystemExit("A project-contained shot-list XLSX is required.")
    legacy_sources = [(project_root / item).resolve() for item in args.legacy_source]
    if any(
        not item.is_file() or project_root not in item.parents
        for item in legacy_sources
    ):
        raise SystemExit("Every legacy source must be a project-contained XLSX.")
    output = project_root / "05-storyboard" / "shots.json"
    payload = build_registry(project_root, source, output, accept_retirements=args.accept_retirements, legacy_sources=legacy_sources)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.dry_run:
        sys.stdout.write(rendered)
    else:
        if payload["status"] == "needs_reconciliation" and not args.write_unresolved:
            raise SystemExit("Registry needs reconciliation. Nothing written; inspect --dry-run or resolve the findings first.")
        temp = output.with_suffix(".json.tmp")
        temp.write_text(rendered, encoding="utf-8")
        temp.replace(output)
        print(f"Wrote {output} ({len(payload['shots'])} shots, {payload['status']}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
