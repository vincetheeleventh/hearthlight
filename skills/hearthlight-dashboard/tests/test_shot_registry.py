from __future__ import annotations

import importlib.util
import unittest
import json
import tempfile
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "build_shot_registry.py"
SPEC = importlib.util.spec_from_file_location("build_shot_registry", MODULE_PATH)
registry = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(registry)


def shot(number: int, title: str, shot_id: str | None = None) -> dict:
    value = {
        "display_number": number,
        "order": number,
        "legacy_numbers": [str(number)],
        "title": title,
        "board_panels": [str(number)],
    }
    if shot_id:
        value["shot_id"] = shot_id
    return value


class ShotRegistryReconciliationTests(unittest.TestCase):
    def test_reorder_preserves_ids(self):
        old = [shot(1, "Arrival", "one"), shot(2, "Embrace", "two")]
        incoming = [shot(1, "Embrace"), shot(2, "Arrival")]
        result, findings, retired = registry.reconcile_shots("film", incoming, old)
        self.assertEqual([item["shot_id"] for item in result], ["two", "one"])
        self.assertIn("2", result[0]["legacy_numbers"])
        self.assertEqual(findings, [])
        self.assertEqual(retired, [])

    def test_insert_and_delete_keep_unambiguous_ids(self):
        old = [shot(1, "Arrival", "one"), shot(2, "Embrace", "two")]
        incoming = [shot(1, "Arrival"), shot(2, "Dog Tags")]
        result, findings, retired = registry.reconcile_shots("film", incoming, old)
        self.assertEqual(result[0]["shot_id"], "one")
        self.assertEqual(result[1]["id_state"], "new")
        self.assertEqual(retired, ["two"])
        self.assertEqual(findings, [])

    def test_ambiguous_title_never_guesses(self):
        old = [shot(1, "Hands", "one"), shot(2, "Hands", "two")]
        incoming = [shot(3, "Hands")]
        incoming[0]["legacy_numbers"] = []
        incoming[0]["board_panels"] = []
        result, findings, _ = registry.reconcile_shots("film", incoming, old)
        self.assertEqual(result[0]["id_state"], "needs_reconciliation")
        self.assertEqual(findings[0]["code"], "ambiguous-shot-match")
    def test_explicit_id_wins_over_changed_labels(self):
        old = [shot(1, "Arrival", "one")]
        incoming = [shot(19, "Renamed Arrival", "one")]
        incoming[0]["legacy_numbers"] = []
        incoming[0]["board_panels"] = []
        result, findings, retired = registry.reconcile_shots("film", incoming, old)
        self.assertEqual(result[0]["shot_id"], "one")
        self.assertEqual(result[0]["matched_by"], "explicit-shot-id")
        self.assertEqual(findings, [])
        self.assertEqual(retired, [])

    def test_placeholder_legacy_values_are_not_identity(self):
        self.assertIsNone(registry.valid_legacy("new"))
        self.assertIsNone(registry.valid_legacy("-"))
        self.assertEqual(registry.valid_legacy("23B"), "23B")

    def test_image_direction_merges_by_legacy_not_shifted_display(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            project = Path(folder)
            target = project / "04-images" / "shot-specs.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps({
                "shots": [{
                    "shot": 3,
                    "legacy_id": "3",
                    "image_visual_description": "Dog tags under collar",
                    "generation_owner": 3,
                }]
            }), encoding="utf-8")
            incoming = [
                {"display_number": 3, "legacy_numbers": [], "shot_id": "new", "title": "New insert"},
                {"display_number": 4, "legacy_numbers": ["3"], "shot_id": "old-three", "title": "Tag goes under"},
            ]
            findings = registry.merge_image_direction(project, incoming)
            self.assertEqual(findings, [])
            self.assertNotIn("image_direction", incoming[0])
            self.assertEqual(incoming[1]["image_direction"]["visual_description"], "Dog tags under collar")

    def test_stable_id_override_sets_shared_setup_owner(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            project = Path(folder)
            storyboard = project / "05-storyboard"
            storyboard.mkdir(parents=True)
            (storyboard / "shot-registry-overrides.json").write_text(json.dumps({
                "shots": [{
                    "shot_id": "insert",
                    "shared_setup_owner_shot_id": "owner",
                }]
            }), encoding="utf-8")
            incoming = [{"shot_id": "owner"}, {"shot_id": "insert"}]
            findings = registry.apply_registry_overrides(project, incoming)
            self.assertEqual(findings, [])
            self.assertEqual(incoming[1]["shared_setup_owner_shot_id"], "owner")




if __name__ == "__main__":
    unittest.main()
