from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "voice_digest_openclaw_notifier.py"
spec = importlib.util.spec_from_file_location("voice_digest_openclaw_notifier", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class VoiceDigestNotifierTests(unittest.TestCase):
    def test_render_error_json_includes_plan_and_process_details(self) -> None:
        rendered = module.render_error_json(
            "send failed",
            {"channel": "signal", "target": "+370"},
            returncode=17,
            stdout="dry-run output",
            stderr="transport unhappy",
        )
        payload = json.loads(rendered)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error"], "send failed")
        self.assertEqual(payload["returncode"], 17)
        self.assertEqual(payload["stdout"], "dry-run output")
        self.assertEqual(payload["stderr"], "transport unhappy")
        self.assertEqual(payload["plan"]["channel"], "signal")

    def test_main_emits_structured_json_when_openclaw_send_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            payload_path = tmp / "delivery_payload.json"
            handoff_path = tmp / "morning_handoff.txt"
            payload_path.write_text(
                json.dumps(
                    {
                        "mode": "live",
                        "notifier_action": "send_audio",
                        "delivery_kind": "audio",
                        "delivery_target": str(tmp / "digest.mp3"),
                        "run": {"selected_input": "digest.txt"},
                        "summary": {
                            "spoken_preview": "Quick preview",
                            "source_digest": "Daily AI digest",
                        },
                    }
                ),
                encoding="utf-8",
            )
            handoff_path.write_text("Morning handoff", encoding="utf-8")

            args = Namespace(
                payload_path=payload_path,
                handoff_text_path=handoff_path,
                channel="signal",
                target="+37060000000",
                config_path=tmp / ".voice_digest_notifier.json",
                audio_message_mode="caption",
                send=True,
                openclaw_dry_run=False,
                json=True,
            )

            failure = subprocess.CalledProcessError(
                9,
                ["openclaw", "message", "send"],
                output='{"status":"transport-error"}\n',
                stderr="gateway unavailable\n",
            )

            with mock.patch.object(module, "parse_args", return_value=args), mock.patch.object(
                module,
                "run_openclaw",
                side_effect=failure,
            ), mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                exit_code = module.main()

            self.assertEqual(exit_code, 1)
            result = json.loads(stdout.getvalue())
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["error"], "openclaw message send failed with exit code 9")
            self.assertEqual(result["returncode"], 9)
            self.assertEqual(result["stdout"], '{"status":"transport-error"}')
            self.assertEqual(result["stderr"], "gateway unavailable")
            self.assertEqual(result["plan"]["audio_message_mode"], "caption")
            self.assertEqual(result["plan"]["channel"], "signal")


if __name__ == "__main__":
    unittest.main()
