from pathlib import Path
import importlib.util
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "voice_digest_prepare.py"
spec = importlib.util.spec_from_file_location("voice_digest_prepare", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class VoiceDigestPrepareTests(unittest.TestCase):
    def test_detects_explicit_visual_prefix(self) -> None:
        line = module.spoken_line("Worth opening later: benchmark chart comparing models")
        self.assertEqual(line, "VISUAL FLAG: benchmark chart comparing models")

    def test_does_not_flag_generic_image_metaphor(self) -> None:
        paragraph = (
            "Executives do not want tool-call traces. They want a synthesized image of how the "
            "company is doing and what to focus on next."
        )
        line = module.spoken_line(paragraph)
        self.assertEqual(line, paragraph)

    def test_detects_visual_review_language(self) -> None:
        paragraph = "Open the chart later to compare training curves side by side."
        line = module.spoken_line(paragraph)
        self.assertEqual(line, "VISUAL FLAG: Open the chart later to compare training curves side by side.")

    def test_build_script_omits_end_of_article_marker(self) -> None:
        script = module.build_script(
            "Headline\n\nKey point.\n\nEnd of article.",
            module.DEFAULT_INTRO,
            module.DEFAULT_OUTRO,
        )
        self.assertNotIn("End of article.", script)
        self.assertIn("Headline", script)
        self.assertIn("Key point.", script)


if __name__ == "__main__":
    unittest.main()
