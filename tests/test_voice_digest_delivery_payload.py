from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "voice_digest_delivery_payload.py"
spec = importlib.util.spec_from_file_location("voice_digest_delivery_payload", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class VoiceDigestDeliveryPayloadTests(unittest.TestCase):
    def test_build_delivery_payload_includes_delivery_target_details_for_live_audio(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            run_dir = tmp / "out" / "runs" / "20260328-053000"
            run_dir.mkdir(parents=True)
            incoming_dir = tmp / "incoming_digests"
            incoming_dir.mkdir(parents=True)

            selected_input = incoming_dir / "digest.txt"
            selected_input.write_text("Digest body\n", encoding="utf-8")

            spoken_script = run_dir / "spoken.txt"
            spoken_script.write_text("Good morning.\n", encoding="utf-8")

            audio_output = run_dir / "digest.mp3"
            audio_output.write_bytes(b"ID3demo-audio")

            timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            manifest_path = run_dir / "manifest.json"
            manifest = {
                "timestamp": timestamp,
                "mode": "live",
                "inputs": {
                    "source_digest": str(selected_input),
                    "voice_id_override": None,
                    "model_id_override": None,
                },
                "outputs": {
                    "spoken_script": str(spoken_script),
                    "audio_output": str(audio_output),
                    "dry_run_note": None,
                },
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            state_path = tmp / "out" / "latest_run.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "timestamp": timestamp,
                "mode": "live",
                "run_dir": str(run_dir),
                "manifest": str(manifest_path),
                "spoken_script": str(spoken_script),
                "audio_output": str(audio_output),
                "dry_run_note": None,
                "selected_input": str(selected_input),
            }
            state_path.write_text(json.dumps(state), encoding="utf-8")

            payload = module.build_delivery_payload(state_path)

            self.assertEqual(payload["delivery_kind"], "audio")
            details = payload["summary"]["delivery_target_details"]
            self.assertEqual(details["path"], str(audio_output))
            self.assertEqual(details["exists"], True)
            self.assertEqual(details["size_bytes"], len(b"ID3demo-audio"))
            self.assertIn("modified_at", details)
            self.assertIn("age_minutes", details)


if __name__ == "__main__":
    unittest.main()
