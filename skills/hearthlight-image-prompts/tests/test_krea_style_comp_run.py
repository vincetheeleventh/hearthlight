import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "skills" / "hearthlight-image-prompts" / "scripts" / "krea_style_comp_run.py"
SPEC = importlib.util.spec_from_file_location("krea_style_comp_run", MODULE)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
PROJECT = ROOT / "projects" / "yugioh"


class KreaStyleCompositionRunnerTests(unittest.TestCase):
    def test_current_plan_blocks_until_current_shot_visions_are_approved(self):
        with self.assertRaisesRegex(SystemExit, "no approved prompt"):
            runner.validate_plan(PROJECT)

    def test_version_history_resolves_legacy_event_mapping(self):
        events = [
            {"event_id": "old", "version": 1},
            {"shot_id": "stable", "version": 3},
            {"shot_id": "other", "version": 9},
        ]
        self.assertEqual(runner.next_version(events, "stable", {"old": "stable"}), 4)

    def test_pending_resume_requires_identical_request_fingerprint(self):
        packet = {"shot_id": "stable", "request_sha256": "request-b"}
        events = [
            {"event": "krea-submitted", "run_id": "a", "shot_id": "stable", "request_sha256": "request-a"},
            {"event": "krea-submitted", "run_id": "b", "shot_id": "stable", "request_sha256": "request-b", "krea_job_id": "job-b"},
        ]
        self.assertEqual(runner.pending_submission(events, packet)["krea_job_id"], "job-b")

    def test_output_filename_contains_stable_id_and_version(self):
        packet = {"shot": "23B", "shot_id": "12345678-aaaa-bbbb-cccc-123456789012"}
        path = runner.output_path(PROJECT, packet, 4)
        self.assertEqual(path.name, "shot-23b-12345678-v04.png")


if __name__ == "__main__":
    unittest.main()