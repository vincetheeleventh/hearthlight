from __future__ import annotations

import importlib.util
import json
import os
import sys
import shutil
import tempfile
import uuid
import types
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
PACKAGE = "hearthlight_studio_test"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(HERE)]
sys.modules.setdefault(PACKAGE, package)


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"{PACKAGE}.{name}", HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


productions = load("productions")
actions_module = load("production_actions")
ProductionAdapter = productions.ProductionAdapter
ProductionActions = actions_module.ProductionActions


class ShotVisionActionsTests(unittest.TestCase):
    def setUp(self) -> None:
        base = Path(os.environ["HEARTHLIGHT_TEST_TMP"]) if os.environ.get("HEARTHLIGHT_TEST_TMP") else HERE / ".test-tmp"
        base.mkdir(parents=True, exist_ok=True)
        self.root = base / uuid.uuid4().hex
        self.root.mkdir()
        self.project = self.root / "projects/demo"
        for path in [self.project / "02-outline", self.project / "03-bible", self.project / "04-images", self.project / "05-storyboard", self.root / "skills/hearthlight-dashboard"]:
            path.mkdir(parents=True, exist_ok=True)
        self.write(self.root / "skills/hearthlight-dashboard/pipeline.json", {"stages": []})
        self.write(self.root / "skills/hearthlight-dashboard/requirements.json", {"requirements": []})
        (self.project / "distribution-spec.md").write_text("- format: short film\n- client: none\n", encoding="utf-8")
        (self.project / "status.yml").write_text("", encoding="utf-8")
        self.write(self.project / "05-storyboard/shots.json", {
            "schema_version": 1, "source": "05-storyboard/board.xlsx", "status": "ready",
            "shots": [
                {"shot_id": "shot-1", "display_number": 1, "order": 1, "title": "Generated", "duration_seconds": 1, "text": {"visual_description": "A still", "action_description": "Then he moves", "camera_movement": "push in", "notes": "Hold"}, "image_direction": {"visual_description": "A still", "render_mode": "generated"}},
                {"shot_id": "shot-2", "display_number": 2, "order": 2, "title": "Photograph", "duration_seconds": 1, "text": {"visual_description": "Real photograph"}, "image_direction": {"visual_description": "Real photograph", "render_mode": "source-photo"}},
            ],
        })
        (self.project / "05-storyboard/board.xlsx").write_bytes(b"source")
        self.write(self.project / "05-storyboard/shot-narrative.json", {"shots": {"shot-1": {"one_liner": "First draft"}, "shot-2": {"one_liner": "Use the real photograph"}}})
        self.write(self.project / "03-bible/assets.json", {
            "master_aspect_ratio": "4:3", "moodboard": {"id": "m", "status": "selected", "strength": 0.35},
            "image_workflow": {"style_composition": {"model": "krea/krea-2/medium", "aspect_ratio": "4:3"}},
            "cost_approvals": {"style_composition_v4": {"status": "estimate-ready", "estimated_cu": 1, "estimated_minutes": 1}},
            "assets": [],
        })
        self.adapter = ProductionAdapter(self.root, self.root / "cache")
        self.compiled: list[tuple[str, list[str]]] = []

        def compiler(_project: Path, batch_id: str, shot_ids: list[str]) -> dict:
            self.compiled.append((batch_id, shot_ids))
            return {"batch_id": batch_id, "shots": [{"shot_id": value} for value in shot_ids]}

        self.actions = ProductionActions(self.adapter, prompt_compiler=compiler)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    @staticmethod
    def write(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def events(self) -> list[dict]:
        path = self.project / "04-images/shot-vision.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_compile_current_board_excludes_source_photos(self) -> None:
        result = self.actions.compile_current_visions("demo")
        self.assertTrue(result["compiled"])
        self.assertEqual(self.compiled[0][1], ["shot-1"])

    def test_submit_is_append_only_and_compiles_generated_shot(self) -> None:
        result = self.actions.submit_vision_batch("demo", {"changes": [{"shotId": "shot-1", "vision": "Hands hold on the card.", "baseRevision": 0}]})
        self.assertTrue(result["compiled"])
        self.assertEqual(self.compiled[0][1], ["shot-1"])
        event = self.events()[0]
        self.assertEqual(event["event"], "vision-updated")
        self.assertEqual(event["previous_vision"], "Vision: First draft")
        self.assertEqual(event["revision"], 1)

    def test_source_photo_saves_vision_without_compiling_or_spending(self) -> None:
        result = self.actions.submit_vision_batch("demo", {"changes": [{"shotId": "shot-2", "vision": "Keep the source photograph untouched.", "baseRevision": 0}]})
        self.assertFalse(result["compiled"])
        self.assertEqual(self.compiled, [])
        self.assertIn("source-photo", result["message"])

    def test_revert_creates_new_revision_and_preserves_history(self) -> None:
        self.actions.submit_vision_batch("demo", {"changes": [{"shotId": "shot-1", "vision": "Revision one", "baseRevision": 0}]})
        self.actions.submit_vision_batch("demo", {"changes": [{"shotId": "shot-1", "vision": "Revision two", "baseRevision": 1}]})
        result = self.actions.revert_vision("demo", "shot-1", {"revision": 1})
        self.assertTrue(result["saved"])
        history = [event for event in self.events() if event.get("shot_id") == "shot-1"]
        self.assertEqual([event["revision"] for event in history], [1, 2, 3])
        self.assertEqual(history[-1]["event"], "vision-reverted")
        self.assertEqual(history[-1]["vision"], "Revision one")

    def test_stale_base_revision_is_rejected(self) -> None:
        self.actions.submit_vision_batch("demo", {"changes": [{"shotId": "shot-1", "vision": "Current", "baseRevision": 0}]})
        with self.assertRaises(productions.ProductionDataError):
            self.actions.submit_vision_batch("demo", {"changes": [{"shotId": "shot-1", "vision": "Stale", "baseRevision": 0}]})


if __name__ == "__main__":
    unittest.main()
