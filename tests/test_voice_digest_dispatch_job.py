from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from subprocess import CompletedProcess
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "voice_digest_dispatch_job.py"
spec = importlib.util.spec_from_file_location("voice_digest_dispatch_job", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class VoiceDigestDispatchJobTests(unittest.TestCase):
    def test_summarize_command_failure_prefers_structured_json_error(self) -> None:
        result = CompletedProcess(
            args=["python3", "notifier"],
            returncode=1,
            stdout='{"status": "error", "error": "gateway unavailable", "returncode": 9}',
            stderr="",
        )
        summary = module.summarize_command_failure(
            result,
            "notifier_send",
            parsed_json={"status": "error", "error": "gateway unavailable", "returncode": 9},
        )
        self.assertEqual(summary["message"], "notifier_send failed with exit code 9")
        self.assertEqual(summary["detail"], "gateway unavailable")
        self.assertEqual(summary["returncode"], 1)

    def test_main_writes_structured_notifier_failure_into_status_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            args = Namespace(
                input_dir=tmp / "incoming_digests",
                glob="*.txt",
                runs_dir=tmp / "out" / "runs",
                state_path=tmp / "out" / "latest_run.json",
                handoff_text_path=tmp / "out" / "morning_handoff.txt",
                handoff_json_path=tmp / "out" / "morning_handoff.json",
                payload_json_path=tmp / "out" / "delivery_payload.json",
                status_json_path=tmp / "out" / "delivery_status.json",
                status_text_path=tmp / "out" / "delivery_status.txt",
                run_id=None,
                intro=None,
                outro=None,
                voice_id=None,
                model_id=None,
                dry_run=True,
                max_age_minutes=180.0,
                channel=None,
                target=None,
                config_path=tmp / ".voice_digest_notifier.json",
                audio_message_mode="caption",
                send=True,
                openclaw_dry_run=True,
            )

            morning_result = CompletedProcess(
                args=["python3", "morning"],
                returncode=0,
                stdout="morning ok\n",
                stderr="",
            )
            notifier_payload = {
                "status": "error",
                "error": "gateway unavailable",
                "returncode": 9,
                "diagnostics": {
                    "config_path": str(tmp / ".voice_digest_notifier.json"),
                    "config_exists": True,
                    "config_has_channel": True,
                    "config_has_target": True,
                    "env_channel_set": False,
                    "env_target_set": False,
                    "env_audio_message_mode_set": False,
                    "cli_channel_set": False,
                    "cli_target_set": False,
                    "cli_audio_message_mode_set": True,
                    "payload_path": str(tmp / "out" / "delivery_payload.json"),
                    "handoff_text_path": str(tmp / "out" / "morning_handoff.txt"),
                },
                "plan": {
                    "channel": "signal",
                    "target": "+37060000000",
                    "destination_source": "config",
                    "audio_message_mode": "caption",
                    "audio_message_mode_source": "config",
                },
            }
            notifier_result = CompletedProcess(
                args=["python3", "notifier"],
                returncode=1,
                stdout=json.dumps(notifier_payload),
                stderr="",
            )
            payload_json = {
                "mode": "live",
                "notifier_action": "send_audio",
                "delivery_kind": "audio",
                "delivery_target": str(tmp / "out" / "runs" / "digest.mp3"),
                "run": {
                    "selected_input": str(tmp / "incoming_digests" / "digest.txt"),
                    "age_minutes": 12.5,
                },
                "summary": {
                    "selected_input_details": {
                        "path": str(tmp / "incoming_digests" / "digest.txt"),
                        "exists": True,
                        "size_bytes": 321,
                        "modified_at": "2026-03-27T18:00:00+00:00",
                        "age_minutes": 9.0,
                    }
                },
            }

            with mock.patch.object(module, "parse_args", return_value=args), mock.patch.object(
                module,
                "run_command",
                side_effect=[morning_result, notifier_result],
            ), mock.patch.object(module, "load_optional_json", return_value=payload_json), mock.patch(
                "sys.stdout", new_callable=io.StringIO
            ), mock.patch("sys.stderr", new_callable=io.StringIO):
                exit_code = module.main()

            self.assertEqual(exit_code, 1)
            status = json.loads(args.status_json_path.read_text(encoding="utf-8"))
            self.assertEqual(status["status"], "failed")
            self.assertEqual(status["error"]["stage"], "notifier_send")
            self.assertEqual(status["error"]["message"], "notifier_send failed with exit code 9")
            self.assertEqual(status["error"]["detail"], "gateway unavailable")
            self.assertEqual(status["destination"]["channel"], "signal")
            self.assertEqual(status["destination"]["source"], "config")
            self.assertEqual(status["dispatch"]["resolved_audio_message_mode"], "caption")
            self.assertEqual(status["dispatch"]["audio_message_mode_source"], "config")
            self.assertEqual(status["summary"]["run_age_minutes"], 12.5)
            self.assertEqual(status["summary"]["selected_input_details"]["age_minutes"], 9.0)
            self.assertEqual(status["diagnostics"]["config_exists"], True)
            self.assertEqual(status["diagnostics"]["config_has_channel"], True)

            status_text = args.status_text_path.read_text(encoding="utf-8")
            self.assertIn("run_age_minutes: 12.5", status_text)
            self.assertIn("selected_input_age_minutes: 9.0", status_text)
            self.assertIn("selected_input_size_bytes: 321", status_text)


if __name__ == "__main__":
    unittest.main()
