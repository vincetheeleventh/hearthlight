from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from pathlib import Path

from film_study_tool.production_actions import ProductionActions
from film_study_tool.productions import ProductionAdapter, ProductionDataError, safe_child
from film_study_tool.ui_server import ServerConfig, make_handler


class ProductionFixture:
    def __init__(self, root: Path):
        self.root = root
        self.project = root / "projects" / "demo"
        for relative in ["03-bible/characters/father", "03-bible/characters/boy", "03-bible/characters/mother", "04-images", "05-storyboard", "06-video", "skills/hearthlight-dashboard"]:
            (self.project / relative).mkdir(parents=True, exist_ok=True) if not relative.startswith("skills/") else (root / relative).mkdir(parents=True, exist_ok=True)
        stages = [
            {"id": "distribution_spec", "label": "Distribution", "gate": "Spec", "kind": "gate"},
            {"id": "gate2_mise_en_scene", "label": "Mise", "gate": "Gate 2", "kind": "gate"},
            {"id": "characters", "label": "Characters", "gate": None, "kind": "support"},
            {"id": "gate3_images", "label": "Images", "gate": "Gate 3", "kind": "gate"},
            {"id": "gate4_storyboard", "label": "Storyboard", "gate": "Gate 4", "kind": "gate"},
            {"id": "gate5_video", "label": "Video", "gate": "Gate 5", "kind": "gate"},
        ]
        self.write(root / "skills/hearthlight-dashboard/pipeline.json", {"stages": stages})
        requirements = [
            {"id": "distribution-spec", "label": "Distribution specification", "scope": "project", "stage_dependency": "distribution_spec", "gate_dependency": "distribution_spec", "expected_path": "distribution-spec.md", "evidence": {"type": "path"}},
            {"id": "character-dossier", "label": "Character dossier", "scope": "project", "stage_dependency": "characters", "gate_dependency": "gate2_mise_en_scene"},
            {"id": "character-record", "label": "Character description", "scope": "project", "stage_dependency": "characters", "gate_dependency": "gate2_mise_en_scene"},
            {"id": "character-sheet", "label": "Approved character sheet", "scope": "project", "stage_dependency": "characters", "gate_dependency": "gate3_images"},
            {"id": "environment-sheet", "label": "Environment sheet", "scope": "project", "stage_dependency": "gate2_mise_en_scene", "gate_dependency": "gate3_images"},
        ]
        self.write(root / "skills/hearthlight-dashboard/requirements.json", {"requirements": requirements})
        (self.project / "distribution-spec.md").write_text("- format: short film\n- client: none\n", encoding="utf-8")
        (self.project / "status.yml").write_text("distribution_spec: pending\ngate2_mise_en_scene: pending\ngate3_images: pending\ngate4_storyboard: approved 2026-07-30\ngate5_video: pending\n", encoding="utf-8")
        shots = []
        for number in range(1, 29):
            shots.append({
                "shot_id": f"shot-{number}", "display_number": number, "order": number, "legacy_numbers": [str(number)], "title": f"Shot {number}",
                "duration_seconds": 1, "board_panels": [], "shared_setup_owner_shot_id": "shot-1" if number == 4 else None,
                "text": {"visual_description": f"Story {number}", "action_description": f"Motion {number}", "dialogue": "", "audio": "", "camera_movement": "static", "notes": ""},
                "image_direction": {"visual_description": f"Still {number}", "action_description": "", "camera_movement": "static", "continuity_note": "", "render_mode": "source-photo" if number == 28 else "generated", "source_asset": None},
            })
        self.write(self.project / "05-storyboard/shots.json", {"schema_version": 1, "source": "05-storyboard/board-v3.xlsx", "status": "ready", "shots": shots})
        (self.project / "05-storyboard/board-v3.xlsx").write_bytes(b"workbook")
        self.write(self.project / "05-storyboard/shot-narrative.json", {
            "schema_version": 2,
            "value_axis": "expression ↔ bottling up",
            "shots": {
                "shot-2": {
                    "one_liner": "The boy digs while his father fills the doorway.",
                    "expanded": "Alienation before connection.",
                    "open_loops": ["Can they speak before he leaves?"],
                    "why_this_shot": "Doorway framing reads as distance.",
                    "beat": "2 · The Attempt",
                    "charge": "First on-screen test of the axis.",
                    "motifs": ["hands before faces", "doorway as threshold"],
                    "never": ["No dialogue restored."],
                    "staging": {
                        "surfaced": {"shot_type": "Two-shot", "camera_move": "None", "character_actions": "Boy sorts cards", "setting": "Boy's bedroom"},
                        "ambient": {"props": "Scattered cards", "lighting": "Hallway silhouette", "sound": "Card shuffle"},
                    },
                }
            },
        })
        assets = [
            {"id": "character-father", "kind": "character-sheet", "local_path": "03-bible/characters/father/father-sheet.png", "status": "approved", "shots": [1]},
            {"id": "character-boy", "kind": "character-sheet", "local_path": "03-bible/characters/boy/boy-sheet.png", "status": "generated", "shots": [1, 2, 3]},
            {"id": "character-mother", "kind": "character-sheet", "local_path": "03-bible/characters/mother/mother-sheet.png", "status": "missing", "shots": [2]},
            *[{"id": f"setting-{name}", "kind": "setting-sheet", "local_path": f"03-bible/refs/environments/{name}.png", "status": "missing", "shots": [1]} for name in ["parents-bedroom", "boy-bedroom", "doorway-driveway"]],
        ]
        self.write(self.project / "03-bible/assets.json", {
            "assets": assets,
            "default_model": "flux-1.1-pro",
            "master_aspect_ratio": "16:9",
            "moodboard": {"id": "moodboard-demo", "name": "Ink wash mood board", "status": "approved", "strength": "0.72"},
            "image_workflow": {
                "style_composition": {"model": "flux-1.1-pro", "aspect_ratio": "16:9", "resolution": "1K"},
                "likeness": {"model": "gpt-image-2", "aspect_ratio": "16:9", "resolution": "1536x1024"},
            },
            "cost_approvals": {"style_composition": {"status": "approved"}, "likeness": {"status": "approved"}},
        })
        for name, status, approved in [("father", "approved", True), ("boy", "proposed", False), ("mother", "proposed", False)]:
            folder = self.project / "03-bible/characters" / name
            (folder / "CHARACTER.md").write_text(f"# {name}\n", encoding="utf-8")
            self.write(folder / "character.json", {"id": name, "status": status, "sheet_status": "APPROVED" if approved else "pending", "sheet": f"03-bible/characters/{name}/{name}-sheet.png"})
        (self.project / "03-bible/characters/father/father-sheet.png").write_bytes(b"father")
        (self.project / "03-bible/characters/boy/boy-sheet.png").write_bytes(b"boy")
        events = []
        for number in [1, 2, 3]:
            path = self.project / "04-images" / f"shot-{number:02d}-v01.png"
            path.write_bytes(f"image-{number}".encode())
            events.append({"schema_version": 2, "event": "generation", "event_id": f"image-{number}", "shot": number, "version": 1, "workflow_stage": "style-composition", "asset_path": path.relative_to(self.project).as_posix(), "dimensions": [1376, 768], "aspect_ratio": "4:3" if number == 1 else "16:9", "review_status": "pending-review", "selected_final": False, "source": "krea", "model": "flux-1.1-pro", "prompt": f"Prompt {number}", "references": [{"id": "moodboard-demo", "type": "moodboard", "strength": "0.72"}], "created_at": f"2026-08-01T00:00:0{number}+00:00"})
        (self.project / "04-images/generations.jsonl").write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")

    @staticmethod
    def write(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")


def tree_snapshot(root: Path) -> list[tuple[str, int, int]]:
    return sorted((path.relative_to(root).as_posix(), path.stat().st_size, path.stat().st_mtime_ns) for path in root.rglob("*") if path.is_file())


class ProductionAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_base = os.environ.get("HEARTHLIGHT_TEST_TMP") or (r"C:\tmp" if os.name == "nt" else None)
        self.temp = tempfile.TemporaryDirectory(dir=temp_base)
        self.root = Path(self.temp.name)
        self.fixture = ProductionFixture(self.root)
        self.adapter = ProductionAdapter(self.root, self.root.parent / "separate-cache")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_yugioh_style_acceptance_fixture(self) -> None:
        production = self.adapter.get_production("demo")
        self.assertEqual(production["shotCount"], 28)
        self.assertEqual(production["uniqueIllustratedSetups"], 26)
        self.assertEqual(production["pendingReviewCount"], 3)
        self.assertEqual([production["shots"][index]["heroAsset"]["assetId"] for index in range(3)], ["image-1", "image-2", "image-3"])
        self.assertEqual(production["shots"][3]["heroAsset"]["assetId"], "image-1")
        self.assertEqual(production["shots"][3]["heroAsset"]["inheritedFromShotId"], "shot-1")
        requirements = {item["label"]: item["status"] for item in production["requirements"]}
        self.assertEqual(requirements["Father character sheet"], "approved")
        self.assertEqual(requirements["Boy character sheet"], "ready for approval")
        self.assertEqual(requirements["Mother character sheet"], "missing")
        self.assertEqual(sum(1 for label, status in requirements.items() if "Bedroom" in label or "Driveway" in label and status == "missing"), 3)
        codes = {item["code"] for item in production["validationFindings"]}
        self.assertIn("gate-history-inconsistency", codes)
        self.assertNotIn("conflicting-character-status", codes)
        self.assertIn("aspect-metadata-mismatch", codes)
        self.assertNotEqual(production["shots"][0]["heroAsset"]["kind"], "video")

    def test_narrative_sidecar_joins_by_shot_id(self) -> None:
        production = self.adapter.get_production("demo")
        by_id = {shot["shotId"]: shot for shot in production["shots"]}
        authored = by_id["shot-2"]["narrative"]
        self.assertTrue(authored["authored"])
        self.assertEqual(authored["oneLiner"], "The boy digs while his father fills the doorway.")
        self.assertEqual(authored["openLoops"], ["Can they speak before he leaves?"])
        self.assertEqual(authored["staging"]["surfaced"]["shotType"], "Two-shot")
        self.assertEqual(authored["staging"]["ambient"]["sound"], "Card shuffle")
        self.assertEqual(authored["beat"], "2 · The Attempt")
        self.assertEqual(authored["charge"], "First on-screen test of the axis.")
        self.assertEqual(authored["motifs"], ["hands before faces", "doorway as threshold"])
        self.assertEqual(authored["never"], ["No dialogue restored."])
        self.assertEqual(production["narrativeValueAxis"], "expression ↔ bottling up")
        unauthored = by_id["shot-1"]["narrative"]
        self.assertFalse(unauthored["authored"])
        self.assertEqual(unauthored["oneLiner"], "")
        self.assertEqual(unauthored["beat"], "")
        self.assertEqual(unauthored["never"], [])

    def test_reads_do_not_change_project_files(self) -> None:
        before = tree_snapshot(self.root)
        self.adapter.list_productions()
        self.adapter.get_production("demo")
        self.adapter.get_shot("demo", "shot-1")
        self.assertEqual(tree_snapshot(self.root), before)

    def test_safe_child_rejects_traversal(self) -> None:
        with self.assertRaises(ProductionDataError):
            safe_child(self.fixture.project, "../../outside.mp4")

    def test_hero_precedence_and_stale_lineage(self) -> None:
        shots = [{"shotId": "s", "sharedSetupOwnerShotId": None, "reconciliationStatus": "stable", "inferred": False}]
        assets = [
            {"assetId": "still-old", "shotId": "s", "kind": "image", "stage": "final", "selectionState": "selected-final", "reviewState": "approved", "createdAt": "2026-01-01", "stale": False},
            {"assetId": "still-current", "shotId": "s", "kind": "image", "stage": "final", "selectionState": "selected-final", "reviewState": "approved", "createdAt": "2026-01-02", "stale": False},
            {"assetId": "video-stale", "shotId": "s", "kind": "video", "stage": "video", "selectionState": "", "reviewState": "approved", "createdAt": "2026-01-03", "parentAssetId": "still-old", "stale": False},
            {"assetId": "video-current", "shotId": "s", "kind": "video", "stage": "video", "selectionState": "", "reviewState": "approved", "createdAt": "2026-01-04", "parentAssetId": "still-current", "stale": False},
        ]
        ProductionAdapter._resolve_heroes(shots, assets)
        self.assertEqual(shots[0]["heroAsset"]["assetId"], "video-current")
        self.assertTrue(next(asset for asset in assets if asset["assetId"] == "video-stale")["stale"])

    def test_malformed_jsonl_is_isolated(self) -> None:
        path = self.fixture.project / "04-images/generations.jsonl"
        path.write_text(path.read_text(encoding="utf-8") + "not-json\n", encoding="utf-8")
        production = self.adapter.get_production("demo")
        self.assertEqual(production["shotCount"], 28)
        self.assertIn("malformed-jsonl", {item["code"] for item in production["validationFindings"]})

    def test_legacy_revision_label_beats_shifted_display_number(self) -> None:
        path = self.fixture.project / "04-images" / "legacy-offset.png"
        path.write_bytes(b"legacy-offset")
        event = {
            "event": "generation", "event_id": "legacy-offset", "shot": 2, "legacy_shot_v3": 1,
            "version": 2, "workflow_stage": "style-composition",
            "asset_path": path.relative_to(self.fixture.project).as_posix(),
        }
        ledger = self.fixture.project / "04-images/generations.jsonl"
        ledger.write_text(ledger.read_text(encoding="utf-8") + json.dumps(event) + "\n", encoding="utf-8")
        production = self.adapter.get_production("demo")
        owner = next(shot for shot in production["shots"] if shot["shotId"] == "shot-1")
        self.assertIn("legacy-offset", {asset["assetId"] for asset in owner["assetHistory"]})
        wrong = next(shot for shot in production["shots"] if shot["shotId"] == "shot-2")
        self.assertNotIn("legacy-offset", {asset["assetId"] for asset in wrong["assetHistory"]})

    def test_retired_asset_is_not_reassigned_by_filename_inference(self) -> None:
        actions = ProductionActions(self.adapter)
        actions.retire_shot("demo", "shot-2", {"reason": "Editorial removal"})
        production = self.adapter.get_production("demo")
        active_asset_ids = {
            asset["assetId"] for shot in production["shots"] for asset in shot["assetHistory"]
        }
        self.assertNotIn("image-2", active_asset_ids)
        self.assertFalse(any(item.get("path") == "04-images/shot-02-v01.png" for item in production["unmappedAssets"]))



class ProductionActionTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_base = os.environ.get("HEARTHLIGHT_TEST_TMP") or (r"C:\tmp" if os.name == "nt" else None)
        self.temp = tempfile.TemporaryDirectory(dir=temp_base)
        self.root = Path(self.temp.name)
        self.fixture = ProductionFixture(self.root)
        self.adapter = ProductionAdapter(self.root, self.root.parent / "action-cache")

    def tearDown(self) -> None:
        self.temp.cleanup()
    def test_generation_metadata_and_dependencies_are_exposed(self) -> None:
        shot = self.adapter.get_shot("demo", "shot-1")["shot"]
        self.assertEqual(shot["currentPrompt"]["usedPrompt"], "Prompt 1")
        self.assertEqual(shot["currentPrompt"]["model"], "flux-1.1-pro")
        self.assertEqual(shot["currentPrompt"]["stageLabel"], "Style + composition")
        self.assertEqual(shot["currentPrompt"]["references"][0]["name"], "Ink wash mood board")
        self.assertNotIn("Boy character sheet", {item["label"] for item in shot["missingDependencies"]})
        self.assertIn("Boy character sheet", {item["label"] for item in shot["approvalDependencies"]})

    def test_registered_shot_list_opens_directly(self) -> None:
        opened: list[Path] = []
        actions = ProductionActions(self.adapter, document_opener=opened.append)
        result = actions.open_shot_list("demo")
        self.assertTrue(result["opened"])
        self.assertEqual(result["name"], "board-v3.xlsx")
        self.assertEqual(opened, [self.fixture.project / "05-storyboard/board-v3.xlsx"])
        self.assertEqual(self.adapter.get_production("demo")["shotListDocument"]["source"], "registered")

    def test_one_shot_vision_save_versions_only_that_shot(self) -> None:
        actions = ProductionActions(self.adapter)
        before_one = self.adapter.get_shot("demo", "shot-1")["shot"]["shotVision"]
        before_two = self.adapter.get_shot("demo", "shot-2")["shot"]["shotVision"]
        with patch.object(actions, "_compile_prompt_batch", return_value={"job_count": 1}) as compile_mock:
            result = actions.submit_vision_batch("demo", {"changes": [{
                "shotId": "shot-1",
                "vision": "Only this shot changes.",
                "baseRevision": before_one["revision"],
            }]})
        self.assertTrue(result["saved"])
        self.assertEqual(result["changed"], 1)
        compile_mock.assert_called_once()
        after_one = self.adapter.get_shot("demo", "shot-1")["shot"]["shotVision"]
        after_two = self.adapter.get_shot("demo", "shot-2")["shot"]["shotVision"]
        self.assertEqual(after_one["revision"], before_one["revision"] + 1)
        self.assertEqual(after_one["text"], "Only this shot changes.")
        self.assertEqual(after_two["revision"], before_two["revision"])
        self.assertEqual(after_two["text"], before_two["text"])

    def test_review_prompt_selection_bulk_approval_and_generation_queue(self) -> None:
        launched: list[Path] = []
        actions = ProductionActions(self.adapter, launched.append)
        saved = actions.save_prompt("demo", "shot-1", {"stage": "style-composition", "assetId": "image-1", "prompt": "Revised prompt"})
        self.assertTrue(saved["saved"])
        self.assertEqual(self.adapter.get_shot("demo", "shot-1")["shot"]["currentPrompt"]["prompt"], "Revised prompt")

        actions.flag_asset("demo", "shot-1", "image-1", "Raise the camera and simplify the room")
        bulk = actions.bulk_approve("demo", {"stage": "style-composition"})
        self.assertEqual(bulk["count"], 2)
        self.assertNotIn("shot-1", {item["shotId"] for item in bulk["approved"]})
        self.assertEqual(self.adapter.get_shot("demo", "shot-1")["shot"]["assetHistory"][0]["reviewState"], "revision-requested")

        actions.approve_asset("demo", "shot-1", "image-1")
        chosen = actions.select_asset("demo", "shot-1", "image-1")
        self.assertTrue(chosen["selected"])
        shot = self.adapter.get_shot("demo", "shot-1")["shot"]
        self.assertEqual(shot["heroAsset"]["assetId"], "image-1")
        self.assertEqual(shot["heroAsset"]["selectionState"], "composition-base")

        queued = actions.queue_generation("demo", "shot-1", {"stage": "style-composition", "prompt": "Fresh composition", "model": "flux-1.1-pro"})
        self.assertEqual(queued["status"], "queued")
        self.assertEqual(len(launched), 1)
        job = json.loads(launched[0].read_text(encoding="utf-8"))
        self.assertEqual(job["version"], 2)
        self.assertRegex(job["outputPath"], r"^04-images/shot-1-[a-f0-9]{8}-v02\.png$")
        self.assertEqual(job["references"][0]["id"], "moodboard-demo")
        with self.assertRaises(ProductionDataError):
            actions.queue_generation("demo", "shot-4", {"stage": "style-composition", "prompt": "Shared setup"})

    def test_insert_retire_restore_preserves_identity_and_history(self) -> None:
        actions = ProductionActions(self.adapter, lambda _path: None)
        original_ids = [shot["shotId"] for shot in self.adapter.get_production("demo")["shots"]]
        created = actions.create_shot("demo", {
            "afterShotId": "shot-1",
            "title": "Inserted reaction",
            "storyVisualDescription": "A held reaction.",
            "imageDirection": "Close reaction, unchanged room.",
            "videoMotion": "One breath.",
        })
        self.assertEqual(created["displayNumber"], "1A")
        production = self.adapter.get_production("demo")
        self.assertEqual(production["shotCount"], 29)
        self.assertEqual([shot["shotId"] for shot in production["shots"] if shot["shotId"] in original_ids], original_ids)
        self.assertTrue(production["structureEditable"])

        actions.retire_shot("demo", created["shotId"], {"reason": "Pacing cut"})
        retired = self.adapter.get_production("demo")
        self.assertEqual(retired["shotCount"], 28)
        self.assertEqual(retired["retiredShots"][0]["shotId"], created["shotId"])
        self.assertEqual(retired["retiredShots"][0]["retiredReason"], "Pacing cut")
        self.assertTrue((self.fixture.project / "05-storyboard/shot-changes.jsonl").is_file())

        restored = actions.restore_shot("demo", created["shotId"], {"afterShotId": "shot-1"})
        self.assertEqual(restored["shotId"], created["shotId"])
        active = self.adapter.get_production("demo")
        self.assertIn(created["shotId"], {shot["shotId"] for shot in active["shots"]})
        self.assertEqual(active["retiredShotCount"], 0)

    def test_shared_setup_owner_cannot_be_retired(self) -> None:
        actions = ProductionActions(self.adapter)
        with self.assertRaises(ProductionDataError):
            actions.retire_shot("demo", "shot-1", {"reason": "Cut"})



class ProductionActionHttpTests(unittest.TestCase):
    def test_prompt_post_route_persists_an_edit(self) -> None:
        temp_base = os.environ.get("HEARTHLIGHT_TEST_TMP") or (r"C:\tmp" if os.name == "nt" else None)
        with tempfile.TemporaryDirectory(dir=temp_base) as folder:
            root = Path(folder)
            ProductionFixture(root)
            static, outputs, data = root / "static", root / "outputs", root / "data"
            for path in [static, outputs, data]:
                path.mkdir()
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(ServerConfig(outputs, static, data, root, root.parent / "action-cache")))
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with patch.object(ProductionActions, "open_shot_list", return_value={"opened": True, "name": "board-v3.xlsx", "path": "05-storyboard/board-v3.xlsx"}) as open_mock:
                    open_request = urllib.request.Request(
                        f"http://127.0.0.1:{server.server_port}/api/productions/demo/open-shot-list",
                        data=b"{}",
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(open_request, timeout=5) as response:
                        opened = json.loads(response.read())
                    self.assertTrue(opened["opened"])
                    open_mock.assert_called_once_with("demo")

                payload = json.dumps({"stage": "style-composition", "assetId": "image-1", "prompt": "HTTP prompt edit"}).encode()
                request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/api/productions/demo/shots/shot-1/prompt", data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(request, timeout=5) as response:
                    self.assertTrue(json.loads(response.read())["saved"])
                with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/api/productions/demo/shots/shot-1", timeout=5) as response:
                    self.assertEqual(json.loads(response.read())["shot"]["currentPrompt"]["prompt"], "HTTP prompt edit")
                create_payload = json.dumps({"afterShotId": "shot-1", "title": "HTTP inserted shot"}).encode()
                create_request = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_port}/api/productions/demo/shots",
                    data=create_payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(create_request, timeout=5) as response:
                    created = json.loads(response.read())
                retire_request = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_port}/api/productions/demo/shots/{created['shotId']}/retire",
                    data=json.dumps({"reason": "HTTP pacing cut"}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(retire_request, timeout=5) as response:
                    self.assertTrue(json.loads(response.read())["retired"])

            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=5)

class ProductionUiSourceTests(unittest.TestCase):
    def test_production_module_has_unique_function_declarations(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "film_study_tool/ui_static/productions.js").read_text(encoding="utf-8")
        names = re.findall(r"^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", source, re.MULTILINE)
        duplicates = sorted(name for name in set(names) if names.count(name) > 1)
        self.assertEqual(duplicates, [])
        self.assertIn("productionRequirementsPanel", source)
        self.assertIn("Open spreadsheet", source)
        self.assertIn('"Save Shot Vision"', source)
        self.assertIn("page.append(productionVisionEditor(production, shot, notice));", source)
        self.assertNotIn("productionVisionToolbar(production, notice)", source)
        self.assertNotIn('"Submit changes"', source)


class ProductionMediaHttpTests(unittest.TestCase):
    def test_registered_video_supports_byte_ranges(self) -> None:
        temp_base = os.environ.get("HEARTHLIGHT_TEST_TMP") or (r"C:\tmp" if os.name == "nt" else None)
        with tempfile.TemporaryDirectory(dir=temp_base) as folder:
            root = Path(folder)
            fixture = ProductionFixture(root)
            clip = fixture.project / "06-video/shot-01.mp4"
            clip.write_bytes(b"0123456789")
            (fixture.project / "06-video/ledger.jsonl").write_text(json.dumps({"event": "video", "event_id": "video-current", "asset_id": "video-current", "shot_id": "shot-1", "asset_path": "06-video/shot-01.mp4", "status": "approved"}) + "\n", encoding="utf-8")
            static = root / "static"
            outputs = root / "outputs"
            data = root / "data"
            for path in [static, outputs, data]:
                path.mkdir()
            config = ServerConfig(outputs, static, data, root, root.parent / "range-cache")
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(config))
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/production-media/demo/video-current", headers={"Range": "bytes=2-5"})
                with urllib.request.urlopen(request, timeout=5) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.read(), b"2345")
                    self.assertEqual(response.headers["Content-Range"], "bytes 2-5/10")
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/production-media/demo/not-registered", timeout=5)
                self.assertEqual(caught.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
