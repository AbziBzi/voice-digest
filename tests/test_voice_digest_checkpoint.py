import tempfile
import unittest
from pathlib import Path

from scripts.voice_digest_checkpoint import extract_latest_progress_entry


class VoiceDigestCheckpointTests(unittest.TestCase):
    def test_extract_latest_progress_entry_prefers_topmost_heading(self) -> None:
        progress_text = """# Voice Digest Progress

### 2026-03-27
- newest entry
- still newest

### 2026-03-26
- older entry
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            progress_path = Path(tmpdir) / "VOICE_DIGEST_PROGRESS.md"
            progress_path.write_text(progress_text, encoding="utf-8")

            self.assertEqual(
                extract_latest_progress_entry(progress_path),
                ["### 2026-03-27", "- newest entry", "- still newest"],
            )


if __name__ == "__main__":
    unittest.main()
