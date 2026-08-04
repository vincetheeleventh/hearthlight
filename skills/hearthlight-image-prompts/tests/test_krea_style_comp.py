import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "projects" / "yugioh"


def load_script(name: str):
    path = ROOT / "skills" / "hearthlight-image-prompts" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compiler = load_script("krea_style_comp")
two_pass = load_script("two_pass")


class KreaStyleCompositionCompilerTests(unittest.TestCase):
    def test_shot_25_prompt_is_frame_one_cell_only(self):
        packet = compiler.compile_legacy_packet(PROJECT, "25")
        source, headers, record, excel_row = compiler.source_row(PROJECT, "25")
        self.assertEqual(packet["prompt"], compiler.normalize_prompt(record[compiler.STILL_COLUMN]))
        self.assertEqual(packet["source"]["prompt_cell"], "H28")
        self.assertEqual(packet["source"]["excluded_action_cell"], "I28")
        self.assertEqual(excel_row, 28)
        self.assertTrue(source.name.endswith("-v4.xlsx"))

    def test_prompt_excludes_motion_and_workflow_material(self):
        prompt = compiler.compile_legacy_packet(PROJECT, "25")["prompt"]
        for fragment in compiler.FORBIDDEN_PROMPT_FRAGMENTS:
            self.assertNotIn(fragment.lower(), prompt.lower())
        self.assertIsNone(compiler.TIMECODE.search(prompt))
        self.assertNotIn("0.0-1.0s", prompt)
        self.assertNotIn("Handheld, rising with the lift", prompt)

    def test_alphanumeric_shot_ids_are_supported(self):
        packet = compiler.compile_legacy_packet(PROJECT, "23B")
        self.assertEqual(packet["shot"], "23B")
        self.assertEqual(packet["title"], "Hiding It")

    def test_full_batch_compiles_all_unique_v4_setups(self):
        plan, packets = compiler.compile_legacy_batch(PROJECT)
        self.assertEqual(plan["generation_count"], 28)
        self.assertEqual(len(packets), 28)
        self.assertEqual(
            {(item["shot"], item["owner_shot"]) for item in plan["shared_setups"]},
            {("5", "1"), ("18B", "17")},
        )
        self.assertEqual([item["shot"] for item in plan["source_only"]], ["29"])
        self.assertEqual(len({packet["shot_id"] for _, packet in packets}), 28)

    def test_every_batch_prompt_equals_its_frame_one_cell(self):
        _, packets = compiler.compile_legacy_batch(PROJECT)
        for _, packet in packets:
            _, _, record, _ = compiler.source_row(PROJECT, packet["shot"])
            self.assertEqual(packet["prompt"], compiler.normalize_prompt(record[compiler.STILL_COLUMN]))
            compiler.validate_prompt(packet["prompt"])
            self.assertEqual(packet["prompt_sha256"], compiler.text_sha256(packet["prompt"]))
    def test_source_photo_cannot_generate(self):
        with self.assertRaisesRegex(SystemExit, "source photography"):
            compiler.compile_legacy_packet(PROJECT, "29")

    def test_dispatcher_blocks_unapproved_current_shot_vision(self):
        with self.assertRaisesRegex(SystemExit, "no approved prompt"):
            compiler.compile_packet(PROJECT, "25")

    def test_batch_dispatcher_blocks_until_every_current_vision_is_approved(self):
        with self.assertRaisesRegex(SystemExit, "no approved prompt"):
            compiler.compile_batch(PROJECT)

    def test_legacy_stage_a_compiler_is_disabled(self):
        with self.assertRaisesRegex(SystemExit, "Legacy Stage-A compiler disabled"):
            two_pass.compile_prompts(PROJECT, "style-composition", 25)


if __name__ == "__main__":
    unittest.main()
