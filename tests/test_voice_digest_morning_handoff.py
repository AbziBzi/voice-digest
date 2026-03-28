import unittest

from scripts.voice_digest_morning_handoff import render_progress_line


class VoiceDigestMorningHandoffTests(unittest.TestCase):
    def test_render_progress_line_prefers_actual_change_over_learned_or_next_step(self) -> None:
        progress_entry = [
            "### 2026-03-28",
            "- Added an explicit notifier readiness probe to the scheduler entrypoint.",
            "- Verification passed in two layers: py_compile and unittest succeeded.",
            "- Learned: this makes the remaining blocker much narrower.",
            "- Next step: wire the real destination.",
        ]

        self.assertEqual(
            render_progress_line(progress_entry),
            "Added an explicit notifier readiness probe to the scheduler entrypoint.",
        )

    def test_render_progress_line_falls_back_to_learned_when_no_change_bullet_exists(self) -> None:
        progress_entry = [
            "### 2026-03-28",
            "- Verification passed in two layers.",
            "- Learned: the notifier already had the right readiness signal.",
            "- Next step: wire the real destination.",
        ]

        self.assertEqual(
            render_progress_line(progress_entry),
            "Verification passed in two layers.",
        )


if __name__ == "__main__":
    unittest.main()
