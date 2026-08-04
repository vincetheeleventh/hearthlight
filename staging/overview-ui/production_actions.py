"""Canonical Hearthlight Studio write actions.

Creative history stays append-only. Shot deletion is reversible retirement;
generation records, media, gate state, and immutable Shot IDs are never erased.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Callable

from .productions import (
    ProductionAdapter,
    ProductionDataError,
    file_hash,
    is_approved,
    read_json,
    safe_child,
)


_EVENT_LOCK = threading.RLock()
_STRUCTURE_LOCK = threading.RLock()
IMAGE_STAGES = {"style-composition", "likeness"}
EDITABLE_STAGES = IMAGE_STAGES | {"video"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def append_jsonl(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    with _EVENT_LOCK:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())


def atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


class ProductionActions:
    def __init__(
        self,
        adapter: ProductionAdapter,
        launcher: Callable[[Path], None] | None = None,
        document_opener: Callable[[Path], None] | None = None,
    ):
        self.adapter = adapter
        self._launcher = launcher
        self._document_opener = document_opener

    def _project(self, slug: str) -> Path:
        return self.adapter._project(slug)

    @staticmethod
    def _ledger(project: Path) -> Path:
        return project / "04-images" / "generations.jsonl"

    @staticmethod
    def _job_dir(project: Path) -> Path:
        return project / "04-images" / "studio-generation-jobs"

    @staticmethod
    def _registry_path(project: Path) -> Path:
        return project / "05-storyboard" / "shots.json"

    @staticmethod
    def _change_log(project: Path) -> Path:
        return project / "05-storyboard" / "shot-changes.jsonl"

    def open_shot_list(self, slug: str) -> dict[str, object]:
        project = self._project(slug)
        registry = read_json(self._registry_path(project), {})
        source_rel = str(registry.get("source") or "") if isinstance(registry, dict) else ""
        workbook = None
        if source_rel:
            candidate = safe_child(project, source_rel)
            if candidate.is_file() and candidate.suffix.casefold() in {".xlsx", ".xlsm"}:
                workbook = candidate
        if workbook is None:
            workbook = max(
                (project / "05-storyboard").glob("*.xlsx"),
                key=lambda path: path.stat().st_mtime_ns,
                default=None,
            )
        if workbook is None:
            raise FileNotFoundError("No shot-list spreadsheet is registered")
        workbook = safe_child(project, workbook.relative_to(project), must_exist=True)
        if workbook.suffix.casefold() not in {".xlsx", ".xlsm"}:
            raise ProductionDataError("Registered shot list is not a spreadsheet")
        if self._document_opener:
            self._document_opener(workbook)
        elif os.name == "nt":
            os.startfile(workbook)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(workbook)])
        else:
            subprocess.Popen(["xdg-open", str(workbook)])
        return {"opened": True, "name": workbook.name, "path": workbook.relative_to(project).as_posix()}

    def _load_editable_registry(self, project: Path) -> dict[str, object]:
        registry = read_json(self._registry_path(project), None)
        if not isinstance(registry, dict):
            raise ProductionDataError("A stable shots.json registry is required before editing shot structure")
        if registry.get("status") != "ready":
            raise ProductionDataError("Shot structure needs reconciliation before it can be edited")
        shots = [item for item in registry.get("shots", []) if isinstance(item, dict)]
        if any(not item.get("shot_id") or item.get("id_state") == "needs_reconciliation" for item in shots):
            raise ProductionDataError("Every active shot needs a stable Shot ID before structure can change")
        source_rel = str(registry.get("source") or "")
        if source_rel:
            source = safe_child(project, source_rel)
            expected = str(registry.get("source_revision_hash") or "")
            if source.is_file() and expected and file_hash(source) != expected:
                raise ProductionDataError("Registered shot source changed. Reconcile it before editing in the UI.")
            workbooks = list((project / "05-storyboard").glob("*.xlsx"))
            if source.is_file() and source.suffix.casefold() == ".xlsx" and workbooks:
                latest = max(workbooks, key=lambda path: path.stat().st_mtime_ns)
                if latest.resolve() != source.resolve() and latest.stat().st_mtime_ns >= source.stat().st_mtime_ns:
                    raise ProductionDataError(f"{latest.name} is newer than the registry. Reconcile it before editing in the UI.")
        registry["shots"] = shots
        registry["retired_shots"] = [item for item in registry.get("retired_shots", []) if isinstance(item, dict)]
        return registry

    @staticmethod
    def _clean_field(payload: dict[str, object], key: str, *, limit: int, required: bool = False) -> str:
        value = str(payload.get(key) or "").strip()
        if required and not value:
            raise ProductionDataError(f"{key} is required")
        if len(value) > limit:
            raise ProductionDataError(f"{key} is too long")
        return value

    @staticmethod
    def _suggest_display(shots: list[dict[str, object]], after_shot_id: str | None = None) -> str:
        used = {str(item.get("display_number") or "").casefold() for item in shots}
        if after_shot_id:
            previous = next((item for item in shots if str(item.get("shot_id")) == after_shot_id), None)
            if previous:
                match = re.fullmatch(r"(\d+)([A-Za-z]*)", str(previous.get("display_number") or ""))
                if match:
                    base, suffix = match.groups()
                    start = ord(suffix[-1].upper()) - 64 if suffix else 0
                    for index in range(start + 1, start + 53):
                        alpha = chr(65 + ((index - 1) % 26))
                        cycle = "" if index <= 26 else str((index - 1) // 26 + 1)
                        candidate = f"{base}{alpha}{cycle}"
                        if candidate.casefold() not in used:
                            return candidate
        numeric = [int(str(item.get("display_number"))) for item in shots if str(item.get("display_number") or "").isdigit()]
        candidate = str(max(numeric, default=0) + 1)
        while candidate.casefold() in used:
            candidate = str(int(candidate) + 1)
        return candidate

    @staticmethod
    def _reindex(shots: list[dict[str, object]]) -> None:
        for index, shot in enumerate(shots, start=1):
            shot["order"] = index

    def _commit_structure(self, project: Path, registry: dict[str, object], event: dict[str, object]) -> None:
        event_id = str(event.get("event_id") or uuid.uuid4())
        revision = int(registry.get("registry_revision") or 0) + 1
        now = utc_now()
        registry.update({
            "schema_version": max(2, int(registry.get("schema_version") or 1)),
            "registry_revision": revision,
            "registry_revision_id": str(uuid.uuid4()),
            "updated_at": now,
            "source_sync_state": "studio-edited",
            "last_structure_event_id": event_id,
            "status": "ready",
        })
        registry["retired_shot_ids"] = [
            str(item.get("shot_id")) for item in registry.get("retired_shots", []) if item.get("shot_id")
        ]
        event.update({
            "schema_version": 1,
            "event_id": event_id,
            "created_at": now,
            "registry_revision": revision,
            "registry_revision_id": registry["registry_revision_id"],
            "source": "hearthlight-studio",
            "confirmed_by_user": True,
        })
        with _STRUCTURE_LOCK:
            atomic_write_json(self._registry_path(project), registry)
            append_jsonl(self._change_log(project), event)

    def create_shot(self, slug: str, payload: dict[str, object]) -> dict[str, object]:
        project = self._project(slug)
        registry = self._load_editable_registry(project)
        shots = registry["shots"]
        after_id = str(payload.get("afterShotId") or "").strip()
        insert_at = len(shots)
        if after_id:
            matches = [index for index, item in enumerate(shots) if str(item.get("shot_id")) == after_id]
            if len(matches) != 1:
                raise ProductionDataError("Insert position no longer exists")
            insert_at = matches[0] + 1
        display = self._clean_field(payload, "displayNumber", limit=24) or self._suggest_display(shots, after_id or None)
        if display.casefold() in {str(item.get("display_number") or "").casefold() for item in shots}:
            raise ProductionDataError(f"Shot label {display} is already in use")
        title = self._clean_field(payload, "title", limit=240, required=True)
        duration_raw = payload.get("durationSeconds")
        duration = None
        if duration_raw not in (None, ""):
            try:
                duration = float(duration_raw)
            except (TypeError, ValueError) as exc:
                raise ProductionDataError("Duration must be a number") from exc
            if duration < 0 or duration > 3600:
                raise ProductionDataError("Duration is outside the supported range")
        owner_id = str(payload.get("sharedSetupOwnerShotId") or "").strip() or None
        if owner_id and not any(str(item.get("shot_id")) == owner_id for item in shots):
            raise ProductionDataError("Shared setup owner no longer exists")
        shot_id = str(uuid.uuid4())
        created = utc_now()
        camera = self._clean_field(payload, "cameraMovement", limit=2_000)
        shot = {
            "shot_id": shot_id,
            "display_number": display,
            "order": insert_at + 1,
            "legacy_numbers": [],
            "title": title,
            "start": "",
            "end": "",
            "duration_seconds": duration,
            "board_panels": [],
            "storyboard_reference": "",
            "text": {
                "visual_description": self._clean_field(payload, "storyVisualDescription", limit=20_000),
                "action_description": self._clean_field(payload, "videoMotion", limit=20_000),
                "dialogue": self._clean_field(payload, "dialogue", limit=20_000),
                "audio": self._clean_field(payload, "audio", limit=20_000),
                "camera_movement": camera,
                "notes": "Created in Hearthlight Studio.",
            },
            "image_direction": {
                "visual_description": self._clean_field(payload, "imageDirection", limit=40_000),
                "action_description": "",
                "camera_movement": camera,
                "continuity_note": "",
                "render_mode": "generated",
                "source_asset": None,
            },
            "id_state": "stable",
            "matched_by": "explicit-shot-id",
            "origin": "hearthlight-studio",
            "created_at": created,
            "shared_setup_owner_shot_id": owner_id,
        }
        shots.insert(insert_at, shot)
        self._reindex(shots)
        self._commit_structure(project, registry, {
            "event": "shot-inserted",
            "shot_id": shot_id,
            "display_number": display,
            "after_shot_id": after_id or None,
            "shot_snapshot": shot,
        })
        return {"created": True, "shotId": shot_id, "displayNumber": display, "order": shot["order"]}

    def retire_shot(self, slug: str, shot_id: str, payload: dict[str, object]) -> dict[str, object]:
        project = self._project(slug)
        registry = self._load_editable_registry(project)
        shots = registry["shots"]
        index = next((index for index, item in enumerate(shots) if str(item.get("shot_id")) == shot_id), None)
        if index is None:
            raise FileNotFoundError(shot_id)
        dependants = [item for item in shots if str(item.get("shared_setup_owner_shot_id") or "") == shot_id]
        if dependants:
            labels = ", ".join(str(item.get("display_number")) for item in dependants)
            raise ProductionDataError(f"Reassign shared setup dependants before deleting this shot: {labels}")
        reason = self._clean_field(payload, "reason", limit=2_000)
        snapshot = dict(shots.pop(index))
        snapshot.update({
            "retired_at": utc_now(),
            "retired_reason": reason,
            "retired_order": snapshot.get("order"),
            "retired_display_number": snapshot.get("display_number"),
        })
        registry["retired_shots"].append(snapshot)
        self._reindex(shots)
        self._commit_structure(project, registry, {
            "event": "shot-retired",
            "shot_id": shot_id,
            "display_number": snapshot.get("display_number"),
            "reason": reason,
            "shot_snapshot": snapshot,
        })
        return {"retired": True, "shotId": shot_id, "retiredCount": len(registry["retired_shots"])}

    def restore_shot(self, slug: str, shot_id: str, payload: dict[str, object]) -> dict[str, object]:
        project = self._project(slug)
        registry = self._load_editable_registry(project)
        retired = registry["retired_shots"]
        retired_index = next((index for index, item in enumerate(retired) if str(item.get("shot_id")) == shot_id), None)
        if retired_index is None:
            raise FileNotFoundError(shot_id)
        shots = registry["shots"]
        after_id = str(payload.get("afterShotId") or "").strip()
        insert_at = len(shots)
        if after_id:
            active_index = next((index for index, item in enumerate(shots) if str(item.get("shot_id")) == after_id), None)
            if active_index is None:
                raise ProductionDataError("Restore position no longer exists")
            insert_at = active_index + 1
        shot = dict(retired.pop(retired_index))
        original_display = str(shot.get("retired_display_number") or shot.get("display_number") or "")
        used = {str(item.get("display_number") or "").casefold() for item in shots}
        shot["display_number"] = original_display if original_display.casefold() not in used else self._suggest_display(shots, after_id or None)
        for key in ["retired_at", "retired_reason", "retired_order", "retired_display_number"]:
            shot.pop(key, None)
        shot["restored_at"] = utc_now()
        shot["id_state"] = "stable"
        shots.insert(insert_at, shot)
        self._reindex(shots)
        self._commit_structure(project, registry, {
            "event": "shot-restored",
            "shot_id": shot_id,
            "display_number": shot["display_number"],
            "after_shot_id": after_id or None,
        })
        return {"restored": True, "shotId": shot_id, "displayNumber": shot["display_number"], "order": shot["order"]}

    def _shot(self, slug: str, shot_id: str) -> dict[str, object]:
        shot = self.adapter.get_shot(slug, shot_id)["shot"]
        if shot.get("reconciliationStatus") not in {"stable", "new"} or shot.get("inferred"):
            raise ProductionDataError("This shot needs identity reconciliation before it can be changed")
        return shot

    @staticmethod
    def _asset(shot: dict[str, object], asset_id: str) -> dict[str, object]:
        match = next((item for item in shot.get("assetHistory", []) if str(item.get("assetId")) == asset_id), None)
        if not match:
            raise FileNotFoundError(asset_id)
        return match

    @staticmethod
    def _base_fields(shot: dict[str, object], asset: dict[str, object] | None = None) -> dict[str, object]:
        fields: dict[str, object] = {
            "schema_version": 2,
            "shot_id": shot["shotId"],
            "shot": shot["displayNumber"],
            "source_shot_label": shot["displayNumber"],
        }
        if shot.get("legacyNumbers"):
            fields["legacy_shot_v3"] = shot["legacyNumbers"][0]
        if asset:
            fields.update({"asset_id": asset.get("assetId"), "version": asset.get("version"), "asset_path": asset.get("path")})
        return fields

    @staticmethod
    def _adopt_if_inferred(project: Path, shot: dict[str, object], asset: dict[str, object]) -> dict[str, object]:
        return asset

    def save_prompt(self, slug: str, shot_id: str, payload: dict[str, object]) -> dict[str, object]:
        project = self._project(slug)
        shot = self._shot(slug, shot_id)
        prompt = str(payload.get("prompt") or "").strip()
        stage = str(payload.get("stage") or "style-composition")
        if stage not in EDITABLE_STAGES:
            raise ProductionDataError("Unsupported prompt stage")
        if not prompt:
            raise ProductionDataError("Prompt cannot be empty")
        if len(prompt) > 100_000:
            raise ProductionDataError("Prompt is too long")
        asset_id = str(payload.get("assetId") or "")
        asset = self._asset(shot, asset_id) if asset_id else None
        event = {
            "event": "prompt-edit", "event_id": str(uuid.uuid4()), "created_at": utc_now(),
            **self._base_fields(shot, asset), "workflow_stage": stage, "prompt": prompt,
            "base_asset_id": asset_id or None, "source": "hearthlight-studio", "confirmed_by_user": True,
        }
        append_jsonl(self._ledger(project), event)
        return {"saved": True, "eventId": event["event_id"], "prompt": prompt, "stage": stage}

    def flag_asset(self, slug: str, shot_id: str, asset_id: str, feedback: object) -> dict[str, object]:
        project = self._project(slug)
        shot = self._shot(slug, shot_id)
        asset = self._adopt_if_inferred(project, shot, self._asset(shot, asset_id))
        note = str(feedback or "").strip()
        if not note:
            raise ProductionDataError("A change note is required")
        event = {
            "event": "review", "event_id": str(uuid.uuid4()), "created_at": utc_now(),
            **self._base_fields(shot, asset), "review_stage": asset.get("stage") or "image",
            "status": "revision-requested", "feedback": note, "source": "hearthlight-studio", "confirmed_by_user": True,
        }
        append_jsonl(self._ledger(project), event)
        return {"saved": True, "eventId": event["event_id"], "status": event["status"], "feedback": note}

    def _append_selection(self, project: Path, shot: dict[str, object], asset: dict[str, object], purpose: str) -> dict[str, object]:
        event = {
            "event": "selection", "event_id": str(uuid.uuid4()), "created_at": utc_now(),
            **self._base_fields(shot, asset), "purpose": purpose, "source": "hearthlight-studio", "confirmed_by_user": True,
        }
        if purpose == "final":
            event["selected_final"] = True
        append_jsonl(self._ledger(project), event)
        return event

    def approve_asset(self, slug: str, shot_id: str, asset_id: str) -> dict[str, object]:
        project = self._project(slug)
        shot = self._shot(slug, shot_id)
        asset = self._adopt_if_inferred(project, shot, self._asset(shot, asset_id))
        if asset.get("stale"):
            raise ProductionDataError("A stale descendant cannot pass its stage")
        stage = str(asset.get("stage") or "image")
        if stage == "storyboard":
            raise ProductionDataError("Storyboard gates are not approved from this screen")
        status = "composition-approved" if stage == "style-composition" else "likeness-approved" if stage == "likeness" else "approved"
        purpose = "composition-base" if stage == "style-composition" else "final"
        review = {
            "event": "review", "event_id": str(uuid.uuid4()), "created_at": utc_now(),
            **self._base_fields(shot, asset), "review_stage": stage, "status": status, "feedback": "",
            "source": "hearthlight-studio", "confirmed_by_user": True,
        }
        append_jsonl(self._ledger(project), review)
        selection = self._append_selection(project, shot, asset, purpose)
        hero = self._append_selection(project, shot, asset, "hero")
        return {"approved": True, "status": status, "purpose": purpose, "reviewEventId": review["event_id"], "selectionEventId": selection["event_id"], "heroEventId": hero["event_id"]}

    def select_asset(self, slug: str, shot_id: str, asset_id: str) -> dict[str, object]:
        project = self._project(slug)
        shot = self._shot(slug, shot_id)
        asset = self._adopt_if_inferred(project, shot, self._asset(shot, asset_id))
        if asset.get("stale"):
            raise ProductionDataError("A stale descendant cannot be chosen as the hero")
        selection = self._append_selection(project, shot, asset, "hero")
        return {"selected": True, "assetId": asset_id, "eventId": selection["event_id"]}

    def bulk_approve(self, slug: str, payload: dict[str, object]) -> dict[str, object]:
        stage = str(payload.get("stage") or "style-composition")
        if stage not in EDITABLE_STAGES:
            raise ProductionDataError("Unsupported review stage")
        production = self.adapter.get_production(slug)
        if not production.get("structureEditable"):
            raise ProductionDataError(str(production.get("structureBlocker") or "Project identity needs reconciliation"))
        candidates: list[tuple[str, str]] = []
        seen: set[str] = set()
        for shot in production["shots"]:
            asset = next((item for item in shot.get("assetHistory", []) if item.get("stage") == stage and not item.get("stale")), None)
            if not asset or str(asset.get("assetId")) in seen:
                continue
            if is_approved(asset.get("reviewState")) or asset.get("reviewState") == "revision-requested" or str(asset.get("feedback") or "").strip():
                continue
            seen.add(str(asset["assetId"]))
            candidates.append((str(shot["shotId"]), str(asset["assetId"])))
        approved = []
        for candidate_shot, candidate_asset in candidates:
            self.approve_asset(slug, candidate_shot, candidate_asset)
            approved.append({"shotId": candidate_shot, "assetId": candidate_asset})
        return {"approved": approved, "count": len(approved), "stage": stage}

    def queue_generation(self, slug: str, shot_id: str, payload: dict[str, object]) -> dict[str, object]:
        project = self._project(slug)
        shot = self._shot(slug, shot_id)
        if shot.get("sharedSetupOwnerShotId"):
            owner_number = shot.get("sharedSetupOwnerDisplayNumber") or "its setup owner"
            raise ProductionDataError(f"This shot shares Shot {owner_number}. Generate from the shared setup owner.")
        stage = str(payload.get("stage") or shot.get("currentPrompt", {}).get("stage") or "style-composition")
        if stage not in IMAGE_STAGES:
            raise ProductionDataError("Only still-image generation is available here")
        prompt = str(payload.get("prompt") or shot.get("currentPrompt", {}).get("prompt") or "").strip()
        if not prompt:
            raise ProductionDataError("Save a prompt before generating")
        manifest = read_json(project / "03-bible" / "assets.json", {})
        manifest = manifest if isinstance(manifest, dict) else {}
        workflow = manifest.get("image_workflow") if isinstance(manifest.get("image_workflow"), dict) else {}
        stage_settings = workflow.get(stage.replace("-", "_")) if isinstance(workflow.get(stage.replace("-", "_")), dict) else {}
        cost_key = "style_composition" if stage == "style-composition" else "likeness"
        approvals = manifest.get("cost_approvals") if isinstance(manifest.get("cost_approvals"), dict) else {}
        if str((approvals.get(cost_key) or {}).get("status") or "").casefold() != "approved":
            raise ProductionDataError(f"{stage} generation cost is not approved")
        if stage == "likeness":
            unresolved = [item["label"] for item in shot.get("requirements", []) if str(item.get("id", "")).startswith("character-") and item.get("status") != "approved"]
            if unresolved:
                raise ProductionDataError("Likeness generation is blocked by: " + ", ".join(unresolved))
            if not any(item.get("selectionState") == "composition-base" for item in shot.get("assetHistory", [])):
                raise ProductionDataError("Pass and select a style + composition base first")
        model = str(payload.get("model") or stage_settings.get("model") or shot.get("currentPrompt", {}).get("model") or "")
        if not model:
            raise ProductionDataError("No model is registered for this stage")
        owner_id = str(shot.get("sharedSetupOwnerShotId") or shot["shotId"])
        production = self.adapter.get_production(slug)
        owner_shot = next((item for item in production["shots"] if item["shotId"] == owner_id), shot)
        versions = [
            int(item["version"])
            for item in owner_shot.get("assetHistory", [])
            if str(item.get("stage") or "") == stage and str(item.get("version") or "").isdigit()
        ]
        version = max(versions, default=0) + 1
        label = re.sub(r"[^A-Za-z0-9]+", "-", str(owner_shot["displayNumber"])).strip("-").casefold() or "shot"
        raw_suffix = re.sub(r"[^a-f0-9]", "", owner_id.casefold())
        stable_suffix = raw_suffix[:8] if len(raw_suffix) >= 8 else uuid.uuid5(uuid.NAMESPACE_URL, owner_id).hex[:8]
        output_rel = f"04-images/shot-{label}-{stable_suffix}-v{version:02d}.png"
        output = safe_child(project, output_rel)
        if output.exists():
            raise ProductionDataError(f"Immutable output already exists: {output_rel}")
        references = (shot.get("generationStages") or {}).get(stage, {}).get("references", [])
        parent = next((item for item in shot.get("assetHistory", []) if item.get("selectionState") == "composition-base"), None) if stage == "likeness" else None
        job_id = str(uuid.uuid4())
        job_path = self._job_dir(project) / f"{job_id}.json"
        job = {
            "schemaVersion": 1, "jobId": job_id, "status": "queued", "slug": slug, "projectRoot": str(project),
            "shotId": shot["shotId"], "shot": shot["displayNumber"], "ownerShotId": owner_id, "ownerShot": owner_shot["displayNumber"],
            "stage": stage, "model": model, "prompt": prompt,
            "aspectRatio": stage_settings.get("aspect_ratio") or manifest.get("master_aspect_ratio") or "16:9",
            "resolution": stage_settings.get("resolution") or "1K", "references": references,
            "parentAssetId": parent.get("assetId") if parent else None, "parentVersion": parent.get("version") if parent else None,
            "version": version, "outputPath": output_rel, "jobPath": str(job_path),
            "completionScript": str((Path(__file__).resolve().parents[1] / "scripts" / "complete_production_generation.py")),
            "createdAt": utc_now(), "registryRevisionId": production.get("registryRevisionId"),
        }
        atomic_write_json(job_path, job)
        if self._launcher:
            self._launcher(job_path)
        else:
            self._spawn_worker(job_path)
        return {"queued": True, "jobId": job_id, "status": "queued", "stage": stage, "model": model}

    @staticmethod
    def _spawn_worker(job_path: Path) -> None:
        command = [sys.executable, "-m", "film_study_tool.production_generation_worker", str(job_path)]
        kwargs: dict[str, object] = {
            "cwd": str(Path(__file__).resolve().parents[1]),
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(command, **kwargs)

    def get_job(self, slug: str, job_id: str) -> dict[str, object]:
        project = self._project(slug)
        if not job_id or Path(job_id).name != job_id:
            raise ProductionDataError("Invalid generation job")
        path = self._job_dir(project) / f"{job_id}.json"
        payload = read_json(path, None)
        if not isinstance(payload, dict) or payload.get("jobId") != job_id:
            raise FileNotFoundError(job_id)
        return payload

