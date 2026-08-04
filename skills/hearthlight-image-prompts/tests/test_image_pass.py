import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "image_pass.py"
TEST_TMP = Path(__file__).resolve().parents[3] / ".test-tmp" / "image-pass"
SPEC = importlib.util.spec_from_file_location("image_pass", MODULE_PATH)
image_pass = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(image_pass)


class ImagePassTests(unittest.TestCase):
    def setUp(self):
        TEST_TMP.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEST_TMP)
        self.root = Path(self.temp.name)
        (self.root / "04-images" / "review-proposals").mkdir(parents=True)
        (self.root / "03-bible" / "refs").mkdir(parents=True)
        specs = {
            "shots": [
                {
                    "shot": shot,
                    "title": f"Shot {shot}",
                    "render_mode": "source-photo" if shot == 23 else "generated",
                    "generation_owner": 1 if shot == 4 else shot,
                    "source_asset": "03-bible/refs/card.webp" if shot == 23 else None,
                }
                for shot in image_pass.ALL_SHOTS
            ]
        }
        image_pass.write_json(self.root / "04-images" / "shot-specs.json", specs)
        (self.root / "04-images" / "generations.jsonl").touch()
        image_pass.write_json(self.root / "03-bible" / "assets.json", image_pass.default_assets(self.root))
        Image.new("RGB", (400, 300), "#c8b99c").save(self.root / "source.png")

    def tearDown(self):
        self.temp.cleanup()

    def args(self, shot=1, job="job-1"):
        return SimpleNamespace(
            shot=shot,
            file=str(self.root / "source.png"),
            source="hearthlight-krea",
            prompt_file=None,
            model="krea/krea-2/medium",
            krea_job_id=job,
            krea_url="https://krea.example/asset.png",
            references_json=None,
            created_at=None,
            parent_version=None,
        )

    def test_record_is_immutable_and_duplicate_job_is_blocked(self):
        first = image_pass.record_generation(self.root, self.args())
        self.assertEqual(first["version"], 1)
        self.assertTrue((self.root / first["asset_path"]).exists())
        with self.assertRaises(SystemExit):
            image_pass.record_generation(self.root, self.args(job="job-1"))
        second = image_pass.record_generation(self.root, self.args(job="job-2"))
        self.assertEqual(second["version"], 2)
        self.assertNotEqual(first["asset_path"], second["asset_path"])

    def test_shared_shot_cannot_create_duplicate_generation(self):
        with self.assertRaises(SystemExit):
            image_pass.record_generation(self.root, self.args(shot=4))

    def test_review_requires_confirmation_and_selection_requires_approval(self):
        image_pass.record_generation(self.root, self.args())
        incoming = self.root / "review.json"
        image_pass.write_json(incoming, {
            "flagged": [{"shot": 2, "feedback": "Closer on the boot."}],
            "ambiguous": [],
        })
        proposal = image_pass.create_review_proposal(self.root, incoming, allow_incomplete=True)
        proposal_path = self.root / "04-images" / "review-proposals" / f"{proposal['proposal_id']}.json"
        with self.assertRaises(SystemExit):
            image_pass.apply_review(self.root, proposal_path, confirmed=False)
        image_pass.apply_review(self.root, proposal_path, confirmed=True)
        events = image_pass.load_events(self.root)
        self.assertEqual(image_pass.latest_review(events, 1)["status"], "approved")
        self.assertEqual(image_pass.latest_review(events, 2)["status"], "revision-requested")
        image_pass.select_final(self.root, 1, 1)
        self.assertEqual(image_pass.latest_selection(image_pass.load_events(self.root), 1)["version"], 1)

    def test_ambiguous_review_cannot_apply(self):
        incoming = self.root / "review.json"
        image_pass.write_json(incoming, {"flagged": [], "ambiguous": ["Did 'the doorway shot' mean 11 or 13?"]})
        proposal = image_pass.create_review_proposal(self.root, incoming, allow_incomplete=True)
        proposal_path = self.root / "04-images" / "review-proposals" / f"{proposal['proposal_id']}.json"
        with self.assertRaises(SystemExit):
            image_pass.apply_review(self.root, proposal_path, confirmed=True)

    def test_contact_sheet_builds_from_available_frames(self):
        image_pass.record_generation(self.root, self.args())
        output = self.root / "04-images" / "contact.png"
        image_pass.contact_sheet(self.root, output)
        self.assertTrue(output.exists())
        with Image.open(output) as image:
            self.assertGreater(image.width, 1000)


if __name__ == "__main__":
    unittest.main()
