from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prompt_authoring.py"
SPEC = importlib.util.spec_from_file_location("prompt_authoring", SCRIPT)
authoring = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(authoring)


STYLE = "Confident dark ink linework, soft flat colour washes, minimal detail."
CHECKS = {
    "single_instant": True,
    "visibility_grounded": True,
    "ownership_clear": True,
    "continuity_grounded": True,
    "illustration_native": True,
    "controls_outside_prose": True,
    "concise": True,
}


class VisibilityAwarePromptTests(unittest.TestCase):
    def character(self, identity: str, traits: list[tuple[str, list[str]]]) -> dict:
        return {
            identity: {
                "id": identity,
                "signature_string": "complete signature that must never be pasted",
                "visual_traits": [{"text": text, "regions": regions} for text, regions in traits],
            }
        }

    def validate(self, spec: dict, characters: dict) -> list[str]:
        return authoring.validate_spec(
            spec,
            {"shot_id": spec["shot_id"], "project": "yugioh", "locked_style": STYLE},
            characters,
            "16:9",
        )

    def test_shot_2_partial_body_prompt_omits_invisible_identity_and_later_action(self) -> None:
        characters = {
            **self.character("father", [
                ("buzzed hair", ["head"]), ("strong nose", ["face"]),
                ("adult male hands", ["hands"]), ("high-laced tan desert boot", ["feet"]),
                ("bloused desert-camouflage trouser cuff", ["legs", "feet"]),
            ]),
            **self.character("mother", [
                ("hair pushed back and unbrushed", ["head"]), ("shadowed eyes", ["face"]),
                ("nightshirt and cardigan hem", ["legs"]), ("worn slippers", ["feet"]),
            ]),
        }
        spec = {
            "shot_id": "shot-2",
            "frozen_instant": "At the bedside, two hands hold one boot lace while a woman's slippered lower legs stand beside him.",
            "composition": {"shot_size": "close insert", "viewpoint": "bed height", "crop": "hands and lower legs only", "staging": "", "depth": "", "negative_space": ""},
            "subjects": [
                {"id": "father", "role": "father", "visible_regions": ["hands", "feet", "legs"], "visible_traits": ["adult male hands", "high-laced tan desert boot", "bloused desert-camouflage trouser cuff"], "screen_position": "frame left", "visibility": "partial", "pose": "hands resting at the laces", "gaze": "", "expression": "", "interaction": "holding the boot lace"},
                {"id": "mother", "role": "mother", "visible_regions": ["legs", "feet"], "visible_traits": ["nightshirt and cardigan hem", "worn slippers"], "screen_position": "frame right", "visibility": "partial", "pose": "standing", "gaze": "", "expression": "", "interaction": ""},
            ],
            "props": [{"name": "high-laced tan desert boot", "owner": "father", "count": 1, "position": "frame left", "legibility": ""}],
            "environment": "bed edge", "lighting": "window light", "required_elements": [],
            "forbidden_elements": ["faces", "hair", "upper bodies", "mug", "dog tags"],
            "prompt_body": "Close insert at bed height. The father's adult male hands rest at the laces of one high-laced tan desert boot; a bloused desert-camouflage trouser cuff is visible at frame left. At frame right, only the mother's nightshirt and cardigan hem and worn slippers are visible beside the bed edge. Pale window light shapes the hands, boot, and lower legs.",
            "quality_checks": CHECKS, "blockers": [],
        }
        self.assertEqual(self.validate(spec, characters), [])
        prompt = authoring.render_prompt(spec, STYLE, "16:9")
        for forbidden in ["buzzed hair", "strong nose", "shadowed eyes", "mug", "dog tags", "timecode", "then"]:
            self.assertNotIn(forbidden, prompt.casefold())
        self.assertIn("adult male hands", prompt)
        self.assertIn("high-laced tan desert boot", prompt)

    def test_invisible_or_paraphrased_character_traits_block(self) -> None:
        characters = self.character("father", [("buzzed hair", ["head"]), ("adult male hands", ["hands"])])
        base = {"shot_id": "shot-2", "frozen_instant": "Hands rest on boot laces.", "composition": {}, "props": [], "quality_checks": CHECKS, "blockers": []}
        invisible = {**base, "prompt_body": "The father's buzzed hair and hands fill the insert.", "subjects": [{"id": "father", "visibility": "partial", "visible_regions": ["hands"], "visible_traits": ["buzzed hair"]}]}
        paraphrased = {**base, "prompt_body": "The father's close-cropped hair fills the insert.", "subjects": [{"id": "father", "visibility": "partial", "visible_regions": ["head"], "visible_traits": ["close-cropped hair"]}]}
        self.assertTrue(any("Invisible trait" in value for value in self.validate(invisible, characters)))
        self.assertTrue(any("Unknown or paraphrased" in value for value in self.validate(paraphrased, characters)))

    def test_shot_9_hand_insert_excludes_face_feet_and_unrelated_wardrobe(self) -> None:
        characters = self.character("boy", [
            ("messy brown hair", ["head"]), ("round face and big dark eyes", ["face"]),
            ("small child's hands", ["hands"]), ("bare feet", ["feet"]),
            ("band-aid on one knee", ["knees"]), ("oversized SONICS tee", ["torso", "arms"]),
        ])
        spec = {
            "shot_id": "shot-9", "frozen_instant": "A child's hand holds one card against an adult palm.",
            "composition": {"shot_size": "insert", "crop": "hands and forearms", "viewpoint": "overhead"},
            "subjects": [{"id": "boy", "role": "boy", "visible_regions": ["hands", "arms"], "visible_traits": ["small child's hands"], "screen_position": "center", "visibility": "partial", "pose": "hand extended", "gaze": "", "expression": "", "interaction": "holds one card against an adult palm"}],
            "props": [{"name": "card", "owner": "boy", "count": 1, "position": "between the hands", "legibility": "illustration visible"}],
            "environment": "", "lighting": "soft room light", "required_elements": [], "forbidden_elements": [],
            "prompt_body": "Overhead insert of the boy's small child's hands and forearms at centre, holding one illustrated card against an adult palm. Soft room light; the crop contains hands and forearms only.",
            "quality_checks": CHECKS, "blockers": [],
        }
        self.assertEqual(self.validate(spec, characters), [])
        prompt = authoring.render_prompt(spec, STYLE, "16:9")
        for forbidden in ["bare feet", "band-aid", "big dark eyes", "SONICS"]:
            self.assertNotIn(forbidden, prompt)

    def test_shot_25_back_of_head_can_hold_head_trait_but_not_face_or_boot_traits(self) -> None:
        characters = self.character("father", [
            ("buzzed hair", ["head"]), ("strong nose", ["face"]), ("high-laced tan desert boot", ["feet"]),
        ])
        spec = {
            "shot_id": "shot-25", "frozen_instant": "Over the father's shoulder, the boy's fully sunlit face occupies the opposite side of frame.",
            "composition": {"shot_size": "close-up", "viewpoint": "over shoulder", "crop": "father's back of head and shoulder only"},
            "subjects": [{"id": "father", "role": "father foreground", "visible_regions": ["head", "shoulder"], "visible_traits": ["buzzed hair"], "screen_position": "frame left", "visibility": "partial", "pose": "back to viewer", "gaze": "", "expression": "", "interaction": ""}],
            "props": [], "environment": "driveway", "lighting": "hard sunlight on the boy", "required_elements": [], "forbidden_elements": ["father's face", "father's boots"],
            "prompt_body": "Close over-shoulder frame. The father's buzzed hair and shoulder form a dark foreground shape at frame left, back to the viewer. Across from him, the boy's face is fully exposed to hard driveway sunlight.",
            "quality_checks": CHECKS, "blockers": [],
        }
        self.assertEqual(self.validate(spec, characters), [])
        prompt = authoring.render_prompt(spec, STYLE, "16:9")
        self.assertIn("buzzed hair", prompt)
        self.assertNotIn("strong nose", prompt)
        self.assertNotIn("high-laced tan desert boot", prompt)

    def test_motion_or_multiple_temporal_states_block(self) -> None:
        spec = {"shot_id": "shot-x", "frozen_instant": "He starts to rise, then looks up at 1.0-3.0s.", "prompt_body": "He starts to rise, then looks up.", "subjects": [], "composition": {}, "props": [], "quality_checks": CHECKS, "blockers": []}
        blockers = self.validate(spec, {})
        self.assertTrue(any("motion or multiple temporal states" in value for value in blockers))

    def test_generic_quality_words_and_model_controls_block(self) -> None:
        spec = {"shot_id": "shot-x", "frozen_instant": "One still figure.", "prompt_body": "A stunning masterpiece using Krea moodboard strength.", "subjects": [], "composition": {}, "props": [], "quality_checks": CHECKS, "blockers": []}
        blockers = self.validate(spec, {})
        self.assertTrue(any("generic quality" in value.casefold() for value in blockers))
        self.assertTrue(any("controls leaked" in value.casefold() for value in blockers))
        incomplete = {**spec, "prompt_body": "One still figure.", "quality_checks": {}}
        self.assertTrue(any("self-audit failed" in value.casefold() for value in self.validate(incomplete, {})))

    def test_rant_event_is_loaded_as_current_confirmed_vision(self) -> None:
        event = {
            "event": "vision-rant-applied", "shot_id": "shot-8", "revision": 2,
            "vision": "Current direction", "confirmed_by_user": True,
        }
        with patch.object(authoring, "seed_visions", return_value={}), patch.object(authoring, "read_jsonl", return_value=[event]):
            current = authoring.current_visions(Path("."))["shot-8"]
        self.assertEqual(current["revision"], 2)
        self.assertEqual(current["vision"], "Current direction")
        self.assertTrue(current["confirmed_by_user"])
    def test_focused_contract_is_injected_into_author_and_reviewer(self) -> None:
        guide = authoring.author_guide()
        self.assertIn("Five control layers", guide)
        self.assertIn("Attribute binding", guide)
        bundle = {"shots": [], "film_laws": "law", "locked_style": STYLE, "visual_system": {}, "target": {}}
        self.assertIn("FOCUSED AUTHOR CONTRACT", authoring.worker_instructions(bundle))
        review = authoring.reviewer_instructions({"shot_id": "shot-x"}, {"shot_id": "shot-x"}, "prompt", bundle)
        self.assertIn("independent Shot Prompt Reviewer", review)
        self.assertIn("Attribute binding", review)


if __name__ == "__main__":
    unittest.main()